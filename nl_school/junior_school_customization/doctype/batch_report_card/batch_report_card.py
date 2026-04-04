# Copyright (c) 2024, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.pdf import get_pdf
from frappe.www.printview import get_letter_head
from frappe.utils import now_datetime
import io

from nl_school.junior_school_customization.controllers.student_report_generation_tool import (
    get_formatted_result,
    get_child_assessment_groups,
    get_attendance_count,
    process_assessment_results,
    calculate_averages,
    detect_exam_types,
    get_rubber_stamp,
    get_student_image,
    get_class_teacher,
)


class BatchReportCard(Document):
    pass


@frappe.whitelist()
def get_students_for_batch(academic_year, program=None, student_group=None):
    """
    Get students based on filters for batch report card generation.
    Returns students enrolled in the given academic year, optionally filtered by program/student_group.
    """
    filters = {"academic_year": academic_year, "docstatus": 1}
    
    if program:
        filters["program"] = program
    
    # Get students from Program Enrollment
    enrollments = frappe.get_all(
        "Program Enrollment",
        filters=filters,
        fields=["student", "student_name", "program", "student_group"],
    )
    
    # If student_group filter is specified, filter further
    if student_group:
        # Get students from the specific student group
        group_students = frappe.get_all(
            "Student Group Student",
            filters={"parent": student_group, "active": 1},
            fields=["student"],
            pluck="student",
        )
        enrollments = [e for e in enrollments if e.student in group_students]
    
    # Remove duplicates (a student might have multiple enrollments)
    seen = set()
    unique_students = []
    for e in enrollments:
        if e.student not in seen:
            seen.add(e.student)
            unique_students.append({
                "student": e.student,
                "student_name": e.student_name,
                "program": e.program,
                "student_group": e.student_group or student_group,
            })
    
    return unique_students


@frappe.whitelist()
def generate_batch_report_cards(doc):
    """
    Generate report cards for all selected students as a single combined PDF.
    """
    import json
    
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))
    
    if not doc.get("students") or len(doc.students) == 0:
        frappe.throw(_("Please select at least one student"))
    
    all_html_parts = []
    
    for idx, student_row in enumerate(doc.students):
        student = student_row.get("student")
        
        # Prepare doc for single student
        student_doc = frappe._dict({
            "student": student,
            "students": [student],
            "academic_year": doc.academic_year,
            "academic_term": doc.academic_term,
            "assessment_group": doc.assessment_group,
            "add_letterhead": doc.get("add_letterhead", 1),
            "include_attendance": doc.get("include_attendance", 1),
        })
        
        try:
            template_data = prepare_batch_report_card_data(student_doc)
            
            # Clean course names
            for item in template_data.get("assessment_result", []):
                if "course" in item and "-" in item["course"]:
                    item["course"] = item["course"].split("-")[0].strip()
            
            html = frappe.render_template(
                "nl_school/public/html/student_report_generation_tool.html",
                template_data
            )
            
            # Add page break between students (except for last one)
            if idx < len(doc.students) - 1:
                html += '<div style="page-break-after: always;"></div>'
            
            all_html_parts.append(html)
            
        except Exception as e:
            frappe.log_error(f"Error generating report card for {student}: {str(e)}")
            frappe.msgprint(
                _("Error generating report card for {0}: {1}").format(student, str(e)),
                indicator="orange"
            )
            continue
    
    if not all_html_parts:
        frappe.throw(_("Could not generate any report cards. Please check the error log."))
    
    # Combine all HTML parts
    combined_html = "\n".join(all_html_parts)
    
    final_template = frappe.render_template(
        "frappe/www/printview.html",
        {"body": combined_html, "title": "Batch Report Cards"}
    )
    
    # Generate PDF
    pdf_content = get_pdf(final_template)
    
    # Return as file response
    frappe.response.filename = f"Batch_Report_Cards_{doc.academic_year}_{now_datetime().strftime('%Y%m%d_%H%M%S')}.pdf"
    frappe.response.filecontent = pdf_content
    frappe.response.type = "pdf"


def prepare_batch_report_card_data(doc):
    """
    Prepare all data needed for a single student's report card in batch mode.
    """
    student = doc.students[0]
    class_teacher = get_class_teacher(student)
    values = get_formatted_result(doc, get_course=True)
    assessment_groups = get_child_assessment_groups(doc.assessment_group)
    letterhead = get_letter_head(doc, not doc.add_letterhead)
    
    # Attendance data
    if doc.get("include_attendance"):
        doc.attendance = get_attendance_count(
            student, doc.academic_year, doc.academic_term
        )
    else:
        doc.attendance = frappe._dict({"present": "-", "absent": "-", "total": "-"})
    
    # Process assessment results
    assessment_results = process_assessment_results(values.get("assessment_result", []))
    averages = calculate_averages(values.get("assessment_result", []))
    exam_types_present = detect_exam_types(values.get("assessment_result", []))
    
    return {
        "doc": doc,
        "values": values,
        "assessment_result": assessment_results,
        "courses": values.get("courses"),
        "assessment_groups": assessment_groups,
        "letterhead": letterhead and letterhead.get("content", None),
        "rubber_stamp": get_rubber_stamp(student),
        "add_letterhead": doc.add_letterhead if doc.add_letterhead else 0,
        "averages": averages,
        "academic_term": doc.academic_term,
        "class_teacher": class_teacher,
        "student_image": get_student_image(student),
        "show_levels": True,
        "show_opener": exam_types_present["Opener Exam"],
        "show_midterm": exam_types_present["Mid Term"],
        "show_endterm": exam_types_present["End Term"],
        "date": now_datetime().strftime("%Y-%m-%d %H:%M:%S"),
    }
