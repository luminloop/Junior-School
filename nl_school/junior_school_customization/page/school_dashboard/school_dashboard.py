import frappe


@frappe.whitelist()
def check_role():
    """Check if user is a teacher and should be redirected"""
    if "Instructor" in frappe.get_roles() and "Education Manager" not in frappe.get_roles():
        return "teacher"
    return "other"
