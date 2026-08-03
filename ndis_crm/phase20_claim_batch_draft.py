import frappe
from frappe import _
from frappe.utils import nowdate


CRM_DEAL = "CRM Deal"
CRM_LEAD = "CRM Lead"
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
CLAIM_DRAFT_LINE = "NDIS CRM Claim Draft Line"
INVOICE_DRAFT = "NDIS CRM Invoice Draft"
SALES_INVOICE_DRAFT_RUN = "NDIS CRM Sales Invoice Draft Run"
SALES_INVOICE_SUBMISSION_RUN = "NDIS CRM Sales Invoice Submission Run"
CLAIM_BATCH_DRAFT_RUN = "NDIS CRM Claim Batch Draft Run"
CLAIM_BATCH_DRAFT_LINE = "NDIS CRM Claim Batch Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

SALES_INVOICE = "Sales Invoice"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"

READY_STATUSES = ["Ready for Claim Batch Draft Creation", "Claim Batch Draft Run Approved", "Draft Claim Batches Created"]
APPROVED_STATUSES = ["Claim Batch Draft Run Approved", "Draft Claim Batches Created"]
APPROVED_CLAIM_DRAFT_STATUSES = ["Claim Draft Approved"]
SUBMITTED_SALES_INVOICE_STATUSES = ["Sales Invoices Submitted"]

ALLOWED_ROLES = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"NDIS CRM Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this claim batch draft action."))


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


def _set_if_field(doc, fieldname, value, force=False):
	if (force or value is not None) and _field_exists(doc.doctype, fieldname):
		doc.set(fieldname, value)
		return True
	return False


def _set_first_existing(doc, fieldnames, value, force=False):
	for fieldname in fieldnames:
		if _set_if_field(doc, fieldname, value, force=force):
			return fieldname
	return None


