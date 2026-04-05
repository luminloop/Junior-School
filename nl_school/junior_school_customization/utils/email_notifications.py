# Copyright (c) 2024, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import nowdate, getdate, add_days, fmt_money, flt


# =============================================================================
# Scheduler Functions - Called automatically by Frappe
# =============================================================================

def send_daily_absent_alerts():
    """
    Daily scheduler task: Send absence alerts for students marked absent today.
    Only sends for first day of absence (not consecutive).
    """
    today = nowdate()
    yesterday = add_days(today, -1)
    
    # Get students absent today but NOT absent yesterday
    absent_today = frappe.get_all(
        "Student Attendance",
        filters={"date": today, "status": "Absent", "docstatus": 1},
        pluck="student"
    )
    
    absent_yesterday = frappe.get_all(
        "Student Attendance",
        filters={"date": yesterday, "status": "Absent", "docstatus": 1},
        pluck="student"
    )
    
    # Only alert for first-day absences
    first_day_absent = set(absent_today) - set(absent_yesterday)
    
    for student in first_day_absent:
        try:
            send_absent_alert_email(student, today, absent_days_count=1)
        except Exception as e:
            frappe.log_error(
                f"Failed to send absent alert for {student}: {str(e)}",
                "Daily Absent Alert Error"
            )
    
    # Also check for consecutive absences (3+ days)
    for student in absent_today:
        consecutive_days = count_consecutive_absences(student, today)
        if consecutive_days >= 3:
            try:
                send_absent_alert_email(student, today, absent_days_count=consecutive_days)
            except Exception as e:
                frappe.log_error(
                    f"Failed to send consecutive absence alert for {student}: {str(e)}",
                    "Consecutive Absence Alert Error"
                )


def send_weekly_attendance_warnings():
    """
    Weekly scheduler task: Send low attendance warnings to parents.
    Checks all active students and warns if attendance < 75%.
    """
    current_year = frappe.db.get_single_value("Education Settings", "current_academic_year")
    if not current_year:
        return
    
    # Get all active students
    students = frappe.get_all("Student", filters={"enabled": 1}, pluck="name")
    
    min_required = 75
    
    for student in students:
        try:
            # Calculate attendance for current term
            total_days = frappe.db.count(
                "Student Attendance",
                filters={"student": student, "docstatus": 1}
            )
            
            if total_days < 10:  # Skip if not enough data
                continue
            
            present_days = frappe.db.count(
                "Student Attendance",
                filters={"student": student, "status": "Present", "docstatus": 1}
            )
            
            absent_days = total_days - present_days
            attendance_pct = (present_days / total_days * 100) if total_days > 0 else 100
            
            if attendance_pct < min_required:
                send_low_attendance_warning(
                    student=student,
                    attendance_percentage=attendance_pct,
                    days_present=present_days,
                    total_days=total_days,
                    days_absent=absent_days,
                    min_required=min_required,
                )
        except Exception as e:
            frappe.log_error(
                f"Failed to send attendance warning for {student}: {str(e)}",
                "Weekly Attendance Warning Error"
            )


def send_overdue_fee_escalations():
    """
    Monthly scheduler task: Send overdue fee escalation emails.
    Checks invoices overdue by 14+ days.
    """
    today = getdate(nowdate())
    threshold_date = add_days(today, -14)
    
    # Get overdue invoices
    overdue_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "due_date": ["<", threshold_date],
            "status": ["in", ["Overdue", "Unpaid"]],
        },
        fields=["name", "customer", "outstanding_amount", "due_date"]
    )
    
    for invoice in overdue_invoices:
        try:
            # Find linked student
            student = frappe.db.get_value("Student", {"customer": invoice.customer}, "name")
            if not student:
                continue
            
            days_overdue = (today - getdate(invoice.due_date)).days
            
            send_overdue_escalation_email(
                student=student,
                outstanding_amount=invoice.outstanding_amount,
                due_date=invoice.due_date,
                invoice_number=invoice.name,
                days_overdue=days_overdue,
            )
        except Exception as e:
            frappe.log_error(
                f"Failed to send overdue escalation for {invoice.name}: {str(e)}",
                "Overdue Fee Escalation Error"
            )


def count_consecutive_absences(student, from_date):
    """Count consecutive days of absence ending at from_date."""
    count = 0
    current_date = getdate(from_date)
    
    while True:
        absent = frappe.db.exists(
            "Student Attendance",
            {"student": student, "date": current_date, "status": "Absent", "docstatus": 1}
        )
        if absent:
            count += 1
            current_date = add_days(current_date, -1)
        else:
            break
    
    return count


