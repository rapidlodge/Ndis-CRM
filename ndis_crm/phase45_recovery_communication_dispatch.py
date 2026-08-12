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
RECOVERY_COMMUNICATION_DRAFT_CREATION_LINE = "NDIS CRM Recovery Communication Draft Creation Line"

RECOVERY_COMMUNICATION_DISPATCH_RUN = "NDIS CRM Recovery Communication Dispatch Run"
RECOVERY_COMMUNICATION_DISPATCH_LINE = "NDIS CRM Recovery Communication Dispatch Line"

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
    "Ready for Communication Dispatch",
    "Communication Dispatch Approved",
    "Communication Dispatch Completed",
]

APPROVED_STATUSES = [
    "Communication Dispatch Approved",
    "Communication Dispatch Completed",
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
        frappe.throw(_("You do not have permission to perform this recovery communication dispatch action."))


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


def _set_if_field(doc, fieldname, value):
    if value is not None and _field_exists(doc.doctype, fieldname):
        doc.set(fieldname, value)
        return True
    return False


def _set_first_existing(doc, fieldnames, value):
    for fieldname in fieldnames:
        if _set_if_field(doc, fieldname, value):
            return fieldname
    return None


def _to_float(value):
    if value in [None, ""]:
        return 0
    try:
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").strip()
        return float(value)
    except Exception:
        return 0


def _safe_sender():
    return frappe.db.get_value("User", frappe.session.user, "email") or frappe.session.user


def _existing_run_for_draft_creation_run(recovery_communication_draft_creation_run):
    if not _doctype_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN):
        return None

    if _field_exists(RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN, "ndis_recovery_communication_dispatch_run"):
        existing = frappe.db.get_value(
            RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN,
            recovery_communication_draft_creation_run,
            "ndis_recovery_communication_dispatch_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        RECOVERY_COMMUNICATION_DISPATCH_RUN,
        {"recovery_communication_draft_creation_run": recovery_communication_draft_creation_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_recovery_communication_dispatch_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_communication_dispatch_run")
        if existing:
            return existing

    return frappe.db.get_value(RECOVERY_COMMUNICATION_DISPATCH_RUN, {"crm_deal": deal}, "name")


def _get_draft_creation_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_recovery_communication_draft_creation_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_communication_draft_creation_run")
        if run:
            return run

    return frappe.db.get_value(RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN, {"crm_deal": deal}, "name")


def _is_draft_creation_done(run):
    if not run or not frappe.db.exists(RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN,
        run,
        ["status", "recovery_communication_draft_creation_run_ready"],
    )

    return status == "Communication Draft Records Created" and bool(ready)


def _is_dispatch_approved(run):
    if not run or not frappe.db.exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_COMMUNICATION_DISPATCH_RUN,
        run,
        ["status", "recovery_communication_dispatch_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _append_line_if_missing(doc, row_data):
    existing = {
        row.recovery_communication_dispatch_source_key
        for row in doc.get("recovery_communication_dispatch_lines") or []
        if row.get("recovery_communication_dispatch_source_key")
    }

    key = row_data.get("recovery_communication_dispatch_source_key")

    if key and key in existing:
        return False

    doc.append("recovery_communication_dispatch_lines", row_data)
    return True


def _source_key(row):
    return row.get("recovery_communication_draft_creation_source_key") or "|".join([
        str(row.get("target_communication") or ""),
        str(row.get("target_todo") or ""),
        str(row.get("target_task") or ""),
        str(row.get("service_line") or ""),
        str(row.get("draft_subject") or ""),
    ])


def _is_creation_line_done(row):
    return row.get("recovery_communication_draft_creation_line_status") in [
        "CRM Communication Draft Prepared",
        "Communication Draft Record Created",
    ]


def _communication_marker_ok(name, draft_creation_run):
    if not name:
        return False

    if not _doctype_exists(COMMUNICATION) or not frappe.db.exists(COMMUNICATION, name):
        return False

    if not _field_exists(COMMUNICATION, "ndis_crm_recovery_communication_draft_creation_run"):
        return False

    return frappe.db.get_value(COMMUNICATION, name, "ndis_crm_recovery_communication_draft_creation_run") == draft_creation_run


def _build_dispatch_line(row, source_doc):
    has_communication = bool(row.get("target_communication"))
    communication_ready = True

    if has_communication:
        communication_ready = _communication_marker_ok(row.get("target_communication"), source_doc.name)

    source_ready = bool(
        source_doc.get("status") == "Communication Draft Records Created"
        and _is_creation_line_done(row)
        and row.get("recovery_communication_draft_creation_source_ready")
        and row.get("communication_record_review_complete")
        and row.get("communication_record_authorized")
        and row.get("line_ready_for_recovery_communication_draft_creation")
        and not row.get("communication_send_authorized")
        and not row.get("email_queue_authorized")
        and not row.get("event_creation_authorized")
        and not row.get("todo_creation_authorized")
        and not row.get("task_creation_authorized")
        and not row.get("journal_entry_authorized")
        and not row.get("manual_gl_authorized")
        and not row.get("payment_entry_authorized")
        and not row.get("sales_invoice_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("bank_reconciliation_authorized")
        and not row.get("recovery_communication_draft_creation_hold")
        and row.get("draft_subject")
        and row.get("draft_body")
        and _to_float(row.get("proposed_recovery_amount")) > 0
        and communication_ready
    )

    return {
        "recovery_communication_dispatch_source_key": _source_key(row),

        "target_dispatch_mode_snapshot": None,
        "target_communication": row.get("target_communication"),
        "target_communication_status": row.get("target_communication_status"),
        "target_email_queue_status": None,
        "dispatch_reference": None,

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

        "recovery_communication_dispatch_source_ready": 1 if source_ready else 0,
        "dispatch_review_complete": 0,
        "recipient_details_verified": 0,
        "dispatch_authorized": 0,

        "communication_send_authorized": 0,
        "email_queue_authorized": 0,
        "mark_communication_sent_authorized": 0,

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

        "recovery_communication_dispatch_hold": 0 if source_ready else 1,
        "recovery_communication_dispatch_hold_reason": None if source_ready else "Phase 44 communication draft creation source is not ready for dispatch.",
        "line_ready_for_recovery_communication_dispatch": 0,
        "recovery_communication_dispatch_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_draft_creation_run(doc, source):
    created = 0

    for row in source.get("recovery_communication_draft_creation_lines") or []:
        if not _is_creation_line_done(row):
            continue

        if _to_float(row.get("proposed_recovery_amount")) <= 0:
            continue

        if _append_line_if_missing(doc, _build_dispatch_line(row, source)):
            created += 1

    return created


def _active_lines(doc):
    return [
        row for row in doc.get("recovery_communication_dispatch_lines") or []
        if _to_float(row.get("proposed_recovery_amount")) > 0
    ]


def _calculate_totals(doc):
    totals = {
        "recovery_communication_dispatch_line_count": 0,
        "recovery_communication_dispatch_amount_total": 0,
        "recovery_communication_dispatch_ready_count": 0,
        "recovery_communication_dispatch_hold_count": 0,
        "dispatch_log_only_count": 0,
        "communication_marked_sent_count": 0,
        "email_dispatch_requested_count": 0,
        "communication_dispatch_completed_count": 0,
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
    }

    for row in doc.get("recovery_communication_dispatch_lines") or []:
        totals["recovery_communication_dispatch_line_count"] += 1
        totals["recovery_communication_dispatch_amount_total"] += _to_float(row.get("proposed_recovery_amount"))

        if row.get("line_ready_for_recovery_communication_dispatch"):
            totals["recovery_communication_dispatch_ready_count"] += 1

        if row.get("recovery_communication_dispatch_hold"):
            totals["recovery_communication_dispatch_hold_count"] += 1

        status = row.get("recovery_communication_dispatch_line_status")
        if status == "Dispatch Logged":
            totals["dispatch_log_only_count"] += 1
            totals["communication_dispatch_completed_count"] += 1
        elif status == "Communication Marked Sent":
            totals["communication_marked_sent_count"] += 1
            totals["communication_dispatch_completed_count"] += 1
        elif status == "Email Dispatch Requested":
            totals["email_dispatch_requested_count"] += 1
            totals["communication_dispatch_completed_count"] += 1

        if row.get("event_creation_authorized"):
            totals["blocked_event_count"] += 1
        if row.get("todo_creation_authorized"):
            totals["blocked_todo_count"] += 1
        if row.get("task_creation_authorized"):
            totals["blocked_task_count"] += 1
        if row.get("recovery_case_creation_authorized"):
            totals["blocked_recovery_case_count"] += 1
        if row.get("journal_entry_authorized"):
            totals["blocked_journal_entry_count"] += 1
        if row.get("manual_gl_authorized"):
            totals["blocked_manual_gl_count"] += 1
        if row.get("payment_entry_authorized"):
            totals["blocked_payment_entry_count"] += 1
        if row.get("sales_invoice_authorized"):
            totals["blocked_sales_invoice_count"] += 1
        if row.get("adjustment_authorized"):
            totals["blocked_adjustment_count"] += 1
        if row.get("bank_reconciliation_authorized"):
            totals["blocked_bank_reconciliation_count"] += 1

    totals["recovery_communication_dispatch_amount_total"] = round(
        totals["recovery_communication_dispatch_amount_total"],
        2,
    )

    return totals


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Recovery Communication Draft Creation Run linked",
        "complete": bool(doc.get("recovery_communication_draft_creation_run")),
    })

    checks.append({
        "label": "Recovery communication draft records created",
        "complete": _is_draft_creation_done(doc.get("recovery_communication_draft_creation_run")),
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
        "label": "Recovery Communication Dispatch Owner assigned",
        "complete": bool(doc.get("recovery_communication_dispatch_owner")),
    })

    mode = doc.get("target_dispatch_mode") or "Dispatch Log Only"

    if mode == "Mark Existing Communication Sent":
        checks.append({
            "label": "Communication DocType exists for mark-sent mode",
            "complete": _doctype_exists(COMMUNICATION),
        })

    if mode == "Send Email From Draft Content":
        checks.append({
            "label": "Email Queue DocType exists for email dispatch mode",
            "complete": _doctype_exists(EMAIL_QUEUE),
        })

    lines = _active_lines(doc)
    no_candidates = bool(doc.get("no_recovery_communication_dispatch_candidate_found"))

    checks.append({
        "label": "Communication dispatch lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("recovery_communication_dispatch_source_ready")]
        checks.append({
            "label": "Communication dispatch source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        missing_subject = [row.service_line for row in lines if not row.get("draft_subject")]
        checks.append({
            "label": "All lines have subject",
            "complete": not missing_subject,
            "details": missing_subject,
        })

        missing_body = [row.service_line for row in lines if not row.get("draft_body")]
        checks.append({
            "label": "All lines have body",
            "complete": not missing_body,
            "details": missing_body,
        })

        missing_owner = [row.service_line for row in lines if not row.get("communication_owner")]
        checks.append({
            "label": "All lines have communication owner",
            "complete": not missing_owner,
            "details": missing_owner,
        })

        review_missing = [row.service_line for row in lines if not row.get("dispatch_review_complete")]
        checks.append({
            "label": "Dispatch review complete",
            "complete": not review_missing,
            "details": review_missing,
        })

        recipient_missing = [row.service_line for row in lines if not row.get("recipient_details_verified")]
        checks.append({
            "label": "Recipient details verified",
            "complete": not recipient_missing,
            "details": recipient_missing,
        })

        auth_missing = [row.service_line for row in lines if not row.get("dispatch_authorized")]
        checks.append({
            "label": "Dispatch authorized",
            "complete": not auth_missing,
            "details": auth_missing,
        })

        if mode == "Mark Existing Communication Sent":
            missing_comm = [row.service_line for row in lines if not row.get("target_communication")]
            checks.append({
                "label": "Existing Phase 44 Communication linked for mark-sent mode",
                "complete": not missing_comm,
                "details": missing_comm,
            })

            missing_mark = [row.service_line for row in lines if not row.get("mark_communication_sent_authorized")]
            checks.append({
                "label": "Mark Communication Sent authorized",
                "complete": not missing_mark,
                "details": missing_mark,
            })

        if mode == "Send Email From Draft Content":
            missing_recipient_email = [row.service_line for row in lines if not row.get("recipient_email")]
            checks.append({
                "label": "Recipient email present for email dispatch",
                "complete": not missing_recipient_email,
                "details": missing_recipient_email,
            })

            missing_email_auth = [row.service_line for row in lines if not row.get("communication_send_authorized")]
            checks.append({
                "label": "Email send authorized on all lines",
                "complete": not missing_email_auth,
                "details": missing_email_auth,
            })

            missing_queue_auth = [row.service_line for row in lines if not row.get("email_queue_authorized")]
            checks.append({
                "label": "Email Queue authorized on all lines",
                "complete": not missing_queue_auth,
                "details": missing_queue_auth,
            })

        blocked_fields = [
            ("Event creation remains blocked in Phase 45", "event_creation_authorized"),
            ("ToDo creation remains blocked in Phase 45", "todo_creation_authorized"),
            ("Task creation remains blocked in Phase 45", "task_creation_authorized"),
            ("Recovery Case creation remains blocked in Phase 45", "recovery_case_creation_authorized"),
            ("Journal Entry authorization remains blocked in Phase 45", "journal_entry_authorized"),
            ("Manual GL authorization remains blocked in Phase 45", "manual_gl_authorized"),
            ("Payment Entry authorization remains blocked in Phase 45", "payment_entry_authorized"),
            ("Sales Invoice authorization remains blocked in Phase 45", "sales_invoice_authorized"),
            ("Adjustment authorization remains blocked in Phase 45", "adjustment_authorized"),
            ("Bank reconciliation authorization remains blocked in Phase 45", "bank_reconciliation_authorized"),
        ]

        for label, fieldname in blocked_fields:
            blocked = [row.service_line for row in lines if row.get(fieldname)]
            checks.append({
                "label": label,
                "complete": not blocked,
                "details": blocked,
            })

        holds = [row.service_line for row in lines if row.get("recovery_communication_dispatch_hold")]
        checks.append({
            "label": "No active dispatch hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_recovery_communication_dispatch")]
        checks.append({
            "label": "All active lines marked ready for communication dispatch",
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
        "recovery_communication_dispatch_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, "recovery_communication_dispatch_run_ready"):
        doc.recovery_communication_dispatch_run_ready = 1 if summary["recovery_communication_dispatch_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_recovery_communication_dispatch_run", doc.name)
        _db_set_if_field(doctype, name, "recovery_communication_dispatch_status", doc.status)
        _db_set_if_field(doctype, name, "recovery_communication_dispatch_ready", 1 if summary["recovery_communication_dispatch_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_recovery_communication_dispatch_run_from_draft_creation_run(recovery_communication_draft_creation_run):
    _check_role()

    if not recovery_communication_draft_creation_run:
        frappe.throw(_("NDIS CRM Recovery Communication Draft Creation Run is required."))

    if not frappe.db.exists(RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN, recovery_communication_draft_creation_run):
        frappe.throw(_("NDIS CRM Recovery Communication Draft Creation Run {0} was not found.").format(recovery_communication_draft_creation_run))

    existing = _existing_run_for_draft_creation_run(recovery_communication_draft_creation_run)
    if existing:
        return {
            "doctype": RECOVERY_COMMUNICATION_DISPATCH_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Communication Dispatch Run returned.",
        }

    source = frappe.get_doc(RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN, recovery_communication_draft_creation_run)

    doc = frappe.new_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN)
    doc.status = "Draft"
    doc.recovery_communication_draft_creation_run = source.name
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

    doc.recovery_communication_dispatch_owner = frappe.session.user
    doc.recovery_communication_draft_creation_owner = source.get("recovery_communication_draft_creation_owner")
    doc.target_dispatch_mode = "Dispatch Log Only"

    doc.communication_dispatch_allowed = 0
    doc.communication_send_allowed = 0
    doc.email_queue_allowed = 0
    doc.mark_communication_sent_allowed = 0
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

    created_count = _generate_lines_from_draft_creation_run(doc, source)
    doc.no_recovery_communication_dispatch_candidate_found = 1 if created_count == 0 else 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_communication_dispatch_run_ready = 1 if summary["recovery_communication_dispatch_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_COMMUNICATION_DISPATCH_RUN,
        "name": doc.name,
        "created": True,
        "recovery_communication_dispatch_line_count": created_count,
        "no_recovery_communication_dispatch_candidate_found": bool(doc.no_recovery_communication_dispatch_candidate_found),
        "message": "NDIS CRM Recovery Communication Dispatch Run created successfully.",
    }


@frappe.whitelist()
def create_recovery_communication_dispatch_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": RECOVERY_COMMUNICATION_DISPATCH_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Communication Dispatch Run returned.",
        }

    source_run = _get_draft_creation_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Recovery Communication Draft Creation Run before creating Recovery Communication Dispatch Run."))

    return create_recovery_communication_dispatch_run_from_draft_creation_run(source_run)


@frappe.whitelist()
def generate_recovery_communication_dispatch_lines(recovery_communication_dispatch_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN, recovery_communication_dispatch_run)

    if not doc.get("recovery_communication_draft_creation_run"):
        frappe.throw(_("Recovery Communication Draft Creation Run is required."))

    source = frappe.get_doc(RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN, doc.recovery_communication_draft_creation_run)
    created_count = _generate_lines_from_draft_creation_run(doc, source)

    if created_count == 0 and not doc.get("recovery_communication_dispatch_lines"):
        doc.no_recovery_communication_dispatch_candidate_found = 1
    else:
        doc.no_recovery_communication_dispatch_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Recovery communication dispatch lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_recovery_communication_dispatch_readiness(recovery_communication_dispatch_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN, recovery_communication_dispatch_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Recovery Communication Dispatch Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_recovery_communication_dispatch(recovery_communication_dispatch_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN, recovery_communication_dispatch_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_communication_dispatch_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Communication Dispatch. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Communication Dispatch"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_communication_dispatch_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_COMMUNICATION_DISPATCH_RUN,
        "name": doc.name,
        "message": "Recovery Communication Dispatch Run marked Ready.",
    }


@frappe.whitelist()
def approve_recovery_communication_dispatch_run(recovery_communication_dispatch_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN, recovery_communication_dispatch_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_communication_dispatch_run_ready"]:
        frappe.throw(
            _("Cannot approve Recovery Communication Dispatch Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Communication Dispatch Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_communication_dispatch_run_ready = 1

    doc.communication_dispatch_allowed = 0
    doc.communication_send_allowed = 0
    doc.email_queue_allowed = 0
    doc.mark_communication_sent_allowed = 0
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

    for row in doc.get("recovery_communication_dispatch_lines") or []:
        if row.get("recovery_communication_dispatch_line_status") in ["Draft", "Ready"]:
            row.recovery_communication_dispatch_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_COMMUNICATION_DISPATCH_RUN,
        "name": doc.name,
        "message": "Recovery Communication Dispatch Run approved. No communication has been sent yet.",
    }


def _ready_lines_for_dispatch(doc):
    ready = []
    mode = doc.get("target_dispatch_mode") or "Dispatch Log Only"

    for row in _active_lines(doc):
        if row.get("recovery_communication_dispatch_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_recovery_communication_dispatch"):
            continue

        if not row.get("recovery_communication_dispatch_source_ready"):
            continue

        if not row.get("dispatch_review_complete"):
            continue

        if not row.get("recipient_details_verified"):
            continue

        if not row.get("dispatch_authorized"):
            continue

        if mode == "Mark Existing Communication Sent":
            if not row.get("target_communication"):
                continue
            if not row.get("mark_communication_sent_authorized"):
                continue

        if mode == "Send Email From Draft Content":
            if not row.get("recipient_email"):
                continue
            if not row.get("communication_send_authorized"):
                continue
            if not row.get("email_queue_authorized"):
                continue

        blocked = any([
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
        ])

        if blocked:
            continue

        if row.get("recovery_communication_dispatch_hold"):
            continue

        ready.append(row)

    return ready


def _mark_existing_communication_sent(run_doc, row):
    if not row.get("target_communication"):
        frappe.throw(_("Target Communication is required for mark-sent mode."))

    if not _communication_marker_ok(row.get("target_communication"), run_doc.get("recovery_communication_draft_creation_run")):
        frappe.throw(_("Communication {0} was not created by the linked Phase 44 run.").format(row.get("target_communication")))

    comm = frappe.get_doc(COMMUNICATION, row.get("target_communication"))

    _set_first_existing(comm, ["ndis_crm_recovery_communication_dispatch_run"], run_doc.name)
    _set_first_existing(comm, ["ndis_crm_recovery_communication_dispatch_line"], row.name)
    _set_first_existing(comm, ["ndis_crm_communication_dispatch_status"], "Sent / Dispatched")
    _set_first_existing(comm, ["ndis_crm_send_blocked"], 0)

    if _field_exists(COMMUNICATION, "sent_or_received"):
        comm.sent_or_received = "Sent"

    if _field_exists(COMMUNICATION, "status"):
        comm.status = "Linked"

    comm.save(ignore_permissions=True)
    return comm.name


def _send_email_from_draft(run_doc, row):
    recipient = row.get("recipient_email")
    if not recipient:
        frappe.throw(_("Recipient email is required for email dispatch."))

    subject = row.get("draft_subject")
    message = row.get("draft_body")

    if not subject or not message:
        frappe.throw(_("Draft subject and body are required for email dispatch."))

    reference_doctype = row.get("target_case_doctype") or RECOVERY_COMMUNICATION_DISPATCH_RUN
    reference_name = row.get("target_case_name") or run_doc.name

    frappe.sendmail(
        recipients=[recipient],
        sender=_safe_sender(),
        subject=subject,
        message=message,
        reference_doctype=reference_doctype,
        reference_name=reference_name,
        delayed=False,
    )

    if row.get("target_communication") and _communication_marker_ok(row.get("target_communication"), run_doc.get("recovery_communication_draft_creation_run")):
        comm = frappe.get_doc(COMMUNICATION, row.get("target_communication"))
        _set_first_existing(comm, ["ndis_crm_recovery_communication_dispatch_run"], run_doc.name)
        _set_first_existing(comm, ["ndis_crm_recovery_communication_dispatch_line"], row.name)
        _set_first_existing(comm, ["ndis_crm_communication_dispatch_status"], "Email Dispatch Requested")
        _set_first_existing(comm, ["ndis_crm_send_blocked"], 0)
        _set_first_existing(comm, ["ndis_crm_email_queue_blocked"], 0)
        comm.save(ignore_permissions=True)

    return f"Email dispatch requested to {recipient}"


@frappe.whitelist()
def dispatch_recovery_communications(recovery_communication_dispatch_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_COMMUNICATION_DISPATCH_RUN, recovery_communication_dispatch_run)

    if doc.status != "Communication Dispatch Approved":
        frappe.throw(_("Recovery Communication Dispatch Run must be approved before dispatch."))

    if not doc.get("communication_dispatch_allowed"):
        frappe.throw(_("Tick Communication Dispatch Allowed before dispatch."))

    mode = doc.get("target_dispatch_mode") or "Dispatch Log Only"

    if mode == "Mark Existing Communication Sent" and not doc.get("mark_communication_sent_allowed"):
        frappe.throw(_("Tick Mark Communication Sent Allowed for mark-sent mode."))

    if mode == "Send Email From Draft Content":
        if not doc.get("communication_send_allowed"):
            frappe.throw(_("Tick Communication Send Allowed for email dispatch mode."))
        if not doc.get("email_queue_allowed"):
            frappe.throw(_("Tick Email Queue Allowed for email dispatch mode."))

    blocked_run_fields = [
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
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} must remain unticked in Phase 45.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["recovery_communication_dispatch_run_ready"]:
        frappe.throw(
            _("Cannot dispatch recovery communications. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_dispatch(doc)

    if not ready_lines and not doc.get("no_recovery_communication_dispatch_candidate_found"):
        frappe.throw(_("No ready recovery communication dispatch lines found."))

    dispatch_log_only = []
    communication_marked_sent = []
    email_dispatch_requested = []

    for row in ready_lines:
        row.target_dispatch_mode_snapshot = mode

        if mode == "Dispatch Log Only":
            row.recovery_communication_dispatch_line_status = "Dispatch Logged"
            row.dispatch_reference = "CRM dispatch log only"
            dispatch_log_only.append(row.name)

        elif mode == "Mark Existing Communication Sent":
            comm_name = _mark_existing_communication_sent(doc, row)
            row.target_communication = comm_name
            row.target_communication_status = "Sent / Dispatched"
            row.dispatch_reference = f"Communication marked sent: {comm_name}"
            row.recovery_communication_dispatch_line_status = "Communication Marked Sent"
            communication_marked_sent.append(comm_name)

        elif mode == "Send Email From Draft Content":
            dispatch_reference = _send_email_from_draft(doc, row)
            row.target_email_queue_status = "Dispatch Requested"
            row.dispatch_reference = dispatch_reference
            row.recovery_communication_dispatch_line_status = "Email Dispatch Requested"
            email_dispatch_requested.append(row.get("recipient_email"))

        else:
            frappe.throw(_("Unsupported Target Dispatch Mode: {0}").format(mode))

    doc.status = "Communication Dispatch Completed"
    doc.communication_dispatch_allowed = 0
    doc.communication_send_allowed = 0
    doc.email_queue_allowed = 0
    doc.mark_communication_sent_allowed = 0
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
    doc.dispatched_by = frappe.session.user
    doc.dispatched_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "dispatch_log_only": dispatch_log_only,
        "communication_marked_sent": communication_marked_sent,
        "email_dispatch_requested": email_dispatch_requested,
        "message": "Recovery communication dispatch completed through controlled Phase 45 gate. No Event, ToDo, Task, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or remittance import was created.",
    }


def validate_recovery_communication_dispatch_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, "recovery_communication_dispatch_run_ready"):
        doc.recovery_communication_dispatch_run_ready = 1 if summary["recovery_communication_dispatch_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["recovery_communication_dispatch_run_ready"]:
        frappe.throw(
            _("Cannot set Recovery Communication Dispatch Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Communication Dispatch Approved" and doc.get("communication_dispatch_allowed"):
        frappe.throw(_("Communication Dispatch Allowed can only be ticked after the run is approved."))

    mode = doc.get("target_dispatch_mode")

    if doc.get("communication_send_allowed") and mode != "Send Email From Draft Content":
        frappe.throw(_("Communication Send Allowed can only be used with Send Email From Draft Content mode."))

    if doc.get("email_queue_allowed") and mode != "Send Email From Draft Content":
        frappe.throw(_("Email Queue Allowed can only be used with Send Email From Draft Content mode."))

    if doc.get("mark_communication_sent_allowed") and mode != "Mark Existing Communication Sent":
        frappe.throw(_("Mark Communication Sent Allowed can only be used with Mark Existing Communication Sent mode."))

    blocked_run_fields = [
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
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} is not allowed in Phase 45.").format(label))


def on_recovery_communication_dispatch_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Recovery Communication Dispatch Run Summary Sync Failed"
        )


def validate_optional_phase45_communication_guard(doc, method=None):
    """
    Phase 44-created Communication records can only become sent/dispatched through Phase 45.
    """
    has_phase44_marker = bool(
        _field_exists(doc.doctype, "ndis_crm_recovery_communication_draft_creation_run")
        and doc.get("ndis_crm_recovery_communication_draft_creation_run")
    )

    if not has_phase44_marker:
        return

    if not _field_exists(doc.doctype, "sent_or_received"):
        return

    if doc.get("sent_or_received") != "Sent":
        return

    dispatch_run = None
    if _field_exists(doc.doctype, "ndis_crm_recovery_communication_dispatch_run"):
        dispatch_run = doc.get("ndis_crm_recovery_communication_dispatch_run")

    if not dispatch_run:
        frappe.throw(_("This Communication was created by Phase 44 and can only be marked Sent through the controlled Phase 45 dispatch gate."))

    if not frappe.db.exists(RECOVERY_COMMUNICATION_DISPATCH_RUN, dispatch_run):
        frappe.throw(_("Linked Recovery Communication Dispatch Run {0} was not found.").format(dispatch_run))

    run_status, ready, dispatch_allowed, send_allowed, mark_allowed, queue_allowed, mode = frappe.db.get_value(
        RECOVERY_COMMUNICATION_DISPATCH_RUN,
        dispatch_run,
        [
            "status",
            "recovery_communication_dispatch_run_ready",
            "communication_dispatch_allowed",
            "communication_send_allowed",
            "mark_communication_sent_allowed",
            "email_queue_allowed",
            "target_dispatch_mode",
        ],
    )

    if run_status != "Communication Dispatch Approved" or not ready or not dispatch_allowed:
        frappe.throw(_("This Communication can only be marked Sent while the linked Phase 45 run is approved, ready, and explicitly dispatch-allowed."))

    if mode == "Mark Existing Communication Sent" and not mark_allowed:
        frappe.throw(_("Mark Communication Sent Allowed must be ticked on the linked Phase 45 run."))

    if mode == "Send Email From Draft Content" and not (send_allowed and queue_allowed):
        frappe.throw(_("Communication Send Allowed and Email Queue Allowed must be ticked on the linked Phase 45 run."))


def validate_crm_deal_phase45(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_recovery_communication_dispatch_run_required"):
        required = doc.get("ndis_recovery_communication_dispatch_run_required")

    if not required:
        return

    run = doc.get("ndis_recovery_communication_dispatch_run") if _field_exists(CRM_DEAL, "ndis_recovery_communication_dispatch_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Communication Dispatch Run must be created and approved/completed.")
        )

    if not _is_dispatch_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Communication Dispatch Run must be approved/completed.")
        )


def validate_crm_deal_phase45_combined(doc, method=None):
    """
    Preserve Phase 2-44 validator chain, then add optional Phase 45 Recovery Communication Dispatch validation.
    """
    try:
        from ndis_crm.phase44_recovery_communication_draft_creation import validate_crm_deal_phase44_combined
        validate_crm_deal_phase44_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase43_recovery_communication_draft_preparation import validate_crm_deal_phase43_combined
            validate_crm_deal_phase43_combined(doc, method)
        except ImportError:
            pass

    validate_crm_deal_phase45(doc, method)


def phase45_health_check():
    print("---- NDIS CRM Phase 45 Health Check ----")

    for dt in [
        RECOVERY_COMMUNICATION_DISPATCH_LINE,
        RECOVERY_COMMUNICATION_DISPATCH_RUN,
        RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN,
        RECOVERY_COMMUNICATION_DRAFT_CREATION_LINE,
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
        "ndis_recovery_communication_dispatch_run_required",
        "ndis_recovery_communication_dispatch_run",
        "recovery_communication_dispatch_status",
        "recovery_communication_dispatch_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    if _doctype_exists(COMMUNICATION):
        for field in [
            "ndis_crm_recovery_communication_dispatch_run",
            "ndis_crm_recovery_communication_dispatch_line",
            "ndis_crm_communication_dispatch_status",
        ]:
            print(f"Communication field {field}: {'OK' if _field_exists(COMMUNICATION, field) else 'MISSING'}")

    print("NDIS CRM Recovery Communication Dispatch Run records:", frappe.db.count(RECOVERY_COMMUNICATION_DISPATCH_RUN) if _doctype_exists(RECOVERY_COMMUNICATION_DISPATCH_RUN) else 0)
    print("Phase 45 creates CRM dispatch run/line records only.")
    print("Phase 45 can mark existing Phase 44 Communication records sent or request email dispatch only through explicit gate.")
    print("Phase 45 does not create Event, ToDo, Task, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 45 Health Check ----")
