// Redirect teachers to teacher-dashboard immediately
frappe.router.on("change", function() {
    if (frappe.router.current_route[0] === "school-dashboard") {
        // Check role immediately via localStorage or session
        var user_roles = frappe.boot ? frappe.boot.user.roles : [];
        
        // If teacher (has Instructor but not Education Manager)
        if (user_roles.indexOf("Instructor") !== -1 && user_roles.indexOf("Education Manager") === -1) {
            window.location.href = "/desk/teacher-dashboard";
        }
    }
});

// Also check on page load in case routing already happened
frappe.ready(function() {
    if (window.location.pathname.indexOf("school-dashboard") !== -1) {
        var user_roles = frappe.boot ? frappe.boot.user.roles : [];
        if (user_roles.indexOf("Instructor") !== -1 && user_roles.indexOf("Education Manager") === -1) {
            window.location.href = "/desk/teacher-dashboard";
        }
    }
});