def get_school_info():
    """Get school branding and contact information."""
    settings = frappe.get_doc("Education Settings")
    company = None
    
    if settings.get("company"):
        try:
            company = frappe.get_doc("Company", settings.company)
        except Exception:
            pass
    
    return {
        "school_name": settings.get("school_name") or company.company_name if company else "School",
        "company_logo": company.company_logo if company else "",
        "company_address": company.address if company else "",
        "company_phone": company.phone_no if company else "",
        "company_email": company.email if company else "",
        "currency": company.default_currency if company else "KES",
    }


def get_student_guardians(student):
    """Get guardian contact info for a student."""
    guardians = frappe.get_all(
        "Student Guardian",
        filters={"parent": student},
        fields=["guardian", "relation"]
    )
    
    result = []
    for g in guardians:
        try:
            guardian_doc = frappe.get_doc("Guardian", g.guardian)
            result.append({
                "guardian": g.guardian,
                "guardian_name": guardian_doc.guardian_name,
                "relation": g.relation,
                "email": guardian_doc.email_address,
                "mobile": guardian_doc.mobile_number,
            })
        except Exception:
            pass
    
    return result


def render_email_template(template_name, context):
    """
    Render an email template with the given context.
    Automatically adds school info to context.
    """
    school_info = get_school_info()
    context.update(school_info)
    
    return frappe.render_template(
        f"nl_school/templates/emails/{template_name}.html",
        context
    )


def send_school_email(recipients, subject, template_name, context, 
                      cc=None, bcc=None, attachments=None, send_now=True):
    """
    Send a school-branded email using a template.
    
    Args:
        recipients: Email address or list of email addresses
        subject: Email subject
        template_name: Template filename (without .html extension)
        context: Dict of template variables
        cc: CC recipients
        bcc: BCC recipients
        attachments: List of file attachments
        send_now: If True, send immediately; if False, queue
    """
    if isinstance(recipients, str):
        recipients = [recipients]
    
    recipients = [r for r in recipients if r]
    if not recipients:
        return
    
    message = render_email_template(template_name, context)
    
    frappe.sendmail(
        recipients=recipients,
        cc=cc,
        bcc=bcc,
        subject=subject,
        message=message,
        attachments=attachments,
        now=send_now,
    )


# =============================================================================
# Notification Functions - Called from doc_events or manually
# =============================================================================

def send_welcome_email(student, guardian_email=None, temporary_password=None):
    """Send welcome email to parent/guardian when student is created."""
    student_doc = frappe.get_doc("Student", student)
    guardians = get_student_guardians(student)
    
    recipients = []
    guardian_name = ""
    
    if guardian_email:
        recipients.append(guardian_email)
    else:
        for g in guardians:
            if g.get("email"):
                recipients.append(g["email"])
                if not guardian_name:
                    guardian_name = g.get("guardian_name", "")
    
    if not recipients:
        return
    
    student_name = student_doc.student_name or student
    login_url = f"{frappe.utils.get_url()}/login"
    
    context = {
        "student_name": student_name,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "email": guardian_email or (guardians[0]["email"] if guardians else ""),
        "temporary_password": temporary_password,
        "login_url": login_url,
    }
    
    send_school_email(
        recipients=recipients,
        subject=f"Welcome to {get_school_info()['school_name']}!",
        template_name="welcome",
        context=context,
    )


def send_application_received_email(application_name):
    """Send confirmation when a student application is submitted."""
    app = frappe.get_doc("Student Applicant", application_name)
    
    if not app.email_id:
        return
    
    guardians = get_student_guardians(app.student) if app.student else []
    guardian_name = ""
    if guardians:
        guardian_name = guardians[0].get("guardian_name", "")
    
    context = {
        "student_name": app.student_name or "Applicant",
        "guardian_name": guardian_name or app.parent_guardian_name or "Parent",
        "parent_name": guardian_name or app.parent_guardian_name or "Parent",
        "program": app.program,
        "academic_year": app.academic_year,
        "application_date": app.application_date or nowdate(),
        "application_name": app.name,
        "portal_url": f"{frappe.utils.get_url()}/desk/student-applicant/{app.name}",
    }
    
    send_school_email(
        recipients=[app.email_id],
        subject=f"Application Received - {app.student_name or 'Applicant'}",
        template_name="application_received",
        context=context,
    )


