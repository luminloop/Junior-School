import frappe
from frappe import _

def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data

def get_columns():
	return [
		{
			"label": _("Time/Day"),
			"fieldtype": "Data",
			"width": 100
		},
		{
			"label": _("Monday"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Tuesday"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Wednesday"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Thursday"),
			"fieldtype": "Data",
			"width": 150
		},
		{
			"label": _("Friday"),
			"fieldtype": "Data",
			"width": 150
		}
	]

def get_data(filters):
	if not filters:
		filters = {}
	
	student_group = filters.get("student_group")
	academic_term = filters.get("academic_term")
	
	if not student_group or not academic_term:
		return []
	
	# Get time slots from Timetable Generator (we could also use a standard set)
	# For simplicity, we'll use a standard set of time slots
	time_slots = [
		("08:00", "08:45"),
		("08:45", "09:30"),
		("09:30", "10:15"),
		("10:15", "10:30"),  # Break
		("10:30", "11:15"),
		("11:15", "12:00"),
		("12:00", "13:00"),  # Lunch
		("13:00", "13:45"),
		("13:45", "14:30"),
		("14:30", "15:15"),
		("15:15", "16:00")
	]
	
	# Get the start and end date of the academic term
	term = frappe.get_doc("Academic Term", academic_term)
	start_date = term.term_start_date
	end_date = term.term_end_date
	
	# Generate list of dates for Monday-Friday of the term
	# We'll just take the first week for simplicity, or we could aggregate by day of week
	# Let's do: for each day of week (Mon-Fri), show the schedule for that day of week (first occurrence)
	# But better: show a composite timetable (what is typically scheduled on each day of week)
	# We'll group by day of week and time slot, and show the course that is scheduled most frequently
	
	# Get all course schedules for the student group in the term
	schedules = frappe.get_all(
		"Course Schedule",
		filters={
			"student_group": student_group,
			"schedule_date": ["between", [start_date, end_date]],
			"docstatus": 1
		},
		fields=["course", "from_time", "to_time", "schedule_date", "instructor_name"]
	)
	
	# Organize by day of week and time slot
	# We'll create a dict: (day_of_week, time_slot) -> list of courses
	from datetime import datetime
	schedule_map = {}
	
	for s in schedules:
		# Get day of week (0=Monday, 4=Friday)
		day_of_week = s.schedule_date.weekday()
		if day_of_week > 4:  # Skip weekend
			continue
		time_slot = (s.from_time.strftime("%H:%M"), s.to_time.strftime("%H:%M"))
		key = (day_of_week, time_slot)
		if key not in schedule_map:
			schedule_map[key] = []
		schedule_map[key].append(s)
	
	# Build data rows for each time slot
	data = []
	days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
	
	for start_time, end_time in time_slots:
		row = {
			"Time/Day": f"{start_time} - {end_time}"
		}
		for day_idx, day_name in enumerate(days):
			key = (day_idx, (start_time, end_time))
			courses = schedule_map.get(key, [])
			if courses:
				# If multiple, take the first one (or we could join)
				course = courses[0]
				display = f"{course.course}\n({course.instructor_name})"
				row[day_name] = display
			else:
				row[day_name] = ""
		data.append(row)
	
	return data
