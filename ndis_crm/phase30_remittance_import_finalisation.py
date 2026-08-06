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
PAYMENT_ENTRY_SUBMISSION_LINE = "NDIS CRM Payment Entry Submission Line"

REMITTANCE_IMPORT_FINALISATION_RUN = "NDIS CRM Remittance Import Finalisation Run"
REMITTANCE_IMPORT_FINALISATION_LINE = "NDIS CRM Remittance Import Finalisation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"

READY_STATUSES = [
    "Ready for Remittance Import Finalisation",
    "Remittance Import Finalisation Approved",
    "Remittance Import Submitted",
    "Remittance Import Finalised",
]

APPROVED_STATUSES = [
    "Remittance Import Finalisation Approved",
    "Remittance Import Submitted",
    "Remittance Import Finalised",
]

SOURCE_READY_STATUSES = [
    "Payment Entries Submitted",
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
        frappe.throw(_("You do not have permission to perform this remittance import finalisation action."))


def _doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
    return bool(
        frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
        or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
    )


def _is_submittable(doctype):
    if not _doctype_exists(doctype):
        return False

    try:
        meta = frappe.get_meta(doctype)
        return bool(getattr(meta, "is_submittable", 0))
    except Exception:
        return bool(frappe.db.get_value("DocType", doctype, "is_submittable"))


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


def _existing_run_for_payment_entry_submission_run(payment_entry_submission_run):
    if not _doctype_exists(REMITTANCE_IMPORT_FINALISATION_RUN):
        return None

    if _field_exists(PAYMENT_ENTRY_SUBMISSION_RUN, "ndis_remittance_import_finalisation_run"):
        existing = frappe.db.get_value(
            PAYMENT_ENTRY_SUBMISSION_RUN,
            payment_entry_submission_run,
            "ndis_remittance_import_finalisation_run",
        )
        if existing:
            return existing

    return frappe.db.get_value(
        REMITTANCE_IMPORT_FINALISATION_RUN,
        {"payment_entry_submission_run": payment_entry_submission_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(REMITTANCE_IMPORT_FINALISATION_RUN):
        return None

    if _field_exists(CRM_DEAL, "ndis_remittance_import_finalisation_run"):
        existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_remittance_import_finalisation_run")
        if existing:
            return existing

    return frappe.db.get_value(REMITTANCE_IMPORT_FINALISATION_RUN, {"crm_deal": deal}, "name")


def _get_payment_entry_submission_run_for_deal(deal):
    if _field_exists(CRM_DEAL, "ndis_payment_entry_submission_run"):
        run = frappe.db.get_value(CRM_DEAL, deal, "ndis_payment_entry_submission_run")
        if run:
            return run

    if _doctype_exists(PAYMENT_ENTRY_SUBMISSION_RUN):
        return frappe.db.get_value(PAYMENT_ENTRY_SUBMISSION_RUN, {"crm_deal": deal}, "name")

    return None


def _is_payment_entry_submission_completed(run):
    if not run or not frappe.db.exists(PAYMENT_ENTRY_SUBMISSION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        PAYMENT_ENTRY_SUBMISSION_RUN,
        run,
        ["status", "payment_entry_submission_run_ready"],
    )

    return status in SOURCE_READY_STATUSES and bool(ready)


def _is_remittance_finalisation_approved(run):
    if not run or not frappe.db.exists(REMITTANCE_IMPORT_FINALISATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        REMITTANCE_IMPORT_FINALISATION_RUN,
        run,
        ["status", "remittance_import_finalisation_run_ready"],
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
        row.remittance_finalisation_source_key
        for row in doc.get("remittance_finalisation_lines") or []
        if row.get("remittance_finalisation_source_key")
    }

    key = row_data.get("remittance_finalisation_source_key")

    if key and key in existing:
        return False

    doc.append("remittance_finalisation_lines", row_data)
    return True


def _source_key(row):
    return row.get("payment_entry_submission_source_key") or "|".join([
        str(row.get("payment_entry") or ""),
        str(row.get("ndis_remittance_import") or ""),
        str(row.get("sales_invoice") or ""),
        str(row.get("actual_payment_reference") or ""),
    ])


def _build_finalisation_line_from_submission_line(row, source_doc):
    payment_entry_snapshot = _payment_entry_snapshot(row.get("payment_entry"))
    remittance_snapshot = _remittance_import_snapshot(row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"))

    source_ready = bool(
        source_doc.get("status") == "Payment Entries Submitted"
        and row.get("payment_entry_submission_line_status") == "Payment Entry Submitted"
        and row.get("payment_entry")
        and int(payment_entry_snapshot.get("docstatus") or 0) == 1
        and row.get("ndis_remittance_import")
        and int(remittance_snapshot.get("docstatus") or 0) in [0, 1]
        and row.get("submission_source_ready")
        and row.get("payment_entry_submission_review_complete")
        and row.get("payment_entry_submission_authorized")
        and row.get("line_ready_for_payment_entry_submission")
        and not row.get("submission_hold")
        and not row.get("journal_authorized")
        and not row.get("write_off_authorized")
        and not row.get("recovery_authorized")
        and not row.get("bank_reconciliation_authorized")
    )

    return {
        "remittance_finalisation_source_key": _source_key(row),
        "ndis_remittance_import": row.get("ndis_remittance_import") or source_doc.get("ndis_remittance_import"),
        "ndis_remittance_import_docstatus": int(remittance_snapshot.get("docstatus") or 0) if remittance_snapshot else None,
        "ndis_remittance_import_status": remittance_snapshot.get("status") or remittance_snapshot.get("import_status") or remittance_snapshot.get("remittance_status"),
        "payment_entry": row.get("payment_entry"),
        "payment_entry_docstatus": int(payment_entry_snapshot.get("docstatus") or 0) if payment_entry_snapshot else row.get("payment_entry_docstatus"),
        "payment_entry_status": payment_entry_snapshot.get("status") or row.get("payment_entry_status"),
        "payment_entry_type": payment_entry_snapshot.get("payment_type") or row.get("payment_entry_type"),
        "party_type": payment_entry_snapshot.get("party_type") or row.get("party_type"),
        "party": payment_entry_snapshot.get("party") or row.get("party"),
        "payment_entry_posting_date": payment_entry_snapshot.get("posting_date") or row.get("payment_entry_posting_date"),
        "payment_entry_reference_no": payment_entry_snapshot.get("reference_no") or row.get("payment_entry_reference_no"),
        "payment_entry_reference_date": payment_entry_snapshot.get("reference_date") or row.get("payment_entry_reference_date"),
        "proposed_payment_amount": row.get("proposed_payment_amount"),
        "paid_amount": payment_entry_snapshot.get("paid_amount") or row.get("paid_amount"),
        "received_amount": payment_entry_snapshot.get("received_amount") or row.get("received_amount"),
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
        "finalisation_source_ready": 1 if source_ready else 0,
        "remittance_import_finalisation_review_complete": 0,
        "remittance_import_finalisation_authorized": 0,
        "remittance_import_submit_authorized": 0,
        "journal_authorized": 0,
        "write_off_authorized": 0,
        "recovery_authorized": 0,
        "bank_reconciliation_authorized": 0,
        "finalisation_hold": 0 if source_ready else 1,
        "finalisation_hold_reason": None if source_ready else "Payment Entry submission source is not ready for remittance import finalisation.",
        "line_ready_for_remittance_import_finalisation": 0,
        "remittance_finalisation_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_payment_entry_submission_run(doc, source):
    created = 0

    for row in source.get("payment_entry_submission_lines") or []:
        if row.get("payment_entry_submission_line_status") != "Payment Entry Submitted":
            continue

        if not row.get("payment_entry"):
            continue

        data = _build_finalisation_line_from_submission_line(row, source)

        if _append_line_if_missing(doc, data):
            created += 1

    return created


def _active_finalisation_lines(doc):
    return [
        row for row in doc.get("remittance_finalisation_lines") or []
        if row.get("payment_entry")
        and row.get("ndis_remittance_import")
    ]


def _calculate_totals(doc):
    line_count = len(doc.get("remittance_finalisation_lines") or [])
    active_lines = _active_finalisation_lines(doc)

    amount_total = 0
    submitted_payment_entries = set()
    remittance_imports = set()
    ready_count = 0
    hold_count = 0
    blocked_submit_count = 0
    blocked_journal_count = 0
    blocked_writeoff_count = 0
    blocked_recovery_count = 0
    blocked_bank_rec_count = 0

    for row in doc.get("remittance_finalisation_lines") or []:
        amount_total += _to_float(row.get("proposed_payment_amount"))

        if row.get("payment_entry") and int(row.get("payment_entry_docstatus") or 0) == 1:
            submitted_payment_entries.add(row.get("payment_entry"))

        if row.get("ndis_remittance_import"):
            remittance_imports.add(row.get("ndis_remittance_import"))

        if row.get("line_ready_for_remittance_import_finalisation"):
            ready_count += 1

        if row.get("finalisation_hold"):
            hold_count += 1

        if row.get("remittance_import_submit_authorized"):
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
        "remittance_finalisation_line_count": line_count,
        "active_finalisation_line_count": len(active_lines),
        "finalisation_amount_total": round(amount_total, 2),
        "submitted_payment_entry_count": len(submitted_payment_entries),
        "remittance_import_count": len(remittance_imports),
        "remittance_finalisation_ready_count": ready_count,
        "finalisation_hold_count": hold_count,
        "blocked_submit_authorization_count": blocked_submit_count,
        "blocked_journal_authorization_count": blocked_journal_count,
        "blocked_write_off_authorization_count": blocked_writeoff_count,
        "blocked_recovery_authorization_count": blocked_recovery_count,
        "blocked_bank_reconciliation_count": blocked_bank_rec_count,
    }


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(REMITTANCE_IMPORT_FINALISATION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Payment Entry Submission Run linked",
        "complete": bool(doc.get("payment_entry_submission_run")),
    })

    checks.append({
        "label": "Payment Entries submitted",
        "complete": _is_payment_entry_submission_completed(doc.get("payment_entry_submission_run")),
    })

    checks.append({
        "label": "NDIS Remittance Import DocType exists",
        "complete": _doctype_exists(NDIS_REMITTANCE_IMPORT),
    })

    checks.append({
        "label": "NDIS Remittance Import linked",
        "complete": bool(doc.get("ndis_remittance_import")),
    })

    if doc.get("ndis_remittance_import"):
        snapshot = _remittance_import_snapshot(doc.get("ndis_remittance_import"))
        if _is_submittable(NDIS_REMITTANCE_IMPORT):
            complete = int(snapshot.get("docstatus") or 0) == 0
            label = "NDIS Remittance Import is Draft before submission"
        else:
            complete = int(snapshot.get("docstatus") or 0) in [0, 1]
            label = "NDIS Remittance Import can be finalised"
        checks.append({"label": label, "complete": complete})
    else:
        checks.append({"label": "NDIS Remittance Import can be finalised", "complete": False})

    checks.append({
        "label": "Participant Customer linked",
        "complete": bool(doc.get("participant_customer")),
    })

    checks.append({
        "label": "Company selected",
        "complete": bool(doc.get("company")),
    })

    checks.append({
        "label": "Remittance Finalisation Owner assigned",
        "complete": bool(doc.get("remittance_finalisation_owner")),
    })

    active_lines = _active_finalisation_lines(doc)

    checks.append({
        "label": "At least one remittance finalisation line exists",
        "complete": bool(active_lines),
    })

    missing_payment_entry = [row.service_line for row in active_lines if not row.get("payment_entry")]
    checks.append({
        "label": "All active lines have Payment Entry reference",
        "complete": not missing_payment_entry,
        "details": missing_payment_entry,
    })

    payment_entry_not_submitted = []
    for row in active_lines:
        pe = row.get("payment_entry")
        if not pe:
            continue
        snapshot = _payment_entry_snapshot(pe)
        if int(snapshot.get("docstatus") or 0) != 1:
            payment_entry_not_submitted.append(pe)

    checks.append({
        "label": "All active Payment Entries are submitted",
        "complete": not payment_entry_not_submitted,
        "details": payment_entry_not_submitted,
    })

    source_not_ready = [row.service_line for row in active_lines if not row.get("finalisation_source_ready")]
    checks.append({
        "label": "Remittance finalisation source-ready flags are complete",
        "complete": not source_not_ready,
        "details": source_not_ready,
    })

    review_missing = [row.service_line for row in active_lines if not row.get("remittance_import_finalisation_review_complete")]
    checks.append({
        "label": "Remittance import finalisation review complete",
        "complete": not review_missing,
        "details": review_missing,
    })

    authorization_missing = [row.service_line for row in active_lines if not row.get("remittance_import_finalisation_authorized")]
    checks.append({
        "label": "Remittance import finalisation authorization complete",
        "complete": not authorization_missing,
        "details": authorization_missing,
    })

    direct_submit_flag_set = [row.service_line for row in active_lines if row.get("remittance_import_submit_authorized")]
    checks.append({
        "label": "Legacy direct remittance submit flags remain blocked on lines",
        "complete": not direct_submit_flag_set,
        "details": direct_submit_flag_set,
    })

    journal_authorized = [row.service_line for row in active_lines if row.get("journal_authorized")]
    checks.append({
        "label": "Journal authorization remains blocked in Phase 30",
        "complete": not journal_authorized,
        "details": journal_authorized,
    })

    writeoff_authorized = [row.service_line for row in active_lines if row.get("write_off_authorized")]
    checks.append({
        "label": "Write-off authorization remains blocked in Phase 30",
        "complete": not writeoff_authorized,
        "details": writeoff_authorized,
    })

    recovery_authorized = [row.service_line for row in active_lines if row.get("recovery_authorized")]
    checks.append({
        "label": "Recovery authorization remains blocked in Phase 30",
        "complete": not recovery_authorized,
        "details": recovery_authorized,
    })

    bank_rec_authorized = [row.service_line for row in active_lines if row.get("bank_reconciliation_authorized")]
    checks.append({
        "label": "Bank reconciliation authorization remains blocked in Phase 30",
        "complete": not bank_rec_authorized,
        "details": bank_rec_authorized,
    })

    holds = [row.service_line for row in active_lines if row.get("finalisation_hold")]
    checks.append({
        "label": "No active remittance finalisation hold remains",
        "complete": not holds,
        "details": holds,
    })

    not_ready = [row.service_line for row in active_lines if not row.get("line_ready_for_remittance_import_finalisation")]
    checks.append({
        "label": "All active lines marked ready for remittance import finalisation",
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
        "remittance_import_finalisation_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(REMITTANCE_IMPORT_FINALISATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(REMITTANCE_IMPORT_FINALISATION_RUN, "remittance_import_finalisation_run_ready"):
        doc.remittance_import_finalisation_run_ready = 1 if summary["remittance_import_finalisation_run_ready"] else 0

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
        (INTAKE, doc.get("participant_intake")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_remittance_import_finalisation_run", doc.name)
        _db_set_if_field(doctype, name, "remittance_import_finalisation_status", doc.status)
        _db_set_if_field(doctype, name, "remittance_import_finalisation_ready", 1 if summary["remittance_import_finalisation_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_remittance_import_finalisation_run_from_payment_entry_submission_run(payment_entry_submission_run):
    _check_role()

    if not payment_entry_submission_run:
        frappe.throw(_("NDIS CRM Payment Entry Submission Run is required."))

    if not frappe.db.exists(PAYMENT_ENTRY_SUBMISSION_RUN, payment_entry_submission_run):
        frappe.throw(_("NDIS CRM Payment Entry Submission Run {0} was not found.").format(payment_entry_submission_run))

    existing = _existing_run_for_payment_entry_submission_run(payment_entry_submission_run)
    if existing:
        return {
            "doctype": REMITTANCE_IMPORT_FINALISATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Remittance Import Finalisation Run returned.",
        }

    source = frappe.get_doc(PAYMENT_ENTRY_SUBMISSION_RUN, payment_entry_submission_run)

    doc = frappe.new_doc(REMITTANCE_IMPORT_FINALISATION_RUN)
    doc.status = "Draft"
    doc.payment_entry_submission_run = source.name
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
    doc.remittance_finalisation_owner = frappe.session.user
    doc.payment_entry_submission_owner = source.get("payment_entry_submission_owner")
    doc.payment_entry_draft_owner = source.get("payment_entry_draft_owner")
    doc.remittance_import_finalisation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    doc.ndis_remittance_import_submittable = 1 if _is_submittable(NDIS_REMITTANCE_IMPORT) else 0

    created_count = _generate_lines_from_payment_entry_submission_run(doc, source)

    if _field_exists(REMITTANCE_IMPORT_FINALISATION_RUN, "remittance_finalisation_line_count"):
        doc.remittance_finalisation_line_count = created_count

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.remittance_import_finalisation_run_ready = 1 if summary["remittance_import_finalisation_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": REMITTANCE_IMPORT_FINALISATION_RUN,
        "name": doc.name,
        "created": True,
        "remittance_finalisation_line_count": created_count,
        "message": "NDIS CRM Remittance Import Finalisation Run created successfully.",
    }


@frappe.whitelist()
def create_remittance_import_finalisation_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": REMITTANCE_IMPORT_FINALISATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Remittance Import Finalisation Run returned.",
        }

    source_run = _get_payment_entry_submission_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Payment Entry Submission Run before creating Remittance Import Finalisation Run."))

    return create_remittance_import_finalisation_run_from_payment_entry_submission_run(source_run)


@frappe.whitelist()
def generate_remittance_import_finalisation_lines(remittance_import_finalisation_run):
    _check_role()

    doc = frappe.get_doc(REMITTANCE_IMPORT_FINALISATION_RUN, remittance_import_finalisation_run)

    if not doc.get("payment_entry_submission_run"):
        frappe.throw(_("Payment Entry Submission Run is required."))

    source = frappe.get_doc(PAYMENT_ENTRY_SUBMISSION_RUN, doc.payment_entry_submission_run)
    created_count = _generate_lines_from_payment_entry_submission_run(doc, source)

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Remittance import finalisation lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_remittance_import_finalisation_readiness(remittance_import_finalisation_run):
    _check_role()

    doc = frappe.get_doc(REMITTANCE_IMPORT_FINALISATION_RUN, remittance_import_finalisation_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Remittance Import Finalisation Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_remittance_import_finalisation(remittance_import_finalisation_run):
    _check_role()

    doc = frappe.get_doc(REMITTANCE_IMPORT_FINALISATION_RUN, remittance_import_finalisation_run)
    summary = _calculate_readiness(doc)

    if not summary["remittance_import_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Remittance Import Finalisation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Remittance Import Finalisation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.remittance_import_finalisation_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": REMITTANCE_IMPORT_FINALISATION_RUN,
        "name": doc.name,
        "message": "Remittance Import Finalisation Run marked Ready.",
    }


@frappe.whitelist()
def approve_remittance_import_finalisation_run(remittance_import_finalisation_run):
    _check_role()

    doc = frappe.get_doc(REMITTANCE_IMPORT_FINALISATION_RUN, remittance_import_finalisation_run)
    summary = _calculate_readiness(doc)

    if not summary["remittance_import_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot approve Remittance Import Finalisation Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Remittance Import Finalisation Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.remittance_import_finalisation_run_ready = 1
    doc.remittance_import_finalisation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0

    for row in doc.get("remittance_finalisation_lines") or []:
        if row.get("remittance_finalisation_line_status") in ["Draft", "Ready"]:
            row.remittance_finalisation_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": REMITTANCE_IMPORT_FINALISATION_RUN,
        "name": doc.name,
        "message": "Remittance Import Finalisation Run approved. No finalisation/submission has happened yet.",
    }


def _ready_lines_for_finalisation(doc):
    ready = []

    for row in _active_finalisation_lines(doc):
        if row.get("remittance_finalisation_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_remittance_import_finalisation"):
            continue

        if not row.get("remittance_import_finalisation_review_complete"):
            continue

        if not row.get("remittance_import_finalisation_authorized"):
            continue

        if row.get("remittance_import_submit_authorized"):
            continue

        if row.get("journal_authorized"):
            continue

        if row.get("write_off_authorized"):
            continue

        if row.get("recovery_authorized"):
            continue

        if row.get("bank_reconciliation_authorized"):
            continue

        if row.get("finalisation_hold"):
            continue

        ready.append(row)

    return ready


def _unique_remittance_imports(lines):
    out = []
    seen = set()

    for row in lines:
        name = row.get("ndis_remittance_import")
        if not name or name in seen:
            continue
        seen.add(name)
        out.append(name)

    return out


def _prepare_remittance_import_for_phase30(name, run_doc):
    remittance_doc = frappe.get_doc(NDIS_REMITTANCE_IMPORT, name)

    _set_first_existing(remittance_doc, ["ndis_crm_remittance_import_finalisation_run"], run_doc.name)
    _set_first_existing(remittance_doc, ["ndis_crm_remittance_import_finalisation_status"], "Finalisation In Progress")
    _set_first_existing(remittance_doc, ["ndis_crm_remittance_import_finalisation_approved"], 1)
    _set_first_existing(remittance_doc, ["ndis_crm_remittance_import_finalisation_blocked"], 0)
    _set_first_existing(remittance_doc, ["crm_deal"], run_doc.get("crm_deal"))
    _set_first_existing(remittance_doc, ["finalisation_run", "crm_remittance_import_finalisation_run"], run_doc.name)
    _set_first_existing(remittance_doc, ["notes", "remarks"], f"Controlled finalisation from {run_doc.doctype} {run_doc.name}. No Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, or manual GL was created by Phase 30.")

    remittance_doc.save(ignore_permissions=True)

    return remittance_doc


def _mark_remittance_import_finalised(name, run_doc, submitted=False):
    status_text = "Submitted" if submitted else "Finalised"

    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "ndis_crm_remittance_import_finalisation_status", status_text)
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "ndis_crm_remittance_import_finalised_on", now())
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "ndis_crm_remittance_import_finalised_by", frappe.session.user)
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "ndis_crm_remittance_import_finalisation_blocked", 0)
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "status", "Remittance Import Submitted" if submitted else "Remittance Import Finalised")
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "import_status", "Remittance Import Submitted" if submitted else "Remittance Import Finalised")
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "remittance_status", "Remittance Import Submitted" if submitted else "Remittance Import Finalised")
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "finalised_by", frappe.session.user)
    _db_set_if_field(NDIS_REMITTANCE_IMPORT, name, "finalised_on", now())


