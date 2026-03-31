import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


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

	student_group = filters.get("student_group")
	academic_term = filters.get("academic_term")

	if not student_group:
		return []

	# Build schedule query
	schedule_filters = {"student_group": student_group}

	if academic_term:
		term = frappe.get_doc("Academic Term", academic_term)
		if term.term_start_date and term.term_end_date:
			schedule_filters["schedule_date"] = [
				"between",
				[term.term_start_date, term.term_end_date],
			]

	schedules = frappe.get_all(
		"Course Schedule",
		filters=schedule_filters,
		fields=[
			"course",
			"from_time",
			"to_time",
			"schedule_date",
			"instructor_name",
			"room",
		],
		order_by="from_time, schedule_date",
	)

	if not schedules:
		return []

	# Collect unique time slots
	time_slots_set = set()
	for s in schedules:
		if isinstance(s.from_time, str):
			start = s.from_time[:5]
			end = s.to_time[:5]
		else:
			start = s.from_time.strftime("%H:%M")
			end = s.to_time.strftime("%H:%M")
		time_slots_set.add((start, end))

	time_slots = sorted(time_slots_set)

	# Build schedule map: (day_of_week, time_slot) -> schedule info
	schedule_map = {}
	for s in schedules:
		day_of_week = s.schedule_date.weekday()
		if day_of_week > 4:
			continue
		if isinstance(s.from_time, str):
			start = s.from_time[:5]
			end = s.to_time[:5]
		else:
			start = s.from_time.strftime("%H:%M")
			end = s.to_time.strftime("%H:%M")
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
					parts.append(f"{e.course}\n({e.instructor_name})")
				row[day_name] = "\n---\n".join(parts)
			else:
				row[day_name] = ""
		data.append(row)

	return data