def send_application_status_email(application_name, status, reason=None):
    """Send application status update (accepted/rejected/waitlisted)."""
    app = frappe.get_doc("Student Applicant", application_name)
    
    if not app.email_id:
        return
    
    context = {
        "student_name": app.student_name or "Applicant",
        "guardian_name": app.parent_guardian_name or "Parent",
        "parent_name": app.parent_guardian_name or "Parent",
        "program": app.program,
        "academic_year": app.academic_year,
        "status": status,
        "rejection_reason": reason,
        "application_name": app.name,
        "portal_url": f"{frappe.utils.get_url()}/desk/student-applicant/{app.name}",
        "enrollment_url": f"{frappe.utils.get_url()}/desk/program-enrollment/new" if status in ["Approved", "Accepted"] else None,
    }
    
    status_labels = {
        "Approved": "Approved",
        "Accepted": "Accepted",
        "Rejected": "Not Accepted",
        "Denied": "Not Accepted",
        "Waitlisted": "Waitlisted",
    }
    
    send_school_email(
        recipients=[app.email_id],
        subject=f"Application {status_labels.get(status, status)} - {app.student_name or 'Applicant'}",
        template_name="application_status",
        context=context,
    )


def send_enrollment_confirmation_email(enrollment_name):
    """Send enrollment confirmation to parent/guardian."""
    enrollment = frappe.get_doc("Program Enrollment", enrollment_name)
    guardians = get_student_guardians(enrollment.student)
    
    recipients = []
    guardian_name = ""
    for g in guardians:
        if g.get("email"):
            recipients.append(g["email"])
            if not guardian_name:
                guardian_name = g.get("guardian_name", "")
    
    if not recipients:
        return
    
    context = {
        "student_name": enrollment.student_name or enrollment.student,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "program": enrollment.program,
        "student_group": enrollment.student_group_name,
        "academic_year": enrollment.academic_year,
        "academic_term": enrollment.academic_term,
        "enrollment_date": enrollment.enrollment_date or nowdate(),
        "portal_url": f"{frappe.utils.get_url()}/desk/program-enrollment/{enrollment.name}",
    }
    
    send_school_email(
        recipients=recipients,
        subject=f"Enrollment Confirmed - {enrollment.student_name}",
        template_name="enrollment_confirmation",
        context=context,
    )


def send_absent_alert_email(student, date, reason=None, absent_days_count=1):
    """Send absence alert to parent/guardian."""
    guardians = get_student_guardians(student)
    
    recipients = []
    guardian_name = ""
    student_group = ""
    
    for g in guardians:
        if g.get("email"):
            recipients.append(g["email"])
            if not guardian_name:
                guardian_name = g.get("guardian_name", "")
    
    if not recipients:
        return
    
    # Get student's primary student group
    student_groups = frappe.get_all(
        "Student Group Student",
        filters={"student": student, "active": 1},
        fields=["parent"],
        limit=1
    )
    if student_groups:
        student_group = frappe.db.get_value("Student Group", student_groups[0].parent, "student_group_name")
    
    student_name = frappe.db.get_value("Student", student, "student_name") or student
    
    context = {
        "student_name": student_name,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "student_group": student_group,
        "date": date,
        "reason": reason,
        "absent_days_count": absent_days_count,
        "portal_url": f"{frappe.utils.get_url()}/desk/student-attendance?student={student}",
        "leave_application_url": f"{frappe.utils.get_url()}/desk/student-leave-application/new",
    }
    
    subject = f"Absence Alert - {student_name} ({date})"
    if absent_days_count > 1:
        subject = f"URGENT: {student_name} absent for {absent_days_count} days"
    
    send_school_email(
        recipients=recipients,
        subject=subject,
        template_name="absent_alert",
        context=context,
    )


