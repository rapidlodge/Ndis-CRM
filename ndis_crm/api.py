import frappe


@frappe.whitelist()
def has_app_permission(user=None):
    """
    Controls whether NDIS CRM appears on the Frappe Apps Page.

    Portable and safe:
    - Does not modify any core app.
    - Administrator can see it.
    - System Manager can see it.
    - NDIS CRM roles can see it.
    - Any System User / staff user can see the app icon.
    - Guest / Website User cannot see it.
    """

    user = user or frappe.session.user

    if not user or user == "Guest":
        return False

    if user == "Administrator":
        return True

    user_type = frappe.db.get_value("User", user, "user_type")

    if user_type != "System User":
        return False

    allowed_roles = {
        "System Manager",
        "NDIS CRM Manager",
        "NDIS Intake Officer",
        "NDIS Service Manager",
        "NDIS Plan Management Officer",
        "NDIS CRM Read Only",
    }

    user_roles = set(frappe.get_roles(user))

    if allowed_roles.intersection(user_roles):
        return True

    # Show the app icon to all internal staff users.
    # Actual document access is still controlled by DocType permissions.
    return True


@frappe.whitelist()
def debug_app_permission(user=None):
    user = user or frappe.session.user

    return {
        "session_user": frappe.session.user,
        "checked_user": user,
        "user_type": frappe.db.get_value("User", user, "user_type") if user else None,
        "roles": frappe.get_roles(user) if user else [],
        "has_permission": has_app_permission(user),
    }
