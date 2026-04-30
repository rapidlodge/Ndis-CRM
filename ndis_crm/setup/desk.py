import json
import frappe


WORKSPACE_NAME = "NDIS CRM"
MODULE_NAME = "Ndis Crm"


def has_field(doctype, fieldname):
    return bool(frappe.get_meta(doctype).get_field(fieldname))


def set_if_exists(doc, fieldname, value):
    if has_field(doc.doctype, fieldname):
        doc.set(fieldname, value)


def clear_table_if_exists(doc, fieldname):
    df = frappe.get_meta(doc.doctype).get_field(fieldname)
    if df and df.fieldtype == "Table":
        doc.set(fieldname, [])


def filter_child_row(child_doctype, row):
    valid_fields = {df.fieldname for df in frappe.get_meta(child_doctype).fields}
    return {k: v for k, v in row.items() if k in valid_fields}


def append_table_row(doc, table_fieldname, row):
    df = frappe.get_meta(doc.doctype).get_field(table_fieldname)

    if not df or df.fieldtype != "Table":
        return

    clean_row = filter_child_row(df.options, row)
    doc.append(table_fieldname, clean_row)


def doctype_exists(doctype):
    return frappe.db.exists("DocType", doctype)


def make_shortcut(label, doctype, doc_view="List"):
    if not doctype_exists(doctype):
        return None

    return {
        "label": label,
        "type": "DocType",
        "link_to": doctype,
        "doc_view": doc_view,
        "color": "Blue"
    }


def make_link(label, doctype):
    if not doctype_exists(doctype):
        return None

    return {
        "label": label,
        "type": "Link",
        "link_type": "DocType",
        "link_to": doctype,
        "hidden": 0,
        "onboard": 0,
        "is_query_report": 0,
        "link_count": 0,
        "dependencies": ""
    }


def install():
    create_or_update_workspace()
    frappe.db.commit()
    frappe.clear_cache()
    print("NDIS CRM Desk workspace installed successfully.")


def create_or_update_workspace():
    if frappe.db.exists("Workspace", WORKSPACE_NAME):
        workspace = frappe.get_doc("Workspace", WORKSPACE_NAME)
        print(f"Updating existing Workspace: {WORKSPACE_NAME}")
    else:
        workspace = frappe.new_doc("Workspace")
        print(f"Creating Workspace: {WORKSPACE_NAME}")

    set_if_exists(workspace, "label", WORKSPACE_NAME)
    set_if_exists(workspace, "title", WORKSPACE_NAME)
    set_if_exists(workspace, "module", MODULE_NAME)
    set_if_exists(workspace, "public", 1)
    set_if_exists(workspace, "for_user", "")
    set_if_exists(workspace, "parent_page", "")
    set_if_exists(workspace, "is_default", 0)
    set_if_exists(workspace, "indicator_color", "blue")
    set_if_exists(workspace, "icon", "organization")
    set_if_exists(workspace, "sequence_id", 25)
    set_if_exists(workspace, "restrict_to_domain", "")

    for table_field in [
        "shortcuts",
        "links",
        "roles",
        "charts",
        "number_cards",
        "custom_blocks"
    ]:
        clear_table_if_exists(workspace, table_field)

    shortcuts = [
        make_shortcut("New Participant Intake", "NDIS Participant Intake", "New"),
        make_shortcut("Participant Intakes", "NDIS Participant Intake", "List"),
        make_shortcut("NDIS Service Lines", "NDIS Service Line", "List"),
        make_shortcut("Desk Leads", "Lead", "List"),
        make_shortcut("Desk Opportunities", "Opportunity", "List"),
        make_shortcut("CRM Leads", "CRM Lead", "List"),
        make_shortcut("CRM Deals", "CRM Deal", "List"),
    ]

    shortcuts = [s for s in shortcuts if s]

    for shortcut in shortcuts:
        append_table_row(workspace, "shortcuts", shortcut)

    card_rows = [
        {"label": "NDIS Intake", "type": "Card Break", "hidden": 0},
        make_link("Participant Intake", "NDIS Participant Intake"),
        make_link("NDIS Service Line", "NDIS Service Line"),

        {"label": "ERPNext CRM", "type": "Card Break", "hidden": 0},
        make_link("Lead", "Lead"),
        make_link("Opportunity", "Opportunity"),

        {"label": "Frappe CRM", "type": "Card Break", "hidden": 0},
        make_link("CRM Lead", "CRM Lead"),
        make_link("CRM Deal", "CRM Deal"),
    ]

    for row in card_rows:
        if row:
            append_table_row(workspace, "links", row)

    content = [
        {
            "type": "header",
            "data": {
                "text": "NDIS CRM",
                "level": 3,
                "col": 12
            }
        },
        {
            "type": "header",
            "data": {
                "text": "Quick Actions",
                "level": 4,
                "col": 12
            }
        }
    ]

    for shortcut in shortcuts:
        content.append({
            "type": "shortcut",
            "data": {
                "shortcut_name": shortcut["label"],
                "col": 3
            }
        })

    content.extend([
        {
            "type": "spacer",
            "data": {
                "col": 12
            }
        },
        {
            "type": "header",
            "data": {
                "text": "Modules",
                "level": 4,
                "col": 12
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "NDIS Intake",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "ERPNext CRM",
                "col": 4
            }
        },
        {
            "type": "card",
            "data": {
                "card_name": "Frappe CRM",
                "col": 4
            }
        }
    ])

    set_if_exists(workspace, "content", json.dumps(content))

    if workspace.is_new():
        workspace.insert(ignore_permissions=True)
    else:
        workspace.save(ignore_permissions=True)

    print("Workspace created / updated.")


def health_check():
    print("---- NDIS CRM Desk Health Check ----")

    print(f"Workspace {WORKSPACE_NAME}: {'OK' if frappe.db.exists('Workspace', WORKSPACE_NAME) else 'MISSING'}")
    print(f"Module Def {MODULE_NAME}: {'OK' if frappe.db.exists('Module Def', MODULE_NAME) else 'MISSING'}")

    for dt in [
        "NDIS Participant Intake",
        "NDIS Service Line",
        "NDIS Service Interest",
        "Lead",
        "Opportunity",
        "CRM Lead",
        "CRM Deal"
    ]:
        if not frappe.db.exists("DocType", dt):
            print(f"{dt}: MISSING")
            continue

        meta = frappe.get_meta(dt)
        table_status = "Child Table" if meta.istable else "Main DocType"
        print(f"{dt}: OK | {table_status} | Module: {meta.module}")

    print("---- End Health Check ----")
