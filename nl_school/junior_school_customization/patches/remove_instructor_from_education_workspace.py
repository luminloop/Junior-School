import frappe


def execute():
    print("\n--- Removing Instructor from Education Workspace ---")
    
    try:
        ws = frappe.get_doc("Workspace", "Education")
        roles_to_remove = [r for r in ws.roles if r.role == "Instructor"]
        
        for r in roles_to_remove:
            ws.remove(r)
        
        ws.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"  Removed {len(roles_to_remove)} Instructor role(s) from Education workspace")
    except Exception as e:
        print(f"  Could not modify Education workspace: {e}")
        print("  Please manually remove Instructor role from Education workspace in Desk > Workspace > Education")
