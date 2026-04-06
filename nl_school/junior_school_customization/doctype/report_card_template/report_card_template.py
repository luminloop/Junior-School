# Copyright (c) 2025, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ReportCardTemplate(Document):
    def validate(self):
        if self.is_default:
            # Unset other defaults for the same company
            filters = {"is_default": 1, "name": ["!=", self.name]}
            if self.company:
                filters["company"] = self.company
            else:
                filters["company"] = ["is", "not set"]
            
            frappe.db.set_value(
                "Report Card Template",
                filters,
                "is_default",
                0
            )


def get_default_template(company=None):
    """Get the default report card template for a company."""
    filters = {"is_default": 1, "disabled": 0}
    
    # First try to find company-specific template
    if company:
        filters["company"] = company
        template = frappe.db.get_value("Report Card Template", filters, "name")
        if template:
            return template
    
    # Fall back to global default (no company set)
    filters["company"] = ["is", "not set"]
    template = frappe.db.get_value("Report Card Template", filters, "name")
    
    return template


def get_template_html(template_name):
    """Get the HTML content of a template."""
    if not template_name:
        return None
    
    return frappe.db.get_value("Report Card Template", template_name, "template_html")


@frappe.whitelist()
def get_default_template_html():
    """Get the default template HTML content for loading into the editor."""
    import os
    
    # Read the default template file
    template_path = frappe.get_app_path(
        "nl_school", "public", "html", "student_report_generation_tool.html"
    )
    
    if os.path.exists(template_path):
        with open(template_path, "r") as f:
            return f.read()
    
    return None
