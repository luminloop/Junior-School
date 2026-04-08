import frappe
from frappe.utils import today, now_datetime


@frappe.whitelist()
def check_role():
    """Check if user is a teacher and should be redirected"""
    if "Instructor" in frappe.get_roles() and "Education Manager" not in frappe.get_roles():
        return "teacher"
    return "other"


@frappe.whitelist()
def get_dashboard_data():
    """Get dashboard data for school"""
    
    # Get current academic year - check for is_current or is_active based on available field
    academic_year = frappe.db.get_value("Academic Year", {"is_current": 1}, "name")
    
    if not academic_year:
        # Try getting the most recent one
        academic_year = frappe.db.get_value("Academic Year", order_by="year_start_date DESC", limit=1)
    
    if not academic_year:
        return {
            "students": 0,
            "teachers": 0,
            "programs": 0,
            "enrollments": 0
        }
    
    # Student count
    students = frappe.db.count("Student", {"academic_year": academic_year})
    
    # Teacher/Instructor count
    teachers = frappe.db.count("Instructor", {"enabled": 1})
    
    # Program count - check for is_active or enabled based on available field
    programs = frappe.db.count("Program", {"enabled": 1})
    
    # Enrollment count
    enrollments = frappe.db.count("Program Enrollment", {"academic_year": academic_year})
    
    return {
        "students": students or 0,
        "teachers": teachers or 0,
        "programs": programs or 0,
        "enrollments": enrollments or 0
    }
