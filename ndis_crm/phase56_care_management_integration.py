import frappe
from frappe import _
from frappe.utils import now


CRM_DEAL = "CRM Deal"
PARTICIPANT_SERVICE_FILE = "NDIS Participant Service File"

POST_CLOSURE_ROUTING_FINALISATION_RUN = "NDIS CRM Post Closure Routing Finalisation Run"
POST_CLOSURE_ROUTING_PREPARATION_RUN = "NDIS CRM Post Closure Routing Preparation Run"
RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN = "NDIS CRM Recovery Outcome Closure Finalisation Run"
RECOVERY_OUTCOME_CLOSURE_DRAFT_RUN = "NDIS CRM Recovery Outcome Closure Draft Run"
RECOVERY_OUTCOME_CLOSURE_PREPARATION_RUN = "NDIS CRM Recovery Outcome Closure Preparation Run"
RECOVERY_OUTCOME_ACTION_COMPLETION_RUN = "NDIS CRM Recovery Outcome Action Completion Run"

CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"
CARE_MANAGEMENT_INTEGRATION_LINE = "NDIS CRM Care Management Integration Line"

COMMUNICATION = "Communication"
EMAIL_QUEUE = "Email Queue"
EVENT = "Event"
TODO = "ToDo"
TASK = "Task"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
JOURNAL_ENTRY = "Journal Entry"
GL_ENTRY = "GL Entry"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_RECOVERY_CASE = "NDIS Recovery Case"

READY_STATUSES = [
    "Ready for Integration",
    "Integration Approved",
    "Integration Completed",
]

APPROVED_STATUSES = [
    "Integration Approved",
    "Integration Completed",
]

ALLOWED_ROLES = {
    "Administrator",
    "System Manager",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
    "Accounts Manager",
    "Accounts User",
}


INTEGRATION_AREAS = [
    {
        "area": "Care Management Profile",
        "require_record": 1,
        "description": "Link the main participant care management profile from the separate Care Management module.",
    },
    {
        "area": "Care Plan / Daily Activity Plan",
        "require_record": 1,
        "description": "Link the active care plan or daily activity plan.",
    },
    {
        "area": "Medication Plan",
        "require_record": 0,
        "description": "Link medication plan if applicable for the participant.",
    },
    {
        "area": "Incident Management",
        "require_record": 0,
        "description": "Link incident register or incident management area if applicable.",
    },
    {
        "area": "NDIS Task Library",
        "require_record": 0,
        "description": "Link task library or standard care task setup if applicable.",
    },
    {
        "area": "Staff Assignment / Responsibility",
        "require_record": 0,
        "description": "Link staff responsibility or assignment source if applicable.",
    },
    {
        "area": "Service Delivery / Shift Execution",
        "require_record": 0,
        "description": "Link delivery execution source if available.",
    },
    {
        "area": "Progress Notes / Evidence",
        "require_record": 0,
        "description": "Link progress note or evidence source if available.",
    },
]


def _check_role():
    if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this care management integration action."))


def _doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
    return bool(
        frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
        or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
    )


def _db_set_if_field(doctype, name, fieldname, value):
    if name and _field_exists(doctype, fieldname):
        frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)


def _get_first_existing_value(doctype, name, fields):
    if not name:
        return None

    for fieldname in fields:
        if _field_exists(doctype, fieldname):
            value = frappe.db.get_value(doctype, name, fieldname)
            if value:
                return value

    return None