@frappe.whitelist()
def finalise_remittance_import(remittance_import_finalisation_run):
    _check_role()

    doc = frappe.get_doc(REMITTANCE_IMPORT_FINALISATION_RUN, remittance_import_finalisation_run)

    if doc.status != "Remittance Import Finalisation Approved":
        frappe.throw(_("Remittance Import Finalisation Run must be approved before finalisation."))

    if not doc.get("remittance_import_finalisation_allowed"):
        frappe.throw(_("Tick Remittance Import Finalisation Allowed before finalising the remittance import."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal Creation Allowed must remain unticked in Phase 30."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write Off Creation Allowed must remain unticked in Phase 30."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery Creation Allowed must remain unticked in Phase 30."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank Reconciliation Allowed must remain unticked in Phase 30."))

    summary = _calculate_readiness(doc)

    if not summary["remittance_import_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot finalise NDIS Remittance Import. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_finalisation(doc)

    if not ready_lines:
        frappe.throw(_("No ready remittance import finalisation lines found."))

    remittance_imports = _unique_remittance_imports(ready_lines)

    if not remittance_imports:
        frappe.throw(_("No NDIS Remittance Import linked for finalisation."))

    submitted_imports = []
    finalised_imports = []
    submittable = _is_submittable(NDIS_REMITTANCE_IMPORT)

    for name in remittance_imports:
        remittance_doc = _prepare_remittance_import_for_phase30(name, doc)

        if submittable:
            if getattr(remittance_doc, "docstatus", 0) != 0:
                frappe.throw(_("NDIS Remittance Import {0} is not in Draft state.").format(name))

            remittance_doc.submit()

            if getattr(remittance_doc, "docstatus", 0) != 1:
                frappe.throw(_("NDIS Remittance Import {0} was not submitted successfully.").format(name))

            _mark_remittance_import_finalised(name, doc, submitted=True)
            submitted_imports.append(name)
        else:
            _mark_remittance_import_finalised(name, doc, submitted=False)
            finalised_imports.append(name)

    final_status = "Remittance Import Submitted" if submitted_imports else "Remittance Import Finalised"

    for row in doc.get("remittance_finalisation_lines") or []:
        if row.get("ndis_remittance_import") in submitted_imports:
            row.ndis_remittance_import_docstatus = 1
            row.remittance_finalisation_line_status = "Remittance Import Submitted"
        elif row.get("ndis_remittance_import") in finalised_imports:
            row.remittance_finalisation_line_status = "Remittance Import Finalised"

    doc.status = final_status
    doc.remittance_import_finalisation_allowed = 0
    doc.journal_creation_allowed = 0
    doc.write_off_creation_allowed = 0
    doc.recovery_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.finalised_by = frappe.session.user
    doc.finalised_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "submitted_remittance_imports": submitted_imports,
        "finalised_remittance_imports": finalised_imports,
        "message": "NDIS Remittance Import finalised through controlled Phase 30 gate. No Payment Entry, Journal Entry, manual GL Entry, write-off, recovery, or bank reconciliation was created by Phase 30.",
    }


