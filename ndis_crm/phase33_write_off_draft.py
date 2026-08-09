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
WRITE_OFF_PREPARATION_LINE = "NDIS CRM Write Off Preparation Line"

WRITE_OFF_DRAFT_RUN = "NDIS CRM Write Off Draft Run"
WRITE_OFF_DRAFT_LINE = "NDIS CRM Write Off Draft Line"

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
    "Ready for Write Off Draft Creation",
    "Write Off Draft Run Approved",
    "Write Off Drafts Created",
]

APPROVED_STATUSES = [
    "Write Off Draft Run Approved",
    "Write Off Drafts Created",
]

SOURCE_READY_STATUSES = [
    "Write Off Prepared",
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
        frappe.throw(_("You do not have permission to perform this write-off draft action."))


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


def _optional_write_off_doctype():
    if _doctype_exists(NDIS_WRITE_OFF):
        return NDIS_WRITE_OFF
    return None


def _existing_run_for_preparation_run(write_off_preparation_run):
    if not _doctype_exists(WRITE_OFF_DRAFT_RUN):
        return None

    if _field_exists(WRITE_OFF_PREPARATION_RUN, "ndis_write_off_draft_run"):
        existing = frappe.db.get_value(
            WRITE_OFF_PREPARATION_RUN,
            write_off_preparation_run,
            "ndis_write_off_draft_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        WRITE_OFF_DRAFT_RUN,
        {"write_off_preparation_run": write_off_preparation_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(WRITE_OFF_DRAFT_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_write_off_draft_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_write_off_draft_run")
        if existing:
            return existing

    return frappe.db.get_value(WRITE_OFF_DRAFT_RUN, {"crm_deal": deal}, "name")


def _get_write_off_preparation_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_write_off_preparation_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_write_off_preparation_run")
        if run:
            return run

    if _doctype_exists(WRITE_OFF_PREPARATION_RUN):
        return frappe.db.get_value(WRITE_OFF_PREPARATION_RUN, {"crm_deal": deal}, "name")

    return None


def _is_write_off_prepared(run):
    if not run or not frappe.db.exists(WRITE_OFF_PREPARATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        WRITE_OFF_PREPARATION_RUN,
        run,
        ["status", "write_off_preparation_run_ready"],
    )

    return status in SOURCE_READY_STATUSES and bool(ready)


def _is_write_off_draft_approved(run):
    if not run or not frappe.db.exists(WRITE_OFF_DRAFT_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        WRITE_OFF_DRAFT_RUN,
        run,
        ["status", "write_off_draft_run_ready"],
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
    ]:
        if _field_exists(NDIS_REMITTANCE_IMPORT, fieldname):
            out[fieldname] = frappe.db.get_value(NDIS_REMITTANCE_IMPORT, ndis_remittance_import, fieldname)

    return out


def _append_line_if_missing(doc, row_data):
    existing = {
        row.write_off_draft_source_key
        for row in doc.get("write_off_draft_lines") or []
        if row.get("write_off_draft_source_key")
    }

    key = row_data.get("write_off_draft_source_key")

    if key and key in existing:
        return False

    doc.append("write_off_draft_lines", row_data)
    return True


def _source_key(row):
    return row.get("write_off_preparation_source_key") or "|".join([
        str(row.get("service_line") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("ndis_remittance_import") or ""),
        str(row.get("write_off_treatment") or ""),
        str(row.get("actual_payment_reference") or ""),
    ])


def _build_draft_line_from_preparation_line(row, source_doc):
    invoice_snapshot = _sales_invoice_snapshot(row.get("sales_invoice"))
    payment_entry_snapshot = _payment_entry_snapshot(row.get("payment_entry"))
    remittance_snapshot = _remittance_import_snapshot(row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"))

    proposed_amount = _to_float(row.get("proposed_write_off_amount"))

    source_ready = bool(
        source_doc.get("status") == "Write Off Prepared"
        and row.get("write_off_preparation_line_status") == "Write Off Prepared"
        and row.get("write_off_preparation_source_ready")
        and row.get("write_off_review_complete")
        and row.get("write_off_decision_authorized")
        and row.get("line_ready_for_write_off_preparation")
        and not row.get("write_off_preparation_hold")
        and not row.get("write_off_posting_authorized")
        and not row.get("journal_authorized")
        and not row.get("recovery_authorized")
        and not row.get("adjustment_authorized")
        and not row.get("bank_reconciliation_authorized")
        and proposed_amount > 0
    )

    target_mode = source_doc.get("target_draft_mode") or "CRM Draft Only"

    return {
        "write_off_draft_source_key": _source_key(row),
        "target_draft_doctype": None,
        "target_draft_name": None,
        "target_draft_docstatus": None,

        "ndis_remittance_import": row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"),
        "ndis_remittance_import_docstatus": int(remittance_snapshot.get("docstatus") or 0) if remittance_snapshot else None,
        "ndis_remittance_import_status": remittance_snapshot.get("status") or remittance_snapshot.get("import_status") or remittance_snapshot.get("remittance_status"),

        "payment_entry": row.get("payment_entry"),
        "payment_entry_docstatus": int(payment_entry_snapshot.get("docstatus") or 0) if payment_entry_snapshot else row.get("payment_entry_docstatus"),
        "payment_entry_status": payment_entry_snapshot.get("status") or row.get("payment_entry_status"),

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

        "proposed_write_off_amount": proposed_amount,
        "write_off_reason": row.get("write_off_reason"),
        "write_off_treatment": row.get("write_off_treatment"),
        "write_off_basis": row.get("write_off_basis"),
        "target_draft_mode": target_mode,

        "write_off_draft_source_ready": 1 if source_ready else 0,
        "write_off_draft_review_complete": 0,
        "write_off_draft_authorized": 0,

        "write_off_submit_authorized": 0,
        "journal_entry_authorized": 0,
        "manual_gl_authorized": 0,
        "recovery_authorized": 0,
        "adjustment_authorized": 0,
        "bank_reconciliation_authorized": 0,

        "write_off_draft_hold": 0 if source_ready else 1,
        "write_off_draft_hold_reason": None if source_ready else "Write-off preparation source is not ready for draft creation.",
        "line_ready_for_write_off_draft": 0,
        "write_off_draft_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_write_off_preparation_run(doc, source):
    created = 0

    for row in source.get("write_off_preparation_lines") or []:
        if row.get("write_off_preparation_line_status") != "Write Off Prepared":
            continue

        if _to_float(row.get("proposed_write_off_amount")) <= 0:
            continue

        data = _build_draft_line_from_preparation_line(row, source)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _active_draft_lines(doc):
    return [
        row for row in doc.get("write_off_draft_lines") or []
        if _to_float(row.get("proposed_write_off_amount")) > 0
    ]


def _calculate_totals(doc):
    line_count = len(doc.get("write_off_draft_lines") or [])
    amount_total = 0
    ready_count = 0
    hold_count = 0
    crm_draft_count = 0
    external_draft_count = 0

    blocked_submit_count = 0
    blocked_journal_count = 0
    blocked_gl_count = 0
    blocked_recovery_count = 0
    blocked_adjustment_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("write_off_draft_lines") or []:
        amount_total += _to_float(row.get("proposed_write_off_amount"))

        if row.get("line_ready_for_write_off_draft"):
            ready_count += 1

        if row.get("write_off_draft_hold"):
            hold_count += 1

        if row.get("target_draft_doctype") == WRITE_OFF_DRAFT_LINE or not row.get("target_draft_doctype"):
            crm_draft_count += 1

        if row.get("target_draft_doctype") and row.get("target_draft_doctype") != WRITE_OFF_DRAFT_LINE:
            external_draft_count += 1

        if row.get("write_off_submit_authorized"):
            blocked_submit_count += 1

        if row.get("journal_entry_authorized"):
            blocked_journal_count += 1

        if row.get("manual_gl_authorized"):
            blocked_gl_count += 1

        if row.get("recovery_authorized"):
            blocked_recovery_count += 1

        if row.get("adjustment_authorized"):
            blocked_adjustment_count += 1

        if row.get("bank_reconciliation_authorized"):
            blocked_bank_rec_count += 1

    return {
        "write_off_draft_line_count": line_count,
        "write_off_draft_amount_total": round(amount_total, 2),
        "write_off_draft_ready_count": ready_count,
        "write_off_draft_hold_count": hold_count,
        "crm_write_off_draft_count": crm_draft_count,
        "external_write_off_draft_count": external_draft_count,
        "blocked_write_off_submit_count": blocked_submit_count,
        "blocked_journal_entry_count": blocked_journal_count,
        "blocked_manual_gl_count": blocked_gl_count,
        "blocked_recovery_authorization_count": blocked_recovery_count,
        "blocked_adjustment_authorization_count": blocked_adjustment_count,
        "blocked_bank_reconciliation_count": blocked_bank_rec_count,
    }


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(WRITE_OFF_DRAFT_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Write Off Preparation Run linked",
        "complete": bool(doc.get("write_off_preparation_run")),
    })

    checks.append({
        "label": "Write Off Preparation completed",
        "complete": _is_write_off_prepared(doc.get("write_off_preparation_run")),
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
        "label": "Write-Off Draft Owner assigned",
        "complete": bool(doc.get("write_off_draft_owner")),
    })

    lines = _active_draft_lines(doc)
    no_candidates = bool(doc.get("no_write_off_draft_candidate_found"))

    checks.append({
        "label": "Write-off draft lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        source_not_ready = [row.service_line for row in lines if not row.get("write_off_draft_source_ready")]
        checks.append({
            "label": "Write-off draft source-ready flags are complete",
            "complete": not source_not_ready,
            "details": source_not_ready,
        })

        missing_amount = [row.service_line for row in lines if not _to_float(row.get("proposed_write_off_amount"))]
        checks.append({
            "label": "All lines have proposed write-off amount",
            "complete": not missing_amount,
            "details": missing_amount,
        })

        review_missing = [row.service_line for row in lines if not row.get("write_off_draft_review_complete")]
        checks.append({
            "label": "Write-off draft review complete",
            "complete": not review_missing,
            "details": review_missing,
        })

        authorization_missing = [row.service_line for row in lines if not row.get("write_off_draft_authorized")]
        checks.append({
            "label": "Write-off draft authorization complete",
            "complete": not authorization_missing,
            "details": authorization_missing,
        })

        submit_authorized = [row.service_line for row in lines if row.get("write_off_submit_authorized")]
        checks.append({
            "label": "Write-off submit authorization remains blocked in Phase 33",
            "complete": not submit_authorized,
            "details": submit_authorized,
        })

        journal_authorized = [row.service_line for row in lines if row.get("journal_entry_authorized")]
        checks.append({
            "label": "Journal Entry authorization remains blocked in Phase 33",
            "complete": not journal_authorized,
            "details": journal_authorized,
        })

        gl_authorized = [row.service_line for row in lines if row.get("manual_gl_authorized")]
        checks.append({
            "label": "Manual GL authorization remains blocked in Phase 33",
            "complete": not gl_authorized,
            "details": gl_authorized,
        })

        recovery_authorized = [row.service_line for row in lines if row.get("recovery_authorized")]
        checks.append({
            "label": "Recovery authorization remains blocked in Phase 33",
            "complete": not recovery_authorized,
            "details": recovery_authorized,
        })

        adjustment_authorized = [row.service_line for row in lines if row.get("adjustment_authorized")]
        checks.append({
            "label": "Adjustment authorization remains blocked in Phase 33",
            "complete": not adjustment_authorized,
            "details": adjustment_authorized,
        })

        bank_rec_authorized = [row.service_line for row in lines if row.get("bank_reconciliation_authorized")]
        checks.append({
            "label": "Bank reconciliation authorization remains blocked in Phase 33",
            "complete": not bank_rec_authorized,
            "details": bank_rec_authorized,
        })

        holds = [row.service_line for row in lines if row.get("write_off_draft_hold")]
        checks.append({
            "label": "No active write-off draft hold remains",
            "complete": not holds,
            "details": holds,
        })

        not_ready = [row.service_line for row in lines if not row.get("line_ready_for_write_off_draft")]
        checks.append({
            "label": "All active lines marked ready for write-off draft",
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
        "write_off_draft_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(WRITE_OFF_DRAFT_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(WRITE_OFF_DRAFT_RUN, "write_off_draft_run_ready"):
        doc.write_off_draft_run_ready = 1 if summary["write_off_draft_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_write_off_draft_run", doc.name)
        _db_set_if_field(doctype, name, "write_off_draft_status", doc.status)
        _db_set_if_field(doctype, name, "write_off_draft_ready", 1 if summary["write_off_draft_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_write_off_draft_run_from_write_off_preparation_run(write_off_preparation_run):
    _check_role()

    if not write_off_preparation_run:
        frappe.throw(_("NDIS CRM Write Off Preparation Run is required."))

    if not frappe.db.exists(WRITE_OFF_PREPARATION_RUN, write_off_preparation_run):
        frappe.throw(_("NDIS CRM Write Off Preparation Run {0} was not found.").format(write_off_preparation_run))

    existing = _existing_run_for_preparation_run(write_off_preparation_run)
    if existing:
        return {
            "doctype": WRITE_OFF_DRAFT_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Write Off Draft Run returned.",
        }

    source = frappe.get_doc(WRITE_OFF_PREPARATION_RUN, write_off_preparation_run)

    doc = frappe.new_doc(WRITE_OFF_DRAFT_RUN)
    doc.status = "Draft"
    doc.write_off_preparation_run = source.name
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
    doc.write_off_draft_owner = frappe.session.user
    doc.write_off_preparation_owner = source.get("write_off_preparation_owner")
    doc.target_draft_mode = "CRM Draft Only"
    doc.optional_ndis_write_off_doctype_available = 1 if _optional_write_off_doctype() else 0
    doc.write_off_draft_creation_allowed = 0
    doc.external_write_off_draft_creation_allowed = 0
    doc.write_off_submit_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    created_count = _generate_lines_from_write_off_preparation_run(doc, source)

    if created_count == 0:
        doc.no_write_off_draft_candidate_found = 1
    else:
        doc.no_write_off_draft_candidate_found = 0

    if _field_exists(WRITE_OFF_DRAFT_RUN, "write_off_draft_line_count"):
        doc.write_off_draft_line_count = created_count

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.write_off_draft_run_ready = 1 if summary["write_off_draft_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": WRITE_OFF_DRAFT_RUN,
        "name": doc.name,
        "created": True,
        "write_off_draft_line_count": created_count,
        "no_write_off_draft_candidate_found": bool(doc.no_write_off_draft_candidate_found),
        "message": "NDIS CRM Write Off Draft Run created successfully.",
    }


@frappe.whitelist()
def create_write_off_draft_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": WRITE_OFF_DRAFT_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Write Off Draft Run returned.",
        }

    source_run = _get_write_off_preparation_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Write Off Preparation Run before creating Write Off Draft Run."))

    return create_write_off_draft_run_from_write_off_preparation_run(source_run)


@frappe.whitelist()
def generate_write_off_draft_lines(write_off_draft_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_DRAFT_RUN, write_off_draft_run)

    if not doc.get("write_off_preparation_run"):
        frappe.throw(_("Write Off Preparation Run is required."))

    source = frappe.get_doc(WRITE_OFF_PREPARATION_RUN, doc.write_off_preparation_run)
    created_count = _generate_lines_from_write_off_preparation_run(doc, source)

    if created_count == 0 and not doc.get("write_off_draft_lines"):
        doc.no_write_off_draft_candidate_found = 1
    else:
        doc.no_write_off_draft_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Write-off draft lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_write_off_draft_readiness(write_off_draft_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_DRAFT_RUN, write_off_draft_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Write Off Draft Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_write_off_draft(write_off_draft_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_DRAFT_RUN, write_off_draft_run)
    summary = _calculate_readiness(doc)

    if not summary["write_off_draft_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Write Off Draft Creation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Write Off Draft Creation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.write_off_draft_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": WRITE_OFF_DRAFT_RUN,
        "name": doc.name,
        "message": "Write Off Draft Run marked Ready.",
    }


@frappe.whitelist()
def approve_write_off_draft_run(write_off_draft_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_DRAFT_RUN, write_off_draft_run)
    summary = _calculate_readiness(doc)

    if not summary["write_off_draft_run_ready"]:
        frappe.throw(
            _("Cannot approve Write Off Draft Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Write Off Draft Run Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.write_off_draft_run_ready = 1
    doc.write_off_draft_creation_allowed = 0
    doc.external_write_off_draft_creation_allowed = 0
    doc.write_off_submit_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("write_off_draft_lines") or []:
        if row.get("write_off_draft_line_status") in ["Draft", "Ready"]:
            row.write_off_draft_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": WRITE_OFF_DRAFT_RUN,
        "name": doc.name,
        "message": "Write Off Draft Run approved. No write-off, Journal Entry, GL, recovery, adjustment, or bank reconciliation was created.",
    }


def _ready_lines_for_draft_creation(doc):
    ready = []

    for row in _active_draft_lines(doc):
        if row.get("write_off_draft_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_write_off_draft"):
            continue

        if not row.get("write_off_draft_review_complete"):
            continue

        if not row.get("write_off_draft_authorized"):
            continue

        if row.get("write_off_submit_authorized"):
            continue

        if row.get("journal_entry_authorized"):
            continue

        if row.get("manual_gl_authorized"):
            continue

        if row.get("recovery_authorized"):
            continue

        if row.get("adjustment_authorized"):
            continue

        if row.get("bank_reconciliation_authorized"):
            continue

        if row.get("write_off_draft_hold"):
            continue

        if row.get("target_draft_name"):
            continue

        ready.append(row)

    return ready


def _create_optional_ndis_write_off_draft(run_doc, row):
    target_doctype = _optional_write_off_doctype()
    if not target_doctype:
        frappe.throw(_("NDIS Write Off DocType is not available. Use CRM Draft Only mode."))

    target = frappe.new_doc(target_doctype)

    _set_first_existing(target, ["crm_deal", "deal"], run_doc.get("crm_deal"))
    _set_first_existing(target, ["participant_customer", "customer", "party"], run_doc.get("participant_customer"))
    _set_first_existing(target, ["participant_name"], run_doc.get("participant_name"))
    _set_first_existing(target, ["ndis_number"], run_doc.get("ndis_number"))
    _set_first_existing(target, ["company"], run_doc.get("company"))
    _set_first_existing(target, ["ndis_remittance_import", "remittance_import"], row.get("ndis_remittance_import"))
    _set_first_existing(target, ["sales_invoice", "invoice"], row.get("sales_invoice"))
    _set_first_existing(target, ["payment_entry"], row.get("payment_entry"))
    _set_first_existing(target, ["ndis_claim_batch", "claim_batch"], row.get("ndis_claim_batch"))
    _set_first_existing(target, ["ndis_claim_line", "claim_line"], row.get("ndis_claim_line"))
    _set_first_existing(target, ["service_line"], row.get("service_line"))
    _set_first_existing(target, ["support_item"], row.get("support_item"))
    _set_first_existing(target, ["finance_service_type", "service_type"], row.get("finance_service_type"))
    _set_first_existing(target, ["plan_budget"], row.get("plan_budget"))
    _set_first_existing(target, ["service_booking"], row.get("service_booking"))
    _set_first_existing(target, ["funding_source"], row.get("funding_source"))
    _set_first_existing(target, ["write_off_amount", "amount", "proposed_write_off_amount"], row.get("proposed_write_off_amount"))
    _set_first_existing(target, ["write_off_reason", "reason"], row.get("write_off_reason"))
    _set_first_existing(target, ["write_off_treatment", "treatment"], row.get("write_off_treatment"))
    _set_first_existing(target, ["write_off_basis", "basis"], row.get("write_off_basis"))
    _set_first_existing(target, ["status"], "Draft")
    _set_first_existing(target, ["ndis_crm_write_off_draft_run"], run_doc.name)
    _set_first_existing(target, ["ndis_crm_write_off_draft_line"], row.name)
    _set_first_existing(target, ["posting_blocked", "submit_blocked", "ndis_crm_submit_blocked"], 1)
    _set_first_existing(target, ["remarks", "notes"], f"Draft only. Created from {run_doc.doctype} {run_doc.name}. Submission/posting is blocked until a later explicit gate.")

    target.insert(ignore_permissions=True)

    if getattr(target, "docstatus", 0) != 0:
        frappe.throw(_("Safety error: NDIS Write Off draft was not created in Draft state."))

    return target.name


@frappe.whitelist()
def create_write_off_drafts(write_off_draft_run):
    _check_role()

    doc = frappe.get_doc(WRITE_OFF_DRAFT_RUN, write_off_draft_run)

    if doc.status != "Write Off Draft Run Approved":
        frappe.throw(_("Write Off Draft Run must be approved before creating write-off drafts."))

    if not doc.get("write_off_draft_creation_allowed"):
        frappe.throw(_("Tick Write Off Draft Creation Allowed before creating write-off drafts."))

    if doc.get("write_off_submit_allowed"):
        frappe.throw(_("Write Off Submit Allowed must remain unticked in Phase 33."))

    if doc.get("journal_entry_creation_allowed"):
        frappe.throw(_("Journal Entry Creation Allowed must remain unticked in Phase 33."))

    if doc.get("manual_gl_creation_allowed"):
        frappe.throw(_("Manual GL Creation Allowed must remain unticked in Phase 33."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery Creation Allowed must remain unticked in Phase 33."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment Creation Allowed must remain unticked in Phase 33."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank Reconciliation Allowed must remain unticked in Phase 33."))

    summary = _calculate_readiness(doc)

    if not summary["write_off_draft_run_ready"]:
        frappe.throw(
            _("Cannot create write-off drafts. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_draft_creation(doc)

    if not ready_lines and not doc.get("no_write_off_draft_candidate_found"):
        frappe.throw(_("No ready write-off draft lines found."))

    external_created = []
    crm_drafts = []

    for row in ready_lines:
        if doc.get("target_draft_mode") == "NDIS Write Off Draft If Available":
            if not doc.get("external_write_off_draft_creation_allowed"):
                frappe.throw(_("External Write Off Draft Creation Allowed must be ticked for NDIS Write Off Draft mode."))

            target_name = _create_optional_ndis_write_off_draft(doc, row)
            row.target_draft_doctype = NDIS_WRITE_OFF
            row.target_draft_name = target_name
            row.target_draft_docstatus = 0
            row.write_off_draft_line_status = "External Write Off Draft Created"
            external_created.append(target_name)
        else:
            row.target_draft_doctype = WRITE_OFF_DRAFT_LINE
            row.target_draft_name = row.name
            row.target_draft_docstatus = 0
            row.write_off_draft_line_status = "CRM Write Off Draft Prepared"
            crm_drafts.append(row.name)

    doc.status = "Write Off Drafts Created"
    doc.write_off_draft_creation_allowed = 0
    doc.external_write_off_draft_creation_allowed = 0
    doc.write_off_submit_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.drafted_by = frappe.session.user
    doc.drafted_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "crm_write_off_drafts": crm_drafts,
        "external_write_off_drafts": external_created,
        "crm_write_off_draft_count": len(crm_drafts),
        "external_write_off_draft_count": len(external_created),
        "message": "Write-off drafts created/prepared. No submission, Journal Entry, GL Entry, Payment Entry, recovery, adjustment, or bank reconciliation was created.",
    }


def validate_write_off_draft_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(WRITE_OFF_DRAFT_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(WRITE_OFF_DRAFT_RUN, "write_off_draft_run_ready"):
        doc.write_off_draft_run_ready = 1 if summary["write_off_draft_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["write_off_draft_run_ready"]:
        frappe.throw(
            _("Cannot set Write Off Draft Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Write Off Draft Run Approved" and doc.get("write_off_draft_creation_allowed"):
        frappe.throw(_("Write Off Draft Creation Allowed can only be ticked after the run is approved."))

    if doc.get("external_write_off_draft_creation_allowed") and doc.get("target_draft_mode") != "NDIS Write Off Draft If Available":
        frappe.throw(_("External Write Off Draft Creation Allowed can only be used with NDIS Write Off Draft If Available mode."))

    if doc.get("write_off_submit_allowed"):
        frappe.throw(_("Write-off submission is not allowed in Phase 33."))

    if doc.get("journal_entry_creation_allowed"):
        frappe.throw(_("Journal Entry creation is not allowed in Phase 33."))

    if doc.get("manual_gl_creation_allowed"):
        frappe.throw(_("Manual GL creation is not allowed in Phase 33."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery creation is not allowed in Phase 33."))

    if doc.get("adjustment_creation_allowed"):
        frappe.throw(_("Adjustment creation is not allowed in Phase 33."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank reconciliation is not allowed in Phase 33."))


def on_write_off_draft_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Write Off Draft Run Summary Sync Failed"
        )


def validate_optional_ndis_write_off_phase33_submit_guard(doc, method=None):
    if doc.doctype != NDIS_WRITE_OFF:
        return

    if not _field_exists(NDIS_WRITE_OFF, "ndis_crm_write_off_draft_run"):
        return

    if not doc.get("ndis_crm_write_off_draft_run"):
        return

    frappe.throw(
        _("This NDIS Write Off was created by NDIS CRM Phase 33 as draft-only. Submission/posting is blocked until a later controlled gate.")
    )


def validate_crm_deal_phase33(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_write_off_draft_run_required"):
        required = doc.get("ndis_write_off_draft_run_required")

    if not required:
        return

    run = doc.get("ndis_write_off_draft_run") if _field_exists(CRM_DEAL, "ndis_write_off_draft_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Write Off Draft Run must be created and approved/completed.")
        )

    if not _is_write_off_draft_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Write Off Draft Run must be approved/completed.")
        )


def validate_crm_deal_phase33_combined(doc, method=None):
    """
    Preserve Phase 2-32 validator chain, then add optional Phase 33 Write-Off Draft validation.
    """
    try:
        from ndis_crm.phase32_write_off_preparation import validate_crm_deal_phase32_combined
        validate_crm_deal_phase32_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase31_variance_rejection_review import validate_crm_deal_phase31_combined
            validate_crm_deal_phase31_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase30_remittance_import_finalisation import validate_crm_deal_phase30_combined
                validate_crm_deal_phase30_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase33(doc, method)


def phase33_health_check():
    print("---- NDIS CRM Phase 33 Health Check ----")

    for dt in [
        WRITE_OFF_DRAFT_LINE,
        WRITE_OFF_DRAFT_RUN,
        WRITE_OFF_PREPARATION_RUN,
        WRITE_OFF_PREPARATION_LINE,
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
        NDIS_REMITTANCE_IMPORT,
        NDIS_CLAIM_BATCH,
        NDIS_CLAIM_LINE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for dt in [
        NDIS_WRITE_OFF,
        JOURNAL_ENTRY,
        GL_ENTRY,
        NDIS_RECOVERY_CASE,
        "Bank Reconciliation Tool",
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    print(f"Optional NDIS Write Off draft target available: {bool(_optional_write_off_doctype())}")

    for field in [
        "ndis_write_off_draft_run_required",
        "ndis_write_off_draft_run",
        "write_off_draft_status",
        "write_off_draft_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print("NDIS CRM Write Off Draft Run records:", frappe.db.count(WRITE_OFF_DRAFT_RUN) if _doctype_exists(WRITE_OFF_DRAFT_RUN) else 0)
    print("Phase 33 creates CRM write-off draft records and optional draft NDIS Write Off records only.")
    print("Phase 33 does not submit, create Journal Entry, create manual GL, create Payment Entry, create recovery case, create adjustment, create bank reconciliation, create Sales Invoice, create Claim Batch, create Claim Line, or create NDIS Remittance Import.")
    print("---- End Phase 33 Health Check ----")
