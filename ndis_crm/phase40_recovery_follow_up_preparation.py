import frappe
from frappe import _
from frappe.utils import now, add_days, getdate


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
RECOVERY_CASE_SUBMISSION_LINE = "NDIS CRM Recovery Case Submission Line"

RECOVERY_FOLLOW_UP_PREPARATION_RUN = "NDIS CRM Recovery Follow Up Preparation Run"
RECOVERY_FOLLOW_UP_PREPARATION_LINE = "NDIS CRM Recovery Follow Up Preparation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
JOURNAL_ENTRY = "Journal Entry"
GL_ENTRY = "GL Entry"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_RECOVERY_CASE = "NDIS Recovery Case"

READY_STATUSES = [
    "Ready for Recovery Follow Up Preparation",
    "Recovery Follow Up Preparation Approved",
    "Recovery Follow Up Prepared",
]

APPROVED_STATUSES = [
    "Recovery Follow Up Preparation Approved",
    "Recovery Follow Up Prepared",
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
        frappe.throw(_("You do not have permission to perform this recovery follow-up preparation action."))


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


def _existing_run_for_submission_run(recovery_case_submission_run):
    if not _doctype_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN):
        return None

    if _field_exists(RECOVERY_CASE_SUBMISSION_RUN, "ndis_recovery_follow_up_preparation_run"):
        existing = frappe.db.get_value(
            RECOVERY_CASE_SUBMISSION_RUN,
            recovery_case_submission_run,
            "ndis_recovery_follow_up_preparation_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        {"recovery_case_submission_run": recovery_case_submission_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_recovery_follow_up_preparation_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_follow_up_preparation_run")
        if existing:
            return existing

    return frappe.db.get_value(RECOVERY_FOLLOW_UP_PREPARATION_RUN, {"crm_deal": deal}, "name")


def _get_recovery_case_submission_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_recovery_case_submission_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_case_submission_run")
        if run:
            return run

    if _doctype_exists(RECOVERY_CASE_SUBMISSION_RUN):
        return frappe.db.get_value(RECOVERY_CASE_SUBMISSION_RUN, {"crm_deal": deal}, "name")

    return None


def _is_recovery_cases_submitted(run):
    if not run or not frappe.db.exists(RECOVERY_CASE_SUBMISSION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_CASE_SUBMISSION_RUN,
        run,
        ["status", "recovery_case_submission_run_ready"],
    )

    return status == "Recovery Cases Submitted" and bool(ready)


