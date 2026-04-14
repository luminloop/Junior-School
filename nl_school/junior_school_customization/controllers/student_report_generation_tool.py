import frappe

from frappe import _
from frappe.desk.treeview import get_children

import json
import re
from frappe.utils.pdf import get_pdf
from frappe.model.document import Document

# from education.education.report.course_wise_assessment_report.course_wise_assessment_report import (
#     get_child_assessment_groups,
# )
from frappe.utils import now_datetime

from nl_school.junior_school_customization.doctype.report_card_template.report_card_template import (
    get_default_template,
    get_template_html,
)


class StudentReportGenerationTool(Document):
    pass


@frappe.whitelist()
def preview_report_card(doc, preview_only=False):
    """Main function to generate report card PDF or HTML preview"""
    doc = process_document_input(doc)
    template_data = prepare_report_card_data(doc)

    for item in template_data.get("assessment_result", []):
        if "course" in item and "-" in item["course"]:
            item["course"] = item["course"].split("-")[0].strip()

    if preview_only:
        # Return HTML for preview
        return generate_html_response(template_data)
    else:
        generate_pdf_response(doc, template_data)


def process_document_input(doc):
    """Parse and prepare the document input"""
    doc = frappe._dict(json.loads(doc))
    doc.students = [doc.student]
    return doc


def prepare_report_card_data(doc):
    """Prepare all data needed for the report card template"""
    # Basic document data
    class_teacher = get_class_teacher(doc.students[0])
    principal = get_principal()
    # If a live signature was captured on the form, override the stored one
    if doc.get("include_principal_signature") and doc.get("principal_signature_data"):
        principal["signature"] = doc.get("principal_signature_data")
    values = get_formatted_result(doc, get_course=True)
    assessment_groups = get_child_assessment_groups(doc.assessment_group)
    # Don't use letterhead for report cards - it contains Jinja code meant for invoices
    # Instead we'll use a simple school header in the template
    letterhead = None

    # Attendance data
    doc.attendance = get_attendance_count(
        doc.students[0], doc.academic_year, doc.academic_term
    )

    # Process assessment results
    assessment_results = process_assessment_results(values.get("assessment_result", []))
    averages = calculate_averages(values.get("assessment_result", []))
    exam_types_present = detect_exam_types(values.get("assessment_result", []))

    return {
        "doc": doc,
        "attendance": doc.attendance,
        "values": values,
        "assessment_result": assessment_results,
        "courses": values.get("courses"),
        "assessment_groups": assessment_groups,
        "letterhead": None,
        "rubber_stamp": get_rubber_stamp(doc.student),
        "add_letterhead": doc.add_letterhead if doc.add_letterhead else 0,
        "averages": averages,
        "academic_term": doc.academic_term,
        "class_teacher": class_teacher,
        "principal": principal,
        "principal_name": principal.get("name"),
        "principal_signature": principal.get("signature"),
        "school_name": get_default_company() or "",
        "student_image": get_student_image(doc.student),
        "show_levels": True,
        "show_opener": exam_types_present["Opener Exam"],
        "show_midterm": exam_types_present["Mid Term"],
        "show_endterm": exam_types_present["End Term"],
        "date": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
        "include_principal_signature": doc.get("include_principal_signature", 0),
        "include_teacher_comments": doc.get("include_teacher_comments", 1),
    }


def get_default_company():
    company = None
    try:
        if frappe.get_meta("Education Settings").has_field("default_company"):
            company = frappe.db.get_single_value("Education Settings", "default_company")
    except Exception:
        company = None

    if not company:
        try:
            if frappe.get_meta("Global Defaults").has_field("default_company"):
                company = frappe.db.get_single_value("Global Defaults", "default_company")
        except Exception:
            company = None

    if not company:
        company = frappe.defaults.get_user_default("Company")

    if not company:
        company = frappe.db.get_value("Company", {}, "name")

    return company


def get_rubber_stamp(student):
    try:
        school = get_default_company()
        if not school:
            return None
        company = frappe.get_doc("Company", school)
        rubber_stamp = getattr(company, "custom_rubber_stamp", None)
        return rubber_stamp if rubber_stamp else None
    except Exception:
        return None


