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
RECOVERY_PREPARATION_LINE = "NDIS CRM Recovery Preparation Line"

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
    "Ready for Recovery Preparation",
    "Recovery Preparation Approved",
    "Recovery Prepared",
]

APPROVED_STATUSES = [
    "Recovery Preparation Approved",
    "Recovery Prepared",
]

SOURCE_READY_STATUSES = {
    VARIANCE_REJECTION_REVIEW_RUN: ["Variance Rejection Review Completed"],
    WRITE_OFF_FINALISATION_RUN: ["Write Off Finalised"],
}

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
        frappe.throw(_("You do not have permission to perform this recovery preparation action."))


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


def _text(value):
    return str(value or "").strip()


def _lower(value):
    return _text(value).lower()


def _contains_any(value, needles):
    haystack = _lower(value)
    return any(needle in haystack for needle in needles)


def _existing_run_for_variance_review_run(variance_rejection_review_run):
    if not _doctype_exists(RECOVERY_PREPARATION_RUN):
        return None

    if _field_exists(VARIANCE_REJECTION_REVIEW_RUN, "ndis_recovery_preparation_run"):
        existing = frappe.db.get_value(
            VARIANCE_REJECTION_REVIEW_RUN,
            variance_rejection_review_run,
            "ndis_recovery_preparation_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        RECOVERY_PREPARATION_RUN,
        {"variance_rejection_review_run": variance_rejection_review_run},
        "name",
    )


