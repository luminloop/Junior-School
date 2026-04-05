# Copyright (c) 2024, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import fmt_money, format_date, format_datetime, pretty_date


def jinja_methods():
    """
    Custom Jinja methods available in email templates and print formats.
    """
    return {
        "get_school_info": get_school_info,
        "get_student_guardians": get_student_guardians,
        "get_student_name": get_student_name,
        "get_guardian_name": get_guardian_name,
    }


def jinja_filters():
    """
    Custom Jinja filters available in email templates and print formats.
    """
    return {
        "format_money": format_money_filter,
        "format_date": format_date_filter,
        "format_datetime": format_datetime_filter,
        "pretty_date": pretty_date_filter,
        "to_json": to_json_filter,
    }


def get_school_info():
    """Get school branding info for templates."""
    settings = frappe.get_doc("Education Settings")
    company = None
    
    if settings.get("company"):
        try:
            company = frappe.get_doc("Company", settings.company)
        except Exception:
            pass
    
    return {
        "school_name": settings.get("school_name") or (company.company_name if company else "School"),
        "company_logo": company.company_logo if company else "",
        "company_address": company.address if company else "",
        "company_phone": company.phone_no if company else "",
        "company_email": company.email if company else "",
        "currency": company.default_currency if company else "KES",
    }


def get_student_guardians(student):
    """Get guardian info for a student."""
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


def get_student_name(student_id):
    """Get student name from ID."""
    return frappe.db.get_value("Student", student_id, "student_name") or student_id


def get_guardian_name(guardian_id):
    """Get guardian name from ID."""
    return frappe.db.get_value("Guardian", guardian_id, "guardian_name") or guardian_id


def format_money_filter(amount, currency=None):
    """Format money with currency symbol."""
    if not currency:
        currency = frappe.db.get_single_value("Education Settings", "company")
        if currency:
            currency = frappe.db.get_value("Company", currency, "default_currency") or "KES"
    return fmt_money(amount, currency=currency or "KES")


def format_date_filter(date_str, format_str=None):
    """Format date string."""
    if not date_str:
        return ""
    return format_date(date_str, format_str) if format_str else format_date(date_str)


def format_datetime_filter(datetime_str):
    """Format datetime string."""
    if not datetime_str:
        return ""
    return format_datetime(datetime_str)


def pretty_date_filter(datetime_str):
    """Convert datetime to relative time (e.g., '2 hours ago')."""
    if not datetime_str:
        return ""
    return pretty_date(datetime_str)


def to_json_filter(obj):
    """Convert object to JSON string."""
    import json
    try:
        return json.dumps(obj, default=str)
    except Exception:
        return ""
