"""
Demo Data Creation Script for nl_school
Creates: Course Schedules (timetable), Assessment Plans (exams), Assessment Results (grades)

Usage: bench --site loop execute nl_school.scripts.create_demo_data.execute
"""

import frappe
from frappe.utils import getdate, add_days
import random
import calendar


def execute():
    """Main entry point"""
    print("=" * 60)
    print("CREATING DEMO DATA FOR NL_SCHOOL")
    print("=" * 60)

    setup_assessment_groups()
    setup_assessment_criteria()
    setup_course_assessment_criteria()
    create_course_schedules()
    create_assessment_plans()
    create_assessment_results()

    print("=" * 60)
    print("DEMO DATA CREATION COMPLETE!")
    print("=" * 60)


def setup_assessment_groups():
    """Create 2026 Term 1 assessment groups if they don't exist"""
    print("\n--- Setting up Assessment Groups ---")

    parent_name = "2026-2027"
    if not frappe.db.exists("Assessment Group", parent_name):
        parent = frappe.new_doc("Assessment Group")
        parent.assessment_group_name = parent_name
        parent.parent_assessment_group = "All Assessment Groups"
        parent.is_group = 1
        parent.save()
        print(f"  Created parent: {parent_name}")
    else:
        print(f"  Parent exists: {parent_name}")

    term_name = "2026-2027 Term 1"
    if not frappe.db.exists("Assessment Group", term_name):
        term = frappe.new_doc("Assessment Group")
        term.assessment_group_name = term_name
        term.parent_assessment_group = parent_name
        term.is_group = 1
        term.save()
        print(f"  Created term: {term_name}")
    else:
        print(f"  Term exists: {term_name}")

    exams = [
        ("Opener Exam - Term 1 2026", term_name),
        ("Mid Term - Term 1 2026", term_name),
        ("End Term - Term 1 2026", term_name),
    ]
    for exam_name, parent in exams:
        if not frappe.db.exists("Assessment Group", exam_name):
            ag = frappe.new_doc("Assessment Group")
            ag.assessment_group_name = exam_name
            ag.parent_assessment_group = parent
            ag.is_group = 0
            ag.save()
            print(f"  Created exam: {exam_name}")
        else:
            print(f"  Exam exists: {exam_name}")

    frappe.db.commit()


def setup_assessment_criteria():
    """Create assessment criteria if they don't exist"""
    print("\n--- Setting up Assessment Criteria ---")

    criteria = [
        "Continuous Assessment",
        "Class Participation",
        "Homework",
        "Project Work",
        "Oral Presentation",
        "Practical Skills",
        "Written Test",
        "Problem Solving",
        "Critical Thinking",
        "Collaboration",
    ]
    for c in criteria:
        if not frappe.db.exists("Assessment Criteria", c):
            doc = frappe.new_doc("Assessment Criteria")
            doc.assessment_criteria = c
            doc.save()
            print(f"  Created: {c}")
        else:
            print(f"  Exists: {c}")

    frappe.db.commit()


def setup_course_assessment_criteria():
    """Add assessment criteria to each course"""
    print("\n--- Setting up Course Assessment Criteria ---")

    courses = frappe.get_all("Course", fields=["name", "course_name"])

    criteria_sets = [
        [("Continuous Assessment", 30), ("Written Test", 50), ("Homework", 20)],
        [("Continuous Assessment", 25), ("Project Work", 40), ("Oral Presentation", 35)],
        [("Class Participation", 20), ("Problem Solving", 40), ("Written Test", 40)],
        [("Continuous Assessment", 30), ("Practical Skills", 50), ("Homework", 20)],
        [("Critical Thinking", 30), ("Written Test", 40), ("Collaboration", 30)],
    ]

    for i, course in enumerate(courses):
        doc = frappe.get_doc("Course", course.name)
        if doc.assessment_criteria:
            print(f"  Skipping {course.name} (already has criteria)")
            continue

        criteria = criteria_sets[i % len(criteria_sets)]
        for crit_name, weightage in criteria:
            doc.append("assessment_criteria", {
                "assessment_criteria": crit_name,
                "weightage": weightage,
            })
        doc.default_grading_scale = "Junior School Grading Scale"
        doc.save()
        print(f"  Added {len(criteria)} criteria to {course.name}")

    frappe.db.commit()


