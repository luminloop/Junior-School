import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    create_scholarship_manager_role()
    create_school_hierarchy_roles()
    setup_role_permissions()
    create_assessment_result_custom_fields()


def create_scholarship_manager_role():
    if not frappe.db.exists("Role", "Scholarship Manager"):
        frappe.get_doc(
            {"doctype": "Role", "role_name": "Scholarship Manager", "desk_access": 1}
        ).save()


def create_school_hierarchy_roles():
    """
    Create the 3-tier school hierarchy roles:
    1. Principal - Top level, full admin access
    2. Academic Coordinator - Middle management, supervises teachers
    3. Instructor - Already exists in education app (teachers)
    """
    roles = [
        {
            "role_name": "Principal",
            "desk_access": 1,
            "is_custom": 1,
            "description": "School Principal - Full administrative access to all education modules"
        },
        {
            "role_name": "Academic Coordinator",
            "desk_access": 1,
            "is_custom": 1,
            "description": "Academic Coordinator - Supervises teachers, approves results, manages academic activities"
        },
    ]
    
    for role in roles:
        if not frappe.db.exists("Role", role["role_name"]):
            frappe.get_doc({"doctype": "Role", **role}).insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"Created role: {role['role_name']}")


def setup_role_permissions():
    """
    Set up permissions for the school hierarchy roles.
    
    Permission Levels:
    - Principal: Full access (like System Manager for education)
    - Academic Coordinator: Supervisory access (view all, approve, run reports)
    - Instructor: Teacher access (own classes only, enter marks, attendance)
    """
    
    # Principal permissions - Full access to all education doctypes
    principal_full_access = [
        "Student", "Student Group", "Student Applicant", "Student Admission",
        "Program Enrollment", "Guardian", "Student Leave Application",
        "Student Attendance", "Student Log", "Assessment Plan", "Assessment Result",
        "Assessment Group", "Assessment Criteria", "Assessment Criteria Group",
        "Grading Scale", "Course", "Course Schedule", "Program", "Academic Year",
        "Academic Term", "Instructor", "Fee Structure", "Fee Schedule", "Fees",
        "Fee Category", "Student Report Generation Tool", "Student Attendance Tool",
        "Assessment Result Tool", "Course Scheduling Tool", "Program Enrollment Tool",
        "Student Group Creation Tool", "Batch Report Card", "Grade Notification Tool",
        "Fee Notification Tool", "School House", "Topic", "Student Category",
        "Education Settings", "Timetable Generator", "Teaching Rooms", 
        "Enhanced Student Attendance Tool", "Student Transcript Tool",
    ]
    
    # Academic Coordinator permissions - Supervisory access
    coordinator_full_access = [
        "Student", "Student Group", "Student Applicant", "Program Enrollment",
        "Guardian", "Student Leave Application", "Student Attendance", "Student Log",
        "Assessment Plan", "Assessment Result", "Assessment Group", "Grading Scale",
        "Course", "Course Schedule", "Program", "Academic Year", "Academic Term",
        "Instructor", "Student Report Generation Tool", "Student Attendance Tool",
        "Assessment Result Tool", "Batch Report Card", "Grade Notification Tool",
        "School House", "Topic", "Student Category",
        "Enhanced Student Attendance Tool", "Student Transcript Tool",
    ]
    
    coordinator_read_only = [
        "Fee Structure", "Fee Schedule", "Fees", "Fee Category",
        "Education Settings", "Timetable Generator", "Teaching Rooms",
    ]
    
    # Instructor (Teacher) permissions - Limited to own work
    instructor_access = [
        "Student", "Student Group", "Course Schedule", "Assessment Plan",
        "Assessment Result", "Student Attendance", "Student Log", "Grading Scale",
        "Course", "Program", "Academic Year", "Academic Term", "School House",
    ]
    
    instructor_tools = [
        "Student Attendance Tool", "Assessment Result Tool",
        "Enhanced Student Attendance Tool", "Student Group",
    ]
    
    # Add Principal permissions
    for doctype in principal_full_access:
        add_permission_if_not_exists(doctype, "Principal", {
            "read": 1, "write": 1, "create": 1, "delete": 1,
            "submit": 1, "cancel": 1, "amend": 1, "report": 1,
            "export": 1, "import": 1, "print": 1, "email": 1, "share": 1
        })
    
    # Add Academic Coordinator permissions
    for doctype in coordinator_full_access:
        add_permission_if_not_exists(doctype, "Academic Coordinator", {
            "read": 1, "write": 1, "create": 1, "delete": 0,
            "submit": 1, "cancel": 1, "amend": 1, "report": 1,
            "export": 1, "print": 1, "email": 1, "share": 1
        })
    
    for doctype in coordinator_read_only:
        add_permission_if_not_exists(doctype, "Academic Coordinator", {
            "read": 1, "report": 1, "export": 1, "print": 1
        })
    
    # Add Instructor (Teacher) permissions
    for doctype in instructor_access:
        # Teachers get read access to most, write to specific ones
        perms = {"read": 1, "report": 1, "print": 1, "if_no_user_permissions": 1}
        if doctype in ["Assessment Result", "Student Attendance", "Student Log"]:
            perms.update({"write": 1, "create": 1, "submit": 1})
        add_permission_if_not_exists(doctype, "Instructor", perms)
    
    for doctype in instructor_tools:
        add_permission_if_not_exists(doctype, "Instructor", {
            "read": 1, "write": 1, "create": 1, "if_no_user_permissions": 1
        })
    
    frappe.db.commit()
    print("Role permissions setup completed")


