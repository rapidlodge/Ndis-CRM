import json

import frappe


CRM_FIELDS_LAYOUT = "CRM Fields Layout"
CRM_FORM_SCRIPT = "CRM Form Script"
CRM_LEAD = "CRM Lead"
CRM_DEAL = "CRM Deal"


DEAL_LAYOUT_SECTIONS = [
    {
        "label": "NDIS Intake and Handover",
        "name": "ndis_intake_handover_section",
        "opened": True,
        "columns": [
            {
                "name": "ndis_intake_handover_col_1",
                "fields": [
                    "participant_crm_lead",
                    "ndis_handover",
                    "ndis_finance_onboarding",
                    "ndis_operations_setup",
                ],
            },
            {
                "name": "ndis_intake_handover_col_2",
                "fields": [
                    "handover_ready",
                    "finance_onboarding_ready",
                    "operations_setup_ready",
                    "participant_service_file_ready",
                ],
            },
        ],
    },
    {
        "label": "NDIS Service Readiness",
        "name": "ndis_service_readiness_section",
        "opened": False,
        "columns": [
            {
                "name": "ndis_service_readiness_col_1",
                "fields": [
                    "ndis_service_schedule_draft",
                    "ndis_roster_build_request",
                    "ndis_participant_service_file",
                    "ndis_service_session_draft",
                ],
            },
            {
                "name": "ndis_service_readiness_col_2",
                "fields": [
                    "service_schedule_ready",
                    "roster_build_ready",
                    "delivery_evidence_ready",
                    "downstream_preparation_ready",
                ],
            },
        ],
    },
    {
        "label": "NDIS V1 Readiness Freeze",
        "name": "ndis_v1_readiness_freeze_section",
        "opened": True,
        "columns": [
            {
                "name": "ndis_v1_readiness_freeze_col_1",
                "fields": [
                    "ndis_care_management_integration_run",
                    "ndis_operational_dashboard_snapshot_run",
                    "ndis_permission_workflow_hardening_run",
                    "ndis_uat_regression_evidence_pack_run",
                    "ndis_production_readiness_freeze_run",
                ],
            },
            {
                "name": "ndis_v1_readiness_freeze_col_2",
                "fields": [
                    "care_management_integration_ready",
                    "operational_dashboard_snapshot_ready",
                    "permission_workflow_hardening_ready",
                    "uat_regression_evidence_pack_ready",
                    "production_readiness_freeze_ready",
                ],
            },
        ],
    },
]


LEAD_LAYOUT_SECTIONS = [
    {
        "label": "NDIS Documents",
        "name": "ndis_documents_section",
        "opened": False,
        "columns": [
            {
                "name": "ndis_documents_col_1",
                "fields": [
                    "required_documents_generated",
                    "document_completion_percent",
                ],
            },
            {
                "name": "ndis_documents_col_2",
                "fields": [
                    "document_summary",
                    "risk_notes",
                ],
            },
        ],
    },
]


def install():
    ensure_crm_ui_layout()
    ensure_ndis_form_scripts_fixture_ready()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM UI layout metadata synced for Frappe CRM.")


def _doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
    return bool(
        frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
        or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
    )


def _load_layout(name):
    doc = frappe.get_doc(CRM_FIELDS_LAYOUT, name)
    try:
        layout = json.loads(doc.layout or "[]")
    except Exception:
        layout = []

    if not isinstance(layout, list):
        layout = []

    if not layout:
        layout = [{"name": "first_tab", "sections": []}]

    if "sections" not in layout[0] or not isinstance(layout[0].get("sections"), list):
        layout[0]["sections"] = []

    return doc, layout


def _section_exists(layout, section_name):
    for tab in layout:
        for section in tab.get("sections") or []:
            if section.get("name") == section_name:
                return True
    return False


def _layout_fieldnames(layout):
    fields = set()
    for tab in layout:
        for section in tab.get("sections") or []:
            for column in section.get("columns") or []:
                fields.update(column.get("fields") or [])
    return fields


