import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate, flt


@frappe.whitelist()
def get_dashboard_data():
    """Get all dashboard data in a single API call"""
    return {
        "stats": get_stats(),
        "attendance_trend": get_attendance_trend(),
        "enrollment_by_program": get_enrollment_by_program(),
        "alerts": get_alerts(),
        "recent_activity": get_recent_activity(),
    }


@frappe.whitelist()
def get_stats():
    """Get summary statistics for the dashboard cards"""
    today = nowdate()
    
    # Total active students
    total_students = frappe.db.count("Student", {"enabled": 1})
    
    # Total active teachers
    total_teachers = frappe.db.count("Instructor", {"status": "Active"})
    
    # Today's attendance
    total_attendance_today = frappe.db.count("Student Attendance", {"date": today})
    present_today = frappe.db.count("Student Attendance", {"date": today, "status": "Present"})
    attendance_rate = round((present_today / total_attendance_today * 100), 1) if total_attendance_today > 0 else 0
    
    # Pending fee invoices
    pending_invoices = frappe.db.count("Sales Invoice", {
        "docstatus": 1,
        "status": ["in", ["Unpaid", "Overdue", "Partly Paid"]]
    })
    
    # Outstanding amount
    outstanding_amount = frappe.db.sql("""
        SELECT COALESCE(SUM(outstanding_amount), 0) as total
        FROM `tabSales Invoice`
        WHERE docstatus = 1 AND outstanding_amount > 0
    """, as_dict=True)[0].get("total", 0)
    
    # New students this month
    first_of_month = getdate(today).replace(day=1)
    new_students_month = frappe.db.count("Student", {
        "enabled": 1,
        "creation": [">=", first_of_month]
    })
    
    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "present_today": present_today,
        "attendance_rate": attendance_rate,
        "pending_invoices": pending_invoices,
        "outstanding_amount": flt(outstanding_amount, 2),
        "new_students_month": new_students_month,
    }


@frappe.whitelist()
def get_attendance_trend():
    """Get attendance data for the last 7 days"""
    today = getdate(nowdate())
    data = []
    
    for i in range(6, -1, -1):
        date = add_days(today, -i)
        
        present = frappe.db.count("Student Attendance", {"date": date, "status": "Present"})
        absent = frappe.db.count("Student Attendance", {"date": date, "status": "Absent"})
        leave = frappe.db.count("Student Attendance", {"date": date, "status": "Leave"})
        
        data.append({
            "date": date.strftime("%a"),  # Mon, Tue, etc.
            "full_date": str(date),
            "present": present,
            "absent": absent,
            "leave": leave,
            "total": present + absent + leave
        })
    
    return data


@frappe.whitelist()
def get_enrollment_by_program():
    """Get student count by program/class"""
    data = frappe.db.sql("""
        SELECT 
            p.program_name as program,
            COUNT(pe.name) as count
        FROM `tabProgram Enrollment` pe
        INNER JOIN `tabProgram` p ON pe.program = p.name
        INNER JOIN `tabStudent` s ON pe.student = s.name
        WHERE s.enabled = 1
        GROUP BY pe.program
        ORDER BY count DESC
        LIMIT 10
    """, as_dict=True)
    
    return data


@frappe.whitelist()
def get_alerts():
    """Get items that need attention"""
    today = nowdate()
    alerts = []
    
    # Students absent 3+ consecutive days
    # Simplified: students absent today who were also absent yesterday
    frequently_absent = frappe.db.sql("""
        SELECT COUNT(DISTINCT sa1.student) as count
        FROM `tabStudent Attendance` sa1
        INNER JOIN `tabStudent Attendance` sa2 ON sa1.student = sa2.student
        WHERE sa1.status = 'Absent' 
        AND sa2.status = 'Absent'
        AND sa1.date = %s
        AND sa2.date = %s
    """, (today, add_days(today, -1)), as_dict=True)
    
    if frequently_absent and frequently_absent[0].count > 0:
        alerts.append({
            "type": "warning",
            "icon": "user-x",
            "message": f"{frequently_absent[0].count} students absent multiple days",
            "link": "/desk/student-attendance?status=Absent"
        })
    
    # Overdue invoices
    overdue_count = frappe.db.count("Sales Invoice", {
        "docstatus": 1,
        "status": "Overdue"
    })
    if overdue_count > 0:
        alerts.append({
            "type": "danger",
            "icon": "alert-circle",
            "message": f"{overdue_count} overdue invoices",
            "link": "/desk/sales-invoice?status=Overdue"
        })
    
    # Pending applications
    pending_applications = frappe.db.count("Student Applicant", {
        "application_status": "Applied"
    })
    if pending_applications > 0:
        alerts.append({
            "type": "info",
            "icon": "user-plus",
            "message": f"{pending_applications} pending applications",
            "link": "/desk/student-applicant?application_status=Applied"
        })
    
    # Upcoming assessments (next 7 days)
    upcoming_assessments = frappe.db.count("Assessment Plan", {
        "schedule_date": ["between", [today, add_days(today, 7)]],
        "docstatus": ["<", 2]
    })
    if upcoming_assessments > 0:
        alerts.append({
            "type": "info",
            "icon": "calendar",
            "message": f"{upcoming_assessments} assessments this week",
            "link": "/desk/assessment-plan"
        })
    
    return alerts


@frappe.whitelist()
def get_recent_activity():
    """Get recent activity/changes"""
    activities = []
    
    # Recent enrollments
    recent_enrollments = frappe.db.sql("""
        SELECT 
            pe.student_name,
            p.program_name as program,
            pe.creation
        FROM `tabProgram Enrollment` pe
        INNER JOIN `tabProgram` p ON pe.program = p.name
        ORDER BY pe.creation DESC
        LIMIT 3
    """, as_dict=True)
    
    for enrollment in recent_enrollments:
        activities.append({
            "icon": "user-plus",
            "message": f"{enrollment.student_name} enrolled in {enrollment.program}",
            "time": enrollment.creation,
            "link": f"/desk/program-enrollment?student_name={enrollment.student_name}"
        })
    
    # Recent fee payments
    recent_payments = frappe.db.sql("""
        SELECT 
            si.customer_name,
            si.grand_total,
            si.currency,
            pe.creation
        FROM `tabPayment Entry` pe
        INNER JOIN `tabPayment Entry Reference` per ON pe.name = per.parent
        INNER JOIN `tabSales Invoice` si ON per.reference_name = si.name
        WHERE pe.docstatus = 1
        ORDER BY pe.creation DESC
        LIMIT 3
    """, as_dict=True)
    
    for payment in recent_payments:
        activities.append({
            "icon": "banknote",
            "message": f"Payment received from {payment.customer_name}",
            "time": payment.creation,
            "link": "/desk/payment-entry"
        })
    
    # Sort by time and limit
    activities.sort(key=lambda x: x["time"], reverse=True)
    
    return activities[:5]


@frappe.whitelist()
def get_gender_distribution():
    """Get student count by gender"""
    data = frappe.db.sql("""
        SELECT 
            COALESCE(gender, 'Not Specified') as gender,
            COUNT(*) as count
        FROM `tabStudent`
        WHERE enabled = 1
        GROUP BY gender
    """, as_dict=True)
    
    return data
