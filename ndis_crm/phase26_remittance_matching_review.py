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
ACTUAL_REMITTANCE_IMPORT_LINE = "NDIS CRM Actual Remittance Import Line"
REMITTANCE_MATCHING_REVIEW_RUN = "NDIS CRM Remittance Matching Review Run"
REMITTANCE_MATCHING_REVIEW_LINE = "NDIS CRM Remittance Matching Review Line"

SALES_INVOICE = "Sales Invoice"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"

READY_STATUSES = ["Ready for Matching Decision Review", "Remittance Matching Review Approved", "Matching Review Completed"]
APPROVED_STATUSES = ["Remittance Matching Review Approved", "Matching Review Completed"]
SOURCE_READY_STATUSES = ["Draft Remittance Import Created"]
ALLOWED_ROLES = {"System Manager", "Accounts Manager", "Accounts User", "NDIS CRM Manager", "NDIS Plan Management Officer"}

CHAIN_FIELDS = [
	"crm_lead",
	"crm_deal",
	"participant_intake",
	"handover",
	"finance_onboarding",
	"operations_setup",
	"service_schedule_draft",
	"roster_build_request",
	"participant_service_file",
	"service_session_draft",
	"delivery_evidence_review",
	"downstream_preparation",
	"attendance_draft",
	"billing_draft",
	"claim_draft",
	"invoice_draft",
	"sales_invoice_draft_run",
	"sales_invoice_submission_run",
	"claim_batch_draft_run",
	"claim_batch_submission_run",
	"claim_export_preparation_run",
	"claim_lodgement_confirmation_run",
	"remittance_import_preparation_run",
]


def _check_role():
	if frappe.session.user == "Administrator":
		return
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this remittance matching review action."))


def _doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
	return bool(frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}) or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}))


def _db_set_if_field(doctype, name, fieldname, value):
	if name and _doctype_exists(doctype) and _field_exists(doctype, fieldname):
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
	if value in (None, ""):
		return 0
	try:
		if isinstance(value, str):
			value = value.replace("$", "").replace(",", "").strip()
		return float(value)
	except Exception:
		return 0


def _existing_run_for_actual_remittance_import_run(actual_remittance_import_run):
	if _field_exists(ACTUAL_REMITTANCE_IMPORT_RUN, "ndis_remittance_matching_review_run"):
		existing = frappe.db.get_value(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run, "ndis_remittance_matching_review_run")
		if existing and frappe.db.exists(REMITTANCE_MATCHING_REVIEW_RUN, existing):
			return existing
	return frappe.db.get_value(REMITTANCE_MATCHING_REVIEW_RUN, {"actual_remittance_import_run": actual_remittance_import_run}, "name")


def _existing_run_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_remittance_matching_review_run"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_remittance_matching_review_run")
		if existing and frappe.db.exists(REMITTANCE_MATCHING_REVIEW_RUN, existing):
			return existing
	return frappe.db.get_value(REMITTANCE_MATCHING_REVIEW_RUN, {"crm_deal": deal}, "name")


def _get_actual_remittance_import_run_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_actual_remittance_import_run"):
		run = frappe.db.get_value(CRM_DEAL, deal, "ndis_actual_remittance_import_run")
		if run:
			return run
	return frappe.db.get_value(ACTUAL_REMITTANCE_IMPORT_RUN, {"crm_deal": deal}, "name")


def _is_actual_remittance_import_draft_created(run):
	if not run or not frappe.db.exists(ACTUAL_REMITTANCE_IMPORT_RUN, run):
		return False
	status, ready, ndis_remittance_import = frappe.db.get_value(ACTUAL_REMITTANCE_IMPORT_RUN, run, ["status", "actual_remittance_import_run_ready", "ndis_remittance_import"])
	return status in SOURCE_READY_STATUSES and bool(ready) and bool(ndis_remittance_import)


