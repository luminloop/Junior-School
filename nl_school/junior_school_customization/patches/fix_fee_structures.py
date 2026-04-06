import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_fee_structures()
    create_transport_zones()
    create_fee_schedules()


def create_fee_schedules():
    print("\n--- Creating Fee Schedules ---")
    
    COMPANY = "Lemana Junior School"
    ACADEMIC_TERM = "2026 Academic Year (Term 1)"
    
    from frappe.utils import nowdate, add_days
    
    # Get accounts
    company_doc = frappe.get_doc("Company", COMPANY)
    receivable_account = company_doc.default_receivable_account
    income_account = company_doc.default_income_account
    cost_center = company_doc.cost_center
    
    fee_structures = [
        f"Grade 7 - Boarder - {ACADEMIC_TERM}",
        f"Grade 7 - Day Scholar - {ACADEMIC_TERM}",
        f"Grade 8 - Boarder - {ACADEMIC_TERM}",
        f"Grade 8 - Day Scholar - {ACADEMIC_TERM}",
    ]
    
    for fs_name in fee_structures:
        if not frappe.db.exists("Fee Structure", fs_name):
            continue
        
        if not frappe.db.exists("Fee Schedule", fs_name):
            try:
                fs = frappe.get_doc("Fee Structure", fs_name)
                
                # Get student groups for this program/type
                program = fs.program
                is_boarder = "Boarder" in fs_name
                
                student_groups = frappe.get_all(
                    "Student Group",
                    filters={"program": program},
                    pluck="name",
                )
                
                for sg in student_groups:
                    schedule_name = f"{fs_name} - {sg}"
                    if not frappe.db.exists("Fee Schedule", schedule_name):
                        fs_schedule = frappe.new_doc("Fee Schedule")
                        fs_schedule.fee_structure = fs_name
                        fs_schedule.academic_term = ACADEMIC_TERM
                        fs_schedule.academic_year = "2026 Academic Year"
                        fs_schedule.company = COMPANY
                        fs_schedule.receivable_account = receivable_account
                        fs_schedule.cost_center = cost_center
                        fs_schedule.posting_date = nowdate()
                        fs_schedule.due_date = add_days(nowdate(), 30)
                        fs_schedule.total_amount = fs.total_amount
                        
                        fs_schedule.append("student_groups", {
                            "student_group": sg,
                        })
                        
                        fs_schedule.insert(ignore_permissions=True)
                        frappe.db.commit()
                        print(f"  Created: {schedule_name} (Ksh {fs.total_amount:,})")
            except Exception as e:
                print(f"  Error creating schedule for {fs_name}: {e}")
    
    print("Done creating fee schedules")


def delete_existing_fee_structures():
    print("\n--- Deleting existing Fee Structures ---")
    deleted = 0
    
    fee_structures = frappe.get_all("Fee Structure", pluck="name")
    for fs_name in fee_structures:
        try:
            doc = frappe.get_doc("Fee Structure", fs_name)
            if doc.docstatus == 1:
                doc.cancel()
                frappe.db.commit()
            doc.delete(force=True)
            print(f"  Deleted: {fs_name}")
            deleted += 1
        except Exception as e:
            print(f"  Error deleting {fs_name}: {e}")
    
    frappe.db.commit()
    print(f"Deleted {deleted} fee structures")


