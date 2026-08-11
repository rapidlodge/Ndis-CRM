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
RECOVERY_FOLLOW_UP_TASK_DRAFT_LINE = "NDIS CRM Recovery Follow Up Task Draft Line"

RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN = "NDIS CRM Recovery Follow Up Task Activation Run"
RECOVERY_FOLLOW_UP_TASK_ACTIVATION_LINE = "NDIS CRM Recovery Follow Up Task Activation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
JOURNAL_ENTRY = "Journal Entry"
GL_ENTRY = "GL Entry"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_RECOVERY_CASE = "NDIS Recovery Case"

TODO = "ToDo"
TASK = "Task"
EVENT = "Event"
COMMUNICATION = "Communication"

READY_STATUSES = [
    "Ready for Follow Up Task Activation",
    "Follow Up Task Activation Run Approved",
    "Follow Up Tasks Activated",
    "Follow Up Tasks Completed",
]

APPROVED_STATUSES = [
    "Follow Up Task Activation Run Approved",
    "Follow Up Tasks Activated",
    "Follow Up Tasks Completed",
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
    user_roles = set(frappe.get_roles())
    if not user_roles.intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this recovery follow-up task activation action."))


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


def _existing_run_for_task_draft_run(recovery_follow_up_task_draft_run):
    if not _doctype_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN):
        return None

    if _field_exists(RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, "ndis_recovery_follow_up_task_activation_run"):
        existing = frappe.db.get_value(
            RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN,
            recovery_follow_up_task_draft_run,
            "ndis_recovery_follow_up_task_activation_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        {"recovery_follow_up_task_draft_run": recovery_follow_up_task_draft_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_recovery_follow_up_task_activation_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_follow_up_task_activation_run")
        if existing:
            return existing

    return frappe.db.get_value(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, {"crm_deal": deal}, "name")


def _get_task_draft_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_recovery_follow_up_task_draft_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_follow_up_task_draft_run")
        if run:
            return run

    if _doctype_exists(RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN):
        return frappe.db.get_value(RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, {"crm_deal": deal}, "name")

    return None


def _is_task_drafts_created(run):
    if not run or not frappe.db.exists(RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN,
        run,
        ["status", "recovery_follow_up_task_draft_run_ready"],
    )

    return status == "Follow Up Task Drafts Created" and bool(ready)


