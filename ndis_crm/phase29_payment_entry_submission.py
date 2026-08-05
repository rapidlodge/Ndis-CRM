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
PAYMENT_ENTRY_DRAFT_LINE = "NDIS CRM Payment Entry Draft Line"

PAYMENT_ENTRY_SUBMISSION_RUN = "NDIS CRM Payment Entry Submission Run"
PAYMENT_ENTRY_SUBMISSION_LINE = "NDIS CRM Payment Entry Submission Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
PAYMENT_ENTRY_REFERENCE = "Payment Entry Reference"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"

READY_STATUSES = [
    "Ready for Payment Entry Submission",
    "Payment Entry Submission Run Approved",
    "Payment Entries Submitted",
]

APPROVED_STATUSES = [
    "Payment Entry Submission Run Approved",
    "Payment Entries Submitted",
]

SOURCE_READY_STATUSES = [
    "Draft Payment Entries Created",
]

ALLOWED_ROLES = {
    "System Manager",
    "Accounts Manager",
    "Accounts User",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
}


def _check_role():
    if frappe.session.user == "Administrator":
        return

    user_roles = set(frappe.get_roles())
    if not user_roles.intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this Payment Entry submission action."))


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


def _existing_run_for_payment_entry_draft_run(payment_entry_draft_run):
    if not _doctype_exists(PAYMENT_ENTRY_SUBMISSION_RUN):
        return None

    if _field_exists(PAYMENT_ENTRY_DRAFT_RUN, "ndis_payment_entry_submission_run"):
        existing = frappe.db.get_value(
            PAYMENT_ENTRY_DRAFT_RUN,
            payment_entry_draft_run,
            "ndis_payment_entry_submission_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        PAYMENT_ENTRY_SUBMISSION_RUN,
        {"payment_entry_draft_run": payment_entry_draft_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(PAYMENT_ENTRY_SUBMISSION_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_payment_entry_submission_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_payment_entry_submission_run")
        if existing:
            return existing

    return frappe.db.get_value(PAYMENT_ENTRY_SUBMISSION_RUN, {"crm_deal": deal}, "name")


def _get_payment_entry_draft_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_payment_entry_draft_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_payment_entry_draft_run")
        if run:
            return run

    if _doctype_exists(PAYMENT_ENTRY_DRAFT_RUN):
        return frappe.db.get_value(PAYMENT_ENTRY_DRAFT_RUN, {"crm_deal": deal}, "name")

    return None


def _is_payment_entry_draft_created(run):
    if not run or not frappe.db.exists(PAYMENT_ENTRY_DRAFT_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        PAYMENT_ENTRY_DRAFT_RUN,
        run,
        ["status", "payment_entry_draft_run_ready"],
    )

    return status in SOURCE_READY_STATUSES and bool(ready)


def _is_payment_entry_submission_approved(run):
    if not run or not frappe.db.exists(PAYMENT_ENTRY_SUBMISSION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        PAYMENT_ENTRY_SUBMISSION_RUN,
        run,
        ["status", "payment_entry_submission_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _payment_entry_snapshot(payment_entry):
    if not payment_entry or not _doctype_exists(PAYMENT_ENTRY):
        return {}

    if not frappe.db.exists(PAYMENT_ENTRY, payment_entry):
        return {}

    return frappe.db.get_value(
        PAYMENT_ENTRY,
        payment_entry,
        [
            "name",
            "docstatus",
            "payment_type",
            "party_type",
            "party",
            "company",
            "posting_date",
            "paid_amount",
            "received_amount",
            "reference_no",
            "reference_date",
            "status",
        ],
        as_dict=True,
    ) or {}


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
        row.payment_entry_submission_source_key
        for row in doc.get("payment_entry_submission_lines") or []
        if row.get("payment_entry_submission_source_key")
    }

    key = row_data.get("payment_entry_submission_source_key")

    if key and key in existing:
        return False

    doc.append("payment_entry_submission_lines", row_data)
    return True


def _source_key(row):
    return row.get("payment_entry_source_key") or "|".join([
        str(row.get("payment_entry") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("ndis_remittance_import") or ""),
        str(row.get("actual_payment_reference") or ""),
    ])


def _build_submission_line_from_draft_line(row, source_doc):
    payment_entry_snapshot = _payment_entry_snapshot(row.get("payment_entry"))
    invoice_snapshot = _sales_invoice_snapshot(row.get("sales_invoice"))

    payment_amount = _to_float(row.get("proposed_payment_amount"))

    source_ready = bool(
        source_doc.get("status") == "Draft Payment Entries Created"
        and row.get("payment_entry_line_status") == "Draft Payment Entry Created"
        and row.get("payment_entry")
        and int(payment_entry_snapshot.get("docstatus") or 0) == 0
        and row.get("payment_entry_source_ready")
        and row.get("payment_entry_review_complete")
        and row.get("payment_entry_draft_authorized")
        and row.get("line_ready_for_payment_entry_draft")
        and not row.get("payment_entry_hold")
        and not row.get("payment_entry_submit_authorized")
        and not row.get("journal_authorized")
        and not row.get("write_off_authorized")
        and not row.get("recovery_authorized")
        and not row.get("bank_reconciliation_authorized")
        and payment_amount > 0
    )

    return {
        "payment_entry_submission_source_key": _source_key(row),
        "payment_entry": row.get("payment_entry"),
        "payment_entry_docstatus": int(payment_entry_snapshot.get("docstatus") or 0) if payment_entry_snapshot else row.get("payment_entry_docstatus"),
        "payment_entry_status": payment_entry_snapshot.get("status"),
        "payment_entry_type": payment_entry_snapshot.get("payment_type") or row.get("payment_entry_type"),
        "party_type": payment_entry_snapshot.get("party_type") or row.get("party_type"),
        "party": payment_entry_snapshot.get("party") or row.get("party"),
        "payment_entry_posting_date": payment_entry_snapshot.get("posting_date") or row.get("payment_entry_posting_date"),
        "payment_entry_reference_no": payment_entry_snapshot.get("reference_no") or row.get("payment_entry_reference_no"),
        "payment_entry_reference_date": payment_entry_snapshot.get("reference_date") or row.get("payment_entry_reference_date"),
        "proposed_payment_amount": payment_amount,
        "paid_amount": payment_entry_snapshot.get("paid_amount") or payment_amount,
        "received_amount": payment_entry_snapshot.get("received_amount") or payment_amount,
        "sales_invoice": row.get("sales_invoice"),
        "sales_invoice_docstatus": int(invoice_snapshot.get("docstatus") or 0) if invoice_snapshot else row.get("sales_invoice_docstatus"),
        "sales_invoice_status": invoice_snapshot.get("status") or row.get("sales_invoice_status"),
        "sales_invoice_outstanding_amount": invoice_snapshot.get("outstanding_amount") if invoice_snapshot else row.get("sales_invoice_outstanding_amount"),
        "ndis_remittance_import": row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"),
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
        "submission_source_ready": 1 if source_ready else 0,
        "payment_entry_submission_review_complete": 0,
        "payment_entry_submission_authorized": 0,
        "payment_entry_submit_authorized": 0,
        "journal_authorized": 0,
        "write_off_authorized": 0,
        "recovery_authorized": 0,
        "bank_reconciliation_authorized": 0,
        "submission_hold": 0 if source_ready else 1,
        "submission_hold_reason": None if source_ready else "Payment Entry draft source is not ready for controlled submission.",
        "line_ready_for_payment_entry_submission": 0,
        "payment_entry_submission_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_payment_entry_draft_run(doc, source):
    created = 0

    for row in source.get("payment_entry_lines") or []:
        if row.get("payment_entry_line_status") != "Draft Payment Entry Created":
            continue

        if not row.get("payment_entry"):
            continue

        data = _build_submission_line_from_draft_line(row, source)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _active_submission_lines(doc):
    return [
        row for row in doc.get("payment_entry_submission_lines") or []
        if row.get("payment_entry")
        and _to_float(row.get("proposed_payment_amount")) > 0
    ]


def _calculate_totals(doc):
    line_count = len(doc.get("payment_entry_submission_lines") or [])
    active_lines = _active_submission_lines(doc)

    amount_total = 0
    ready_count = 0
    submitted_payment_entries = set()
    draft_payment_entries = set()
    hold_count = 0

    blocked_submit_count = 0
    blocked_journal_count = 0
    blocked_writeoff_count = 0
    blocked_recovery_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("payment_entry_submission_lines") or []:
        amount_total += _to_float(row.get("proposed_payment_amount"))

        if row.get("line_ready_for_payment_entry_submission"):
            ready_count += 1

        if row.get("payment_entry"):
            if int(row.get("payment_entry_docstatus") or 0) == 1:
                submitted_payment_entries.add(row.get("payment_entry"))
            else:
                draft_payment_entries.add(row.get("payment_entry"))

        if row.get("submission_hold"):
            hold_count += 1

        if row.get("payment_entry_submit_authorized"):
            blocked_submit_count += 1

        if row.get("journal_authorized"):
            blocked_journal_count += 1

        if row.get("write_off_authorized"):
            blocked_writeoff_count += 1

        if row.get("recovery_authorized"):
            blocked_recovery_count += 1

        if row.get("bank_reconciliation_authorized"):
            blocked_bank_rec_count += 1

    return {
        "payment_entry_submission_line_count": line_count,
        "active_submission_line_count": len(active_lines),
        "payment_entry_submission_amount_total": round(amount_total, 2),
        "draft_payment_entry_count": len(draft_payment_entries),
        "submitted_payment_entry_count": len(submitted_payment_entries),
        "payment_entry_submission_ready_count": ready_count,
        "submission_hold_count": hold_count,
        "blocked_submit_authorization_count": blocked_submit_count,
        "blocked_journal_authorization_count": blocked_journal_count,
        "blocked_write_off_authorization_count": blocked_writeoff_count,
        "blocked_recovery_authorization_count": blocked_recovery_count,
        "blocked_bank_reconciliation_count": blocked_bank_rec_count,
    }


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(PAYMENT_ENTRY_SUBMISSION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Payment Entry Draft Run linked",
        "complete": bool(doc.get("payment_entry_draft_run")),
    })

    checks.append({
        "label": "Draft Payment Entries created",
        "complete": _is_payment_entry_draft_created(doc.get("payment_entry_draft_run")),
    })

    checks.append({
        "label": "Payment Entry DocType exists",
        "complete": _doctype_exists(PAYMENT_ENTRY),
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
        "label": "Payment Entry Submission Owner assigned",
        "complete": bool(doc.get("payment_entry_submission_owner")),
    })

    active_lines = _active_submission_lines(doc)

    checks.append({
        "label": "At least one active Payment Entry submission line exists",
        "complete": bool(active_lines),
    })

    missing_payment_entry = [row.service_line for row in active_lines if not row.get("payment_entry")]
    checks.append({
        "label": "All active lines have Payment Entry reference",
        "complete": not missing_payment_entry,
        "details": missing_payment_entry,
    })

    not_draft = []
    for row in active_lines:
        pe = row.get("payment_entry")
        if not pe:
            continue
        snapshot = _payment_entry_snapshot(pe)
        if int(snapshot.get("docstatus") or 0) != 0:
            not_draft.append(pe)

    checks.append({
        "label": "All active Payment Entries are still Draft before submission",
        "complete": not not_draft,
        "details": not_draft,
    })

    source_not_ready = [row.service_line for row in active_lines if not row.get("submission_source_ready")]
    checks.append({
        "label": "Payment Entry submission source-ready flags are complete",
        "complete": not source_not_ready,
        "details": source_not_ready,
    })

    review_missing = [row.service_line for row in active_lines if not row.get("payment_entry_submission_review_complete")]
    checks.append({
        "label": "Payment Entry submission review complete",
        "complete": not review_missing,
        "details": review_missing,
    })

    authorization_missing = [row.service_line for row in active_lines if not row.get("payment_entry_submission_authorized")]
    checks.append({
        "label": "Payment Entry submission authorization complete",
        "complete": not authorization_missing,
        "details": authorization_missing,
    })

    submit_flag_set = [row.service_line for row in active_lines if row.get("payment_entry_submit_authorized")]
    checks.append({
        "label": "Legacy direct submit flags remain blocked on lines",
        "complete": not submit_flag_set,
        "details": submit_flag_set,
    })

    journal_authorized = [row.service_line for row in active_lines if row.get("journal_authorized")]
    checks.append({
        "label": "Journal authorization remains blocked in Phase 29",
        "complete": not journal_authorized,
        "details": journal_authorized,
    })

    writeoff_authorized = [row.service_line for row in active_lines if row.get("write_off_authorized")]
    checks.append({
        "label": "Write-off authorization remains blocked in Phase 29",
        "complete": not writeoff_authorized,
        "details": writeoff_authorized,
    })

    recovery_authorized = [row.service_line for row in active_lines if row.get("recovery_authorized")]
    checks.append({
        "label": "Recovery authorization remains blocked in Phase 29",
        "complete": not recovery_authorized,
        "details": recovery_authorized,
    })

    bank_rec_authorized = [row.service_line for row in active_lines if row.get("bank_reconciliation_authorized")]
    checks.append({
        "label": "Bank reconciliation authorization remains blocked in Phase 29",
        "complete": not bank_rec_authorized,
        "details": bank_rec_authorized,
    })

    holds = [row.service_line for row in active_lines if row.get("submission_hold")]
    checks.append({
        "label": "No active Payment Entry submission hold remains",
        "complete": not holds,
        "details": holds,
    })

    not_ready = [row.service_line for row in active_lines if not row.get("line_ready_for_payment_entry_submission")]
    checks.append({
        "label": "All active lines marked ready for Payment Entry submission",
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
        "payment_entry_submission_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(PAYMENT_ENTRY_SUBMISSION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(PAYMENT_ENTRY_SUBMISSION_RUN, "payment_entry_submission_run_ready"):
        doc.payment_entry_submission_run_ready = 1 if summary["payment_entry_submission_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_payment_entry_submission_run", doc.name)
        _db_set_if_field(doctype, name, "payment_entry_submission_status", doc.status)
        _db_set_if_field(doctype, name, "payment_entry_submission_ready", 1 if summary["payment_entry_submission_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_payment_entry_submission_run_from_payment_entry_draft_run(payment_entry_draft_run):
    _check_role()

    if not payment_entry_draft_run:
        frappe.throw(_("NDIS CRM Payment Entry Draft Run is required."))

    if not frappe.db.exists(PAYMENT_ENTRY_DRAFT_RUN, payment_entry_draft_run):
        frappe.throw(_("NDIS CRM Payment Entry Draft Run {0} was not found.").format(payment_entry_draft_run))

    existing = _existing_run_for_payment_entry_draft_run(payment_entry_draft_run)
    if existing:
        return {
            "doctype": PAYMENT_ENTRY_SUBMISSION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Payment Entry Submission Run returned.",
        }

    source = frappe.get_doc(PAYMENT_ENTRY_DRAFT_RUN, payment_entry_draft_run)
    if not _is_payment_entry_draft_created(source.name):
        frappe.throw(_("Payment Entry Draft Run must have Draft Payment Entries Created before creating Payment Entry Submission Run."))

    doc = frappe.new_doc(PAYMENT_ENTRY_SUBMISSION_RUN)
    doc.status = "Draft"
    doc.payment_entry_draft_run = source.name
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
    doc.payment_entry_submission_owner = frappe.session.user
    doc.payment_entry_draft_owner = source.get("payment_entry_draft_owner")
    doc.payment_allocation_owner = source.get("payment_allocation_owner")
    doc.payment_entry_submission_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines_from_payment_entry_draft_run(doc, source)

    if _field_exists(PAYMENT_ENTRY_SUBMISSION_RUN, "payment_entry_submission_line_count"):
        doc.payment_entry_submission_line_count = created_count

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.payment_entry_submission_run_ready = 1 if summary["payment_entry_submission_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PAYMENT_ENTRY_SUBMISSION_RUN,
        "name": doc.name,
        "created": True,
        "payment_entry_submission_line_count": created_count,
        "message": "NDIS CRM Payment Entry Submission Run created successfully.",
    }


@frappe.whitelist()
def create_payment_entry_submission_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": PAYMENT_ENTRY_SUBMISSION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Payment Entry Submission Run returned.",
        }

    source_run = _get_payment_entry_draft_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please create NDIS CRM Payment Entry Draft Run before creating Payment Entry Submission Run."))

    return create_payment_entry_submission_run_from_payment_entry_draft_run(source_run)


@frappe.whitelist()
def generate_payment_entry_submission_lines(payment_entry_submission_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ENTRY_SUBMISSION_RUN, payment_entry_submission_run)

    if not doc.get("payment_entry_draft_run"):
        frappe.throw(_("Payment Entry Draft Run is required."))

    source = frappe.get_doc(PAYMENT_ENTRY_DRAFT_RUN, doc.payment_entry_draft_run)
    created_count = _generate_lines_from_payment_entry_draft_run(doc, source)

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Payment Entry submission lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_payment_entry_submission_readiness(payment_entry_submission_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ENTRY_SUBMISSION_RUN, payment_entry_submission_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Payment Entry Submission Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_payment_entry_submission(payment_entry_submission_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ENTRY_SUBMISSION_RUN, payment_entry_submission_run)
    summary = _calculate_readiness(doc)

    if not summary["payment_entry_submission_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Payment Entry Submission. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Payment Entry Submission"
    doc.readiness_percent = summary["readiness_percent"]
    doc.payment_entry_submission_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PAYMENT_ENTRY_SUBMISSION_RUN,
        "name": doc.name,
        "message": "Payment Entry Submission Run marked Ready.",
    }


@frappe.whitelist()
def approve_payment_entry_submission_run(payment_entry_submission_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ENTRY_SUBMISSION_RUN, payment_entry_submission_run)
    summary = _calculate_readiness(doc)

    if not summary["payment_entry_submission_run_ready"]:
        frappe.throw(
            _("Cannot approve Payment Entry Submission Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Payment Entry Submission Run Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.payment_entry_submission_run_ready = 1
    doc.payment_entry_submission_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("payment_entry_submission_lines") or []:
        if row.get("payment_entry_submission_line_status") in ["Draft", "Ready"]:
            row.payment_entry_submission_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PAYMENT_ENTRY_SUBMISSION_RUN,
        "name": doc.name,
        "message": "Payment Entry Submission Run approved. No Payment Entry has been submitted yet.",
    }


def _ready_lines_for_submission(doc):
    ready = []

    for row in _active_submission_lines(doc):
        if row.get("payment_entry_submission_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_payment_entry_submission"):
            continue

        if not row.get("payment_entry_submission_review_complete"):
            continue

        if not row.get("payment_entry_submission_authorized"):
            continue

        if row.get("payment_entry_submit_authorized"):
            continue

        if row.get("journal_authorized"):
            continue

        if row.get("write_off_authorized"):
            continue

        if row.get("recovery_authorized"):
            continue

        if row.get("bank_reconciliation_authorized"):
            continue

        if row.get("submission_hold"):
            continue

        pe_snapshot = _payment_entry_snapshot(row.get("payment_entry"))
        if int(pe_snapshot.get("docstatus") or 0) != 0:
            continue

        ready.append(row)

    return ready


def _unique_payment_entries(lines):
    out = []
    seen = set()

    for row in lines:
        pe = row.get("payment_entry")
        if not pe or pe in seen:
            continue

        seen.add(pe)
        out.append(pe)

    return out


def _link_submission_run_to_payment_entry(payment_entry_name, run_doc):
    pe = frappe.get_doc(PAYMENT_ENTRY, payment_entry_name)

    _set_first_existing(pe, ["ndis_crm_payment_entry_submission_run"], run_doc.name)
    _set_first_existing(pe, ["ndis_crm_payment_entry_submission_status"], "Submission In Progress")
    _set_first_existing(pe, ["ndis_crm_payment_entry_submission_approved"], 1)
    _set_first_existing(pe, ["ndis_crm_payment_entry_submission_blocked"], 0)
    _set_first_existing(pe, ["ndis_crm_payment_entry_status"], "Submission In Progress")

    pe.save(ignore_permissions=True)

    return pe


def _mark_payment_entry_submitted(payment_entry_name, run_doc):
    pe = frappe.get_doc(PAYMENT_ENTRY, payment_entry_name)

    _set_first_existing(pe, ["ndis_crm_payment_entry_submission_status"], "Submitted")
    _set_first_existing(pe, ["ndis_crm_payment_entry_status"], "Submitted")
    _set_first_existing(pe, ["ndis_crm_payment_entry_submitted_on"], now())
    _set_first_existing(pe, ["ndis_crm_payment_entry_submitted_by"], frappe.session.user)

    pe.save(ignore_permissions=True)


def _update_source_draft_lines(doc, submitted_payment_entries):
    if not doc.get("payment_entry_draft_run"):
        return

    if not frappe.db.exists(PAYMENT_ENTRY_DRAFT_RUN, doc.payment_entry_draft_run):
        return

    source = frappe.get_doc(PAYMENT_ENTRY_DRAFT_RUN, doc.payment_entry_draft_run)

    changed = False

    for row in source.get("payment_entry_lines") or []:
        if row.get("payment_entry") in submitted_payment_entries:
            row.payment_entry_docstatus = 1
            row.payment_entry_line_status = "Payment Entry Submitted"
            changed = True

    if changed:
        source.status = "Payment Entries Submitted"
        _set_if_field(source, "payment_entry_submission_allowed", 0)
        _set_if_field(source, "journal_creation_allowed", 0)
        _set_if_field(source, "write_off_creation_allowed", 0)
        _set_if_field(source, "recovery_creation_allowed", 0)
        _set_if_field(source, "bank_reconciliation_allowed", 0)
        source.save(ignore_permissions=True)


@frappe.whitelist()
def submit_payment_entries(payment_entry_submission_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ENTRY_SUBMISSION_RUN, payment_entry_submission_run)

    if doc.status != "Payment Entry Submission Run Approved":
        frappe.throw(_("Payment Entry Submission Run must be approved before submitting Payment Entries."))

    if not doc.get("payment_entry_submission_allowed"):
        frappe.throw(_("Tick Payment Entry Submission Allowed before submitting Payment Entries."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal Creation Allowed must remain unticked in Phase 29."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write Off Creation Allowed must remain unticked in Phase 29."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery Creation Allowed must remain unticked in Phase 29."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank Reconciliation Allowed must remain unticked in Phase 29."))

    summary = _calculate_readiness(doc)

    if not summary["payment_entry_submission_run_ready"]:
        frappe.throw(
            _("Cannot submit Payment Entries. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_submission(doc)

    if not ready_lines:
        frappe.throw(_("No ready Payment Entry submission lines found."))

    payment_entries = _unique_payment_entries(ready_lines)
    submitted = []

    for payment_entry_name in payment_entries:
        pe = _link_submission_run_to_payment_entry(payment_entry_name, doc)

        if getattr(pe, "docstatus", 0) != 0:
            frappe.throw(_("Payment Entry {0} is not in Draft state.").format(payment_entry_name))

        pe.submit()

        if getattr(pe, "docstatus", 0) != 1:
            frappe.throw(_("Payment Entry {0} was not submitted successfully.").format(payment_entry_name))

        _mark_payment_entry_submitted(payment_entry_name, doc)
        submitted.append(payment_entry_name)

    for row in doc.get("payment_entry_submission_lines") or []:
        if row.get("payment_entry") in submitted:
            row.payment_entry_docstatus = 1
            row.payment_entry_submission_line_status = "Payment Entry Submitted"

    doc.status = "Payment Entries Submitted"
    doc.payment_entry_submission_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.submitted_by = frappe.session.user
    doc.submitted_on = now()

    _sync_totals(doc)
    _update_source_draft_lines(doc, set(submitted))
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "submitted_payment_entries": submitted,
        "submitted_payment_entry_count": len(submitted),
        "message": "Payment Entries submitted through controlled Phase 29 gate. No Journal Entry, manual GL Entry, write-off, recovery, or bank reconciliation was created by Phase 29.",
    }


def validate_payment_entry_submission_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(PAYMENT_ENTRY_SUBMISSION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(PAYMENT_ENTRY_SUBMISSION_RUN, "payment_entry_submission_run_ready"):
        doc.payment_entry_submission_run_ready = 1 if summary["payment_entry_submission_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["payment_entry_submission_run_ready"]:
        frappe.throw(
            _("Cannot set Payment Entry Submission Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Payment Entry Submission Run Approved" and doc.get("payment_entry_submission_allowed"):
        frappe.throw(_("Payment Entry Submission Allowed can only be ticked after the run is approved."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal creation is not allowed in Phase 29."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write-off creation is not allowed in Phase 29."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery creation is not allowed in Phase 29."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank reconciliation is not allowed in Phase 29."))


def on_payment_entry_submission_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Payment Entry Submission Run Summary Sync Failed"
        )


def validate_payment_entry_phase29_submit_guard(doc, method=None):
    if not _field_exists(PAYMENT_ENTRY, "ndis_crm_payment_entry_draft_run"):
        return

    if not doc.get("ndis_crm_payment_entry_draft_run"):
        return

    submission_run = None

    if _field_exists(PAYMENT_ENTRY, "ndis_crm_payment_entry_submission_run"):
        submission_run = doc.get("ndis_crm_payment_entry_submission_run")

    if not submission_run:
        frappe.throw(
            _("This Payment Entry was created by NDIS CRM Phase 28. It can only be submitted through the controlled Phase 29 Payment Entry Submission Run.")
        )

    if not frappe.db.exists(PAYMENT_ENTRY_SUBMISSION_RUN, submission_run):
        frappe.throw(_("Linked Payment Entry Submission Run {0} was not found.").format(submission_run))

    status, ready, allowed = frappe.db.get_value(
        PAYMENT_ENTRY_SUBMISSION_RUN,
        submission_run,
        ["status", "payment_entry_submission_run_ready", "payment_entry_submission_allowed"],
    )

    if status != "Payment Entry Submission Run Approved" or not ready or not allowed:
        frappe.throw(
            _("Payment Entry can only be submitted while the linked Phase 29 submission run is approved, ready, and explicitly allowed.")
        )


def validate_crm_deal_phase29(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_payment_entry_submission_run_required"):
        required = doc.get("ndis_payment_entry_submission_run_required")

    if not required:
        return

    run = doc.get("ndis_payment_entry_submission_run") if _field_exists(CRM_DEAL, "ndis_payment_entry_submission_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Payment Entry Submission Run must be created and approved.")
        )

    if not _is_payment_entry_submission_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Payment Entry Submission Run must be approved.")
        )


def validate_crm_deal_phase29_combined(doc, method=None):
    """
    Preserve Phase 2-28 validator chain, then add optional Phase 29 Payment Entry Submission validation.
    """
    try:
        from ndis_crm.phase28_payment_entry_draft import validate_crm_deal_phase28_combined
        validate_crm_deal_phase28_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase27_payment_allocation_preparation import validate_crm_deal_phase27_combined
            validate_crm_deal_phase27_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase26_remittance_matching_review import validate_crm_deal_phase26_combined
                validate_crm_deal_phase26_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase29(doc, method)


def phase29_health_check():
    print("---- NDIS CRM Phase 29 Health Check ----")

    for dt in [
        PAYMENT_ENTRY_SUBMISSION_LINE,
        PAYMENT_ENTRY_SUBMISSION_RUN,
        PAYMENT_ENTRY_DRAFT_RUN,
        PAYMENT_ENTRY_DRAFT_LINE,
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
        PAYMENT_ENTRY_REFERENCE,
        NDIS_REMITTANCE_IMPORT,
        NDIS_CLAIM_BATCH,
        NDIS_CLAIM_LINE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for dt in [
        "Journal Entry",
        "GL Entry",
        "Bank Reconciliation Tool",
        "NDIS Recovery Case",
        "NDIS Write Off",
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_payment_entry_submission_run_required",
        "ndis_payment_entry_submission_run",
        "payment_entry_submission_status",
        "payment_entry_submission_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    for field in [
        "ndis_crm_payment_entry_submission_run",
        "ndis_crm_payment_entry_submission_status",
        "ndis_crm_payment_entry_submission_approved",
        "ndis_crm_payment_entry_submitted_on",
        "ndis_crm_payment_entry_submitted_by",
    ]:
        print(f"Payment Entry field {field}: {'OK' if _field_exists(PAYMENT_ENTRY, field) else 'MISSING'}")

    print("NDIS CRM Payment Entry Submission Run records:", frappe.db.count(PAYMENT_ENTRY_SUBMISSION_RUN) if _doctype_exists(PAYMENT_ENTRY_SUBMISSION_RUN) else 0)
    print("Phase 29 may submit existing Phase 28 draft Payment Entries only.")
    print("Phase 29 does not create new Payment Entries, Journal Entries, write-offs, recovery cases, bank reconciliation records, or manual GL Entries.")
    print("ERPNext standard GL entries may be generated by Payment Entry submit; that is the intended controlled accounting effect.")
    print("---- End Phase 29 Health Check ----")
