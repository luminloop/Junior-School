import frappe
from frappe.utils import today, now_datetime, add_days, getdate


@frappe.whitelist()
def check_role():
    """Check if user is a teacher and should be redirected"""
    if "Instructor" in frappe.get_roles() and "Education Manager" not in frappe.get_roles():
        return "teacher"
    return "other"


@frappe.whitelist()
def get_dashboard_data():
    """Get dashboard data for school"""
    
    # Get most recent academic year based on start date
    latest_year = frappe.get_all(
        "Academic Year", fields=["name"], order_by="year_start_date DESC", limit=1
    )
    academic_year = latest_year[0].name if latest_year else None
    
    if not academic_year:
        return {
            "stats": {
                "total_students": 0,
                "total_teachers": 0,
                "new_students_month": 0,
                "attendance_rate": 0,
                "present_today": 0,
                "pending_invoices": 0
            },
            "attendance_trend": [],
            "recent_activity": [],
            "alerts": []
        }
    
    # Student count (use Program Enrollment for academic year)
    total_students = frappe.db.count("Program Enrollment", {"academic_year": academic_year})
    
    # Teacher/Instructor count (no 'enabled' field in this Frappe version)
    total_teachers = frappe.db.count("Instructor")
    
    # New students this month
    month_start = getdate(today()).replace(day=1)
    new_students_month = frappe.db.count(
        "Program Enrollment", 
        {"academic_year": academic_year, "enrollment_date": [">=", month_start]}
    )
    
    # Today's attendance
    attendance_today = frappe.get_all(
        "Student Attendance",
        filters={"date": today()},
        fields=["status"]
    )
    present_today = sum(1 for a in attendance_today if a.status == "Present")
    total_today = len(attendance_today)
    attendance_rate = round((present_today / total_today * 100) if total_today > 0 else 0)
    
    # Pending invoices
    pending_invoices = frappe.db.count(
        "Sales Invoice",
        {"status": ["in", ["Unpaid", "Overdue"]], "docstatus": 1}
    )
    
    # Attendance trend (last 7 days)
    attendance_trend = []
    for i in range(6, -1, -1):
        date = add_days(today(), -i)
        day_attendance = frappe.get_all(
            "Student Attendance",
            filters={"date": date},
            fields=["status"]
        )
        present = sum(1 for a in day_attendance if a.status == "Present")
        absent = sum(1 for a in day_attendance if a.status == "Absent")
        attendance_trend.append({
            "date": str(date),
            "present": present,
            "absent": absent
        })
    
    # Recent activity (last 10 activities)
    recent_activity = []
    
    # Get recent enrollments
    recent_enrollments = frappe.get_all(
        "Program Enrollment",
        filters={"academic_year": academic_year},
        fields=["student_name", "program", "creation"],
        order_by="creation desc",
        limit=5
    )
    for enrollment in recent_enrollments:
        recent_activity.append({
            "message": f"{enrollment.student_name} enrolled in {enrollment.program}",
            "time": enrollment.creation
        })
    
    # Get recent attendance submissions
    recent_attendance = frappe.get_all(
        "Student Attendance",
        fields=["student_name", "status", "date", "creation"],
        order_by="creation desc",
        limit=5
    )
    for att in recent_attendance:
        recent_activity.append({
            "message": f"{att.student_name} marked {att.status}",
            "time": att.creation
        })
    
    # Sort by time and take top 10
    recent_activity.sort(key=lambda x: x.get("time") or "", reverse=True)
    recent_activity = recent_activity[:10]
    
    # Alerts
    alerts = []
    
    # Check for students with low attendance (example)
    if attendance_rate < 80 and total_today > 0:
        alerts.append({
            "type": "warning",
            "message": f"Today's attendance is {attendance_rate}%",
            "link": "/app/student-attendance"
        })
    
    # Check for pending invoices
    if pending_invoices > 0:
        alerts.append({
            "type": "warning",
            "message": f"{pending_invoices} pending invoice(s)",
            "link": "/app/sales-invoice?status=Unpaid"
        })
    
    return {
        "stats": {
            "total_students": total_students or 0,
            "total_teachers": total_teachers or 0,
            "new_students_month": new_students_month or 0,
            "attendance_rate": attendance_rate,
            "present_today": present_today,
            "pending_invoices": pending_invoices or 0
        },
        "attendance_trend": attendance_trend,
        "recent_activity": recent_activity,
        "alerts": alerts
    }
