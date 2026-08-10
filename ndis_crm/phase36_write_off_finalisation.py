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
WRITE_OFF_JE_SUBMISSION_LINE = "NDIS CRM Write Off JE Submission Line"

WRITE_OFF_FINALISATION_RUN = "NDIS CRM Write Off Finalisation Run"
WRITE_OFF_FINALISATION_LINE = "NDIS CRM Write Off Finalisation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
JOURNAL_ENTRY = "Journal Entry"
GL_ENTRY = "GL Entry"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_WRITE_OFF = "NDIS Write Off"
NDIS_RECOVERY_CASE = "NDIS Recovery Case"

READY_STATUSES = [
    "Ready for Write Off Finalisation",
    "Write Off Finalisation Approved",
    "Write Off Finalised",
]

APPROVED_STATUSES = [
    "Write Off Finalisation Approved",
    "Write Off Finalised",
]

SOURCE_READY_STATUSES = [
    "Journal Entries Submitted",
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
        frappe.throw(_("You do not have permission to perform this write-off finalisation action."))


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


def _to_float(value):
    if value in [None, ""]:
        return 0
    try:
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").strip()
        return float(value)
    except Exception:
        return 0


def _existing_run_for_submission_run(write_off_je_submission_run):
    if not _doctype_exists(WRITE_OFF_FINALISATION_RUN):
        return None

    if _field_exists(WRITE_OFF_JE_SUBMISSION_RUN, "ndis_write_off_finalisation_run"):
        existing = frappe.db.get_value(
            WRITE_OFF_JE_SUBMISSION_RUN,
            write_off_je_submission_run,
            "ndis_write_off_finalisation_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        WRITE_OFF_FINALISATION_RUN,
        {"write_off_je_submission_run": write_off_je_submission_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(WRITE_OFF_FINALISATION_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_write_off_finalisation_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_write_off_finalisation_run")
        if existing:
            return existing

    return frappe.db.get_value(WRITE_OFF_FINALISATION_RUN, {"crm_deal": deal}, "name")


def _get_submission_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_write_off_je_submission_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_write_off_je_submission_run")
        if run:
            return run

    if _doctype_exists(WRITE_OFF_JE_SUBMISSION_RUN):
        return frappe.db.get_value(WRITE_OFF_JE_SUBMISSION_RUN, {"crm_deal": deal}, "name")

    return None


def _is_submission_completed(run):
    if not run or not frappe.db.exists(WRITE_OFF_JE_SUBMISSION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        WRITE_OFF_JE_SUBMISSION_RUN,
        run,
        ["status", "write_off_je_submission_run_ready"],
    )

    return status in SOURCE_READY_STATUSES and bool(ready)


def _is_finalisation_approved(run):
    if not run or not frappe.db.exists(WRITE_OFF_FINALISATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        WRITE_OFF_FINALISATION_RUN,
        run,
        ["status", "write_off_finalisation_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _journal_entry_snapshot(journal_entry):
    if not journal_entry or not _doctype_exists(JOURNAL_ENTRY):
        return {}

    if not frappe.db.exists(JOURNAL_ENTRY, journal_entry):
        return {}

    fields = [
        "name",
        "docstatus",
        "voucher_type",
        "company",
        "posting_date",
        "total_debit",
        "total_credit",
        "status",
    ]

    safe_fields = []
    for field in fields:
        if field in ["name", "docstatus"] or _field_exists(JOURNAL_ENTRY, field):
            safe_fields.append(field)

    return frappe.db.get_value(JOURNAL_ENTRY, journal_entry, safe_fields, as_dict=True) or {}


def _gl_entry_count_for_journal_entry(journal_entry):
    if not journal_entry or not _doctype_exists(GL_ENTRY):
        return 0

    return frappe.db.count(GL_ENTRY, {"voucher_type": JOURNAL_ENTRY, "voucher_no": journal_entry})


def _sales_invoice_snapshot(sales_invoice):
    if not sales_invoice or not _doctype_exists(SALES_INVOICE):
        return {}

    if not frappe.db.exists(SALES_INVOICE, sales_invoice):
        return {}

    return frappe.db.get_value(
        SALES_INVOICE,
        sales_invoice,
        [
            "name",
            "docstatus",
            "customer",
            "company",
            "grand_total",
            "rounded_total",
            "outstanding_amount",
            "status",
        ],
        as_dict=True,
    ) or {}


def _append_line_if_missing(doc, row_data):
    existing = {
        row.write_off_finalisation_source_key
        for row in doc.get("write_off_finalisation_lines") or []
        if row.get("write_off_finalisation_source_key")
    }

    key = row_data.get("write_off_finalisation_source_key")

    if key and key in existing:
        return False

    doc.append("write_off_finalisation_lines", row_data)
    return True


def _source_key(row):
    return row.get("write_off_je_submission_source_key") or "|".join([
        str(row.get("journal_entry") or ""),
        str(row.get("service_line") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("source_write_off_draft_name") or ""),
    ])


def _is_submitted_submission_line(row):
    return bool(
        row.get("write_off_je_submission_line_status") == "Journal Entry Submitted"
        and row.get("journal_entry")
        and int(row.get("journal_entry_docstatus") or 0) == 1
    )


def _build_finalisation_line_from_submission_line(row, source_doc):
    journal_entry = row.get("journal_entry")
    je_snapshot = _journal_entry_snapshot(journal_entry)
    invoice_snapshot = _sales_invoice_snapshot(row.get("sales_invoice"))

    je_docstatus = int(je_snapshot.get("docstatus") or 0) if je_snapshot else int(row.get("journal_entry_docstatus") or 0)
    gl_count = _gl_entry_count_for_journal_entry(journal_entry)

    source_ready = bool(
        source_doc.get("status") == "Journal Entries Submitted"
        and row.get("write_off_je_submission_line_status") == "Journal Entry Submitted"
        and journal_entry
        and je_docstatus == 1
        and row.get("write_off_je_submission_source_ready")
        and row.get("journal_entry_submission_review_complete")
        and row.get("journal_entry_submission_authorized")
        and row.get("line_ready_for_journal_entry_submission")
        and not row.get("write_off_je_submission_hold")
        and not row.get("manual_gl_authorized")
        and not row.get("payment_entry_authorized")
        and not row.get("write_off_submit_authorized")
        and not row.get("recovery_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("bank_reconciliation_authorized")
    )

    return {
        "write_off_finalisation_source_key": _source_key(row),

        "journal_entry": journal_entry,
        "journal_entry_docstatus": je_docstatus,
        "journal_entry_status": je_snapshot.get("status") or row.get("journal_entry_status"),
        "journal_entry_posting_date": je_snapshot.get("posting_date") or row.get("journal_entry_posting_date"),
        "journal_entry_total_debit": je_snapshot.get("total_debit") or row.get("journal_entry_total_debit"),
        "journal_entry_total_credit": je_snapshot.get("total_credit") or row.get("journal_entry_total_credit"),
        "standard_gl_entry_count": gl_count,

        "source_write_off_draft_doctype": row.get("source_write_off_draft_doctype"),
        "source_write_off_draft_name": row.get("source_write_off_draft_name"),
        "source_write_off_draft_docstatus": row.get("source_write_off_draft_docstatus"),

        "ndis_remittance_import": row.get("ndis_remittance_import"),
        "ndis_remittance_import_docstatus": row.get("ndis_remittance_import_docstatus"),
        "ndis_remittance_import_status": row.get("ndis_remittance_import_status"),

        "payment_entry": row.get("payment_entry"),
        "payment_entry_docstatus": row.get("payment_entry_docstatus"),
        "payment_entry_status": row.get("payment_entry_status"),

        "sales_invoice": row.get("sales_invoice"),
        "sales_invoice_docstatus": int(invoice_snapshot.get("docstatus") or 0) if invoice_snapshot else row.get("sales_invoice_docstatus"),
        "sales_invoice_status": invoice_snapshot.get("status") or row.get("sales_invoice_status"),
        "sales_invoice_outstanding_amount": invoice_snapshot.get("outstanding_amount") if invoice_snapshot else row.get("sales_invoice_outstanding_amount"),

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

        "finalised_write_off_amount": row.get("proposed_write_off_amount"),
        "write_off_reason": row.get("write_off_reason"),
        "write_off_treatment": row.get("write_off_treatment"),
        "write_off_basis": row.get("write_off_basis"),

        "write_off_expense_account": row.get("write_off_expense_account"),
        "receivable_account": row.get("receivable_account"),
        "party_type": row.get("party_type"),
        "party": row.get("party"),
        "cost_center": row.get("cost_center"),

        "write_off_finalisation_source_ready": 1 if source_ready else 0,
        "journal_entry_posting_verified": 0,
        "standard_gl_review_complete": 0,
        "write_off_finalisation_authorized": 0,

        "manual_gl_authorized": 0,
        "payment_entry_authorized": 0,
        "additional_journal_entry_authorized": 0,
        "recovery_authorized": 0,
        "adjustment_authorized": 0,
        "bank_reconciliation_authorized": 0,

        "write_off_finalisation_hold": 0 if source_ready else 1,
        "write_off_finalisation_hold_reason": None if source_ready else "Submitted Journal Entry source is not ready for write-off finalisation.",
        "line_ready_for_write_off_finalisation": 0,
        "write_off_finalisation_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_submission_run(doc, source):
    created = 0

    for row in source.get("write_off_je_submission_lines") or []:
        if not _is_submitted_submission_line(row):
            continue

        data = _build_finalisation_line_from_submission_line(row, source)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _active_finalisation_lines(doc):
    return [
        row for row in doc.get("write_off_finalisation_lines") or []
        if row.get("journal_entry")
    ]


def _calculate_totals(doc):
    line_count = len(doc.get("write_off_finalisation_lines") or [])
    amount_total = 0
    ready_count = 0
    hold_count = 0
    submitted_je_count = 0
    standard_gl_count = 0
    finalised_count = 0

    blocked_manual_gl_count = 0
    blocked_payment_entry_count = 0
    blocked_additional_je_count = 0
    blocked_recovery_count = 0
    blocked_adjustment_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("write_off_finalisation_lines") or []:
        amount_total += _to_float(row.get("finalised_write_off_amount"))

        if row.get("line_ready_for_write_off_finalisation"):
            ready_count += 1

        if row.get("write_off_finalisation_hold"):
            hold_count += 1

        if int(row.get("journal_entry_docstatus") or 0) == 1:
            submitted_je_count += 1

        standard_gl_count += int(row.get("standard_gl_entry_count") or 0)

        if row.get("write_off_finalisation_line_status") == "Write Off Finalised":
            finalised_count += 1

        if row.get("manual_gl_authorized"):
            blocked_manual_gl_count += 1

        if row.get("payment_entry_authorized"):
            blocked_payment_entry_count += 1

        if row.get("additional_journal_entry_authorized"):
            blocked_additional_je_count += 1

        if row.get("recovery_authorized"):
            blocked_recovery_count += 1

        if row.get("adjustment_authorized"):
            blocked_adjustment_count += 1

        if row.get("bank_reconciliation_authorized"):
            blocked_bank_rec_count += 1

    return {
        "write_off_finalisation_line_count": line_count,
        "finalised_write_off_amount_total": round(amount_total, 2),
        "write_off_finalisation_ready_count": ready_count,
        "write_off_finalisation_hold_count": hold_count,
        "submitted_journal_entry_count": submitted_je_count,
        "standard_gl_entry_count": standard_gl_count,
        "write_off_finalised_line_count": finalised_count,
        "blocked_manual_gl_count": blocked_manual_gl_count,
        "blocked_payment_entry_count": blocked_payment_entry_count,
        "blocked_additional_journal_entry_count": blocked_additional_je_count,
        "blocked_recovery_authorization_count": blocked_recovery_count,
        "blocked_adjustment_authorization_count": blocked_adjustment_count,
        "blocked_bank_reconciliation_count": blocked_bank_rec_count,
    }


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(WRITE_OFF_FINALISATION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Write Off JE Submission Run linked",
        "complete": bool(doc.get("write_off_je_submission_run")),
    })

    checks.append({
        "label": "Journal Entries submitted through Phase 35",
        "complete": _is_submission_completed(doc.get("write_off_je_submission_run")),
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
        "label": "Write-Off Finalisation Owner assigned",
        "complete": bool(doc.get("write_off_finalisation_owner")),
    })

    lines = _active_finalisation_lines(doc)
    no_candidates = bool(doc.get("no_write_off_finalisation_candidate_found"))

    checks.append({
        "label": "Write-off finalisation lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("write_off_finalisation_source_ready")]
        checks.append({
            "label": "Write-off finalisation source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        not_submitted = []
        for row in lines:
            snapshot = _journal_entry_snapshot(row.get("journal_entry"))
            if int(snapshot.get("docstatus") or 0) != 1:
                not_submitted.append(row.get("journal_entry"))

        checks.append({
            "label": "All linked Journal Entries are submitted",
            "complete": not not_submitted,
            "details": not_submitted,
        })

        missing_amount = [row.service_line for row in lines if not _to_float(row.get("finalised_write_off_amount"))]
        checks.append({
            "label": "All lines have finalised write-off amount",
            "complete": not missing_amount,
            "details": missing_amount,
        })

        posting_not_verified = [row.service_line for row in lines if not row.get("journal_entry_posting_verified")]
        checks.append({
            "label": "Journal Entry posting verified",
            "complete": not posting_not_verified,
            "details": posting_not_verified,
        })

        gl_not_reviewed = [row.service_line for row in lines if not row.get("standard_gl_review_complete")]
        checks.append({
            "label": "Standard GL review complete",
            "complete": not gl_not_reviewed,
            "details": gl_not_reviewed,
        })

        finalisation_not_authorized = [row.service_line for row in lines if not row.get("write_off_finalisation_authorized")]
        checks.append({
            "label": "Write-off finalisation authorization complete",
            "complete": not finalisation_not_authorized,
            "details": finalisation_not_authorized,
        })

        manual_gl_authorized = [row.service_line for row in lines if row.get("manual_gl_authorized")]
        checks.append({
            "label": "Manual GL authorization remains blocked in Phase 36",
            "complete": not manual_gl_authorized,
            "details": manual_gl_authorized,
        })

        payment_entry_authorized = [row.service_line for row in lines if row.get("payment_entry_authorized")]
        checks.append({
            "label": "Payment Entry authorization remains blocked in Phase 36",
            "complete": not payment_entry_authorized,
            "details": payment_entry_authorized,
        })

        additional_je_authorized = [row.service_line for row in lines if row.get("additional_journal_entry_authorized")]
        checks.append({
            "label": "Additional Journal Entry authorization remains blocked in Phase 36",
            "complete": not additional_je_authorized,
            "details": additional_je_authorized,
        })

        recovery_authorized = [row.service_line for row in lines if row.get("recovery_authorized")]
        checks.append({
            "label": "Recovery authorization remains blocked in Phase 36",
            "complete": not recovery_authorized,
            "details": recovery_authorized,
        })

        adjustment_authorized = [row.service_line for row in lines if row.get("adjustment_authorized")]
        checks.append({
            "label": "Adjustment authorization remains blocked in Phase 36",
            "complete": not adjustment_authorized,
            "details": adjustment_authorized,
        })

        bank_rec_authorized = [row.service_line for row in lines if row.get("bank_reconciliation_authorized")]
        checks.append({
            "label": "Bank reconciliation authorization remains blocked in Phase 36",
            "complete": not bank_rec_authorized,
            "details": bank_rec_authorized,
        })

        holds = [row.service_line for row in lines if row.get("write_off_finalisation_hold")]
        checks.append({
            "label": "No active write-off finalisation hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_write_off_finalisation")]
        checks.append({
            "label": "All active lines marked ready for write-off finalisation",
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
        "write_off_finalisation_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(WRITE_OFF_FINALISATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(WRITE_OFF_FINALISATION_RUN, "write_off_finalisation_run_ready"):
        doc.write_off_finalisation_run_ready = 1 if summary["write_off_finalisation_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_write_off_finalisation_run", doc.name)
        _db_set_if_field(doctype, name, "write_off_finalisation_status", doc.status)
        _db_set_if_field(doctype, name, "write_off_finalisation_ready", 1 if summary["write_off_finalisation_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_write_off_finalisation_run_from_je_submission_run(write_off_je_submission_run):
    _check_role()

    if not write_off_je_submission_run:
        frappe.throw(_("NDIS CRM Write Off JE Submission Run is required."))

    if not frappe.db.exists(WRITE_OFF_JE_SUBMISSION_RUN, write_off_je_submission_run):
        frappe.throw(_("NDIS CRM Write Off JE Submission Run {0} was not found.").format(write_off_je_submission_run))

    existing = _existing_run_for_submission_run(write_off_je_submission_run)
    if existing:
        return {
            "doctype": WRITE_OFF_FINALISATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Write Off Finalisation Run returned.",
        }

    source = frappe.get_doc(WRITE_OFF_JE_SUBMISSION_RUN, write_off_je_submission_run)

    doc = frappe.new_doc(WRITE_OFF_FINALISATION_RUN)
    doc.status = "Draft"
    doc.write_off_je_submission_run = source.name
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

    doc.write_off_finalisation_owner = frappe.session.user
    doc.write_off_je_submission_owner = source.get("write_off_je_submission_owner")
    doc.write_off_finalisation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.additional_journal_entry_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines_from_submission_run(doc, source)

    if created_count == 0:
        doc.no_write_off_finalisation_candidate_found = 1
    else:
        doc.no_write_off_finalisation_candidate_found = 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.write_off_finalisation_run_ready = 1 if summary["write_off_finalisation_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": WRITE_OFF_FINALISATION_RUN,
        "name": doc.name,
        "created": True,
        "write_off_finalisation_line_count": created_count,
        "no_write_off_finalisation_candidate_found": bool(doc.no_write_off_finalisation_candidate_found),
        "message": "NDIS CRM Write Off Finalisation Run created successfully.",
    }


@frappe.whitelist()
def create_write_off_finalisation_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": WRITE_OFF_FINALISATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Write Off Finalisation Run returned.",
        }

    source_run = _get_submission_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Write Off JE Submission Run before creating Write Off Finalisation Run."))

    return create_write_off_finalisation_run_from_je_submission_run(source_run)


@frappe.whitelist()
def generate_write_off_finalisation_lines(write_off_finalisation_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_FINALISATION_RUN, write_off_finalisation_run)

    if not doc.get("write_off_je_submission_run"):
        frappe.throw(_("Write Off JE Submission Run is required."))

    source = frappe.get_doc(WRITE_OFF_JE_SUBMISSION_RUN, doc.write_off_je_submission_run)
    created_count = _generate_lines_from_submission_run(doc, source)

    if created_count == 0 and not doc.get("write_off_finalisation_lines"):
        doc.no_write_off_finalisation_candidate_found = 1
    else:
        doc.no_write_off_finalisation_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Write-off finalisation lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_write_off_finalisation_readiness(write_off_finalisation_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_FINALISATION_RUN, write_off_finalisation_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Write Off Finalisation Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_write_off_finalisation(write_off_finalisation_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_FINALISATION_RUN, write_off_finalisation_run)
    summary = _calculate_readiness(doc)

    if not summary["write_off_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Write Off Finalisation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Write Off Finalisation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.write_off_finalisation_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": WRITE_OFF_FINALISATION_RUN,
        "name": doc.name,
        "message": "Write Off Finalisation Run marked Ready.",
    }


@frappe.whitelist()
def approve_write_off_finalisation_run(write_off_finalisation_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_FINALISATION_RUN, write_off_finalisation_run)
    summary = _calculate_readiness(doc)

    if not summary["write_off_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot approve Write Off Finalisation Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Write Off Finalisation Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.write_off_finalisation_run_ready = 1
    doc.write_off_finalisation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.additional_journal_entry_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("write_off_finalisation_lines") or []:
        if row.get("write_off_finalisation_line_status") in ["Draft", "Ready"]:
            row.write_off_finalisation_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": WRITE_OFF_FINALISATION_RUN,
        "name": doc.name,
        "message": "Write Off Finalisation Run approved. No new accounting document was created.",
    }


def _ready_lines_for_finalisation(doc):
    ready = []

    for row in _active_finalisation_lines(doc):
        if row.get("write_off_finalisation_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_write_off_finalisation"):
            continue

        if not row.get("write_off_finalisation_source_ready"):
            continue

        if not row.get("journal_entry_posting_verified"):
            continue

        if not row.get("standard_gl_review_complete"):
            continue

        if not row.get("write_off_finalisation_authorized"):
            continue

        if row.get("manual_gl_authorized"):
            continue

        if row.get("payment_entry_authorized"):
            continue

        if row.get("additional_journal_entry_authorized"):
            continue

        if row.get("recovery_authorized"):
            continue

        if row.get("adjustment_authorized"):
            continue

        if row.get("bank_reconciliation_authorized"):
            continue

        if row.get("write_off_finalisation_hold"):
            continue

        snapshot = _journal_entry_snapshot(row.get("journal_entry"))
        if int(snapshot.get("docstatus") or 0) != 1:
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_write_off_finalisation(write_off_finalisation_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_FINALISATION_RUN, write_off_finalisation_run)

    if doc.status != "Write Off Finalisation Approved":
        frappe.throw(_("Write Off Finalisation Run must be approved before finalisation."))

    if not doc.get("write_off_finalisation_allowed"):
        frappe.throw(_("Tick Write Off Finalisation Allowed before completing finalisation."))

    if doc.get("manual_gl_creation_allowed"):
        frappe.throw(_("Manual GL Creation Allowed must remain unticked in Phase 36."))

    if doc.get("payment_entry_creation_allowed"):
        frappe.throw(_("Payment Entry Creation Allowed must remain unticked in Phase 36."))

    if doc.get("additional_journal_entry_creation_allowed"):
        frappe.throw(_("Additional Journal Entry Creation Allowed must remain unticked in Phase 36."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery Creation Allowed must remain unticked in Phase 36."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment Creation Allowed must remain unticked in Phase 36."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank Reconciliation Allowed must remain unticked in Phase 36."))

    summary = _calculate_readiness(doc)

    if not summary["write_off_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot complete Write Off Finalisation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_finalisation(doc)

    if not ready_lines and not doc.get("no_write_off_finalisation_candidate_found"):
        frappe.throw(_("No ready write-off finalisation lines found."))

    finalised_journal_entries = []

    for row in ready_lines:
        journal_entry = row.get("journal_entry")
        snapshot = _journal_entry_snapshot(journal_entry)

        if int(snapshot.get("docstatus") or 0) != 1:
            frappe.throw(_("Journal Entry {0} must be submitted before finalisation.").format(journal_entry))

        row.journal_entry_docstatus = 1
        row.journal_entry_status = snapshot.get("status") or "Submitted"
        row.standard_gl_entry_count = _gl_entry_count_for_journal_entry(journal_entry)
        row.write_off_finalisation_line_status = "Write Off Finalised"
        finalised_journal_entries.append(journal_entry)

        if journal_entry:
            _db_set_if_field(JOURNAL_ENTRY, journal_entry, "ndis_crm_write_off_finalisation_run", doc.name)
            _db_set_if_field(JOURNAL_ENTRY, journal_entry, "ndis_crm_write_off_finalisation_line", row.name)
            _db_set_if_field(JOURNAL_ENTRY, journal_entry, "ndis_crm_write_off_finalisation_status", "Write Off Finalised")

    doc.status = "Write Off Finalised"
    doc.write_off_finalisation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.additional_journal_entry_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.finalised_by = frappe.session.user
    doc.finalised_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "finalised_journal_entries": finalised_journal_entries,
        "finalised_journal_entry_count": len(finalised_journal_entries),
        "message": "Write-off finalisation completed. Status was synced only. No new Journal Entry, GL Entry, Payment Entry, recovery, adjustment, or bank reconciliation was created.",
    }


def validate_write_off_finalisation_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(WRITE_OFF_FINALISATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(WRITE_OFF_FINALISATION_RUN, "write_off_finalisation_run_ready"):
        doc.write_off_finalisation_run_ready = 1 if summary["write_off_finalisation_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["write_off_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot set Write Off Finalisation Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Write Off Finalisation Approved" and doc.get("write_off_finalisation_allowed"):
        frappe.throw(_("Write Off Finalisation Allowed can only be ticked after the run is approved."))

    if doc.get("manual_gl_creation_allowed"):
        frappe.throw(_("Manual GL creation is not allowed in Phase 36."))

    if doc.get("payment_entry_creation_allowed"):
        frappe.throw(_("Payment Entry creation is not allowed in Phase 36."))

    if doc.get("additional_journal_entry_creation_allowed"):
        frappe.throw(_("Additional Journal Entry creation is not allowed in Phase 36."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery creation is not allowed in Phase 36."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment creation is not allowed in Phase 36."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank reconciliation is not allowed in Phase 36."))


def on_write_off_finalisation_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Write Off Finalisation Run Summary Sync Failed"
        )


def validate_crm_deal_phase36(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_write_off_finalisation_run_required"):
        required = doc.get("ndis_write_off_finalisation_run_required")

    if not required:
        return

    run = doc.get("ndis_write_off_finalisation_run") if _field_exists(CRM_DEAL, "ndis_write_off_finalisation_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Write Off Finalisation Run must be created and approved/finalised.")
        )

    if not _is_finalisation_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Write Off Finalisation Run must be approved/finalised.")
        )


def validate_crm_deal_phase36_combined(doc, method=None):
    """
    Preserve Phase 2-35 validator chain, then add optional Phase 36 Write-Off Finalisation validation.
    """
    try:
        from ndis_crm.phase35_write_off_je_submission import validate_crm_deal_phase35_combined
        validate_crm_deal_phase35_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase34_write_off_je_draft import validate_crm_deal_phase34_combined
            validate_crm_deal_phase34_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase33_write_off_draft import validate_crm_deal_phase33_combined
                validate_crm_deal_phase33_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase36(doc, method)


def phase36_health_check():
    print("---- NDIS CRM Phase 36 Health Check ----")

    for dt in [
        WRITE_OFF_FINALISATION_LINE,
        WRITE_OFF_FINALISATION_RUN,
        WRITE_OFF_JE_SUBMISSION_RUN,
        WRITE_OFF_JE_SUBMISSION_LINE,
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
        NDIS_WRITE_OFF,
        NDIS_RECOVERY_CASE,
        "Bank Reconciliation Tool",
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_write_off_finalisation_run_required",
        "ndis_write_off_finalisation_run",
        "write_off_finalisation_status",
        "write_off_finalisation_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    for field in [
        "ndis_crm_write_off_finalisation_run",
        "ndis_crm_write_off_finalisation_line",
        "ndis_crm_write_off_finalisation_status",
    ]:
        print(f"Journal Entry field {field}: {'OK' if _field_exists(JOURNAL_ENTRY, field) else 'MISSING'}")

    print("NDIS CRM Write Off Finalisation Run records:", frappe.db.count(WRITE_OFF_FINALISATION_RUN) if _doctype_exists(WRITE_OFF_FINALISATION_RUN) else 0)
    print("Phase 36 creates CRM finalisation records only.")
    print("Phase 36 only verifies submitted Journal Entry / standard GL status and syncs finalisation status.")
    print("Phase 36 does not create or submit Journal Entry, create GL Entry, Payment Entry, Sales Invoice, recovery case, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 36 Health Check ----")
