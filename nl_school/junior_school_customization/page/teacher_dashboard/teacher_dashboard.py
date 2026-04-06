import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate, flt


@frappe.whitelist()
def get_dashboard_data():
    """Get all dashboard data for teacher in a single API call"""
    user = frappe.session.user
    instructor = get_current_instructor(user)
    
    if not instructor:
        return {
            "error": "No instructor profile found for this user",
            "stats": {},
            "my_classes": [],
            "pending_results": [],
            "attendance_trend": [],
            "upcoming_assessments": [],
            "recent_activity": [],
            "my_timetable": [],
        }
    
    return {
        "instructor": instructor,
        "stats": get_stats(instructor),
        "my_classes": get_my_classes(instructor),
        "pending_results": get_pending_results(instructor),
        "attendance_trend": get_attendance_trend(instructor),
        "upcoming_assessments": get_upcoming_assessments(instructor),
        "recent_activity": get_recent_activity(instructor),
        "my_timetable": get_my_timetable(instructor),
    }


def get_current_instructor(user):
    """Get the instructor record for the current user"""
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return None
    
    instructor = frappe.db.get_value("Instructor", {"employee": employee}, ["name", "instructor_name"], as_dict=True)
    return instructor


def get_stats(instructor):
    """Get summary statistics for the teacher dashboard"""
    today = nowdate()
    instructor_name = instructor.get("name")
    
    student_groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor": instructor_name},
        pluck="parent"
    )
    
    total_students = 0
    if student_groups:
        total_students = frappe.db.count(
            "Student Group Student",
            filters={"parent": ["in", student_groups], "active": 1}
        )
    
    total_classes = len(student_groups)
    
    attendance_marked = 0
    if student_groups:
        attendance_marked = frappe.db.count(
            "Student Attendance",
            filters={
                "date": today,
                "student_group": ["in", student_groups]
            }
        )
    
    pending_results = frappe.db.count(
        "Assessment Result",
        filters={
            "docstatus": 0,
            "student_group": ["in", student_groups] if student_groups else ["in", []]
        }
    )
    
    pending_approval = frappe.db.sql("""
        SELECT COUNT(*) as count FROM `tabAssessment Result`
        WHERE docstatus = 0 
        AND workflow_state = 'Pending Approval'
        AND student_group IN %(groups)s
    """, {"groups": student_groups or [""]}, as_dict=True)[0].get("count", 0) if student_groups else 0
    
    return {
        "total_students": total_students,
        "total_classes": total_classes,
        "attendance_marked": attendance_marked,
        "pending_results": pending_results,
        "pending_approval": pending_approval,
    }


def get_my_classes(instructor):
    """Get list of student groups assigned to this instructor"""
    instructor_name = instructor.get("name")
    
    classes = frappe.db.sql("""
        SELECT 
            sg.name,
            sg.student_group_name,
            sg.program,
            sg.academic_year,
            sg.academic_term,
            (SELECT COUNT(*) FROM `tabStudent Group Student` sgs 
             WHERE sgs.parent = sg.name AND sgs.active = 1) as student_count
        FROM `tabStudent Group` sg
        INNER JOIN `tabStudent Group Instructor` sgi ON sgi.parent = sg.name
        WHERE sgi.instructor = %(instructor)s
        AND sg.disabled = 0
        ORDER BY sg.program, sg.student_group_name
    """, {"instructor": instructor_name}, as_dict=True)
    
    return classes


def get_pending_results(instructor):
    """Get assessment results that need attention"""
    instructor_name = instructor.get("name")
    
    student_groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor": instructor_name},
        pluck="parent"
    )
    
    if not student_groups:
        return []
    
    results = frappe.db.sql("""
        SELECT 
            ar.name,
            ar.student_name,
            ar.course,
            ar.assessment_plan,
            ar.workflow_state,
            ar.student_group,
            ar.modified
        FROM `tabAssessment Result` ar
        WHERE ar.docstatus = 0
        AND ar.student_group IN %(groups)s
        ORDER BY ar.modified DESC
        LIMIT 10
    """, {"groups": student_groups}, as_dict=True)
    
    return results


def get_attendance_trend(instructor):
    """Get attendance trend for instructor's classes over last 7 days"""
    instructor_name = instructor.get("name")
    today = getdate(nowdate())
    
    student_groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor": instructor_name},
        pluck="parent"
    )
    
    if not student_groups:
        return []
    
    data = []
    for i in range(6, -1, -1):
        date = add_days(today, -i)
        
        present = frappe.db.count("Student Attendance", {
            "date": date, 
            "status": "Present",
            "student_group": ["in", student_groups]
        })
        absent = frappe.db.count("Student Attendance", {
            "date": date, 
            "status": "Absent",
            "student_group": ["in", student_groups]
        })
        
        data.append({
            "date": date.strftime("%a"),
            "full_date": str(date),
            "present": present,
            "absent": absent,
            "total": present + absent
        })
    
    return data


