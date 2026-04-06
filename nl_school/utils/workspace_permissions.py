"""
Workspace Permission Hooks

Provides hard restriction for workspace access based on user roles.
Users with restricted roles (Instructor, Academic Coordinator) can only
see their designated workspaces.
"""

import frappe

# Role-to-workspace mapping
ROLE_WORKSPACE_MAP = {
    "Instructor": "Teacher",
    "Academic Coordinator": "Academic Coordinator",
    "Education Manager": "Academic Coordinator",
    "Principal": "Academic Coordinator",
}

# Priority order for role matching (first match wins)
ROLE_PRIORITY = [
    "Academic Coordinator",
    "Education Manager",
    "Principal",
    "Instructor",
]


def get_allowed_workspaces(roles):
    """
    Get list of workspaces a user is allowed to see based on their roles.

    Returns:
        list: Names of workspaces the user can access, or None for full access
    """
    allowed = set()

    # Check if user has any restricted roles
    has_restricted_role = False
    for role in roles:
        if role in ROLE_WORKSPACE_MAP:
            has_restricted_role = True
            allowed.add(ROLE_WORKSPACE_MAP[role])

    # If user has no restricted roles, they see all workspaces (full access)
    if not has_restricted_role:
        return None  # None means no restriction

    return list(allowed)


def auto_assign_workspace(doc, method=None):
    """
    Auto-assign default_workspace to a user based on their roles.
    Called on User on_update.

    Priority: Academic Coordinator > Education Manager > Principal > Instructor
    If user has System Manager, don't set a workspace (full access).
    """
    # Skip if not a system user
    if doc.user_type != "System User":
        return

    # Skip if disabled
    if not doc.enabled:
        return

    roles = [r.role for r in doc.roles] if hasattr(doc, "roles") and doc.roles else frappe.get_roles(doc.name)

    # System Manager gets full access - no workspace restriction
    if "System Manager" in roles:
        if doc.default_workspace:
            doc.default_workspace = None
        return

    # Find highest priority role that maps to a workspace
    for role in ROLE_PRIORITY:
        if role in roles and role in ROLE_WORKSPACE_MAP:
            workspace = ROLE_WORKSPACE_MAP[role]
            if doc.default_workspace != workspace:
                doc.default_workspace = workspace
            return

    # No matching role - clear workspace
    if doc.default_workspace:
        doc.default_workspace = None


def get_workspace_permissions(doctype, user=None, permission_type="read"):
    """
    Permission query condition for Workspace.
    Returns a condition that restricts workspace visibility.
    """
    if user is None:
        user = frappe.session.user

    roles = frappe.get_roles(user)
    allowed_workspaces = get_allowed_workspaces(roles)

    # If None, user has full access - no restriction
    if allowed_workspaces is None:
        return ""

    # Build condition: only show allowed workspaces
    if allowed_workspaces:
        workspace_list = ", ".join(f"'{ws}'" for ws in allowed_workspaces)
        return f"`tabWorkspace`.name IN ({workspace_list})"

    # If no workspaces allowed, return impossible condition
    return "`tabWorkspace`.name = ''"


def has_workspace_permission(doc, user=None, permission_type="read"):
    """
    Check if user has permission to access a specific workspace.
    """
    if user is None:
        user = frappe.session.user

    # System Manager always has access
    if "System Manager" in frappe.get_roles(user):
        return True

    roles = frappe.get_roles(user)
    allowed_workspaces = get_allowed_workspaces(roles)

    # If None, user has full access
    if allowed_workspaces is None:
        return True

    return doc.name in allowed_workspaces
