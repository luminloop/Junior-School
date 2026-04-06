# Copyright (c) 2024, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def sync_instructor_user_permissions(doc, method=None):
    """
    Sync User Permissions for instructors when they are assigned to Student Groups.
    Called on Student Group save.
    
    This ensures teachers can only see:
    - Students in their assigned student groups
    - Assessment results for their student groups
    - Attendance for their student groups
    """
    # Get all instructors assigned to this student group
    for instructor_row in doc.get("instructors", []):
        instructor = instructor_row.instructor
        sync_permissions_for_instructor(instructor, doc.name)


def sync_permissions_for_instructor(instructor_name, student_group):
    """
    Create User Permissions for an instructor to access a specific student group.
    """
    # Get the user linked to this instructor
    instructor_doc = frappe.get_doc("Instructor", instructor_name)
    
    # Find user via Employee link
    user = None
    if instructor_doc.employee:
        user = frappe.db.get_value("Employee", instructor_doc.employee, "user_id")
    
    if not user:
        return
    
    # Check if user has Instructor role
    if not frappe.db.exists("Has Role", {"parent": user, "role": "Instructor"}):
        return
    
    # Create User Permission for Student Group if not exists
    if not frappe.db.exists("User Permission", {
        "user": user,
        "allow": "Student Group",
        "for_value": student_group
    }):
        frappe.get_doc({
            "doctype": "User Permission",
            "user": user,
            "allow": "Student Group",
            "for_value": student_group,
            "apply_to_all_doctypes": 0,
            "applicable_for": "",
            "is_default": 0
        }).insert(ignore_permissions=True)


def remove_instructor_permissions_on_removal(doc, method=None):
    """
    Remove User Permissions when instructor is removed from a student group.
    Called before Student Group save to detect removed instructors.
    """
    if doc.is_new():
        return
    
    # Get previous instructors
    previous_doc = doc.get_doc_before_save()
    if not previous_doc:
        return
    
    previous_instructors = {i.instructor for i in previous_doc.get("instructors", [])}
    current_instructors = {i.instructor for i in doc.get("instructors", [])}
    
    removed_instructors = previous_instructors - current_instructors
    
    for instructor_name in removed_instructors:
        remove_permissions_for_instructor(instructor_name, doc.name)


def remove_permissions_for_instructor(instructor_name, student_group):
    """
    Remove User Permission for an instructor for a specific student group.
    """
    instructor_doc = frappe.get_doc("Instructor", instructor_name)
    
    user = None
    if instructor_doc.employee:
        user = frappe.db.get_value("Employee", instructor_doc.employee, "user_id")
    
    if not user:
        return
    
    # Delete the User Permission
    frappe.db.delete("User Permission", {
        "user": user,
        "allow": "Student Group",
        "for_value": student_group
    })


def setup_instructor_user_on_create(doc, method=None):
    """
    When an Employee is linked to an Instructor and has a user_id,
    automatically assign the Instructor role.
    Called on Instructor save.
    """
    if not doc.employee:
        return
    
    user_id = frappe.db.get_value("Employee", doc.employee, "user_id")
    if not user_id:
        return
    
    # Check if user already has Instructor role
    if frappe.db.exists("Has Role", {"parent": user_id, "role": "Instructor"}):
        return
    
    # Add Instructor role to user
    user = frappe.get_doc("User", user_id)
    user.append("roles", {"role": "Instructor"})
    user.save(ignore_permissions=True)
    frappe.db.commit()


@frappe.whitelist()
def get_instructor_student_groups(user=None):
    """
    Get list of student groups assigned to the current instructor.
    Useful for filtering in list views.
    """
    if not user:
        user = frappe.session.user

    # Find employee linked to this user
    # Use ignore_permissions because User Permissions may block Employee access
    employees = frappe.get_all(
        "Employee",
        filters={"user_id": user},
        pluck="name",
        ignore_permissions=True,
    )

    if not employees:
        return []

    instructors = frappe.get_all(
        "Instructor",
        filters={"employee": ["in", employees]},
        pluck="name",
        ignore_permissions=True,
    )

    if not instructors:
        return []

    # Get student groups where this instructor is assigned
    student_groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor": ["in", instructors]},
        pluck="parent",
        ignore_permissions=True,
    )

    return list(set(student_groups))


@frappe.whitelist()
def get_instructor_students(user=None):
    """
    Get list of students in the student groups assigned to the current instructor.
    """
    student_groups = get_instructor_student_groups(user)

    if not student_groups:
        return []

    students = frappe.get_all(
        "Student Group Student",
        filters={"parent": ["in", student_groups], "active": 1},
        pluck="student",
        ignore_permissions=True,
    )

    return list(set(students))
