import frappe
from frappe import _
from datetime import timedelta


def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def format_time_slot(from_time, to_time):
    """Convert time to HH:MM format, handling timedelta, datetime, and string."""
    def format_single(t):
        if isinstance(t, timedelta):
            total_seconds = int(t.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours:02d}:{minutes:02d}"
        elif isinstance(t, str):
            return t[:5]
        else:
            return t.strftime("%H:%M")
    return format_single(from_time), format_single(to_time)


def get_columns():
    return [
        {"label": _("Time"), "fieldtype": "Data", "width": 120},
        {"label": _("Monday"), "fieldtype": "Data", "width": 180},
        {"label": _("Tuesday"), "fieldtype": "Data", "width": 180},
        {"label": _("Wednesday"), "fieldtype": "Data", "width": 180},
        {"label": _("Thursday"), "fieldtype": "Data", "width": 180},
        {"label": _("Friday"), "fieldtype": "Data", "width": 180},
    ]


def get_data(filters):
    if not filters:
        filters = {}

    instructor = filters.get("instructor")
    student_group = filters.get("student_group")
    academic_term = filters.get("academic_term")

    if not instructor and not student_group:
        return []

    # Build schedule filters
    schedule_filters = {}
    if instructor:
        schedule_filters["instructor"] = instructor
    if student_group:
        schedule_filters["student_group"] = student_group

    # Get academic term date range if provided
    date_range = None
    if academic_term:
        term = frappe.get_doc("Academic Term", academic_term)
        if term.term_start_date and term.term_end_date:
            date_range = [term.term_start_date, term.term_end_date]

    # Get all matching schedules
    query_filters = dict(schedule_filters)
    if date_range:
        query_filters["schedule_date"] = ["between", date_range]

    schedules = frappe.get_all(
        "Course Schedule",
        filters=query_filters,
        fields=[
            "course",
            "from_time",
            "to_time",
            "schedule_date",
            "instructor_name",
            "student_group",
            "room",
        ],
        order_by="from_time, schedule_date",
    )

    if not schedules:
        return []

    # Collect unique time slots
    time_slots_set = set()
    for s in schedules:
        start, end = format_time_slot(s.from_time, s.to_time)
        time_slots_set.add((start, end))

    time_slots = sorted(time_slots_set)

    # Build schedule map: (day_of_week, time_slot) -> schedule info
    schedule_map = {}
    for s in schedules:
        day_of_week = s.schedule_date.weekday()
        if day_of_week > 4:
            continue
        start, end = format_time_slot(s.from_time, s.to_time)
        key = (day_of_week, (start, end))
        if key not in schedule_map:
            schedule_map[key] = []
        schedule_map[key].append(s)

    # Build output rows
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    data = []

    for start, end in time_slots:
        row = {"Time": f"{start} - {end}"}
        for day_idx, day_name in enumerate(days):
            key = (day_idx, (start, end))
            entries = schedule_map.get(key, [])
            if entries:
                parts = []
                for e in entries:
                    parts.append(f"{e.course}\n{e.student_group}")
                row[day_name] = "\n---\n".join(parts)
            else:
                row[day_name] = ""
        data.append(row)

    return data
