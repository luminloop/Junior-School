frappe.router.on("change", function() {
    if (frappe.router.current_route[0] === "school-dashboard") {
        frappe.call({
            method: "nl_school.junior_school_customization.page.school_dashboard.school_dashboard.check_role",
            callback: function(r) {
                if (r.message === "teacher") {
                    window.location.href = "/desk/teacher-dashboard";
                }
            }
        });
    }
});
