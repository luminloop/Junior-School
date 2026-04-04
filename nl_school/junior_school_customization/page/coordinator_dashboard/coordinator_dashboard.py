import frappe
from frappe import _
from frappe.utils import nowdate, add_days, getdate, flt


@frappe.whitelist()
def get_dashboard_data():
    """Get all dashboard data for academic coordinator in a single API call"""
    return {
        "stats": get_stats(),
        "pending_approvals": get_pending_approvals(),
        "teacher_summary": get_teacher_summary(),
        "attendance_trend": get_attendance_trend(),
        "class_performance": get_class_performance(),
        "alerts": get_alerts(),
        "recent_activity": get_recent_activity(),
    }


def get_stats():
    """Get summary statistics for the coordinator dashboard"""
    today = nowdate()
    
    # Total active students
    total_students = frappe.db.count("Student", {"enabled": 1})
    
    # Total active teachers
    total_teachers = frappe.db.count("Instructor", {"status": "Active"})
    
    # Total classes/student groups
    total_classes = frappe.db.count("Student Group", {"disabled": 0})
    
    # Today's attendance
    total_attendance_today = frappe.db.count("Student Attendance", {"date": today})
    present_today = frappe.db.count("Student Attendance", {"date": today, "status": "Present"})
    attendance_rate = round((present_today / total_attendance_today * 100), 1) if total_attendance_today > 0 else 0
    
    # Pending assessment approvals
    pending_approvals = frappe.db.sql("""
        SELECT COUNT(*) as count FROM `tabAssessment Result`
        WHERE docstatus = 0 AND workflow_state = 'Pending Approval'
    """, as_dict=True)[0].get("count", 0)
    
    # Draft results (not yet submitted)
    draft_results = frappe.db.sql("""
        SELECT COUNT(*) as count FROM `tabAssessment Result`
        WHERE docstatus = 0 AND (workflow_state IS NULL OR workflow_state = 'Draft')
    """, as_dict=True)[0].get("count", 0)
    
    # Upcoming assessments this week
    upcoming_assessments = frappe.db.count("Assessment Plan", {
        "schedule_date": ["between", [today, add_days(today, 7)]],
        "docstatus": ["<", 2]
    })
    
    return {
        "total_students": total_students,
        "total_teachers": total_teachers,
        "total_classes": total_classes,
        "present_today": present_today,
        "attendance_rate": attendance_rate,
        "pending_approvals": pending_approvals,
        "draft_results": draft_results,
        "upcoming_assessments": upcoming_assessments,
    }


def get_pending_approvals():
    """Get assessment results pending approval"""
    results = frappe.db.sql("""
        SELECT 
            ar.name,
            ar.student_name,
            ar.course,
            ar.student_group,
            ar.total_score,
            ar.grade,
            ar.modified,
            ar.owner
        FROM `tabAssessment Result` ar
        WHERE ar.docstatus = 0 
        AND ar.workflow_state = 'Pending Approval'
        ORDER BY ar.modified DESC
        LIMIT 15
    """, as_dict=True)
    
    # Get owner names
    for r in results:
        if r.owner:
            r.submitted_by = frappe.db.get_value("User", r.owner, "full_name") or r.owner
    
    return results


def get_teacher_summary():
    """Get summary of teacher workload and submissions"""
    teachers = frappe.db.sql("""
        SELECT 
            i.name,
            i.instructor_name,
            (SELECT COUNT(DISTINCT sgi.parent) 
             FROM `tabStudent Group Instructor` sgi 
             WHERE sgi.instructor = i.name) as class_count,
            (SELECT COUNT(*) 
             FROM `tabAssessment Result` ar 
             INNER JOIN `tabStudent Group Instructor` sgi ON ar.student_group = sgi.parent
             WHERE sgi.instructor = i.name 
             AND ar.docstatus = 0 
             AND ar.workflow_state = 'Pending Approval') as pending_approvals,
            (SELECT COUNT(*) 
             FROM `tabAssessment Result` ar 
             INNER JOIN `tabStudent Group Instructor` sgi ON ar.student_group = sgi.parent
             WHERE sgi.instructor = i.name 
             AND ar.docstatus = 0 
             AND (ar.workflow_state IS NULL OR ar.workflow_state = 'Draft')) as draft_results
        FROM `tabInstructor` i
        WHERE i.status = 'Active'
        ORDER BY pending_approvals DESC, draft_results DESC
        LIMIT 10
    """, as_dict=True)
    
    return teachers


def get_attendance_trend():
    """Get attendance data for the last 7 days (all classes)"""
    today = getdate(nowdate())
    data = []
    
    for i in range(6, -1, -1):
        date = add_days(today, -i)
        
        present = frappe.db.count("Student Attendance", {"date": date, "status": "Present"})
        absent = frappe.db.count("Student Attendance", {"date": date, "status": "Absent"})
        
        data.append({
            "date": date.strftime("%a"),
            "full_date": str(date),
            "present": present,
            "absent": absent,
            "total": present + absent
        })
    
    return data


