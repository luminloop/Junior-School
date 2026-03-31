frappe.query_reports["Timetable Report"] = {
  filters: [
    {
      fieldname: "student_group",
      label: __("Stream/Class"),
      fieldtype: "Link",
      options: "Student Group",
      reqd: 1,
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
