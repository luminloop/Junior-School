# Copyright (c) 2024, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import today, getdate, fmt_money
from frappe.utils.pdf import get_pdf
from jinja2 import Template


class FeeNotificationTool(Document):
    pass


@frappe.whitelist()
def get_students_with_outstanding_fees(
    academic_year, academic_term=None, program=None, student_group=None,
    min_outstanding_amount=0, only_overdue=False
):
    """
    Get students with outstanding fee balances.
    """
    filters = {
        "academic_year": academic_year,
        "docstatus": 1,
        "outstanding_amount": [">", min_outstanding_amount or 0],
    }
    
    if academic_term:
        filters["academic_term"] = academic_term
    if program:
        filters["program"] = program
    
    if only_overdue:
        filters["due_date"] = ["<", today()]
    
    # Get fees with outstanding amounts
    fees = frappe.get_all(
        "Fees",
        filters=filters,
        fields=[
            "name", "student", "student_name", "program", "grand_total",
            "outstanding_amount", "due_date", "academic_term"
        ],
        order_by="student"
    )
    
    # Filter by student group if specified
    if student_group:
        group_students = frappe.get_all(
            "Student Group Student",
            filters={"parent": student_group, "active": 1},
            fields=["student"],
            pluck="student"
        )
        fees = [f for f in fees if f.student in group_students]
    
    # Group by student
    students = {}
    for fee in fees:
        if fee.student not in students:
            students[fee.student] = {
                "student": fee.student,
                "student_name": fee.student_name,
                "program": fee.program,
                "fees": [],
                "total_outstanding": 0,
            }
        
        # Get fee components for breakdown
        components = frappe.get_all(
            "Fee Component",
            filters={"parent": fee.name},
            fields=["fees_category", "amount"]
        )
        
        students[fee.student]["fees"].append({
            "fee_name": fee.name,
            "grand_total": fee.grand_total,
            "outstanding": fee.outstanding_amount,
            "due_date": fee.due_date,
            "academic_term": fee.academic_term,
            "components": components,
        })
        students[fee.student]["total_outstanding"] += fee.outstanding_amount
    
    # Get guardian info for each student
    for student_id, student_data in students.items():
        guardians = get_student_guardians(student_id)
        student_data["guardians"] = guardians
    
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
def send_fee_notifications(doc):
    """
    Send fee reminder notifications to parents via email and/or SMS.
    """
    import json
    
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))
    
    students = get_students_with_outstanding_fees(
        academic_year=doc.academic_year,
        academic_term=doc.academic_term,
        program=doc.program,
        student_group=doc.student_group,
        min_outstanding_amount=doc.min_outstanding_amount,
        only_overdue=doc.only_overdue,
    )
    
    if not students:
        frappe.throw(_("No students found with outstanding fees for the selected filters"))
    
    sent_count = 0
    failed_count = 0
    
    school_name = frappe.db.get_single_value("Education Settings", "school_name") or "School"
    company = frappe.db.get_single_value("Education Settings", "company")
    currency = frappe.db.get_value("Company", company, "default_currency") if company else "KES"
    
    for student in students:
        for guardian in student.get("guardians", []):
            # Prepare fee breakdown
            fee_breakdown = []
            if doc.include_fee_breakdown:
                for fee in student.get("fees", []):
                    for comp in fee.get("components", []):
                        fee_breakdown.append({
                            "description": comp.get("fees_category"),
                            "amount": comp.get("amount"),
                        })
            
            # Get earliest due date
            due_dates = [f.get("due_date") for f in student.get("fees", []) if f.get("due_date")]
            earliest_due = min(due_dates) if due_dates else None
            
            message = render_message(
                template=doc.message_template,
                guardian_name=guardian.get("guardian_name"),
                student_name=student.get("student_name"),
                outstanding_amount=fmt_money(student.get("total_outstanding"), currency=currency),
                fee_breakdown=fee_breakdown if doc.include_fee_breakdown else None,
                due_date=earliest_due,
                currency=currency,
                school_name=school_name,
            )
            
            try:
                if doc.notification_channel in ["Email", "Both"] and guardian.get("email"):
                    attachments = []
                    if doc.attach_statement_pdf:
                        pdf_content = generate_fee_statement_pdf(student, school_name, currency)
                        attachments = [{
                            "fname": f"Fee_Statement_{student.get('student_name')}.pdf",
                            "fcontent": pdf_content,
                        }]
                    
                    send_email_notification(
                        recipient=guardian.get("email"),
                        subject=f"Fee Reminder - {student.get('student_name')}",
                        message=message,
                        attachments=attachments,
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
                    f"Failed to send fee notification to {guardian.get('guardian_name')}: {str(e)}",
                    "Fee Notification Error"
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


def generate_fee_statement_pdf(student, school_name, currency):
    """Generate a PDF fee statement for a student."""
    html = frappe.render_template(
        "nl_school/public/html/fee_statement.html",
        {
            "student": student,
            "school_name": school_name,
            "currency": currency,
            "date": today(),
        }
    )
    return get_pdf(html)


def send_email_notification(recipient, subject, message, attachments=None):
    """Send email notification with optional attachments."""
    frappe.sendmail(
        recipients=[recipient],
        subject=subject,
        message=message,
        attachments=attachments,
        now=True,
    )


def send_sms_notification(recipient, message):
    """Send SMS notification."""
    if frappe.db.exists("SMS Settings"):
        try:
            from frappe.core.doctype.sms_settings.sms_settings import send_sms
            send_sms([recipient], message)
        except Exception as e:
            frappe.log_error(f"SMS sending failed: {str(e)}")
            raise
    else:
        frappe.log_error("SMS Settings not configured", "Fee Notification - SMS")
        raise Exception("SMS Settings not configured")


@frappe.whitelist()
def preview_notification(doc):
    """Generate a preview of the notification message."""
    import json
    
    if isinstance(doc, str):
        doc = frappe._dict(json.loads(doc))
    
    students = get_students_with_outstanding_fees(
        academic_year=doc.academic_year,
        academic_term=doc.academic_term,
        program=doc.program,
        student_group=doc.student_group,
        min_outstanding_amount=doc.min_outstanding_amount,
        only_overdue=doc.only_overdue,
    )
    
    if not students:
        return "No students found with outstanding fees. Please adjust filters."
    
    student = students[0]
    guardian = student.get("guardians", [{}])[0] if student.get("guardians") else {}
    
    school_name = frappe.db.get_single_value("Education Settings", "school_name") or "School"
    company = frappe.db.get_single_value("Education Settings", "company")
    currency = frappe.db.get_value("Company", company, "default_currency") if company else "KES"
    
    fee_breakdown = []
    if doc.include_fee_breakdown:
        for fee in student.get("fees", []):
            for comp in fee.get("components", []):
                fee_breakdown.append({
                    "description": comp.get("fees_category"),
                    "amount": comp.get("amount"),
                })
    
    due_dates = [f.get("due_date") for f in student.get("fees", []) if f.get("due_date")]
    earliest_due = min(due_dates) if due_dates else None
    
    message = render_message(
        template=doc.message_template,
        guardian_name=guardian.get("guardian_name", "Parent/Guardian"),
        student_name=student.get("student_name"),
        outstanding_amount=fmt_money(student.get("total_outstanding"), currency=currency),
        fee_breakdown=fee_breakdown if doc.include_fee_breakdown else None,
        due_date=earliest_due,
        currency=currency,
        school_name=school_name,
    )
    
    return message


# Scheduled task for automated fee reminders
def send_automated_fee_reminders():
    """
    Scheduled task to send automated fee reminders for overdue fees.
    Called weekly by scheduler.
    """
    # Get current academic year and term
    current_year = frappe.db.get_single_value("Education Settings", "current_academic_year")
    current_term = frappe.db.get_single_value("Education Settings", "current_academic_term")
    
    if not current_year:
        return
    
    # Get students with overdue fees
    students = get_students_with_outstanding_fees(
        academic_year=current_year,
        academic_term=current_term,
        only_overdue=True,
        min_outstanding_amount=100,  # Minimum amount to trigger reminder
    )
    
    if not students:
        return
    
    school_name = frappe.db.get_single_value("Education Settings", "school_name") or "School"
    company = frappe.db.get_single_value("Education Settings", "company")
    currency = frappe.db.get_value("Company", company, "default_currency") if company else "KES"
    
    default_template = """Dear {{ guardian_name }},

This is an automated reminder that fees for {{ student_name }} are overdue.

Outstanding Balance: {{ currency }} {{ outstanding_amount }}

Please arrange payment at your earliest convenience to avoid any inconvenience.

Regards,
{{ school_name }}"""
    
    for student in students:
        for guardian in student.get("guardians", []):
            if guardian.get("email"):
                try:
                    message = render_message(
                        template=default_template,
                        guardian_name=guardian.get("guardian_name"),
                        student_name=student.get("student_name"),
                        outstanding_amount=fmt_money(student.get("total_outstanding"), currency=currency),
                        currency=currency,
                        school_name=school_name,
                    )
                    
                    send_email_notification(
                        recipient=guardian.get("email"),
                        subject=f"Overdue Fee Reminder - {student.get('student_name')}",
                        message=message,
                    )
                except Exception as e:
                    frappe.log_error(
                        f"Automated fee reminder failed for {student.get('student_name')}: {str(e)}",
                        "Automated Fee Reminder Error"
                    )
