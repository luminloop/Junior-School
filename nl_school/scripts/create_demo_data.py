"""
Demo Data Creation Script for nl_school
Creates: Students assigned to groups, Assessment Plans, Assessment Results

Usage: bench --site loop execute nl_school.scripts.create_demo_data.execute
"""

import frappe
from frappe.utils import getdate, add_days
import random


def execute():
    """Main entry point"""
    print("=" * 60)
    print("CREATING DEMO DATA FOR NL_SCHOOL")
    print("=" * 60)

    setup_assessment_groups()
    setup_assessment_criteria()
    setup_course_assessment_criteria()
    assign_students_to_groups()
    create_assessment_plans()
    create_assessment_results()

    print("\n" + "=" * 60)
    print("DEMO DATA CREATION COMPLETE!")
    print("=" * 60)


def setup_assessment_groups():
    """Create clean assessment groups: Opener Exam, Mid Term, End Term"""
    print("\n--- Setting up Assessment Groups ---")

    exams = ["Opener Exam", "Mid Term", "End Term"]
    for exam_name in exams:
        if not frappe.db.exists("Assessment Group", exam_name):
            frappe.get_doc({
                "doctype": "Assessment Group",
                "assessment_group_name": exam_name,
                "parent_assessment_group": "All Assessment Groups",
                "is_group": 0,
            }).save()
            print(f"  Created: {exam_name}")
        else:
            print(f"  Exists: {exam_name}")

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
            frappe.get_doc({
                "doctype": "Assessment Criteria",
                "assessment_criteria": c,
            }).save()
            print(f"  Created: {c}")
        else:
            print(f"  Exists: {c}")

    frappe.db.commit()


def setup_course_assessment_criteria():
    """Add assessment criteria to each course"""
    print("\n--- Setting up Course Assessment Criteria ---")

    courses = frappe.get_all("Course", fields=["name", "course_name"])
    if not courses:
        print("  No courses found!")
        return

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


def assign_students_to_groups():
    """Assign unassigned students to ALL form groups with proper Program Enrollments"""
    print("\n--- Assigning Students to Form Groups ---")

    # Form group to batch/program mapping
    form_config = {
        "Form 1 - North": {"program": "Grade 7", "batch": "2026 - Form 1"},
        "Form 1 - South": {"program": "Grade 7", "batch": "2026 - Form 1"},
        "Form 1 - East": {"program": "Grade 7", "batch": "2026 - Form 1"},
        "Form 1 - West": {"program": "Grade 7", "batch": "2026 - Form 1"},
        "Form 2 - North": {"program": "Grade 8", "batch": "2026 - Form 2"},
        "Form 2 - South": {"program": "Grade 8", "batch": "2026 - Form 2"},
        "Form 2 - East": {"program": "Grade 8", "batch": "2026 - Form 2"},
        "Form 2 - West": {"program": "Grade 8", "batch": "2026 - Form 2"},
        "Form 3 - North": {"program": "Grade 9", "batch": "2026 - Form 3"},
        "Form 3 - South": {"program": "Grade 9", "batch": "2026 - Form 3"},
        "Form 3 - East": {"program": "Grade 9", "batch": "2026 - Form 3"},
        "Form 3 - West": {"program": "Grade 9", "batch": "2026 - Form 3"},
        "Form 4 - North": {"program": "Grade 10", "batch": "2026 - Form 4"},
        "Form 4 - South": {"program": "Grade 10", "batch": "2026 - Form 4"},
        "Form 4 - East": {"program": "Grade 8", "batch": "2026 - Form 4"},
        "Form 4 - West": {"program": "Grade 10", "batch": "2026 - Form 4"},
    }

    # Get all students not yet enrolled in any program
    enrolled_students = set(
        frappe.get_all("Program Enrollment",
            filters={"docstatus": 1},
            pluck="student",
        )
    )
    all_students = frappe.get_all("Student", fields=["name", "student_name"])
    unenrolled = [s for s in all_students if s.name not in enrolled_students]
    random.shuffle(unenrolled)

    print(f"  Students without enrollment: {len(unenrolled)}")

    # Also get students already enrolled but not in student groups
    enrolled_but_unassigned = []
    for s in all_students:
        if s.name in enrolled_students:
            in_group = frappe.db.exists("Student Group Student", {"student": s.name})
            if not in_group:
                enrolled_but_unassigned.append(s)

    print(f"  Enrolled but unassigned to groups: {len(enrolled_but_unassigned)}")

    students_per_group = 5
    student_idx = 0
    available = unenrolled + enrolled_but_unassigned

    for group_name, config in form_config.items():
        if not frappe.db.exists("Student Group", group_name):
            continue

        existing_count = frappe.db.count("Student Group Student", {"parent": group_name})
        if existing_count >= students_per_group:
            print(f"  Skip {group_name} ({existing_count} students)")
            continue

        needed = students_per_group - existing_count
        added = 0

        for _ in range(needed):
            if student_idx >= len(available):
                break

            student = available[student_idx]
            student_idx += 1

            # Create Program Enrollment if needed
            if student.name not in enrolled_students:
                try:
                    pe = frappe.new_doc("Program Enrollment")
                    pe.student = student.name
                    pe.student_name = student.student_name
                    pe.program = config["program"]
                    pe.student_batch_name = config["batch"]
                    pe.academic_year = "year 2026"
                    pe.academic_term = "year 2026 (Term1)"
                    pe.enrollment_date = getdate("2026-01-02")
                    pe.save()
                    pe.submit()
                    enrolled_students.add(student.name)
                except Exception as e:
                    print(f"  Enrollment error for {student.student_name}: {e}")
                    continue

            # Add to student group
            try:
                doc = frappe.get_doc("Student Group", group_name)
                doc.append("students", {
                    "student": student.name,
                    "student_name": student.student_name,
                })
                doc.save()
                added += 1
            except Exception as e:
                print(f"  Group error for {student.student_name} in {group_name}: {e}")

        if added > 0:
            print(f"  Added {added} to {group_name}")

    frappe.db.commit()

    # Summary
    print("\n  --- Student Group Summary ---")
    for group_name in form_config:
        count = frappe.db.count("Student Group Student", {"parent": group_name})
        if count > 0:
            print(f"  {group_name}: {count} students")


