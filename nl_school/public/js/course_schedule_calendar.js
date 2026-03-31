// Override Course Schedule calendar with better filters
frappe.views.calendar["Course Schedule"] = {
  field_map: {
    start: "from_time",
    end: "to_time",
    id: "name",
    title: "title",
    allDay: "allDay",
  },
  gantt: false,
  order_by: "schedule_date",
  filters: [
    {
      fieldtype: "Link",
      fieldname: "student_group",
      options: "Student Group",
      label: __("Stream/Class"),
      get_query: function () {
        return {
          filters: {
            group_based_on: "Batch",
          },
        };
      },
    },
    {
      fieldtype: "Link",
      fieldname: "instructor",
      options: "Instructor",
      label: __("Teacher"),
    },
    {
      fieldtype: "Link",
      fieldname: "course",
      options: "Course",
      label: __("Subject"),
    },
    {
      fieldtype: "Link",
      fieldname: "room",
      options: "Room",
      label: __("Room"),
    },
  ],
  get_events_method: "education.education.api.get_course_schedule_events",
};