def get_upcoming_assessments(instructor):
    """Get upcoming assessments for instructor's classes"""
    instructor_name = instructor.get("name")
    today = nowdate()
    
    student_groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor": instructor_name},
        pluck="parent"
    )
    
    if not student_groups:
        return []
    
    assessments = frappe.db.sql("""
        SELECT 
            ap.name,
            ap.assessment_name,
            ap.course,
            ap.schedule_date,
            ap.student_group,
            ap.assessment_group
        FROM `tabAssessment Plan` ap
        WHERE ap.schedule_date >= %(today)s
        AND ap.student_group IN %(groups)s
        AND ap.docstatus < 2
        ORDER BY ap.schedule_date ASC
        LIMIT 5
    """, {"today": today, "groups": student_groups}, as_dict=True)
    
    return assessments


def get_recent_activity(instructor):
    """Get recent activity for instructor's classes"""
    instructor_name = instructor.get("name")
    activities = []
    
    student_groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor": instructor_name},
        pluck="parent"
    )
    
    if not student_groups:
        return []
    
    recent_results = frappe.db.sql("""
        SELECT 
            ar.student_name,
            ar.course,
            ar.total_score,
            ar.grade,
            ar.modified
        FROM `tabAssessment Result` ar
        WHERE ar.student_group IN %(groups)s
        ORDER BY ar.modified DESC
        LIMIT 5
    """, {"groups": student_groups}, as_dict=True)
    
    for result in recent_results:
        activities.append({
            "icon": "chart",
            "message": f"{result.student_name} - {result.course}: {result.total_score or 0} ({result.grade or 'N/A'})",
            "time": result.modified,
        })
    
    recent_attendance = frappe.db.sql("""
        SELECT 
            sa.student_name,
            sa.status,
            sa.date,
            sa.modified
        FROM `tabStudent Attendance` sa
        WHERE sa.student_group IN %(groups)s
        ORDER BY sa.modified DESC
        LIMIT 3
    """, {"groups": student_groups}, as_dict=True)
    
    for att in recent_attendance:
        activities.append({
            "icon": "tick" if att.status == "Present" else "remove",
            "message": f"{att.student_name} marked {att.status}",
            "time": att.modified,
        })
    
    activities.sort(key=lambda x: x["time"], reverse=True)
    
    return activities[:8]


def get_my_timetable(instructor):
    """Get this week's timetable for the instructor."""
    from datetime import timedelta
    
    instructor_name = instructor.get("name")
    today = getdate(nowdate())
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    student_groups = frappe.get_all(
        "Student Group Instructor",
        filters={"instructor": instructor_name},
        pluck="parent"
    )
    
    if not student_groups:
        return []
    
    schedules = frappe.db.sql("""
        SELECT 
            cs.name,
            cs.course,
            cs.student_group,
            sg.student_group_name,
            cs.room,
            cs.schedule_date,
            cs.from_time,
            cs.to_time,
            cs.title
        FROM `tabCourse Schedule` cs
        LEFT JOIN `tabStudent Group` sg ON cs.student_group = sg.name
        WHERE cs.instructor = %(instructor)s
        AND cs.schedule_date BETWEEN %(monday)s AND %(sunday)s
        ORDER BY cs.schedule_date, cs.from_time
    """, {
        "instructor": instructor_name,
        "monday": monday,
        "sunday": sunday,
    }, as_dict=True)
    
    days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    timetable = {}
    
    for sched in schedules:
        day_name = frappe.utils.getdate(sched.schedule_date).strftime("%A")
        if day_name not in timetable:
            timetable[day_name] = {
                "day": day_name,
                "date": sched.schedule_date,
                "schedules": []
            }
        
        timetable[day_name]["schedules"].append({
            "name": sched.name,
            "course": sched.course,
            "student_group": sched.student_group,
            "student_group_name": sched.student_group_name,
            "room": sched.room,
            "from_time": str(sched.from_time) if sched.from_time else "",
            "to_time": str(sched.to_time) if sched.to_time else "",
            "title": sched.title,
        })
    
    result = []
    for day in days_order:
        if day in timetable:
            result.append(timetable[day])
    
    return result