def validate_remittance_import_finalisation_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(REMITTANCE_IMPORT_FINALISATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(REMITTANCE_IMPORT_FINALISATION_RUN, "remittance_import_finalisation_run_ready"):
        doc.remittance_import_finalisation_run_ready = 1 if summary["remittance_import_finalisation_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["remittance_import_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot set Remittance Import Finalisation Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Remittance Import Finalisation Approved" and doc.get("remittance_import_finalisation_allowed"):
        frappe.throw(_("Remittance Import Finalisation Allowed can only be ticked after the run is approved."))

    if doc.get("journal_creation_allowed"):
        frappe.throw(_("Journal creation is not allowed in Phase 30."))

    if doc.get("write_off_creation_allowed"):
        frappe.throw(_("Write-off creation is not allowed in Phase 30."))

    if doc.get("recovery_creation_allowed"):
        frappe.throw(_("Recovery creation is not allowed in Phase 30."))

    if doc.get("bank_reconciliation_allowed"):
        frappe.throw(_("Bank reconciliation is not allowed in Phase 30."))


def on_remittance_import_finalisation_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Remittance Import Finalisation Run Summary Sync Failed"
        )


def validate_remittance_import_phase30_submit_guard(doc, method=None):
    if not _field_exists(NDIS_REMITTANCE_IMPORT, "ndis_crm_remittance_import_finalisation_run"):
        return

    run = doc.get("ndis_crm_remittance_import_finalisation_run")

    if not run:
        frappe.throw(
            _("NDIS Remittance Import can only be submitted through the controlled Phase 30 Remittance Import Finalisation Run.")
        )

    if not frappe.db.exists(REMITTANCE_IMPORT_FINALISATION_RUN, run):
        frappe.throw(_("Linked Remittance Import Finalisation Run {0} was not found.").format(run))

    status, ready, allowed = frappe.db.get_value(
        REMITTANCE_IMPORT_FINALISATION_RUN,
        run,
        ["status", "remittance_import_finalisation_run_ready", "remittance_import_finalisation_allowed"],
    )

    if status != "Remittance Import Finalisation Approved" or not ready or not allowed:
        frappe.throw(
            _("NDIS Remittance Import can only be submitted while the linked Phase 30 run is approved, ready, and explicitly allowed.")
        )


def validate_crm_deal_phase30(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_remittance_import_finalisation_run_required"):
        required = doc.get("ndis_remittance_import_finalisation_run_required")

    if not required:
        return

    run = doc.get("ndis_remittance_import_finalisation_run") if _field_exists(CRM_DEAL, "ndis_remittance_import_finalisation_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Remittance Import Finalisation Run must be created and approved.")
        )

    if not _is_remittance_finalisation_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Remittance Import Finalisation Run must be approved/finalised.")
        )


