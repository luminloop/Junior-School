# Copyright (c) 2024, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from jinja2 import Template


class GradeNotificationTool(Document):
    pass


@frappe.whitelist()
def get_students_with_results(academic_year, academic_term=None, program=None, student_group=None, assessment_group=None):
    """
    Get students with their assessment results and guardian contact info.
    """
    filters = {
        "academic_year": academic_year,
        "docstatus": 1,
    }
    
    if academic_term:
        filters["academic_term"] = academic_term
    if program:
        filters["program"] = program
    if student_group:
        filters["student_group"] = student_group
    if assessment_group:
        filters["assessment_group"] = assessment_group
    
    # Get assessment results
    results = frappe.get_all(
        "Assessment Result",
        filters=filters,
        fields=[
            "student", "student_name", "course", "total_score", "grade",
            "class_rank", "class_total_students", "program", "student_group"
        ],
        order_by="student, course"
    )
    
    # Group by student
    students = {}
    for r in results:
        if r.student not in students:
            students[r.student] = {
                "student": r.student,
                "student_name": r.student_name,
                "program": r.program,
                "student_group": r.student_group,
                "scores": [],
                "class_rank": r.class_rank,
                "class_total": r.class_total_students,
            }
        students[r.student]["scores"].append({
            "course": r.course,
            "total_score": r.total_score,
            "grade": r.grade,
        })
    
    # Get guardian info for each student
    for student_id, student_data in students.items():
        guardians = get_student_guardians(student_id)
        student_data["guardians"] = guardians
        
        # Calculate average
        scores = [s["total_score"] for s in student_data["scores"] if s["total_score"]]
        student_data["average"] = round(sum(scores) / len(scores), 1) if scores else 0
    
    return list(students.values())


def get_student_guardians(student):
    """Get guardian contact info for a student."""
    guardians = frappe.get_all(
        "Student Guardian",
        filters={"parent": student},
        fields=["guardian", "relation"]
    )
    
    result = []
    for g in guardians:
        guardian_doc = frappe.get_doc("Guardian", g.guardian)
        result.append({
            "guardian": g.guardian,
            "guardian_name": guardian_doc.guardian_name,
            "relation": g.relation,
            "email": guardian_doc.email_address,
            "mobile": guardian_doc.mobile_number,
        })
    
    return result


@frappe.whitelist()
def send_grade_notifications(doc):
    """
    Send grade notifications to parents via email and/or SMS.
    """
    import json
    
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))
    
    students = get_students_with_results(
        academic_year=doc.academic_year,
        academic_term=doc.academic_term,
        program=doc.program,
        student_group=doc.student_group,
        assessment_group=doc.assessment_group,
    )
    
    if not students:
        frappe.throw(_("No students found with assessment results for the selected filters"))
    
    sent_count = 0
    failed_count = 0
    
    school_name = frappe.db.get_single_value("Education Settings", "school_name") or "School"
    
    for student in students:
        for guardian in student.get("guardians", []):
            message = render_message(
                template=doc.message_template,
                guardian_name=guardian.get("guardian_name"),
                student_name=student.get("student_name"),
                academic_term=doc.academic_term,
                scores=student.get("scores") if doc.include_scores else None,
                average=student.get("average"),
                class_rank=student.get("class_rank") if doc.include_ranking else None,
                class_total=student.get("class_total") if doc.include_ranking else None,
                school_name=school_name,
            )
            
            try:
                if doc.notification_channel in ["Email", "Both"] and guardian.get("email"):
                    send_email_notification(
                        recipient=guardian.get("email"),
                        subject=f"Academic Performance Report - {student.get('student_name')}",
                        message=message,
                    )
                    sent_count += 1
                
                if doc.notification_channel in ["SMS", "Both"] and guardian.get("mobile"):
                    send_sms_notification(
                        recipient=guardian.get("mobile"),
                        message=message,
                    )
                    sent_count += 1
                    
            except Exception as e:
                frappe.log_error(
                    f"Failed to send notification to {guardian.get('guardian_name')}: {str(e)}",
                    "Grade Notification Error"
                )
                failed_count += 1
    
    return {
        "sent": sent_count,
        "failed": failed_count,
        "total_students": len(students),
    }


def render_message(template, **context):
    """Render the message template with the given context."""
    try:
        jinja_template = Template(template)
        return jinja_template.render(**context)
    except Exception as e:
        frappe.log_error(f"Template rendering error: {str(e)}")
        return template


def send_email_notification(recipient, subject, message):
    """Send email notification."""
    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        now=True,
    )


def send_sms_notification(recipient, message):
    """
    Send SMS notification.
    This is a placeholder - actual implementation depends on SMS provider.
    """
    # Check if SMS Settings exist and are configured
    if frappe.db.exists("SMS Settings"):
        try:
            from frappe.core.doctype.sms_settings.sms_settings import send_sms
            send_sms([recipient], message)
        except Exception as e:
            frappe.log_error(f"SMS sending failed: {str(e)}")
            raise
    else:
        frappe.log_error("SMS Settings not configured", "Grade Notification - SMS")
        raise Exception("SMS Settings not configured")


@frappe.whitelist()
def preview_notification(doc):
    """Generate a preview of the notification message."""
    import json
    
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))
    
    # Get sample data for preview
    students = get_students_with_results(
        academic_year=doc.academic_year,
        academic_term=doc.academic_term,
        program=doc.program,
        student_group=doc.student_group,
        assessment_group=doc.assessment_group,
    )
    
    if not students:
        return "No students found. Please adjust filters."
    
    # Use first student for preview
    student = students[0]
    guardian = student.get("guardians", [{}])[0] if student.get("guardians") else {}
    
    school_name = frappe.db.get_single_value("Education Settings", "school_name") or "School"
    
    message = render_message(
        template=doc.message_template,
        guardian_name=guardian.get("guardian_name", "Parent/Guardian"),
        student_name=student.get("student_name"),
        academic_term=doc.academic_term,
        scores=student.get("scores") if doc.include_scores else None,
        average=student.get("average"),
        class_rank=student.get("class_rank") if doc.include_ranking else None,
        class_total=student.get("class_total") if doc.include_ranking else None,
        school_name=school_name,
    )
    
    return message
