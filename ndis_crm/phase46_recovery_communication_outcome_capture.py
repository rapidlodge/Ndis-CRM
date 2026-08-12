import frappe
from frappe import _
from frappe.utils import now


CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
ROSTER_REQUEST = "NDIS CRM Roster Build Request"
SERVICE_FILE = "NDIS Participant Service File"
SESSION_DRAFT = "NDIS CRM Service Session Draft"
EVIDENCE_REVIEW = "NDIS CRM Service Delivery Evidence Review"
DOWNSTREAM_PREPARATION = "NDIS CRM Downstream Preparation"
ATTENDANCE_DRAFT = "NDIS CRM Attendance Draft"
BILLING_DRAFT = "NDIS CRM Billing Draft"
CLAIM_DRAFT = "NDIS CRM Claim Draft"
INVOICE_DRAFT = "NDIS CRM Invoice Draft"
SALES_INVOICE_DRAFT_RUN = "NDIS CRM Sales Invoice Draft Run"
SALES_INVOICE_SUBMISSION_RUN = "NDIS CRM Sales Invoice Submission Run"
CLAIM_BATCH_DRAFT_RUN = "NDIS CRM Claim Batch Draft Run"
CLAIM_BATCH_SUBMISSION_RUN = "NDIS CRM Claim Batch Submission Run"
CLAIM_EXPORT_PREP_RUN = "NDIS CRM Claim Export Preparation Run"
CLAIM_LODGEMENT_CONFIRMATION_RUN = "NDIS CRM Claim Lodgement Confirmation Run"
REMITTANCE_IMPORT_PREP_RUN = "NDIS CRM Remittance Import Preparation Run"
ACTUAL_REMITTANCE_IMPORT_RUN = "NDIS CRM Actual Remittance Import Run"
REMITTANCE_MATCHING_REVIEW_RUN = "NDIS CRM Remittance Matching Review Run"
PAYMENT_ALLOCATION_PREP_RUN = "NDIS CRM Payment Allocation Preparation Run"
PAYMENT_ENTRY_DRAFT_RUN = "NDIS CRM Payment Entry Draft Run"
PAYMENT_ENTRY_SUBMISSION_RUN = "NDIS CRM Payment Entry Submission Run"
REMITTANCE_IMPORT_FINALISATION_RUN = "NDIS CRM Remittance Import Finalisation Run"
VARIANCE_REJECTION_REVIEW_RUN = "NDIS CRM Variance Rejection Review Run"
WRITE_OFF_PREPARATION_RUN = "NDIS CRM Write Off Preparation Run"
WRITE_OFF_DRAFT_RUN = "NDIS CRM Write Off Draft Run"
WRITE_OFF_JE_DRAFT_RUN = "NDIS CRM Write Off JE Draft Run"
WRITE_OFF_JE_SUBMISSION_RUN = "NDIS CRM Write Off JE Submission Run"
WRITE_OFF_FINALISATION_RUN = "NDIS CRM Write Off Finalisation Run"
RECOVERY_PREPARATION_RUN = "NDIS CRM Recovery Preparation Run"
RECOVERY_CASE_DRAFT_RUN = "NDIS CRM Recovery Case Draft Run"
RECOVERY_CASE_SUBMISSION_RUN = "NDIS CRM Recovery Case Submission Run"
RECOVERY_FOLLOW_UP_PREPARATION_RUN = "NDIS CRM Recovery Follow Up Preparation Run"
RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN = "NDIS CRM Recovery Follow Up Task Draft Run"
RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN = "NDIS CRM Recovery Follow Up Task Activation Run"
RECOVERY_COMMUNICATION_DRAFT_PREPARATION_RUN = "NDIS CRM Recovery Communication Draft Preparation Run"
RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN = "NDIS CRM Recovery Communication Draft Creation Run"
RECOVERY_COMMUNICATION_DISPATCH_RUN = "NDIS CRM Recovery Communication Dispatch Run"
RECOVERY_COMMUNICATION_DISPATCH_LINE = "NDIS CRM Recovery Communication Dispatch Line"

RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN = "NDIS CRM Recovery Communication Outcome Capture Run"
RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_LINE = "NDIS CRM Recovery Communication Outcome Capture Line"

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
    "Ready for Outcome Capture",
    "Outcome Capture Approved",
    "Outcomes Captured",
]

APPROVED_STATUSES = [
    "Outcome Capture Approved",
    "Outcomes Captured",
]

ALLOWED_ROLES = {
    "Administrator",
    "System Manager",
    "Accounts Manager",
    "Accounts User",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
}


def _check_role():
    if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this recovery communication outcome capture action."))


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


def _to_float(value):
    if value in [None, ""]:
        return 0
    try:
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").strip()
        return float(value)
    except Exception:
        return 0


