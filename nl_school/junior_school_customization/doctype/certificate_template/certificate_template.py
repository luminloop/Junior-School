# Copyright (c) 2026, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from jinja2 import Template


class CertificateTemplate(Document):
    def validate(self):
        if self.is_default and self.certificate_type:
            # Unset other defaults for the same type and company
            filters = {
                "is_default": 1, 
                "name": ["!=", self.name],
                "certificate_type": self.certificate_type
            }
            if self.company:
                filters["company"] = self.company
            else:
                filters["company"] = ["is", "not set"]
            
            frappe.db.set_value(
                "Certificate Template",
                filters,
                "is_default",
                0
            )


def get_default_template(certificate_type, company=None):
    """Get the default certificate template for a type and company."""
    filters = {"is_default": 1, "disabled": 0, "certificate_type": certificate_type}
    
    # First try to find company-specific template
    if company:
        filters["company"] = company
        template = frappe.db.get_value("Certificate Template", filters, "name")
        if template:
            return template
    
    # Fall back to global default (no company set)
    filters["company"] = ["is", "not set"]
    template = frappe.db.get_value("Certificate Template", filters, "name")
    
    return template


def render_certificate(template_name, context=None):
    """Render a certificate template with the given context."""
    if not template_name:
        return None
    
    template = frappe.get_doc("Certificate Template", template_name)
    context = context or {}
    
    template_tmpl = Template(template.template_html)
    html = template_tmpl.render(**context)
    
    return {
        "html": html,
        "css": template.custom_css,
        "page_size": template.page_size,
        "orientation": template.orientation,
        "background_image": template.background_image
    }


@frappe.whitelist()
def get_templates_by_type(certificate_type):
    """Get all templates of a specific type."""
    return frappe.get_all(
        "Certificate Template",
        filters={"certificate_type": certificate_type, "disabled": 0},
        fields=["name", "template_name", "is_default", "company"]
    )


@frappe.whitelist()
def preview_template(template_name):
    """Preview a certificate template with sample data."""
    template = frappe.get_doc("Certificate Template", template_name)
    
    # Sample data for preview
    sample_context = {
        "student_name": "John Doe",
        "student": "STU-0001",
        "program": "Grade 5",
        "company": "Sample School",
        "company_logo": "/assets/frappe/images/default-logo.png",
        "academic_year": "2025-2026",
        "academic_term": "Term 1",
        "date": "April 9, 2026",
        "award_title": "Academic Excellence",
        "description": "For outstanding academic performance during the academic year.",
        "principal_name": "Dr. Jane Smith",
        "principal_signature": "",
        "class_teacher": "Mr. John Teacher",
        "rubber_stamp": "",
        "certificate_number": "CERT-2026-0001",
        "certificate_type": template.certificate_type
    }
    
    html = Template(template.template_html).render(**sample_context)
    
    return {
        "html": html,
        "css": template.custom_css,
        "page_size": template.page_size,
        "orientation": template.orientation,
        "background_image": template.background_image
    }


@frappe.whitelist()
def generate_certificate(template_name, student, **kwargs):
    """Generate a certificate for a student."""
    from frappe.utils import today, get_fullname
    
    template = frappe.get_doc("Certificate Template", template_name)
    student_doc = frappe.get_doc("Student", student)
    
    # Get company details
    company = kwargs.get("company") or frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_doc("Company", company) if company else None
    
    context = {
        "student_name": student_doc.student_name,
        "student": student,
        "program": kwargs.get("program") or student_doc.current_program,
        "company": company_doc.company_name if company_doc else "",
        "company_logo": company_doc.company_logo if company_doc else "",
        "academic_year": kwargs.get("academic_year") or frappe.defaults.get_user_default("Academic Year"),
        "academic_term": kwargs.get("academic_term") or frappe.defaults.get_user_default("Academic Term"),
        "date": kwargs.get("date") or today(),
        "award_title": kwargs.get("award_title") or template.certificate_type,
        "description": kwargs.get("description") or "",
        "principal_name": kwargs.get("principal_name") or "",
        "principal_signature": kwargs.get("principal_signature") or "",
        "class_teacher": kwargs.get("class_teacher") or "",
        "rubber_stamp": kwargs.get("rubber_stamp") or "",
        "certificate_number": kwargs.get("certificate_number") or f"CERT-{today().replace('-', '')}-{student}",
        "certificate_type": template.certificate_type
    }
    
    html = Template(template.template_html).render(**context)
    
    return {
        "html": html,
        "css": template.custom_css,
        "page_size": template.page_size,
        "orientation": template.orientation,
        "background_image": template.background_image
    }