def generate_pdf_response(doc, template_data):
    """Generate and return the PDF response"""
    # Check if a custom template is specified
    template_name = doc.get("report_card_template")
    
    # If no template specified, try to get default for the company
    if not template_name:
        company = get_default_company()
        template_name = get_default_template(company)
    
    # Get template HTML
    template_html = None
    if template_name:
        template_html = get_template_html(template_name)
    
    # Use custom template or fall back to default file
    if template_html:
        html = frappe.render_template(template_html, template_data)
    else:
        html = frappe.render_template(
            "nl_school/public/html/student_report_generation_tool.html", template_data
        )

    final_template = frappe.render_template(
        "frappe/www/printview.html", {"body": html, "title": "Report Card"}
    )

    frappe.response.filename = f"Report Card {doc.students[0]}.pdf"
    frappe.response.filecontent = get_pdf(final_template)
    frappe.response.type = "pdf"


def generate_html_response(template_data):
    """Generate and return HTML for preview"""
    # Check if a custom template is specified
    template_name = template_data.get("doc", {}).get("report_card_template")
    
    # If no template specified, try to get default for the company
    if not template_name:
        company = get_default_company()
        template_name = get_default_template(company)
    
    # Get template HTML
    template_html = None
    if template_name:
        template_html = get_template_html(template_name)
    
    # Use custom template or fall back to default file
    if template_html:
        html = frappe.render_template(template_html, template_data)
    else:
        html = frappe.render_template(
            "nl_school/public/html/student_report_generation_tool.html", template_data
        )
    
    return html


def process_assessment_results(assessment_results):
    """Add levels and percentage to assessment results"""
    processed_results = []
    for result in assessment_results:
        grading_scale = frappe.db.get_value(
            "Assessment Result", result["name"], "grading_scale"
        )
        maximum_score = frappe.db.get_value(
            "Assessment Result", result["name"], "maximum_score"
        )
        if maximum_score and maximum_score > 0:
            percentage = (result["total_score"] / maximum_score) * 100
        else:
            percentage = result["total_score"]
        grade_info = get_grade(percentage, grading_scale)
        result["levels"] = grade_info.get("levels") or result.get("grade") or "-"
        result["percentage"] = round(percentage, 1)
        
        # Auto-generate teacher comments if enabled and no existing comment
        try:
            company = frappe.defaults.get_user_default("Company")
            if company:
                settings = frappe.get_all(
                    "School Email Settings",
                    filters={"company": company, "auto_generate_comment": 1},
                    fields=["teacher_comment_template"]
                )
                
                if settings and settings[0].teacher_comment_template:
                    # Check if this result already has a comment
                    existing_comments = frappe.get_all(
                        "Subject Teacher Comment",
                        {"parent": result["name"]},
                        ["comment"]
                    )
                    
                    if not existing_comments:
                        # Auto-generate comment based on grade
                        auto_comment = get_auto_teacher_comment(
                            result.get("student"),
                            result.get("course"),
                            result.get("grade"),
                            result.get("total_score")
                        )
                        if auto_comment:
                            # Store as subject_teacher_comments for template
                            result["auto_generated_comment"] = auto_comment
        except Exception:
            pass
        
        processed_results.append(result)
    return processed_results


def detect_exam_types(assessment_results):
    """Determine which exam types are present in the results"""
    exam_types_present = {
        "Opener Exam": False,
        "Mid Term": False,
        "End Term": False,
    }

    for result in assessment_results:
        ag = result.get("assessment_group", "")
        if ag in exam_types_present:
            exam_types_present[ag] = True

    return exam_types_present