def _existing_run_for_dispatch_run(recovery_communication_dispatch_run):
    if not _doctype_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN):
        return None

    if _field_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, "ndis_recovery_communication_outcome_capture_run"):
        existing = frappe.db.get_value(
            RECOVERY_COMMUNICATION_DISPATCH_RUN,
            recovery_communication_dispatch_run,
            "ndis_recovery_communication_outcome_capture_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
        {"recovery_communication_dispatch_run": recovery_communication_dispatch_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_recovery_communication_outcome_capture_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_communication_outcome_capture_run")
        if existing:
            return existing

    return frappe.db.get_value(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, {"crm_deal": deal}, "name")


def _get_dispatch_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_recovery_communication_dispatch_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_communication_dispatch_run")
        if run:
            return run

    return frappe.db.get_value(RECOVERY_COMMUNICATION_DISPATCH_RUN, {"crm_deal": deal}, "name")


def _is_dispatch_completed(run):
    if not run or not frappe.db.exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_COMMUNICATION_DISPATCH_RUN,
        run,
        ["status", "recovery_communication_dispatch_run_ready"],
    )

    return status == "Communication Dispatch Completed" and bool(ready)


def _is_outcome_capture_approved(run):
    if not run or not frappe.db.exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
        run,
        ["status", "recovery_communication_outcome_capture_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _append_line_if_missing(doc, row_data):
    existing = {
        row.recovery_communication_outcome_source_key
        for row in doc.get("recovery_communication_outcome_capture_lines") or []
        if row.get("recovery_communication_outcome_source_key")
    }

    key = row_data.get("recovery_communication_outcome_source_key")

    if key and key in existing:
        return False

    doc.append("recovery_communication_outcome_capture_lines", row_data)
    return True


def _source_key(row):
    return row.get("recovery_communication_dispatch_source_key") or "|".join([
        str(row.get("target_communication") or ""),
        str(row.get("target_todo") or ""),
        str(row.get("target_task") or ""),
        str(row.get("service_line") or ""),
        str(row.get("draft_subject") or ""),
    ])


def _is_dispatch_line_done(row):
    return row.get("recovery_communication_dispatch_line_status") in [
        "Dispatch Logged",
        "Communication Marked Sent",
        "Email Dispatch Requested",
    ]


def _default_outcome_status(row):
    status = row.get("recovery_communication_dispatch_line_status")
    if status == "Email Dispatch Requested":
        return "No Response Yet"
    if status == "Communication Marked Sent":
        return "No Response Yet"
    if status == "Dispatch Logged":
        return "No Response Yet"
    return "No Response Yet"


def _default_next_action(outcome_status):
    if outcome_status == "No Response Yet":
        return "Monitor for response"
    if outcome_status == "Response Received":
        return "Review response details"
    if outcome_status == "Payment Promise Received":
        return "Prepare recovery payment monitoring"
    if outcome_status == "Evidence Requested":
        return "Prepare evidence request follow-up"
    if outcome_status == "Wrong Contact":
        return "Prepare contact correction"
    if outcome_status == "Dispute Raised":
        return "Prepare dispute review"
    if outcome_status == "Escalation Required":
        return "Prepare escalation review"
    if outcome_status == "Recovery Not Required":
        return "Prepare closure review"
    if outcome_status == "Closed No Further Action":
        return "Close recovery communication path"
    return "Review outcome"


def _build_outcome_line(row, source_doc):
    source_ready = bool(
        source_doc.get("status") == "Communication Dispatch Completed"
        and _is_dispatch_line_done(row)
        and row.get("recovery_communication_dispatch_source_ready")
        and row.get("dispatch_review_complete")
        and row.get("recipient_details_verified")
        and row.get("dispatch_authorized")
        and row.get("line_ready_for_recovery_communication_dispatch")
        and not row.get("event_creation_authorized")
        and not row.get("todo_creation_authorized")
        and not row.get("task_creation_authorized")
        and not row.get("recovery_case_creation_authorized")
        and not row.get("journal_entry_authorized")
        and not row.get("manual_gl_authorized")
        and not row.get("payment_entry_authorized")
        and not row.get("sales_invoice_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("bank_reconciliation_authorized")
        and not row.get("recovery_communication_dispatch_hold")
        and _to_float(row.get("proposed_recovery_amount")) > 0
    )

    outcome_status = _default_outcome_status(row)

    return {
        "recovery_communication_outcome_source_key": _source_key(row),

        "target_dispatch_mode_snapshot": row.get("target_dispatch_mode_snapshot"),
        "target_communication": row.get("target_communication"),
        "target_communication_status": row.get("target_communication_status"),
        "target_email_queue_status": row.get("target_email_queue_status"),
        "dispatch_reference": row.get("dispatch_reference"),
        "dispatch_line_status_snapshot": row.get("recovery_communication_dispatch_line_status"),

        "target_creation_mode_snapshot": row.get("target_creation_mode_snapshot"),
        "target_task_mode_snapshot": row.get("target_task_mode_snapshot"),
        "target_todo": row.get("target_todo"),
        "target_todo_status": row.get("target_todo_status"),
        "target_task": row.get("target_task"),
        "target_task_status": row.get("target_task_status"),

        "target_case_doctype": row.get("target_case_doctype"),
        "target_case_name": row.get("target_case_name"),
        "target_case_docstatus": row.get("target_case_docstatus"),
        "target_case_status": row.get("target_case_status"),

        "service_line": row.get("service_line"),
        "service_code": row.get("service_code"),
        "service_date": row.get("service_date"),
        "sales_invoice": row.get("sales_invoice"),
        "payment_entry": row.get("payment_entry"),
        "journal_entry": row.get("journal_entry"),
        "ndis_remittance_import": row.get("ndis_remittance_import"),
        "ndis_claim_batch": row.get("ndis_claim_batch"),
        "ndis_claim_line": row.get("ndis_claim_line"),

        "proposed_recovery_amount": row.get("proposed_recovery_amount"),
        "recovery_type": row.get("recovery_type"),
        "recovery_route": row.get("recovery_route"),
        "recovery_reason": row.get("recovery_reason"),
        "recovery_party_type": row.get("recovery_party_type") or "Customer",
        "recovery_party": row.get("recovery_party") or source_doc.get("participant_customer"),
        "recovery_contact_name": row.get("recovery_contact_name"),
        "recovery_contact_email": row.get("recovery_contact_email"),
        "recovery_due_date": row.get("recovery_due_date"),

        "communication_draft_type": row.get("communication_draft_type"),
        "communication_priority": row.get("communication_priority") or "Normal",
        "communication_owner": row.get("communication_owner") or frappe.session.user,
        "communication_due_date": row.get("communication_due_date"),
        "recipient_party_type": row.get("recipient_party_type"),
        "recipient_party": row.get("recipient_party") or source_doc.get("participant_customer"),
        "recipient_name": row.get("recipient_name"),
        "recipient_email": row.get("recipient_email"),
        "recipient_phone": row.get("recipient_phone"),
        "draft_subject": row.get("draft_subject"),
        "draft_body": row.get("draft_body"),
        "draft_call_script": row.get("draft_call_script"),
        "internal_review_note": row.get("internal_review_note"),

        "recovery_communication_outcome_source_ready": 1 if source_ready else 0,
        "outcome_review_complete": 0,
        "outcome_recorded": 0,
        "outcome_authorized": 0,

        "outcome_status": outcome_status,
        "outcome_summary": None,
        "response_received_on": None,
        "response_received_from": None,
        "response_reference": None,
        "promised_payment_date": None,
        "promised_payment_amount": 0,
        "evidence_requested": 0,
        "dispute_reason": None,
        "correct_contact_name": None,
        "correct_contact_email": None,
        "correct_contact_phone": None,
        "next_action_recommendation": _default_next_action(outcome_status),

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

        "recovery_communication_outcome_hold": 0 if source_ready else 1,
        "recovery_communication_outcome_hold_reason": None if source_ready else "Phase 45 dispatch source is not ready for outcome capture.",
        "line_ready_for_recovery_communication_outcome_capture": 0,
        "recovery_communication_outcome_capture_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_dispatch_run(doc, source):
    created = 0

    for row in source.get("recovery_communication_dispatch_lines") or []:
        if not _is_dispatch_line_done(row):
            continue

        if _to_float(row.get("proposed_recovery_amount")) <= 0:
            continue

        if _append_line_if_missing(doc, _build_outcome_line(row, source)):
            created += 1

    return created


def _active_lines(doc):
    return [
        row for row in doc.get("recovery_communication_outcome_capture_lines") or []
        if _to_float(row.get("proposed_recovery_amount")) > 0
    ]


def _calculate_totals(doc):
    totals = {
        "recovery_communication_outcome_capture_line_count": 0,
        "recovery_communication_outcome_amount_total": 0,
        "recovery_communication_outcome_ready_count": 0,
        "recovery_communication_outcome_hold_count": 0,
        "no_response_count": 0,
        "response_received_count": 0,
        "payment_promise_count": 0,
        "evidence_requested_count": 0,
        "wrong_contact_count": 0,
        "dispute_raised_count": 0,
        "escalation_required_count": 0,
        "closed_no_action_count": 0,
        "outcome_captured_count": 0,
        "blocked_communication_count": 0,
        "blocked_email_send_count": 0,
        "blocked_event_count": 0,
        "blocked_todo_count": 0,
        "blocked_task_count": 0,
        "blocked_recovery_case_count": 0,
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

    for row in doc.get("recovery_communication_outcome_capture_lines") or []:
        totals["recovery_communication_outcome_capture_line_count"] += 1
        totals["recovery_communication_outcome_amount_total"] += _to_float(row.get("proposed_recovery_amount"))

        if row.get("line_ready_for_recovery_communication_outcome_capture"):
            totals["recovery_communication_outcome_ready_count"] += 1

        if row.get("recovery_communication_outcome_hold"):
            totals["recovery_communication_outcome_hold_count"] += 1

        outcome_status = row.get("outcome_status")
        if outcome_status == "No Response Yet":
            totals["no_response_count"] += 1
        elif outcome_status == "Response Received":
            totals["response_received_count"] += 1
        elif outcome_status == "Payment Promise Received":
            totals["payment_promise_count"] += 1
        elif outcome_status == "Evidence Requested":
            totals["evidence_requested_count"] += 1
        elif outcome_status == "Wrong Contact":
            totals["wrong_contact_count"] += 1
        elif outcome_status == "Dispute Raised":
            totals["dispute_raised_count"] += 1
        elif outcome_status == "Escalation Required":
            totals["escalation_required_count"] += 1
        elif outcome_status in ["Closed No Further Action", "Recovery Not Required"]:
            totals["closed_no_action_count"] += 1

        if row.get("recovery_communication_outcome_capture_line_status") == "Outcome Captured":
            totals["outcome_captured_count"] += 1

        blocked_fields = [
            ("blocked_communication_count", "communication_creation_authorized"),
            ("blocked_email_send_count", "email_send_authorized"),
            ("blocked_event_count", "event_creation_authorized"),
            ("blocked_todo_count", "todo_creation_authorized"),
            ("blocked_task_count", "task_creation_authorized"),
            ("blocked_recovery_case_count", "recovery_case_creation_authorized"),
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

        for counter, fieldname in blocked_fields:
            if row.get(fieldname):
                totals[counter] += 1

    totals["recovery_communication_outcome_amount_total"] = round(
        totals["recovery_communication_outcome_amount_total"],
        2,
    )

    return totals


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Recovery Communication Dispatch Run linked",
        "complete": bool(doc.get("recovery_communication_dispatch_run")),
    })

    checks.append({
        "label": "Recovery communication dispatch completed",
        "complete": _is_dispatch_completed(doc.get("recovery_communication_dispatch_run")),
    })

    checks.append({
        "label": "Participant Customer linked",
        "complete": bool(doc.get("participant_customer")),
    })

    checks.append({
        "label": "Company selected",
        "complete": bool(doc.get("company")),
    })

    checks.append({
        "label": "Recovery Communication Outcome Capture Owner assigned",
        "complete": bool(doc.get("recovery_communication_outcome_capture_owner")),
    })

    lines = _active_lines(doc)
    no_candidates = bool(doc.get("no_recovery_communication_outcome_candidate_found"))

    checks.append({
        "label": "Outcome capture lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("recovery_communication_outcome_source_ready")]
        checks.append({
            "label": "Outcome source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        missing_outcome = [row.service_line for row in lines if not row.get("outcome_status")]
        checks.append({
            "label": "All lines have outcome status",
            "complete": not missing_outcome,
            "details": missing_outcome,
        })

        review_missing = [row.service_line for row in lines if not row.get("outcome_review_complete")]
        checks.append({
            "label": "Outcome review complete",
            "complete": not review_missing,
            "details": review_missing,
        })

        recorded_missing = [row.service_line for row in lines if not row.get("outcome_recorded")]
        checks.append({
            "label": "Outcome recorded",
            "complete": not recorded_missing,
            "details": recorded_missing,
        })

        auth_missing = [row.service_line for row in lines if not row.get("outcome_authorized")]
        checks.append({
            "label": "Outcome authorized",
            "complete": not auth_missing,
            "details": auth_missing,
        })

        payment_promise_missing = [
            row.service_line for row in lines
            if row.get("outcome_status") == "Payment Promise Received"
            and (not row.get("promised_payment_date") or _to_float(row.get("promised_payment_amount")) <= 0)
        ]
        checks.append({
            "label": "Payment promise outcomes include promised date and amount",
            "complete": not payment_promise_missing,
            "details": payment_promise_missing,
        })

        wrong_contact_missing = [
            row.service_line for row in lines
            if row.get("outcome_status") == "Wrong Contact"
            and not (row.get("correct_contact_name") or row.get("correct_contact_email") or row.get("correct_contact_phone"))
        ]
        checks.append({
            "label": "Wrong contact outcomes include corrected contact detail",
            "complete": not wrong_contact_missing,
            "details": wrong_contact_missing,
        })

        blocked_fields = [
            ("Communication creation remains blocked in Phase 46", "communication_creation_authorized"),
            ("Email sending remains blocked in Phase 46", "email_send_authorized"),
            ("Event creation remains blocked in Phase 46", "event_creation_authorized"),
            ("ToDo creation remains blocked in Phase 46", "todo_creation_authorized"),
            ("Task creation remains blocked in Phase 46", "task_creation_authorized"),
            ("Recovery Case creation remains blocked in Phase 46", "recovery_case_creation_authorized"),
            ("Journal Entry authorization remains blocked in Phase 46", "journal_entry_authorized"),
            ("Manual GL authorization remains blocked in Phase 46", "manual_gl_authorized"),
            ("Payment Entry authorization remains blocked in Phase 46", "payment_entry_authorized"),
            ("Sales Invoice authorization remains blocked in Phase 46", "sales_invoice_authorized"),
            ("Adjustment authorization remains blocked in Phase 46", "adjustment_authorized"),
            ("Bank reconciliation authorization remains blocked in Phase 46", "bank_reconciliation_authorized"),
            ("Claim Batch authorization remains blocked in Phase 46", "claim_batch_authorized"),
            ("Claim Line authorization remains blocked in Phase 46", "claim_line_authorized"),
            ("Remittance Import authorization remains blocked in Phase 46", "remittance_import_authorized"),
        ]

        for label, fieldname in blocked_fields:
            blocked = [row.service_line for row in lines if row.get(fieldname)]
            checks.append({
                "label": label,
                "complete": not blocked,
                "details": blocked,
            })

        holds = [row.service_line for row in lines if row.get("recovery_communication_outcome_hold")]
        checks.append({
            "label": "No active outcome capture hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_recovery_communication_outcome_capture")]
        checks.append({
            "label": "All active lines marked ready for outcome capture",
            "complete": not not_ready,
            "details": not_ready,
        })

    total = len(checks)
    complete = len([row for row in checks if row["complete"]])
    readiness_percent = round((complete / total) * 100, 2) if total else 0

    incomplete = []
    for row in checks:
        if row["complete"]:
            continue

        label = row["label"]
        if row.get("details"):
            label += ": " + ", ".join([str(x) for x in row["details"] if x])
        incomplete.append(label)

    return {
        "total_checks": total,
        "complete_checks": complete,
        "readiness_percent": readiness_percent,
        "recovery_communication_outcome_capture_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, "recovery_communication_outcome_capture_run_ready"):
        doc.recovery_communication_outcome_capture_run_ready = 1 if summary["recovery_communication_outcome_capture_run_ready"] else 0

    targets = [
        (CRM_DEAL, doc.get("crm_deal")),
        (HANDOVER, doc.get("handover")),
        (FINANCE_ONBOARDING, doc.get("finance_onboarding")),
        (OPERATIONS_SETUP, doc.get("operations_setup")),
        (SCHEDULE_DRAFT, doc.get("service_schedule_draft")),
        (ROSTER_REQUEST, doc.get("roster_build_request")),
        (SERVICE_FILE, doc.get("participant_service_file")),
        (SESSION_DRAFT, doc.get("service_session_draft")),
        (EVIDENCE_REVIEW, doc.get("delivery_evidence_review")),
        (DOWNSTREAM_PREPARATION, doc.get("downstream_preparation")),
        (ATTENDANCE_DRAFT, doc.get("attendance_draft")),
        (BILLING_DRAFT, doc.get("billing_draft")),
        (CLAIM_DRAFT, doc.get("claim_draft")),
        (INVOICE_DRAFT, doc.get("invoice_draft")),
        (SALES_INVOICE_DRAFT_RUN, doc.get("sales_invoice_draft_run")),
        (SALES_INVOICE_SUBMISSION_RUN, doc.get("sales_invoice_submission_run")),
        (CLAIM_BATCH_DRAFT_RUN, doc.get("claim_batch_draft_run")),
        (CLAIM_BATCH_SUBMISSION_RUN, doc.get("claim_batch_submission_run")),
        (CLAIM_EXPORT_PREP_RUN, doc.get("claim_export_preparation_run")),
        (CLAIM_LODGEMENT_CONFIRMATION_RUN, doc.get("claim_lodgement_confirmation_run")),
        (REMITTANCE_IMPORT_PREP_RUN, doc.get("remittance_import_preparation_run")),
        (ACTUAL_REMITTANCE_IMPORT_RUN, doc.get("actual_remittance_import_run")),
        (REMITTANCE_MATCHING_REVIEW_RUN, doc.get("remittance_matching_review_run")),
        (PAYMENT_ALLOCATION_PREP_RUN, doc.get("payment_allocation_preparation_run")),
        (PAYMENT_ENTRY_DRAFT_RUN, doc.get("payment_entry_draft_run")),
        (PAYMENT_ENTRY_SUBMISSION_RUN, doc.get("payment_entry_submission_run")),
        (REMITTANCE_IMPORT_FINALISATION_RUN, doc.get("remittance_import_finalisation_run")),
        (VARIANCE_REJECTION_REVIEW_RUN, doc.get("variance_rejection_review_run")),
        (WRITE_OFF_PREPARATION_RUN, doc.get("write_off_preparation_run")),
        (WRITE_OFF_DRAFT_RUN, doc.get("write_off_draft_run")),
        (WRITE_OFF_JE_DRAFT_RUN, doc.get("write_off_je_draft_run")),
        (WRITE_OFF_JE_SUBMISSION_RUN, doc.get("write_off_je_submission_run")),
        (WRITE_OFF_FINALISATION_RUN, doc.get("write_off_finalisation_run")),
        (RECOVERY_PREPARATION_RUN, doc.get("recovery_preparation_run")),
        (RECOVERY_CASE_DRAFT_RUN, doc.get("recovery_case_draft_run")),
        (RECOVERY_CASE_SUBMISSION_RUN, doc.get("recovery_case_submission_run")),
        (RECOVERY_FOLLOW_UP_PREPARATION_RUN, doc.get("recovery_follow_up_preparation_run")),
        (RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, doc.get("recovery_follow_up_task_draft_run")),
        (RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, doc.get("recovery_follow_up_task_activation_run")),
        (RECOVERY_COMMUNICATION_DRAFT_PREPARATION_RUN, doc.get("recovery_communication_draft_preparation_run")),
        (RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN, doc.get("recovery_communication_draft_creation_run")),
        (RECOVERY_COMMUNICATION_DISPATCH_RUN, doc.get("recovery_communication_dispatch_run")),
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_recovery_communication_outcome_capture_run", doc.name)
        _db_set_if_field(doctype, name, "recovery_communication_outcome_capture_status", doc.status)
        _db_set_if_field(doctype, name, "recovery_communication_outcome_capture_ready", 1 if summary["recovery_communication_outcome_capture_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_recovery_communication_outcome_capture_run_from_dispatch_run(recovery_communication_dispatch_run):
    _check_role()

    if not recovery_communication_dispatch_run:
        frappe.throw(_("NDIS CRM Recovery Communication Dispatch Run is required."))

    if not frappe.db.exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, recovery_communication_dispatch_run):
        frappe.throw(_("NDIS CRM Recovery Communication Dispatch Run {0} was not found.").format(recovery_communication_dispatch_run))

    existing = _existing_run_for_dispatch_run(recovery_communication_dispatch_run)
    if existing:
        return {
            "doctype": RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Communication Outcome Capture Run returned.",
        }

    source = frappe.get_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN, recovery_communication_dispatch_run)

    doc = frappe.new_doc(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN)
    doc.status = "Draft"
    doc.recovery_communication_dispatch_run = source.name
    doc.recovery_communication_draft_creation_run = source.get("recovery_communication_draft_creation_run")
    doc.recovery_communication_draft_preparation_run = source.get("recovery_communication_draft_preparation_run")
    doc.recovery_follow_up_task_activation_run = source.get("recovery_follow_up_task_activation_run")
    doc.recovery_follow_up_task_draft_run = source.get("recovery_follow_up_task_draft_run")
    doc.recovery_follow_up_preparation_run = source.get("recovery_follow_up_preparation_run")
    doc.recovery_case_submission_run = source.get("recovery_case_submission_run")
    doc.recovery_case_draft_run = source.get("recovery_case_draft_run")
    doc.recovery_preparation_run = source.get("recovery_preparation_run")
    doc.write_off_finalisation_run = source.get("write_off_finalisation_run")
    doc.write_off_je_submission_run = source.get("write_off_je_submission_run")
    doc.write_off_je_draft_run = source.get("write_off_je_draft_run")
    doc.write_off_draft_run = source.get("write_off_draft_run")
    doc.write_off_preparation_run = source.get("write_off_preparation_run")
    doc.variance_rejection_review_run = source.get("variance_rejection_review_run")
    doc.remittance_import_finalisation_run = source.get("remittance_import_finalisation_run")
    doc.payment_entry_submission_run = source.get("payment_entry_submission_run")
    doc.payment_entry_draft_run = source.get("payment_entry_draft_run")
    doc.payment_allocation_preparation_run = source.get("payment_allocation_preparation_run")
    doc.remittance_matching_review_run = source.get("remittance_matching_review_run")
    doc.actual_remittance_import_run = source.get("actual_remittance_import_run")
    doc.remittance_import_preparation_run = source.get("remittance_import_preparation_run")
    doc.claim_lodgement_confirmation_run = source.get("claim_lodgement_confirmation_run")
    doc.claim_export_preparation_run = source.get("claim_export_preparation_run")
    doc.claim_batch_submission_run = source.get("claim_batch_submission_run")
    doc.claim_batch_draft_run = source.get("claim_batch_draft_run")
    doc.sales_invoice_submission_run = source.get("sales_invoice_submission_run")
    doc.sales_invoice_draft_run = source.get("sales_invoice_draft_run")
    doc.invoice_draft = source.get("invoice_draft")
    doc.claim_draft = source.get("claim_draft")
    doc.billing_draft = source.get("billing_draft")
    doc.attendance_draft = source.get("attendance_draft")
    doc.downstream_preparation = source.get("downstream_preparation")
    doc.delivery_evidence_review = source.get("delivery_evidence_review")
    doc.service_session_draft = source.get("service_session_draft")
    doc.participant_service_file = source.get("participant_service_file")
    doc.roster_build_request = source.get("roster_build_request")
    doc.service_schedule_draft = source.get("service_schedule_draft")
    doc.operations_setup = source.get("operations_setup")
    doc.finance_onboarding = source.get("finance_onboarding")
    doc.handover = source.get("handover")
    doc.crm_deal = source.get("crm_deal")
    doc.crm_lead = source.get("crm_lead")
    doc.participant_intake = source.get("participant_intake")
    doc.participant_customer = source.get("participant_customer")
    doc.ndis_financial_profile = source.get("ndis_financial_profile")
    doc.participant_name = source.get("participant_name") or source.get("participant_customer") or source.name
    doc.ndis_number = source.get("ndis_number")
    doc.plan_start_date = source.get("plan_start_date")
    doc.plan_end_date = source.get("plan_end_date")
    doc.claim_period_start = source.get("claim_period_start")
    doc.claim_period_end = source.get("claim_period_end")
    doc.company = source.get("company")
    doc.ndis_remittance_import = source.get("ndis_remittance_import")

    doc.recovery_communication_outcome_capture_owner = frappe.session.user
    doc.recovery_communication_dispatch_owner = source.get("recovery_communication_dispatch_owner")

    doc.outcome_capture_completion_allowed = 0
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

    created_count = _generate_lines_from_dispatch_run(doc, source)
    doc.no_recovery_communication_outcome_candidate_found = 1 if created_count == 0 else 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_communication_outcome_capture_run_ready = 1 if summary["recovery_communication_outcome_capture_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
        "name": doc.name,
        "created": True,
        "recovery_communication_outcome_capture_line_count": created_count,
        "no_recovery_communication_outcome_candidate_found": bool(doc.no_recovery_communication_outcome_candidate_found),
        "message": "NDIS CRM Recovery Communication Outcome Capture Run created successfully.",
    }


@frappe.whitelist()
def create_recovery_communication_outcome_capture_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Communication Outcome Capture Run returned.",
        }

    source_run = _get_dispatch_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Recovery Communication Dispatch Run before creating Recovery Communication Outcome Capture Run."))

    return create_recovery_communication_outcome_capture_run_from_dispatch_run(source_run)


@frappe.whitelist()
def generate_recovery_communication_outcome_capture_lines(recovery_communication_outcome_capture_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, recovery_communication_outcome_capture_run)

    if not doc.get("recovery_communication_dispatch_run"):
        frappe.throw(_("Recovery Communication Dispatch Run is required."))

    source = frappe.get_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN, doc.recovery_communication_dispatch_run)
    created_count = _generate_lines_from_dispatch_run(doc, source)

    if created_count == 0 and not doc.get("recovery_communication_outcome_capture_lines"):
        doc.no_recovery_communication_outcome_candidate_found = 1
    else:
        doc.no_recovery_communication_outcome_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Recovery communication outcome capture lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_recovery_communication_outcome_capture_readiness(recovery_communication_outcome_capture_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, recovery_communication_outcome_capture_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Recovery Communication Outcome Capture Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_recovery_communication_outcome_capture(recovery_communication_outcome_capture_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, recovery_communication_outcome_capture_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_communication_outcome_capture_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Outcome Capture. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Outcome Capture"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_communication_outcome_capture_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
        "name": doc.name,
        "message": "Recovery Communication Outcome Capture Run marked Ready.",
    }


@frappe.whitelist()
def approve_recovery_communication_outcome_capture_run(recovery_communication_outcome_capture_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, recovery_communication_outcome_capture_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_communication_outcome_capture_run_ready"]:
        frappe.throw(
            _("Cannot approve Recovery Communication Outcome Capture Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Outcome Capture Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_communication_outcome_capture_run_ready = 1

    doc.outcome_capture_completion_allowed = 0
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

    for row in doc.get("recovery_communication_outcome_capture_lines") or []:
        if row.get("recovery_communication_outcome_capture_line_status") in ["Draft", "Ready"]:
            row.recovery_communication_outcome_capture_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
        "name": doc.name,
        "message": "Recovery Communication Outcome Capture Run approved. No downstream document was created.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("recovery_communication_outcome_capture_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_recovery_communication_outcome_capture"):
            continue

        if not row.get("recovery_communication_outcome_source_ready"):
            continue

        if not row.get("outcome_review_complete"):
            continue

        if not row.get("outcome_recorded"):
            continue

        if not row.get("outcome_authorized"):
            continue

        blocked = any([
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

        if blocked:
            continue

        if row.get("recovery_communication_outcome_hold"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_recovery_communication_outcome_capture(recovery_communication_outcome_capture_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, recovery_communication_outcome_capture_run)

    if doc.status != "Outcome Capture Approved":
        frappe.throw(_("Recovery Communication Outcome Capture Run must be approved before completion."))

    if not doc.get("outcome_capture_completion_allowed"):
        frappe.throw(_("Tick Outcome Capture Completion Allowed before completing outcome capture."))

    blocked_run_fields = [
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
            frappe.throw(_("{0} must remain unticked in Phase 46.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["recovery_communication_outcome_capture_run_ready"]:
        frappe.throw(
            _("Cannot complete recovery communication outcome capture. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines and not doc.get("no_recovery_communication_outcome_candidate_found"):
        frappe.throw(_("No ready recovery communication outcome capture lines found."))

    for row in ready_lines:
        row.recovery_communication_outcome_capture_line_status = "Outcome Captured"
        if not row.get("next_action_recommendation"):
            row.next_action_recommendation = _default_next_action(row.get("outcome_status"))

    doc.status = "Outcomes Captured"
    doc.outcome_capture_completion_allowed = 0
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
        "captured_line_count": len(ready_lines),
        "message": "Recovery communication outcomes captured. No Communication, Email Queue, Event, ToDo, Task, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or Remittance Import was created.",
    }


def validate_recovery_communication_outcome_capture_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN, "recovery_communication_outcome_capture_run_ready"):
        doc.recovery_communication_outcome_capture_run_ready = 1 if summary["recovery_communication_outcome_capture_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["recovery_communication_outcome_capture_run_ready"]:
        frappe.throw(
            _("Cannot set Recovery Communication Outcome Capture Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Outcome Capture Approved" and doc.get("outcome_capture_completion_allowed"):
        frappe.throw(_("Outcome Capture Completion Allowed can only be ticked after the run is approved."))

    blocked_run_fields = [
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
            frappe.throw(_("{0} is not allowed in Phase 46.").format(label))


def on_recovery_communication_outcome_capture_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Recovery Communication Outcome Capture Run Summary Sync Failed"
        )


def validate_crm_deal_phase46(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_recovery_communication_outcome_capture_run_required"):
        required = doc.get("ndis_recovery_communication_outcome_capture_run_required")

    if not required:
        return

    run = doc.get("ndis_recovery_communication_outcome_capture_run") if _field_exists(CRM_DEAL, "ndis_recovery_communication_outcome_capture_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Communication Outcome Capture Run must be created and approved/completed.")
        )

    if not _is_outcome_capture_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Communication Outcome Capture Run must be approved/completed.")
        )


def validate_crm_deal_phase46_combined(doc, method=None):
    """
    Preserve Phase 2-45 validator chain, then add optional Phase 46 Outcome Capture validation.
    """
    try:
        from ndis_crm.phase45_recovery_communication_dispatch import validate_crm_deal_phase45_combined
        validate_crm_deal_phase45_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase44_recovery_communication_draft_creation import validate_crm_deal_phase44_combined
            validate_crm_deal_phase44_combined(doc, method)
        except ImportError:
            pass

    validate_crm_deal_phase46(doc, method)


def phase46_health_check():
    print("---- NDIS CRM Phase 46 Health Check ----")

    for dt in [
        RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_LINE,
        RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
        RECOVERY_COMMUNICATION_DISPATCH_RUN,
        RECOVERY_COMMUNICATION_DISPATCH_LINE,
        RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN,
        RECOVERY_COMMUNICATION_DRAFT_PREPARATION_RUN,
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN,
        RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        RECOVERY_CASE_SUBMISSION_RUN,
        RECOVERY_CASE_DRAFT_RUN,
        RECOVERY_PREPARATION_RUN,
        WRITE_OFF_FINALISATION_RUN,
        WRITE_OFF_JE_SUBMISSION_RUN,
        WRITE_OFF_JE_DRAFT_RUN,
        WRITE_OFF_DRAFT_RUN,
        WRITE_OFF_PREPARATION_RUN,
        VARIANCE_REJECTION_REVIEW_RUN,
        REMITTANCE_IMPORT_FINALISATION_RUN,
        PAYMENT_ENTRY_SUBMISSION_RUN,
        PAYMENT_ENTRY_DRAFT_RUN,
        PAYMENT_ALLOCATION_PREP_RUN,
        REMITTANCE_MATCHING_REVIEW_RUN,
        ACTUAL_REMITTANCE_IMPORT_RUN,
        REMITTANCE_IMPORT_PREP_RUN,
        CLAIM_LODGEMENT_CONFIRMATION_RUN,
        CLAIM_EXPORT_PREP_RUN,
        CLAIM_BATCH_SUBMISSION_RUN,
        CLAIM_BATCH_DRAFT_RUN,
        CLAIM_DRAFT,
        SALES_INVOICE_SUBMISSION_RUN,
        SALES_INVOICE_DRAFT_RUN,
        INVOICE_DRAFT,
        BILLING_DRAFT,
        ATTENDANCE_DRAFT,
        DOWNSTREAM_PREPARATION,
        EVIDENCE_REVIEW,
        SESSION_DRAFT,
        SERVICE_FILE,
        ROSTER_REQUEST,
        SCHEDULE_DRAFT,
        OPERATIONS_SETUP,
        CRM_DEAL,
        HANDOVER,
        FINANCE_ONBOARDING,
        INTAKE,
        SALES_INVOICE,
        PAYMENT_ENTRY,
        JOURNAL_ENTRY,
        GL_ENTRY,
        NDIS_REMITTANCE_IMPORT,
        NDIS_CLAIM_BATCH,
        NDIS_CLAIM_LINE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for dt in [
        COMMUNICATION,
        EMAIL_QUEUE,
        EVENT,
        TODO,
        TASK,
        NDIS_RECOVERY_CASE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_recovery_communication_outcome_capture_run_required",
        "ndis_recovery_communication_outcome_capture_run",
        "recovery_communication_outcome_capture_status",
        "recovery_communication_outcome_capture_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print("NDIS CRM Recovery Communication Outcome Capture Run records:", frappe.db.count(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN) if _doctype_exists(RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN) else 0)
    print("Phase 46 creates CRM outcome capture run/line records only.")
    print("Phase 46 does not create Communication, Email Queue, Event, ToDo, Task, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 46 Health Check ----")