def send_low_attendance_warning(student, attendance_percentage, days_present, 
                                total_days, days_absent, min_required=75):
    """Send low attendance warning to parent/guardian."""
    guardians = get_student_guardians(student)
    
    recipients = []
    guardian_name = ""
    student_group = ""
    
    for g in guardians:
        if g.get("email"):
            recipients.append(g["email"])
            if not guardian_name:
                guardian_name = g.get("guardian_name", "")
    
    if not recipients:
        return
    
    student_groups = frappe.get_all(
        "Student Group Student",
        filters={"student": student, "active": 1},
        fields=["parent"],
        limit=1
    )
    if student_groups:
        student_group = frappe.db.get_value("Student Group", student_groups[0].parent, "student_group_name")
    
    student_name = frappe.db.get_value("Student", student, "student_name") or student
    
    context = {
        "student_name": student_name,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "student_group": student_group,
        "attendance_percentage": round(attendance_percentage, 1),
        "min_required_percentage": min_required,
        "days_present": days_present,
        "total_days": total_days,
        "days_absent": days_absent,
        "portal_url": f"{frappe.utils.get_url()}/desk/student-attendance?student={student}",
    }
    
    send_school_email(
        recipients=recipients,
        subject=f"Low Attendance Warning - {student_name} ({attendance_percentage:.1f}%)",
        template_name="low_attendance_warning",
        context=context,
    )


def send_exam_schedule_email(student_group, assessment_plan_name):
    """Send exam schedule notification to parents of students in a group."""
    plan = frappe.get_doc("Assessment Plan", assessment_plan_name)
    
    # Get all students in the group
    students = frappe.get_all(
        "Student Group Student",
        filters={"parent": student_group, "active": 1},
        fields=["student"]
    )
    
    for student_entry in students:
        guardians = get_student_guardians(student_entry.student)
        recipients = []
        guardian_name = ""
        
        for g in guardians:
            if g.get("email"):
                recipients.append(g["email"])
                if not guardian_name:
                    guardian_name = g.get("guardian_name", "")
        
        if not recipients:
            continue
        
        student_name = frappe.db.get_value("Student", student_entry.student, "student_name")
        sg_name = frappe.db.get_value("Student Group", student_group, "student_group_name")
        
        context = {
            "student_name": student_name or student_entry.student,
            "guardian_name": guardian_name,
            "parent_name": guardian_name,
            "student_group": sg_name,
            "program": plan.program,
            "assessment_name": plan.assessment_name or plan.course,
            "academic_term": plan.academic_term,
            "exam_schedule": [],
            "timetable_url": f"{frappe.utils.get_url()}/desk/education-timetable",
        }
        
        send_school_email(
            recipients=recipients,
            subject=f"Upcoming Exam Reminder - {student_name}",
            template_name="exam_schedule_reminder",
            context=context,
        )


def send_results_published_email(student, assessment_plan_name):
    """Send results published notification to parent/guardian."""
    guardians = get_student_guardians(student)
    
    recipients = []
    guardian_name = ""
    for g in guardians:
        if g.get("email"):
            recipients.append(g["email"])
            if not guardian_name:
                guardian_name = g.get("guardian_name", "")
    
    if not recipients:
        return
    
    student_name = frappe.db.get_value("Student", student, "student_name") or student
    
    plan = frappe.get_doc("Assessment Plan", assessment_plan_name)
    sg_name = ""
    student_groups = frappe.get_all(
        "Student Group Student",
        filters={"student": student, "active": 1},
        fields=["parent"],
        limit=1
    )
    if student_groups:
        sg_name = frappe.db.get_value("Student Group", student_groups[0].parent, "student_group_name")
    
    context = {
        "student_name": student_name,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "student_group": sg_name,
        "program": plan.program,
        "assessment_name": plan.assessment_name or plan.course,
        "academic_term": plan.academic_term,
        "academic_year": plan.academic_year,
        "report_card_url": f"{frappe.utils.get_url()}/desk/student-report-generation-tool?student={student}",
        "portal_url": f"{frappe.utils.get_url()}/desk",
    }
    
    send_school_email(
        recipients=recipients,
        subject=f"Results Published - {student_name}",
        template_name="results_published",
        context=context,
    )