def add_permission_if_not_exists(doctype, role, perms):
    """Add permission for a role on a doctype if it doesn't exist."""
    if not frappe.db.exists("DocType", doctype):
        return
    
    # Check if permission already exists
    existing = frappe.db.exists("Custom DocPerm", {
        "parent": doctype,
        "role": role
    })
    
    if not existing:
        # Also check in DocType's permissions
        doc = frappe.get_doc("DocType", doctype)
        role_exists = any(p.role == role for p in doc.permissions)
        
        if not role_exists:
            try:
                frappe.get_doc({
                    "doctype": "Custom DocPerm",
                    "parent": doctype,
                    "parenttype": "DocType",
                    "parentfield": "permissions",
                    "role": role,
                    **perms
                }).insert(ignore_permissions=True)
            except Exception as e:
                # If Custom DocPerm fails, try adding directly to DocType
                print(f"Note: Could not add permission for {role} on {doctype}: {e}")


def create_assessment_result_custom_fields():
    """Create custom fields for ranking and teacher comments on Assessment Result"""
    custom_fields = {
        "Assessment Result": [
            # Ranking fields
            {
                "fieldname": "ranking_section",
                "fieldtype": "Section Break",
                "label": "Ranking",
                "insert_after": "grade",
                "collapsible": 1,
            },
            {
                "fieldname": "class_rank",
                "fieldtype": "Int",
                "label": "Class Rank",
                "insert_after": "ranking_section",
                "read_only": 1,
                "description": "Rank within the student's class/student group",
            },
            {
                "fieldname": "class_total_students",
                "fieldtype": "Int",
                "label": "Class Total Students",
                "insert_after": "class_rank",
                "read_only": 1,
            },
            {
                "fieldname": "ranking_column_break",
                "fieldtype": "Column Break",
                "insert_after": "class_total_students",
            },
            {
                "fieldname": "grade_level_rank",
                "fieldtype": "Int",
                "label": "Grade Level Rank",
                "insert_after": "ranking_column_break",
                "read_only": 1,
                "description": "Rank within the entire grade/program",
            },
            {
                "fieldname": "grade_level_total_students",
                "fieldtype": "Int",
                "label": "Grade Level Total Students",
                "insert_after": "grade_level_rank",
                "read_only": 1,
            },
            # Subject Teacher Comments
            {
                "fieldname": "teacher_comments_section",
                "fieldtype": "Section Break",
                "label": "Subject Teacher Comments",
                "insert_after": "comment",
                "collapsible": 1,
            },
            {
                "fieldname": "subject_teacher_comments",
                "fieldtype": "Table",
                "label": "Subject Teacher Comments",
                "insert_after": "teacher_comments_section",
                "options": "Subject Teacher Comment",
                "description": "Comments from subject teachers to be printed on report card",
            },
        ]
    }
    create_custom_fields(custom_fields)
