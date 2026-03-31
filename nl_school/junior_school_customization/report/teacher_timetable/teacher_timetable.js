frappe.query_reports["Teacher Timetable"] = {
  filters: [
    {
      fieldname: "instructor",
      label: __("Teacher"),
      fieldtype: "Link",
      options: "Instructor",
      reqd: 1,
    },
    {
      fieldname: "student_group",
      label: __("Stream/Class"),
      fieldtype: "Link",
      options: "Student Group",
      get_query: function () {
        return {
          filters: {
            group_based_on: "Batch",
          },
        };
      },
    },
    {
      fieldname: "academic_term",
      label: __("Academic Term"),
      fieldtype: "Link",
      options: "Academic Term",
    },
  ],
};
