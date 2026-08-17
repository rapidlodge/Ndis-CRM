import frappe
from frappe import _
from frappe.utils import now


CRM_DEAL = "CRM Deal"
PARTICIPANT_SERVICE_FILE = "NDIS Participant Service File"
CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"
POST_CLOSURE_ROUTING_FINALISATION_RUN = "NDIS CRM Post Closure Routing Finalisation Run"

OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"
OPERATIONAL_DASHBOARD_SNAPSHOT_LINE = "NDIS CRM Operational Dashboard Snapshot Line"

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
    "Ready for Dashboard Completion",
    "Dashboard Snapshot Approved",
    "Dashboard Snapshot Completed",
]

APPROVED_STATUSES = [
    "Dashboard Snapshot Approved",
    "Dashboard Snapshot Completed",
]

ALLOWED_ROLES = {
    "Administrator",
    "System Manager",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
    "Accounts Manager",
    "Accounts User",
}


STAGE_DEFINITIONS = [
    {
        "area": "CRM",
        "stage": "CRM Deal",
        "doctype": CRM_DEAL,
        "link_fields": [],
        "status_fields": ["status"],
        "ready_fields": [],
    },
    {
        "area": "CRM",
        "stage": "Participant Intake",
        "doctype": "NDIS Participant Intake",
        "link_fields": ["participant_intake", "ndis_participant_intake"],
        "status_fields": ["participant_intake_status", "intake_status"],
        "ready_fields": ["participant_intake_ready", "intake_ready"],
    },
    {
        "area": "CRM",
        "stage": "Document Request / Handover",
        "doctype": "NDIS CRM Handover",
        "link_fields": ["handover", "ndis_crm_handover"],
        "status_fields": ["handover_status", "ndis_handover_status"],
        "ready_fields": ["handover_ready", "ndis_handover_ready"],
    },
    {
        "area": "Finance",
        "stage": "Finance Onboarding",
        "doctype": "NDIS CRM Finance Onboarding",
        "link_fields": ["finance_onboarding", "ndis_crm_finance_onboarding"],
        "status_fields": ["finance_onboarding_status"],
        "ready_fields": ["finance_onboarding_ready"],
    },
    {
        "area": "Operations",
        "stage": "Operations Setup",
        "doctype": "NDIS CRM Operations Setup",
        "link_fields": ["operations_setup", "ndis_crm_operations_setup"],
        "status_fields": ["operations_setup_status"],
        "ready_fields": ["operations_setup_ready"],
    },
    {
        "area": "Operations",
        "stage": "Service Schedule Draft",
        "doctype": "NDIS CRM Service Schedule Draft",
        "link_fields": ["service_schedule_draft", "ndis_service_schedule_draft"],
        "status_fields": ["service_schedule_draft_status"],
        "ready_fields": ["service_schedule_draft_ready"],
    },
    {
        "area": "Operations",
        "stage": "Roster Build Request",
        "doctype": "NDIS CRM Roster Build Request",
        "link_fields": ["roster_build_request", "ndis_roster_build_request"],
        "status_fields": ["roster_build_request_status"],
        "ready_fields": ["roster_build_request_ready"],
    },
    {
        "area": "Operations",
        "stage": "Participant Service File",
        "doctype": PARTICIPANT_SERVICE_FILE,
        "link_fields": ["participant_service_file", "ndis_participant_service_file"],
        "status_fields": ["participant_service_file_status", "service_file_status"],
        "ready_fields": ["participant_service_file_ready", "service_file_ready"],
    },
    {
        "area": "Care Management",
        "stage": "Care Management Integration",
        "doctype": CARE_MANAGEMENT_INTEGRATION_RUN,
        "link_fields": ["ndis_care_management_integration_run", "care_management_integration_run"],
        "status_fields": ["care_management_integration_status"],
        "ready_fields": ["care_management_integration_ready"],
    },
    {
        "area": "Service Delivery",
        "stage": "Service Session Draft",
        "doctype": "NDIS CRM Service Session Draft",
        "link_fields": ["service_session_draft", "ndis_service_session_draft"],
        "status_fields": ["service_session_draft_status"],
        "ready_fields": ["service_session_draft_ready"],
    },
    {
        "area": "Service Delivery",
        "stage": "Evidence Review",
        "doctype": "NDIS CRM Service Delivery Evidence Review",
        "link_fields": ["delivery_evidence_review", "service_delivery_evidence_review"],
        "status_fields": ["delivery_evidence_review_status", "service_delivery_evidence_review_status"],
        "ready_fields": ["delivery_evidence_review_ready", "service_delivery_evidence_review_ready"],
    },
    {
        "area": "Service Delivery",
        "stage": "Downstream Preparation",
        "doctype": "NDIS CRM Downstream Preparation",
        "link_fields": ["downstream_preparation"],
        "status_fields": ["downstream_preparation_status"],
        "ready_fields": ["downstream_preparation_ready"],
    },
    {
        "area": "Service Delivery",
        "stage": "Attendance Draft",
        "doctype": "NDIS CRM Attendance Draft",
        "link_fields": ["attendance_draft"],
        "status_fields": ["attendance_draft_status"],
        "ready_fields": ["attendance_draft_ready"],
    },
    {
        "area": "Billing",
        "stage": "Billing Draft",
        "doctype": "NDIS CRM Billing Draft",
        "link_fields": ["billing_draft"],
        "status_fields": ["billing_draft_status"],
        "ready_fields": ["billing_draft_ready"],
    },
    {
        "area": "Claims",
        "stage": "Claim Draft",
        "doctype": "NDIS CRM Claim Draft",
        "link_fields": ["claim_draft"],
        "status_fields": ["claim_draft_status"],
        "ready_fields": ["claim_draft_ready"],
    },
    {
        "area": "Invoices",
        "stage": "Invoice Draft",
        "doctype": "NDIS CRM Invoice Draft",
        "link_fields": ["invoice_draft"],
        "status_fields": ["invoice_draft_status"],
        "ready_fields": ["invoice_draft_ready"],
    },
    {
        "area": "Invoices",
        "stage": "Sales Invoice Draft Run",
        "doctype": "NDIS CRM Sales Invoice Draft Run",
        "link_fields": ["sales_invoice_draft_run"],
        "status_fields": ["sales_invoice_draft_run_status", "sales_invoice_draft_status"],
        "ready_fields": ["sales_invoice_draft_run_ready", "sales_invoice_draft_ready"],
    },
    {
        "area": "Invoices",
        "stage": "Sales Invoice Submission Run",
        "doctype": "NDIS CRM Sales Invoice Submission Run",
        "link_fields": ["sales_invoice_submission_run"],
        "status_fields": ["sales_invoice_submission_status"],
        "ready_fields": ["sales_invoice_submission_ready"],
    },
    {
        "area": "Claims",
        "stage": "Claim Batch Draft Run",
        "doctype": "NDIS CRM Claim Batch Draft Run",
        "link_fields": ["claim_batch_draft_run"],
        "status_fields": ["claim_batch_draft_status"],
        "ready_fields": ["claim_batch_draft_ready"],
    },
    {
        "area": "Claims",
        "stage": "Claim Batch Submission Run",
        "doctype": "NDIS CRM Claim Batch Submission Run",
        "link_fields": ["claim_batch_submission_run"],
        "status_fields": ["claim_batch_submission_status"],
        "ready_fields": ["claim_batch_submission_ready"],
    },
    {
        "area": "Claims",
        "stage": "Claim Export Preparation",
        "doctype": "NDIS CRM Claim Export Preparation Run",
        "link_fields": ["claim_export_preparation_run"],
        "status_fields": ["claim_export_preparation_status"],
        "ready_fields": ["claim_export_preparation_ready"],
    },
    {
        "area": "Claims",
        "stage": "Claim Lodgement Confirmation",
        "doctype": "NDIS CRM Claim Lodgement Confirmation Run",
        "link_fields": ["claim_lodgement_confirmation_run"],
        "status_fields": ["claim_lodgement_confirmation_status"],
        "ready_fields": ["claim_lodgement_confirmation_ready"],
    },
    {
        "area": "Remittance",
        "stage": "Remittance Import Preparation",
        "doctype": "NDIS CRM Remittance Import Preparation Run",
        "link_fields": ["remittance_import_preparation_run"],
        "status_fields": ["remittance_import_preparation_status"],
        "ready_fields": ["remittance_import_preparation_ready"],
    },
    {
        "area": "Remittance",
        "stage": "Actual Remittance Import",
        "doctype": "NDIS CRM Actual Remittance Import Run",
        "link_fields": ["actual_remittance_import_run"],
        "status_fields": ["actual_remittance_import_status"],
        "ready_fields": ["actual_remittance_import_ready"],
    },
    {
        "area": "Remittance",
        "stage": "Remittance Matching Review",
        "doctype": "NDIS CRM Remittance Matching Review Run",
        "link_fields": ["remittance_matching_review_run"],
        "status_fields": ["remittance_matching_review_status"],
        "ready_fields": ["remittance_matching_review_ready"],
    },
    {
        "area": "Payments",
        "stage": "Payment Allocation Preparation",
        "doctype": "NDIS CRM Payment Allocation Preparation Run",
        "link_fields": ["payment_allocation_preparation_run"],
        "status_fields": ["payment_allocation_preparation_status"],
        "ready_fields": ["payment_allocation_preparation_ready"],
    },
    {
        "area": "Payments",
        "stage": "Payment Entry Draft Run",
        "doctype": "NDIS CRM Payment Entry Draft Run",
        "link_fields": ["payment_entry_draft_run"],
        "status_fields": ["payment_entry_draft_status"],
        "ready_fields": ["payment_entry_draft_ready"],
    },
    {
        "area": "Payments",
        "stage": "Payment Entry Submission Run",
        "doctype": "NDIS CRM Payment Entry Submission Run",
        "link_fields": ["payment_entry_submission_run"],
        "status_fields": ["payment_entry_submission_status"],
        "ready_fields": ["payment_entry_submission_ready"],
    },
    {
        "area": "Remittance",
        "stage": "Remittance Import Finalisation",
        "doctype": "NDIS CRM Remittance Import Finalisation Run",
        "link_fields": ["remittance_import_finalisation_run"],
        "status_fields": ["remittance_import_finalisation_status"],
        "ready_fields": ["remittance_import_finalisation_ready"],
    },
    {
        "area": "Variance",
        "stage": "Variance Rejection Review",
        "doctype": "NDIS CRM Variance Rejection Review Run",
        "link_fields": ["variance_rejection_review_run"],
        "status_fields": ["variance_rejection_review_status"],
        "ready_fields": ["variance_rejection_review_ready"],
    },
    {
        "area": "Write Off",
        "stage": "Write Off Preparation",
        "doctype": "NDIS CRM Write Off Preparation Run",
        "link_fields": ["write_off_preparation_run"],
        "status_fields": ["write_off_preparation_status"],
        "ready_fields": ["write_off_preparation_ready"],
    },
    {
        "area": "Write Off",
        "stage": "Write Off Finalisation",
        "doctype": "NDIS CRM Write Off Finalisation Run",
        "link_fields": ["write_off_finalisation_run"],
        "status_fields": ["write_off_finalisation_status"],
        "ready_fields": ["write_off_finalisation_ready"],
    },
    {
        "area": "Recovery",
        "stage": "Recovery Preparation",
        "doctype": "NDIS CRM Recovery Preparation Run",
        "link_fields": ["recovery_preparation_run"],
        "status_fields": ["recovery_preparation_status"],
        "ready_fields": ["recovery_preparation_ready"],
    },
    {
        "area": "Recovery",
        "stage": "Recovery Case Submission",
        "doctype": "NDIS CRM Recovery Case Submission Run",
        "link_fields": ["recovery_case_submission_run"],
        "status_fields": ["recovery_case_submission_status"],
        "ready_fields": ["recovery_case_submission_ready"],
    },
    {
        "area": "Recovery",
        "stage": "Recovery Follow Up",
        "doctype": "NDIS CRM Recovery Follow Up Preparation Run",
        "link_fields": ["recovery_follow_up_preparation_run"],
        "status_fields": ["recovery_follow_up_preparation_status"],
        "ready_fields": ["recovery_follow_up_preparation_ready"],
    },
    {
        "area": "Recovery",
        "stage": "Recovery Communication",
        "doctype": "NDIS CRM Recovery Communication Dispatch Run",
        "link_fields": ["recovery_communication_dispatch_run"],
        "status_fields": ["recovery_communication_dispatch_status"],
        "ready_fields": ["recovery_communication_dispatch_ready"],
    },
    {
        "area": "Recovery",
        "stage": "Recovery Communication Outcome",
        "doctype": "NDIS CRM Recovery Communication Outcome Capture Run",
        "link_fields": ["recovery_communication_outcome_capture_run"],
        "status_fields": ["recovery_communication_outcome_capture_status"],
        "ready_fields": ["recovery_communication_outcome_capture_ready"],
    },
    {
        "area": "Recovery",
        "stage": "Recovery Outcome Action Completion",
        "doctype": "NDIS CRM Recovery Outcome Action Completion Run",
        "link_fields": ["recovery_outcome_action_completion_run"],
        "status_fields": ["recovery_outcome_action_completion_status"],
        "ready_fields": ["recovery_outcome_action_completion_ready"],
    },
    {
        "area": "Recovery Closure",
        "stage": "Recovery Outcome Closure Finalisation",
        "doctype": "NDIS CRM Recovery Outcome Closure Finalisation Run",
        "link_fields": ["recovery_outcome_closure_finalisation_run"],
        "status_fields": ["recovery_outcome_closure_finalisation_status"],
        "ready_fields": ["recovery_outcome_closure_finalisation_ready"],
    },
    {
        "area": "Post Closure",
        "stage": "Post Closure Routing Preparation",
        "doctype": "NDIS CRM Post Closure Routing Preparation Run",
        "link_fields": ["ndis_post_closure_routing_prep_run", "ndis_recovery_outcome_post_closure_routing_preparation_run"],
        "status_fields": ["post_closure_routing_preparation_status"],
        "ready_fields": ["post_closure_routing_preparation_ready"],
    },
    {
        "area": "Post Closure",
        "stage": "Post Closure Routing Finalisation",
        "doctype": POST_CLOSURE_ROUTING_FINALISATION_RUN,
        "link_fields": ["ndis_post_closure_routing_final_run", "ndis_recovery_outcome_post_closure_routing_finalisation_run"],
        "status_fields": ["post_closure_routing_finalisation_status"],
        "ready_fields": ["post_closure_routing_finalisation_ready"],
    },
]