def send_payment_receipt_email(customer, amount, transaction_id=None, 
                               invoice_number=None, payment_method="Online Payment"):
    """Send payment receipt after successful payment."""
    customer_name = frappe.db.get_value("Customer", customer, "customer_name") or customer
    
    # Try to find linked student
    student = frappe.db.get_value("Student", {"customer": customer}, "name")
    student_name = ""
    if student:
        student_name = frappe.db.get_value("Student", student, "student_name") or ""
    
    # Get guardian emails
    guardians = []
    if student:
        guardians = get_student_guardians(student)
    
    recipients = []
    guardian_name = ""
    
    # Try guardian emails first
    for g in guardians:
        if g.get("email"):
            recipients.append(g["email"])
            if not guardian_name:
                guardian_name = g.get("guardian_name", "")
    
    # Fallback to customer email
    if not recipients:
        cust_email = frappe.db.get_value("Customer", customer, "email_id")
        if cust_email:
            recipients.append(cust_email)
    
    if not recipients:
        return
    
    school_info = get_school_info()
    
    context = {
        "student_name": student_name or customer_name,
        "customer_name": customer_name,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "amount": amount,
        "currency": school_info["currency"],
        "transaction_id": transaction_id,
        "invoice_number": invoice_number,
        "payment_method": payment_method,
        "payment_date": nowdate(),
        "outstanding_amount": 0,
        "receipt_url": f"{frappe.utils.get_url()}/paystack-success/{transaction_id}" if transaction_id else None,
        "portal_url": f"{frappe.utils.get_url()}/desk",
    }
    
    send_school_email(
        recipients=recipients,
        subject=f"Payment Receipt - {school_info['currency']} {amount:,.2f}",
        template_name="payment_receipt",
        context=context,
    )


def send_fee_invoice_email(invoice_name):
    """Send fee invoice to parent/guardian."""
    invoice = frappe.get_doc("Sales Invoice", invoice_name)
    
    # Find linked student
    student = frappe.db.get_value("Student", {"customer": invoice.customer}, "name")
    student_name = ""
    if student:
        student_name = frappe.db.get_value("Student", student, "student_name") or ""
    
    guardians = get_student_guardians(student) if student else []
    
    recipients = []
    guardian_name = ""
    for g in guardians:
        if g.get("email"):
            recipients.append(g["email"])
            if not guardian_name:
                guardian_name = g.get("guardian_name", "")
    
    if not recipients:
        cust_email = frappe.db.get_value("Customer", invoice.customer, "email_id")
        if cust_email:
            recipients.append(cust_email)
    
    if not recipients:
        return
    
    school_info = get_school_info()
    
    # Get fee components
    fee_components = frappe.get_all(
        "Fee Component",
        filters={"parent": invoice_name},
        fields=["fees_category as description", "amount"]
    )
    
    context = {
        "student_name": student_name or invoice.customer_name,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "student_group": "",
        "program": "",
        "invoice_number": invoice_name,
        "invoice_date": invoice.posting_date,
        "due_date": invoice.due_date,
        "total_amount": invoice.grand_total,
        "amount_due": invoice.outstanding_amount,
        "already_paid": invoice.grand_total - invoice.outstanding_amount,
        "currency": school_info["currency"],
        "fee_components": fee_components,
        "payment_url": None,
        "portal_url": f"{frappe.utils.get_url()}/desk",
    }
    
    send_school_email(
        recipients=recipients,
        subject=f"Fee Invoice - {invoice_name}",
        template_name="fee_invoice",
        context=context,
    )


def send_overdue_escalation_email(student, outstanding_amount, due_date, 
                                  invoice_number=None, days_overdue=None):
    """Send overdue fee escalation email."""
    guardians = get_student_guardians(student)
    
    recipients = []
    guardian_name = ""
    student_group = ""
    
    for g in guardians:
        if g.get("email"):
            recipients.append(g["email"])
            if not guardian_name:
                guardian_name = g.get("guardian_name", "")
    
    if not recipients:
        return
    
    student_name = frappe.db.get_value("Student", student, "student_name") or student
    
    student_groups = frappe.get_all(
        "Student Group Student",
        filters={"student": student, "active": 1},
        fields=["parent"],
        limit=1
    )
    if student_groups:
        student_group = frappe.db.get_value("Student Group", student_groups[0].parent, "student_group_name")
    
    if not days_overdue:
        days_overdue = (getdate(nowdate()) - getdate(due_date)).days
    
    school_info = get_school_info()
    
    context = {
        "student_name": student_name,
        "guardian_name": guardian_name,
        "parent_name": guardian_name,
        "student_group": student_group,
        "outstanding_amount": outstanding_amount,
        "due_date": due_date,
        "days_overdue": days_overdue,
        "invoice_number": invoice_number,
        "currency": school_info["currency"],
        "payment_url": None,
        "installment_option": True,
        "fee_breakdown": [],
    }
    
    send_school_email(
        recipients=recipients,
        subject=f"URGENT: Overdue Fees - {student_name} ({days_overdue} days overdue)",
        template_name="overdue_escalation",
        context=context,
    )