def validate_crm_deal_phase30_combined(doc, method=None):
    """
    Preserve Phase 2-29 validator chain, then add optional Phase 30 Remittance Import Finalisation validation.
    """
    try:
        from ndis_crm.phase29_payment_entry_submission import validate_crm_deal_phase29_combined
        validate_crm_deal_phase29_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase28_payment_entry_draft import validate_crm_deal_phase28_combined
            validate_crm_deal_phase28_combined(doc, method)
        except ImportError:
            try:
                from ndis_crm.phase27_payment_allocation_preparation import validate_crm_deal_phase27_combined
                validate_crm_deal_phase27_combined(doc, method)
            except ImportError:
                pass

    validate_crm_deal_phase30(doc, method)


def phase30_health_check():
    print("---- NDIS CRM Phase 30 Health Check ----")

    for dt in [
        REMITTANCE_IMPORT_FINALISATION_LINE,
        REMITTANCE_IMPORT_FINALISATION_RUN,
        PAYMENT_ENTRY_SUBMISSION_RUN,
        PAYMENT_ENTRY_SUBMISSION_LINE,
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

    print(f"NDIS Remittance Import is submittable: {_is_submittable(NDIS_REMITTANCE_IMPORT)}")

    for dt in [
        "Journal Entry",
        "GL Entry",
        "Bank Reconciliation Tool",
        "NDIS Recovery Case",
        "NDIS Write Off",
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for field in [
        "ndis_remittance_import_finalisation_run_required",
        "ndis_remittance_import_finalisation_run",
        "remittance_import_finalisation_status",
        "remittance_import_finalisation_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    for field in [
        "ndis_crm_remittance_import_finalisation_run",
        "ndis_crm_remittance_import_finalisation_status",
        "ndis_crm_remittance_import_finalisation_approved",
        "ndis_crm_remittance_import_finalisation_blocked",
        "ndis_crm_remittance_import_finalised_on",
        "ndis_crm_remittance_import_finalised_by",
    ]:
        print(f"NDIS Remittance Import field {field}: {'OK' if _field_exists(NDIS_REMITTANCE_IMPORT, field) else 'MISSING'}")

    print("NDIS CRM Remittance Import Finalisation Run records:", frappe.db.count(REMITTANCE_IMPORT_FINALISATION_RUN) if _doctype_exists(REMITTANCE_IMPORT_FINALISATION_RUN) else 0)
    print("Phase 30 finalises or submits existing NDIS Remittance Import only.")
    print("Phase 30 does not create Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, Sales Invoice, Claim Batch, Claim Line, or manual GL Entry.")
    print("---- End Phase 30 Health Check ----")