def _is_task_activation_approved(run):
    if not run or not frappe.db.exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        run,
        ["status", "recovery_follow_up_task_activation_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _append_line_if_missing(doc, row_data):
    existing = {
        row.recovery_follow_up_task_activation_source_key
        for row in doc.get("recovery_follow_up_task_activation_lines") or []
        if row.get("recovery_follow_up_task_activation_source_key")
    }

    key = row_data.get("recovery_follow_up_task_activation_source_key")

    if key and key in existing:
        return False

    doc.append("recovery_follow_up_task_activation_lines", row_data)
    return True


def _source_key(row):
    return row.get("recovery_follow_up_task_draft_source_key") or "|".join([
        str(row.get("target_todo") or ""),
        str(row.get("target_task") or ""),
        str(row.get("target_case_name") or ""),
        str(row.get("service_line") or ""),
        str(row.get("task_subject") or ""),
    ])


def _is_task_draft_line_ready(row):
    return row.get("recovery_follow_up_task_draft_line_status") in [
        "CRM Follow Up Task Draft Prepared",
        "ToDo Draft Created",
        "Task Draft Created",
        "ToDo and Task Drafts Created",
    ]


def _target_exists(doctype, name):
    if not doctype or not name:
        return False

    if not _doctype_exists(doctype):
        return False

    return bool(frappe.db.exists(doctype, name))


def _target_status(doctype, name):
    if not _target_exists(doctype, name):
        return None

    if _field_exists(doctype, "status"):
        return frappe.db.get_value(doctype, name, "status")

    return None


def _target_marker_ok(doctype, name, source_run):
    if not _target_exists(doctype, name):
        return False

    if not _field_exists(doctype, "ndis_crm_recovery_follow_up_task_draft_run"):
        return False

    return frappe.db.get_value(doctype, name, "ndis_crm_recovery_follow_up_task_draft_run") == source_run


def _build_activation_line(row, source_doc):
    has_todo = bool(row.get("target_todo"))
    has_task = bool(row.get("target_task"))

    todo_ready = True
    task_ready = True

    if has_todo:
        todo_ready = _target_marker_ok(TODO, row.get("target_todo"), source_doc.name)

    if has_task:
        task_ready = _target_marker_ok(TASK, row.get("target_task"), source_doc.name)

    source_ready = bool(
        source_doc.get("status") == "Follow Up Task Drafts Created"
        and _is_task_draft_line_ready(row)
        and row.get("recovery_follow_up_task_draft_source_ready")
        and row.get("task_draft_review_complete")
        and row.get("task_draft_authorized")
        and row.get("line_ready_for_recovery_follow_up_task_draft")
        and not row.get("todo_activation_authorized")
        and not row.get("task_activation_authorized")
        and not row.get("event_creation_authorized")
        and not row.get("email_creation_authorized")
        and not row.get("journal_entry_authorized")
        and not row.get("manual_gl_authorized")
        and not row.get("payment_entry_authorized")
        and not row.get("sales_invoice_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("bank_reconciliation_authorized")
        and not row.get("recovery_follow_up_task_draft_hold")
        and _to_float(row.get("proposed_recovery_amount")) > 0
        and todo_ready
        and task_ready
    )

    return {
        "recovery_follow_up_task_activation_source_key": _source_key(row),

        "target_task_mode_snapshot": row.get("target_task_mode_snapshot"),
        "target_todo": row.get("target_todo"),
        "target_todo_status": _target_status(TODO, row.get("target_todo")) if has_todo else None,
        "target_task": row.get("target_task"),
        "target_task_status": _target_status(TASK, row.get("target_task")) if has_task else row.get("target_task_status"),

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

        "follow_up_action_type": row.get("follow_up_action_type"),
        "follow_up_priority": row.get("follow_up_priority") or "Normal",
        "follow_up_owner": row.get("follow_up_owner") or frappe.session.user,
        "follow_up_due_date": row.get("follow_up_due_date"),
        "follow_up_channel": row.get("follow_up_channel"),
        "follow_up_instruction": row.get("follow_up_instruction"),
        "follow_up_message_draft": row.get("follow_up_message_draft"),
        "task_subject": row.get("task_subject"),
        "task_description": row.get("task_description"),
        "task_reference_doctype": row.get("task_reference_doctype"),
        "task_reference_name": row.get("task_reference_name"),

        "recovery_follow_up_task_activation_source_ready": 1 if source_ready else 0,
        "task_activation_review_complete": 0,
        "task_activation_authorized": 0,
        "task_completion_authorized": 0,

        "event_creation_authorized": 0,
        "email_creation_authorized": 0,
        "journal_entry_authorized": 0,
        "manual_gl_authorized": 0,
        "payment_entry_authorized": 0,
        "sales_invoice_authorized": 0,
        "adjustment_authorized": 0,
        "bank_reconciliation_authorized": 0,

        "recovery_follow_up_task_activation_hold": 0 if source_ready else 1,
        "recovery_follow_up_task_activation_hold_reason": None if source_ready else "Phase 41 task draft source is not ready or external target marker is missing.",
        "line_ready_for_recovery_follow_up_task_activation": 0,
        "recovery_follow_up_task_activation_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_task_draft_run(doc, source):
    created = 0

    for row in source.get("recovery_follow_up_task_draft_lines") or []:
        if not _is_task_draft_line_ready(row):
            continue

        if _to_float(row.get("proposed_recovery_amount")) <= 0:
            continue

        data = _build_activation_line(row, source)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _active_lines(doc):
    return [
        row for row in doc.get("recovery_follow_up_task_activation_lines") or []
        if _to_float(row.get("proposed_recovery_amount")) > 0
    ]


def _calculate_totals(doc):
    line_count = len(doc.get("recovery_follow_up_task_activation_lines") or [])
    amount_total = 0
    ready_count = 0
    hold_count = 0
    crm_activated_count = 0
    todo_activated_count = 0
    task_activated_count = 0
    todo_completed_count = 0
    task_completed_count = 0

    blocked_event_count = 0
    blocked_email_count = 0
    blocked_je_count = 0
    blocked_gl_count = 0
    blocked_pe_count = 0
    blocked_si_count = 0
    blocked_adjustment_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("recovery_follow_up_task_activation_lines") or []:
        amount_total += _to_float(row.get("proposed_recovery_amount"))

        if row.get("line_ready_for_recovery_follow_up_task_activation"):
            ready_count += 1

        if row.get("recovery_follow_up_task_activation_hold"):
            hold_count += 1

        status = row.get("recovery_follow_up_task_activation_line_status")
        if status == "CRM Task Activated":
            crm_activated_count += 1
        elif status == "ToDo Activated":
            todo_activated_count += 1
        elif status == "Task Activated":
            task_activated_count += 1
        elif status == "ToDo and Task Activated":
            todo_activated_count += 1
            task_activated_count += 1
        elif status == "ToDo Completed":
            todo_completed_count += 1
        elif status == "Task Completed":
            task_completed_count += 1
        elif status == "ToDo and Task Completed":
            todo_completed_count += 1
            task_completed_count += 1

        if row.get("event_creation_authorized"):
            blocked_event_count += 1
        if row.get("email_creation_authorized"):
            blocked_email_count += 1
        if row.get("journal_entry_authorized"):
            blocked_je_count += 1
        if row.get("manual_gl_authorized"):
            blocked_gl_count += 1
        if row.get("payment_entry_authorized"):
            blocked_pe_count += 1
        if row.get("sales_invoice_authorized"):
            blocked_si_count += 1
        if row.get("adjustment_authorized"):
            blocked_adjustment_count += 1
        if row.get("bank_reconciliation_authorized"):
            blocked_bank_rec_count += 1

    return {
        "recovery_follow_up_task_activation_line_count": line_count,
        "recovery_follow_up_task_activation_amount_total": round(amount_total, 2),
        "recovery_follow_up_task_activation_ready_count": ready_count,
        "recovery_follow_up_task_activation_hold_count": hold_count,
        "crm_task_activated_count": crm_activated_count,
        "todo_activated_count": todo_activated_count,
        "task_activated_count": task_activated_count,
        "todo_completed_count": todo_completed_count,
        "task_completed_count": task_completed_count,
        "blocked_event_count": blocked_event_count,
        "blocked_email_count": blocked_email_count,
        "blocked_journal_entry_count": blocked_je_count,
        "blocked_manual_gl_count": blocked_gl_count,
        "blocked_payment_entry_count": blocked_pe_count,
        "blocked_sales_invoice_count": blocked_si_count,
        "blocked_adjustment_count": blocked_adjustment_count,
        "blocked_bank_reconciliation_count": blocked_bank_rec_count,
    }


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Recovery Follow Up Task Draft Run linked",
        "complete": bool(doc.get("recovery_follow_up_task_draft_run")),
    })

    checks.append({
        "label": "Recovery follow-up task drafts created",
        "complete": _is_task_drafts_created(doc.get("recovery_follow_up_task_draft_run")),
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
        "label": "Recovery Follow-Up Task Activation Owner assigned",
        "complete": bool(doc.get("recovery_follow_up_task_activation_owner")),
    })

    lines = _active_lines(doc)
    no_candidates = bool(doc.get("no_follow_up_task_activation_candidate_found"))

    checks.append({
        "label": "Follow-up task activation lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("recovery_follow_up_task_activation_source_ready")]
        checks.append({
            "label": "Follow-up task activation source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        missing_subject = [row.service_line for row in lines if not row.get("task_subject")]
        checks.append({
            "label": "All lines have task subject",
            "complete": not missing_subject,
            "details": missing_subject,
        })

        missing_owner = [row.service_line for row in lines if not row.get("follow_up_owner")]
        checks.append({
            "label": "All lines have follow-up owner",
            "complete": not missing_owner,
            "details": missing_owner,
        })

        review_missing = [row.service_line for row in lines if not row.get("task_activation_review_complete")]
        checks.append({
            "label": "Task activation review complete",
            "complete": not review_missing,
            "details": review_missing,
        })

        activation_missing = [row.service_line for row in lines if not row.get("task_activation_authorized")]
        checks.append({
            "label": "Task activation authorization complete",
            "complete": not activation_missing,
            "details": activation_missing,
        })

        if doc.get("target_task_action_mode") == "Complete Tasks If Authorized":
            completion_missing = [row.service_line for row in lines if not row.get("task_completion_authorized")]
            checks.append({
                "label": "Task completion authorization complete",
                "complete": not completion_missing,
                "details": completion_missing,
            })

        blocked_fields = [
            ("Event creation remains blocked in Phase 42", "event_creation_authorized"),
            ("Email creation remains blocked in Phase 42", "email_creation_authorized"),
            ("Journal Entry authorization remains blocked in Phase 42", "journal_entry_authorized"),
            ("Manual GL authorization remains blocked in Phase 42", "manual_gl_authorized"),
            ("Payment Entry authorization remains blocked in Phase 42", "payment_entry_authorized"),
            ("Sales Invoice authorization remains blocked in Phase 42", "sales_invoice_authorized"),
            ("Adjustment authorization remains blocked in Phase 42", "adjustment_authorized"),
            ("Bank reconciliation authorization remains blocked in Phase 42", "bank_reconciliation_authorized"),
        ]

        for label, fieldname in blocked_fields:
            blocked = [row.service_line for row in lines if row.get(fieldname)]
            checks.append({
                "label": label,
                "complete": not blocked,
                "details": blocked,
            })

        holds = [row.service_line for row in lines if row.get("recovery_follow_up_task_activation_hold")]
        checks.append({
            "label": "No active follow-up task activation hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_recovery_follow_up_task_activation")]
        checks.append({
            "label": "All active lines marked ready for follow-up task activation",
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
        "recovery_follow_up_task_activation_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, "recovery_follow_up_task_activation_run_ready"):
        doc.recovery_follow_up_task_activation_run_ready = 1 if summary["recovery_follow_up_task_activation_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_recovery_follow_up_task_activation_run", doc.name)
        _db_set_if_field(doctype, name, "recovery_follow_up_task_activation_status", doc.status)
        _db_set_if_field(doctype, name, "recovery_follow_up_task_activation_ready", 1 if summary["recovery_follow_up_task_activation_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_recovery_follow_up_task_activation_run_from_task_draft_run(recovery_follow_up_task_draft_run):
    _check_role()

    if not recovery_follow_up_task_draft_run:
        frappe.throw(_("NDIS CRM Recovery Follow Up Task Draft Run is required."))

    if not frappe.db.exists(RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, recovery_follow_up_task_draft_run):
        frappe.throw(_("NDIS CRM Recovery Follow Up Task Draft Run {0} was not found.").format(recovery_follow_up_task_draft_run))

    existing = _existing_run_for_task_draft_run(recovery_follow_up_task_draft_run)
    if existing:
        return {
            "doctype": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Follow Up Task Activation Run returned.",
        }

    source = frappe.get_doc(RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, recovery_follow_up_task_draft_run)

    doc = frappe.new_doc(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN)
    doc.status = "Draft"
    doc.recovery_follow_up_task_draft_run = source.name
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

    doc.recovery_follow_up_task_activation_owner = frappe.session.user
    doc.recovery_follow_up_task_draft_owner = source.get("recovery_follow_up_task_draft_owner")
    doc.target_task_action_mode = "Activate Tasks Only"

    doc.follow_up_task_activation_allowed = 0
    doc.follow_up_task_completion_allowed = 0
    doc.event_creation_allowed = 0
    doc.email_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines_from_task_draft_run(doc, source)
    doc.no_follow_up_task_activation_candidate_found = 1 if created_count == 0 else 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_follow_up_task_activation_run_ready = 1 if summary["recovery_follow_up_task_activation_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        "name": doc.name,
        "created": True,
        "recovery_follow_up_task_activation_line_count": created_count,
        "no_follow_up_task_activation_candidate_found": bool(doc.no_follow_up_task_activation_candidate_found),
        "message": "NDIS CRM Recovery Follow Up Task Activation Run created successfully.",
    }


@frappe.whitelist()
def create_recovery_follow_up_task_activation_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Follow Up Task Activation Run returned.",
        }

    source_run = _get_task_draft_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Recovery Follow Up Task Draft Run before creating Recovery Follow Up Task Activation Run."))

    return create_recovery_follow_up_task_activation_run_from_task_draft_run(source_run)


@frappe.whitelist()
def generate_recovery_follow_up_task_activation_lines(recovery_follow_up_task_activation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, recovery_follow_up_task_activation_run)

    if not doc.get("recovery_follow_up_task_draft_run"):
        frappe.throw(_("Recovery Follow Up Task Draft Run is required."))

    source = frappe.get_doc(RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, doc.recovery_follow_up_task_draft_run)
    created_count = _generate_lines_from_task_draft_run(doc, source)

    if created_count == 0 and not doc.get("recovery_follow_up_task_activation_lines"):
        doc.no_follow_up_task_activation_candidate_found = 1
    else:
        doc.no_follow_up_task_activation_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Recovery follow-up task activation lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_recovery_follow_up_task_activation_readiness(recovery_follow_up_task_activation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, recovery_follow_up_task_activation_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Recovery Follow Up Task Activation Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_recovery_follow_up_task_activation(recovery_follow_up_task_activation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, recovery_follow_up_task_activation_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_follow_up_task_activation_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Follow Up Task Activation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Follow Up Task Activation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_follow_up_task_activation_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        "name": doc.name,
        "message": "Recovery Follow Up Task Activation Run marked Ready.",
    }


@frappe.whitelist()
def approve_recovery_follow_up_task_activation_run(recovery_follow_up_task_activation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, recovery_follow_up_task_activation_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_follow_up_task_activation_run_ready"]:
        frappe.throw(
            _("Cannot approve Recovery Follow Up Task Activation Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Follow Up Task Activation Run Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_follow_up_task_activation_run_ready = 1

    doc.follow_up_task_activation_allowed = 0
    doc.follow_up_task_completion_allowed = 0
    doc.event_creation_allowed = 0
    doc.email_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("recovery_follow_up_task_activation_lines") or []:
        if row.get("recovery_follow_up_task_activation_line_status") in ["Draft", "Ready"]:
            row.recovery_follow_up_task_activation_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        "name": doc.name,
        "message": "Recovery Follow Up Task Activation Run approved. No ToDo/Task was activated or completed yet.",
    }


def _ready_lines_for_activation(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("recovery_follow_up_task_activation_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_recovery_follow_up_task_activation"):
            continue

        if not row.get("recovery_follow_up_task_activation_source_ready"):
            continue

        if not row.get("task_activation_review_complete"):
            continue

        if not row.get("task_activation_authorized"):
            continue

        if doc.get("target_task_action_mode") == "Complete Tasks If Authorized" and not row.get("task_completion_authorized"):
            continue

        blocked = any([
            row.get("event_creation_authorized"),
            row.get("email_creation_authorized"),
            row.get("journal_entry_authorized"),
            row.get("manual_gl_authorized"),
            row.get("payment_entry_authorized"),
            row.get("sales_invoice_authorized"),
            row.get("adjustment_authorized"),
            row.get("bank_reconciliation_authorized"),
        ])

        if blocked:
            continue

        if row.get("recovery_follow_up_task_activation_hold"):
            continue

        ready.append(row)

    return ready


def _activate_external_task(run_doc, row, doctype, name, complete=False):
    if not name:
        return None

    if not _target_marker_ok(doctype, name, run_doc.get("recovery_follow_up_task_draft_run")):
        frappe.throw(_("{0} {1} was not created by the linked Phase 41 task draft run.").format(doctype, name))

    target = frappe.get_doc(doctype, name)

    _set_first_existing(target, ["ndis_crm_recovery_follow_up_task_activation_run"], run_doc.name)
    _set_first_existing(target, ["ndis_crm_recovery_follow_up_task_activation_line"], row.name)
    _set_first_existing(target, ["ndis_crm_activation_blocked"], 0)
    _set_first_existing(target, ["ndis_crm_task_activation_status"], "Activated")

    if complete:
        _set_first_existing(target, ["ndis_crm_completion_blocked"], 0)
        _set_first_existing(target, ["ndis_crm_task_activation_status"], "Completed")

        if doctype == TODO:
            target.status = "Closed"
        elif doctype == TASK:
            target.status = "Completed"
    else:
        _set_first_existing(target, ["ndis_crm_completion_blocked"], 1)

    target.save(ignore_permissions=True)

    return target.get("status")


@frappe.whitelist()
def activate_or_complete_follow_up_tasks(recovery_follow_up_task_activation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, recovery_follow_up_task_activation_run)

    if doc.status != "Follow Up Task Activation Run Approved":
        frappe.throw(_("Recovery Follow Up Task Activation Run must be approved before activation/completion."))

    if not doc.get("follow_up_task_activation_allowed"):
        frappe.throw(_("Tick Follow Up Task Activation Allowed before activating follow-up tasks."))

    complete_mode = doc.get("target_task_action_mode") == "Complete Tasks If Authorized"

    if complete_mode and not doc.get("follow_up_task_completion_allowed"):
        frappe.throw(_("Tick Follow Up Task Completion Allowed before completing follow-up tasks."))

    blocked_run_fields = [
        ("Event Creation Allowed", "event_creation_allowed"),
        ("Email Creation Allowed", "email_creation_allowed"),
        ("Journal Entry Creation Allowed", "journal_entry_creation_allowed"),
        ("Manual GL Creation Allowed", "manual_gl_creation_allowed"),
        ("Payment Entry Creation Allowed", "payment_entry_creation_allowed"),
        ("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed"),
        ("Adjustment Creation Allowed", "adjustment_creation_allowed"),
        ("Bank Reconciliation Allowed", "bank_reconciliation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} must remain unticked in Phase 42.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["recovery_follow_up_task_activation_run_ready"]:
        frappe.throw(
            _("Cannot activate/complete follow-up tasks. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_activation(doc)

    if not ready_lines and not doc.get("no_follow_up_task_activation_candidate_found"):
        frappe.throw(_("No ready recovery follow-up task activation lines found."))

    crm_activated = []
    todo_activated = []
    task_activated = []
    todo_completed = []
    task_completed = []

    for row in ready_lines:
        has_todo = bool(row.get("target_todo"))
        has_task = bool(row.get("target_task"))

        if has_todo:
            todo_status = _activate_external_task(doc, row, TODO, row.get("target_todo"), complete=complete_mode)
            row.target_todo_status = todo_status
            if complete_mode:
                todo_completed.append(row.get("target_todo"))
            else:
                todo_activated.append(row.get("target_todo"))

        if has_task:
            task_status = _activate_external_task(doc, row, TASK, row.get("target_task"), complete=complete_mode)
            row.target_task_status = task_status
            if complete_mode:
                task_completed.append(row.get("target_task"))
            else:
                task_activated.append(row.get("target_task"))

        if not has_todo and not has_task:
            crm_activated.append(row.name)

        if complete_mode:
            if has_todo and has_task:
                row.recovery_follow_up_task_activation_line_status = "ToDo and Task Completed"
            elif has_todo:
                row.recovery_follow_up_task_activation_line_status = "ToDo Completed"
            elif has_task:
                row.recovery_follow_up_task_activation_line_status = "Task Completed"
            else:
                row.recovery_follow_up_task_activation_line_status = "CRM Task Activated"
        else:
            if has_todo and has_task:
                row.recovery_follow_up_task_activation_line_status = "ToDo and Task Activated"
            elif has_todo:
                row.recovery_follow_up_task_activation_line_status = "ToDo Activated"
            elif has_task:
                row.recovery_follow_up_task_activation_line_status = "Task Activated"
            else:
                row.recovery_follow_up_task_activation_line_status = "CRM Task Activated"

    doc.status = "Follow Up Tasks Completed" if complete_mode else "Follow Up Tasks Activated"
    doc.follow_up_task_activation_allowed = 0
    doc.follow_up_task_completion_allowed = 0
    doc.event_creation_allowed = 0
    doc.email_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.activated_by = frappe.session.user
    doc.activated_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "crm_tasks_activated": crm_activated,
        "todo_activated": todo_activated,
        "task_activated": task_activated,
        "todo_completed": todo_completed,
        "task_completed": task_completed,
        "message": "Recovery follow-up tasks activated/completed through controlled Phase 42 gate. No Event, Email/Communication, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or remittance import was created.",
    }


def validate_recovery_follow_up_task_activation_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, "recovery_follow_up_task_activation_run_ready"):
        doc.recovery_follow_up_task_activation_run_ready = 1 if summary["recovery_follow_up_task_activation_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["recovery_follow_up_task_activation_run_ready"]:
        frappe.throw(
            _("Cannot set Recovery Follow Up Task Activation Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Follow Up Task Activation Run Approved" and doc.get("follow_up_task_activation_allowed"):
        frappe.throw(_("Follow Up Task Activation Allowed can only be ticked after the run is approved."))

    if doc.get("follow_up_task_completion_allowed") and not doc.get("follow_up_task_activation_allowed"):
        frappe.throw(_("Follow Up Task Activation Allowed must also be ticked for completion mode."))

    if doc.get("follow_up_task_completion_allowed") and doc.get("target_task_action_mode") != "Complete Tasks If Authorized":
        frappe.throw(_("Follow Up Task Completion Allowed can only be used with Complete Tasks If Authorized mode."))

    blocked_run_fields = [
        ("Event creation", "event_creation_allowed"),
        ("Email creation", "email_creation_allowed"),
        ("Journal Entry creation", "journal_entry_creation_allowed"),
        ("Manual GL creation", "manual_gl_creation_allowed"),
        ("Payment Entry creation", "payment_entry_creation_allowed"),
        ("Sales Invoice creation", "sales_invoice_creation_allowed"),
        ("Adjustment creation", "adjustment_creation_allowed"),
        ("Bank reconciliation", "bank_reconciliation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} is not allowed in Phase 42.").format(label))


def on_recovery_follow_up_task_activation_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Recovery Follow Up Task Activation Run Summary Sync Failed"
        )


def validate_optional_phase42_task_status_guard(doc, method=None):
    """
    Phase 41-created ToDo/Task records may only be completed/closed through an approved Phase 42 gate.
    """
    has_phase41_marker = bool(
        _field_exists(doc.doctype, "ndis_crm_recovery_follow_up_task_draft_run")
        and doc.get("ndis_crm_recovery_follow_up_task_draft_run")
    )

    if not has_phase41_marker:
        return

    status = doc.get("status")
    closing_statuses = ["Closed", "Completed", "Cancelled"]

    if status not in closing_statuses:
        return

    has_phase42_marker = bool(
        _field_exists(doc.doctype, "ndis_crm_recovery_follow_up_task_activation_run")
        and doc.get("ndis_crm_recovery_follow_up_task_activation_run")
    )

    if not has_phase42_marker:
        frappe.throw(_("This follow-up task was created by Phase 41. It can only be completed/closed through the controlled Phase 42 gate."))

    run = doc.get("ndis_crm_recovery_follow_up_task_activation_run")

    if not frappe.db.exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN, run):
        frappe.throw(_("Linked Recovery Follow Up Task Activation Run {0} was not found.").format(run))

    run_status, ready, activation_allowed, completion_allowed, mode = frappe.db.get_value(
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        run,
        [
            "status",
            "recovery_follow_up_task_activation_run_ready",
            "follow_up_task_activation_allowed",
            "follow_up_task_completion_allowed",
            "target_task_action_mode",
        ],
    )

    if (
        run_status != "Follow Up Task Activation Run Approved"
        or not ready
        or not activation_allowed
        or not completion_allowed
        or mode != "Complete Tasks If Authorized"
    ):
        frappe.throw(_("This follow-up task can only be completed while the linked Phase 42 run is approved, ready, completion-mode, and explicitly allowed."))


def validate_crm_deal_phase42(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_recovery_follow_up_task_activation_run_required"):
        required = doc.get("ndis_recovery_follow_up_task_activation_run_required")

    if not required:
        return

    run = doc.get("ndis_recovery_follow_up_task_activation_run") if _field_exists(CRM_DEAL, "ndis_recovery_follow_up_task_activation_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Follow Up Task Activation Run must be created and approved/completed.")
        )

    if not _is_task_activation_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Follow Up Task Activation Run must be approved/completed.")
        )


def validate_crm_deal_phase42_combined(doc, method=None):
    """
    Preserve Phase 2-41 validator chain, then add optional Phase 42 Recovery Follow-Up Task Activation validation.
    """
    try:
        from ndis_crm.phase41_recovery_follow_up_task_draft import validate_crm_deal_phase41_combined
        validate_crm_deal_phase41_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase40_recovery_follow_up_preparation import validate_crm_deal_phase40_combined
            validate_crm_deal_phase40_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase39_recovery_case_submission import validate_crm_deal_phase39_combined
                validate_crm_deal_phase39_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase42(doc, method)


def phase42_health_check():
    print("---- NDIS CRM Phase 42 Health Check ----")

    for dt in [
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_LINE,
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN,
        RECOVERY_FOLLOW_UP_TASK_DRAFT_LINE,
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
        TODO,
        TASK,
        EVENT,
        COMMUNICATION,
        NDIS_RECOVERY_CASE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_recovery_follow_up_task_activation_run_required",
        "ndis_recovery_follow_up_task_activation_run",
        "recovery_follow_up_task_activation_status",
        "recovery_follow_up_task_activation_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    for dt in [TODO, TASK]:
        if _doctype_exists(dt):
            for field in [
                "ndis_crm_recovery_follow_up_task_draft_run",
                "ndis_crm_recovery_follow_up_task_activation_run",
                "ndis_crm_recovery_follow_up_task_activation_line",
                "ndis_crm_task_activation_status",
                "ndis_crm_activation_blocked",
                "ndis_crm_completion_blocked",
            ]:
                print(f"{dt} field {field}: {'OK' if _field_exists(dt, field) else 'MISSING'}")

    print("NDIS CRM Recovery Follow Up Task Activation Run records:", frappe.db.count(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN) if _doctype_exists(RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN) else 0)
    print("Phase 42 creates CRM recovery follow-up task activation records only.")
    print("Phase 42 may update existing Phase 41 ToDo/Task status through explicit gate.")
    print("Phase 42 does not create ToDo, Task, Event, Communication, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 42 Health Check ----")
