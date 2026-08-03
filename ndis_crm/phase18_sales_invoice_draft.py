import frappe
from frappe import _
from frappe.utils import add_days, nowdate


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
INVOICE_DRAFT = "NDIS CRM Invoice Draft"
INVOICE_DRAFT_LINE = "NDIS CRM Invoice Draft Line"

SALES_INVOICE_DRAFT_RUN = "NDIS CRM Sales Invoice Draft Run"
SALES_INVOICE_DRAFT_LINE = "NDIS CRM Sales Invoice Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"
SALES_INVOICE = "Sales Invoice"
SALES_INVOICE_ITEM = "Sales Invoice Item"
ITEM = "Item"

READY_STATUSES = [
	"Ready for Sales Invoice Draft Creation",
	"Sales Invoice Draft Run Approved",
	"Draft Sales Invoices Created",
]
APPROVED_STATUSES = ["Sales Invoice Draft Run Approved", "Draft Sales Invoices Created"]
APPROVED_INVOICE_DRAFT_STATUSES = ["Invoice Draft Approved"]

ALLOWED_ROLES = {
	"System Manager",
	"Sales Manager",
	"Sales User",
	"Accounts Manager",
	"Accounts User",
	"NDIS CRM Manager",
	"NDIS Intake Officer",
	"NDIS Service Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this Sales Invoice draft action."))


def _doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
	return bool(
		frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
		or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
	)


def _set_if_field(doc, fieldname, value):
	if value is not None and _field_exists(doc.doctype, fieldname):
		doc.set(fieldname, value)


def _db_set_if_field(doctype, name, fieldname, value):
	if name and _field_exists(doctype, fieldname):
		frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)


def _get_first_existing_value(doctype, name, fieldnames):
	if not name or not _doctype_exists(doctype):
		return None
	for fieldname in fieldnames:
		if _field_exists(doctype, fieldname):
			value = frappe.db.get_value(doctype, name, fieldname)
			if value:
				return value
	return None


def _existing_run_for_invoice_draft(invoice_draft):
	if not _doctype_exists(SALES_INVOICE_DRAFT_RUN):
		return None
	if _field_exists(INVOICE_DRAFT, "ndis_sales_invoice_draft_run"):
		existing = frappe.db.get_value(INVOICE_DRAFT, invoice_draft, "ndis_sales_invoice_draft_run")
		if existing:
			return existing
	return frappe.db.get_value(SALES_INVOICE_DRAFT_RUN, {"invoice_draft": invoice_draft}, "name")


