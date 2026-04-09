# Copyright (c) 2026, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from jinja2 import Template


class SchoolEmailTemplate(Document):
    def validate(self):
        if self.is_default and self.template_type:
            # Unset other defaults for the same type and company
            filters = {
                "is_default": 1, 
                "name": ["!=", self.name],
                "template_type": self.template_type
            }
            if self.company:
                filters["company"] = self.company
            else:
                filters["company"] = ["is", "not set"]
            
            frappe.db.set_value(
                "School Email Template",
                filters,
                "is_default",
                0
            )


def get_default_template(template_type, company=None):
    """Get the default email template for a type and company."""
    filters = {"is_default": 1, "disabled": 0, "template_type": template_type}
    
    # First try to find company-specific template
    if company:
        filters["company"] = company
        template = frappe.db.get_value("School Email Template", filters, "name")
        if template:
            return template
    
    # Fall back to global default (no company set)
    filters["company"] = ["is", "not set"]
    template = frappe.db.get_value("School Email Template", filters, "name")
    
    return template


def render_email_template(template_name, context=None):
    """Render an email template with the given context."""
    if not template_name:
        return None, None
    
    template = frappe.get_doc("School Email Template", template_name)
    context = context or {}
    
    subject_tmpl = Template(template.subject)
    message_tmpl = Template(template.message)
    
    subject = subject_tmpl.render(**context)
    message = message_tmpl.render(**context)
    
    return subject, message


@frappe.whitelist()
def get_templates_by_type(template_type):
    """Get all templates of a specific type."""
    return frappe.get_all(
        "School Email Template",
        filters={"template_type": template_type, "disabled": 0},
        fields=["name", "template_name", "is_default", "company"]
    )


@frappe.whitelist()
def preview_template(template_name):
    """Preview a template with sample data."""
    template = frappe.get_doc("School Email Template", template_name)
    
    # Sample data for preview
    sample_context = {
        "student_name": "John Doe",
        "student": "STU-0001",
        "guardian_name": "Jane Doe",
        "company": "Sample School",
        "academic_year": "2025-2026",
        "academic_term": "Term 1",
        "program": "Grade 5",
        "total_score": "85",
        "grade": "A",
        "rank": "3",
        "class_teacher": "Mr. Smith",
        "attendance_date": "2026-04-09",
        "status": "Present",
        "amount_due": "5,000",
        "due_date": "2026-04-30"
    }
    
    subject = Template(template.subject).render(**sample_context)
    message = Template(template.message).render(**sample_context)
    
    return {
        "subject": subject,
        "message": message
    }
