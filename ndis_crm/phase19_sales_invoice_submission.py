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
SALES_INVOICE_DRAFT_LINE = "NDIS CRM Sales Invoice Draft Line"
SALES_INVOICE_SUBMISSION_RUN = "NDIS CRM Sales Invoice Submission Run"
SALES_INVOICE_SUBMISSION_LINE = "NDIS CRM Sales Invoice Submission Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"
SALES_INVOICE = "Sales Invoice"

READY_STATUSES = ["Ready for Sales Invoice Submission", "Sales Invoice Submission Run Approved"]
APPROVED_STATUSES = ["Sales Invoice Submission Run Approved", "Sales Invoices Submitted"]
APPROVED_DRAFT_RUN_STATUSES = ["Draft Sales Invoices Created"]

ALLOWED_ROLES = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"NDIS CRM Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this Sales Invoice submission action."))


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


def _existing_submission_run_for_draft_run(sales_invoice_draft_run):
	if not _doctype_exists(SALES_INVOICE_SUBMISSION_RUN):
		return None
	if _field_exists(SALES_INVOICE_DRAFT_RUN, "ndis_sales_invoice_submission_run"):
		existing = frappe.db.get_value(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run, "ndis_sales_invoice_submission_run")
		if existing:
			return existing
	return frappe.db.get_value(SALES_INVOICE_SUBMISSION_RUN, {"sales_invoice_draft_run": sales_invoice_draft_run}, "name")