def _check_role():
    if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this operational dashboard snapshot action."))


def _doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
    return bool(
        frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
        or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
    )


def _get_value_if_field(doctype, name, fieldname):
    if not name or not _field_exists(doctype, fieldname):
        return None

    try:
        return frappe.db.get_value(doctype, name, fieldname)
    except Exception:
        return None


def _get_first_existing_value(doctype, name, fields):
    if not name:
        return None

    for fieldname in fields:
        value = _get_value_if_field(doctype, name, fieldname)
        if value not in [None, ""]:
            return value

    return None


def _db_set_if_field(doctype, name, fieldname, value):
    if name and _field_exists(doctype, fieldname):
        frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)


def _existing_run_for_deal(deal):
    if not _doctype_exists(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN):
        return None

    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_operational_dashboard_snapshot_run",
            "operational_dashboard_snapshot_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        {"crm_deal": deal},
        "name",
        order_by="creation desc",
    )


def _is_snapshot_approved(run):
    if not run or not frappe.db.exists(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        run,
        ["status", "operational_dashboard_snapshot_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _stage_category(status, ready, source_record):
    text = (status or "").strip().lower()

    if ready or text in [
        "approved",
        "completed",
        "complete",
        "active",
        "enabled",
        "integration completed",
        "post closure routing finalised",
        "dashboard snapshot completed",
    ]:
        return "Ready / Complete"

    if not source_record and not status:
        return "Not Started"

    if any(token in text for token in ["hold", "returned", "cancelled", "blocked", "failed", "error"]):
        return "Needs Attention"

    if source_record or status:
        return "In Progress"

    return "Not Started"


def _stage_action_required(category, status, source_record):
    if category == "Ready / Complete":
        return "No immediate action required."
    if category == "Needs Attention":
        return "Review blocker, returned status, hold, or failed state."
    if category == "In Progress":
        return "Continue current workflow and complete readiness checks."
    if not source_record:
        return "Create or link the relevant upstream record when applicable."
    return "Review stage status."


def _resolve_stage_from_deal(deal, definition):
    if definition["doctype"] == CRM_DEAL:
        source_record = deal
        status = _get_first_existing_value(CRM_DEAL, deal, definition.get("status_fields") or []) or "Linked"
        ready = 1 if status else 0
    else:
        source_record = _get_first_existing_value(CRM_DEAL, deal, definition.get("link_fields") or [])
        status = _get_first_existing_value(CRM_DEAL, deal, definition.get("status_fields") or [])
        ready = _get_first_existing_value(CRM_DEAL, deal, definition.get("ready_fields") or [])

    source_doctype = definition["doctype"]

    if source_record and _doctype_exists(source_doctype):
        if not status:
            status = _get_value_if_field(source_doctype, source_record, "status")
        if ready in [None, ""]:
            for fieldname in definition.get("ready_fields") or []:
                ready = _get_value_if_field(source_doctype, source_record, fieldname)
                if ready not in [None, ""]:
                    break

    ready = 1 if ready else 0
    category = _stage_category(status, ready, source_record)

    return {
        "module_area": definition["area"],
        "module_stage": definition["stage"],
        "source_doctype": source_doctype,
        "source_record": source_record,
        "source_status": status or "Not Linked",
        "source_ready": ready,
        "stage_category": category,
        "action_required": _stage_action_required(category, status, source_record),
    }


def _clear_lines(doc):
    doc.set("operational_dashboard_snapshot_lines", [])


def _append_snapshot_line(doc, data):
    doc.append("operational_dashboard_snapshot_lines", {
        "module_area": data.get("module_area"),
        "module_stage": data.get("module_stage"),
        "source_doctype": data.get("source_doctype"),
        "source_record": data.get("source_record"),
        "source_status": data.get("source_status"),
        "source_ready": data.get("source_ready"),
        "stage_category": data.get("stage_category"),
        "action_required": data.get("action_required"),
        "snapshot_review_complete": 0,
        "snapshot_data_verified": 0,
        "line_ready_for_dashboard": 0,
        "dashboard_line_status": "Draft",
    })


def _generate_lines(doc):
    if not doc.get("crm_deal"):
        frappe.throw(_("CRM Deal is required to generate operational dashboard snapshot lines."))

    _clear_lines(doc)

    for definition in STAGE_DEFINITIONS:
        _append_snapshot_line(doc, _resolve_stage_from_deal(doc.crm_deal, definition))

    return len(doc.get("operational_dashboard_snapshot_lines") or [])


def _active_lines(doc):
    return doc.get("operational_dashboard_snapshot_lines") or []


def _calculate_totals(doc):
    totals = {
        "snapshot_line_count": 0,
        "ready_stage_count": 0,
        "in_progress_stage_count": 0,
        "attention_stage_count": 0,
        "not_started_stage_count": 0,
        "linked_stage_count": 0,
        "dashboard_completed_line_count": 0,

        "crm_stage_count": 0,
        "finance_stage_count": 0,
        "operations_stage_count": 0,
        "care_management_stage_count": 0,
        "service_delivery_stage_count": 0,
        "billing_stage_count": 0,
        "claim_stage_count": 0,
        "invoice_stage_count": 0,
        "remittance_stage_count": 0,
        "payment_stage_count": 0,
        "variance_stage_count": 0,
        "write_off_stage_count": 0,
        "recovery_stage_count": 0,
        "post_closure_stage_count": 0,

        "blocked_record_creation_count": 0,
        "blocked_record_update_count": 0,
        "blocked_communication_count": 0,
        "blocked_email_send_count": 0,
        "blocked_event_count": 0,
        "blocked_todo_count": 0,
        "blocked_task_count": 0,
        "blocked_finance_creation_count": 0,
        "blocked_claim_creation_count": 0,
        "blocked_remittance_creation_count": 0,
        "blocked_accounting_creation_count": 0,
    }

    area_counter = {
        "CRM": "crm_stage_count",
        "Finance": "finance_stage_count",
        "Operations": "operations_stage_count",
        "Care Management": "care_management_stage_count",
        "Service Delivery": "service_delivery_stage_count",
        "Billing": "billing_stage_count",
        "Claims": "claim_stage_count",
        "Invoices": "invoice_stage_count",
        "Remittance": "remittance_stage_count",
        "Payments": "payment_stage_count",
        "Variance": "variance_stage_count",
        "Write Off": "write_off_stage_count",
        "Recovery": "recovery_stage_count",
        "Recovery Closure": "recovery_stage_count",
        "Post Closure": "post_closure_stage_count",
    }

    for row in _active_lines(doc):
        totals["snapshot_line_count"] += 1

        if row.get("source_record"):
            totals["linked_stage_count"] += 1

        category = row.get("stage_category")

        if category == "Ready / Complete":
            totals["ready_stage_count"] += 1
        elif category == "In Progress":
            totals["in_progress_stage_count"] += 1
        elif category == "Needs Attention":
            totals["attention_stage_count"] += 1
        else:
            totals["not_started_stage_count"] += 1

        if row.get("dashboard_line_status") == "Dashboard Line Completed":
            totals["dashboard_completed_line_count"] += 1

        counter = area_counter.get(row.get("module_area"))
        if counter:
            totals[counter] += 1

    blocked_run_fields = [
        ("blocked_record_creation_count", "record_creation_allowed"),
        ("blocked_record_update_count", "record_update_allowed"),
        ("blocked_communication_count", "communication_creation_allowed"),
        ("blocked_email_send_count", "email_send_allowed"),
        ("blocked_event_count", "event_creation_allowed"),
        ("blocked_todo_count", "todo_creation_allowed"),
        ("blocked_task_count", "task_creation_allowed"),
        ("blocked_finance_creation_count", "finance_document_creation_allowed"),
        ("blocked_claim_creation_count", "claim_document_creation_allowed"),
        ("blocked_remittance_creation_count", "remittance_document_creation_allowed"),
        ("blocked_accounting_creation_count", "accounting_document_creation_allowed"),
    ]

    for counter, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            totals[counter] = 1

    return totals


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, fieldname):
            doc.set(fieldname, value)

    if totals["snapshot_line_count"]:
        doc.overall_completion_percent = round(
            (totals["ready_stage_count"] / totals["snapshot_line_count"]) * 100,
            2,
        )
    else:
        doc.overall_completion_percent = 0

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "CRM Deal linked",
        "complete": bool(doc.get("crm_deal")),
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
        "label": "Care Management Integration Run linked",
        "complete": bool(doc.get("care_management_integration_run")),
    })

    checks.append({
        "label": "Dashboard owner assigned",
        "complete": bool(doc.get("operational_dashboard_owner")),
    })

    lines = _active_lines(doc)

    checks.append({
        "label": "Dashboard snapshot lines exist",
        "complete": bool(lines),
    })

    checks.append({
        "label": "Dashboard review complete",
        "complete": bool(doc.get("dashboard_review_complete")),
    })

    checks.append({
        "label": "Dashboard data verified",
        "complete": bool(doc.get("dashboard_data_verified")),
    })

    blocked_run_fields = [
        ("Record creation remains blocked in Phase 57", "record_creation_allowed"),
        ("Record update remains blocked in Phase 57", "record_update_allowed"),
        ("Communication creation remains blocked in Phase 57", "communication_creation_allowed"),
        ("Email sending remains blocked in Phase 57", "email_send_allowed"),
        ("Event creation remains blocked in Phase 57", "event_creation_allowed"),
        ("ToDo creation remains blocked in Phase 57", "todo_creation_allowed"),
        ("Task creation remains blocked in Phase 57", "task_creation_allowed"),
        ("Finance document creation remains blocked in Phase 57", "finance_document_creation_allowed"),
        ("Claim document creation remains blocked in Phase 57", "claim_document_creation_allowed"),
        ("Remittance document creation remains blocked in Phase 57", "remittance_document_creation_allowed"),
        ("Accounting document creation remains blocked in Phase 57", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        checks.append({
            "label": label,
            "complete": not bool(doc.get(fieldname)),
        })

    if lines:
        checks.extend([
            {
                "label": "All lines reviewed",
                "complete": not [row.module_stage for row in lines if not row.get("snapshot_review_complete")],
            },
            {
                "label": "All line data verified",
                "complete": not [row.module_stage for row in lines if not row.get("snapshot_data_verified")],
            },
            {
                "label": "All lines ready for dashboard",
                "complete": not [row.module_stage for row in lines if not row.get("line_ready_for_dashboard")],
            },
        ])

    total = len(checks)
    complete = len([row for row in checks if row["complete"]])
    readiness_percent = round((complete / total) * 100, 2) if total else 0
    incomplete = [row["label"] for row in checks if not row["complete"]]

    return {
        "total_checks": total,
        "complete_checks": complete,
        "readiness_percent": readiness_percent,
        "operational_dashboard_snapshot_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.operational_dashboard_snapshot_run_ready = 1 if summary["operational_dashboard_snapshot_run_ready"] else 0

    targets = [
        (CRM_DEAL, doc.get("crm_deal")),
        (PARTICIPANT_SERVICE_FILE, doc.get("participant_service_file")),
        (CARE_MANAGEMENT_INTEGRATION_RUN, doc.get("care_management_integration_run")),
        (POST_CLOSURE_ROUTING_FINALISATION_RUN, doc.get("post_closure_routing_finalisation_run")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_operational_dashboard_snapshot_run", doc.name)
        _db_set_if_field(doctype, name, "operational_dashboard_snapshot_status", doc.status)
        _db_set_if_field(doctype, name, "operational_dashboard_snapshot_ready", 1 if summary["operational_dashboard_snapshot_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


def _copy_deal_values(doc, deal):
    doc.crm_deal = deal
    doc.crm_lead = _get_first_existing_value(CRM_DEAL, deal, ["crm_lead", "lead", "ndis_crm_lead"])
    doc.participant_customer = _get_first_existing_value(CRM_DEAL, deal, ["participant_customer", "customer", "ndis_customer"])
    doc.participant_service_file = _get_first_existing_value(CRM_DEAL, deal, ["participant_service_file", "ndis_participant_service_file"])
    doc.care_management_integration_run = _get_first_existing_value(CRM_DEAL, deal, ["ndis_care_management_integration_run", "care_management_integration_run"])
    doc.post_closure_routing_finalisation_run = _get_first_existing_value(CRM_DEAL, deal, ["ndis_post_closure_routing_final_run", "ndis_recovery_outcome_post_closure_routing_finalisation_run"])

    doc.participant_name = _get_first_existing_value(CRM_DEAL, deal, ["participant_name", "customer_name", "organization", "title"]) or deal
    doc.ndis_number = _get_first_existing_value(CRM_DEAL, deal, ["ndis_number", "participant_ndis_number"])
    doc.plan_start_date = _get_first_existing_value(CRM_DEAL, deal, ["plan_start_date", "ndis_plan_start_date"])
    doc.plan_end_date = _get_first_existing_value(CRM_DEAL, deal, ["plan_end_date", "ndis_plan_end_date"])
    doc.company = _get_first_existing_value(CRM_DEAL, deal, ["company"])


@frappe.whitelist()
def create_operational_dashboard_snapshot_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Operational Dashboard Snapshot Run returned.",
        }

    doc = frappe.new_doc(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN)
    doc.status = "Draft"
    doc.snapshot_mode = "Read Only Operational Snapshot"
    doc.operational_dashboard_owner = frappe.session.user

    doc.dashboard_completion_allowed = 0
    doc.record_creation_allowed = 0
    doc.record_update_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.finance_document_creation_allowed = 0
    doc.claim_document_creation_allowed = 0
    doc.remittance_document_creation_allowed = 0
    doc.accounting_document_creation_allowed = 0

    _copy_deal_values(doc, deal)
    created_count = _generate_lines(doc)
    doc.snapshot_line_count = created_count

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.operational_dashboard_snapshot_run_ready = 1 if summary["operational_dashboard_snapshot_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)

    frappe.db.commit()

    return {
        "doctype": OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        "name": doc.name,
        "created": True,
        "snapshot_line_count": created_count,
        "message": "NDIS CRM Operational Dashboard Snapshot Run created successfully.",
    }


@frappe.whitelist()
def refresh_operational_dashboard_snapshot_lines(operational_dashboard_snapshot_run):
    _check_role()

    doc = frappe.get_doc(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, operational_dashboard_snapshot_run)

    created_count = _generate_lines(doc)

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Operational dashboard snapshot lines refreshed. Lines: {created_count}.",
    }


@frappe.whitelist()
def validate_operational_dashboard_snapshot_readiness(operational_dashboard_snapshot_run):
    _check_role()

    doc = frappe.get_doc(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, operational_dashboard_snapshot_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Operational Dashboard Snapshot readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_operational_dashboard_snapshot(operational_dashboard_snapshot_run):
    _check_role()

    doc = frappe.get_doc(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, operational_dashboard_snapshot_run)
    summary = _calculate_readiness(doc)

    if not summary["operational_dashboard_snapshot_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Dashboard Completion. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Dashboard Completion"
    doc.readiness_percent = summary["readiness_percent"]
    doc.operational_dashboard_snapshot_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        "name": doc.name,
        "message": "Operational Dashboard Snapshot Run marked Ready.",
    }


@frappe.whitelist()
def approve_operational_dashboard_snapshot_run(operational_dashboard_snapshot_run):
    _check_role()

    doc = frappe.get_doc(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, operational_dashboard_snapshot_run)
    summary = _calculate_readiness(doc)

    if not summary["operational_dashboard_snapshot_run_ready"]:
        frappe.throw(
            _("Cannot approve Operational Dashboard Snapshot Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Dashboard Snapshot Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.operational_dashboard_snapshot_run_ready = 1
    doc.dashboard_completion_allowed = 0

    for row in doc.get("operational_dashboard_snapshot_lines") or []:
        if row.get("dashboard_line_status") in ["Draft", "Ready"]:
            row.dashboard_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        "name": doc.name,
        "message": "Operational Dashboard Snapshot Run approved. No downstream record was created or updated.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("dashboard_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("snapshot_review_complete"):
            continue

        if not row.get("snapshot_data_verified"):
            continue

        if not row.get("line_ready_for_dashboard"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_operational_dashboard_snapshot(operational_dashboard_snapshot_run):
    _check_role()

    doc = frappe.get_doc(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, operational_dashboard_snapshot_run)

    if doc.status != "Dashboard Snapshot Approved":
        frappe.throw(_("Operational Dashboard Snapshot Run must be approved before completion."))

    if not doc.get("dashboard_completion_allowed"):
        frappe.throw(_("Tick Dashboard Completion Allowed before completing the dashboard snapshot."))

    if (doc.get("snapshot_mode") or "Read Only Operational Snapshot") != "Read Only Operational Snapshot":
        frappe.throw(_("Phase 57 supports read-only operational snapshot mode only."))

    blocked_run_fields = [
        ("Record Creation Allowed", "record_creation_allowed"),
        ("Record Update Allowed", "record_update_allowed"),
        ("Communication Creation Allowed", "communication_creation_allowed"),
        ("Email Send Allowed", "email_send_allowed"),
        ("Event Creation Allowed", "event_creation_allowed"),
        ("ToDo Creation Allowed", "todo_creation_allowed"),
        ("Task Creation Allowed", "task_creation_allowed"),
        ("Finance Document Creation Allowed", "finance_document_creation_allowed"),
        ("Claim Document Creation Allowed", "claim_document_creation_allowed"),
        ("Remittance Document Creation Allowed", "remittance_document_creation_allowed"),
        ("Accounting Document Creation Allowed", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} must remain unticked in Phase 57.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["operational_dashboard_snapshot_run_ready"]:
        frappe.throw(
            _("Cannot complete Operational Dashboard Snapshot. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines:
        frappe.throw(_("No ready Operational Dashboard Snapshot lines found."))

    for row in ready_lines:
        row.dashboard_line_status = "Dashboard Line Completed"

    doc.status = "Dashboard Snapshot Completed"
    doc.dashboard_completion_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "completed_line_count": len(ready_lines),
        "message": "Operational dashboard snapshot completed. No Care Management, Communication, Email Queue, Event, ToDo, Task, Recovery Case, Sales Invoice, Payment Entry, Journal Entry, GL Entry, Claim Batch, Claim Line, Remittance Import, adjustment, or bank reconciliation record was created or updated.",
    }


def validate_operational_dashboard_snapshot_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.operational_dashboard_snapshot_run_ready = 1 if summary["operational_dashboard_snapshot_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["operational_dashboard_snapshot_run_ready"]:
        frappe.throw(
            _("Cannot set Operational Dashboard Snapshot Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Dashboard Snapshot Approved" and doc.get("dashboard_completion_allowed"):
        frappe.throw(_("Dashboard Completion Allowed can only be ticked after the run is approved."))

    blocked_run_fields = [
        ("Record creation", "record_creation_allowed"),
        ("Record update", "record_update_allowed"),
        ("Communication creation", "communication_creation_allowed"),
        ("Email send", "email_send_allowed"),
        ("Event creation", "event_creation_allowed"),
        ("ToDo creation", "todo_creation_allowed"),
        ("Task creation", "task_creation_allowed"),
        ("Finance document creation", "finance_document_creation_allowed"),
        ("Claim document creation", "claim_document_creation_allowed"),
        ("Remittance document creation", "remittance_document_creation_allowed"),
        ("Accounting document creation", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} is not allowed in Phase 57.").format(label))


def on_operational_dashboard_snapshot_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Operational Dashboard Snapshot Run Summary Sync Failed"
        )


def validate_crm_deal_phase57(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_operational_dashboard_snapshot_required"):
        required = doc.get("ndis_operational_dashboard_snapshot_required")

    if not required:
        return

    run = doc.get("ndis_operational_dashboard_snapshot_run") if _field_exists(CRM_DEAL, "ndis_operational_dashboard_snapshot_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Operational Dashboard Snapshot Run must be created and approved/completed.")
        )

    if not _is_snapshot_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Operational Dashboard Snapshot Run must be approved/completed.")
        )


def validate_crm_deal_phase57_combined(doc, method=None):
    try:
        from ndis_crm.phase56_care_management_integration import validate_crm_deal_phase56_combined
        validate_crm_deal_phase56_combined(doc, method)
    except ImportError:
        pass

    validate_crm_deal_phase57(doc, method)


def phase57_health_check():
    print("---- NDIS CRM Phase 57 Health Check ----")

    for dt in [
        OPERATIONAL_DASHBOARD_SNAPSHOT_LINE,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        CRM_DEAL,
        PARTICIPANT_SERVICE_FILE,
        CARE_MANAGEMENT_INTEGRATION_RUN,
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
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
        "ndis_operational_dashboard_snapshot_required",
        "ndis_operational_dashboard_snapshot_run",
        "operational_dashboard_snapshot_status",
        "operational_dashboard_snapshot_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print(
        "NDIS CRM Operational Dashboard Snapshot Run records:",
        frappe.db.count(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN) if _doctype_exists(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN) else 0
    )
    print("Phase 57 creates CRM operational dashboard snapshot run/line records only.")
    print("Phase 57 is read-only visibility and does not create or update operational, care management, finance, claim, remittance, communication, task, or accounting records.")
    print("---- End Phase 57 Health Check ----")
