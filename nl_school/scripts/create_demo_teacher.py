import frappe
from frappe.utils.password import update_password


def execute():
    """Create demo teacher user linked to Kush instructor"""
    email = "kush@loop.com"
    password = "D3moKush!Tchr@2026"

    # 1. Create or update User
    if frappe.db.exists("User", email):
        print(f"Updating user {email}...")
        user = frappe.get_doc("User", email)
    else:
        print(f"Creating user {email}...")
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = "Kush"
        user.last_name = "Teacher"
        user.send_welcome_email = 0

    user.enabled = 1
    user.roles = []

    for role in ["Instructor", "Academics User"]:
        user.append("roles", {"role": role})

    user.save(ignore_permissions=True)
    update_password(user.email, password)
    print(f"  Done. Email: {email} | Password: {password}")

    # 2. Check what schedules Kush has
    schedules = frappe.get_all("Course Schedule",
        filters={"instructor": "Kush"},
        fields=["name", "student_group", "course", "schedule_date", "from_time", "to_time"],
        order_by="schedule_date, from_time",
        limit=10
    )
    print(f"\n  Kush's Course Schedules: {len(schedules)}")
    for s in schedules[:5]:
        print(f"    {s.schedule_date} {s.from_time}-{s.to_time} | {s.course} | {s.student_group}")

    # 3. Show which student groups Kush is linked to
    groups = frappe.db.sql("""
        SELECT DISTINCT student_group
        FROM `tabCourse Schedule`
        WHERE instructor = 'Kush'
    """, as_dict=1)
    print(f"\n  Kush's Student Groups: {[g.student_group for g in groups]}")

    print(f"\n{'='*50}")
    print(f"LOGIN: http://loop.localhost:8004")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print(f"{'='*50}")

    frappe.db.commit()