def _existing_submission_run_for_deal(deal):
	if not _doctype_exists(SALES_INVOICE_SUBMISSION_RUN):
		return None
	if _field_exists(CRM_DEAL, "ndis_sales_invoice_submission_run"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_sales_invoice_submission_run")
		if existing:
			return existing
	return frappe.db.get_value(SALES_INVOICE_SUBMISSION_RUN, {"crm_deal": deal}, "name")


def _get_sales_invoice_draft_run_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_sales_invoice_draft_run"):
		run = frappe.db.get_value(CRM_DEAL, deal, "ndis_sales_invoice_draft_run")
		if run:
			return run
	if _doctype_exists(SALES_INVOICE_DRAFT_RUN):
		return frappe.db.get_value(SALES_INVOICE_DRAFT_RUN, {"crm_deal": deal}, "name")
	return None


def _is_draft_run_created(sales_invoice_draft_run):
	if not sales_invoice_draft_run or not frappe.db.exists(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run):
		return False
	status, ready = frappe.db.get_value(
		SALES_INVOICE_DRAFT_RUN,
		sales_invoice_draft_run,
		["status", "sales_invoice_draft_run_ready"],
	)
	return status in APPROVED_DRAFT_RUN_STATUSES and bool(ready)


def _is_submission_run_approved(run):
	if not run or not frappe.db.exists(SALES_INVOICE_SUBMISSION_RUN, run):
		return False
	status, ready = frappe.db.get_value(
		SALES_INVOICE_SUBMISSION_RUN,
		run,
		["status", "sales_invoice_submission_run_ready"],
	)
	return status in APPROVED_STATUSES and bool(ready)


def _line_key(row):
	return row.get("invoice_source_key") or "|".join([
		str(row.get("service_line") or ""),
		str(row.get("sales_invoice") or ""),
		str(row.get("invoice_date") or ""),
	])


def _append_line_if_missing(doc, row_data):
	existing = {
		row.sales_invoice_source_key
		for row in doc.get("submission_lines") or []
		if row.get("sales_invoice_source_key")
	}
	key = row_data.get("sales_invoice_source_key")
	if key and key in existing:
		return False
	doc.append("submission_lines", row_data)
	return True


def _get_sales_invoice_snapshot(sales_invoice):
	if not sales_invoice or not frappe.db.exists(SALES_INVOICE, sales_invoice):
		return {}
	return frappe.db.get_value(
		SALES_INVOICE,
		sales_invoice,
		["name", "docstatus", "customer", "company", "posting_date", "due_date", "grand_total", "rounded_total", "status"],
		as_dict=True,
	) or {}


def _draft_sales_invoice_ready(sales_invoice):
	snapshot = _get_sales_invoice_snapshot(sales_invoice)
	return bool(snapshot and snapshot.get("docstatus") == 0)


def _build_submission_line_from_draft_line(row):
	sales_invoice = row.get("sales_invoice")
	snapshot = _get_sales_invoice_snapshot(sales_invoice)
	docstatus = snapshot.get("docstatus")
	invoice_total = snapshot.get("rounded_total") or snapshot.get("grand_total") or row.get("invoice_amount")
	source_ready = bool(
		sales_invoice
		and snapshot
		and docstatus == 0
		and row.get("sales_invoice_draft_status") == "Draft Sales Invoice Created"
		and row.get("line_ready_for_draft_sales_invoice_creation")
		and not row.get("billing_hold")
		and not row.get("sales_invoice_draft_creation_hold")
	)
	return {
		"sales_invoice_source_key": _line_key(row),
		"sales_invoice": sales_invoice,
		"sales_invoice_docstatus": docstatus,
		"sales_invoice_status": snapshot.get("status"),
		"customer": snapshot.get("customer"),
		"company": snapshot.get("company"),
		"posting_date": snapshot.get("posting_date"),
		"due_date": snapshot.get("due_date"),
		"sales_invoice_total": invoice_total,
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"invoice_group_key": row.get("invoice_group_key"),
		"invoice_date": row.get("invoice_date"),
		"invoice_quantity": row.get("invoice_quantity"),
		"invoice_rate": row.get("invoice_rate"),
		"invoice_amount": row.get("invoice_amount"),
		"erp_item_code": row.get("erp_item_code"),
		"income_account": row.get("income_account"),
		"cost_center": row.get("cost_center"),
		"support_item": row.get("support_item"),
		"finance_service_type": row.get("finance_service_type"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"funding_source": row.get("funding_source"),
		"default_house": row.get("default_house"),
		"billing_preparation_ready": row.get("billing_preparation_ready"),
		"submission_precheck_ready": 1 if source_ready else 0,
		"finance_submission_review_complete": 0,
		"submit_authorized": 0,
		"submission_hold": 0 if source_ready else 1,
		"submission_hold_reason": None if source_ready else "Draft Sales Invoice is not ready for submission.",
		"line_ready_for_sales_invoice_submit": 0,
		"submission_status": "Draft",
		"submitted_by": None,
		"submitted_on": None,
		"notes": row.get("notes"),
	}


def _generate_lines_from_draft_run(submission_doc, draft_run_doc):
	created = 0
	for row in draft_run_doc.get("sales_invoice_draft_lines") or []:
		if not row.get("sales_invoice"):
			continue
		if row.get("sales_invoice_draft_status") != "Draft Sales Invoice Created":
			continue
		if _append_line_if_missing(submission_doc, _build_submission_line_from_draft_line(row)):
			created += 1
	return created


def _calculate_totals(doc):
	totals = {
		"submission_line_count": len(doc.get("submission_lines") or []),
		"sales_invoice_amount_total": 0,
		"draft_sales_invoice_count": 0,
		"submitted_sales_invoice_count": 0,
		"sales_invoice_submit_ready_count": 0,
		"sales_invoice_submission_hold_count": 0,
		"missing_sales_invoice_count": 0,
	}
	for row in doc.get("submission_lines") or []:
		try:
			totals["sales_invoice_amount_total"] += float(row.get("sales_invoice_total") or 0)
		except Exception:
			pass
		if row.get("sales_invoice_docstatus") == 0:
			totals["draft_sales_invoice_count"] += 1
		if row.get("sales_invoice_docstatus") == 1:
			totals["submitted_sales_invoice_count"] += 1
		if row.get("line_ready_for_sales_invoice_submit"):
			totals["sales_invoice_submit_ready_count"] += 1
		if row.get("submission_hold"):
			totals["sales_invoice_submission_hold_count"] += 1
		if not row.get("sales_invoice"):
			totals["missing_sales_invoice_count"] += 1
	totals["sales_invoice_amount_total"] = round(totals["sales_invoice_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(SALES_INVOICE_SUBMISSION_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _add_check(checks, label, complete, details=None):
	checks.append({"label": label, "complete": bool(complete), "details": details or []})


def _calculate_readiness(doc):
	checks = []
	lines = doc.get("submission_lines") or []
	_add_check(checks, "Sales Invoice Draft Run linked", doc.get("sales_invoice_draft_run"))
	_add_check(checks, "Draft Sales Invoices created by Phase 18", _is_draft_run_created(doc.get("sales_invoice_draft_run")))
	_add_check(checks, "ERPNext Sales Invoice DocType exists", _doctype_exists(SALES_INVOICE))
	_add_check(checks, "Participant Customer linked", doc.get("participant_customer"))
	_add_check(checks, "Company selected", doc.get("company"))
	_add_check(checks, "Submission Owner assigned", doc.get("submission_owner"))
	_add_check(checks, "At least one submission line exists", lines)
	_add_check(checks, "All lines have Sales Invoice reference", not [row.service_line for row in lines if not row.get("sales_invoice")])

	missing_invoice_doc = [
		row.sales_invoice for row in lines
		if row.get("sales_invoice") and not frappe.db.exists(SALES_INVOICE, row.get("sales_invoice"))
	]
	_add_check(checks, "All referenced Sales Invoices exist", not missing_invoice_doc, missing_invoice_doc)

	wrong_docstatus = []
	for row in lines:
		if not row.get("sales_invoice"):
			continue
		docstatus = _get_sales_invoice_snapshot(row.get("sales_invoice")).get("docstatus")
		if doc.status == "Sales Invoices Submitted":
			if docstatus != 1:
				wrong_docstatus.append(row.get("sales_invoice"))
		elif docstatus != 0:
			wrong_docstatus.append(row.get("sales_invoice"))
	_add_check(checks, "Sales Invoice docstatus is valid for current run status", not wrong_docstatus, wrong_docstatus)

	customer_mismatch = []
	for row in lines:
		if not row.get("sales_invoice"):
			continue
		snapshot = _get_sales_invoice_snapshot(row.get("sales_invoice"))
		if snapshot and doc.get("participant_customer") and snapshot.get("customer") != doc.get("participant_customer"):
			customer_mismatch.append(row.get("sales_invoice"))
	_add_check(checks, "Sales Invoice customer matches participant customer", not customer_mismatch, customer_mismatch)

	_add_check(
		checks,
		"Submission precheck-ready flags are complete",
		not [row.service_line for row in lines if not row.get("submission_precheck_ready")],
	)
	_add_check(
		checks,
		"Finance submission review complete",
		not [row.service_line for row in lines if not row.get("finance_submission_review_complete")],
	)
	_add_check(
		checks,
		"All lines have submit authorization",
		not [row.service_line for row in lines if not row.get("submit_authorized")],
	)
	_add_check(checks, "No submission hold remains", not [row.service_line for row in lines if row.get("submission_hold")])
	_add_check(
		checks,
		"All lines marked ready for Sales Invoice submit",
		not [row.service_line for row in lines if not row.get("line_ready_for_sales_invoice_submit")],
	)

	total = len(checks)
	complete = len([row for row in checks if row["complete"]])
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
		"readiness_percent": round((complete / total) * 100, 2) if total else 0,
		"sales_invoice_submission_run_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(SALES_INVOICE_SUBMISSION_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(SALES_INVOICE_SUBMISSION_RUN, "sales_invoice_submission_run_ready"):
		doc.sales_invoice_submission_run_ready = 1 if summary["sales_invoice_submission_run_ready"] else 0
	for doctype, name in [
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
		(INTAKE, doc.get("participant_intake")),
	]:
		_db_set_if_field(doctype, name, "ndis_sales_invoice_submission_run", doc.name)
		_db_set_if_field(doctype, name, "sales_invoice_submission_status", doc.status)
		_db_set_if_field(doctype, name, "sales_invoice_submission_ready", 1 if summary["sales_invoice_submission_run_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_sales_invoice_submission_run_from_draft_run(sales_invoice_draft_run):
	_check_role()
	if not sales_invoice_draft_run:
		frappe.throw(_("NDIS CRM Sales Invoice Draft Run is required."))
	if not frappe.db.exists(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run):
		frappe.throw(_("NDIS CRM Sales Invoice Draft Run {0} was not found.").format(sales_invoice_draft_run))
	existing = _existing_submission_run_for_draft_run(sales_invoice_draft_run)
	if existing:
		return {"doctype": SALES_INVOICE_SUBMISSION_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Sales Invoice Submission Run returned."}
	source = frappe.get_doc(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run)
	doc = frappe.new_doc(SALES_INVOICE_SUBMISSION_RUN)
	doc.status = "Draft"
	doc.sales_invoice_draft_run = source.name
	for fieldname in [
		"invoice_draft",
		"claim_draft",
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
		"invoice_period_start",
		"invoice_period_end",
		"sales_invoice_owner",
		"invoice_owner",
		"billing_owner",
		"company",
	]:
		doc.set(fieldname, source.get(fieldname))
	doc.participant_name = doc.get("participant_name") or doc.get("participant_customer") or source.name
	doc.submission_owner = frappe.session.user
	doc.submission_allowed = 0
	created_count = _generate_lines_from_draft_run(doc, source)
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_submission_run_ready = 1 if summary["sales_invoice_submission_run_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": SALES_INVOICE_SUBMISSION_RUN,
		"name": doc.name,
		"created": True,
		"submission_line_count": created_count,
		"message": "NDIS CRM Sales Invoice Submission Run created successfully.",
	}


@frappe.whitelist()
def create_sales_invoice_submission_run_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))
	existing = _existing_submission_run_for_deal(deal)
	if existing:
		return {"doctype": SALES_INVOICE_SUBMISSION_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Sales Invoice Submission Run returned."}
	draft_run = _get_sales_invoice_draft_run_for_deal(deal)
	if not draft_run:
		frappe.throw(_("Please create NDIS CRM Sales Invoice Draft Run before creating Submission Run."))
	return create_sales_invoice_submission_run_from_draft_run(draft_run)


@frappe.whitelist()
def generate_sales_invoice_submission_lines(sales_invoice_submission_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_SUBMISSION_RUN, sales_invoice_submission_run)
	if not doc.get("sales_invoice_draft_run"):
		frappe.throw(_("Sales Invoice Draft Run is required."))
	source = frappe.get_doc(SALES_INVOICE_DRAFT_RUN, doc.sales_invoice_draft_run)
	created_count = _generate_lines_from_draft_run(doc, source)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Sales Invoice submission lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_sales_invoice_submission_readiness(sales_invoice_submission_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_SUBMISSION_RUN, sales_invoice_submission_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Sales Invoice Submission Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_sales_invoice_submission(sales_invoice_submission_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_SUBMISSION_RUN, sales_invoice_submission_run)
	summary = _calculate_readiness(doc)
	if not summary["sales_invoice_submission_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Sales Invoice Submission. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Sales Invoice Submission"
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_submission_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": SALES_INVOICE_SUBMISSION_RUN, "name": doc.name, "message": "Sales Invoice Submission Run marked Ready for Submission."}


@frappe.whitelist()
def approve_sales_invoice_submission_run(sales_invoice_submission_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_SUBMISSION_RUN, sales_invoice_submission_run)
	summary = _calculate_readiness(doc)
	if not summary["sales_invoice_submission_run_ready"]:
		frappe.throw(_("Cannot approve Sales Invoice Submission Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Sales Invoice Submission Run Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_submission_run_ready = 1
	doc.submission_allowed = 0
	for row in doc.get("submission_lines") or []:
		if row.get("submission_status") in ["Draft", "Ready"]:
			row.submission_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": SALES_INVOICE_SUBMISSION_RUN, "name": doc.name, "message": "Sales Invoice Submission Run approved. Sales Invoices were not submitted yet."}


def _ready_lines_for_submit(doc):
	ready = []
	for row in doc.get("submission_lines") or []:
		if row.get("submission_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("line_ready_for_sales_invoice_submit") or not row.get("submit_authorized"):
			continue
		if row.get("submission_hold") or not row.get("sales_invoice"):
			continue
		if not _draft_sales_invoice_ready(row.get("sales_invoice")):
			continue
		ready.append(row)
	return ready


@frappe.whitelist()
def submit_sales_invoices(sales_invoice_submission_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_SUBMISSION_RUN, sales_invoice_submission_run)
	if doc.status != "Sales Invoice Submission Run Approved":
		frappe.throw(_("Sales Invoice Submission Run must be approved before submission."))
	if not doc.get("submission_allowed"):
		frappe.throw(_("Tick Submission Allowed before submitting Sales Invoices."))
	summary = _calculate_readiness(doc)
	if not summary["sales_invoice_submission_run_ready"]:
		frappe.throw(_("Cannot submit Sales Invoices. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	ready_lines = _ready_lines_for_submit(doc)
	if not ready_lines:
		frappe.throw(_("No ready draft Sales Invoices found for submission."))
	submitted = []
	for row in ready_lines:
		sales_invoice = row.get("sales_invoice")
		invoice = frappe.get_doc(SALES_INVOICE, sales_invoice)
		if invoice.docstatus != 0:
			frappe.throw(_("Sales Invoice {0} is not in Draft status.").format(sales_invoice))
		invoice.submit()
		if invoice.docstatus != 1:
			frappe.throw(_("Safety error: Sales Invoice {0} was not submitted correctly.").format(sales_invoice))
		row.sales_invoice_docstatus = 1
		row.sales_invoice_status = invoice.get("status") or "Submitted"
		row.submission_status = "Submitted"
		row.submitted_by = frappe.session.user
		row.submitted_on = now()
		row.submission_hold = 0
		submitted.append(sales_invoice)
	doc.status = "Sales Invoices Submitted"
	doc.submission_allowed = 0
	_sync_totals(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"submitted_count": len(submitted),
		"sales_invoices": submitted,
		"message": f"Submitted {len(submitted)} Sales Invoice(s). No Payment Entry, Journal Entry, manual GL Entry, or Claim Batch was created by Phase 19.",
	}


def validate_sales_invoice_submission_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_submission_run_ready = 1 if summary["sales_invoice_submission_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["sales_invoice_submission_run_ready"]:
		frappe.throw(_("Cannot set Sales Invoice Submission Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Sales Invoice Submission Run Approved" and doc.get("submission_allowed"):
		frappe.throw(_("Submission Allowed can only be ticked after the run is approved."))


def on_sales_invoice_submission_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Sales Invoice Submission Run Summary Sync Failed")


def validate_crm_deal_phase19(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	required = doc.get("ndis_sales_invoice_submission_run_required") if _field_exists(CRM_DEAL, "ndis_sales_invoice_submission_run_required") else 0
	if not required:
		return
	run = doc.get("ndis_sales_invoice_submission_run") if _field_exists(CRM_DEAL, "ndis_sales_invoice_submission_run") else None
	if not run:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Sales Invoice Submission Run must be created and approved."))
	if not _is_submission_run_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Sales Invoice Submission Run must be approved."))


def validate_crm_deal_phase19_combined(doc, method=None):
	try:
		from ndis_crm.phase18_sales_invoice_draft import validate_crm_deal_phase18_combined
		validate_crm_deal_phase18_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase17_invoice_draft import validate_crm_deal_phase17_combined
			validate_crm_deal_phase17_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase19(doc, method)


def phase19_health_check():
	print("---- NDIS CRM Phase 19 Health Check ----")
	for dt in [
		SALES_INVOICE_SUBMISSION_LINE,
		SALES_INVOICE_SUBMISSION_RUN,
		SALES_INVOICE_DRAFT_RUN,
		SALES_INVOICE_DRAFT_LINE,
		INVOICE_DRAFT,
		CLAIM_DRAFT,
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
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for dt in ["Payment Entry", "Journal Entry", "GL Entry", "NDIS Claim Batch", "NDIS Claim Line", PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in ["ndis_sales_invoice_submission_run_required", "ndis_sales_invoice_submission_run", "sales_invoice_submission_status", "sales_invoice_submission_ready"]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")
	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, SESSION_DRAFT, EVIDENCE_REVIEW, DOWNSTREAM_PREPARATION, ATTENDANCE_DRAFT, BILLING_DRAFT, CLAIM_DRAFT, INVOICE_DRAFT, SALES_INVOICE_DRAFT_RUN, INTAKE]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_sales_invoice_submission_run", "sales_invoice_submission_status", "sales_invoice_submission_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Sales Invoice Submission Run records:", frappe.db.count(SALES_INVOICE_SUBMISSION_RUN) if _doctype_exists(SALES_INVOICE_SUBMISSION_RUN) else 0)
	print("Phase 19 may submit existing Draft Sales Invoices only after explicit approval.")
	print("Phase 19 does not create Payment Entry / Journal Entry / manual GL Entry / Claim Batch.")
	print("---- End Phase 19 Health Check ----")
