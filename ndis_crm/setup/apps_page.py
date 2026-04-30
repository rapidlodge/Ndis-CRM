import frappe


APP_NAME = "ndis_crm"
APP_TITLE = "NDIS CRM"
APP_ROUTE = "/app/ndis-crm"
APP_LOGO = "/assets/ndis_crm/images/ndis_crm.svg"
WORKSPACE_NAME = "NDIS CRM"
MODULE_NAME = "Ndis Crm"


def desktop_icon_available():
    return frappe.db.exists("DocType", "Desktop Icon")


def get_df(fieldname):
    return frappe.get_meta("Desktop Icon").get_field(fieldname)


def has_field(fieldname):
    return bool(get_df(fieldname))


def is_url_safe_field(fieldname):
    df = get_df(fieldname)

    if not df:
        return False

    return df.fieldtype in [
        "Data",
        "Small Text",
        "Text",
        "Code",
        "Read Only",
    ]


def set_field_if_exists(doc, fieldname, value):
    if has_field(fieldname):
        doc.set(fieldname, value)


def set_url_field_if_safe(doc, fieldname, value):
    """
    Only put URL/route values into plain text fields.
    Never put URL/route values into Link or Dynamic Link fields.
    """
    if is_url_safe_field(fieldname):
        doc.set(fieldname, value)


def get_icon_doc():
    existing = frappe.db.exists("Desktop Icon", {"app": APP_NAME})

    if existing:
        return frappe.get_doc("Desktop Icon", existing)

    existing = frappe.db.exists("Desktop Icon", {"label": APP_TITLE})

    if existing:
        return frappe.get_doc("Desktop Icon", existing)

    return frappe.new_doc("Desktop Icon")


def get_link_type_options():
    df = get_df("link_type")

    if not df or not df.options:
        return []

    return [x.strip() for x in df.options.split("\n") if x.strip()]


def configure_link_target(icon):
    """
    Correct handling:
    - link_to must point to a real document, not a URL.
    - URL route can only go into plain text route/link fields.
    """

    # Safe URL fields only
    set_url_field_if_safe(icon, "route", APP_ROUTE)
    set_url_field_if_safe(icon, "link", APP_ROUTE)
    set_url_field_if_safe(icon, "url", APP_ROUTE)

    # Valid Link/Dynamic Link handling
    if not has_field("link_type") or not has_field("link_to"):
        return

    options = get_link_type_options()

    if "Workspace" in options and frappe.db.exists("Workspace", WORKSPACE_NAME):
        icon.link_type = "Workspace"
        icon.link_to = WORKSPACE_NAME
        return

    if "Module Def" in options and frappe.db.exists("Module Def", MODULE_NAME):
        icon.link_type = "Module Def"
        icon.link_to = MODULE_NAME
        return

    if "Page" in options and frappe.db.exists("Page", "ndis-crm"):
        icon.link_type = "Page"
        icon.link_to = "ndis-crm"
        return

    # If no valid option exists, leave link_type/link_to untouched.
    # This avoids breaking insert/save on version differences.


def install():
    """
    Clean Desktop Icon setup for NDIS CRM.

    This is a compatibility layer only.
    Main Apps Page entry still comes from hooks.py add_to_apps_screen.
    """

    if not desktop_icon_available():
        print("Desktop Icon DocType not found. Nothing to install.")
        return

    icon = get_icon_doc()

    set_field_if_exists(icon, "label", APP_TITLE)
    set_field_if_exists(icon, "app", APP_NAME)
    set_field_if_exists(icon, "hidden", 0)
    set_field_if_exists(icon, "standard", 0)
    set_field_if_exists(icon, "idx", 100)
    set_field_if_exists(icon, "logo_url", APP_LOGO)
    set_field_if_exists(icon, "icon", "organization")
    set_field_if_exists(icon, "color", "blue")

    configure_link_target(icon)

    if icon.is_new():
        icon.insert(ignore_permissions=True)
        print("Created Desktop Icon for NDIS CRM.")
    else:
        icon.save(ignore_permissions=True)
        print("Updated Desktop Icon for NDIS CRM.")

    frappe.db.commit()
    frappe.clear_cache()

    print("NDIS CRM Apps Page compatibility setup completed.")


def cleanup():
    """
    Removes only NDIS CRM Desktop Icon records.
    Does not touch any other app.
    """

    if not desktop_icon_available():
        print("Desktop Icon DocType not found. Nothing to clean.")
        return

    names = frappe.get_all(
        "Desktop Icon",
        filters=[
            ["Desktop Icon", "app", "=", APP_NAME]
        ],
        pluck="name",
    )

    names += frappe.get_all(
        "Desktop Icon",
        filters=[
            ["Desktop Icon", "label", "=", APP_TITLE]
        ],
        pluck="name",
    )

    names = list(set(names))

    for name in names:
        frappe.delete_doc("Desktop Icon", name, ignore_permissions=True, force=True)
        print(f"Deleted Desktop Icon: {name}")

    frappe.db.commit()
    frappe.clear_cache()

    print("NDIS CRM Desktop Icon cleanup completed.")


def health_check():
    print("---- NDIS CRM Apps Page Health Check ----")

    print("Hook check:")
    found_hook = False

    for app in frappe.get_hooks("add_to_apps_screen"):
        if app.get("name") == APP_NAME:
            found_hook = True
            print(f"  Hook OK: {app}")

    if not found_hook:
        print("  Hook MISSING for ndis_crm")

    print("Desktop Icon check:")

    if not desktop_icon_available():
        print("  Desktop Icon DocType missing")
        print("---- End Health Check ----")
        return

    icons = frappe.get_all(
        "Desktop Icon",
        filters=[
            ["Desktop Icon", "app", "=", APP_NAME]
        ],
        fields=["name", "label", "app", "hidden"],
    )

    if not icons:
        print("  Desktop Icon MISSING for ndis_crm")
    else:
        for icon in icons:
            print(f"  Desktop Icon OK: {icon}")

    print("Workspace check:")
    print(f"  Workspace {WORKSPACE_NAME}: {'OK' if frappe.db.exists('Workspace', WORKSPACE_NAME) else 'MISSING'}")

    print("Module check:")
    print(f"  Module Def {MODULE_NAME}: {'OK' if frappe.db.exists('Module Def', MODULE_NAME) else 'MISSING'}")

    print("Expected logo:")
    print(f"  {APP_LOGO}")

    print("---- End Health Check ----")
