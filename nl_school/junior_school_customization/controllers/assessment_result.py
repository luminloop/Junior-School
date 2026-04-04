import frappe


def before_submit(doc, method):
    """Hook called before Assessment Result is submitted"""
    if not doc.academic_term:
        doc.academic_term = frappe.db.get_value(
            "Education Settings", None, "current_academic_term"
        )


def on_submit(doc, method):
    """Hook called when Assessment Result is submitted - calculates rankings"""
    calculate_and_update_rankings(doc)


def calculate_and_update_rankings(doc):
    """
    Calculate class rank and grade-level rank for the submitted assessment result.
    
    Class Rank: Ranking within the student_group (class/section)
    Grade Level Rank: Ranking within the program (grade level) across all sections
    
    Rankings are based on total_score for the same:
    - course
    - assessment_plan
    - academic_term
    - academic_year
    """
    if not doc.total_score:
        return
    
    # Get all submitted assessment results for the same assessment context
    base_filters = {
        "assessment_plan": doc.assessment_plan,
        "course": doc.course,
        "academic_term": doc.academic_term,
        "academic_year": doc.academic_year,
        "docstatus": 1,  # Only submitted results
    }
    
    # Calculate Class Rank (within student_group)
    if doc.student_group:
        class_results = frappe.get_all(
            "Assessment Result",
            filters={**base_filters, "student_group": doc.student_group},
            fields=["name", "student", "total_score"],
            order_by="total_score desc",
        )
        
        class_rank = _calculate_rank(doc.name, class_results)
        class_total = len(class_results)
        
        # Update the document directly in database to avoid recursion
        frappe.db.set_value(
            "Assessment Result",
            doc.name,
            {
                "class_rank": class_rank,
                "class_total_students": class_total,
            },
            update_modified=False,
        )
        
        # Also update rankings for all other students in the same class
        # (their ranks may have changed due to this new submission)
        _update_all_class_rankings(class_results)
    
    # Calculate Grade Level Rank (within program)
    if doc.program:
        grade_results = frappe.get_all(
            "Assessment Result",
            filters={**base_filters, "program": doc.program},
            fields=["name", "student", "total_score"],
            order_by="total_score desc",
        )
        
        grade_rank = _calculate_rank(doc.name, grade_results)
        grade_total = len(grade_results)
        
        # Update the document directly in database
        frappe.db.set_value(
            "Assessment Result",
            doc.name,
            {
                "grade_level_rank": grade_rank,
                "grade_level_total_students": grade_total,
            },
            update_modified=False,
        )
        
        # Update rankings for all students in the same program
        _update_all_grade_level_rankings(grade_results)


def _calculate_rank(doc_name, results):
    """
    Calculate rank for a specific document within a list of results.
    Handles ties by giving the same rank to students with equal scores.
    """
    if not results:
        return 0
    
    # Sort by total_score descending
    sorted_results = sorted(results, key=lambda x: x.total_score or 0, reverse=True)
    
    current_rank = 0
    previous_score = None
    skip_count = 0
    
    for result in sorted_results:
        score = result.total_score or 0
        
        if score != previous_score:
            current_rank += 1 + skip_count
            skip_count = 0
        else:
            skip_count += 1
        
        if result.name == doc_name:
            return current_rank
        
        previous_score = score
    
    return 0


def _update_all_class_rankings(results):
    """Update class rankings for all students in the results list"""
    if not results:
        return
    
    sorted_results = sorted(results, key=lambda x: x.total_score or 0, reverse=True)
    total_students = len(sorted_results)
    
    current_rank = 0
    previous_score = None
    skip_count = 0
    
    for result in sorted_results:
        score = result.total_score or 0
        
        if score != previous_score:
            current_rank += 1 + skip_count
            skip_count = 0
        else:
            skip_count += 1
        
        frappe.db.set_value(
            "Assessment Result",
            result.name,
            {
                "class_rank": current_rank,
                "class_total_students": total_students,
            },
            update_modified=False,
        )
        
        previous_score = score


def _update_all_grade_level_rankings(results):
    """Update grade-level rankings for all students in the results list"""
    if not results:
        return
    
    sorted_results = sorted(results, key=lambda x: x.total_score or 0, reverse=True)
    total_students = len(sorted_results)
    
    current_rank = 0
    previous_score = None
    skip_count = 0
    
    for result in sorted_results:
        score = result.total_score or 0
        
        if score != previous_score:
            current_rank += 1 + skip_count
            skip_count = 0
        else:
            skip_count += 1
        
        frappe.db.set_value(
            "Assessment Result",
            result.name,
            {
                "grade_level_rank": current_rank,
                "grade_level_total_students": total_students,
            },
            update_modified=False,
        )
        
        previous_score = score