def _remove_sections(layout, section_names):
    section_names = set(section_names)
    for tab in layout:
        tab["sections"] = [
            section
            for section in tab.get("sections") or []
            if section.get("name") not in section_names
        ]


def _filter_section_fields(doctype, section, existing_fields):
    section = dict(section)
    columns = []
    for column in section.get("columns") or []:
        column = dict(column)
        column["fields"] = [
            fieldname
            for fieldname in column.get("fields") or []
            if _field_exists(doctype, fieldname)
            and fieldname not in existing_fields
        ]
        if column["fields"]:
            columns.append(column)

    section["columns"] = columns
    return section if columns else None


def _append_sections(layout_name, doctype, sections):
    if not _doctype_exists(CRM_FIELDS_LAYOUT) or not frappe.db.exists(CRM_FIELDS_LAYOUT, layout_name):
        print(f"CRM Fields Layout missing: {layout_name}")
        return 0

    doc, layout = _load_layout(layout_name)
    created = 0
    managed_section_names = [section["name"] for section in sections]
    _remove_sections(layout, managed_section_names)
    existing_fields = _layout_fieldnames(layout)

    for section in sections:
        section = _filter_section_fields(doctype, section, existing_fields)
        if not section:
            continue

        layout[0]["sections"].append(section)
        existing_fields.update(
            fieldname
            for column in section.get("columns") or []
            for fieldname in column.get("fields") or []
        )
        created += 1

    doc.layout = json.dumps(layout, indent=2)
    doc.save(ignore_permissions=True)
    print(f"Updated {layout_name}: synced {created} NDIS section(s).")

    return created


def ensure_crm_ui_layout():
    _append_sections("CRM Deal-Data Fields", CRM_DEAL, DEAL_LAYOUT_SECTIONS)
    _append_sections("CRM Lead-Data Fields", CRM_LEAD, LEAD_LAYOUT_SECTIONS)


def ensure_ndis_form_scripts_fixture_ready():
    missing = []
    for name in ["NDIS CRM Lead Actions", "NDIS CRM Deal Actions"]:
        if not frappe.db.exists(CRM_FORM_SCRIPT, name):
            missing.append(name)

    if missing:
        frappe.throw("Missing required CRM Form Script records: " + ", ".join(missing))

    print("NDIS CRM Lead and Deal form scripts are present.")


def health_check():
    print("---- NDIS CRM UI Layout Health Check ----")

    for name in ["CRM Deal-Data Fields", "CRM Lead-Data Fields"]:
        exists = _doctype_exists(CRM_FIELDS_LAYOUT) and frappe.db.exists(CRM_FIELDS_LAYOUT, name)
        print(f"{name}: {'OK' if exists else 'MISSING'}")

    checks = {
        "CRM Deal-Data Fields": [
            "ndis_handover",
            "ndis_finance_onboarding",
            "ndis_operations_setup",
            "ndis_uat_regression_evidence_pack_run",
            "ndis_production_readiness_freeze_run",
            "production_readiness_freeze_ready",
        ],
        "CRM Lead-Data Fields": [
            "is_ndis_participant",
            "ndis_number",
            "required_documents_generated",
            "document_completion_percent",
        ],
    }

    for layout_name, fields in checks.items():
        layout = frappe.db.get_value(CRM_FIELDS_LAYOUT, layout_name, "layout") if _doctype_exists(CRM_FIELDS_LAYOUT) else ""
        for fieldname in fields:
            print(f"{layout_name} field {fieldname}: {'OK' if fieldname in (layout or '') else 'MISSING'}")

    for script in ["NDIS CRM Lead Actions", "NDIS CRM Deal Actions"]:
        print(f"CRM Form Script {script}: {'OK' if frappe.db.exists(CRM_FORM_SCRIPT, script) else 'MISSING'}")

    print("---- End NDIS CRM UI Layout Health Check ----")