def _is_follow_up_preparation_approved(run):
    if not run or not frappe.db.exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        run,
        ["status", "recovery_follow_up_preparation_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _append_line_if_missing(doc, row_data):
    existing = {
        row.recovery_follow_up_source_key
        for row in doc.get("recovery_follow_up_preparation_lines") or []
        if row.get("recovery_follow_up_source_key")
    }

    key = row_data.get("recovery_follow_up_source_key")

    if key and key in existing:
        return False

    doc.append("recovery_follow_up_preparation_lines", row_data)
    return True


def _source_key(row):
    return row.get("recovery_case_submission_source_key") or "|".join([
        str(row.get("target_case_doctype") or ""),
        str(row.get("target_case_name") or ""),
        str(row.get("service_line") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("actual_payment_reference") or ""),
    ])


def _is_submission_line_completed(row):
    return row.get("recovery_case_submission_line_status") in [
        "CRM Recovery Case Activated",
        "External Recovery Case Submitted",
        "External Recovery Case Activated",
    ]


def _default_follow_up_action(row):
    route = (row.get("recovery_route") or "").lower()
    recovery_type = (row.get("recovery_type") or "").lower()

    if "plan manager" in route:
        return "Plan Manager Follow-Up"
    if "participant" in route:
        return "Participant Debt Follow-Up"
    if "provider" in route:
        return "Provider Correction Follow-Up"
    if "ndia" in route or "portal" in route:
        return "NDIA / Portal Follow-Up"
    if "duplicate" in recovery_type:
        return "Duplicate Payment Follow-Up"
    if "overpayment" in recovery_type:
        return "Overpayment Follow-Up"

    return "Accounts Recovery Follow-Up"


def _default_priority(row):
    amount = _to_float(row.get("proposed_recovery_amount"))

    if amount >= 1000:
        return "High"
    if amount >= 250:
        return "Medium"

    return "Normal"


def _default_due_date(row):
    priority = _default_priority(row)

    if priority == "High":
        return add_days(getdate(), 2)
    if priority == "Medium":
        return add_days(getdate(), 5)

    return add_days(getdate(), 7)


def _follow_up_instruction(row):
    action = _default_follow_up_action(row)
    amount = _to_float(row.get("proposed_recovery_amount"))
    party = row.get("recovery_party")
    reason = row.get("recovery_reason") or row.get("recommended_resolution") or "Recovery follow-up required."

    return (
        f"{action}: follow up with {party or 'the recovery party'} "
        f"for proposed recovery amount {amount:.2f}. Reason: {reason}"
    )


def _build_follow_up_line(row, source_doc):
    source_ready = bool(
        source_doc.get("status") == "Recovery Cases Submitted"
        and _is_submission_line_completed(row)
        and row.get("recovery_case_submission_source_ready")
        and row.get("recovery_case_submission_review_complete")
        and row.get("recovery_case_submission_authorized")
        and row.get("line_ready_for_recovery_case_submission")
        and not row.get("recovery_case_submission_hold")
        and not row.get("journal_entry_authorized")
        and not row.get("manual_gl_authorized")
        and not row.get("payment_entry_authorized")
        and not row.get("sales_invoice_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("bank_reconciliation_authorized")
        and _to_float(row.get("proposed_recovery_amount")) > 0
    )

    return {
        "recovery_follow_up_source_key": _source_key(row),

        "target_case_doctype": row.get("target_case_doctype"),
        "target_case_name": row.get("target_case_name"),
        "target_case_docstatus": row.get("target_case_docstatus"),
        "target_case_status": row.get("target_case_status"),
        "target_case_submittable": row.get("target_case_submittable"),

        "recovery_preparation_source_type": row.get("recovery_preparation_source_type"),

        "journal_entry": row.get("journal_entry"),
        "journal_entry_docstatus": row.get("journal_entry_docstatus"),
        "journal_entry_status": row.get("journal_entry_status"),
        "standard_gl_entry_count": row.get("standard_gl_entry_count"),

        "ndis_remittance_import": row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"),
        "ndis_remittance_import_docstatus": row.get("ndis_remittance_import_docstatus"),
        "ndis_remittance_import_status": row.get("ndis_remittance_import_status"),

        "payment_entry": row.get("payment_entry"),
        "payment_entry_docstatus": row.get("payment_entry_docstatus"),
        "payment_entry_status": row.get("payment_entry_status"),

        "sales_invoice": row.get("sales_invoice"),
        "sales_invoice_docstatus": row.get("sales_invoice_docstatus"),
        "sales_invoice_status": row.get("sales_invoice_status"),
        "sales_invoice_outstanding_amount": row.get("sales_invoice_outstanding_amount"),

        "ndis_claim_batch": row.get("ndis_claim_batch"),
        "ndis_claim_line": row.get("ndis_claim_line"),
        "service_line": row.get("service_line"),
        "service_code": row.get("service_code"),
        "service_model": row.get("service_model"),
        "service_date": row.get("service_date"),
        "support_item": row.get("support_item"),
        "finance_service_type": row.get("finance_service_type"),
        "plan_budget": row.get("plan_budget"),
        "service_booking": row.get("service_booking"),
        "funding_source": row.get("funding_source"),
        "default_house": row.get("default_house"),

        "external_lodgement_reference": row.get("external_lodgement_reference"),
        "external_batch_reference": row.get("external_batch_reference"),
        "external_line_reference": row.get("external_line_reference"),
        "actual_payment_reference": row.get("actual_payment_reference"),
        "actual_payment_date": row.get("actual_payment_date"),

        "review_category": row.get("review_category"),
        "recommended_resolution": row.get("recommended_resolution"),
        "matching_result": row.get("matching_result"),
        "allocation_type": row.get("allocation_type"),

        "claim_amount": row.get("claim_amount"),
        "expected_paid_amount": row.get("expected_paid_amount"),
        "actual_paid_amount": row.get("actual_paid_amount"),
        "actual_rejected_amount": row.get("actual_rejected_amount"),
        "variance_amount": row.get("variance_amount"),
        "short_paid_amount": row.get("short_paid_amount"),
        "rejected_amount": row.get("rejected_amount"),

        "proposed_recovery_amount": row.get("proposed_recovery_amount"),
        "recovery_type": row.get("recovery_type"),
        "recovery_route": row.get("recovery_route"),
        "recovery_reason": row.get("recovery_reason"),
        "recovery_party_type": row.get("recovery_party_type") or "Customer",
        "recovery_party": row.get("recovery_party") or source_doc.get("participant_customer"),
        "recovery_contact_name": row.get("recovery_contact_name"),
        "recovery_contact_email": row.get("recovery_contact_email"),
        "recovery_due_date": row.get("recovery_due_date"),

        "follow_up_action_type": _default_follow_up_action(row),
        "follow_up_priority": _default_priority(row),
        "follow_up_owner": frappe.session.user,
        "follow_up_due_date": row.get("recovery_due_date") or _default_due_date(row),
        "follow_up_channel": "Phone / Email Review",
        "follow_up_instruction": _follow_up_instruction(row),
        "follow_up_message_draft": None,

        "recovery_follow_up_source_ready": 1 if source_ready else 0,
        "follow_up_review_complete": 0,
        "contact_details_verified": 0,
        "follow_up_decision_authorized": 0,

        "todo_creation_authorized": 0,
        "task_creation_authorized": 0,
        "event_creation_authorized": 0,
        "email_creation_authorized": 0,
        "journal_entry_authorized": 0,
        "manual_gl_authorized": 0,
        "payment_entry_authorized": 0,
        "sales_invoice_authorized": 0,
        "adjustment_authorized": 0,
        "bank_reconciliation_authorized": 0,

        "recovery_follow_up_hold": 0 if source_ready else 1,
        "recovery_follow_up_hold_reason": None if source_ready else "Recovery case submission source is not ready for follow-up preparation.",
        "line_ready_for_recovery_follow_up_preparation": 0,
        "recovery_follow_up_preparation_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_submission_run(doc, source):
    created = 0

    for row in source.get("recovery_case_submission_lines") or []:
        if not _is_submission_line_completed(row):
            continue

        if _to_float(row.get("proposed_recovery_amount")) <= 0:
            continue

        data = _build_follow_up_line(row, source)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _active_lines(doc):
    return [
        row for row in doc.get("recovery_follow_up_preparation_lines") or []
        if _to_float(row.get("proposed_recovery_amount")) > 0
    ]


def _calculate_totals(doc):
    line_count = len(doc.get("recovery_follow_up_preparation_lines") or [])
    amount_total = 0
    ready_count = 0
    hold_count = 0
    high_priority_count = 0
    medium_priority_count = 0
    normal_priority_count = 0
    prepared_count = 0

    blocked_todo_count = 0
    blocked_task_count = 0
    blocked_event_count = 0
    blocked_email_count = 0
    blocked_je_count = 0
    blocked_gl_count = 0
    blocked_pe_count = 0
    blocked_si_count = 0
    blocked_adjustment_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("recovery_follow_up_preparation_lines") or []:
        amount_total += _to_float(row.get("proposed_recovery_amount"))

        if row.get("line_ready_for_recovery_follow_up_preparation"):
            ready_count += 1

        if row.get("recovery_follow_up_hold"):
            hold_count += 1

        priority = row.get("follow_up_priority")
        if priority == "High":
            high_priority_count += 1
        elif priority == "Medium":
            medium_priority_count += 1
        else:
            normal_priority_count += 1

        if row.get("recovery_follow_up_preparation_line_status") == "Follow Up Prepared":
            prepared_count += 1

        if row.get("todo_creation_authorized"):
            blocked_todo_count += 1
        if row.get("task_creation_authorized"):
            blocked_task_count += 1
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
        "recovery_follow_up_preparation_line_count": line_count,
        "recovery_follow_up_amount_total": round(amount_total, 2),
        "recovery_follow_up_ready_count": ready_count,
        "recovery_follow_up_hold_count": hold_count,
        "high_priority_follow_up_count": high_priority_count,
        "medium_priority_follow_up_count": medium_priority_count,
        "normal_priority_follow_up_count": normal_priority_count,
        "follow_up_prepared_line_count": prepared_count,
        "blocked_todo_count": blocked_todo_count,
        "blocked_task_count": blocked_task_count,
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
        if _field_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Recovery Case Submission Run linked",
        "complete": bool(doc.get("recovery_case_submission_run")),
    })

    checks.append({
        "label": "Recovery cases submitted / activated",
        "complete": _is_recovery_cases_submitted(doc.get("recovery_case_submission_run")),
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
        "label": "Recovery Follow-Up Preparation Owner assigned",
        "complete": bool(doc.get("recovery_follow_up_preparation_owner")),
    })

    lines = _active_lines(doc)
    no_candidates = bool(doc.get("no_recovery_follow_up_candidate_found"))

    checks.append({
        "label": "Recovery follow-up lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("recovery_follow_up_source_ready")]
        checks.append({
            "label": "Recovery follow-up source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        missing_amount = [row.service_line for row in lines if not _to_float(row.get("proposed_recovery_amount"))]
        checks.append({
            "label": "All lines have proposed recovery amount",
            "complete": not missing_amount,
            "details": missing_amount,
        })

        missing_action = [row.service_line for row in lines if not row.get("follow_up_action_type")]
        checks.append({
            "label": "All lines have follow-up action type",
            "complete": not missing_action,
            "details": missing_action,
        })

        missing_owner = [row.service_line for row in lines if not row.get("follow_up_owner")]
        checks.append({
            "label": "All lines have follow-up owner",
            "complete": not missing_owner,
            "details": missing_owner,
        })

        missing_due_date = [row.service_line for row in lines if not row.get("follow_up_due_date")]
        checks.append({
            "label": "All lines have follow-up due date",
            "complete": not missing_due_date,
            "details": missing_due_date,
        })

        missing_instruction = [row.service_line for row in lines if not row.get("follow_up_instruction")]
        checks.append({
            "label": "All lines have follow-up instruction",
            "complete": not missing_instruction,
            "details": missing_instruction,
        })

        review_missing = [row.service_line for row in lines if not row.get("follow_up_review_complete")]
        checks.append({
            "label": "Follow-up review complete",
            "complete": not review_missing,
            "details": review_missing,
        })

        contact_missing = [row.service_line for row in lines if not row.get("contact_details_verified")]
        checks.append({
            "label": "Contact details verified",
            "complete": not contact_missing,
            "details": contact_missing,
        })

        decision_missing = [row.service_line for row in lines if not row.get("follow_up_decision_authorized")]
        checks.append({
            "label": "Follow-up decision authorization complete",
            "complete": not decision_missing,
            "details": decision_missing,
        })

        blocked_fields = [
            ("ToDo creation remains blocked in Phase 40", "todo_creation_authorized"),
            ("Task creation remains blocked in Phase 40", "task_creation_authorized"),
            ("Event creation remains blocked in Phase 40", "event_creation_authorized"),
            ("Email creation remains blocked in Phase 40", "email_creation_authorized"),
            ("Journal Entry authorization remains blocked in Phase 40", "journal_entry_authorized"),
            ("Manual GL authorization remains blocked in Phase 40", "manual_gl_authorized"),
            ("Payment Entry authorization remains blocked in Phase 40", "payment_entry_authorized"),
            ("Sales Invoice authorization remains blocked in Phase 40", "sales_invoice_authorized"),
            ("Adjustment authorization remains blocked in Phase 40", "adjustment_authorized"),
            ("Bank reconciliation authorization remains blocked in Phase 40", "bank_reconciliation_authorized"),
        ]

        for label, fieldname in blocked_fields:
            blocked = [row.service_line for row in lines if row.get(fieldname)]
            checks.append({
                "label": label,
                "complete": not blocked,
                "details": blocked,
            })

        holds = [row.service_line for row in lines if row.get("recovery_follow_up_hold")]
        checks.append({
            "label": "No active recovery follow-up hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_recovery_follow_up_preparation")]
        checks.append({
            "label": "All active lines marked ready for recovery follow-up preparation",
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
        "recovery_follow_up_preparation_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN, "recovery_follow_up_preparation_run_ready"):
        doc.recovery_follow_up_preparation_run_ready = 1 if summary["recovery_follow_up_preparation_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_recovery_follow_up_preparation_run", doc.name)
        _db_set_if_field(doctype, name, "recovery_follow_up_preparation_status", doc.status)
        _db_set_if_field(doctype, name, "recovery_follow_up_preparation_ready", 1 if summary["recovery_follow_up_preparation_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_recovery_follow_up_preparation_run_from_case_submission_run(recovery_case_submission_run):
    _check_role()

    if not recovery_case_submission_run:
        frappe.throw(_("NDIS CRM Recovery Case Submission Run is required."))

    if not frappe.db.exists(RECOVERY_CASE_SUBMISSION_RUN, recovery_case_submission_run):
        frappe.throw(_("NDIS CRM Recovery Case Submission Run {0} was not found.").format(recovery_case_submission_run))

    existing = _existing_run_for_submission_run(recovery_case_submission_run)
    if existing:
        return {
            "doctype": RECOVERY_FOLLOW_UP_PREPARATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Follow Up Preparation Run returned.",
        }

    source = frappe.get_doc(RECOVERY_CASE_SUBMISSION_RUN, recovery_case_submission_run)

    doc = frappe.new_doc(RECOVERY_FOLLOW_UP_PREPARATION_RUN)
    doc.status = "Draft"
    doc.recovery_case_submission_run = source.name
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

    doc.recovery_follow_up_preparation_owner = frappe.session.user
    doc.recovery_case_submission_owner = source.get("recovery_case_submission_owner")

    doc.recovery_follow_up_preparation_completion_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.event_creation_allowed = 0
    doc.email_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines_from_submission_run(doc, source)
    doc.no_recovery_follow_up_candidate_found = 1 if created_count == 0 else 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_follow_up_preparation_run_ready = 1 if summary["recovery_follow_up_preparation_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        "name": doc.name,
        "created": True,
        "recovery_follow_up_preparation_line_count": created_count,
        "no_recovery_follow_up_candidate_found": bool(doc.no_recovery_follow_up_candidate_found),
        "message": "NDIS CRM Recovery Follow Up Preparation Run created successfully.",
    }


@frappe.whitelist()
def create_recovery_follow_up_preparation_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": RECOVERY_FOLLOW_UP_PREPARATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Follow Up Preparation Run returned.",
        }

    source_run = _get_recovery_case_submission_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Recovery Case Submission Run before creating Recovery Follow Up Preparation Run."))

    return create_recovery_follow_up_preparation_run_from_case_submission_run(source_run)


@frappe.whitelist()
def generate_recovery_follow_up_preparation_lines(recovery_follow_up_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_PREPARATION_RUN, recovery_follow_up_preparation_run)

    if not doc.get("recovery_case_submission_run"):
        frappe.throw(_("Recovery Case Submission Run is required."))

    source = frappe.get_doc(RECOVERY_CASE_SUBMISSION_RUN, doc.recovery_case_submission_run)
    created_count = _generate_lines_from_submission_run(doc, source)

    if created_count == 0 and not doc.get("recovery_follow_up_preparation_lines"):
        doc.no_recovery_follow_up_candidate_found = 1
    else:
        doc.no_recovery_follow_up_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Recovery follow-up preparation lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_recovery_follow_up_preparation_readiness(recovery_follow_up_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_PREPARATION_RUN, recovery_follow_up_preparation_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Recovery Follow Up Preparation Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_recovery_follow_up_preparation(recovery_follow_up_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_PREPARATION_RUN, recovery_follow_up_preparation_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_follow_up_preparation_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Recovery Follow Up Preparation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Recovery Follow Up Preparation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_follow_up_preparation_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        "name": doc.name,
        "message": "Recovery Follow Up Preparation Run marked Ready.",
    }


@frappe.whitelist()
def approve_recovery_follow_up_preparation_run(recovery_follow_up_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_PREPARATION_RUN, recovery_follow_up_preparation_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_follow_up_preparation_run_ready"]:
        frappe.throw(
            _("Cannot approve Recovery Follow Up Preparation Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Recovery Follow Up Preparation Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_follow_up_preparation_run_ready = 1

    doc.recovery_follow_up_preparation_completion_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.event_creation_allowed = 0
    doc.email_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("recovery_follow_up_preparation_lines") or []:
        if row.get("recovery_follow_up_preparation_line_status") in ["Draft", "Ready"]:
            row.recovery_follow_up_preparation_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        "name": doc.name,
        "message": "Recovery Follow Up Preparation Run approved. No task, email, ToDo, Event, invoice, payment, journal, adjustment, or posting was created.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("recovery_follow_up_preparation_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_recovery_follow_up_preparation"):
            continue

        if not row.get("recovery_follow_up_source_ready"):
            continue

        if not row.get("follow_up_review_complete"):
            continue

        if not row.get("contact_details_verified"):
            continue

        if not row.get("follow_up_decision_authorized"):
            continue

        blocked = any([
            row.get("todo_creation_authorized"),
            row.get("task_creation_authorized"),
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

        if row.get("recovery_follow_up_hold"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_recovery_follow_up_preparation(recovery_follow_up_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_FOLLOW_UP_PREPARATION_RUN, recovery_follow_up_preparation_run)

    if doc.status != "Recovery Follow Up Preparation Approved":
        frappe.throw(_("Recovery Follow Up Preparation Run must be approved before completion."))

    if not doc.get("recovery_follow_up_preparation_completion_allowed"):
        frappe.throw(_("Tick Recovery Follow Up Preparation Completion Allowed before completing preparation."))

    blocked_run_fields = [
        ("ToDo Creation Allowed", "todo_creation_allowed"),
        ("Task Creation Allowed", "task_creation_allowed"),
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
            frappe.throw(_("{0} must remain unticked in Phase 40.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["recovery_follow_up_preparation_run_ready"]:
        frappe.throw(
            _("Cannot complete Recovery Follow Up Preparation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines and not doc.get("no_recovery_follow_up_candidate_found"):
        frappe.throw(_("No ready recovery follow-up preparation lines found."))

    for row in ready_lines:
        row.recovery_follow_up_preparation_line_status = "Follow Up Prepared"

    doc.status = "Recovery Follow Up Prepared"
    doc.recovery_follow_up_preparation_completion_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.event_creation_allowed = 0
    doc.email_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "prepared_line_count": len(ready_lines),
        "no_recovery_follow_up_candidate_found": bool(doc.get("no_recovery_follow_up_candidate_found")),
        "message": "Recovery follow-up preparation completed. No ToDo, Task, Event, Email, Journal Entry, GL, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or remittance import was created.",
    }


def validate_recovery_follow_up_preparation_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN, "recovery_follow_up_preparation_run_ready"):
        doc.recovery_follow_up_preparation_run_ready = 1 if summary["recovery_follow_up_preparation_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["recovery_follow_up_preparation_run_ready"]:
        frappe.throw(
            _("Cannot set Recovery Follow Up Preparation Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Recovery Follow Up Preparation Approved" and doc.get("recovery_follow_up_preparation_completion_allowed"):
        frappe.throw(_("Recovery Follow Up Preparation Completion Allowed can only be ticked after the run is approved."))

    blocked_run_fields = [
        ("ToDo creation", "todo_creation_allowed"),
        ("Task creation", "task_creation_allowed"),
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
            frappe.throw(_("{0} is not allowed in Phase 40.").format(label))


def on_recovery_follow_up_preparation_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Recovery Follow Up Preparation Run Summary Sync Failed"
        )


def validate_crm_deal_phase40(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_recovery_follow_up_preparation_run_required"):
        required = doc.get("ndis_recovery_follow_up_preparation_run_required")

    if not required:
        return

    run = doc.get("ndis_recovery_follow_up_preparation_run") if _field_exists(CRM_DEAL, "ndis_recovery_follow_up_preparation_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Follow Up Preparation Run must be created and approved/prepared.")
        )

    if not _is_follow_up_preparation_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Follow Up Preparation Run must be approved/prepared.")
        )


def validate_crm_deal_phase40_combined(doc, method=None):
    """
    Preserve Phase 2-39 validator chain, then add optional Phase 40 Recovery Follow-Up Preparation validation.
    """
    try:
        from ndis_crm.phase39_recovery_case_submission import validate_crm_deal_phase39_combined
        validate_crm_deal_phase39_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase38_recovery_case_draft import validate_crm_deal_phase38_combined
            validate_crm_deal_phase38_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase37_recovery_preparation import validate_crm_deal_phase37_combined
                validate_crm_deal_phase37_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase40(doc, method)


def phase40_health_check():
    print("---- NDIS CRM Phase 40 Health Check ----")

    for dt in [
        RECOVERY_FOLLOW_UP_PREPARATION_LINE,
        RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        RECOVERY_CASE_SUBMISSION_RUN,
        RECOVERY_CASE_SUBMISSION_LINE,
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
        "ToDo",
        "Task",
        "Event",
        "Communication",
        NDIS_RECOVERY_CASE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_recovery_follow_up_preparation_run_required",
        "ndis_recovery_follow_up_preparation_run",
        "recovery_follow_up_preparation_status",
        "recovery_follow_up_preparation_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print("NDIS CRM Recovery Follow Up Preparation Run records:", frappe.db.count(RECOVERY_FOLLOW_UP_PREPARATION_RUN) if _doctype_exists(RECOVERY_FOLLOW_UP_PREPARATION_RUN) else 0)
    print("Phase 40 creates CRM recovery follow-up preparation records only.")
    print("Phase 40 does not create ToDo, Task, Event, Communication, Email, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 40 Health Check ----")
