import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    create_scholarship_manager_role()
    create_assessment_result_custom_fields()


def create_scholarship_manager_role():
    if not frappe.db.exists("Role", "Scholarship Manager"):
        frappe.get_doc(
            {"doctype": "Role", "role_name": "Scholarship Manager", "desk_access": 1}
        ).save()


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