def create_course_schedules():
    """Create timetable entries for the week"""
    print("\n--- Creating Course Schedules (Timetable) ---")

    groups = frappe.db.sql("""
        SELECT sg.name, sg.program, sg.academic_year, sg.academic_term
        FROM `tabStudent Group` sg
        INNER JOIN `tabStudent Group Student` sgs ON sgs.parent = sg.name
        WHERE sg.group_based_on = 'Batch'
        GROUP BY sg.name
        HAVING COUNT(sgs.student) > 0
        ORDER BY sg.name
    """, as_dict=1)

    if not groups:
        print("  No student groups with students found!")
        return

    instructors = frappe.get_all("Instructor", fields=["name", "instructor_name"], limit=10)
    rooms = frappe.get_all("Room", fields=["name"], limit=10)

    if not instructors or not rooms:
        print("  Missing instructors or rooms!")
        return

    periods = [
        ("08:00:00", "08:40:00"),
        ("08:40:00", "09:20:00"),
        ("09:40:00", "10:20:00"),
        ("10:20:00", "11:00:00"),
        ("11:20:00", "12:00:00"),
        ("12:00:00", "12:40:00"),
        ("13:20:00", "14:00:00"),
        ("14:00:00", "14:40:00"),
    ]

    # Schedule within the academic term (Term 1: 2026-01-02 to 2026-03-29)
    # Use a week in the middle of the term
    term_start = getdate("2026-01-05")  # First Monday of term
    weekdays = [add_days(term_start, i) for i in range(5)]  # Mon-Fri of first week
    colors = ["blue", "green", "red", "orange", "teal", "violet", "cyan", "amber", "pink", "purple"]

    schedule_count = 0
    for group in groups:
        courses = frappe.db.sql(
            "SELECT course FROM `tabProgram Course` WHERE parent = %s",
            (group.program,), as_dict=1
        )
        if not courses:
            print(f"  No courses found for {group.program}, skipping {group.name}")
            continue

        course_list = [c.course for c in courses]

        for day_idx, day in enumerate(weekdays):
            num_periods = min(5, len(periods))
            for period_idx in range(num_periods):
                course = course_list[schedule_count % len(course_list)]
                instructor = instructors[schedule_count % len(instructors)]
                room = rooms[schedule_count % len(rooms)]
                color = colors[schedule_count % len(colors)]

                existing = frappe.db.exists("Course Schedule", {
                    "student_group": group.name,
                    "schedule_date": day,
                    "from_time": periods[period_idx][0],
                })
                if existing:
                    schedule_count += 1
                    continue

                try:
                    cs = frappe.new_doc("Course Schedule")
                    cs.student_group = group.name
                    cs.course = course
                    cs.instructor = instructor.name
                    cs.room = room.name
                    cs.schedule_date = day
                    cs.from_time = periods[period_idx][0]
                    cs.to_time = periods[period_idx][1]
                    cs.class_schedule_color = color
                    cs.save()
                    schedule_count += 1
                except Exception as e:
                    print(f"  Schedule error for {group.name} {day} P{period_idx}: {e}")
                    schedule_count += 1

    frappe.db.commit()
    total = frappe.db.count("Course Schedule")
    print(f"  Total course schedules in system: {total}")