def _existing_run_for_deal(deal):
	if not _doctype_exists(SALES_INVOICE_DRAFT_RUN):
		return None
	if _field_exists(CRM_DEAL, "ndis_sales_invoice_draft_run"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_sales_invoice_draft_run")
		if existing:
			return existing
	return frappe.db.get_value(SALES_INVOICE_DRAFT_RUN, {"crm_deal": deal}, "name")


def _get_invoice_draft_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_invoice_draft"):
		invoice_draft = frappe.db.get_value(CRM_DEAL, deal, "ndis_invoice_draft")
		if invoice_draft:
			return invoice_draft
	if _doctype_exists(INVOICE_DRAFT):
		return frappe.db.get_value(INVOICE_DRAFT, {"crm_deal": deal}, "name")
	return None


def _is_invoice_draft_approved(invoice_draft):
	if not invoice_draft or not frappe.db.exists(INVOICE_DRAFT, invoice_draft):
		return False
	status, ready = frappe.db.get_value(INVOICE_DRAFT, invoice_draft, ["status", "invoice_draft_ready"])
	return status in APPROVED_INVOICE_DRAFT_STATUSES and bool(ready)


def _is_sales_invoice_run_approved(run):
	if not run or not frappe.db.exists(SALES_INVOICE_DRAFT_RUN, run):
		return False
	status, ready = frappe.db.get_value(SALES_INVOICE_DRAFT_RUN, run, ["status", "sales_invoice_draft_run_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _invoice_line_key(row):
	return row.get("billing_source_key") or "|".join([
		str(row.get("service_line") or ""),
		str(row.get("invoice_date") or ""),
		str(row.get("support_item") or ""),
		str(row.get("service_booking") or ""),
	])


def _append_run_line_if_missing(run_doc, row_data):
	existing = {
		row.invoice_source_key
		for row in run_doc.get("sales_invoice_draft_lines") or []
		if row.get("invoice_source_key")
	}
	key = row_data.get("invoice_source_key")
	if key and key in existing:
		return False
	run_doc.append("sales_invoice_draft_lines", row_data)
	return True


def _calculate_amount(quantity, rate):
	try:
		return round(float(quantity or 0) * float(rate or 0), 2)
	except Exception:
		return 0


def _resolve_item_code(invoice_line, run_doc=None):
	if invoice_line.get("erp_item_code"):
		return invoice_line.get("erp_item_code")
	if run_doc and run_doc.get("default_item_code"):
		return run_doc.get("default_item_code")
	support_item = invoice_line.get("support_item")
	if support_item and _doctype_exists(NDIS_SUPPORT_ITEM):
		mapped = _get_first_existing_value(
			NDIS_SUPPORT_ITEM,
			support_item,
			["erp_item_code", "item_code", "custom_erp_item_code", "custom_item_code"],
		)
		if mapped:
			return mapped
	if support_item and _doctype_exists(ITEM) and frappe.db.exists(ITEM, support_item):
		return support_item
	return None


def _resolve_funding_source(line):
	for doctype, name in [
		(SERVICE_BOOKING, line.get("service_booking")),
		(PLAN_BUDGET, line.get("plan_budget")),
	]:
		funding_source = _get_first_existing_value(
			doctype,
			name,
			["funding_source", "ndis_funding_source", "custom_ndis_funding_source"],
		)
		if funding_source:
			return funding_source
	return None


def _source_invoice_ready(row):
	return bool(
		row.get("invoice_draft_status") in ["Approved", "Ready"]
		and row.get("line_ready_for_sales_invoice_creation")
		and row.get("billing_preparation_ready")
		and not row.get("billing_hold")
		and not row.get("sales_invoice_creation_hold")
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("plan_budget")
		and row.get("invoice_date")
		and row.get("invoice_quantity")
		and row.get("invoice_rate")
		and row.get("invoice_amount")
	)


def _build_run_line_from_invoice_line(row, run_doc=None):
	quantity = row.get("invoice_quantity") or 0
	rate = row.get("invoice_rate") or 0
	amount = row.get("invoice_amount") or _calculate_amount(quantity, rate)
	item_code = _resolve_item_code(row, run_doc=run_doc)
	funding_source = _resolve_funding_source(row)
	source_ready = 1 if _source_invoice_ready(row) else 0
	item_ready = 1 if item_code else 0
	amount_ready = 1 if amount else 0
	line_ready = bool(source_ready and item_ready and amount_ready)
	return {
		"invoice_source_key": _invoice_line_key(row),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"invoice_group_key": row.get("invoice_group_key"),
		"proposed_invoice_reference": row.get("proposed_invoice_reference"),
		"invoice_date": row.get("invoice_date"),
		"billable_date": row.get("billable_date"),
		"session_date": row.get("session_date"),
		"actual_start_time": row.get("actual_start_time"),
		"actual_end_time": row.get("actual_end_time"),
		"delivered_hours": row.get("delivered_hours"),
		"invoice_quantity": quantity,
		"invoice_unit": row.get("invoice_unit") or "Hour",
		"invoice_rate": rate,
		"invoice_amount": amount,
		"gst_treatment": row.get("gst_treatment"),
		"rate_source": row.get("rate_source"),
		"erp_item_code": item_code,
		"item_ready": item_ready,
		"income_account": run_doc.get("default_income_account") if run_doc else None,
		"cost_center": run_doc.get("default_cost_center") if run_doc else None,
		"support_worker_user": row.get("support_worker_user"),
		"support_worker_employee": row.get("support_worker_employee"),
		"support_worker_name": row.get("support_worker_name"),
		"participant_attended": row.get("participant_attended"),
		"service_delivered": row.get("service_delivered"),
		"progress_note": row.get("progress_note"),
		"incident_flag": row.get("incident_flag"),
		"incident_notes": row.get("incident_notes"),
		"finance_service_type": row.get("finance_service_type"),
		"support_item": row.get("support_item"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"funding_source": funding_source,
		"default_house": row.get("default_house"),
		"delivery_location": row.get("delivery_location"),
		"billing_preparation_ready": source_ready,
		"claim_preparation_ready": row.get("claim_preparation_ready"),
		"billing_hold": row.get("billing_hold") or (0 if line_ready else 1),
		"billing_hold_reason": None if line_ready else "Sales Invoice draft source not fully ready.",
		"sales_invoice_draft_creation_ready": 0,
		"sales_invoice_draft_creation_hold": 1,
		"sales_invoice": None,
		"line_ready_for_draft_sales_invoice_creation": 0,
		"sales_invoice_draft_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_invoice_draft(run_doc, invoice_doc):
	created = 0
	for row in invoice_doc.get("invoice_lines") or []:
		if row.get("invoice_draft_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("line_ready_for_sales_invoice_creation"):
			continue
		if _append_run_line_if_missing(run_doc, _build_run_line_from_invoice_line(row, run_doc=run_doc)):
			created += 1
	return created


def _calculate_totals(doc):
	totals = {
		"sales_invoice_draft_line_count": len(doc.get("sales_invoice_draft_lines") or []),
		"invoice_quantity_total": 0,
		"invoice_amount_total": 0,
		"sales_invoice_ready_count": 0,
		"draft_sales_invoice_created_count": 0,
		"sales_invoice_draft_hold_count": 0,
		"missing_item_count": 0,
		"missing_income_account_count": 0,
		"missing_service_booking_count": 0,
	}
	for row in doc.get("sales_invoice_draft_lines") or []:
		try:
			totals["invoice_quantity_total"] += float(row.get("invoice_quantity") or 0)
			totals["invoice_amount_total"] += float(row.get("invoice_amount") or 0)
		except Exception:
			pass
		if row.get("line_ready_for_draft_sales_invoice_creation"):
			totals["sales_invoice_ready_count"] += 1
		if row.get("sales_invoice"):
			totals["draft_sales_invoice_created_count"] += 1
		if row.get("billing_hold") or row.get("sales_invoice_draft_creation_hold"):
			totals["sales_invoice_draft_hold_count"] += 1
		if not row.get("erp_item_code"):
			totals["missing_item_count"] += 1
		if not row.get("income_account"):
			totals["missing_income_account_count"] += 1
		if not row.get("service_booking"):
			totals["missing_service_booking_count"] += 1
	totals["invoice_quantity_total"] = round(totals["invoice_quantity_total"], 2)
	totals["invoice_amount_total"] = round(totals["invoice_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(SALES_INVOICE_DRAFT_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _add_check(checks, label, complete, details=None):
	checks.append({"label": label, "complete": bool(complete), "details": details or []})


def _calculate_readiness(doc):
	checks = []
	lines = doc.get("sales_invoice_draft_lines") or []
	_add_check(checks, "Invoice Draft linked", doc.get("invoice_draft"))
	_add_check(checks, "Invoice Draft approved", _is_invoice_draft_approved(doc.get("invoice_draft")))
	_add_check(checks, "ERPNext Sales Invoice DocType exists", _doctype_exists(SALES_INVOICE))
	_add_check(checks, "Participant Customer linked", doc.get("participant_customer"))
	_add_check(checks, "Company selected", doc.get("company"))
	_add_check(checks, "Posting Date entered", doc.get("posting_date"))
	_add_check(checks, "Due Date entered", doc.get("due_date"))
	_add_check(checks, "Sales Invoice Owner assigned", doc.get("sales_invoice_owner"))
	_add_check(checks, "At least one Sales Invoice draft line exists", lines)

	field_checks = [
		("All lines have ERPNext Item Code", "erp_item_code"),
		("All lines have income account", "income_account"),
		("All lines have invoice date", "invoice_date"),
		("All lines have invoice quantity", "invoice_quantity"),
		("All lines have invoice rate", "invoice_rate"),
		("All lines have invoice amount", "invoice_amount"),
		("All lines have support item", "support_item"),
		("All lines have service booking", "service_booking"),
		("All lines have plan budget", "plan_budget"),
	]
	for label, fieldname in field_checks:
		missing = [row.service_line for row in lines if not row.get(fieldname)]
		_add_check(checks, label, not missing, missing)

	if doc.get("enable_ndis_finance_invoice_controls"):
		for label, fieldname in [
			("NDIS Finance funding source mapping complete", "funding_source"),
			("NDIS Finance service type mapping complete", "finance_service_type"),
		]:
			missing = [row.service_line for row in lines if not row.get(fieldname)]
			_add_check(checks, label, not missing, missing)

	source_not_ready = [row.service_line for row in lines if not row.get("billing_preparation_ready")]
	_add_check(checks, "Billing preparation-ready flags are complete", not source_not_ready, source_not_ready)

	holds = []
	for row in lines:
		if row.get("billing_hold"):
			holds.append(f"{row.service_line}: billing")
		if row.get("sales_invoice_draft_creation_hold"):
			holds.append(f"{row.service_line}: sales invoice draft")
	_add_check(checks, "No Sales Invoice draft holds remain", not holds, holds)

	missing_line_ready = [row.service_line for row in lines if not row.get("line_ready_for_draft_sales_invoice_creation")]
	_add_check(
		checks,
		"All lines marked ready for Draft Sales Invoice creation",
		not missing_line_ready,
		missing_line_ready,
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
		"sales_invoice_draft_run_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(SALES_INVOICE_DRAFT_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(SALES_INVOICE_DRAFT_RUN, "sales_invoice_draft_run_ready"):
		doc.sales_invoice_draft_run_ready = 1 if summary["sales_invoice_draft_run_ready"] else 0
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
		(INTAKE, doc.get("participant_intake")),
	]
	for doctype, name in targets:
		_db_set_if_field(doctype, name, "ndis_sales_invoice_draft_run", doc.name)
		_db_set_if_field(doctype, name, "sales_invoice_draft_run_status", doc.status)
		_db_set_if_field(
			doctype,
			name,
			"sales_invoice_draft_run_ready",
			1 if summary["sales_invoice_draft_run_ready"] else 0,
		)
	return {"readiness": summary, "totals": totals}


def _get_default_company():
	return frappe.defaults.get_user_default("Company") or frappe.db.get_single_value("Global Defaults", "default_company")


def _build_item_description(line):
	parts = []
	for fieldname in ["service_code", "service_model"]:
		if line.get(fieldname):
			parts.append(str(line.get(fieldname)))
	if line.get("billable_date"):
		parts.append(f"Date: {line.get('billable_date')}")
	if line.get("progress_note"):
		parts.append(str(line.get("progress_note"))[:250])
	return " | ".join(parts) or line.get("erp_item_code") or line.get("support_item") or "NDIS Service"


@frappe.whitelist()
def create_sales_invoice_draft_run_from_invoice_draft(invoice_draft):
	_check_role()
	if not invoice_draft:
		frappe.throw(_("NDIS CRM Invoice Draft is required."))
	if not frappe.db.exists(INVOICE_DRAFT, invoice_draft):
		frappe.throw(_("NDIS CRM Invoice Draft {0} was not found.").format(invoice_draft))
	existing = _existing_run_for_invoice_draft(invoice_draft)
	if existing:
		return {
			"doctype": SALES_INVOICE_DRAFT_RUN,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Sales Invoice Draft Run returned.",
		}
	invoice_doc = frappe.get_doc(INVOICE_DRAFT, invoice_draft)
	doc = frappe.new_doc(SALES_INVOICE_DRAFT_RUN)
	doc.status = "Draft"
	doc.invoice_draft = invoice_doc.name
	for fieldname in [
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
		"invoice_owner",
		"billing_owner",
		"preparation_owner",
		"operations_owner",
		"rostering_owner",
		"service_manager",
		"clinical_owner",
		"default_cost_center",
		"default_house",
	]:
		_set_if_field(doc, fieldname, invoice_doc.get(fieldname))
	doc.participant_name = doc.get("participant_name") or doc.get("participant_customer") or invoice_doc.name
	doc.sales_invoice_owner = frappe.session.user
	doc.company = _get_default_company()
	doc.posting_date = nowdate()
	doc.due_date = add_days(nowdate(), 7)
	doc.sales_invoice_draft_creation_allowed = 0
	doc.enable_ndis_finance_invoice_controls = 1
	created_count = _generate_lines_from_invoice_draft(doc, invoice_doc)
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_draft_run_ready = 1 if summary["sales_invoice_draft_run_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": SALES_INVOICE_DRAFT_RUN,
		"name": doc.name,
		"created": True,
		"sales_invoice_draft_line_count": created_count,
		"message": "NDIS CRM Sales Invoice Draft Run created successfully.",
	}


@frappe.whitelist()
def create_sales_invoice_draft_run_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))
	existing = _existing_run_for_deal(deal)
	if existing:
		return {
			"doctype": SALES_INVOICE_DRAFT_RUN,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Sales Invoice Draft Run returned.",
		}
	invoice_draft = _get_invoice_draft_for_deal(deal)
	if not invoice_draft:
		try:
			from ndis_crm.phase17_invoice_draft import create_invoice_draft_from_crm_deal
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Invoice Draft before creating Sales Invoice Draft Run."))
		result = create_invoice_draft_from_crm_deal(deal)
		invoice_draft = result.get("name")
	return create_sales_invoice_draft_run_from_invoice_draft(invoice_draft)


@frappe.whitelist()
def generate_sales_invoice_draft_lines(sales_invoice_draft_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run)
	if not doc.get("invoice_draft"):
		frappe.throw(_("Invoice Draft is required."))
	invoice_doc = frappe.get_doc(INVOICE_DRAFT, doc.invoice_draft)
	created_count = _generate_lines_from_invoice_draft(doc, invoice_doc)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"created_count": created_count,
		"summary": summary,
		"message": f"Sales Invoice draft lines generated. Created: {created_count}.",
	}


@frappe.whitelist()
def validate_sales_invoice_draft_run_readiness(sales_invoice_draft_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Sales Invoice Draft Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_sales_invoice_draft_creation(sales_invoice_draft_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run)
	summary = _calculate_readiness(doc)
	if not summary["sales_invoice_draft_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Sales Invoice Draft Creation. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Sales Invoice Draft Creation"
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_draft_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"doctype": SALES_INVOICE_DRAFT_RUN,
		"name": doc.name,
		"message": "Sales Invoice Draft Run marked Ready for Sales Invoice Draft Creation.",
	}


@frappe.whitelist()
def approve_sales_invoice_draft_run(sales_invoice_draft_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run)
	summary = _calculate_readiness(doc)
	if not summary["sales_invoice_draft_run_ready"]:
		frappe.throw(_("Cannot approve Sales Invoice Draft Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Sales Invoice Draft Run Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_draft_run_ready = 1
	doc.sales_invoice_draft_creation_allowed = 0
	for row in doc.get("sales_invoice_draft_lines") or []:
		if row.get("sales_invoice_draft_status") in ["Draft", "Ready"]:
			row.sales_invoice_draft_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"doctype": SALES_INVOICE_DRAFT_RUN,
		"name": doc.name,
		"message": "Sales Invoice Draft Run approved. Draft Sales Invoices were not created yet.",
	}


def _group_ready_lines(doc):
	groups = {}
	for row in doc.get("sales_invoice_draft_lines") or []:
		if row.get("sales_invoice"):
			continue
		if row.get("sales_invoice_draft_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("line_ready_for_draft_sales_invoice_creation"):
			continue
		if row.get("billing_hold") or row.get("sales_invoice_draft_creation_hold"):
			continue
		key = row.get("invoice_group_key") or f"{doc.get('participant_customer')}|{row.get('invoice_date')}"
		groups.setdefault(key, []).append(row)
	return groups


def _create_sales_invoice_for_group(doc, group_key, lines):
	if not _doctype_exists(SALES_INVOICE):
		frappe.throw(_("Sales Invoice DocType is not available."))
	if not lines:
		return None
	invoice = frappe.new_doc(SALES_INVOICE)
	invoice.customer = doc.participant_customer
	invoice.company = doc.company
	invoice.posting_date = doc.posting_date
	invoice.due_date = doc.due_date
	_set_if_field(invoice, "debit_to", doc.get("receivable_account"))
	_set_if_field(invoice, "cost_center", doc.get("default_cost_center"))
	_set_if_field(invoice, "remarks", f"Created as Draft only from {doc.doctype} {doc.name}. Group: {group_key}")
	if doc.get("enable_ndis_finance_invoice_controls"):
		_set_if_field(invoice, "custom_is_ndis_invoice", 1)
		_set_if_field(invoice, "custom_ndis_participant_profile", doc.get("ndis_financial_profile"))
		_set_if_field(invoice, "custom_ndis_funding_source", lines[0].get("funding_source"))
		_set_if_field(invoice, "custom_ndis_house", doc.get("default_house"))
		_set_if_field(invoice, "custom_ndis_billing_status", "Draft")
	for line in lines:
		item = {
			"item_code": line.get("erp_item_code"),
			"qty": line.get("invoice_quantity"),
			"rate": line.get("invoice_rate"),
			"description": _build_item_description(line),
		}
		if line.get("income_account"):
			item["income_account"] = line.get("income_account")
		if line.get("cost_center") or doc.get("default_cost_center"):
			item["cost_center"] = line.get("cost_center") or doc.get("default_cost_center")
		invoice.append("items", item)
		invoice_item = invoice.items[-1]
		_set_if_field(invoice_item, "custom_ndis_participant", doc.get("participant_customer"))
		_set_if_field(invoice_item, "custom_ndis_house", line.get("default_house") or doc.get("default_house"))
		_set_if_field(invoice_item, "custom_ndis_support_item", line.get("support_item"))
		_set_if_field(invoice_item, "custom_ndis_service_type", line.get("finance_service_type"))
		_set_if_field(invoice_item, "custom_ndis_funding_source", line.get("funding_source"))
		_set_if_field(invoice_item, "custom_ndis_service_date", line.get("invoice_date"))
		_set_if_field(invoice_item, "custom_ndis_claimable", 1)
		_set_if_field(invoice_item, "custom_ndis_claim_status", "Draft")
	invoice.insert(ignore_permissions=True)
	if invoice.docstatus != 0:
		frappe.throw(_("Safety error: Sales Invoice was not created in Draft status."))
	return invoice.name


@frappe.whitelist()
def create_draft_sales_invoices(sales_invoice_draft_run):
	_check_role()
	doc = frappe.get_doc(SALES_INVOICE_DRAFT_RUN, sales_invoice_draft_run)
	if doc.status != "Sales Invoice Draft Run Approved":
		frappe.throw(_("Sales Invoice Draft Run must be approved before Draft Sales Invoices can be created."))
	if not doc.get("sales_invoice_draft_creation_allowed"):
		frappe.throw(_("Tick Sales Invoice Draft Creation Allowed before creating Draft Sales Invoices."))
	summary = _calculate_readiness(doc)
	if not summary["sales_invoice_draft_run_ready"]:
		frappe.throw(_("Cannot create Draft Sales Invoices. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	groups = _group_ready_lines(doc)
	if not groups:
		frappe.throw(_("No ready Sales Invoice draft lines found for creation."))
	created = []
	for group_key, lines in groups.items():
		sales_invoice = _create_sales_invoice_for_group(doc, group_key, lines)
		if not sales_invoice:
			continue
		created.append(sales_invoice)
		for line in lines:
			line.sales_invoice = sales_invoice
			line.sales_invoice_draft_status = "Draft Sales Invoice Created"
			line.sales_invoice_draft_creation_ready = 1
			line.sales_invoice_draft_creation_hold = 0
	doc.status = "Draft Sales Invoices Created"
	doc.sales_invoice_draft_creation_allowed = 0
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_draft_run_ready = 1 if summary["sales_invoice_draft_run_ready"] else 0
	_sync_totals(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"created_count": len(created),
		"sales_invoices": created,
		"message": f"Created {len(created)} Draft Sales Invoice(s). No invoice was submitted.",
	}


def validate_sales_invoice_draft_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.sales_invoice_draft_run_ready = 1 if summary["sales_invoice_draft_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["sales_invoice_draft_run_ready"]:
		frappe.throw(_("Cannot set Sales Invoice Draft Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Sales Invoice Draft Run Approved" and doc.get("sales_invoice_draft_creation_allowed"):
		frappe.throw(_("Sales Invoice Draft Creation Allowed can only be ticked after the run is approved."))


def on_sales_invoice_draft_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Sales Invoice Draft Run Summary Sync Failed")


def validate_crm_deal_phase18(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	run_required = doc.get("ndis_sales_invoice_draft_run_required") if _field_exists(CRM_DEAL, "ndis_sales_invoice_draft_run_required") else 0
	if not run_required:
		return
	run = doc.get("ndis_sales_invoice_draft_run") if _field_exists(CRM_DEAL, "ndis_sales_invoice_draft_run") else None
	if not run:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Sales Invoice Draft Run must be created and approved."))
	if not _is_sales_invoice_run_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Sales Invoice Draft Run must be approved."))


def validate_crm_deal_phase18_combined(doc, method=None):
	try:
		from ndis_crm.phase17_invoice_draft import validate_crm_deal_phase17_combined
		validate_crm_deal_phase17_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase16_claim_draft import validate_crm_deal_phase16_combined
			validate_crm_deal_phase16_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase18(doc, method)


def phase18_health_check():
	print("---- NDIS CRM Phase 18 Health Check ----")
	for dt in [
		SALES_INVOICE_DRAFT_LINE,
		SALES_INVOICE_DRAFT_RUN,
		INVOICE_DRAFT,
		INVOICE_DRAFT_LINE,
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
		"NDIS Service Line",
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for dt in [
		SALES_INVOICE,
		SALES_INVOICE_ITEM,
		ITEM,
		"Payment Entry",
		"Journal Entry",
		"GL Entry",
		"NDIS Claim Batch",
		"NDIS Claim Line",
		PLAN_BUDGET,
		SERVICE_BOOKING,
		NDIS_SERVICE_TYPE,
		NDIS_SUPPORT_ITEM,
		NDIS_HOUSE,
		FINANCE_PROFILE,
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in [
		"ndis_sales_invoice_draft_run_required",
		"ndis_sales_invoice_draft_run",
		"sales_invoice_draft_run_status",
		"sales_invoice_draft_run_ready",
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
		INTAKE,
	]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in [
			"ndis_sales_invoice_draft_run",
			"sales_invoice_draft_run_status",
			"sales_invoice_draft_run_ready",
		]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Sales Invoice Draft Run records:", frappe.db.count(SALES_INVOICE_DRAFT_RUN) if _doctype_exists(SALES_INVOICE_DRAFT_RUN) else 0)
	print("Sales Invoice Draft creation method creates docstatus=0 only.")
	print("Phase 18 boundary: no submit / payment / journal / GL / claim batch creation.")
	print("---- End Phase 18 Health Check ----")