def create_assessment_plans():
    """Create exam/assessment plans for ALL student groups and exam types"""
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

    if not groups:
        print("  No groups with students!")
        return

    grading_scale = "Junior School Grading Scale"
    instructors = frappe.get_all("Instructor", fields=["name"], limit=5)
    rooms = frappe.get_all("Room", fields=["name"], limit=5)

    exam_types = [
        ("Opener Exam", 30),
        ("Mid Term", 50),
        ("End Term", 100),
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
                continue

            for course_row in courses[:3]:
                course = course_row.course

                existing = frappe.db.exists("Assessment Plan", {
                    "student_group": group.name,
                    "course": course,
                    "assessment_group": exam_name,
                })
                if existing:
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

                    ap.flags.ignore_permissions = True
                    ap.flags.ignore_mandatory = True
                    ap.insert()
                    frappe.db.set_value("Assessment Plan", ap.name, "course", course)
                    frappe.db.set_value("Assessment Plan", ap.name, "program", group.program)
                    ap.reload()
                    ap.submit()
                    plan_count += 1
                except Exception as e:
                    print(f"  Error: {course}/{exam_name} for {group.name}: {e}")

    frappe.db.commit()
    total = frappe.db.count("Assessment Plan")
    print(f"  Created/verified {plan_count} assessment plans (total: {total})")


def create_assessment_results():
    """Create grades for ALL exam types"""
    print("\n--- Creating Assessment Results (Grades) ---")

    exam_types = [
        "Opener Exam",
        "Mid Term",
        "End Term",
    ]

    result_count = 0
    for exam_name in exam_types:
        plans = frappe.get_all("Assessment Plan",
            filters={"assessment_group": exam_name, "docstatus": 1},
            fields=["name", "student_group", "course", "maximum_assessment_score"],
        )

        if not plans:
            print(f"  No submitted {exam_name} plans")
            continue

        print(f"\n  Processing {exam_name} ({len(plans)} plans)...")

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
                        min_score = crit.maximum_score * 0.35
                        score = round(random.uniform(min_score, crit.maximum_score), 1)
                        ar.append("details", {
                            "assessment_criteria": crit.assessment_criteria,
                            "maximum_score": crit.maximum_score,
                            "score": score,
                        })

                    ar.save()
                    ar.submit()
                    result_count += 1
                except Exception as e:
                    print(f"  Error: {student.student_name}: {e}")

    frappe.db.commit()
    total = frappe.db.count("Assessment Result")
    print(f"\n  Created {result_count} new results (total in system: {total})")