def _is_matching_review_approved(run):
	if not run or not frappe.db.exists(REMITTANCE_MATCHING_REVIEW_RUN, run):
		return False
	status, ready = frappe.db.get_value(REMITTANCE_MATCHING_REVIEW_RUN, run, ["status", "remittance_matching_review_run_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _snapshot(doctype, name, fields):
	if not name or not _doctype_exists(doctype) or not frappe.db.exists(doctype, name):
		return {}
	out = {"name": name}
	for fieldname in fields:
		if _field_exists(doctype, fieldname):
			out[fieldname] = frappe.db.get_value(doctype, name, fieldname)
	return out


def _remittance_import_snapshot(name):
	return _snapshot(
		NDIS_REMITTANCE_IMPORT,
		name,
		["docstatus", "status", "import_status", "remittance_status", "company", "participant_customer", "customer", "posting_date", "import_date", "remittance_date", "total_claim_amount", "claim_amount_total", "total_paid_amount", "paid_amount_total", "actual_paid_amount_total", "total_rejected_amount", "rejected_amount_total", "external_lodgement_reference", "lodgement_reference", "payment_reference", "remittance_reference"],
	)


def _sales_invoice_snapshot(name):
	if not name or not frappe.db.exists(SALES_INVOICE, name):
		return {}
	return frappe.db.get_value(SALES_INVOICE, name, ["name", "docstatus", "customer", "company", "posting_date", "due_date", "grand_total", "rounded_total", "outstanding_amount", "status"], as_dict=True) or {}


def _claim_batch_snapshot(name):
	return _snapshot(NDIS_CLAIM_BATCH, name, ["docstatus", "status", "claim_batch_status", "batch_status", "company", "participant_customer", "customer", "claim_period_start", "claim_period_end", "total_claim_amount", "claim_amount_total", "lodgement_reference", "external_lodgement_reference", "payment_reference"])


def _claim_line_snapshot(name):
	return _snapshot(NDIS_CLAIM_LINE, name, ["docstatus", "status", "claim_status", "claim_batch", "ndis_claim_batch", "sales_invoice", "support_item", "service_booking", "plan_budget", "quantity", "claim_quantity", "rate", "claim_rate", "amount", "claim_amount", "service_date", "external_lodgement_reference", "payment_reference"])


def _source_key(row):
	return row.get("actual_remittance_source_key") or "|".join(str(row.get(fieldname) or "") for fieldname in ["service_line", "ndis_claim_batch", "ndis_claim_line", "sales_invoice", "external_lodgement_reference", "actual_payment_reference"])


def _append_line_if_missing(doc, row_data):
	key = row_data.get("matching_source_key")
	if key and any(row.get("matching_source_key") == key for row in doc.get("matching_lines") or []):
		return False
	doc.append("matching_lines", row_data)
	return True


def _classify_matching(row):
	expected_paid = _to_float(row.get("expected_paid_amount"))
	actual_paid = _to_float(row.get("actual_paid_amount"))
	actual_rejected = _to_float(row.get("actual_rejected_amount"))
	variance = round(actual_paid - expected_paid, 2)
	if not row.get("actual_file_matched"):
		return "Unmatched", "Investigate uploaded remittance file mapping."
	if actual_rejected and not actual_paid:
		return "Rejected", "Move to rejection review gate later."
	if actual_rejected and actual_paid:
		return "Partial Payment", "Part paid and part rejected. Review variance before allocation."
	if variance == 0:
		return "Full Payment Match", "Ready for later payment allocation gate."
	if actual_paid > expected_paid:
		return "Overpayment", "Overpayment review required before allocation."
	if actual_paid < expected_paid and actual_paid > 0:
		return "Partial Payment", "Short payment review required before allocation/recovery decision."
	if actual_paid == 0 and expected_paid:
		return "Underpayment", "No payment received against expected amount."
	return "Manual Review", "Manual matching review required."


def _recommended_next_action(match_result, variance_amount, actual_rejected_amount):
	if match_result == "Full Payment Match":
		return "Payment Allocation Review"
	if match_result in ("Partial Payment", "Underpayment"):
		return "Rejection / Recovery Review" if actual_rejected_amount else "Short Payment Review"
	if match_result == "Rejected":
		return "Rejection Review"
	if match_result == "Overpayment":
		return "Overpayment Review"
	if match_result == "Unmatched":
		return "Manual Matching Investigation"
	return "Manual Review"


def _build_matching_line_from_actual_line(row, run_doc):
	invoice = _sales_invoice_snapshot(row.get("sales_invoice"))
	batch = _claim_batch_snapshot(row.get("ndis_claim_batch"))
	claim_line = _claim_line_snapshot(row.get("ndis_claim_line"))
	remit = _remittance_import_snapshot(run_doc.get("ndis_remittance_import"))
	expected_paid = _to_float(row.get("expected_paid_amount"))
	actual_paid = _to_float(row.get("actual_paid_amount"))
	actual_rejected = _to_float(row.get("actual_rejected_amount"))
	variance = round(actual_paid - expected_paid, 2)
	match_result, match_reason = _classify_matching(row)
	source_ready = bool(
		run_doc.get("status") == "Draft Remittance Import Created"
		and run_doc.get("ndis_remittance_import")
		and int(remit.get("docstatus") or 0) == 0
		and row.get("actual_remittance_line_status") == "Draft Remittance Import Created"
		and row.get("ndis_remittance_import")
		and row.get("remittance_import_draft_authorized")
		and row.get("line_ready_for_remittance_import_draft")
		and not row.get("actual_remittance_hold")
		and row.get("actual_file_matched")
		and row.get("sales_invoice")
		and int(invoice.get("docstatus") or row.get("sales_invoice_docstatus") or 0) == 1
		and row.get("ndis_claim_batch")
	)
	return {
		"matching_source_key": _source_key(row),
		"ndis_remittance_import": row.get("ndis_remittance_import") or run_doc.get("ndis_remittance_import"),
		"ndis_remittance_import_docstatus": remit.get("docstatus"),
		"ndis_remittance_import_status": remit.get("status") or remit.get("import_status") or remit.get("remittance_status"),
		"ndis_claim_batch": row.get("ndis_claim_batch"),
		"ndis_claim_line": row.get("ndis_claim_line"),
		"claim_batch_status": batch.get("status") or batch.get("claim_batch_status") or batch.get("batch_status"),
		"claim_line_status": claim_line.get("status") or claim_line.get("claim_status"),
		"sales_invoice": row.get("sales_invoice"),
		"sales_invoice_docstatus": int(invoice.get("docstatus") or row.get("sales_invoice_docstatus") or 0),
		"sales_invoice_status": invoice.get("status") or row.get("sales_invoice_status"),
		"sales_invoice_outstanding_amount": invoice.get("outstanding_amount") if invoice else row.get("sales_invoice_outstanding_amount"),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"service_date": row.get("service_date"),
		"claim_quantity": row.get("claim_quantity"),
		"claim_unit": row.get("claim_unit") or "Hour",
		"claim_rate": row.get("claim_rate"),
		"claim_amount": row.get("claim_amount"),
		"expected_paid_amount": expected_paid,
		"expected_rejected_amount": row.get("expected_rejected_amount"),
		"actual_paid_amount": actual_paid,
		"actual_rejected_amount": actual_rejected,
		"variance_amount": variance,
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
		"rejection_code": row.get("rejection_code"),
		"rejection_reason": row.get("rejection_reason"),
		"remittance_import_source_ready": 1 if source_ready else 0,
		"matching_result": match_result,
		"matching_reason": match_reason,
		"recommended_next_action": _recommended_next_action(match_result, variance, actual_rejected),
		"matching_review_complete": 0,
		"matching_decision_authorized": 0,
		"payment_allocation_authorized": 0,
		"journal_authorized": 0,
		"write_off_authorized": 0,
		"recovery_authorized": 0,
		"matching_hold": 0 if source_ready else 1,
		"matching_hold_reason": None if source_ready else "Actual remittance import source is not ready for matching review.",
		"line_ready_for_matching_completion": 0,
		"matching_line_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_actual_remittance_import_run(doc, source):
	created = 0
	for row in source.get("actual_remittance_lines") or []:
		if row.get("actual_remittance_line_status") != "Draft Remittance Import Created" or not row.get("ndis_remittance_import"):
			continue
		if _append_line_if_missing(doc, _build_matching_line_from_actual_line(row, source)):
			created += 1
	return created


def _calculate_totals(doc):
	lines = list(doc.get("matching_lines") or [])
	return {
		"matching_line_count": len(lines),
		"claim_batch_count": len({row.ndis_claim_batch for row in lines if row.ndis_claim_batch}),
		"claim_amount_total": round(sum(_to_float(row.claim_amount) for row in lines), 2),
		"expected_paid_amount_total": round(sum(_to_float(row.expected_paid_amount) for row in lines), 2),
		"actual_paid_amount_total": round(sum(_to_float(row.actual_paid_amount) for row in lines), 2),
		"actual_rejected_amount_total": round(sum(_to_float(row.actual_rejected_amount) for row in lines), 2),
		"variance_amount_total": round(sum(_to_float(row.variance_amount) for row in lines), 2),
		"full_match_count": sum(1 for row in lines if row.matching_result == "Full Payment Match"),
		"partial_payment_count": sum(1 for row in lines if row.matching_result == "Partial Payment"),
		"rejected_count": sum(1 for row in lines if row.matching_result == "Rejected"),
		"overpayment_count": sum(1 for row in lines if row.matching_result == "Overpayment"),
		"underpayment_count": sum(1 for row in lines if row.matching_result == "Underpayment"),
		"unmatched_count": sum(1 for row in lines if row.matching_result == "Unmatched"),
		"manual_review_count": sum(1 for row in lines if row.matching_result == "Manual Review"),
		"matching_ready_count": sum(1 for row in lines if row.line_ready_for_matching_completion),
		"matching_hold_count": sum(1 for row in lines if row.matching_hold),
		"blocked_payment_authorization_count": sum(1 for row in lines if row.payment_allocation_authorized),
		"blocked_journal_authorization_count": sum(1 for row in lines if row.journal_authorized),
		"blocked_write_off_authorization_count": sum(1 for row in lines if row.write_off_authorized),
		"blocked_recovery_authorization_count": sum(1 for row in lines if row.recovery_authorized),
	}


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(REMITTANCE_MATCHING_REVIEW_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _calculate_readiness(doc):
	checks = [
		("Actual Remittance Import Run linked", bool(doc.get("actual_remittance_import_run"))),
		("Draft NDIS Remittance Import created", _is_actual_remittance_import_draft_created(doc.get("actual_remittance_import_run"))),
		("NDIS Remittance Import linked", bool(doc.get("ndis_remittance_import"))),
		("NDIS Remittance Import is still Draft", bool(doc.get("ndis_remittance_import")) and int(_remittance_import_snapshot(doc.get("ndis_remittance_import")).get("docstatus") or 0) == 0),
		("Participant Customer linked", bool(doc.get("participant_customer"))),
		("Company selected", bool(doc.get("company"))),
		("Matching Review Owner assigned", bool(doc.get("matching_review_owner"))),
		("At least one matching review line exists", bool(doc.get("matching_lines"))),
	]
	for row in doc.get("matching_lines") or []:
		ref = row.idx or row.get("matching_source_key") or "line"
		checks.extend([
			(f"Line {ref}: NDIS Remittance Import reference exists", bool(row.get("ndis_remittance_import"))),
			(f"Line {ref}: NDIS Remittance Import is Draft", bool(row.get("ndis_remittance_import")) and int(_remittance_import_snapshot(row.get("ndis_remittance_import")).get("docstatus") or 0) == 0),
			(f"Line {ref}: Sales Invoice reference exists", bool(row.get("sales_invoice"))),
			(f"Line {ref}: NDIS Claim Batch reference exists", bool(row.get("ndis_claim_batch"))),
			(f"Line {ref}: matching result exists", bool(row.get("matching_result"))),
			(f"Line {ref}: remittance import source ready", bool(row.get("remittance_import_source_ready"))),
			(f"Line {ref}: matching review complete", bool(row.get("matching_review_complete"))),
			(f"Line {ref}: matching decision authorized", bool(row.get("matching_decision_authorized"))),
			(f"Line {ref}: future payment/journal/write-off/recovery authorization blocked", not any([row.get("payment_allocation_authorized"), row.get("journal_authorized"), row.get("write_off_authorized"), row.get("recovery_authorized")])),
			(f"Line {ref}: no matching hold", not row.get("matching_hold")),
			(f"Line {ref}: ready for matching completion", bool(row.get("line_ready_for_matching_completion"))),
		])
	missing = [label for label, complete in checks if not complete]
	percent = round(((len(checks) - len(missing)) / len(checks)) * 100, 2) if checks else 0
	return {"total_checks": len(checks), "complete_checks": len(checks) - len(missing), "readiness_percent": percent, "remittance_matching_review_run_ready": bool(checks) and not missing, "incomplete": missing}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_matching_review_run_ready = 1 if summary["remittance_matching_review_run_ready"] else 0
	targets = [
		(CRM_DEAL, doc.get("crm_deal")),
		(INTAKE, doc.get("participant_intake")),
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
	]
	for doctype, name in targets:
		_db_set_if_field(doctype, name, "ndis_remittance_matching_review_run", doc.name)
		_db_set_if_field(doctype, name, "remittance_matching_review_status", doc.status)
		_db_set_if_field(doctype, name, "remittance_matching_review_ready", 1 if summary["remittance_matching_review_run_ready"] else 0)
	return {"readiness": summary, "totals": totals}


def _copy_source_fields(doc, source):
	for fieldname in CHAIN_FIELDS:
		doc.set(fieldname, source.get(fieldname))
	for fieldname in ["participant_customer", "ndis_financial_profile", "participant_name", "ndis_number", "plan_start_date", "plan_end_date", "claim_period_start", "claim_period_end", "claim_window_start", "claim_window_end", "company", "ndis_remittance_import", "uploaded_remittance_file", "uploaded_file_sha256", "uploaded_file_hash", "actual_remittance_import_date", "external_lodgement_reference", "external_batch_reference", "actual_payment_reference", "actual_remittance_owner", "remittance_owner", "claim_lodgement_owner", "claim_owner", "billing_owner"]:
		if _field_exists(REMITTANCE_MATCHING_REVIEW_RUN, fieldname):
			doc.set(fieldname, source.get(fieldname))
	if _field_exists(REMITTANCE_MATCHING_REVIEW_RUN, "uploaded_file_hash") and not doc.get("uploaded_file_hash"):
		doc.uploaded_file_hash = source.get("uploaded_file_sha256")
	if not doc.participant_name:
		doc.participant_name = source.get("participant_customer") or source.name


@frappe.whitelist()
def create_remittance_matching_review_run_from_actual_remittance_import_run(actual_remittance_import_run):
	_check_role()
	if not actual_remittance_import_run or not frappe.db.exists(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run):
		frappe.throw(_("NDIS CRM Actual Remittance Import Run is required."))
	if not _is_actual_remittance_import_draft_created(actual_remittance_import_run):
		frappe.throw(_("Actual Remittance Import Run must have created a draft NDIS Remittance Import before matching review."))
	existing = _existing_run_for_actual_remittance_import_run(actual_remittance_import_run)
	if existing:
		return {"doctype": REMITTANCE_MATCHING_REVIEW_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Remittance Matching Review Run returned."}
	source = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run)
	doc = frappe.new_doc(REMITTANCE_MATCHING_REVIEW_RUN)
	doc.status = "Draft"
	doc.actual_remittance_import_run = source.name
	doc.matching_review_owner = frappe.session.user
	doc.matching_completion_allowed = 0
	doc.payment_allocation_allowed = 0
	doc.journal_creation_allowed = 0
	doc.write_off_creation_allowed = 0
	doc.recovery_creation_allowed = 0
	_copy_source_fields(doc, source)
	created_count = _generate_lines_from_actual_remittance_import_run(doc, source)
	_sync_totals(doc)
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_matching_review_run_ready = 1 if summary["remittance_matching_review_run_ready"] else 0
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": REMITTANCE_MATCHING_REVIEW_RUN, "name": doc.name, "created": True, "matching_line_count": created_count, "message": "NDIS CRM Remittance Matching Review Run created successfully."}


@frappe.whitelist()
def create_remittance_matching_review_run_from_crm_deal(deal):
	_check_role()
	if not deal or not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal is required."))
	existing = _existing_run_for_deal(deal)
	if existing:
		return {"doctype": REMITTANCE_MATCHING_REVIEW_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Remittance Matching Review Run returned."}
	source_run = _get_actual_remittance_import_run_for_deal(deal)
	if not source_run:
		frappe.throw(_("Please create NDIS CRM Actual Remittance Import Run before creating Remittance Matching Review Run."))
	return create_remittance_matching_review_run_from_actual_remittance_import_run(source_run)


@frappe.whitelist()
def generate_remittance_matching_review_lines(remittance_matching_review_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_MATCHING_REVIEW_RUN, remittance_matching_review_run)
	source = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, doc.actual_remittance_import_run)
	created_count = _generate_lines_from_actual_remittance_import_run(doc, source)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Remittance matching review lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_remittance_matching_review_readiness(remittance_matching_review_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_MATCHING_REVIEW_RUN, remittance_matching_review_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Remittance Matching Review Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_matching_decision_review(remittance_matching_review_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_MATCHING_REVIEW_RUN, remittance_matching_review_run)
	summary = _calculate_readiness(doc)
	if not summary["remittance_matching_review_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Matching Decision Review. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Matching Decision Review"
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_matching_review_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": REMITTANCE_MATCHING_REVIEW_RUN, "name": doc.name, "message": "Remittance Matching Review Run marked Ready."}


@frappe.whitelist()
def approve_remittance_matching_review_run(remittance_matching_review_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_MATCHING_REVIEW_RUN, remittance_matching_review_run)
	summary = _calculate_readiness(doc)
	if not summary["remittance_matching_review_run_ready"]:
		frappe.throw(_("Cannot approve Remittance Matching Review Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Remittance Matching Review Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_matching_review_run_ready = 1
	doc.matching_completion_allowed = 0
	doc.payment_allocation_allowed = 0
	doc.journal_creation_allowed = 0
	doc.write_off_creation_allowed = 0
	doc.recovery_creation_allowed = 0
	for row in doc.get("matching_lines") or []:
		if row.get("matching_line_status") in ("Draft", "Ready"):
			row.matching_line_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": REMITTANCE_MATCHING_REVIEW_RUN, "name": doc.name, "message": "Remittance Matching Review Run approved. No payment, journal, write-off, recovery, bank reconciliation, or GL action was performed."}


def _ready_lines_for_completion(doc):
	return [
		row
		for row in doc.get("matching_lines") or []
		if row.get("matching_line_status") in ("Approved", "Ready")
		and row.get("line_ready_for_matching_completion")
		and row.get("matching_review_complete")
		and row.get("matching_decision_authorized")
		and not any([row.get("payment_allocation_authorized"), row.get("journal_authorized"), row.get("write_off_authorized"), row.get("recovery_authorized"), row.get("matching_hold")])
	]


def _update_draft_remittance_import_review_status(doc):
	if not doc.get("ndis_remittance_import") or not frappe.db.exists(NDIS_REMITTANCE_IMPORT, doc.ndis_remittance_import):
		return None
	remittance_doc = frappe.get_doc(NDIS_REMITTANCE_IMPORT, doc.ndis_remittance_import)
	if remittance_doc.docstatus != 0:
		frappe.throw(_("Safety error: NDIS Remittance Import is no longer Draft."))
	_set_first_existing(remittance_doc, ["status", "import_status", "remittance_status"], "Matching Review Completed")
	_set_first_existing(remittance_doc, ["matching_review_completed", "remittance_matching_review_completed"], 1)
	_set_first_existing(remittance_doc, ["matching_review_run", "crm_remittance_matching_review_run"], doc.name)
	_set_first_existing(remittance_doc, ["matching_review_completed_on"], now())
	_set_first_existing(remittance_doc, ["matching_review_completed_by"], frappe.session.user)
	_set_first_existing(remittance_doc, ["matched_amount_total", "actual_paid_amount_total", "total_paid_amount"], doc.get("actual_paid_amount_total"))
	_set_first_existing(remittance_doc, ["rejected_amount_total", "actual_rejected_amount_total", "total_rejected_amount"], doc.get("actual_rejected_amount_total"))
	_set_first_existing(remittance_doc, ["variance_amount_total"], doc.get("variance_amount_total"))
	_set_first_existing(remittance_doc, ["notes", "remarks"], f"Matching review completed from {doc.doctype} {doc.name}. No Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, or GL posting was created.")
	remittance_doc.save(ignore_permissions=True)
	return remittance_doc.name


@frappe.whitelist()
def complete_remittance_matching_review(remittance_matching_review_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_MATCHING_REVIEW_RUN, remittance_matching_review_run)
	if doc.status != "Remittance Matching Review Approved":
		frappe.throw(_("Remittance Matching Review Run must be approved before completion."))
	if not doc.get("matching_completion_allowed"):
		frappe.throw(_("Tick Matching Completion Allowed before completing the matching review."))
	if any([doc.get("payment_allocation_allowed"), doc.get("journal_creation_allowed"), doc.get("write_off_creation_allowed"), doc.get("recovery_creation_allowed")]):
		frappe.throw(_("Payment allocation, journal, write-off, and recovery creation must remain blocked in Phase 26."))
	summary = _calculate_readiness(doc)
	if not summary["remittance_matching_review_run_ready"]:
		frappe.throw(_("Cannot complete matching review. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	ready_lines = _ready_lines_for_completion(doc)
	if not ready_lines:
		frappe.throw(_("No ready matching review lines found."))
	for row in ready_lines:
		row.matching_line_status = "Matching Review Completed"
	doc.status = "Matching Review Completed"
	doc.matching_completion_allowed = 0
	doc.payment_allocation_allowed = 0
	doc.journal_creation_allowed = 0
	doc.write_off_creation_allowed = 0
	doc.recovery_creation_allowed = 0
	doc.completed_by = frappe.session.user
	doc.completed_on = now()
	_sync_totals(doc)
	_update_draft_remittance_import_review_status(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"ndis_remittance_import": doc.get("ndis_remittance_import"), "completed_line_count": len(ready_lines), "message": "Remittance matching review completed. No Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, or manual GL was created."}


def validate_remittance_matching_review_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_matching_review_run_ready = 1 if summary["remittance_matching_review_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["remittance_matching_review_run_ready"]:
		frappe.throw(_("Cannot set Remittance Matching Review Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Remittance Matching Review Approved" and doc.get("matching_completion_allowed"):
		frappe.throw(_("Matching Completion Allowed can only be ticked after the run is approved."))
	if any([doc.get("payment_allocation_allowed"), doc.get("journal_creation_allowed"), doc.get("write_off_creation_allowed"), doc.get("recovery_creation_allowed")]):
		frappe.throw(_("Payment allocation, journal creation, write-off, and recovery creation are not allowed in Phase 26."))


def on_remittance_matching_review_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Remittance Matching Review Run Summary Sync Failed")


def validate_crm_deal_phase26(doc, method=None):
	if doc.status != "Won / Active Client" or not doc.get("ndis_remittance_matching_review_run_required"):
		return
	run = doc.get("ndis_remittance_matching_review_run")
	if not run or not _is_matching_review_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Remittance Matching Review Run must be created and approved."))


def validate_crm_deal_phase26_combined(doc, method=None):
	try:
		from ndis_crm.phase25_actual_remittance_import import validate_crm_deal_phase25_combined

		validate_crm_deal_phase25_combined(doc, method)
	except ImportError:
		pass
	validate_crm_deal_phase26(doc, method)


@frappe.whitelist()
def phase26_health_check():
	required = [REMITTANCE_MATCHING_REVIEW_LINE, REMITTANCE_MATCHING_REVIEW_RUN, ACTUAL_REMITTANCE_IMPORT_RUN, ACTUAL_REMITTANCE_IMPORT_LINE, REMITTANCE_IMPORT_PREP_RUN, NDIS_CLAIM_BATCH, NDIS_CLAIM_LINE, NDIS_REMITTANCE_IMPORT, SALES_INVOICE]
	missing = [doctype for doctype in required if not _doctype_exists(doctype)]
	if missing:
		frappe.throw("Missing Phase 26 DocTypes: " + ", ".join(missing))
	for field in ["ndis_remittance_matching_review_run_required", "ndis_remittance_matching_review_run", "remittance_matching_review_status", "remittance_matching_review_ready"]:
		if not _field_exists(CRM_DEAL, field):
			frappe.throw(f"Missing CRM Deal field {field}")
	for doctype in [INTAKE, HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, SESSION_DRAFT, EVIDENCE_REVIEW, DOWNSTREAM_PREPARATION, BILLING_DRAFT, CLAIM_DRAFT, INVOICE_DRAFT, SALES_INVOICE_DRAFT_RUN, SALES_INVOICE_SUBMISSION_RUN, CLAIM_BATCH_DRAFT_RUN, CLAIM_BATCH_SUBMISSION_RUN, CLAIM_EXPORT_PREP_RUN, CLAIM_LODGEMENT_CONFIRMATION_RUN, REMITTANCE_IMPORT_PREP_RUN, ACTUAL_REMITTANCE_IMPORT_RUN]:
		for field in ["ndis_remittance_matching_review_run", "remittance_matching_review_status", "remittance_matching_review_ready"]:
			if not _field_exists(doctype, field):
				frappe.throw(f"Missing Phase 26 field {doctype}.{field}")
	print("Phase 26 health check passed. Remittance matching review creates CRM review records only and does not create payment, journal, manual GL, write-off, recovery, bank reconciliation, invoice, claim batch, claim line, or new/submitted remittance import records.")
	return {"status": "ok", "remittance_matching_review_runs": frappe.db.count(REMITTANCE_MATCHING_REVIEW_RUN), "remittance_matching_review_lines": frappe.db.count(REMITTANCE_MATCHING_REVIEW_LINE), "boundary": "matching_review_only"}
