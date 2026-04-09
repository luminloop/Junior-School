# Copyright (c) 2026, Navari and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SchoolEmailSettings(Document):
    pass


def get_email_account_for_purpose(company, purpose):
    """Get the email account configured for a specific purpose."""
    settings = frappe.db.get_value(
        "School Email Settings",
        {"company": company},
        ["name", "default_email_account"],
        as_dict=True
    )
    
    if not settings:
        return None
    
    # Check purpose-specific email accounts
    purpose_map = {
        "attendance": "attendance_email_account",
        "fee": "fee_email_account",
        "grade": "grade_email_account",
        "event": "event_email_account"
    }
    
    if purpose in purpose_map:
        field = purpose_map[purpose]
        account = frappe.db.get_value("School Email Settings", settings.name, field)
        if account:
            return account
    
    # Check the email_accounts child table
    accounts = frappe.get_all(
        "School Email Account Purpose",
        filters={"parent": settings.name, "purpose": purpose},
        fields=["email_account"]
    )
    
    if accounts:
        return accounts[0].email_account
    
    # Fall back to default
    return settings.default_email_account


@frappe.whitelist()
def get_settings_for_company(company):
    """Get email settings for a company."""
    settings = frappe.db.get_value(
        "School Email Settings",
        {"company": company},
        "*",
        as_dict=True
    )
    
    return settings


@frappe.whitelist()
def create_email_account(email, password, company, purpose="default"):
    """Helper to create an email account for the school."""
    from frappe.email.doctype.email_account.email_account import EmailAccount
    
    # Basic email account creation - this would need to be customized based on email provider
    account = frappe.new_doc("Email Account")
    account.email_account_name = f"{company} - {purpose.title()}"
    account.email_id = email
    account.password = password
    account.enable_outgoing = 1
    account.default_outgoing = 0 if purpose != "default" else 1
    
    # Auto-detect email provider settings
    if "gmail.com" in email:
        account.smtp_server = "smtp.gmail.com"
        account.smtp_port = 587
        account.use_tls = 1
    elif "outlook" in email or "hotmail" in email:
        account.smtp_server = "smtp-mail.outlook.com"
        account.smtp_port = 587
        account.use_tls = 1
    elif "yahoo" in email:
        account.smtp_server = "smtp.mail.yahoo.com"
        account.smtp_port = 587
        account.use_tls = 1
    
    account.insert(ignore_permissions=True)
    
    return account.name