def calculate_averages(assessment_result):
    """
    Calculate average scores, grades and levels for assessments
    Returns '-' for both score and levels when no assessments exist for a term
    """
    opener_percentages = []
    mid_term_percentages = []
    end_term_percentages = []
    grading_scale = ""

    for result in assessment_result:
        if not grading_scale:
            grading_scale = frappe.db.get_value(
                "Assessment Result", result["name"], "grading_scale"
            )

        maximum_score = frappe.db.get_value(
            "Assessment Result", result["name"], "maximum_score"
        )
        if maximum_score and maximum_score > 0:
            pct = (result["total_score"] / maximum_score) * 100
        else:
            pct = result["total_score"]

        ag = result.get("assessment_group", "")
        if ag == "Opener Exam":
            opener_percentages.append(pct)
        elif ag == "Mid Term":
            mid_term_percentages.append(pct)
        elif ag == "End Term":
            end_term_percentages.append(pct)

    # Default values when no assessments exist
    no_result = {"score": "-", "grade": "-", "levels": "-"}

    # Calculate averages only if assessments exist
    opener = no_result
    if opener_percentages:
        avg = sum(opener_percentages) / len(opener_percentages)
        grade_info = get_grade(avg, grading_scale)
        opener = {
            "score": round(avg, 2),
            "grade": grade_info.get("grade") or "-",
            "levels": grade_info.get("levels") or "-",
        }

    mid_term = no_result
    if mid_term_percentages:
        avg = sum(mid_term_percentages) / len(mid_term_percentages)
        grade_info = get_grade(avg, grading_scale)
        mid_term = {
            "score": round(avg, 2),
            "grade": grade_info.get("grade") or "-",
            "levels": grade_info.get("levels") or "-",
        }

    end_term = no_result
    if end_term_percentages:
        avg = sum(end_term_percentages) / len(end_term_percentages)
        grade_info = get_grade(avg, grading_scale)
        end_term = {
            "score": round(avg, 2),
            "grade": grade_info.get("grade") or "-",
            "levels": grade_info.get("levels") or "-",
        }

    return {"opener": opener, "mid_term": mid_term, "end_term": end_term}


def get_grade(score, grading_scale):
    results = {"grade": None, "levels": None}
    grading_scale = frappe.get_doc("Grading Scale", grading_scale)
    grading_intervals = grading_scale.intervals

    for interval in sorted(grading_intervals, key=lambda x: x.threshold, reverse=True):
        if score >= interval.threshold:
            # Use grade_description as levels, fallback to grade_code
            levels = interval.grade_description or interval.grade_code
            return {"grade": interval.grade_code, "levels": levels}

    return results


def get_attendance_count(student, academic_year, academic_term=None):
    attendance = frappe._dict()
    attendance.total = 0

    if academic_year:
        from_date, to_date = frappe.db.get_value(
            "Academic Year", academic_year, ["year_start_date", "year_end_date"]
        )
    elif academic_term:
        from_date, to_date = frappe.db.get_value(
            "Academic Term", academic_term, ["term_start_date", "term_end_date"]
        )

    if from_date and to_date:
        data = frappe.db.sql("""
            SELECT status, COUNT(name) as count
            FROM `tabStudent Attendance`
            WHERE student = %s AND docstatus = 1 AND date BETWEEN %s AND %s
            GROUP BY status
        """, (student, from_date, to_date), as_dict=True)

        for row in data:
            if row.status == "Present":
                attendance.present = row.count
            if row.status == "Absent":
                attendance.absent = row.count
            attendance.total += row.count
        return attendance
    else:
        return attendance


def execute(filters=None):
    data, chart = [], []

    if filters.get("assessment_group") == "All Assessment Groups":
        frappe.throw(
            _("Please select the assessment group other than 'All Assessment Groups'")
        )

    data, criterias = get_data(filters)
    columns = get_column(criterias)
    chart = get_chart(data, criterias)

    return columns, data, None, chart


def get_data(filters):
    data = []
    criterias = []
    values = get_formatted_result(filters)

    for result in values.get("assessment_result"):
        row = frappe._dict()
        row.student = result.get("student")
        row.student_name = result.get("student_name")

        for detail in result.details:
            criteria = detail.get("assessment_criteria")
            row[frappe.scrub(criteria)] = detail.get("grade")
            row[frappe.scrub(criteria) + "_score"] = detail.get("score")
            if criteria not in criterias:
                criterias.append(criteria)

        data.append(row)

    return data, criterias


def get_formatted_result(args, get_course=False):
    courses = []
    filters = prepare_filters(args)

    assessment_result = frappe.get_all(
        "Assessment Result",
        filters,
        [
            "student",
            "student_name",
            "name",
            "course",
            "assessment_group",
            "total_score",
            "grade",
            "academic_term",
        ],
        order_by="",
    )
    for result in assessment_result:
        if get_course and result.course not in courses:
            courses.append(result.course)

        details = frappe.get_all(
            "Assessment Result Detail",
            {
                "parent": result.name,
            },
            ["assessment_criteria", "maximum_score", "grade", "score"],
        )
        result.update({"details": details})

        # Get subject teacher comments
        comments = frappe.get_all(
            "Subject Teacher Comment",
            {"parent": result.name},
            ["course", "course_name", "comment"],
        )
        if comments:
            result.update({"subject_teacher_comments": comments})

    return {"assessment_result": assessment_result, "courses": courses}


