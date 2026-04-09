// Simple redirect for teachers to their dashboard on initial login
// Full desk access is allowed

(function() {
    "use strict";

    function getUserRoles() {
        if (frappe.boot && frappe.boot.user && frappe.boot.user.roles) {
            return frappe.boot.user.roles;
        }
        return [];
    }

    function isTeacher() {
        var user_roles = getUserRoles();
        return user_roles.indexOf("Instructor") !== -1 && 
               user_roles.indexOf("Education Manager") === -1 &&
               user_roles.indexOf("Principal") === -1 &&
               user_roles.indexOf("System Manager") === -1;
    }

    function isCoordinator() {
        var user_roles = getUserRoles();
        return user_roles.indexOf("Academic Coordinator") !== -1 && 
               user_roles.indexOf("Education Manager") === -1 &&
               user_roles.indexOf("Principal") === -1 &&
               user_roles.indexOf("System Manager") === -1;
    }

    // Redirect to appropriate dashboard if on generic home page
    function redirectToHomeDashboard() {
        var currentPath = window.location.pathname;
        
        // Only redirect if on the generic /app or /app/ page
        if (currentPath === "/app" || currentPath === "/app/") {
            if (isTeacher()) {
                window.location.href = "/app/teacher-dashboard";
                return;
            }
            
            if (isCoordinator()) {
                window.location.href = "/app/coordinator-dashboard";
                return;
            }
        }
    }

    // Apply on page load
    if (typeof frappe !== 'undefined') {
        frappe.ready(function() {
            setTimeout(redirectToHomeDashboard, 500);
        });
    }

    // Check periodically until frappe.boot is available
    var checkCount = 0;
    var checkInterval = setInterval(function() {
        checkCount++;
        if (checkCount > 10) {
            clearInterval(checkInterval);
            return;
        }
        
        if (typeof frappe !== 'undefined' && frappe.boot && frappe.boot.user) {
            clearInterval(checkInterval);
            setTimeout(redirectToHomeDashboard, 300);
        }
    }, 300);

})();
