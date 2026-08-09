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
REMITTANCE_IMPORT_FINALISATION_LINE = "NDIS CRM Remittance Import Finalisation Line"

VARIANCE_REJECTION_REVIEW_RUN = "NDIS CRM Variance Rejection Review Run"
VARIANCE_REJECTION_REVIEW_LINE = "NDIS CRM Variance Rejection Review Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"

READY_STATUSES = [
    "Ready for Variance Rejection Review",
    "Variance Rejection Review Approved",
    "Variance Rejection Review Completed",
]

APPROVED_STATUSES = [
    "Variance Rejection Review Approved",
    "Variance Rejection Review Completed",
]

SOURCE_READY_STATUSES = [
    "Remittance Import Finalised",
    "Remittance Import Submitted",
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
        frappe.throw(_("You do not have permission to perform this variance/rejection review action."))


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


def _existing_run_for_finalisation_run(remittance_import_finalisation_run):
    if not _doctype_exists(VARIANCE_REJECTION_REVIEW_RUN):
        return None

    if _field_exists(REMITTANCE_IMPORT_FINALISATION_RUN, "ndis_variance_rejection_review_run"):
        existing = frappe.db.get_value(
            REMITTANCE_IMPORT_FINALISATION_RUN,
            remittance_import_finalisation_run,
            "ndis_variance_rejection_review_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        VARIANCE_REJECTION_REVIEW_RUN,
        {"remittance_import_finalisation_run": remittance_import_finalisation_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(VARIANCE_REJECTION_REVIEW_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_variance_rejection_review_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_variance_rejection_review_run")
        if existing:
            return existing

    return frappe.db.get_value(VARIANCE_REJECTION_REVIEW_RUN, {"crm_deal": deal}, "name")


def _get_finalisation_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_remittance_import_finalisation_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_remittance_import_finalisation_run")
        if run:
            return run

    if _doctype_exists(REMITTANCE_IMPORT_FINALISATION_RUN):
        return frappe.db.get_value(REMITTANCE_IMPORT_FINALISATION_RUN, {"crm_deal": deal}, "name")

    return None


def _is_remittance_finalised(run):
    if not run or not frappe.db.exists(REMITTANCE_IMPORT_FINALISATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        REMITTANCE_IMPORT_FINALISATION_RUN,
        run,
        ["status", "remittance_import_finalisation_run_ready"],
    )

    return status in SOURCE_READY_STATUSES and bool(ready)


def _is_variance_review_approved(run):
    if not run or not frappe.db.exists(VARIANCE_REJECTION_REVIEW_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        VARIANCE_REJECTION_REVIEW_RUN,
        run,
        ["status", "variance_rejection_review_run_ready"],
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


def _remittance_import_snapshot(ndis_remittance_import):
    if not ndis_remittance_import or not _doctype_exists(NDIS_REMITTANCE_IMPORT):
        return {}

    if not frappe.db.exists(NDIS_REMITTANCE_IMPORT, ndis_remittance_import):
        return {}

    out = {"name": ndis_remittance_import}

    for fieldname in [
        "docstatus",
        "status",
        "import_status",
        "remittance_status",
        "company",
        "participant_customer",
        "customer",
        "payment_reference",
        "remittance_reference",
        "allocated_amount_total",
        "proposed_allocation_amount_total",
        "matched_amount_total",
        "variance_amount_total",
    ]:
        if _field_exists(NDIS_REMITTANCE_IMPORT, fieldname):
            out[fieldname] = frappe.db.get_value(NDIS_REMITTANCE_IMPORT, ndis_remittance_import, fieldname)

    return out


def _append_line_if_missing(doc, row_data):
    existing = {
        row.variance_review_source_key
        for row in doc.get("variance_review_lines") or []
        if row.get("variance_review_source_key")
    }

    key = row_data.get("variance_review_source_key")

    if key and key in existing:
        return False

    doc.append("variance_review_lines", row_data)
    return True


def _source_key(row):
    return row.get("payment_allocation_source_key") or "|".join([
        str(row.get("service_line") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("ndis_remittance_import") or ""),
        str(row.get("actual_payment_reference") or ""),
        str(row.get("allocation_type") or ""),
    ])


def _is_exception_allocation_line(row):
    allocation_type = row.get("allocation_type")
    matching_result = row.get("matching_result")
    proposed = _to_float(row.get("proposed_allocation_amount"))
    short_paid = _to_float(row.get("short_paid_amount"))
    overpaid = _to_float(row.get("overpaid_amount"))
    rejected = _to_float(row.get("rejected_amount"))
    actual_rejected = _to_float(row.get("actual_rejected_amount"))
    variance = _to_float(row.get("variance_amount"))

    if row.get("requires_manual_review"):
        return True

    if short_paid or overpaid or rejected or actual_rejected:
        return True

    if allocation_type and allocation_type not in ["Full Payment Allocation"]:
        return True

    if matching_result and matching_result not in ["Full Payment Match"]:
        return True

    if variance:
        return True

    if proposed <= 0 and allocation_type != "Full Payment Allocation":
        return True

    return False


def _review_category(row):
    allocation_type = row.get("allocation_type")
    matching_result = row.get("matching_result")
    short_paid = _to_float(row.get("short_paid_amount"))
    overpaid = _to_float(row.get("overpaid_amount"))
    rejected = _to_float(row.get("rejected_amount"))
    actual_rejected = _to_float(row.get("actual_rejected_amount"))

    if rejected or actual_rejected or allocation_type == "No Payment / Rejected" or matching_result == "Rejected":
        return "Rejected Claim"

    if overpaid or allocation_type == "Overpayment Review" or matching_result == "Overpayment":
        return "Overpayment"

    if short_paid or allocation_type in ["Partial Payment Allocation", "Underpayment Review"] or matching_result in ["Partial Payment", "Underpayment"]:
        return "Short Payment"

    if matching_result == "Unmatched":
        return "Unmatched"

    if row.get("requires_manual_review") or allocation_type == "Manual Review" or matching_result == "Manual Review":
        return "Manual Review"

    return "Variance Investigation"


def _recommended_resolution(row, category):
    short_paid = _to_float(row.get("short_paid_amount"))
    overpaid = _to_float(row.get("overpaid_amount"))
    rejected = _to_float(row.get("rejected_amount")) or _to_float(row.get("actual_rejected_amount"))

    if category == "Rejected Claim":
        if rejected:
            return "Prepare Rejection Follow-up"
        return "Manual Rejection Review"

    if category == "Short Payment":
        if short_paid:
            return "Prepare Recovery Review"
        return "Short Payment Review"

    if category == "Overpayment":
        if overpaid:
            return "Prepare Overpayment Adjustment Review"
        return "Overpayment Review"

    if category == "Unmatched":
        return "Manual Matching Investigation"

    if category == "Manual Review":
        return "Manual Review Required"

    return "Variance Investigation"


def _candidate_flags(category, row):
    short_paid = _to_float(row.get("short_paid_amount"))
    overpaid = _to_float(row.get("overpaid_amount"))
    rejected = _to_float(row.get("rejected_amount")) or _to_float(row.get("actual_rejected_amount"))

    return {
        "write_off_candidate": 1 if category in ["Rejected Claim", "Short Payment"] and (short_paid or rejected) else 0,
        "recovery_candidate": 1 if category in ["Short Payment", "Rejected Claim"] and (short_paid or rejected) else 0,
        "adjustment_candidate": 1 if category == "Overpayment" and overpaid else 0,
        "dispute_candidate": 1 if category in ["Rejected Claim", "Unmatched", "Manual Review", "Variance Investigation"] else 0,
        "bank_reconciliation_candidate": 1 if category == "Overpayment" else 0,
    }


def _build_review_line_from_allocation_line(row, source_doc):
    invoice_snapshot = _sales_invoice_snapshot(row.get("sales_invoice"))
    payment_entry = row.get("payment_entry")
    payment_entry_snapshot = _payment_entry_snapshot(payment_entry)
    remittance_snapshot = _remittance_import_snapshot(row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"))

    category = _review_category(row)
    recommended_resolution = _recommended_resolution(row, category)
    flags = _candidate_flags(category, row)

    source_ready = bool(
        source_doc.get("status") in SOURCE_READY_STATUSES
        and row.get("payment_allocation_line_status") == "Payment Allocation Prepared"
        and row.get("payment_allocation_review_complete")
        and row.get("allocation_decision_authorized")
        and not row.get("payment_entry_authorized")
        and not row.get("journal_authorized")
        and not row.get("write_off_authorized")
        and not row.get("recovery_authorized")
        and row.get("ndis_remittance_import")
    )

    return {
        "variance_review_source_key": _source_key(row),
        "ndis_remittance_import": row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"),
        "ndis_remittance_import_docstatus": int(remittance_snapshot.get("docstatus") or 0) if remittance_snapshot else None,
        "ndis_remittance_import_status": remittance_snapshot.get("status") or remittance_snapshot.get("import_status") or remittance_snapshot.get("remittance_status"),
        "payment_entry": payment_entry,
        "payment_entry_docstatus": int(payment_entry_snapshot.get("docstatus") or 0) if payment_entry_snapshot else None,
        "payment_entry_status": payment_entry_snapshot.get("status") if payment_entry_snapshot else None,
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
        "matching_result": row.get("matching_result"),
        "allocation_type": row.get("allocation_type"),
        "claim_amount": row.get("claim_amount"),
        "expected_paid_amount": row.get("expected_paid_amount"),
        "actual_paid_amount": row.get("actual_paid_amount"),
        "actual_rejected_amount": row.get("actual_rejected_amount"),
        "variance_amount": row.get("variance_amount"),
        "proposed_allocation_amount": row.get("proposed_allocation_amount"),
        "short_paid_amount": row.get("short_paid_amount"),
        "overpaid_amount": row.get("overpaid_amount"),
        "rejected_amount": row.get("rejected_amount"),
        "review_category": category,
        "recommended_resolution": recommended_resolution,
        "write_off_candidate": flags["write_off_candidate"],
        "recovery_candidate": flags["recovery_candidate"],
        "adjustment_candidate": flags["adjustment_candidate"],
        "dispute_candidate": flags["dispute_candidate"],
        "bank_reconciliation_candidate": flags["bank_reconciliation_candidate"],
        "variance_review_source_ready": 1 if source_ready else 0,
        "variance_review_complete": 0,
        "variance_decision_authorized": 0,
        "write_off_authorized": 0,
        "recovery_authorized": 0,
        "adjustment_authorized": 0,
        "journal_authorized": 0,
        "bank_reconciliation_authorized": 0,
        "variance_review_hold": 0 if source_ready else 1,
        "variance_review_hold_reason": None if source_ready else "Payment allocation/remittance finalisation source is not ready for variance review.",
        "line_ready_for_variance_review_completion": 0,
        "variance_review_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_sources(doc, finalisation_doc):
    created = 0

    if not doc.get("payment_allocation_preparation_run"):
        return created

    if not frappe.db.exists(PAYMENT_ALLOCATION_PREP_RUN, doc.payment_allocation_preparation_run):
        return created

    allocation_doc = frappe.get_doc(PAYMENT_ALLOCATION_PREP_RUN, doc.payment_allocation_preparation_run)

    synthetic_source = {
        "status": finalisation_doc.get("status"),
        "ndis_remittance_import": finalisation_doc.get("ndis_remittance_import"),
    }

    class SourceAdapter(dict):
        def get(self, key, default=None):
            return super().get(key, default)

    source_adapter = SourceAdapter(synthetic_source)

    for row in allocation_doc.get("payment_allocation_lines") or []:
        if row.get("payment_allocation_line_status") != "Payment Allocation Prepared":
            continue

        if not _is_exception_allocation_line(row):
            continue

        data = _build_review_line_from_allocation_line(row, source_adapter)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _active_review_lines(doc):
    return list(doc.get("variance_review_lines") or [])


def _calculate_totals(doc):
    line_count = len(doc.get("variance_review_lines") or [])
    amount_total = 0
    short_total = 0
    overpaid_total = 0
    rejected_total = 0
    ready_count = 0
    hold_count = 0
    rejection_count = 0
    short_count = 0
    overpaid_count = 0
    manual_count = 0
    unmatched_count = 0
    variance_count = 0

    write_off_candidate_count = 0
    recovery_candidate_count = 0
    adjustment_candidate_count = 0
    dispute_candidate_count = 0
    bank_rec_candidate_count = 0

    blocked_writeoff_count = 0
    blocked_recovery_count = 0
    blocked_adjustment_count = 0
    blocked_journal_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("variance_review_lines") or []:
        amount_total += _to_float(row.get("variance_amount"))
        short_total += _to_float(row.get("short_paid_amount"))
        overpaid_total += _to_float(row.get("overpaid_amount"))
        rejected_total += _to_float(row.get("rejected_amount")) or _to_float(row.get("actual_rejected_amount"))

        if row.get("line_ready_for_variance_review_completion"):
            ready_count += 1

        if row.get("variance_review_hold"):
            hold_count += 1

        category = row.get("review_category")
        if category == "Rejected Claim":
            rejection_count += 1
        elif category == "Short Payment":
            short_count += 1
        elif category == "Overpayment":
            overpaid_count += 1
        elif category == "Manual Review":
            manual_count += 1
        elif category == "Unmatched":
            unmatched_count += 1
        elif category == "Variance Investigation":
            variance_count += 1

        if row.get("write_off_candidate"):
            write_off_candidate_count += 1
        if row.get("recovery_candidate"):
            recovery_candidate_count += 1
        if row.get("adjustment_candidate"):
            adjustment_candidate_count += 1
        if row.get("dispute_candidate"):
            dispute_candidate_count += 1
        if row.get("bank_reconciliation_candidate"):
            bank_rec_candidate_count += 1

        if row.get("write_off_authorized"):
            blocked_writeoff_count += 1
        if row.get("recovery_authorized"):
            blocked_recovery_count += 1
        if row.get("adjustment_authorized"):
            blocked_adjustment_count += 1
        if row.get("journal_authorized"):
            blocked_journal_count += 1
        if row.get("bank_reconciliation_authorized"):
            blocked_bank_rec_count += 1

    return {
        "variance_review_line_count": line_count,
        "variance_amount_total": round(amount_total, 2),
        "short_paid_amount_total": round(short_total, 2),
        "overpaid_amount_total": round(overpaid_total, 2),
        "rejected_amount_total": round(rejected_total, 2),
        "variance_review_ready_count": ready_count,
        "variance_review_hold_count": hold_count,
        "rejected_claim_count": rejection_count,
        "short_payment_count": short_count,
        "overpayment_count": overpaid_count,
        "manual_review_count": manual_count,
        "unmatched_count": unmatched_count,
        "variance_investigation_count": variance_count,
        "write_off_candidate_count": write_off_candidate_count,
        "recovery_candidate_count": recovery_candidate_count,
        "adjustment_candidate_count": adjustment_candidate_count,
        "dispute_candidate_count": dispute_candidate_count,
        "bank_reconciliation_candidate_count": bank_rec_candidate_count,
        "blocked_write_off_authorization_count": blocked_writeoff_count,
        "blocked_recovery_authorization_count": blocked_recovery_count,
        "blocked_adjustment_authorization_count": blocked_adjustment_count,
        "blocked_journal_authorization_count": blocked_journal_count,
        "blocked_bank_reconciliation_count": blocked_bank_rec_count,
    }


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(VARIANCE_REJECTION_REVIEW_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Remittance Import Finalisation Run linked",
        "complete": bool(doc.get("remittance_import_finalisation_run")),
    })

    checks.append({
        "label": "Remittance Import finalised/submitted",
        "complete": _is_remittance_finalised(doc.get("remittance_import_finalisation_run")),
    })

    checks.append({
        "label": "Payment Allocation Preparation Run linked",
        "complete": bool(doc.get("payment_allocation_preparation_run")),
    })

    checks.append({
        "label": "NDIS Remittance Import linked",
        "complete": bool(doc.get("ndis_remittance_import")),
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
        "label": "Variance Review Owner assigned",
        "complete": bool(doc.get("variance_review_owner")),
    })

    lines = _active_review_lines(doc)
    no_exceptions = bool(doc.get("no_variance_or_rejection_found"))

    checks.append({
        "label": "Variance/rejection lines exist or no-exception flag is set",
        "complete": bool(lines) or no_exceptions,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("variance_review_source_ready")]
        checks.append({
            "label": "Variance review source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        missing_category = [row.service_line for row in lines if not row.get("review_category")]
        checks.append({
            "label": "All lines have review category",
            "complete": not missing_category,
            "details": missing_category,
        })

        review_missing = [row.service_line for row in lines if not row.get("variance_review_complete")]
        checks.append({
            "label": "Variance review complete",
            "complete": not review_missing,
            "details": review_missing,
        })

        decision_missing = [row.service_line for row in lines if not row.get("variance_decision_authorized")]
        checks.append({
            "label": "Variance decision authorization complete",
            "complete": not decision_missing,
            "details": decision_missing,
        })

        writeoff_authorized = [row.service_line for row in lines if row.get("write_off_authorized")]
        checks.append({
            "label": "Write-off authorization remains blocked in Phase 31",
            "complete": not writeoff_authorized,
            "details": writeoff_authorized,
        })

        recovery_authorized = [row.service_line for row in lines if row.get("recovery_authorized")]
        checks.append({
            "label": "Recovery authorization remains blocked in Phase 31",
            "complete": not recovery_authorized,
            "details": recovery_authorized,
        })

        adjustment_authorized = [row.service_line for row in lines if row.get("adjustment_authorized")]
        checks.append({
            "label": "Adjustment authorization remains blocked in Phase 31",
            "complete": not adjustment_authorized,
            "details": adjustment_authorized,
        })

        journal_authorized = [row.service_line for row in lines if row.get("journal_authorized")]
        checks.append({
            "label": "Journal authorization remains blocked in Phase 31",
            "complete": not journal_authorized,
            "details": journal_authorized,
        })

        bank_rec_authorized = [row.service_line for row in lines if row.get("bank_reconciliation_authorized")]
        checks.append({
            "label": "Bank reconciliation authorization remains blocked in Phase 31",
            "complete": not bank_rec_authorized,
            "details": bank_rec_authorized,
        })

        holds = [row.service_line for row in lines if row.get("variance_review_hold")]
        checks.append({
            "label": "No active variance review hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_variance_review_completion")]
        checks.append({
            "label": "All active lines marked ready for variance review completion",
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
        "variance_rejection_review_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(VARIANCE_REJECTION_REVIEW_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(VARIANCE_REJECTION_REVIEW_RUN, "variance_rejection_review_run_ready"):
        doc.variance_rejection_review_run_ready = 1 if summary["variance_rejection_review_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_variance_rejection_review_run", doc.name)
        _db_set_if_field(doctype, name, "variance_rejection_review_status", doc.status)
        _db_set_if_field(doctype, name, "variance_rejection_review_ready", 1 if summary["variance_rejection_review_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_variance_rejection_review_run_from_finalisation_run(remittance_import_finalisation_run):
    _check_role()

    if not remittance_import_finalisation_run:
        frappe.throw(_("NDIS CRM Remittance Import Finalisation Run is required."))

    if not frappe.db.exists(REMITTANCE_IMPORT_FINALISATION_RUN, remittance_import_finalisation_run):
        frappe.throw(_("NDIS CRM Remittance Import Finalisation Run {0} was not found.").format(remittance_import_finalisation_run))

    existing = _existing_run_for_finalisation_run(remittance_import_finalisation_run)
    if existing:
        return {
            "doctype": VARIANCE_REJECTION_REVIEW_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Variance Rejection Review Run returned.",
        }

    source = frappe.get_doc(REMITTANCE_IMPORT_FINALISATION_RUN, remittance_import_finalisation_run)

    doc = frappe.new_doc(VARIANCE_REJECTION_REVIEW_RUN)
    doc.status = "Draft"
    doc.remittance_import_finalisation_run = source.name
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
    doc.variance_review_owner = frappe.session.user
    doc.remittance_finalisation_owner = source.get("remittance_finalisation_owner")
    doc.payment_entry_submission_owner = source.get("payment_entry_submission_owner")
    doc.variance_review_completion_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines_from_sources(doc, source)

    if created_count == 0:
        doc.no_variance_or_rejection_found = 1
    else:
        doc.no_variance_or_rejection_found = 0

    if _field_exists(VARIANCE_REJECTION_REVIEW_RUN, "variance_review_line_count"):
        doc.variance_review_line_count = created_count

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.variance_rejection_review_run_ready = 1 if summary["variance_rejection_review_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": VARIANCE_REJECTION_REVIEW_RUN,
        "name": doc.name,
        "created": True,
        "variance_review_line_count": created_count,
        "no_variance_or_rejection_found": bool(doc.no_variance_or_rejection_found),
        "message": "NDIS CRM Variance Rejection Review Run created successfully.",
    }


@frappe.whitelist()
def create_variance_rejection_review_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": VARIANCE_REJECTION_REVIEW_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Variance Rejection Review Run returned.",
        }

    source_run = _get_finalisation_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Remittance Import Finalisation Run before creating Variance Rejection Review Run."))

    return create_variance_rejection_review_run_from_finalisation_run(source_run)


@frappe.whitelist()
def generate_variance_rejection_review_lines(variance_rejection_review_run):
    _check_role()

    doc = frappe.get_doc(VARIANCE_REJECTION_REVIEW_RUN, variance_rejection_review_run)

    if not doc.get("remittance_import_finalisation_run"):
        frappe.throw(_("Remittance Import Finalisation Run is required."))

    source = frappe.get_doc(REMITTANCE_IMPORT_FINALISATION_RUN, doc.remittance_import_finalisation_run)
    created_count = _generate_lines_from_sources(doc, source)

    if created_count == 0 and not doc.get("variance_review_lines"):
        doc.no_variance_or_rejection_found = 1
    else:
        doc.no_variance_or_rejection_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Variance/rejection review lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_variance_rejection_review_readiness(variance_rejection_review_run):
    _check_role()

    doc = frappe.get_doc(VARIANCE_REJECTION_REVIEW_RUN, variance_rejection_review_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Variance Rejection Review Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_variance_rejection_review(variance_rejection_review_run):
    _check_role()

    doc = frappe.get_doc(VARIANCE_REJECTION_REVIEW_RUN, variance_rejection_review_run)
    summary = _calculate_readiness(doc)

    if not summary["variance_rejection_review_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Variance Rejection Review. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Variance Rejection Review"
    doc.readiness_percent = summary["readiness_percent"]
    doc.variance_rejection_review_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": VARIANCE_REJECTION_REVIEW_RUN,
        "name": doc.name,
        "message": "Variance Rejection Review Run marked Ready.",
    }


@frappe.whitelist()
def approve_variance_rejection_review_run(variance_rejection_review_run):
    _check_role()

    doc = frappe.get_doc(VARIANCE_REJECTION_REVIEW_RUN, variance_rejection_review_run)
    summary = _calculate_readiness(doc)

    if not summary["variance_rejection_review_run_ready"]:
        frappe.throw(
            _("Cannot approve Variance Rejection Review Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Variance Rejection Review Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.variance_rejection_review_run_ready = 1
    doc.variance_review_completion_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("variance_review_lines") or []:
        if row.get("variance_review_line_status") in ["Draft", "Ready"]:
            row.variance_review_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": VARIANCE_REJECTION_REVIEW_RUN,
        "name": doc.name,
        "message": "Variance Rejection Review Run approved. No write-off, recovery, adjustment, journal, bank reconciliation, or GL action was performed.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_review_lines(doc):
        if row.get("variance_review_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_variance_review_completion"):
            continue

        if not row.get("variance_review_complete"):
            continue

        if not row.get("variance_decision_authorized"):
            continue

        if row.get("write_off_authorized"):
            continue

        if row.get("recovery_authorized"):
            continue

        if row.get("adjustment_authorized"):
            continue

        if row.get("journal_authorized"):
            continue

        if row.get("bank_reconciliation_authorized"):
            continue

        if row.get("variance_review_hold"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_variance_rejection_review(variance_rejection_review_run):
    _check_role()

    doc = frappe.get_doc(VARIANCE_REJECTION_REVIEW_RUN, variance_rejection_review_run)

    if doc.status != "Variance Rejection Review Approved":
        frappe.throw(_("Variance Rejection Review Run must be approved before completion."))

    if not doc.get("variance_review_completion_allowed"):
        frappe.throw(_("Tick Variance Review Completion Allowed before completing this review."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write Off Creation Allowed must remain unticked in Phase 31."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery Creation Allowed must remain unticked in Phase 31."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment Creation Allowed must remain unticked in Phase 31."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal Creation Allowed must remain unticked in Phase 31."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank Reconciliation Allowed must remain unticked in Phase 31."))

    summary = _calculate_readiness(doc)

    if not summary["variance_rejection_review_run_ready"]:
        frappe.throw(
            _("Cannot complete Variance Rejection Review. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines and not doc.get("no_variance_or_rejection_found"):
        frappe.throw(_("No ready variance/rejection review lines found."))

    for row in ready_lines:
        row.variance_review_line_status = "Variance Review Completed"

    doc.status = "Variance Rejection Review Completed"
    doc.variance_review_completion_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "completed_line_count": len(ready_lines),
        "no_variance_or_rejection_found": bool(doc.get("no_variance_or_rejection_found")),
        "message": "Variance/rejection review completed. No Journal Entry, write-off, recovery, adjustment, bank reconciliation, Payment Entry, or manual GL was created.",
    }


def validate_variance_rejection_review_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(VARIANCE_REJECTION_REVIEW_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(VARIANCE_REJECTION_REVIEW_RUN, "variance_rejection_review_run_ready"):
        doc.variance_rejection_review_run_ready = 1 if summary["variance_rejection_review_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["variance_rejection_review_run_ready"]:
        frappe.throw(
            _("Cannot set Variance Rejection Review Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Variance Rejection Review Approved" and doc.get("variance_review_completion_allowed"):
        frappe.throw(_("Variance Review Completion Allowed can only be ticked after the run is approved."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write-off creation is not allowed in Phase 31."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery creation is not allowed in Phase 31."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment creation is not allowed in Phase 31."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal creation is not allowed in Phase 31."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank reconciliation is not allowed in Phase 31."))


def on_variance_rejection_review_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Variance Rejection Review Run Summary Sync Failed"
        )


def validate_crm_deal_phase31(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_variance_rejection_review_run_required"):
        required = doc.get("ndis_variance_rejection_review_run_required")

    if not required:
        return

    run = doc.get("ndis_variance_rejection_review_run") if _field_exists(CRM_DEAL, "ndis_variance_rejection_review_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Variance Rejection Review Run must be created and approved/completed.")
        )

    if not _is_variance_review_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Variance Rejection Review Run must be approved/completed.")
        )


def validate_crm_deal_phase31_combined(doc, method=None):
    """
    Preserve Phase 2-30 validator chain, then add optional Phase 31 Variance/Rejection Review validation.
    """
    try:
        from ndis_crm.phase30_remittance_import_finalisation import validate_crm_deal_phase30_combined
        validate_crm_deal_phase30_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase29_payment_entry_submission import validate_crm_deal_phase29_combined
            validate_crm_deal_phase29_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase28_payment_entry_draft import validate_crm_deal_phase28_combined
                validate_crm_deal_phase28_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase31(doc, method)


def phase31_health_check():
    print("---- NDIS CRM Phase 31 Health Check ----")

    for dt in [
        VARIANCE_REJECTION_REVIEW_LINE,
        VARIANCE_REJECTION_REVIEW_RUN,
        REMITTANCE_IMPORT_FINALISATION_RUN,
        REMITTANCE_IMPORT_FINALISATION_LINE,
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
        "ndis_variance_rejection_review_run_required",
        "ndis_variance_rejection_review_run",
        "variance_rejection_review_status",
        "variance_rejection_review_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print("NDIS CRM Variance Rejection Review Run records:", frappe.db.count(VARIANCE_REJECTION_REVIEW_RUN) if _doctype_exists(VARIANCE_REJECTION_REVIEW_RUN) else 0)
    print("Phase 31 creates CRM variance/rejection review records only.")
    print("Phase 31 does not create Payment Entry, Journal Entry, write-off, recovery, adjustment, bank reconciliation, Sales Invoice, Claim Batch, Claim Line, or manual GL.")
    print("---- End Phase 31 Health Check ----")
