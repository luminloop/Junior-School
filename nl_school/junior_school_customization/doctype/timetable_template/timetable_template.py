# Copyright (c) 2026, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TimetableTemplate(Document):
    def validate(self):
        if self.is_default:
            # Unset other defaults for the same company
            filters = {"is_default": 1, "name": ["!=", self.name]}
            if self.company:
                filters["company"] = self.company
            else:
                filters["company"] = ["is", "not set"]
            
            frappe.db.set_value(
                "Timetable Template",
                filters,
                "is_default",
                0
            )


def get_default_template(company=None):
    """Get the default timetable template for a company."""
    filters = {"is_default": 1, "disabled": 0}
    
    # First try to find company-specific template
    if company:
        filters["company"] = company
        template = frappe.db.get_value("Timetable Template", filters, "name")
        if template:
            return template
    
    # Fall back to global default (no company set)
    filters["company"] = ["is", "not set"]
    template = frappe.db.get_value("Timetable Template", filters, "name")
    
    return template


def get_template_styles(template_name=None, company=None):
    """Get the style settings from a template."""
    if not template_name:
        template_name = get_default_template(company)
    
    if not template_name:
        # Return default styles
        return {
            "header_color": "#f3f4f6",
            "break_color": "#ffe4e6",
            "row_odd_color": "#ffffff",
            "row_even_color": "#f9fafb",
            "custom_css": ""
        }
    
    template = frappe.get_doc("Timetable Template", template_name)
    return {
        "header_color": template.header_color or "#f3f4f6",
        "break_color": template.break_color or "#ffe4e6",
        "row_odd_color": template.row_odd_color or "#ffffff",
        "row_even_color": template.row_even_color or "#f9fafb",
        "custom_css": template.custom_css or ""
    }


@frappe.whitelist()
def get_template_for_print(company=None):
    """Get template data for printing."""
    template_name = get_default_template(company)
    
    if template_name:
        template = frappe.get_doc("Timetable Template", template_name)
        return {
            "name": template.name,
            "header_color": template.header_color,
            "break_color": template.break_color,
            "row_odd_color": template.row_odd_color,
            "row_even_color": template.row_even_color,
            "custom_css": template.custom_css,
            "template_html": template.template_html
        }
    
    return None
