frappe.ui.form.on("Course Schedule", {
  setup(frm) {
    // Only show batch groups (streams) in student_group filter
    frm.set_query("student_group", function () {
      let filters = { group_based_on: "Batch" };
      if (frm.doc.company) {
        filters.company = frm.doc.company;
      }
      return { filters };
    });

    frm.set_query("room", function () {
      if (frm.doc.company) {
        return { filters: { company: frm.doc.company } };
      }
    });
  },

  student_group(frm) {
    // Auto-set course filter based on program when student group changes
    if (frm.doc.student_group && frm.doc.program) {
      frm.set_query("course", function () {
        return {
          query:
            "education.education.doctype.program_enrollment.program_enrollment.get_program_courses",
          filters: { program: frm.doc.program },
        };
      });
    }
  },
});