def create_assessment_plans():
    """Create exam/assessment plans for different exam types"""
    print("\n--- Creating Assessment Plans (Exams) ---")

    groups = frappe.db.sql("""
        SELECT sg.name, sg.program, sg.academic_year, sg.academic_term
        FROM `tabStudent Group` sg
        INNER JOIN `tabStudent Group Student` sgs ON sgs.parent = sg.name
        WHERE sg.group_based_on = 'Batch'
        GROUP BY sg.name
        HAVING COUNT(sgs.student) > 0
        ORDER BY sg.name
    """, as_dict=1)

    grading_scale = "Junior School Grading Scale"
    instructors = frappe.get_all("Instructor", fields=["name"], limit=5)
    rooms = frappe.get_all("Room", fields=["name"], limit=5)

    exam_types = [
        ("Opener Exam - Term 1 2026", 30),
        ("Mid Term - Term 1 2026", 50),
        ("End Term - Term 1 2026", 100),
    ]

    plan_count = 0
    for group in groups:
        courses = frappe.db.sql(
            "SELECT course FROM `tabProgram Course` WHERE parent = %s",
            (group.program,), as_dict=1
        )
        if not courses:
            continue

        for exam_name, max_score in exam_types:
            if not frappe.db.exists("Assessment Group", exam_name):
                print(f"  Assessment Group '{exam_name}' not found, skipping")
                continue

            for course_row in courses[:3]:
                course = course_row.course

                existing = frappe.db.exists("Assessment Plan", {
                    "student_group": group.name,
                    "course": course,
                    "assessment_group": exam_name,
                })
                if existing:
                    print(f"  Exists: {group.name} / {course} / {exam_name}")
                    plan_count += 1
                    continue

                try:
                    ap = frappe.new_doc("Assessment Plan")
                    ap.student_group = group.name
                    ap.assessment_group = exam_name
                    ap.grading_scale = grading_scale
                    ap.maximum_assessment_score = max_score
                    ap.academic_year = group.academic_year
                    ap.academic_term = group.academic_term
                    ap.assessment_name = f"{exam_name} - {course} - {group.name}"

                    ap.schedule_date = add_days(getdate("2026-03-15"), random.randint(0, 10))
                    ap.from_time = "09:00:00"
                    ap.to_time = "11:00:00"
                    if instructors:
                        ap.examiner = random.choice(instructors).name
                    if rooms:
                        ap.room = random.choice(rooms).name

                    # Set course and program
                    # Must override the fetch_from (student_group.course) which returns None for batch groups
                    ap.course = course
                    ap.program = group.program

                    course_doc = frappe.get_doc("Course", course)
                    if course_doc.assessment_criteria:
                        for crit in course_doc.assessment_criteria:
                            ap.append("assessment_criteria", {
                                "assessment_criteria": crit.assessment_criteria,
                                "maximum_score": (crit.weightage / 100) * max_score,
                            })
                    else:
                        ap.append("assessment_criteria", {
                            "assessment_criteria": "Written Test",
                            "maximum_score": max_score,
                        })

                    # Save without triggering fetch_from override
                    # We insert directly to bypass the fetch_from mechanism that clears course
                    ap.flags.ignore_permissions = True
                    ap.flags.ignore_mandatory = True
                    ap.insert()
                    # After insert, set the course directly in DB to override fetch_from
                    frappe.db.set_value("Assessment Plan", ap.name, "course", course)
                    frappe.db.set_value("Assessment Plan", ap.name, "program", group.program)
                    ap.reload()
                    ap.submit()
                    plan_count += 1
                    print(f"  Created: {ap.assessment_name}")
                except Exception as e:
                    print(f"  Error: {course}/{exam_name}: {e}")

    frappe.db.commit()
    total = frappe.db.count("Assessment Plan")
    print(f"  Total assessment plans in system: {total}")


def create_assessment_results():
    """Create grades for the Opener Exam"""
    print("\n--- Creating Assessment Results (Grades) ---")

    plans = frappe.get_all("Assessment Plan",
        filters={
            "assessment_group": "Opener Exam - Term 1 2026",
            "docstatus": 1,
        },
        fields=["name", "student_group", "course", "maximum_assessment_score"],
    )

    if not plans:
        print("  No submitted Opener Exam plans found!")
        return

    result_count = 0
    for plan in plans:
        students = frappe.get_all("Student Group Student",
            filters={"parent": plan.student_group},
            fields=["student", "student_name"],
        )
        if not students:
            continue

        plan_doc = frappe.get_doc("Assessment Plan", plan.name)

        for student in students:
            existing = frappe.db.exists("Assessment Result", {
                "student": student.student,
                "assessment_plan": plan.name,
            })
            if existing:
                continue

            try:
                ar = frappe.new_doc("Assessment Result")
                ar.student = student.student
                ar.assessment_plan = plan.name
                ar.student_group = plan.student_group
                ar.course = plan.course
                ar.grading_scale = plan_doc.grading_scale
                ar.maximum_score = plan.maximum_assessment_score

                for crit in plan_doc.assessment_criteria:
                    min_score = crit.maximum_score * 0.4
                    score = round(random.uniform(min_score, crit.maximum_score), 1)
                    ar.append("details", {
                        "assessment_criteria": crit.assessment_criteria,
                        "maximum_score": crit.maximum_score,
                        "score": score,
                    })

                ar.save()
                ar.submit()
                result_count += 1
                print(f"  Created: {student.student_name} - {plan.course}")
            except Exception as e:
                print(f"  Error: {student.student_name}: {e}")

    frappe.db.commit()
    total = frappe.db.count("Assessment Result")
    print(f"  Total assessment results in system: {total}")
