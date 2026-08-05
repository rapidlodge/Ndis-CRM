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
REMITTANCE_MATCHING_REVIEW_LINE = "NDIS CRM Remittance Matching Review Line"

PAYMENT_ALLOCATION_PREP_RUN = "NDIS CRM Payment Allocation Preparation Run"
PAYMENT_ALLOCATION_PREP_LINE = "NDIS CRM Payment Allocation Preparation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

SALES_INVOICE = "Sales Invoice"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"

READY_STATUSES = [
    "Ready for Payment Allocation Preparation",
    "Payment Allocation Preparation Approved",
    "Payment Allocation Prepared",
]

APPROVED_STATUSES = [
    "Payment Allocation Preparation Approved",
    "Payment Allocation Prepared",
]

SOURCE_READY_STATUSES = [
    "Matching Review Completed",
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
        frappe.throw(_("You do not have permission to perform this payment allocation preparation action."))


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


def _existing_run_for_matching_review_run(remittance_matching_review_run):
    if not _doctype_exists(PAYMENT_ALLOCATION_PREP_RUN):
        return None

    if _field_exists(REMITTANCE_MATCHING_REVIEW_RUN, "ndis_payment_allocation_preparation_run"):
        existing = frappe.db.get_value(
            REMITTANCE_MATCHING_REVIEW_RUN,
            remittance_matching_review_run,
            "ndis_payment_allocation_preparation_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        PAYMENT_ALLOCATION_PREP_RUN,
        {"remittance_matching_review_run": remittance_matching_review_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(PAYMENT_ALLOCATION_PREP_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_payment_allocation_preparation_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_payment_allocation_preparation_run")
        if existing:
            return existing

    return frappe.db.get_value(PAYMENT_ALLOCATION_PREP_RUN, {"crm_deal": deal}, "name")


def _get_matching_review_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_remittance_matching_review_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_remittance_matching_review_run")
        if run:
            return run

    if _doctype_exists(REMITTANCE_MATCHING_REVIEW_RUN):
        return frappe.db.get_value(REMITTANCE_MATCHING_REVIEW_RUN, {"crm_deal": deal}, "name")

    return None


def _is_matching_review_completed(run):
    if not run or not frappe.db.exists(REMITTANCE_MATCHING_REVIEW_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        REMITTANCE_MATCHING_REVIEW_RUN,
        run,
        ["status", "remittance_matching_review_run_ready"],
    )

    return status in SOURCE_READY_STATUSES and bool(ready)


def _is_payment_allocation_prep_approved(run):
    if not run or not frappe.db.exists(PAYMENT_ALLOCATION_PREP_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        PAYMENT_ALLOCATION_PREP_RUN,
        run,
        ["status", "payment_allocation_preparation_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


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
        "participant",
        "participant_customer",
        "customer",
        "posting_date",
        "import_date",
        "remittance_date",
        "total_claim_amount",
        "claim_amount_total",
        "total_paid_amount",
        "paid_amount_total",
        "actual_paid_amount_total",
        "total_rejected_amount",
        "rejected_amount_total",
        "variance_amount_total",
        "external_lodgement_reference",
        "lodgement_reference",
        "portal_reference",
        "payment_reference",
        "remittance_reference",
    ]:
        if _field_exists(NDIS_REMITTANCE_IMPORT, fieldname):
            out[fieldname] = frappe.db.get_value(NDIS_REMITTANCE_IMPORT, ndis_remittance_import, fieldname)

    return out


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
            "posting_date",
            "due_date",
            "grand_total",
            "rounded_total",
            "outstanding_amount",
            "status",
        ],
        as_dict=True,
    ) or {}


def _source_key(row):
    return row.get("matching_source_key") or "|".join([
        str(row.get("service_line") or ""),
        str(row.get("ndis_remittance_import") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("external_lodgement_reference") or ""),
        str(row.get("actual_payment_reference") or ""),
    ])


def _append_line_if_missing(doc, row_data):
    existing = {
        row.payment_allocation_source_key
        for row in doc.get("payment_allocation_lines") or []
        if row.get("payment_allocation_source_key")
    }

    key = row_data.get("payment_allocation_source_key")

    if key and key in existing:
        return False

    doc.append("payment_allocation_lines", row_data)
    return True


def _allocation_decision(row):
    matching_result = row.get("matching_result")
    expected_paid = _to_float(row.get("expected_paid_amount"))
    actual_paid = _to_float(row.get("actual_paid_amount"))
    actual_rejected = _to_float(row.get("actual_rejected_amount"))
    variance = _to_float(row.get("variance_amount"))

    if matching_result == "Full Payment Match":
        return {
            "allocation_type": "Full Payment Allocation",
            "allocation_amount": actual_paid,
            "short_paid_amount": 0,
            "overpaid_amount": 0,
            "rejected_amount": 0,
            "requires_manual_review": 0,
            "recommended_next_action": "Payment Entry Preparation",
            "hold": 0,
            "reason": "Full payment matched. Prepare for later Payment Entry gate.",
        }

    if matching_result == "Partial Payment":
        short_paid = max(expected_paid - actual_paid, 0)
        return {
            "allocation_type": "Partial Payment Allocation",
            "allocation_amount": actual_paid,
            "short_paid_amount": short_paid,
            "overpaid_amount": 0,
            "rejected_amount": actual_rejected,
            "requires_manual_review": 1 if short_paid or actual_rejected else 0,
            "recommended_next_action": "Payment Entry Preparation + Short Payment Review",
            "hold": 0,
            "reason": "Partial payment matched. Payment allocation can be prepared; shortfall remains for later review.",
        }

    if matching_result == "Rejected":
        return {
            "allocation_type": "No Payment / Rejected",
            "allocation_amount": 0,
            "short_paid_amount": expected_paid,
            "overpaid_amount": 0,
            "rejected_amount": actual_rejected or expected_paid,
            "requires_manual_review": 1,
            "recommended_next_action": "Rejection / Recovery Review",
            "hold": 0,
            "reason": "Claim rejected. No payment allocation amount prepared.",
        }

    if matching_result == "Overpayment":
        overpaid = max(actual_paid - expected_paid, 0)
        return {
            "allocation_type": "Overpayment Review",
            "allocation_amount": min(actual_paid, expected_paid) if expected_paid else actual_paid,
            "short_paid_amount": 0,
            "overpaid_amount": overpaid,
            "rejected_amount": 0,
            "requires_manual_review": 1,
            "recommended_next_action": "Overpayment Review",
            "hold": 1,
            "reason": "Overpayment detected. Keep on hold until allocation treatment is approved.",
        }

    if matching_result == "Underpayment":
        short_paid = max(expected_paid - actual_paid, 0)
        return {
            "allocation_type": "Underpayment Review",
            "allocation_amount": actual_paid,
            "short_paid_amount": short_paid,
            "overpaid_amount": 0,
            "rejected_amount": actual_rejected,
            "requires_manual_review": 1,
            "recommended_next_action": "Short Payment / Recovery Review",
            "hold": 1,
            "reason": "Underpayment detected. Keep on hold until recovery/write-off decision is separated into later phases.",
        }

    if matching_result == "Unmatched":
        return {
            "allocation_type": "Manual Review",
            "allocation_amount": 0,
            "short_paid_amount": expected_paid,
            "overpaid_amount": 0,
            "rejected_amount": 0,
            "requires_manual_review": 1,
            "recommended_next_action": "Manual Matching Investigation",
            "hold": 1,
            "reason": "Unmatched remittance line. Manual investigation required.",
        }

    return {
        "allocation_type": "Manual Review",
        "allocation_amount": 0,
        "short_paid_amount": expected_paid,
        "overpaid_amount": 0,
        "rejected_amount": actual_rejected,
        "requires_manual_review": 1,
        "recommended_next_action": row.get("recommended_next_action") or "Manual Review",
        "hold": 1,
        "reason": "Manual review required before payment allocation preparation.",
    }


def _build_payment_allocation_line_from_matching_line(row, source_doc):
    invoice_snapshot = _sales_invoice_snapshot(row.get("sales_invoice"))
    remittance_snapshot = _remittance_import_snapshot(row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"))
    decision = _allocation_decision(row)

    source_ready = bool(
        source_doc.get("status") == "Matching Review Completed"
        and row.get("matching_line_status") == "Matching Review Completed"
        and row.get("remittance_import_source_ready")
        and row.get("matching_review_complete")
        and row.get("matching_decision_authorized")
        and not row.get("matching_hold")
        and row.get("ndis_remittance_import")
        and int(remittance_snapshot.get("docstatus") or 0) == 0
        and row.get("sales_invoice")
        and int(invoice_snapshot.get("docstatus") or 0) == 1
        and row.get("matching_result")
    )

    hold = 1 if decision["hold"] or not source_ready else 0

    data = {
        "payment_allocation_source_key": _source_key(row),
        "ndis_remittance_import": row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"),
        "ndis_remittance_import_docstatus": remittance_snapshot.get("docstatus"),
        "ndis_remittance_import_status": remittance_snapshot.get("status") or remittance_snapshot.get("import_status") or remittance_snapshot.get("remittance_status"),
        "ndis_claim_batch": row.get("ndis_claim_batch"),
        "ndis_claim_line": row.get("ndis_claim_line"),
        "claim_batch_status": row.get("claim_batch_status"),
        "claim_line_status": row.get("claim_line_status"),
        "sales_invoice": row.get("sales_invoice"),
        "sales_invoice_docstatus": int(invoice_snapshot.get("docstatus") or 0) if invoice_snapshot else row.get("sales_invoice_docstatus"),
        "sales_invoice_status": invoice_snapshot.get("status") or row.get("sales_invoice_status"),
        "sales_invoice_outstanding_amount": invoice_snapshot.get("outstanding_amount") if invoice_snapshot else row.get("sales_invoice_outstanding_amount"),
        "service_line": row.get("service_line"),
        "service_code": row.get("service_code"),
        "service_model": row.get("service_model"),
        "service_date": row.get("service_date"),
        "claim_quantity": row.get("claim_quantity"),
        "claim_unit": row.get("claim_unit") or "Hour",
        "claim_rate": row.get("claim_rate"),
        "claim_amount": row.get("claim_amount"),
        "expected_paid_amount": row.get("expected_paid_amount"),
        "actual_paid_amount": row.get("actual_paid_amount"),
        "actual_rejected_amount": row.get("actual_rejected_amount"),
        "variance_amount": row.get("variance_amount"),
        "proposed_allocation_amount": decision["allocation_amount"],
        "short_paid_amount": decision["short_paid_amount"],
        "overpaid_amount": decision["overpaid_amount"],
        "rejected_amount": decision["rejected_amount"],
        "support_item": row.get("support_item"),
        "finance_service_type": row.get("finance_service_type"),
        "plan_budget": row.get("plan_budget"),
        "service_booking": row.get("service_booking"),
        "funding_source": row.get("funding_source"),
        "default_house": row.get("default_house"),
        "invoice_group_key": row.get("invoice_group_key"),
        "external_lodgement_reference": row.get("external_lodgement_reference"),
        "external_batch_reference": row.get("external_batch_reference"),
        "external_line_reference": row.get("external_line_reference"),
        "actual_payment_reference": row.get("actual_payment_reference"),
        "actual_payment_date": row.get("actual_payment_date"),
        "actual_remittance_status": row.get("actual_remittance_status"),
        "matching_result": row.get("matching_result"),
        "matching_reason": row.get("matching_reason"),
        "allocation_type": decision["allocation_type"],
        "recommended_next_action": decision["recommended_next_action"],
        "payment_allocation_source_ready": 1 if source_ready else 0,
        "payment_allocation_review_complete": 0,
        "allocation_decision_authorized": 0,
        "requires_manual_review": decision["requires_manual_review"],
        "payment_entry_authorized": 0,
        "journal_authorized": 0,
        "write_off_authorized": 0,
        "recovery_authorized": 0,
        "payment_allocation_hold": hold,
        "payment_allocation_hold_reason": None if not hold else decision["reason"] if source_ready else "Remittance matching source is not ready for payment allocation preparation.",
        "line_ready_for_payment_allocation_preparation": 0,
        "payment_allocation_line_status": "Draft",
        "notes": row.get("notes"),
    }

    return data


def _generate_lines_from_matching_review_run(doc, source):
    created = 0

    for row in source.get("matching_lines") or []:
        if row.get("matching_line_status") != "Matching Review Completed":
            continue

        data = _build_payment_allocation_line_from_matching_line(row, source)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _calculate_totals(doc):
    line_count = len(doc.get("payment_allocation_lines") or [])
    claim_total = 0
    expected_total = 0
    paid_total = 0
    rejected_total = 0
    variance_total = 0
    proposed_allocation_total = 0
    short_paid_total = 0
    overpaid_total = 0
    ready_count = 0
    hold_count = 0
    full_allocation_count = 0
    partial_allocation_count = 0
    rejected_count = 0
    manual_review_count = 0
    blocked_payment_count = 0
    blocked_journal_count = 0
    blocked_writeoff_count = 0
    blocked_recovery_count = 0

    for row in doc.get("payment_allocation_lines") or []:
        claim_total += _to_float(row.get("claim_amount"))
        expected_total += _to_float(row.get("expected_paid_amount"))
        paid_total += _to_float(row.get("actual_paid_amount"))
        rejected_total += _to_float(row.get("actual_rejected_amount"))
        variance_total += _to_float(row.get("variance_amount"))
        proposed_allocation_total += _to_float(row.get("proposed_allocation_amount"))
        short_paid_total += _to_float(row.get("short_paid_amount"))
        overpaid_total += _to_float(row.get("overpaid_amount"))

        if row.get("line_ready_for_payment_allocation_preparation"):
            ready_count += 1

        if row.get("payment_allocation_hold"):
            hold_count += 1

        if row.get("allocation_type") == "Full Payment Allocation":
            full_allocation_count += 1
        elif row.get("allocation_type") == "Partial Payment Allocation":
            partial_allocation_count += 1
        elif row.get("allocation_type") == "No Payment / Rejected":
            rejected_count += 1
        elif row.get("requires_manual_review"):
            manual_review_count += 1

        if row.get("payment_entry_authorized"):
            blocked_payment_count += 1

        if row.get("journal_authorized"):
            blocked_journal_count += 1

        if row.get("write_off_authorized"):
            blocked_writeoff_count += 1

        if row.get("recovery_authorized"):
            blocked_recovery_count += 1

    return {
        "payment_allocation_line_count": line_count,
        "claim_amount_total": round(claim_total, 2),
        "expected_paid_amount_total": round(expected_total, 2),
        "actual_paid_amount_total": round(paid_total, 2),
        "actual_rejected_amount_total": round(rejected_total, 2),
        "variance_amount_total": round(variance_total, 2),
        "proposed_allocation_amount_total": round(proposed_allocation_total, 2),
        "short_paid_amount_total": round(short_paid_total, 2),
        "overpaid_amount_total": round(overpaid_total, 2),
        "payment_allocation_ready_count": ready_count,
        "payment_allocation_hold_count": hold_count,
        "full_allocation_count": full_allocation_count,
        "partial_allocation_count": partial_allocation_count,
        "rejected_no_payment_count": rejected_count,
        "manual_review_count": manual_review_count,
        "blocked_payment_authorization_count": blocked_payment_count,
        "blocked_journal_authorization_count": blocked_journal_count,
        "blocked_write_off_authorization_count": blocked_writeoff_count,
        "blocked_recovery_authorization_count": blocked_recovery_count,
    }


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(PAYMENT_ALLOCATION_PREP_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Remittance Matching Review Run linked",
        "complete": bool(doc.get("remittance_matching_review_run")),
    })

    checks.append({
        "label": "Remittance matching review completed",
        "complete": _is_matching_review_completed(doc.get("remittance_matching_review_run")),
    })

    checks.append({
        "label": "NDIS Remittance Import linked",
        "complete": bool(doc.get("ndis_remittance_import")),
    })

    if doc.get("ndis_remittance_import"):
        snapshot = _remittance_import_snapshot(doc.get("ndis_remittance_import"))
        checks.append({
            "label": "NDIS Remittance Import is still Draft",
            "complete": int(snapshot.get("docstatus") or 0) == 0,
        })
    else:
        checks.append({
            "label": "NDIS Remittance Import is still Draft",
            "complete": False,
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
        "label": "Payment Allocation Owner assigned",
        "complete": bool(doc.get("payment_allocation_owner")),
    })

    lines = doc.get("payment_allocation_lines") or []

    checks.append({
        "label": "At least one payment allocation preparation line exists",
        "complete": bool(lines),
    })

    missing_import = [row.service_line for row in lines if not row.get("ndis_remittance_import")]
    checks.append({
        "label": "All lines have NDIS Remittance Import reference",
        "complete": not missing_import,
        "details": missing_import,
    })

    missing_invoice = [row.service_line for row in lines if not row.get("sales_invoice")]
    checks.append({
        "label": "All lines have Sales Invoice reference",
        "complete": not missing_invoice,
        "details": missing_invoice,
    })

    missing_allocation_type = [row.service_line for row in lines if not row.get("allocation_type")]
    checks.append({
        "label": "All lines have allocation type",
        "complete": not missing_allocation_type,
        "details": missing_allocation_type,
    })

    source_not_ready = [row.service_line for row in lines if not row.get("payment_allocation_source_ready")]
    checks.append({
        "label": "Payment allocation source-ready flags are complete",
        "complete": not source_not_ready,
        "details": source_not_ready,
    })

    review_missing = [row.service_line for row in lines if not row.get("payment_allocation_review_complete")]
    checks.append({
        "label": "Payment allocation review complete",
        "complete": not review_missing,
        "details": review_missing,
    })

    decision_missing = [row.service_line for row in lines if not row.get("allocation_decision_authorized")]
    checks.append({
        "label": "Allocation decision authorization complete",
        "complete": not decision_missing,
        "details": decision_missing,
    })

    payment_authorized = [row.service_line for row in lines if row.get("payment_entry_authorized")]
    checks.append({
        "label": "Payment Entry authorization remains blocked in Phase 27",
        "complete": not payment_authorized,
        "details": payment_authorized,
    })

    journal_authorized = [row.service_line for row in lines if row.get("journal_authorized")]
    checks.append({
        "label": "Journal authorization remains blocked in Phase 27",
        "complete": not journal_authorized,
        "details": journal_authorized,
    })

    writeoff_authorized = [row.service_line for row in lines if row.get("write_off_authorized")]
    checks.append({
        "label": "Write-off authorization remains blocked in Phase 27",
        "complete": not writeoff_authorized,
        "details": writeoff_authorized,
    })

    recovery_authorized = [row.service_line for row in lines if row.get("recovery_authorized")]
    checks.append({
        "label": "Recovery authorization remains blocked in Phase 27",
        "complete": not recovery_authorized,
        "details": recovery_authorized,
    })

    holds = [row.service_line for row in lines if row.get("payment_allocation_hold")]
    checks.append({
        "label": "No payment allocation preparation hold remains",
        "complete": not holds,
        "details": holds,
    })

    not_ready = [row.service_line for row in lines if not row.get("line_ready_for_payment_allocation_preparation")]
    checks.append({
        "label": "All lines marked ready for payment allocation preparation",
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
        "payment_allocation_preparation_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(PAYMENT_ALLOCATION_PREP_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(PAYMENT_ALLOCATION_PREP_RUN, "payment_allocation_preparation_run_ready"):
        doc.payment_allocation_preparation_run_ready = 1 if summary["payment_allocation_preparation_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_payment_allocation_preparation_run", doc.name)
        _db_set_if_field(doctype, name, "payment_allocation_preparation_status", doc.status)
        _db_set_if_field(doctype, name, "payment_allocation_preparation_ready", 1 if summary["payment_allocation_preparation_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_payment_allocation_preparation_run_from_matching_review_run(remittance_matching_review_run):
    _check_role()

    if not remittance_matching_review_run:
        frappe.throw(_("NDIS CRM Remittance Matching Review Run is required."))

    if not frappe.db.exists(REMITTANCE_MATCHING_REVIEW_RUN, remittance_matching_review_run):
        frappe.throw(_("NDIS CRM Remittance Matching Review Run {0} was not found.").format(remittance_matching_review_run))

    existing = _existing_run_for_matching_review_run(remittance_matching_review_run)
    if existing:
        return {
            "doctype": PAYMENT_ALLOCATION_PREP_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Payment Allocation Preparation Run returned.",
        }

    source = frappe.get_doc(REMITTANCE_MATCHING_REVIEW_RUN, remittance_matching_review_run)
    if not _is_matching_review_completed(source.name):
        frappe.throw(_("Remittance Matching Review Run must be completed before payment allocation preparation."))

    doc = frappe.new_doc(PAYMENT_ALLOCATION_PREP_RUN)
    doc.status = "Draft"
    doc.remittance_matching_review_run = source.name
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
    doc.uploaded_remittance_file = source.get("uploaded_remittance_file")
    doc.uploaded_file_hash = source.get("uploaded_file_hash")
    doc.actual_remittance_import_date = source.get("actual_remittance_import_date")
    doc.external_lodgement_reference = source.get("external_lodgement_reference")
    doc.external_batch_reference = source.get("external_batch_reference")
    doc.actual_payment_reference = source.get("actual_payment_reference")
    doc.payment_allocation_owner = frappe.session.user
    doc.matching_review_owner = source.get("matching_review_owner")
    doc.actual_remittance_owner = source.get("actual_remittance_owner")
    doc.remittance_owner = source.get("remittance_owner")
    doc.claim_owner = source.get("claim_owner")
    doc.billing_owner = source.get("billing_owner")
    doc.payment_allocation_preparation_completion_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0

    created_count = _generate_lines_from_matching_review_run(doc, source)

    if _field_exists(PAYMENT_ALLOCATION_PREP_RUN, "payment_allocation_line_count"):
        doc.payment_allocation_line_count = created_count

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.payment_allocation_preparation_run_ready = 1 if summary["payment_allocation_preparation_run_ready"] else 0

    _sync_totals(doc)

    doc.insert(ignore_permissions=False)

    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PAYMENT_ALLOCATION_PREP_RUN,
        "name": doc.name,
        "created": True,
        "payment_allocation_line_count": created_count,
        "message": "NDIS CRM Payment Allocation Preparation Run created successfully.",
    }


@frappe.whitelist()
def create_payment_allocation_preparation_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": PAYMENT_ALLOCATION_PREP_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Payment Allocation Preparation Run returned.",
        }

    source_run = _get_matching_review_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please create and complete NDIS CRM Remittance Matching Review Run before creating Payment Allocation Preparation Run."))

    return create_payment_allocation_preparation_run_from_matching_review_run(source_run)


@frappe.whitelist()
def generate_payment_allocation_preparation_lines(payment_allocation_preparation_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ALLOCATION_PREP_RUN, payment_allocation_preparation_run)

    if not doc.get("remittance_matching_review_run"):
        frappe.throw(_("Remittance Matching Review Run is required."))

    source = frappe.get_doc(REMITTANCE_MATCHING_REVIEW_RUN, doc.remittance_matching_review_run)
    created_count = _generate_lines_from_matching_review_run(doc, source)

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Payment allocation preparation lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_payment_allocation_preparation_readiness(payment_allocation_preparation_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ALLOCATION_PREP_RUN, payment_allocation_preparation_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Payment Allocation Preparation Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_payment_allocation_preparation(payment_allocation_preparation_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ALLOCATION_PREP_RUN, payment_allocation_preparation_run)
    summary = _calculate_readiness(doc)

    if not summary["payment_allocation_preparation_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Payment Allocation Preparation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Payment Allocation Preparation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.payment_allocation_preparation_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PAYMENT_ALLOCATION_PREP_RUN,
        "name": doc.name,
        "message": "Payment Allocation Preparation Run marked Ready.",
    }


@frappe.whitelist()
def approve_payment_allocation_preparation_run(payment_allocation_preparation_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ALLOCATION_PREP_RUN, payment_allocation_preparation_run)
    summary = _calculate_readiness(doc)

    if not summary["payment_allocation_preparation_run_ready"]:
        frappe.throw(
            _("Cannot approve Payment Allocation Preparation Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Payment Allocation Preparation Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.payment_allocation_preparation_run_ready = 1
    doc.payment_allocation_preparation_completion_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0

    for row in doc.get("payment_allocation_lines") or []:
        if row.get("payment_allocation_line_status") in ["Draft", "Ready"]:
            row.payment_allocation_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PAYMENT_ALLOCATION_PREP_RUN,
        "name": doc.name,
        "message": "Payment Allocation Preparation Run approved. No Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, or GL action was performed.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in doc.get("payment_allocation_lines") or []:
        if row.get("payment_allocation_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_payment_allocation_preparation"):
            continue

        if not row.get("payment_allocation_review_complete"):
            continue

        if not row.get("allocation_decision_authorized"):
            continue

        if row.get("payment_entry_authorized"):
            continue

        if row.get("journal_authorized"):
            continue

        if row.get("write_off_authorized"):
            continue

        if row.get("recovery_authorized"):
            continue

        if row.get("payment_allocation_hold"):
            continue

        ready.append(row)

    return ready


def _update_draft_remittance_import_allocation_status(doc, ready_lines):
    if not doc.get("ndis_remittance_import"):
        return None

    if not frappe.db.exists(NDIS_REMITTANCE_IMPORT, doc.ndis_remittance_import):
        return None

    remittance_doc = frappe.get_doc(NDIS_REMITTANCE_IMPORT, doc.ndis_remittance_import)

    if getattr(remittance_doc, "docstatus", 0) != 0:
        frappe.throw(_("Safety error: NDIS Remittance Import is no longer Draft."))

    _set_first_existing(remittance_doc, ["status", "import_status", "remittance_status"], "Payment Allocation Prepared")
    _set_first_existing(remittance_doc, ["payment_allocation_prepared", "allocation_prepared"], 1)
    _set_first_existing(remittance_doc, ["payment_allocation_preparation_run", "crm_payment_allocation_preparation_run"], doc.name)
    _set_first_existing(remittance_doc, ["payment_allocation_prepared_on"], now())
    _set_first_existing(remittance_doc, ["payment_allocation_prepared_by"], frappe.session.user)
    _set_first_existing(remittance_doc, ["allocated_amount_total", "proposed_allocation_amount_total"], doc.get("proposed_allocation_amount_total"))
    _set_first_existing(remittance_doc, ["short_paid_amount_total"], doc.get("short_paid_amount_total"))
    _set_first_existing(remittance_doc, ["overpaid_amount_total"], doc.get("overpaid_amount_total"))
    _set_first_existing(
        remittance_doc,
        ["notes", "remarks"],
        f"Payment allocation prepared from {doc.doctype} {doc.name}. No Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, or GL posting was created.",
    )

    remittance_doc.save(ignore_permissions=True)

    return remittance_doc.name


@frappe.whitelist()
def complete_payment_allocation_preparation(payment_allocation_preparation_run):
    _check_role()

    doc = frappe.get_doc(PAYMENT_ALLOCATION_PREP_RUN, payment_allocation_preparation_run)

    if doc.status != "Payment Allocation Preparation Approved":
        frappe.throw(_("Payment Allocation Preparation Run must be approved before completion."))

    if not doc.get("payment_allocation_preparation_completion_allowed"):
        frappe.throw(_("Tick Payment Allocation Preparation Completion Allowed before completing this run."))

    if doc.get("payment_entry_creation_allowed"):
        frappe.throw(_("Payment Entry Creation Allowed must remain unticked in Phase 27."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal Creation Allowed must remain unticked in Phase 27."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write Off Creation Allowed must remain unticked in Phase 27."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery Creation Allowed must remain unticked in Phase 27."))

    summary = _calculate_readiness(doc)

    if not summary["payment_allocation_preparation_run_ready"]:
        frappe.throw(
            _("Cannot complete payment allocation preparation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines:
        frappe.throw(_("No ready payment allocation preparation lines found."))

    for row in ready_lines:
        row.payment_allocation_line_status = "Payment Allocation Prepared"

    doc.status = "Payment Allocation Prepared"
    doc.payment_allocation_preparation_completion_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    _update_draft_remittance_import_allocation_status(doc, ready_lines)

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "ndis_remittance_import": doc.get("ndis_remittance_import"),
        "completed_line_count": len(ready_lines),
        "message": "Payment allocation preparation completed. No Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, or manual GL was created.",
    }


def validate_payment_allocation_preparation_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(PAYMENT_ALLOCATION_PREP_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(PAYMENT_ALLOCATION_PREP_RUN, "payment_allocation_preparation_run_ready"):
        doc.payment_allocation_preparation_run_ready = 1 if summary["payment_allocation_preparation_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["payment_allocation_preparation_run_ready"]:
        frappe.throw(
            _("Cannot set Payment Allocation Preparation Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Payment Allocation Preparation Approved" and doc.get("payment_allocation_preparation_completion_allowed"):
        frappe.throw(_("Payment Allocation Preparation Completion Allowed can only be ticked after the run is approved."))

    if doc.get("payment_entry_creation_allowed"):
        frappe.throw(_("Payment Entry creation is not allowed in Phase 27."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal creation is not allowed in Phase 27."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write-off creation is not allowed in Phase 27."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery creation is not allowed in Phase 27."))


def on_payment_allocation_preparation_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Payment Allocation Preparation Run Summary Sync Failed"
        )


def validate_crm_deal_phase27(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_payment_allocation_preparation_run_required"):
        required = doc.get("ndis_payment_allocation_preparation_run_required")

    if not required:
        return

    run = doc.get("ndis_payment_allocation_preparation_run") if _field_exists(CRM_DEAL, "ndis_payment_allocation_preparation_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Payment Allocation Preparation Run must be created and approved.")
        )

    if not _is_payment_allocation_prep_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Payment Allocation Preparation Run must be approved.")
        )


def validate_crm_deal_phase27_combined(doc, method=None):
    """
    Preserve Phase 2-26 validator chain, then add optional Phase 27 Payment Allocation Preparation validation.
    """
    try:
        from ndis_crm.phase26_remittance_matching_review import validate_crm_deal_phase26_combined
        validate_crm_deal_phase26_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase25_actual_remittance_import import validate_crm_deal_phase25_combined
            validate_crm_deal_phase25_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase24_remittance_import_preparation import validate_crm_deal_phase24_combined
                validate_crm_deal_phase24_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase27(doc, method)


def phase27_health_check():
    print("---- NDIS CRM Phase 27 Health Check ----")

    for dt in [
        PAYMENT_ALLOCATION_PREP_LINE,
        PAYMENT_ALLOCATION_PREP_RUN,
        REMITTANCE_MATCHING_REVIEW_RUN,
        REMITTANCE_MATCHING_REVIEW_LINE,
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
        NDIS_CLAIM_BATCH,
        NDIS_CLAIM_LINE,
        NDIS_REMITTANCE_IMPORT,
        SALES_INVOICE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for dt in [
        "Payment Entry",
        "Journal Entry",
        "GL Entry",
        "NDIS Recovery Case",
        "NDIS Write Off",
        PLAN_BUDGET,
        SERVICE_BOOKING,
        NDIS_SERVICE_TYPE,
        NDIS_SUPPORT_ITEM,
        NDIS_HOUSE,
        FINANCE_PROFILE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_payment_allocation_preparation_run_required",
        "ndis_payment_allocation_preparation_run",
        "payment_allocation_preparation_status",
        "payment_allocation_preparation_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    for doctype in [
        HANDOVER,
        FINANCE_ONBOARDING,
        OPERATIONS_SETUP,
        SCHEDULE_DRAFT,
        ROSTER_REQUEST,
        SERVICE_FILE,
        SESSION_DRAFT,
        EVIDENCE_REVIEW,
        DOWNSTREAM_PREPARATION,
        ATTENDANCE_DRAFT,
        BILLING_DRAFT,
        CLAIM_DRAFT,
        INVOICE_DRAFT,
        SALES_INVOICE_DRAFT_RUN,
        SALES_INVOICE_SUBMISSION_RUN,
        CLAIM_BATCH_DRAFT_RUN,
        CLAIM_BATCH_SUBMISSION_RUN,
        CLAIM_EXPORT_PREP_RUN,
        CLAIM_LODGEMENT_CONFIRMATION_RUN,
        REMITTANCE_IMPORT_PREP_RUN,
        ACTUAL_REMITTANCE_IMPORT_RUN,
        REMITTANCE_MATCHING_REVIEW_RUN,
        INTAKE,
    ]:
        if not _doctype_exists(doctype):
            print(f"{doctype}: OPTIONAL / MISSING")
            continue

        for field in [
            "ndis_payment_allocation_preparation_run",
            "payment_allocation_preparation_status",
            "payment_allocation_preparation_ready",
        ]:
            print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")

    print("NDIS CRM Payment Allocation Preparation Run records:", frappe.db.count(PAYMENT_ALLOCATION_PREP_RUN) if _doctype_exists(PAYMENT_ALLOCATION_PREP_RUN) else 0)
    print("Phase 27 creates CRM payment allocation preparation records only.")
    print("Phase 27 does not create Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, or manual GL.")
    print("---- End Phase 27 Health Check ----")