def _existing_run_for_post_closure_finalisation(post_closure_routing_finalisation_run):
    if not _doctype_exists(CARE_MANAGEMENT_INTEGRATION_RUN):
        return None

    existing = _get_first_existing_value(
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        post_closure_routing_finalisation_run,
        [
            "ndis_care_management_integration_run",
            "care_management_integration_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        CARE_MANAGEMENT_INTEGRATION_RUN,
        {"post_closure_routing_finalisation_run": post_closure_routing_finalisation_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(CARE_MANAGEMENT_INTEGRATION_RUN):
        return None

    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_care_management_integration_run",
            "care_management_integration_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(CARE_MANAGEMENT_INTEGRATION_RUN, {"crm_deal": deal}, "name")


def _get_post_closure_finalisation_for_deal(deal):
    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_post_closure_routing_final_run",
            "ndis_recovery_outcome_post_closure_routing_finalisation_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(POST_CLOSURE_ROUTING_FINALISATION_RUN, {"crm_deal": deal}, "name")


def _is_post_closure_finalisation_completed(run):
    if not run or not frappe.db.exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        run,
        ["status", "post_closure_routing_finalisation_run_ready"],
    )

    return status == "Post Closure Routing Finalised" and bool(ready)


def _is_integration_approved(run):
    if not run or not frappe.db.exists(CARE_MANAGEMENT_INTEGRATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        CARE_MANAGEMENT_INTEGRATION_RUN,
        run,
        ["status", "care_management_integration_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _blocked_line(row):
    return any([
        row.get("care_management_record_creation_authorized"),
        row.get("care_management_record_update_authorized"),
        row.get("care_management_record_delete_authorized"),
        row.get("communication_creation_authorized"),
        row.get("email_send_authorized"),
        row.get("event_creation_authorized"),
        row.get("todo_creation_authorized"),
        row.get("task_creation_authorized"),
        row.get("recovery_case_creation_authorized"),
        row.get("journal_entry_authorized"),
        row.get("manual_gl_authorized"),
        row.get("payment_entry_authorized"),
        row.get("sales_invoice_authorized"),
        row.get("adjustment_authorized"),
        row.get("bank_reconciliation_authorized"),
        row.get("claim_batch_authorized"),
        row.get("claim_line_authorized"),
        row.get("remittance_import_authorized"),
    ])


def _append_line_if_missing(doc, row_data):
    existing = {
        row.integration_area
        for row in doc.get("care_management_integration_lines") or []
        if row.get("integration_area")
    }

    if row_data.get("integration_area") in existing:
        return False

    doc.append("care_management_integration_lines", row_data)
    return True


def _build_template_line(template, doc):
    return {
        "integration_area": template["area"],
        "integration_description": template["description"],
        "record_required": template["require_record"],

        "target_care_doctype": None,
        "target_care_record": None,
        "target_care_record_title": None,
        "target_care_record_status": None,
        "target_care_record_owner": None,
        "target_care_last_checked_on": None,

        "participant_customer": doc.get("participant_customer"),
        "participant_service_file": doc.get("participant_service_file"),
        "crm_deal": doc.get("crm_deal"),
        "participant_name": doc.get("participant_name"),
        "ndis_number": doc.get("ndis_number"),

        "integration_source_ready": 1,
        "link_confirmed": 0,
        "data_scope_confirmed": 0,
        "no_duplicate_record_confirmed": 0,
        "read_only_bridge_confirmed": 0,
        "owner_confirmed": 0,
        "operational_visibility_confirmed": 0,
        "integration_authorized": 0,

        "care_management_record_creation_authorized": 0,
        "care_management_record_update_authorized": 0,
        "care_management_record_delete_authorized": 0,
        "communication_creation_authorized": 0,
        "email_send_authorized": 0,
        "event_creation_authorized": 0,
        "todo_creation_authorized": 0,
        "task_creation_authorized": 0,
        "recovery_case_creation_authorized": 0,
        "journal_entry_authorized": 0,
        "manual_gl_authorized": 0,
        "payment_entry_authorized": 0,
        "sales_invoice_authorized": 0,
        "adjustment_authorized": 0,
        "bank_reconciliation_authorized": 0,
        "claim_batch_authorized": 0,
        "claim_line_authorized": 0,
        "remittance_import_authorized": 0,

        "integration_hold": 0,
        "integration_hold_reason": None,
        "line_ready_for_integration": 0,
        "integration_line_status": "Draft",
    }


def _generate_lines(doc):
    created = 0

    for template in INTEGRATION_AREAS:
        if _append_line_if_missing(doc, _build_template_line(template, doc)):
            created += 1

    return created


def _line_has_valid_target(row):
    if not row.get("record_required"):
        if not row.get("target_care_doctype") and not row.get("target_care_record"):
            return True

    if not row.get("target_care_doctype") or not row.get("target_care_record"):
        return False

    if not _doctype_exists(row.get("target_care_doctype")):
        return False

    return bool(frappe.db.exists(row.get("target_care_doctype"), row.get("target_care_record")))


def _active_lines(doc):
    return doc.get("care_management_integration_lines") or []


def _calculate_totals(doc):
    totals = {
        "integration_line_count": 0,
        "required_integration_line_count": 0,
        "linked_integration_line_count": 0,
        "ready_integration_line_count": 0,
        "hold_integration_line_count": 0,
        "integration_completed_count": 0,

        "care_profile_linked_count": 0,
        "care_plan_linked_count": 0,
        "medication_plan_linked_count": 0,
        "incident_management_linked_count": 0,
        "task_library_linked_count": 0,
        "staff_assignment_linked_count": 0,
        "service_delivery_linked_count": 0,
        "progress_notes_linked_count": 0,

        "blocked_care_create_count": 0,
        "blocked_care_update_count": 0,
        "blocked_care_delete_count": 0,
        "blocked_communication_count": 0,
        "blocked_email_send_count": 0,
        "blocked_event_count": 0,
        "blocked_todo_count": 0,
        "blocked_task_count": 0,
        "blocked_recovery_case_creation_count": 0,
        "blocked_journal_entry_count": 0,
        "blocked_manual_gl_count": 0,
        "blocked_payment_entry_count": 0,
        "blocked_sales_invoice_count": 0,
        "blocked_adjustment_count": 0,
        "blocked_bank_reconciliation_count": 0,
        "blocked_claim_batch_count": 0,
        "blocked_claim_line_count": 0,
        "blocked_remittance_import_count": 0,
    }

    area_counters = {
        "Care Management Profile": "care_profile_linked_count",
        "Care Plan / Daily Activity Plan": "care_plan_linked_count",
        "Medication Plan": "medication_plan_linked_count",
        "Incident Management": "incident_management_linked_count",
        "NDIS Task Library": "task_library_linked_count",
        "Staff Assignment / Responsibility": "staff_assignment_linked_count",
        "Service Delivery / Shift Execution": "service_delivery_linked_count",
        "Progress Notes / Evidence": "progress_notes_linked_count",
    }

    blocked_fields = [
        ("blocked_care_create_count", "care_management_record_creation_authorized"),
        ("blocked_care_update_count", "care_management_record_update_authorized"),
        ("blocked_care_delete_count", "care_management_record_delete_authorized"),
        ("blocked_communication_count", "communication_creation_authorized"),
        ("blocked_email_send_count", "email_send_authorized"),
        ("blocked_event_count", "event_creation_authorized"),
        ("blocked_todo_count", "todo_creation_authorized"),
        ("blocked_task_count", "task_creation_authorized"),
        ("blocked_recovery_case_creation_count", "recovery_case_creation_authorized"),
        ("blocked_journal_entry_count", "journal_entry_authorized"),
        ("blocked_manual_gl_count", "manual_gl_authorized"),
        ("blocked_payment_entry_count", "payment_entry_authorized"),
        ("blocked_sales_invoice_count", "sales_invoice_authorized"),
        ("blocked_adjustment_count", "adjustment_authorized"),
        ("blocked_bank_reconciliation_count", "bank_reconciliation_authorized"),
        ("blocked_claim_batch_count", "claim_batch_authorized"),
        ("blocked_claim_line_count", "claim_line_authorized"),
        ("blocked_remittance_import_count", "remittance_import_authorized"),
    ]

    for row in _active_lines(doc):
        totals["integration_line_count"] += 1

        if row.get("record_required"):
            totals["required_integration_line_count"] += 1

        if row.get("target_care_doctype") and row.get("target_care_record"):
            totals["linked_integration_line_count"] += 1
            counter = area_counters.get(row.get("integration_area"))
            if counter:
                totals[counter] += 1

        if row.get("line_ready_for_integration"):
            totals["ready_integration_line_count"] += 1

        if row.get("integration_hold"):
            totals["hold_integration_line_count"] += 1

        if row.get("integration_line_status") == "Integration Completed":
            totals["integration_completed_count"] += 1

        for counter, fieldname in blocked_fields:
            if row.get(fieldname):
                totals[counter] += 1

    return totals


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(CARE_MANAGEMENT_INTEGRATION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Post Closure Routing Finalisation Run linked",
        "complete": bool(doc.get("post_closure_routing_finalisation_run")),
    })

    checks.append({
        "label": "Post Closure Routing Finalisation completed",
        "complete": _is_post_closure_finalisation_completed(doc.get("post_closure_routing_finalisation_run")),
    })

    checks.append({
        "label": "Participant Customer linked",
        "complete": bool(doc.get("participant_customer")),
    })

    checks.append({
        "label": "Participant Service File linked",
        "complete": bool(doc.get("participant_service_file")),
    })

    checks.append({
        "label": "Company selected",
        "complete": bool(doc.get("company")),
    })

    checks.append({
        "label": "Care Management Integration Owner assigned",
        "complete": bool(doc.get("care_management_integration_owner")),
    })

    lines = _active_lines(doc)

    checks.append({
        "label": "Integration lines exist",
        "complete": bool(lines),
    })

    if lines:
        checks.extend([
            {
                "label": "All required care links point to existing records",
                "complete": not [
                    row.integration_area
                    for row in lines
                    if row.get("record_required") and not _line_has_valid_target(row)
                ],
            },
            {
                "label": "All optional care links are blank or valid",
                "complete": not [
                    row.integration_area
                    for row in lines
                    if not row.get("record_required") and not _line_has_valid_target(row)
                ],
            },
            {
                "label": "All source-ready flags are complete",
                "complete": not [row.integration_area for row in lines if not row.get("integration_source_ready")],
            },
            {
                "label": "Link confirmation complete",
                "complete": not [row.integration_area for row in lines if not row.get("link_confirmed")],
            },
            {
                "label": "Data scope confirmation complete",
                "complete": not [row.integration_area for row in lines if not row.get("data_scope_confirmed")],
            },
            {
                "label": "No duplicate record confirmation complete",
                "complete": not [row.integration_area for row in lines if not row.get("no_duplicate_record_confirmed")],
            },
            {
                "label": "Read-only bridge confirmation complete",
                "complete": not [row.integration_area for row in lines if not row.get("read_only_bridge_confirmed")],
            },
            {
                "label": "Owner confirmation complete",
                "complete": not [row.integration_area for row in lines if not row.get("owner_confirmed")],
            },
            {
                "label": "Operational visibility confirmation complete",
                "complete": not [row.integration_area for row in lines if not row.get("operational_visibility_confirmed")],
            },
            {
                "label": "Integration authorization complete",
                "complete": not [row.integration_area for row in lines if not row.get("integration_authorized")],
            },
        ])

        blocked_fields = [
            ("Care Management record creation remains blocked in Phase 56", "care_management_record_creation_authorized"),
            ("Care Management record update remains blocked in Phase 56", "care_management_record_update_authorized"),
            ("Care Management record delete remains blocked in Phase 56", "care_management_record_delete_authorized"),
            ("Communication creation remains blocked in Phase 56", "communication_creation_authorized"),
            ("Email sending remains blocked in Phase 56", "email_send_authorized"),
            ("Event creation remains blocked in Phase 56", "event_creation_authorized"),
            ("ToDo creation remains blocked in Phase 56", "todo_creation_authorized"),
            ("Task creation remains blocked in Phase 56", "task_creation_authorized"),
            ("Recovery Case creation remains blocked in Phase 56", "recovery_case_creation_authorized"),
            ("Journal Entry authorization remains blocked in Phase 56", "journal_entry_authorized"),
            ("Manual GL authorization remains blocked in Phase 56", "manual_gl_authorized"),
            ("Payment Entry authorization remains blocked in Phase 56", "payment_entry_authorized"),
            ("Sales Invoice authorization remains blocked in Phase 56", "sales_invoice_authorized"),
            ("Adjustment authorization remains blocked in Phase 56", "adjustment_authorized"),
            ("Bank reconciliation authorization remains blocked in Phase 56", "bank_reconciliation_authorized"),
            ("Claim Batch authorization remains blocked in Phase 56", "claim_batch_authorized"),
            ("Claim Line authorization remains blocked in Phase 56", "claim_line_authorized"),
            ("Remittance Import authorization remains blocked in Phase 56", "remittance_import_authorized"),
        ]

        for label, fieldname in blocked_fields:
            checks.append({
                "label": label,
                "complete": not [row.integration_area for row in lines if row.get(fieldname)],
            })

        checks.append({
            "label": "No active integration hold remains",
            "complete": not [row.integration_area for row in lines if row.get("integration_hold")],
        })

        checks.append({
            "label": "All lines marked ready for integration",
            "complete": not [row.integration_area for row in lines if not row.get("line_ready_for_integration")],
        })

    total = len(checks)
    complete = len([row for row in checks if row["complete"]])
    readiness_percent = round((complete / total) * 100, 2) if total else 0
    incomplete = [row["label"] for row in checks if not row["complete"]]

    return {
        "total_checks": total,
        "complete_checks": complete,
        "readiness_percent": readiness_percent,
        "care_management_integration_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(CARE_MANAGEMENT_INTEGRATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(CARE_MANAGEMENT_INTEGRATION_RUN, "care_management_integration_run_ready"):
        doc.care_management_integration_run_ready = 1 if summary["care_management_integration_run_ready"] else 0

    targets = [
        (CRM_DEAL, doc.get("crm_deal")),
        (PARTICIPANT_SERVICE_FILE, doc.get("participant_service_file")),
        (POST_CLOSURE_ROUTING_FINALISATION_RUN, doc.get("post_closure_routing_finalisation_run")),
        (POST_CLOSURE_ROUTING_PREPARATION_RUN, doc.get("post_closure_routing_preparation_run")),
        (RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN, doc.get("recovery_outcome_closure_finalisation_run")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_care_management_integration_run", doc.name)
        _db_set_if_field(doctype, name, "care_management_integration_status", doc.status)
        _db_set_if_field(doctype, name, "care_management_integration_ready", 1 if summary["care_management_integration_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


def _copy_source_values(doc, source):
    doc.post_closure_routing_finalisation_run = source.name
    doc.post_closure_routing_preparation_run = source.get("post_closure_routing_preparation_run")
    doc.recovery_outcome_closure_finalisation_run = source.get("recovery_outcome_closure_finalisation_run")
    doc.recovery_outcome_closure_draft_run = source.get("recovery_outcome_closure_draft_run")
    doc.recovery_outcome_closure_preparation_run = source.get("recovery_outcome_closure_preparation_run")
    doc.recovery_outcome_action_completion_run = source.get("recovery_outcome_action_completion_run")

    doc.crm_deal = source.get("crm_deal")
    doc.crm_lead = source.get("crm_lead")
    doc.participant_intake = source.get("participant_intake")
    doc.participant_customer = source.get("participant_customer")
    doc.participant_service_file = source.get("participant_service_file")
    doc.ndis_financial_profile = source.get("ndis_financial_profile")
    doc.participant_name = source.get("participant_name") or source.get("participant_customer") or source.name
    doc.ndis_number = source.get("ndis_number")
    doc.plan_start_date = source.get("plan_start_date")
    doc.plan_end_date = source.get("plan_end_date")
    doc.company = source.get("company")
    doc.claim_period_start = source.get("claim_period_start")
    doc.claim_period_end = source.get("claim_period_end")


@frappe.whitelist()
def create_care_management_integration_run_from_post_closure_finalisation(post_closure_routing_finalisation_run):
    _check_role()

    if not post_closure_routing_finalisation_run:
        frappe.throw(_("NDIS CRM Post Closure Routing Finalisation Run is required."))

    if not frappe.db.exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, post_closure_routing_finalisation_run):
        frappe.throw(_("NDIS CRM Post Closure Routing Finalisation Run {0} was not found.").format(post_closure_routing_finalisation_run))

    existing = _existing_run_for_post_closure_finalisation(post_closure_routing_finalisation_run)
    if existing:
        return {
            "doctype": CARE_MANAGEMENT_INTEGRATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Care Management Integration Run returned.",
        }

    source = frappe.get_doc(POST_CLOSURE_ROUTING_FINALISATION_RUN, post_closure_routing_finalisation_run)

    doc = frappe.new_doc(CARE_MANAGEMENT_INTEGRATION_RUN)
    doc.status = "Draft"
    doc.integration_mode = "Reference Existing Care Management Records Only"
    doc.care_management_integration_owner = frappe.session.user
    doc.post_closure_routing_finalisation_owner = source.get("post_closure_routing_finalisation_owner")

    doc.care_management_record_creation_allowed = 0
    doc.care_management_record_update_allowed = 0
    doc.care_management_record_delete_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.claim_batch_creation_allowed = 0
    doc.claim_line_creation_allowed = 0
    doc.remittance_import_creation_allowed = 0

    _copy_source_values(doc, source)

    created_count = _generate_lines(doc)
    doc.integration_line_count = created_count

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.care_management_integration_run_ready = 1 if summary["care_management_integration_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)

    frappe.db.commit()

    return {
        "doctype": CARE_MANAGEMENT_INTEGRATION_RUN,
        "name": doc.name,
        "created": True,
        "integration_line_count": created_count,
        "message": "NDIS CRM Care Management Integration Run created successfully.",
    }


@frappe.whitelist()
def create_care_management_integration_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": CARE_MANAGEMENT_INTEGRATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Care Management Integration Run returned.",
        }

    source_run = _get_post_closure_finalisation_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Post Closure Routing Finalisation Run before creating Care Management Integration Run."))

    return create_care_management_integration_run_from_post_closure_finalisation(source_run)


@frappe.whitelist()
def generate_care_management_integration_lines(care_management_integration_run):
    _check_role()

    doc = frappe.get_doc(CARE_MANAGEMENT_INTEGRATION_RUN, care_management_integration_run)
    created_count = _generate_lines(doc)

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Care Management Integration lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_care_management_integration_readiness(care_management_integration_run):
    _check_role()

    doc = frappe.get_doc(CARE_MANAGEMENT_INTEGRATION_RUN, care_management_integration_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Care Management Integration readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_care_management_integration(care_management_integration_run):
    _check_role()

    doc = frappe.get_doc(CARE_MANAGEMENT_INTEGRATION_RUN, care_management_integration_run)
    summary = _calculate_readiness(doc)

    if not summary["care_management_integration_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Integration. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Integration"
    doc.readiness_percent = summary["readiness_percent"]
    doc.care_management_integration_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": CARE_MANAGEMENT_INTEGRATION_RUN,
        "name": doc.name,
        "message": "Care Management Integration Run marked Ready.",
    }


@frappe.whitelist()
def approve_care_management_integration_run(care_management_integration_run):
    _check_role()

    doc = frappe.get_doc(CARE_MANAGEMENT_INTEGRATION_RUN, care_management_integration_run)
    summary = _calculate_readiness(doc)

    if not summary["care_management_integration_run_ready"]:
        frappe.throw(
            _("Cannot approve Care Management Integration Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Integration Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.care_management_integration_run_ready = 1

    doc.integration_completion_allowed = 0
    doc.care_management_record_creation_allowed = 0
    doc.care_management_record_update_allowed = 0
    doc.care_management_record_delete_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.claim_batch_creation_allowed = 0
    doc.claim_line_creation_allowed = 0
    doc.remittance_import_creation_allowed = 0

    for row in doc.get("care_management_integration_lines") or []:
        if row.get("integration_line_status") in ["Draft", "Ready"]:
            row.integration_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": CARE_MANAGEMENT_INTEGRATION_RUN,
        "name": doc.name,
        "message": "Care Management Integration Run approved. No Care Management or downstream record was created or updated.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("integration_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_integration"):
            continue

        if not row.get("integration_source_ready"):
            continue

        if row.get("integration_hold"):
            continue

        if _blocked_line(row):
            continue

        if not _line_has_valid_target(row):
            continue

        required_checks = [
            "link_confirmed",
            "data_scope_confirmed",
            "no_duplicate_record_confirmed",
            "read_only_bridge_confirmed",
            "owner_confirmed",
            "operational_visibility_confirmed",
            "integration_authorized",
        ]

        if any(not row.get(fieldname) for fieldname in required_checks):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_care_management_integration(care_management_integration_run):
    _check_role()

    doc = frappe.get_doc(CARE_MANAGEMENT_INTEGRATION_RUN, care_management_integration_run)

    if doc.status != "Integration Approved":
        frappe.throw(_("Care Management Integration Run must be approved before completion."))

    if not doc.get("integration_completion_allowed"):
        frappe.throw(_("Tick Integration Completion Allowed before completing the integration bridge."))

    if (doc.get("integration_mode") or "Reference Existing Care Management Records Only") != "Reference Existing Care Management Records Only":
        frappe.throw(_("Phase 56 supports reference-only integration. It cannot create or update Care Management records."))

    blocked_run_fields = [
        ("Care Management Record Creation Allowed", "care_management_record_creation_allowed"),
        ("Care Management Record Update Allowed", "care_management_record_update_allowed"),
        ("Care Management Record Delete Allowed", "care_management_record_delete_allowed"),
        ("Communication Creation Allowed", "communication_creation_allowed"),
        ("Email Send Allowed", "email_send_allowed"),
        ("Event Creation Allowed", "event_creation_allowed"),
        ("ToDo Creation Allowed", "todo_creation_allowed"),
        ("Task Creation Allowed", "task_creation_allowed"),
        ("Recovery Case Creation Allowed", "recovery_case_creation_allowed"),
        ("Journal Entry Creation Allowed", "journal_entry_creation_allowed"),
        ("Manual GL Creation Allowed", "manual_gl_creation_allowed"),
        ("Payment Entry Creation Allowed", "payment_entry_creation_allowed"),
        ("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed"),
        ("Adjustment Creation Allowed", "adjustment_creation_allowed"),
        ("Bank Reconciliation Allowed", "bank_reconciliation_allowed"),
        ("Claim Batch Creation Allowed", "claim_batch_creation_allowed"),
        ("Claim Line Creation Allowed", "claim_line_creation_allowed"),
        ("Remittance Import Creation Allowed", "remittance_import_creation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} must remain unticked in Phase 56.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["care_management_integration_run_ready"]:
        frappe.throw(
            _("Cannot complete Care Management Integration. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines:
        frappe.throw(_("No ready Care Management Integration lines found."))

    for row in ready_lines:
        row.integration_line_status = "Integration Completed"
        row.target_care_last_checked_on = now()

    doc.status = "Integration Completed"
    doc.integration_completion_allowed = 0
    doc.care_management_record_creation_allowed = 0
    doc.care_management_record_update_allowed = 0
    doc.care_management_record_delete_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.claim_batch_creation_allowed = 0
    doc.claim_line_creation_allowed = 0
    doc.remittance_import_creation_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "completed_line_count": len(ready_lines),
        "message": "Care Management Integration completed as reference-only bridge. No Care Management, Communication, Email Queue, Event, ToDo, Task, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or Remittance Import was created or updated.",
    }


def validate_care_management_integration_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(CARE_MANAGEMENT_INTEGRATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(CARE_MANAGEMENT_INTEGRATION_RUN, "care_management_integration_run_ready"):
        doc.care_management_integration_run_ready = 1 if summary["care_management_integration_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["care_management_integration_run_ready"]:
        frappe.throw(
            _("Cannot set Care Management Integration Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Integration Approved" and doc.get("integration_completion_allowed"):
        frappe.throw(_("Integration Completion Allowed can only be ticked after the run is approved."))

    blocked_run_fields = [
        ("Care Management record creation", "care_management_record_creation_allowed"),
        ("Care Management record update", "care_management_record_update_allowed"),
        ("Care Management record delete", "care_management_record_delete_allowed"),
        ("Communication creation", "communication_creation_allowed"),
        ("Email send", "email_send_allowed"),
        ("Event creation", "event_creation_allowed"),
        ("ToDo creation", "todo_creation_allowed"),
        ("Task creation", "task_creation_allowed"),
        ("Recovery Case creation", "recovery_case_creation_allowed"),
        ("Journal Entry creation", "journal_entry_creation_allowed"),
        ("Manual GL creation", "manual_gl_creation_allowed"),
        ("Payment Entry creation", "payment_entry_creation_allowed"),
        ("Sales Invoice creation", "sales_invoice_creation_allowed"),
        ("Adjustment creation", "adjustment_creation_allowed"),
        ("Bank reconciliation", "bank_reconciliation_allowed"),
        ("Claim Batch creation", "claim_batch_creation_allowed"),
        ("Claim Line creation", "claim_line_creation_allowed"),
        ("Remittance Import creation", "remittance_import_creation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} is not allowed in Phase 56.").format(label))


def on_care_management_integration_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Care Management Integration Run Summary Sync Failed"
        )


def validate_crm_deal_phase56(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_care_management_integration_required"):
        required = doc.get("ndis_care_management_integration_required")

    if not required:
        return

    run = doc.get("ndis_care_management_integration_run") if _field_exists(CRM_DEAL, "ndis_care_management_integration_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Care Management Integration Run must be created and approved/completed.")
        )

    if not _is_integration_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Care Management Integration Run must be approved/completed.")
        )


def validate_crm_deal_phase56_combined(doc, method=None):
    try:
        from ndis_crm.phase55_post_closure_routing_finalisation import validate_crm_deal_phase55_combined
        validate_crm_deal_phase55_combined(doc, method)
    except ImportError:
        pass

    validate_crm_deal_phase56(doc, method)


def phase56_health_check():
    print("---- NDIS CRM Phase 56 Health Check ----")

    for dt in [
        CARE_MANAGEMENT_INTEGRATION_LINE,
        CARE_MANAGEMENT_INTEGRATION_RUN,
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        POST_CLOSURE_ROUTING_PREPARATION_RUN,
        RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN,
        PARTICIPANT_SERVICE_FILE,
        CRM_DEAL,
        SALES_INVOICE,
        PAYMENT_ENTRY,
        JOURNAL_ENTRY,
        GL_ENTRY,
        NDIS_REMITTANCE_IMPORT,
        NDIS_CLAIM_BATCH,
        NDIS_CLAIM_LINE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for dt in [COMMUNICATION, EMAIL_QUEUE, EVENT, TODO, TASK, NDIS_RECOVERY_CASE]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_care_management_integration_required",
        "ndis_care_management_integration_run",
        "care_management_integration_status",
        "care_management_integration_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print(
        "NDIS CRM Care Management Integration Run records:",
        frappe.db.count(CARE_MANAGEMENT_INTEGRATION_RUN) if _doctype_exists(CARE_MANAGEMENT_INTEGRATION_RUN) else 0
    )
    print("Phase 56 creates CRM care management integration run/line records only.")
    print("Phase 56 is reference-only and does not create or update Care Management records.")
    print("Phase 56 does not create Communication, Email Queue, Event, ToDo, Task, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 56 Health Check ----")