def _existing_run_for_claim_draft(claim_draft):
	if not _doctype_exists(CLAIM_BATCH_DRAFT_RUN):
		return None
	if _field_exists(CLAIM_DRAFT, "ndis_claim_batch_draft_run"):
		existing = frappe.db.get_value(CLAIM_DRAFT, claim_draft, "ndis_claim_batch_draft_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_BATCH_DRAFT_RUN, {"claim_draft": claim_draft}, "name")


def _existing_run_for_deal(deal):
	if not _doctype_exists(CLAIM_BATCH_DRAFT_RUN):
		return None
	if _field_exists(CRM_DEAL, "ndis_claim_batch_draft_run"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_batch_draft_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_BATCH_DRAFT_RUN, {"crm_deal": deal}, "name")


def _get_claim_draft_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_claim_draft"):
		claim_draft = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_draft")
		if claim_draft:
			return claim_draft
	if _doctype_exists(CLAIM_DRAFT):
		return frappe.db.get_value(CLAIM_DRAFT, {"crm_deal": deal}, "name")
	return None


def _get_submission_run_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_sales_invoice_submission_run"):
		run = frappe.db.get_value(CRM_DEAL, deal, "ndis_sales_invoice_submission_run")
		if run:
			return run
	if _doctype_exists(SALES_INVOICE_SUBMISSION_RUN):
		return frappe.db.get_value(SALES_INVOICE_SUBMISSION_RUN, {"crm_deal": deal}, "name")
	return None


def _get_submission_run_for_claim_draft(claim_draft):
	if not claim_draft or not frappe.db.exists(CLAIM_DRAFT, claim_draft):
		return None
	deal = frappe.db.get_value(CLAIM_DRAFT, claim_draft, "crm_deal")
	return _get_submission_run_for_deal(deal)


def _is_claim_draft_approved(claim_draft):
	if not claim_draft or not frappe.db.exists(CLAIM_DRAFT, claim_draft):
		return False
	status, ready = frappe.db.get_value(CLAIM_DRAFT, claim_draft, ["status", "claim_draft_ready"])
	return status in APPROVED_CLAIM_DRAFT_STATUSES and bool(ready)


def _is_sales_invoice_submission_complete(run):
	if not run or not frappe.db.exists(SALES_INVOICE_SUBMISSION_RUN, run):
		return False
	status, ready = frappe.db.get_value(SALES_INVOICE_SUBMISSION_RUN, run, ["status", "sales_invoice_submission_run_ready"])
	return status in SUBMITTED_SALES_INVOICE_STATUSES and bool(ready)


def _is_claim_batch_draft_run_approved(run):
	if not run or not frappe.db.exists(CLAIM_BATCH_DRAFT_RUN, run):
		return False
	status, ready = frappe.db.get_value(CLAIM_BATCH_DRAFT_RUN, run, ["status", "claim_batch_draft_run_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _sales_invoice_snapshot(sales_invoice):
	if not sales_invoice or not _doctype_exists(SALES_INVOICE) or not frappe.db.exists(SALES_INVOICE, sales_invoice):
		return {}
	return frappe.db.get_value(
		SALES_INVOICE,
		sales_invoice,
		["name", "docstatus", "customer", "company", "posting_date", "due_date", "grand_total", "rounded_total", "status"],
		as_dict=True,
	) or {}


def _claim_line_key(row):
	return row.get("billing_source_key") or "|".join(
		[
			str(row.get("service_line") or ""),
			str(row.get("service_date") or ""),
			str(row.get("support_item") or ""),
			str(row.get("service_booking") or ""),
		]
	)


def _append_line_if_missing(doc, row_data):
	existing = {row.claim_source_key for row in doc.get("claim_batch_draft_lines") or [] if row.get("claim_source_key")}
	key = row_data.get("claim_source_key")
	if key and key in existing:
		return False
	doc.append("claim_batch_draft_lines", row_data)
	return True


def _find_submitted_sales_invoice_for_claim_line(claim_row, submission_run):
	if not submission_run or not frappe.db.exists(SALES_INVOICE_SUBMISSION_RUN, submission_run):
		return None
	submission_doc = frappe.get_doc(SALES_INVOICE_SUBMISSION_RUN, submission_run)
	claim_group = claim_row.get("invoice_group_key")
	claim_service_line = claim_row.get("service_line")
	first_submitted = None
	for row in submission_doc.get("submission_lines") or []:
		if row.get("submission_status") != "Submitted":
			continue
		sales_invoice = row.get("sales_invoice")
		snapshot = _sales_invoice_snapshot(sales_invoice)
		if not snapshot or snapshot.get("docstatus") != 1:
			continue
		first_submitted = first_submitted or sales_invoice
		if claim_group and row.get("invoice_group_key") == claim_group:
			return sales_invoice
		if claim_service_line and row.get("service_line") == claim_service_line:
			return sales_invoice
	return first_submitted


def _claim_source_ready(row):
	return bool(
		row.get("claim_draft_status") in ["Approved", "Ready"]
		and row.get("line_ready_for_claim_batch_draft")
		and row.get("claim_preparation_ready")
		and not row.get("claim_hold")
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("plan_budget")
		and row.get("service_date")
		and row.get("claim_quantity")
		and row.get("claim_rate")
		and row.get("claim_amount")
	)


def _build_run_line_from_claim_line(row, submission_run=None):
	sales_invoice = _find_submitted_sales_invoice_for_claim_line(row, submission_run)
	snapshot = _sales_invoice_snapshot(sales_invoice)
	source_ready = 1 if _claim_source_ready(row) else 0
	submitted_invoice_ready = 1 if snapshot and snapshot.get("docstatus") == 1 else 0
	ready = bool(source_ready and submitted_invoice_ready)
	return {
		"claim_source_key": _claim_line_key(row),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"sales_invoice": sales_invoice,
		"sales_invoice_docstatus": snapshot.get("docstatus"),
		"sales_invoice_status": snapshot.get("status"),
		"service_date": row.get("service_date"),
		"billable_date": row.get("billable_date"),
		"claim_quantity": row.get("claim_quantity"),
		"claim_unit": row.get("claim_unit") or "Hour",
		"claim_rate": row.get("claim_rate"),
		"claim_amount": row.get("claim_amount"),
		"gst_treatment": row.get("gst_treatment"),
		"rate_source": row.get("rate_source"),
		"finance_service_type": row.get("finance_service_type"),
		"support_item": row.get("support_item"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"default_house": row.get("default_house"),
		"delivery_location": row.get("delivery_location"),
		"participant_attended": row.get("participant_attended"),
		"service_delivered": row.get("service_delivered"),
		"support_worker_user": row.get("support_worker_user"),
		"support_worker_employee": row.get("support_worker_employee"),
		"support_worker_name": row.get("support_worker_name"),
		"progress_note": row.get("progress_note"),
		"incident_flag": row.get("incident_flag"),
		"incident_notes": row.get("incident_notes"),
		"invoice_group_key": row.get("invoice_group_key"),
		"invoice_draft_reference": row.get("invoice_draft_reference"),
		"claim_preparation_ready": source_ready,
		"submitted_invoice_ready": submitted_invoice_ready,
		"claim_batch_mapping_ready": 0,
		"claim_batch_draft_creation_ready": 0,
		"claim_batch_draft_creation_hold": 0 if ready else 1,
		"claim_batch_draft_creation_hold_reason": None if ready else "Claim source or submitted Sales Invoice is not ready.",
		"line_ready_for_claim_batch_draft_creation": 0,
		"claim_batch_draft_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_claim_draft(run_doc, claim_doc):
	created = 0
	submission_run = run_doc.get("sales_invoice_submission_run")
	for row in claim_doc.get("claim_lines") or []:
		if row.get("claim_draft_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("line_ready_for_claim_batch_draft"):
			continue
		if _append_line_if_missing(run_doc, _build_run_line_from_claim_line(row, submission_run=submission_run)):
			created += 1
	return created


def _calculate_totals(doc):
	totals = {
		"claim_batch_draft_line_count": len(doc.get("claim_batch_draft_lines") or []),
		"claim_quantity_total": 0,
		"claim_amount_total": 0,
		"claim_batch_ready_count": 0,
		"draft_claim_line_created_count": 0,
		"claim_batch_draft_hold_count": 0,
		"missing_sales_invoice_count": 0,
		"missing_service_booking_count": 0,
		"missing_support_item_count": 0,
	}
	for row in doc.get("claim_batch_draft_lines") or []:
		totals["claim_quantity_total"] += float(row.get("claim_quantity") or 0)
		totals["claim_amount_total"] += float(row.get("claim_amount") or 0)
		if row.get("line_ready_for_claim_batch_draft_creation"):
			totals["claim_batch_ready_count"] += 1
		if row.get("ndis_claim_batch") or row.get("ndis_claim_line"):
			totals["draft_claim_line_created_count"] += 1
		if row.get("claim_batch_draft_creation_hold"):
			totals["claim_batch_draft_hold_count"] += 1
		if not row.get("sales_invoice"):
			totals["missing_sales_invoice_count"] += 1
		if not row.get("service_booking"):
			totals["missing_service_booking_count"] += 1
		if not row.get("support_item"):
			totals["missing_support_item_count"] += 1
	totals["claim_quantity_total"] = round(totals["claim_quantity_total"], 2)
	totals["claim_amount_total"] = round(totals["claim_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(CLAIM_BATCH_DRAFT_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _add_check(checks, label, complete, details=None):
	checks.append({"label": label, "complete": bool(complete), "details": details or []})


def _calculate_readiness(doc):
	checks = []
	lines = doc.get("claim_batch_draft_lines") or []
	_add_check(checks, "Claim Draft linked", doc.get("claim_draft"))
	_add_check(checks, "Claim Draft approved", _is_claim_draft_approved(doc.get("claim_draft")))
	_add_check(checks, "Sales Invoice Submission Run linked", doc.get("sales_invoice_submission_run"))
	_add_check(checks, "Sales Invoices submitted", _is_sales_invoice_submission_complete(doc.get("sales_invoice_submission_run")))
	_add_check(checks, "NDIS Claim Batch DocType exists", _doctype_exists(NDIS_CLAIM_BATCH))
	_add_check(checks, "NDIS Claim Line DocType exists", _doctype_exists(NDIS_CLAIM_LINE))
	_add_check(checks, "Participant Customer linked", doc.get("participant_customer"))
	_add_check(checks, "Company selected", doc.get("company"))
	_add_check(checks, "Claim Batch Owner assigned", doc.get("claim_batch_owner"))
	_add_check(checks, "At least one claim batch draft line exists", lines)
	_add_check(checks, "All lines have submitted Sales Invoice reference", not [row.service_line for row in lines if not row.get("sales_invoice")])
	_add_check(checks, "All linked Sales Invoices are submitted", not [row.get("sales_invoice") for row in lines if row.get("sales_invoice") and _sales_invoice_snapshot(row.get("sales_invoice")).get("docstatus") != 1])
	_add_check(checks, "All lines have service date", not [row.service_line for row in lines if not row.get("service_date")])
	_add_check(checks, "All lines have support item", not [row.service_line for row in lines if not row.get("support_item")])
	_add_check(checks, "All lines have service booking", not [row.service_line for row in lines if not row.get("service_booking")])
	_add_check(checks, "All lines have plan budget", not [row.service_line for row in lines if not row.get("plan_budget")])
	_add_check(checks, "All lines have claim amount", not [row.service_line for row in lines if not row.get("claim_amount")])
	_add_check(checks, "Claim preparation-ready flags are complete", not [row.service_line for row in lines if not row.get("claim_preparation_ready")])
	_add_check(checks, "Submitted invoice-ready flags are complete", not [row.service_line for row in lines if not row.get("submitted_invoice_ready")])
	_add_check(checks, "Claim batch mapping review complete", not [row.service_line for row in lines if not row.get("claim_batch_mapping_ready")])
	_add_check(checks, "No claim batch draft creation hold remains", not [row.service_line for row in lines if row.get("claim_batch_draft_creation_hold")])
	_add_check(checks, "All lines marked ready for claim batch draft creation", not [row.service_line for row in lines if not row.get("line_ready_for_claim_batch_draft_creation")])
	total = len(checks)
	complete = len([row for row in checks if row["complete"]])
	incomplete = [row["label"] for row in checks if not row["complete"]]
	return {
		"total_checks": total,
		"complete_checks": complete,
		"readiness_percent": round((complete / total) * 100, 2) if total else 0,
		"claim_batch_draft_run_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(CLAIM_BATCH_DRAFT_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_BATCH_DRAFT_RUN, "claim_batch_draft_run_ready"):
		doc.claim_batch_draft_run_ready = 1 if summary["claim_batch_draft_run_ready"] else 0
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
		(INTAKE, doc.get("participant_intake")),
	]
	for doctype, name in targets:
		_db_set_if_field(doctype, name, "ndis_claim_batch_draft_run", doc.name)
		_db_set_if_field(doctype, name, "claim_batch_draft_status", doc.status)
		_db_set_if_field(doctype, name, "claim_batch_draft_ready", 1 if summary["claim_batch_draft_run_ready"] else 0)
	return {"readiness": summary, "totals": totals}


def _get_default_company():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")


@frappe.whitelist()
def create_claim_batch_draft_run_from_claim_draft(claim_draft):
	_check_role()
	if not claim_draft or not frappe.db.exists(CLAIM_DRAFT, claim_draft):
		frappe.throw(_("NDIS CRM Claim Draft {0} was not found.").format(claim_draft))
	existing = _existing_run_for_claim_draft(claim_draft)
	if existing:
		return {"doctype": CLAIM_BATCH_DRAFT_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Batch Draft Run returned."}
	claim_doc = frappe.get_doc(CLAIM_DRAFT, claim_draft)
	doc = frappe.new_doc(CLAIM_BATCH_DRAFT_RUN)
	doc.status = "Draft"
	doc.claim_draft = claim_doc.name
	doc.sales_invoice_submission_run = _get_submission_run_for_claim_draft(claim_draft)
	for fieldname in [
		"billing_draft",
		"attendance_draft",
		"downstream_preparation",
		"delivery_evidence_review",
		"service_session_draft",
		"participant_service_file",
		"roster_build_request",
		"service_schedule_draft",
		"operations_setup",
		"finance_onboarding",
		"handover",
		"crm_deal",
		"crm_lead",
		"participant_intake",
		"participant_customer",
		"ndis_financial_profile",
		"participant_name",
		"ndis_number",
		"plan_start_date",
		"plan_end_date",
		"claim_period_start",
		"claim_period_end",
		"claim_owner",
		"billing_owner",
	]:
		doc.set(fieldname, claim_doc.get(fieldname))
	doc.invoice_draft = claim_doc.get("invoice_draft")
	doc.sales_invoice_draft_run = claim_doc.get("sales_invoice_draft_run")
	doc.claim_batch_owner = frappe.session.user
	doc.company = _get_default_company()
	doc.claim_batch_draft_creation_allowed = 0
	created_count = _generate_lines_from_claim_draft(doc, claim_doc)
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_batch_draft_run_ready = 1 if summary["claim_batch_draft_run_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": CLAIM_BATCH_DRAFT_RUN,
		"name": doc.name,
		"created": True,
		"claim_batch_draft_line_count": created_count,
		"message": "NDIS CRM Claim Batch Draft Run created successfully.",
	}


@frappe.whitelist()
def create_claim_batch_draft_run_from_crm_deal(deal):
	_check_role()
	if not deal or not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))
	existing = _existing_run_for_deal(deal)
	if existing:
		return {"doctype": CLAIM_BATCH_DRAFT_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Batch Draft Run returned."}
	claim_draft = _get_claim_draft_for_deal(deal)
	if not claim_draft:
		frappe.throw(_("Please create and approve NDIS CRM Claim Draft before creating Claim Batch Draft Run."))
	return create_claim_batch_draft_run_from_claim_draft(claim_draft)


@frappe.whitelist()
def generate_claim_batch_draft_lines(claim_batch_draft_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run)
	if not doc.get("claim_draft"):
		frappe.throw(_("Claim Draft is required."))
	created_count = _generate_lines_from_claim_draft(doc, frappe.get_doc(CLAIM_DRAFT, doc.claim_draft))
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Claim batch draft lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_claim_batch_draft_run_readiness(claim_batch_draft_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Claim Batch Draft Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_claim_batch_draft_creation(claim_batch_draft_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_batch_draft_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Claim Batch Draft Creation. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Claim Batch Draft Creation"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_batch_draft_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_BATCH_DRAFT_RUN, "name": doc.name, "message": "Claim Batch Draft Run marked Ready for Claim Batch Draft Creation."}


@frappe.whitelist()
def approve_claim_batch_draft_run(claim_batch_draft_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_batch_draft_run_ready"]:
		frappe.throw(_("Cannot approve Claim Batch Draft Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Claim Batch Draft Run Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_batch_draft_run_ready = 1
	doc.claim_batch_draft_creation_allowed = 0
	for row in doc.get("claim_batch_draft_lines") or []:
		if row.get("claim_batch_draft_status") in ["Draft", "Ready"]:
			row.claim_batch_draft_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_BATCH_DRAFT_RUN, "name": doc.name, "message": "Claim Batch Draft Run approved. Draft NDIS Claim Batch was not created yet."}


def _ready_lines_for_claim_batch_creation(doc):
	return [
		row
		for row in doc.get("claim_batch_draft_lines") or []
		if row.get("claim_batch_draft_status") in ["Approved", "Ready"]
		and row.get("line_ready_for_claim_batch_draft_creation")
		and not row.get("claim_batch_draft_creation_hold")
		and not row.get("ndis_claim_batch")
		and row.get("submitted_invoice_ready")
	]


def _set_claim_batch_fields(batch, run_doc, ready_lines):
	_set_first_existing(batch, ["claim_batch_id"], f"CRM-CB-{run_doc.name}", force=True)
	_set_first_existing(batch, ["batch_type"], "NDIA Claim", force=True)
	_set_first_existing(batch, ["status", "claim_batch_status", "batch_status"], "Draft", force=True)
	_set_first_existing(batch, ["company"], run_doc.get("company"))
	_set_first_existing(batch, ["claim_period_start", "period_start", "from_date", "start_date"], run_doc.get("claim_period_start"))
	_set_first_existing(batch, ["claim_period_end", "period_end", "to_date", "end_date"], run_doc.get("claim_period_end"))
	_set_first_existing(batch, ["participant", "participant_customer", "customer", "ndis_participant"], run_doc.get("participant_customer"))
	_set_first_existing(batch, ["funding_source"], next((row.get("funding_source") for row in ready_lines if row.get("funding_source")), None))
	_set_first_existing(batch, ["total_claim_amount"], sum(float(row.get("claim_amount") or 0) for row in ready_lines), force=True)
	_set_first_existing(batch, ["claim_line_count"], len(ready_lines), force=True)
	_set_first_existing(batch, ["batch_notes", "notes", "remarks"], f"Draft only. Created from {run_doc.doctype} {run_doc.name}. No claim export/submission performed.")


def _set_claim_line_fields(line_doc, run_doc, row, batch_name=None):
	line_key = row.get("claim_source_key") or row.name
	_set_first_existing(line_doc, ["claim_batch", "batch", "ndis_claim_batch", "parent_claim_batch"], batch_name)
	_set_first_existing(line_doc, ["batch_type"], "NDIA Claim", force=True)
	_set_first_existing(line_doc, ["company"], run_doc.get("company"))
	_set_first_existing(line_doc, ["sales_invoice"], row.get("sales_invoice"))
	_set_first_existing(line_doc, ["sales_invoice_item"], line_key, force=True)
	_set_first_existing(line_doc, ["posting_date"], _sales_invoice_snapshot(row.get("sales_invoice")).get("posting_date"))
	_set_first_existing(line_doc, ["participant", "participant_customer", "customer", "ndis_participant"], run_doc.get("participant_customer"))
	_set_first_existing(line_doc, ["house", "ndis_house", "default_house"], row.get("default_house"))
	_set_first_existing(line_doc, ["service_date", "claim_date", "date"], row.get("service_date"))
	_set_first_existing(line_doc, ["funding_source", "ndis_funding_source"], row.get("funding_source"))
	_set_first_existing(line_doc, ["service_type", "finance_service_type", "ndis_service_type"], row.get("finance_service_type"))
	_set_first_existing(line_doc, ["support_item", "ndis_support_item", "item", "item_code"], row.get("support_item"))
	_set_first_existing(line_doc, ["qty", "quantity", "claim_quantity"], row.get("claim_quantity"))
	_set_first_existing(line_doc, ["rate", "claim_rate"], row.get("claim_rate"))
	_set_first_existing(line_doc, ["claim_amount", "amount"], row.get("claim_amount"))
	_set_first_existing(line_doc, ["gst_treatment"], row.get("gst_treatment"))
	_set_first_existing(line_doc, ["plan_budget", "ndis_plan_budget"], row.get("plan_budget"))
	_set_first_existing(line_doc, ["service_booking", "ndis_service_booking"], row.get("service_booking"))
	_set_first_existing(line_doc, ["claim_status", "status"], "Draft", force=True)
	_set_first_existing(line_doc, ["payment_status"], "Not Paid", force=True)
	_set_first_existing(line_doc, ["export_status"], "Not Exported", force=True)
	_set_first_existing(line_doc, ["external_claim_reference"], f"{run_doc.name}:{line_key}")
	_set_first_existing(line_doc, ["custom_ndis_batch_source_sales_invoice"], row.get("sales_invoice"))
	_set_first_existing(line_doc, ["custom_ndis_batch_source_amount"], row.get("claim_amount"))


def _missing_required_fields(doc):
	missing = []
	for df in frappe.get_meta(doc.doctype).fields:
		if df.reqd and not doc.get(df.fieldname):
			missing.append(df.fieldname)
	return missing


def _create_claim_batch_for_ready_lines(run_doc, ready_lines):
	batch = frappe.new_doc(NDIS_CLAIM_BATCH)
	_set_claim_batch_fields(batch, run_doc, ready_lines)
	missing = _missing_required_fields(batch)
	if missing:
		frappe.throw(_("Cannot create NDIS Claim Batch. Missing required fields on {0}: {1}").format(NDIS_CLAIM_BATCH, ", ".join(missing)))
	batch.insert(ignore_permissions=True)
	if getattr(batch, "docstatus", 0) != 0:
		frappe.throw(_("Safety error: NDIS Claim Batch was not created in Draft state."))
	claim_lines = []
	for row in ready_lines:
		claim_line = frappe.new_doc(NDIS_CLAIM_LINE)
		_set_claim_line_fields(claim_line, run_doc, row, batch_name=batch.name)
		missing = _missing_required_fields(claim_line)
		if missing:
			frappe.throw(_("Cannot create NDIS Claim Line. Missing required fields on {0}: {1}").format(NDIS_CLAIM_LINE, ", ".join(missing)))
		claim_line.insert(ignore_permissions=True)
		if getattr(claim_line, "docstatus", 0) != 0:
			frappe.throw(_("Safety error: NDIS Claim Line was not created in Draft state."))
		claim_lines.append(claim_line.name)
		row.ndis_claim_batch = batch.name
		row.ndis_claim_line = claim_line.name
		row.claim_batch_draft_status = "Draft Claim Batch Created"
		row.claim_batch_draft_creation_ready = 1
		row.claim_batch_draft_creation_hold = 0
	return batch.name, claim_lines


@frappe.whitelist()
def create_draft_claim_batches(claim_batch_draft_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run)
	if doc.status != "Claim Batch Draft Run Approved":
		frappe.throw(_("Claim Batch Draft Run must be approved before draft claim batches can be created."))
	if not doc.get("claim_batch_draft_creation_allowed"):
		frappe.throw(_("Tick Claim Batch Draft Creation Allowed before creating draft claim batches."))
	summary = _calculate_readiness(doc)
	if not summary["claim_batch_draft_run_ready"]:
		frappe.throw(_("Cannot create draft claim batches. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	ready_lines = _ready_lines_for_claim_batch_creation(doc)
	if not ready_lines:
		frappe.throw(_("No ready claim batch draft lines found for creation."))
	claim_batch, claim_lines = _create_claim_batch_for_ready_lines(doc, ready_lines)
	doc.status = "Draft Claim Batches Created"
	doc.claim_batch_draft_creation_allowed = 0
	_sync_totals(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"claim_batch": claim_batch,
		"claim_lines": claim_lines,
		"created_line_count": len(ready_lines),
		"message": "Draft NDIS Claim Batch created. No claim export, claim submission, payment, journal, manual GL, remittance, or write-off was created.",
	}


def validate_claim_batch_draft_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(CLAIM_BATCH_DRAFT_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_BATCH_DRAFT_RUN, "claim_batch_draft_run_ready"):
		doc.claim_batch_draft_run_ready = 1 if summary["claim_batch_draft_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["claim_batch_draft_run_ready"]:
		frappe.throw(_("Cannot set Claim Batch Draft Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Claim Batch Draft Run Approved" and doc.get("claim_batch_draft_creation_allowed"):
		frappe.throw(_("Claim Batch Draft Creation Allowed can only be ticked after the run is approved."))


def on_claim_batch_draft_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Claim Batch Draft Run Summary Sync Failed")


def validate_crm_deal_phase20(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	required = doc.get("ndis_claim_batch_draft_run_required") if _field_exists(CRM_DEAL, "ndis_claim_batch_draft_run_required") else 0
	if not required:
		return
	run = doc.get("ndis_claim_batch_draft_run") if _field_exists(CRM_DEAL, "ndis_claim_batch_draft_run") else None
	if not run:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Batch Draft Run must be created and approved."))
	if not _is_claim_batch_draft_run_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Batch Draft Run must be approved."))


def validate_crm_deal_phase20_combined(doc, method=None):
	try:
		from ndis_crm.phase19_sales_invoice_submission import validate_crm_deal_phase19_combined

		validate_crm_deal_phase19_combined(doc, method)
	except ImportError:
		pass
	validate_crm_deal_phase20(doc, method)


def phase20_health_check():
	print("---- NDIS CRM Phase 20 Health Check ----")
	for dt in [
		CLAIM_BATCH_DRAFT_LINE,
		CLAIM_BATCH_DRAFT_RUN,
		CLAIM_DRAFT,
		CLAIM_DRAFT_LINE,
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
		NDIS_CLAIM_BATCH,
		NDIS_CLAIM_LINE,
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	print("NDIS Claim Line child table field on NDIS Claim Batch: STANDALONE / NOT FOUND")
	for dt in ["Payment Entry", "Journal Entry", "GL Entry", "NDIS Remittance Import", "NDIS Recovery Case", "NDIS Write Off", PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in ["ndis_claim_batch_draft_run_required", "ndis_claim_batch_draft_run", "claim_batch_draft_status", "claim_batch_draft_ready"]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")
	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, SESSION_DRAFT, EVIDENCE_REVIEW, DOWNSTREAM_PREPARATION, ATTENDANCE_DRAFT, BILLING_DRAFT, CLAIM_DRAFT, INVOICE_DRAFT, SALES_INVOICE_DRAFT_RUN, SALES_INVOICE_SUBMISSION_RUN, INTAKE]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_claim_batch_draft_run", "claim_batch_draft_status", "claim_batch_draft_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Claim Batch Draft Run records:", frappe.db.count(CLAIM_BATCH_DRAFT_RUN) if _doctype_exists(CLAIM_BATCH_DRAFT_RUN) else 0)
	print("Phase 20 creates NDIS Claim Batch / Claim Line drafts only.")
	print("Phase 20 does not export, submit, remit, pay, journal, write off, or manually post GL.")
	print("---- End Phase 20 Health Check ----")