def get_class_performance():
    """Get average performance by class/student group"""
    # Get current academic year
    current_year = frappe.db.get_single_value("Education Settings", "current_academic_year")
    
    if not current_year:
        return []
    
    performance = frappe.db.sql("""
        SELECT 
            ar.student_group,
            sg.program,
            AVG(ar.total_score) as avg_score,
            COUNT(*) as result_count
        FROM `tabAssessment Result` ar
        INNER JOIN `tabStudent Group` sg ON ar.student_group = sg.name
        WHERE ar.docstatus = 1
        AND ar.academic_year = %(year)s
        GROUP BY ar.student_group
        ORDER BY avg_score DESC
        LIMIT 10
    """, {"year": current_year}, as_dict=True)
    
    return performance


def get_alerts():
    """Get items that need coordinator attention"""
    today = nowdate()
    alerts = []
    
    # Pending approvals count
    pending = frappe.db.sql("""
        SELECT COUNT(*) as count FROM `tabAssessment Result`
        WHERE docstatus = 0 AND workflow_state = 'Pending Approval'
    """, as_dict=True)[0].get("count", 0)
    
    if pending > 0:
        alerts.append({
            "type": "warning",
            "icon": "time",
            "message": f"{pending} assessment results awaiting approval",
            "link": "/app/assessment-result?workflow_state=Pending+Approval"
        })
    
    # Teachers with no attendance marked today
    teachers_no_attendance = frappe.db.sql("""
        SELECT COUNT(DISTINCT sgi.instructor) as count
        FROM `tabStudent Group Instructor` sgi
        INNER JOIN `tabStudent Group` sg ON sgi.parent = sg.name
        WHERE sg.disabled = 0
        AND sgi.instructor NOT IN (
            SELECT DISTINCT sgi2.instructor
            FROM `tabStudent Attendance` sa
            INNER JOIN `tabStudent Group Instructor` sgi2 ON sa.student_group = sgi2.parent
            WHERE sa.date = %(today)s
        )
    """, {"today": today}, as_dict=True)[0].get("count", 0)
    
    if teachers_no_attendance > 0:
        alerts.append({
            "type": "info",
            "icon": "user-x",
            "message": f"{teachers_no_attendance} teachers haven't marked attendance",
            "link": "/app/instructor"
        })
    
    # Students absent 3+ consecutive days
    frequently_absent = frappe.db.sql("""
        SELECT COUNT(DISTINCT sa1.student) as count
        FROM `tabStudent Attendance` sa1
        INNER JOIN `tabStudent Attendance` sa2 ON sa1.student = sa2.student
        INNER JOIN `tabStudent Attendance` sa3 ON sa1.student = sa3.student
        WHERE sa1.status = 'Absent' 
        AND sa2.status = 'Absent'
        AND sa3.status = 'Absent'
        AND sa1.date = %(today)s
        AND sa2.date = %(yesterday)s
        AND sa3.date = %(day_before)s
    """, {
        "today": today, 
        "yesterday": add_days(today, -1),
        "day_before": add_days(today, -2)
    }, as_dict=True)
    
    if frequently_absent and frequently_absent[0].count > 0:
        alerts.append({
            "type": "danger",
            "icon": "alert-circle",
            "message": f"{frequently_absent[0].count} students absent 3+ days",
            "link": "/app/student-attendance?status=Absent"
        })
    
    # Upcoming assessments
    upcoming = frappe.db.count("Assessment Plan", {
        "schedule_date": ["between", [today, add_days(today, 3)]],
        "docstatus": ["<", 2]
    })
    if upcoming > 0:
        alerts.append({
            "type": "info",
            "icon": "calendar",
            "message": f"{upcoming} assessments in next 3 days",
            "link": "/app/assessment-plan"
        })
    
    return alerts


def get_recent_activity():
    """Get recent activity across all teachers"""
    activities = []
    
    # Recent approved results
    approved_results = frappe.db.sql("""
        SELECT 
            ar.student_name,
            ar.course,
            ar.student_group,
            ar.modified
        FROM `tabAssessment Result` ar
        WHERE ar.docstatus = 1
        ORDER BY ar.modified DESC
        LIMIT 5
    """, as_dict=True)
    
    for result in approved_results:
        activities.append({
            "icon": "solid-success",
            "message": f"{result.student_name} - {result.course} approved",
            "time": result.modified,
        })
    
    # Recent submissions for approval
    submissions = frappe.db.sql("""
        SELECT 
            ar.student_name,
            ar.course,
            ar.owner,
            ar.modified
        FROM `tabAssessment Result` ar
        WHERE ar.workflow_state = 'Pending Approval'
        ORDER BY ar.modified DESC
        LIMIT 3
    """, as_dict=True)
    
    for sub in submissions:
        owner_name = frappe.db.get_value("User", sub.owner, "full_name") or sub.owner
        activities.append({
            "icon": "time",
            "message": f"{sub.student_name} - {sub.course} submitted by {owner_name}",
            "time": sub.modified,
        })
    
    # Sort by time
    activities.sort(key=lambda x: x["time"], reverse=True)
    
    return activities[:10]