def prepare_filters(args):
    filters = {"academic_year": args.academic_year, "docstatus": 1}

    options = ["course", "academic_term", "student_group"]
    for option in options:
        if args.get(option):
            filters[option] = args.get(option)

    assessment_groups = get_child_assessment_groups(args.assessment_group)

    filters.update({"assessment_group": ["in", assessment_groups]})

    if args.students:
        filters.update({"student": ["in", args.students]})

    return filters


def get_column(criterias):
    columns = [
        {
            "fieldname": "student",
            "label": _("Student ID"),
            "fieldtype": "Link",
            "options": "Student",
            "width": 150,
        },
        {
            "fieldname": "student_name",
            "label": _("Student Name"),
            "fieldtype": "Data",
            "width": 150,
        },
    ]
    for criteria in criterias:
        columns.append(
            {
                "fieldname": frappe.scrub(criteria),
                "label": criteria,
                "fieldtype": "Data",
                "width": 100,
            }
        )
        columns.append(
            {
                "fieldname": frappe.scrub(criteria) + "_score",
                "label": "Score (" + criteria + ")",
                "fieldtype": "Float",
                "width": 100,
            }
        )

    return columns


def get_chart(data, criterias):
    dataset = []
    students = [row.student_name for row in data]

    for criteria in criterias:
        dataset_row = {"values": []}
        dataset_row["name"] = criteria
        for row in data:
            if frappe.scrub(criteria) + "_score" in row:
                dataset_row["values"].append(row[frappe.scrub(criteria) + "_score"])
            else:
                dataset_row["values"].append(0)

        dataset.append(dataset_row)

    charts = {
        "data": {"labels": students, "datasets": dataset},
        "type": "bar",
        "colors": ["#ff0e0e", "#ff9966", "#ffcc00", "#99cc33", "#339900"],
    }

    return charts


def get_child_assessment_groups(assessment_group):
    assessment_groups = []
    group_type = frappe.get_value("Assessment Group", assessment_group, "is_group")
    if group_type:
        assessment_groups = [
            d.get("value")
            for d in get_children("Assessment Group", assessment_group)
            if d.get("value") and not d.get("expandable")
        ]
    else:
        assessment_groups = [assessment_group]
    return assessment_groups


def get_student_image(student):
    try:
        student = frappe.get_doc("Student", student)
        if student.image:
            # Only return image if it's a valid URL (not a local file path)
            if student.image.startswith('http'):
                return student.image
        return None
    except Exception:
        return None


def get_class_teacher(student_name):
    parent_list = frappe.get_all(
        "Student Group Student",
        filters={"student": student_name, "active": 1},
        fields=["parent"],
        as_list=True,
    )
    if parent_list:
        first_parent = parent_list[0][0]

        # Get the first instructor assigned to this student group
        class_teacher = frappe.db.get_value(
            "Student Group Instructor",
            {"parent": first_parent},
            "instructor_name"
        )
        return class_teacher


def get_principal(company=None):
    """Get the principal name and signature for the school."""
    if not company:
        company = frappe.defaults.get_user_default("Company")
    
    principal_data = {
        "name": None,
        "signature": None
    }
    
    if company:
        # Try to get principal from School Email Settings (company-specific)
        settings = frappe.get_all(
            "School Email Settings",
            filters={"company": company},
            fields=["name", "principal_name", "principal_signature"]
        )
        
        if settings:
            principal_data["name"] = settings[0].principal_name
            principal_data["signature"] = settings[0].principal_signature
    
    return principal_data


def get_auto_teacher_comment(student_name, course, grade, score):
    """Auto-generate teacher comment based on grade."""
    try:
        company = frappe.defaults.get_user_default("Company")
        
        if not company:
            return None
        
        # Get settings for auto-generation
        settings = frappe.get_all(
            "School Email Settings",
            filters={"company": company, "auto_generate_comment": 1},
            fields=["teacher_comment_template", "name"]
        )
        
        if not settings or not settings[0].teacher_comment_template:
            return None
        
        template = settings[0].teacher_comment_template
        student = frappe.get_doc("Student", student_name)
        
        # Render template with variables
        from jinja2 import Template
        comment = Template(template).render(
            student_name=student.student_name,
            course=course,
            grade=grade,
            score=score
        )
        
        return comment
    
    except Exception:
        return None


# TODO: Add the function to create charts and convert them to images