def create_fee_structures():
    print("\n--- Creating simplified Fee Structures ---")
    
    COMPANY = "Lemana Junior School"
    ACADEMIC_YEAR = "2026 Academic Year"
    ACADEMIC_TERM = "2026 Academic Year (Term 1)"
    
    boards = frappe.get_doc("Company", COMPANY)
    receivable_account = boards.default_receivable_account
    income_account = boards.default_income_account
    cost_center = boards.cost_center
    
    if not receivable_account:
        receivable_account = frappe.db.get_value("Account", {"company": COMPANY, "account_type": "Receivable"}, "name")
    if not income_account:
        income_account = frappe.db.get_value("Account", {"company": COMPANY, "account_type": "Income Account"}, "name")
    if not cost_center:
        cost_center = frappe.db.get_value("Cost Center", {"company": COMPANY, "is_group": 0}, "name")
    
    fee_categories = {
        "Tuition Fee": "Tuition Fee",
        "Boarding Fee": "Boarding Fee",
        "Activity Fee": "Activity Fee",
        "Exam Fee": "Exam Fee",
        "Sports Fee": "Sports Fee",
        "Library Fee": "Library Fee",
        "Computer Lab Fee": "Computer Lab Fee",
        "Medical Fee": "Medical Fee",
        "Development Fee": "Development Fee",
    }
    
    for cat_name, cat_desc in fee_categories.items():
        if not frappe.db.exists("Fee Category", cat_name):
            fc = frappe.new_doc("Fee Category")
            fc.category_name = cat_name
            fc.description = cat_desc
            fc.insert(ignore_permissions=True)
            frappe.db.commit()
    
    BOARDER_FEES = {
        "Grade 7": {"total": 55800, "components": [
            {"category": "Tuition Fee", "amount": 30000},
            {"category": "Boarding Fee", "amount": 10000},
            {"category": "Activity Fee", "amount": 5000},
            {"category": "Exam Fee", "amount": 5000},
            {"category": "Sports Fee", "amount": 3000},
            {"category": "Library Fee", "amount": 2800},
        ]},
        "Grade 8": {"total": 55800, "components": [
            {"category": "Tuition Fee", "amount": 30000},
            {"category": "Boarding Fee", "amount": 10000},
            {"category": "Activity Fee", "amount": 5000},
            {"category": "Exam Fee", "amount": 5000},
            {"category": "Sports Fee", "amount": 3000},
            {"category": "Library Fee", "amount": 2800},
        ]},
    }
    
    DAY_SCHOLAR_FEES = {
        "Grade 7": {"total": 45850, "components": [
            {"category": "Tuition Fee", "amount": 28000},
            {"category": "Activity Fee", "amount": 4000},
            {"category": "Exam Fee", "amount": 4000},
            {"category": "Sports Fee", "amount": 2500},
            {"category": "Library Fee", "amount": 2350},
            {"category": "Development Fee", "amount": 5000},
        ]},
        "Grade 8": {"total": 45850, "components": [
            {"category": "Tuition Fee", "amount": 28000},
            {"category": "Activity Fee", "amount": 4000},
            {"category": "Exam Fee", "amount": 4000},
            {"category": "Sports Fee", "amount": 2500},
            {"category": "Library Fee", "amount": 2350},
            {"category": "Development Fee", "amount": 5000},
        ]},
    }
    
    for grade in ["Grade 7", "Grade 8"]:
        boarder_name = f"{grade} - Boarder - {ACADEMIC_TERM}"
        if not frappe.db.exists("Fee Structure", boarder_name):
            fs = frappe.new_doc("Fee Structure")
            fs.program = grade
            fs.academic_year = ACADEMIC_YEAR
            fs.academic_term = ACADEMIC_TERM
            fs.company = COMPANY
            fs.receivable_account = receivable_account
            fs.cost_center = cost_center
            
            for comp in BOARDER_FEES[grade]["components"]:
                fs.append("components", {
                    "fees_category": comp["category"],
                    "description": comp["category"],
                    "amount": comp["amount"],
                })
            
            fs.insert(ignore_permissions=True)
            fs.submit()
            frappe.db.commit()
            print(f"  Created: {boarder_name} (Ksh {BOARDER_FEES[grade]['total']:,})")
        
        day_name = f"{grade} - Day Scholar - {ACADEMIC_TERM}"
        if not frappe.db.exists("Fee Structure", day_name):
            fs = frappe.new_doc("Fee Structure")
            fs.program = grade
            fs.academic_year = ACADEMIC_YEAR
            fs.academic_term = ACADEMIC_TERM
            fs.company = COMPANY
            fs.receivable_account = receivable_account
            fs.cost_center = cost_center
            
            for comp in DAY_SCHOLAR_FEES[grade]["components"]:
                fs.append("components", {
                    "fees_category": comp["category"],
                    "description": comp["category"],
                    "amount": comp["amount"],
                })
            
            fs.insert(ignore_permissions=True)
            fs.submit()
            frappe.db.commit()
            print(f"  Created: {day_name} (Ksh {DAY_SCHOLAR_FEES[grade]['total']:,})")


def create_transport_zones():
    print("\n--- Creating Transport Zones ---")
    
    custom_fields = {
        "Student": [
            {
                "fieldname": "transport_zone",
                "label": "Transport Zone",
                "fieldtype": "Select",
                "options": "\nZone 1\nZone 2\nZone 3",
                "insert_after": "custom_section_phone",
                "description": "Zone 1: Ksh 10,000 | Zone 2: Ksh 12,000 | Zone 3: Ksh 15,000",
            },
            {
                "fieldname": "transport_area",
                "label": "Transport Area",
                "fieldtype": "Data",
                "insert_after": "transport_zone",
                "description": "Specific pickup area (e.g., Kalro, Ruaka, etc.)",
            },
        ],
    }
    
    create_custom_fields(custom_fields)
    frappe.db.commit()
    print("  Created transport zone fields on Student")
    
    transport_categories = {
        "Zone 1 - Transport": 10000,
        "Zone 2 - Transport": 12000,
        "Zone 3 - Transport": 15000,
    }
    
    for cat_name, amount in transport_categories.items():
        if not frappe.db.exists("Fee Category", cat_name):
            fc = frappe.new_doc("Fee Category")
            fc.category_name = cat_name
            fc.description = f"Transport Fee - {amount:,}"
            fc.insert(ignore_permissions=True)
            frappe.db.commit()
            print(f"  Created Fee Category: {cat_name} (Ksh {amount:,})")
