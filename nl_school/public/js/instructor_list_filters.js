// Auto-filter list views for Instructor role
// When a teacher views Assessment Results, Attendance, or Course Schedule,
// it automatically filters to only show their assigned student groups

frappe.listview_settings["Assessment Result"] = {
  onload(listview) {
    if (frappe.user.has_role("Instructor") && !frappe.user.has_role("Academic Coordinator") && !frappe.user.has_role("Principal")) {
      // Get instructor's student groups
      frappe.call({
        method: "nl_school.junior_school_customization.controllers.user_permissions.get_instructor_student_groups",
        callback(r) {
          if (r.message && r.message.length > 0) {
            const groups = r.message;
            // Set default filter
            listview.filter_area.add([
              ["Assessment Result", "student_group", "in", groups]
            ]);
          }
        }
      });
    }
  }
};

frappe.listview_settings["Student Attendance"] = {
  onload(listview) {
    if (frappe.user.has_role("Instructor") && !frappe.user.has_role("Academic Coordinator") && !frappe.user.has_role("Principal")) {
      frappe.call({
        method: "nl_school.junior_school_customization.controllers.user_permissions.get_instructor_student_groups",
        callback(r) {
          if (r.message && r.message.length > 0) {
            listview.filter_area.add([
              ["Student Attendance", "student_group", "in", r.message]
            ]);
          }
        }
      });
    }
  }
};

frappe.listview_settings["Course Schedule"] = {
  onload(listview) {
    if (frappe.user.has_role("Instructor") && !frappe.user.has_role("Academic Coordinator") && !frappe.user.has_role("Principal")) {
      frappe.call({
        method: "nl_school.junior_school_customization.controllers.user_permissions.get_instructor_student_groups",
        callback(r) {
          if (r.message && r.message.length > 0) {
            listview.filter_area.add([
              ["Course Schedule", "student_group", "in", r.message]
            ]);
          }
        }
      });
    }
  }
};

frappe.listview_settings["Student Log"] = {
  onload(listview) {
    if (frappe.user.has_role("Instructor") && !frappe.user.has_role("Academic Coordinator") && !frappe.user.has_role("Principal")) {
      frappe.call({
        method: "nl_school.junior_school_customization.controllers.user_permissions.get_instructor_students",
        callback(r) {
          if (r.message && r.message.length > 0) {
            listview.filter_area.add([
              ["Student Log", "student", "in", r.message]
            ]);
          }
        }
      });
    }
  }
};