def _existing_run_for_write_off_finalisation_run(write_off_finalisation_run):
    if not _doctype_exists(RECOVERY_PREPARATION_RUN):
        return None

    if _field_exists(WRITE_OFF_FINALISATION_RUN, "ndis_recovery_preparation_run"):
        existing = frappe.db.get_value(
            WRITE_OFF_FINALISATION_RUN,
            write_off_finalisation_run,
            "ndis_recovery_preparation_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        RECOVERY_PREPARATION_RUN,
        {"write_off_finalisation_run": write_off_finalisation_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(RECOVERY_PREPARATION_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_recovery_preparation_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_recovery_preparation_run")
        if existing:
            return existing

    return frappe.db.get_value(RECOVERY_PREPARATION_RUN, {"crm_deal": deal}, "name")


def _get_best_source_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_write_off_finalisation_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_write_off_finalisation_run")
        if run:
            return WRITE_OFF_FINALISATION_RUN, run

    if _field_exists(CRM_DEAL, "ndis_variance_rejection_review_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_variance_rejection_review_run")
        if run:
            return VARIANCE_REJECTION_REVIEW_RUN, run

    if _doctype_exists(WRITE_OFF_FINALISATION_RUN):
        run = frappe.db.get_value(WRITE_OFF_FINALISATION_RUN, {"crm_deal": deal}, "name")
        if run:
            return WRITE_OFF_FINALISATION_RUN, run

    if _doctype_exists(VARIANCE_REJECTION_REVIEW_RUN):
        run = frappe.db.get_value(VARIANCE_REJECTION_REVIEW_RUN, {"crm_deal": deal}, "name")
        if run:
            return VARIANCE_REJECTION_REVIEW_RUN, run

    return None, None


def _is_source_completed(source_doctype, source_name):
    if not source_doctype or not source_name:
        return False

    if not frappe.db.exists(source_doctype, source_name):
        return False

    ready_field = {
        VARIANCE_REJECTION_REVIEW_RUN: "variance_rejection_review_run_ready",
        WRITE_OFF_FINALISATION_RUN: "write_off_finalisation_run_ready",
    }.get(source_doctype)

    if not ready_field or not _field_exists(source_doctype, ready_field):
        return False

    status, ready = frappe.db.get_value(source_doctype, source_name, ["status", ready_field])
    return status in SOURCE_READY_STATUSES.get(source_doctype, []) and bool(ready)


def _is_recovery_preparation_approved(run):
    if not run or not frappe.db.exists(RECOVERY_PREPARATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        RECOVERY_PREPARATION_RUN,
        run,
        ["status", "recovery_preparation_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _is_recovery_candidate(row):
    if row.get("recovery_candidate"):
        return True

    if row.get("recovery_required"):
        return True

    recommended = row.get("recommended_resolution")
    category = row.get("review_category")
    treatment = row.get("write_off_treatment")
    matching = row.get("matching_result")
    allocation = row.get("allocation_type")

    if _contains_any(recommended, ["recover", "recovery", "debt", "follow up", "follow-up", "chase", "repay"]):
        return True

    if _contains_any(category, ["overpayment", "duplicate", "incorrect payment", "debt", "recover", "recovery"]):
        return True

    if _contains_any(matching, ["overpaid", "duplicate", "incorrect", "unmatched overpayment"]):
        return True

    if _contains_any(allocation, ["overpayment", "recovery", "debt"]):
        return True

    if _contains_any(treatment, ["recover", "recovery"]):
        return True

    return False


def _proposed_recovery_amount(row):
    candidates = [
        row.get("proposed_recovery_amount"),
        row.get("recovery_amount"),
        row.get("overpaid_amount"),
        row.get("actual_rejected_amount"),
        row.get("short_paid_amount"),
        row.get("rejected_amount"),
        row.get("variance_amount"),
        row.get("finalised_write_off_amount"),
        row.get("proposed_write_off_amount"),
    ]

    for value in candidates:
        amount = abs(_to_float(value))
        if amount > 0:
            return round(amount, 2)

    return 0


def _recovery_type(row):
    category = _lower(row.get("review_category"))
    recommended = _lower(row.get("recommended_resolution"))
    matching = _lower(row.get("matching_result"))

    combined = " ".join([category, recommended, matching])

    if "overpayment" in combined or "overpaid" in combined:
        return "Overpayment Recovery"
    if "duplicate" in combined:
        return "Duplicate Payment Recovery"
    if "rejected" in combined or "rejection" in combined:
        return "Rejected Claim Recovery"
    if "short" in combined or "underpaid" in combined:
        return "Short Payment Recovery"
    if "participant" in combined or "debt" in combined:
        return "Participant Debt Review"
    if "plan manager" in combined:
        return "Plan Manager Follow-Up"

    return "Manual Recovery Review"


def _recovery_route(row):
    recommended = _lower(row.get("recommended_resolution"))
    category = _lower(row.get("review_category"))

    combined = " ".join([recommended, category])

    if "plan manager" in combined:
        return "Plan Manager Follow-Up"
    if "participant" in combined:
        return "Participant Debt Review"
    if "provider" in combined:
        return "Provider Correction"
    if "ndia" in combined or "portal" in combined:
        return "NDIA / Portal Correction"
    if "internal" in combined:
        return "Internal Correction Review"

    return "Accounts Recovery Review"


def _recovery_reason(row):
    if row.get("recommended_resolution"):
        return row.get("recommended_resolution")

    category = row.get("review_category")
    if category:
        return f"Recovery preparation required from {category} outcome."

    return "Manual recovery review required."


def _source_key(row):
    for fieldname in [
        "write_off_finalisation_source_key",
        "variance_review_source_key",
        "write_off_je_submission_source_key",
    ]:
        if row.get(fieldname):
            return row.get(fieldname)

    return "|".join([
        str(row.get("journal_entry") or ""),
        str(row.get("service_line") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("ndis_remittance_import") or ""),
        str(row.get("actual_payment_reference") or ""),
    ])


def _append_line_if_missing(doc, row_data):
    existing = {
        row.recovery_preparation_source_key
        for row in doc.get("recovery_preparation_lines") or []
        if row.get("recovery_preparation_source_key")
    }

    key = row_data.get("recovery_preparation_source_key")

    if key and key in existing:
        return False

    doc.append("recovery_preparation_lines", row_data)
    return True


def _line_source_ready_from_variance(row, source_doc):
    amount = _proposed_recovery_amount(row)

    return bool(
        source_doc.get("status") == "Variance Rejection Review Completed"
        and row.get("variance_review_line_status") == "Variance Review Completed"
        and row.get("variance_review_source_ready")
        and row.get("variance_review_complete")
        and row.get("variance_decision_authorized")
        and row.get("line_ready_for_variance_review_completion")
        and not row.get("variance_review_hold")
        and not row.get("write_off_authorized")
        and not row.get("recovery_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("journal_authorized")
        and not row.get("bank_reconciliation_authorized")
        and amount > 0
    )


def _line_source_ready_from_finalisation(row, source_doc):
    amount = _proposed_recovery_amount(row)

    return bool(
        source_doc.get("status") == "Write Off Finalised"
        and row.get("write_off_finalisation_line_status") == "Write Off Finalised"
        and row.get("write_off_finalisation_source_ready")
        and row.get("journal_entry_posting_verified")
        and row.get("standard_gl_review_complete")
        and row.get("write_off_finalisation_authorized")
        and row.get("line_ready_for_write_off_finalisation")
        and not row.get("write_off_finalisation_hold")
        and not row.get("manual_gl_authorized")
        and not row.get("payment_entry_authorized")
        and not row.get("additional_journal_entry_authorized")
        and not row.get("recovery_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("bank_reconciliation_authorized")
        and amount > 0
    )


def _build_recovery_line(row, source_doc, source_doctype):
    proposed_amount = _proposed_recovery_amount(row)

    if source_doctype == VARIANCE_REJECTION_REVIEW_RUN:
        source_ready = _line_source_ready_from_variance(row, source_doc)
        source_label = "Phase 31 Variance Rejection Review"
    else:
        source_ready = _line_source_ready_from_finalisation(row, source_doc)
        source_label = "Phase 36 Write Off Finalisation"

    return {
        "recovery_preparation_source_type": source_label,
        "recovery_preparation_source_key": _source_key(row),

        "journal_entry": row.get("journal_entry"),
        "journal_entry_docstatus": row.get("journal_entry_docstatus"),
        "journal_entry_status": row.get("journal_entry_status"),
        "standard_gl_entry_count": row.get("standard_gl_entry_count") or row.get("gl_entry_count"),

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

        "proposed_recovery_amount": proposed_amount,
        "recovery_type": _recovery_type(row),
        "recovery_route": _recovery_route(row),
        "recovery_reason": _recovery_reason(row),
        "recovery_party_type": "Customer",
        "recovery_party": row.get("party") or source_doc.get("participant_customer"),
        "recovery_contact_name": None,
        "recovery_contact_email": None,
        "recovery_due_date": None,

        "recovery_preparation_source_ready": 1 if source_ready else 0,
        "recovery_review_complete": 0,
        "recovery_decision_authorized": 0,

        "recovery_case_creation_authorized": 0,
        "journal_entry_authorized": 0,
        "manual_gl_authorized": 0,
        "payment_entry_authorized": 0,
        "sales_invoice_authorized": 0,
        "adjustment_authorized": 0,
        "bank_reconciliation_authorized": 0,

        "recovery_preparation_hold": 0 if source_ready else 1,
        "recovery_preparation_hold_reason": None if source_ready else "Source line is not ready for recovery preparation.",
        "line_ready_for_recovery_preparation": 0,
        "recovery_preparation_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_from_variance_review(doc, source):
    created = 0

    for row in source.get("variance_review_lines") or []:
        if row.get("variance_review_line_status") != "Variance Review Completed":
            continue

        if not _is_recovery_candidate(row):
            continue

        amount = _proposed_recovery_amount(row)
        if amount <= 0:
            continue

        data = _build_recovery_line(row, source, VARIANCE_REJECTION_REVIEW_RUN)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _generate_from_write_off_finalisation(doc, source):
    created = 0

    for row in source.get("write_off_finalisation_lines") or []:
        if row.get("write_off_finalisation_line_status") != "Write Off Finalised":
            continue

        if not _is_recovery_candidate(row):
            continue

        amount = _proposed_recovery_amount(row)
        if amount <= 0:
            continue

        data = _build_recovery_line(row, source, WRITE_OFF_FINALISATION_RUN)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _generate_lines(doc):
    created = 0

    if doc.get("variance_rejection_review_run"):
        source = frappe.get_doc(VARIANCE_REJECTION_REVIEW_RUN, doc.variance_rejection_review_run)
        created += _generate_from_variance_review(doc, source)

    if doc.get("write_off_finalisation_run"):
        source = frappe.get_doc(WRITE_OFF_FINALISATION_RUN, doc.write_off_finalisation_run)
        created += _generate_from_write_off_finalisation(doc, source)

    return created


def _active_lines(doc):
    return [
        row for row in doc.get("recovery_preparation_lines") or []
        if _to_float(row.get("proposed_recovery_amount")) > 0
    ]


def _calculate_totals(doc):
    line_count = len(doc.get("recovery_preparation_lines") or [])
    amount_total = 0
    ready_count = 0
    hold_count = 0
    overpayment_count = 0
    rejected_claim_count = 0
    short_payment_count = 0
    manual_review_count = 0

    blocked_case_count = 0
    blocked_je_count = 0
    blocked_gl_count = 0
    blocked_pe_count = 0
    blocked_si_count = 0
    blocked_adjustment_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("recovery_preparation_lines") or []:
        amount_total += _to_float(row.get("proposed_recovery_amount"))

        if row.get("line_ready_for_recovery_preparation"):
            ready_count += 1

        if row.get("recovery_preparation_hold"):
            hold_count += 1

        recovery_type = row.get("recovery_type")
        if recovery_type == "Overpayment Recovery":
            overpayment_count += 1
        elif recovery_type == "Rejected Claim Recovery":
            rejected_claim_count += 1
        elif recovery_type == "Short Payment Recovery":
            short_payment_count += 1
        else:
            manual_review_count += 1

        if row.get("recovery_case_creation_authorized"):
            blocked_case_count += 1
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
        "recovery_preparation_line_count": line_count,
        "proposed_recovery_amount_total": round(amount_total, 2),
        "recovery_preparation_ready_count": ready_count,
        "recovery_preparation_hold_count": hold_count,
        "overpayment_recovery_count": overpayment_count,
        "rejected_claim_recovery_count": rejected_claim_count,
        "short_payment_recovery_count": short_payment_count,
        "manual_recovery_review_count": manual_review_count,
        "blocked_recovery_case_count": blocked_case_count,
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
        if _field_exists(RECOVERY_PREPARATION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    has_source = bool(doc.get("variance_rejection_review_run") or doc.get("write_off_finalisation_run"))

    checks.append({
        "label": "Recovery source linked",
        "complete": has_source,
    })

    source_complete = True

    if doc.get("variance_rejection_review_run"):
        source_complete = source_complete and _is_source_completed(VARIANCE_REJECTION_REVIEW_RUN, doc.variance_rejection_review_run)

    if doc.get("write_off_finalisation_run"):
        source_complete = source_complete and _is_source_completed(WRITE_OFF_FINALISATION_RUN, doc.write_off_finalisation_run)

    checks.append({
        "label": "Recovery source completed",
        "complete": source_complete,
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
        "label": "Recovery Preparation Owner assigned",
        "complete": bool(doc.get("recovery_preparation_owner")),
    })

    lines = _active_lines(doc)
    no_candidates = bool(doc.get("no_recovery_candidate_found"))

    checks.append({
        "label": "Recovery lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("recovery_preparation_source_ready")]
        checks.append({
            "label": "Recovery preparation source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        missing_amount = [row.service_line for row in lines if not _to_float(row.get("proposed_recovery_amount"))]
        checks.append({
            "label": "All lines have proposed recovery amount",
            "complete": not missing_amount,
            "details": missing_amount,
        })

        missing_route = [row.service_line for row in lines if not row.get("recovery_route")]
        checks.append({
            "label": "All lines have recovery route",
            "complete": not missing_route,
            "details": missing_route,
        })

        missing_party = [row.service_line for row in lines if not row.get("recovery_party")]
        checks.append({
            "label": "All lines have recovery party",
            "complete": not missing_party,
            "details": missing_party,
        })

        review_missing = [row.service_line for row in lines if not row.get("recovery_review_complete")]
        checks.append({
            "label": "Recovery review complete",
            "complete": not review_missing,
            "details": review_missing,
        })

        decision_missing = [row.service_line for row in lines if not row.get("recovery_decision_authorized")]
        checks.append({
            "label": "Recovery decision authorization complete",
            "complete": not decision_missing,
            "details": decision_missing,
        })

        blocked_case = [row.service_line for row in lines if row.get("recovery_case_creation_authorized")]
        checks.append({
            "label": "Recovery Case creation remains blocked in Phase 37",
            "complete": not blocked_case,
            "details": blocked_case,
        })

        blocked_je = [row.service_line for row in lines if row.get("journal_entry_authorized")]
        checks.append({
            "label": "Journal Entry authorization remains blocked in Phase 37",
            "complete": not blocked_je,
            "details": blocked_je,
        })

        blocked_gl = [row.service_line for row in lines if row.get("manual_gl_authorized")]
        checks.append({
            "label": "Manual GL authorization remains blocked in Phase 37",
            "complete": not blocked_gl,
            "details": blocked_gl,
        })

        blocked_pe = [row.service_line for row in lines if row.get("payment_entry_authorized")]
        checks.append({
            "label": "Payment Entry authorization remains blocked in Phase 37",
            "complete": not blocked_pe,
            "details": blocked_pe,
        })

        blocked_si = [row.service_line for row in lines if row.get("sales_invoice_authorized")]
        checks.append({
            "label": "Sales Invoice authorization remains blocked in Phase 37",
            "complete": not blocked_si,
            "details": blocked_si,
        })

        blocked_adj = [row.service_line for row in lines if row.get("adjustment_authorized")]
        checks.append({
            "label": "Adjustment authorization remains blocked in Phase 37",
            "complete": not blocked_adj,
            "details": blocked_adj,
        })

        blocked_bank = [row.service_line for row in lines if row.get("bank_reconciliation_authorized")]
        checks.append({
            "label": "Bank reconciliation authorization remains blocked in Phase 37",
            "complete": not blocked_bank,
            "details": blocked_bank,
        })

        holds = [row.service_line for row in lines if row.get("recovery_preparation_hold")]
        checks.append({
            "label": "No active recovery preparation hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_recovery_preparation")]
        checks.append({
            "label": "All active lines marked ready for recovery preparation",
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
        "recovery_preparation_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(RECOVERY_PREPARATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_PREPARATION_RUN, "recovery_preparation_run_ready"):
        doc.recovery_preparation_run_ready = 1 if summary["recovery_preparation_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_recovery_preparation_run", doc.name)
        _db_set_if_field(doctype, name, "recovery_preparation_status", doc.status)
        _db_set_if_field(doctype, name, "recovery_preparation_ready", 1 if summary["recovery_preparation_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


def _copy_common_chain_fields(doc, source):
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


@frappe.whitelist()
def create_recovery_preparation_run_from_variance_review_run(variance_rejection_review_run):
    _check_role()

    if not variance_rejection_review_run:
        frappe.throw(_("NDIS CRM Variance Rejection Review Run is required."))

    if not frappe.db.exists(VARIANCE_REJECTION_REVIEW_RUN, variance_rejection_review_run):
        frappe.throw(_("NDIS CRM Variance Rejection Review Run {0} was not found.").format(variance_rejection_review_run))

    existing = _existing_run_for_variance_review_run(variance_rejection_review_run)
    if existing:
        return {
            "doctype": RECOVERY_PREPARATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Preparation Run returned.",
        }

    source = frappe.get_doc(VARIANCE_REJECTION_REVIEW_RUN, variance_rejection_review_run)

    doc = frappe.new_doc(RECOVERY_PREPARATION_RUN)
    doc.status = "Draft"
    doc.recovery_source_type = "Phase 31 Variance Rejection Review"
    doc.variance_rejection_review_run = source.name
    _copy_common_chain_fields(doc, source)

    doc.recovery_preparation_owner = frappe.session.user
    doc.variance_review_owner = source.get("variance_review_owner")
    doc.recovery_preparation_completion_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines(doc)
    doc.no_recovery_candidate_found = 1 if created_count == 0 else 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_preparation_run_ready = 1 if summary["recovery_preparation_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_PREPARATION_RUN,
        "name": doc.name,
        "created": True,
        "recovery_preparation_line_count": created_count,
        "no_recovery_candidate_found": bool(doc.no_recovery_candidate_found),
        "message": "NDIS CRM Recovery Preparation Run created successfully.",
    }


@frappe.whitelist()
def create_recovery_preparation_run_from_write_off_finalisation_run(write_off_finalisation_run):
    _check_role()

    if not write_off_finalisation_run:
        frappe.throw(_("NDIS CRM Write Off Finalisation Run is required."))

    if not frappe.db.exists(WRITE_OFF_FINALISATION_RUN, write_off_finalisation_run):
        frappe.throw(_("NDIS CRM Write Off Finalisation Run {0} was not found.").format(write_off_finalisation_run))

    existing = _existing_run_for_write_off_finalisation_run(write_off_finalisation_run)
    if existing:
        return {
            "doctype": RECOVERY_PREPARATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Preparation Run returned.",
        }

    source = frappe.get_doc(WRITE_OFF_FINALISATION_RUN, write_off_finalisation_run)

    doc = frappe.new_doc(RECOVERY_PREPARATION_RUN)
    doc.status = "Draft"
    doc.recovery_source_type = "Phase 36 Write Off Finalisation"
    doc.write_off_finalisation_run = source.name
    doc.write_off_je_submission_run = source.get("write_off_je_submission_run")
    doc.write_off_je_draft_run = source.get("write_off_je_draft_run")
    doc.write_off_draft_run = source.get("write_off_draft_run")
    doc.write_off_preparation_run = source.get("write_off_preparation_run")
    doc.variance_rejection_review_run = source.get("variance_rejection_review_run")
    _copy_common_chain_fields(doc, source)

    doc.recovery_preparation_owner = frappe.session.user
    doc.write_off_finalisation_owner = source.get("write_off_finalisation_owner")
    doc.recovery_preparation_completion_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines(doc)
    doc.no_recovery_candidate_found = 1 if created_count == 0 else 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_preparation_run_ready = 1 if summary["recovery_preparation_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_PREPARATION_RUN,
        "name": doc.name,
        "created": True,
        "recovery_preparation_line_count": created_count,
        "no_recovery_candidate_found": bool(doc.no_recovery_candidate_found),
        "message": "NDIS CRM Recovery Preparation Run created successfully.",
    }


@frappe.whitelist()
def create_recovery_preparation_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": RECOVERY_PREPARATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Recovery Preparation Run returned.",
        }

    source_doctype, source_name = _get_best_source_for_deal(deal)

    if not source_doctype or not source_name:
        frappe.throw(_("Please complete Variance Rejection Review or Write Off Finalisation before creating Recovery Preparation Run."))

    if source_doctype == WRITE_OFF_FINALISATION_RUN:
        return create_recovery_preparation_run_from_write_off_finalisation_run(source_name)

    return create_recovery_preparation_run_from_variance_review_run(source_name)


@frappe.whitelist()
def generate_recovery_preparation_lines(recovery_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_PREPARATION_RUN, recovery_preparation_run)

    created_count = _generate_lines(doc)

    if created_count == 0 and not doc.get("recovery_preparation_lines"):
        doc.no_recovery_candidate_found = 1
    else:
        doc.no_recovery_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Recovery preparation lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_recovery_preparation_readiness(recovery_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_PREPARATION_RUN, recovery_preparation_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Recovery Preparation Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_recovery_preparation(recovery_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_PREPARATION_RUN, recovery_preparation_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_preparation_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Recovery Preparation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Recovery Preparation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_preparation_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_PREPARATION_RUN,
        "name": doc.name,
        "message": "Recovery Preparation Run marked Ready.",
    }


@frappe.whitelist()
def approve_recovery_preparation_run(recovery_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_PREPARATION_RUN, recovery_preparation_run)
    summary = _calculate_readiness(doc)

    if not summary["recovery_preparation_run_ready"]:
        frappe.throw(
            _("Cannot approve Recovery Preparation Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Recovery Preparation Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.recovery_preparation_run_ready = 1
    doc.recovery_preparation_completion_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("recovery_preparation_lines") or []:
        if row.get("recovery_preparation_line_status") in ["Draft", "Ready"]:
            row.recovery_preparation_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": RECOVERY_PREPARATION_RUN,
        "name": doc.name,
        "message": "Recovery Preparation Run approved. No Recovery Case, Journal Entry, GL, Payment Entry, Sales Invoice, adjustment, or bank reconciliation was created.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("recovery_preparation_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_recovery_preparation"):
            continue

        if not row.get("recovery_preparation_source_ready"):
            continue

        if not row.get("recovery_review_complete"):
            continue

        if not row.get("recovery_decision_authorized"):
            continue

        if row.get("recovery_case_creation_authorized"):
            continue

        if row.get("journal_entry_authorized"):
            continue

        if row.get("manual_gl_authorized"):
            continue

        if row.get("payment_entry_authorized"):
            continue

        if row.get("sales_invoice_authorized"):
            continue

        if row.get("adjustment_authorized"):
            continue

        if row.get("bank_reconciliation_authorized"):
            continue

        if row.get("recovery_preparation_hold"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_recovery_preparation(recovery_preparation_run):
    _check_role()

    doc = frappe.get_doc(RECOVERY_PREPARATION_RUN, recovery_preparation_run)

    if doc.status != "Recovery Preparation Approved":
        frappe.throw(_("Recovery Preparation Run must be approved before completion."))

    if not doc.get("recovery_preparation_completion_allowed"):
        frappe.throw(_("Tick Recovery Preparation Completion Allowed before completing preparation."))

    if doc.get("recovery_case_creation_allowed"):
        frappe.throw(_("Recovery Case Creation Allowed must remain unticked in Phase 37."))

    if doc.get("journal_entry_creation_allowed"):
        frappe.throw(_("Journal Entry Creation Allowed must remain unticked in Phase 37."))

    if doc.get("manual_gl_creation_allowed"):
        frappe.throw(_("Manual GL Creation Allowed must remain unticked in Phase 37."))

    if doc.get("payment_entry_creation_allowed"):
        frappe.throw(_("Payment Entry Creation Allowed must remain unticked in Phase 37."))

    if doc.get("sales_invoice_creation_allowed"):
        frappe.throw(_("Sales Invoice Creation Allowed must remain unticked in Phase 37."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment Creation Allowed must remain unticked in Phase 37."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank Reconciliation Allowed must remain unticked in Phase 37."))

    summary = _calculate_readiness(doc)

    if not summary["recovery_preparation_run_ready"]:
        frappe.throw(
            _("Cannot complete Recovery Preparation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines and not doc.get("no_recovery_candidate_found"):
        frappe.throw(_("No ready recovery preparation lines found."))

    for row in ready_lines:
        row.recovery_preparation_line_status = "Recovery Prepared"

    doc.status = "Recovery Prepared"
    doc.recovery_preparation_completion_allowed = 0
    doc.recovery_case_creation_allowed = 0
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
        "completed_line_count": len(ready_lines),
        "no_recovery_candidate_found": bool(doc.get("no_recovery_candidate_found")),
        "message": "Recovery preparation completed. No Recovery Case, Journal Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, or manual GL was created.",
    }


def validate_recovery_preparation_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(RECOVERY_PREPARATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(RECOVERY_PREPARATION_RUN, "recovery_preparation_run_ready"):
        doc.recovery_preparation_run_ready = 1 if summary["recovery_preparation_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["recovery_preparation_run_ready"]:
        frappe.throw(
            _("Cannot set Recovery Preparation Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Recovery Preparation Approved" and doc.get("recovery_preparation_completion_allowed"):
        frappe.throw(_("Recovery Preparation Completion Allowed can only be ticked after the run is approved."))

    if doc.get("recovery_case_creation_allowed"):
        frappe.throw(_("Recovery Case creation is not allowed in Phase 37."))

    if doc.get("journal_entry_creation_allowed"):
        frappe.throw(_("Journal Entry creation is not allowed in Phase 37."))

    if doc.get("manual_gl_creation_allowed"):
        frappe.throw(_("Manual GL creation is not allowed in Phase 37."))

    if doc.get("payment_entry_creation_allowed"):
        frappe.throw(_("Payment Entry creation is not allowed in Phase 37."))

    if doc.get("sales_invoice_creation_allowed"):
        frappe.throw(_("Sales Invoice creation is not allowed in Phase 37."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment creation is not allowed in Phase 37."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank reconciliation is not allowed in Phase 37."))


def on_recovery_preparation_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Recovery Preparation Run Summary Sync Failed"
        )


def validate_crm_deal_phase37(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_recovery_preparation_run_required"):
        required = doc.get("ndis_recovery_preparation_run_required")

    if not required:
        return

    run = doc.get("ndis_recovery_preparation_run") if _field_exists(CRM_DEAL, "ndis_recovery_preparation_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Preparation Run must be created and approved/prepared.")
        )

    if not _is_recovery_preparation_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Recovery Preparation Run must be approved/prepared.")
        )


def validate_crm_deal_phase37_combined(doc, method=None):
    """
    Preserve Phase 2-36 validator chain, then add optional Phase 37 Recovery Preparation validation.
    """
    try:
        from ndis_crm.phase36_write_off_finalisation import validate_crm_deal_phase36_combined
        validate_crm_deal_phase36_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase35_write_off_je_submission import validate_crm_deal_phase35_combined
            validate_crm_deal_phase35_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase34_write_off_je_draft import validate_crm_deal_phase34_combined
                validate_crm_deal_phase34_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase37(doc, method)


def phase37_health_check():
    print("---- NDIS CRM Phase 37 Health Check ----")

    for dt in [
        RECOVERY_PREPARATION_LINE,
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
        NDIS_RECOVERY_CASE,
        "Bank Reconciliation Tool",
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_recovery_preparation_run_required",
        "ndis_recovery_preparation_run",
        "recovery_preparation_status",
        "recovery_preparation_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print("NDIS CRM Recovery Preparation Run records:", frappe.db.count(RECOVERY_PREPARATION_RUN) if _doctype_exists(RECOVERY_PREPARATION_RUN) else 0)
    print("Phase 37 creates CRM recovery preparation records only.")
    print("Phase 37 does not create Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 37 Health Check ----")
