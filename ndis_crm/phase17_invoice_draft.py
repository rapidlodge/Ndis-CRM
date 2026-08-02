import frappe
from frappe import _


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
BILLING_DRAFT_LINE = "NDIS CRM Billing Draft Line"
CLAIM_DRAFT = "NDIS CRM Claim Draft"

INVOICE_DRAFT = "NDIS CRM Invoice Draft"
INVOICE_DRAFT_LINE = "NDIS CRM Invoice Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Invoice Review", "Invoice Draft Approved"]
APPROVED_STATUSES = ["Invoice Draft Approved"]
APPROVED_BILLING_STATUSES = ["Billing Draft Approved"]

ALLOWED_ROLES = {
	"System Manager",
	"Sales Manager",
	"Sales User",
	"NDIS CRM Manager",
	"NDIS Intake Officer",
	"NDIS Service Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this invoice draft action."))


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


def _existing_invoice_draft_for_billing(billing_draft):
	if not _doctype_exists(INVOICE_DRAFT):
		return None
	if _field_exists(BILLING_DRAFT, "ndis_invoice_draft"):
		existing = frappe.db.get_value(BILLING_DRAFT, billing_draft, "ndis_invoice_draft")
		if existing:
			return existing
	return frappe.db.get_value(INVOICE_DRAFT, {"billing_draft": billing_draft}, "name")


def _existing_invoice_draft_for_claim(claim_draft):
	if not _doctype_exists(INVOICE_DRAFT) or not _doctype_exists(CLAIM_DRAFT):
		return None
	if _field_exists(CLAIM_DRAFT, "ndis_invoice_draft"):
		existing = frappe.db.get_value(CLAIM_DRAFT, claim_draft, "ndis_invoice_draft")
		if existing:
			return existing
	return frappe.db.get_value(INVOICE_DRAFT, {"claim_draft": claim_draft}, "name")


def _existing_invoice_draft_for_deal(deal):
	if not _doctype_exists(INVOICE_DRAFT):
		return None
	if _field_exists(CRM_DEAL, "ndis_invoice_draft"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_invoice_draft")
		if existing:
			return existing
	return frappe.db.get_value(INVOICE_DRAFT, {"crm_deal": deal}, "name")


def _get_billing_draft_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_billing_draft"):
		billing = frappe.db.get_value(CRM_DEAL, deal, "ndis_billing_draft")
		if billing:
			return billing
	if _doctype_exists(BILLING_DRAFT):
		return frappe.db.get_value(BILLING_DRAFT, {"crm_deal": deal}, "name")
	return None


def _get_claim_draft_for_billing(billing_draft):
	if not _doctype_exists(CLAIM_DRAFT):
		return None
	if _field_exists(BILLING_DRAFT, "ndis_claim_draft"):
		claim = frappe.db.get_value(BILLING_DRAFT, billing_draft, "ndis_claim_draft")
		if claim:
			return claim
	return frappe.db.get_value(CLAIM_DRAFT, {"billing_draft": billing_draft}, "name")


def _is_billing_approved(billing_draft):
	if not billing_draft or not frappe.db.exists(BILLING_DRAFT, billing_draft):
		return False
	status, ready = frappe.db.get_value(BILLING_DRAFT, billing_draft, ["status", "billing_draft_ready"])
	return status in APPROVED_BILLING_STATUSES and bool(ready)


def _is_invoice_draft_approved(invoice_draft):
	if not invoice_draft or not frappe.db.exists(INVOICE_DRAFT, invoice_draft):
		return False
	status, ready = frappe.db.get_value(INVOICE_DRAFT, invoice_draft, ["status", "invoice_draft_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _billing_line_key(row):
	return row.get("preparation_source_key") or "|".join([
		str(row.get("service_line") or ""),
		str(row.get("billable_date") or ""),
		str(row.get("support_item") or ""),
		str(row.get("service_booking") or ""),
	])


def _append_invoice_line_if_missing(draft_doc, row_data):
	existing = {
		row.billing_source_key
		for row in draft_doc.get("invoice_lines") or []
		if row.get("billing_source_key")
	}
	key = row_data.get("billing_source_key")
	if key and key in existing:
		return False
	draft_doc.append("invoice_lines", row_data)
	return True


def _calculate_amount(quantity, rate):
	try:
		return round(float(quantity or 0) * float(rate or 0), 2)
	except Exception:
		return 0


def _invoice_source_ready(row):
	return bool(
		row.get("line_ready_for_invoice_draft")
		and row.get("billing_draft_status") in ["Approved", "Ready"]
		and row.get("billing_preparation_ready")
		and not row.get("billing_hold")
		and row.get("participant_attended")
		and row.get("service_delivered")
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("plan_budget")
		and row.get("billable_date")
		and row.get("billable_quantity")
		and row.get("billing_rate")
		and row.get("billing_amount")
	)


def _build_invoice_line_from_billing(row):
	quantity = row.get("billable_quantity") or 0
	rate = row.get("billing_rate") or 0
	amount = row.get("billing_amount") or _calculate_amount(quantity, rate)
	source_ready = 1 if _invoice_source_ready(row) else 0
	return {
		"billing_source_key": _billing_line_key(row),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"invoice_group_key": row.get("invoice_group_key"),
		"proposed_invoice_reference": row.get("proposed_invoice_reference"),
		"invoice_date": row.get("billable_date"),
		"billable_date": row.get("billable_date"),
		"session_date": row.get("session_date"),
		"actual_start_time": row.get("actual_start_time"),
		"actual_end_time": row.get("actual_end_time"),
		"delivered_hours": row.get("delivered_hours"),
		"invoice_quantity": quantity,
		"invoice_unit": row.get("billing_unit") or "Hour",
		"invoice_rate": rate,
		"invoice_amount": amount,
		"gst_treatment": row.get("gst_treatment"),
		"rate_source": row.get("rate_source"),
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
		"default_house": row.get("default_house"),
		"delivery_location": row.get("delivery_location"),
		"billing_preparation_required": row.get("billing_preparation_required"),
		"billing_preparation_ready": source_ready,
		"claim_preparation_ready": row.get("claim_preparation_ready"),
		"billing_hold": row.get("billing_hold") or (0 if source_ready else 1),
		"billing_hold_reason": None if source_ready else "Invoice source not fully ready.",
		"sales_invoice_creation_ready": 0,
		"sales_invoice_creation_hold": 1,
		"sales_invoice_reference": None,
		"line_ready_for_sales_invoice_creation": 0,
		"invoice_draft_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_billing_draft(draft_doc, billing_doc):
	created = 0
	for row in billing_doc.get("billing_lines") or []:
		if row.get("billing_draft_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("line_ready_for_invoice_draft"):
			continue
		if _append_invoice_line_if_missing(draft_doc, _build_invoice_line_from_billing(row)):
			created += 1
	return created


def _line_label(row):
	return row.get("service_line") or row.get("billing_source_key") or row.idx


def _calculate_totals(doc):
	totals = {
		"invoice_line_count": len(doc.get("invoice_lines") or []),
		"invoice_quantity_total": 0,
		"invoice_amount_total": 0,
		"invoice_ready_count": 0,
		"invoice_approved_count": 0,
		"invoice_hold_count": 0,
		"missing_customer_count": 0,
		"missing_support_item_count": 0,
		"missing_service_booking_count": 0,
	}
	for row in doc.get("invoice_lines") or []:
		for source, target in [("invoice_quantity", "invoice_quantity_total"), ("invoice_amount", "invoice_amount_total")]:
			try:
				totals[target] += float(row.get(source) or 0)
			except Exception:
				pass
		if row.get("line_ready_for_sales_invoice_creation"):
			totals["invoice_ready_count"] += 1
		if row.get("invoice_draft_status") == "Approved":
			totals["invoice_approved_count"] += 1
		if row.get("billing_hold") or row.get("sales_invoice_creation_hold"):
			totals["invoice_hold_count"] += 1
		if not doc.get("participant_customer"):
			totals["missing_customer_count"] += 1
		if not row.get("support_item"):
			totals["missing_support_item_count"] += 1
		if not row.get("service_booking"):
			totals["missing_service_booking_count"] += 1
	totals["invoice_quantity_total"] = round(totals["invoice_quantity_total"], 2)
	totals["invoice_amount_total"] = round(totals["invoice_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(INVOICE_DRAFT, fieldname):
			doc.set(fieldname, value)
	return totals


def _calculate_readiness(doc):
	lines = doc.get("invoice_lines") or []
	checks = [
		{"label": "Billing Draft linked", "complete": bool(doc.get("billing_draft"))},
		{"label": "Billing Draft approved", "complete": _is_billing_approved(doc.get("billing_draft"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Invoice Owner assigned", "complete": bool(doc.get("invoice_owner"))},
		{"label": "Invoice Period Start entered", "complete": bool(doc.get("invoice_period_start"))},
		{"label": "Invoice Period End entered", "complete": bool(doc.get("invoice_period_end"))},
		{"label": "At least one invoice draft line exists", "complete": bool(lines)},
	]
	line_checks = [
		("All invoice lines have invoice date", [row for row in lines if not row.get("invoice_date")]),
		("All invoice lines have invoice quantity", [row for row in lines if not row.get("invoice_quantity")]),
		("All invoice lines have invoice rate", [row for row in lines if not row.get("invoice_rate")]),
		("All invoice lines have invoice amount", [row for row in lines if not row.get("invoice_amount")]),
		("All invoice lines have support item", [row for row in lines if not row.get("support_item")]),
		("All invoice lines have service booking", [row for row in lines if not row.get("service_booking")]),
		("All invoice lines have plan budget", [row for row in lines if not row.get("plan_budget")]),
		("All invoice lines have invoice group key", [row for row in lines if not row.get("invoice_group_key")]),
		("Billing preparation-ready flags are complete", [row for row in lines if not row.get("billing_preparation_ready")]),
		("No billing hold remains", [row for row in lines if row.get("billing_hold")]),
		("No Sales Invoice creation review hold remains", [row for row in lines if row.get("sales_invoice_creation_hold")]),
		("All invoice lines marked ready for Sales Invoice creation review", [row for row in lines if not row.get("line_ready_for_sales_invoice_creation")]),
	]
	for label, missing in line_checks:
		checks.append({"label": label, "complete": not missing, "details": [_line_label(row) for row in missing]})

	total = len(checks)
	complete = len([row for row in checks if row["complete"]])
	incomplete = []
	for row in checks:
		if row["complete"]:
			continue
		label = row["label"]
		if row.get("details"):
			label += ": " + ", ".join([str(value) for value in row["details"] if value])
		incomplete.append(label)
	return {
		"total_checks": total,
		"complete_checks": complete,
		"readiness_percent": round((complete / total) * 100, 2) if total else 0,
		"invoice_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(INVOICE_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(INVOICE_DRAFT, "invoice_draft_ready"):
		doc.invoice_draft_ready = 1 if summary["invoice_ready"] else 0

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
		(INTAKE, doc.get("participant_intake")),
	]:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_invoice_draft", doc.name)
		_db_set_if_field(doctype, name, "invoice_draft_status", doc.status)
		_db_set_if_field(doctype, name, "invoice_draft_ready", 1 if summary["invoice_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_invoice_draft_from_billing_draft(billing_draft):
	_check_role()
	if not billing_draft:
		frappe.throw(_("NDIS CRM Billing Draft is required."))
	if not frappe.db.exists(BILLING_DRAFT, billing_draft):
		frappe.throw(_("NDIS CRM Billing Draft {0} was not found.").format(billing_draft))

	existing = _existing_invoice_draft_for_billing(billing_draft)
	if existing:
		return {"doctype": INVOICE_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Invoice Draft returned."}

	billing_doc = frappe.get_doc(BILLING_DRAFT, billing_draft)
	doc = frappe.new_doc(INVOICE_DRAFT)
	doc.status = "Draft"
	for target, source in [
		("billing_draft", "name"),
		("attendance_draft", "attendance_draft"),
		("downstream_preparation", "downstream_preparation"),
		("delivery_evidence_review", "delivery_evidence_review"),
		("service_session_draft", "service_session_draft"),
		("participant_service_file", "participant_service_file"),
		("roster_build_request", "roster_build_request"),
		("service_schedule_draft", "service_schedule_draft"),
		("operations_setup", "operations_setup"),
		("finance_onboarding", "finance_onboarding"),
		("handover", "handover"),
		("crm_deal", "crm_deal"),
		("crm_lead", "crm_lead"),
		("participant_intake", "participant_intake"),
		("participant_customer", "participant_customer"),
		("ndis_financial_profile", "ndis_financial_profile"),
		("ndis_number", "ndis_number"),
		("plan_start_date", "plan_start_date"),
		("plan_end_date", "plan_end_date"),
		("billing_owner", "billing_owner"),
		("preparation_owner", "preparation_owner"),
		("operations_owner", "operations_owner"),
		("rostering_owner", "rostering_owner"),
		("service_manager", "service_manager"),
		("clinical_owner", "clinical_owner"),
	]:
		doc.set(target, billing_doc.get(source))
	doc.claim_draft = _get_claim_draft_for_billing(billing_doc.name)
	doc.participant_name = billing_doc.get("participant_name") or billing_doc.get("participant_customer") or billing_doc.name
	doc.invoice_period_start = billing_doc.get("billing_period_start")
	doc.invoice_period_end = billing_doc.get("billing_period_end")
	doc.invoice_owner = frappe.session.user
	doc.sales_invoice_creation_allowed = 0
	_set_if_field(doc, "default_house", billing_doc.get("default_house"))
	_set_if_field(doc, "default_cost_center", billing_doc.get("default_cost_center"))

	created_count = _generate_lines_from_billing_draft(doc, billing_doc)
	if _field_exists(INVOICE_DRAFT, "invoice_line_count"):
		doc.invoice_line_count = created_count
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.invoice_draft_ready = 1 if summary["invoice_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": INVOICE_DRAFT,
		"name": doc.name,
		"created": True,
		"invoice_line_count": created_count,
		"message": "NDIS CRM Invoice Draft created successfully.",
	}


@frappe.whitelist()
def create_invoice_draft_from_claim_draft(claim_draft):
	_check_role()
	if not claim_draft:
		frappe.throw(_("NDIS CRM Claim Draft is required."))
	if not _doctype_exists(CLAIM_DRAFT) or not frappe.db.exists(CLAIM_DRAFT, claim_draft):
		frappe.throw(_("NDIS CRM Claim Draft {0} was not found.").format(claim_draft))

	existing = _existing_invoice_draft_for_claim(claim_draft)
	if existing:
		return {"doctype": INVOICE_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Invoice Draft returned."}
	billing_draft = frappe.db.get_value(CLAIM_DRAFT, claim_draft, "billing_draft")
	if not billing_draft:
		frappe.throw(_("Claim Draft must be linked to Billing Draft."))
	result = create_invoice_draft_from_billing_draft(billing_draft)
	if result.get("name"):
		_db_set_if_field(INVOICE_DRAFT, result.get("name"), "claim_draft", claim_draft)
		_db_set_if_field(CLAIM_DRAFT, claim_draft, "ndis_invoice_draft", result.get("name"))
	return result


@frappe.whitelist()
def create_invoice_draft_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_invoice_draft_for_deal(deal)
	if existing:
		return {"doctype": INVOICE_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Invoice Draft returned."}
	billing_draft = _get_billing_draft_for_deal(deal)
	if not billing_draft:
		try:
			from ndis_crm.phase15_billing_draft import create_billing_draft_from_crm_deal
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Billing Draft before creating Invoice Draft."))
		result = create_billing_draft_from_crm_deal(deal)
		billing_draft = result.get("name")
	return create_invoice_draft_from_billing_draft(billing_draft)


@frappe.whitelist()
def generate_invoice_lines(invoice_draft):
	_check_role()
	doc = frappe.get_doc(INVOICE_DRAFT, invoice_draft)
	if not doc.get("billing_draft"):
		frappe.throw(_("Billing Draft is required."))
	billing_doc = frappe.get_doc(BILLING_DRAFT, doc.billing_draft)
	created_count = _generate_lines_from_billing_draft(doc, billing_doc)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Invoice lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_invoice_draft_readiness(invoice_draft):
	_check_role()
	doc = frappe.get_doc(INVOICE_DRAFT, invoice_draft)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Invoice draft readiness validated."}


@frappe.whitelist()
def mark_ready_for_invoice_review(invoice_draft):
	_check_role()
	doc = frappe.get_doc(INVOICE_DRAFT, invoice_draft)
	summary = _calculate_readiness(doc)
	if not summary["invoice_ready"]:
		frappe.throw(_("Cannot mark Ready for Invoice Review. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Invoice Review"
	doc.readiness_percent = summary["readiness_percent"]
	doc.invoice_draft_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": INVOICE_DRAFT, "name": doc.name, "message": "Invoice Draft marked Ready for Invoice Review."}


@frappe.whitelist()
def approve_invoice_draft(invoice_draft):
	_check_role()
	doc = frappe.get_doc(INVOICE_DRAFT, invoice_draft)
	summary = _calculate_readiness(doc)
	if not summary["invoice_ready"]:
		frappe.throw(_("Cannot approve Invoice Draft. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Invoice Draft Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.invoice_draft_ready = 1
	doc.sales_invoice_creation_allowed = 0
	for row in doc.get("invoice_lines") or []:
		if row.get("invoice_draft_status") in ["Draft", "Ready"]:
			row.invoice_draft_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": INVOICE_DRAFT, "name": doc.name, "message": "Invoice Draft approved. No Sales Invoice was created."}


def validate_invoice_draft(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(INVOICE_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(INVOICE_DRAFT, "invoice_draft_ready"):
		doc.invoice_draft_ready = 1 if summary["invoice_ready"] else 0
	if doc.status in READY_STATUSES and not summary["invoice_ready"]:
		frappe.throw(_("Cannot set Invoice Draft to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.get("sales_invoice_creation_allowed"):
		frappe.throw(_("Sales Invoice creation is not allowed in Phase 17. This phase is invoice draft only."))


def on_invoice_draft_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Invoice Draft Summary Sync Failed")


def validate_crm_deal_phase17(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	invoice_required = doc.get("ndis_invoice_draft_required") if _field_exists(CRM_DEAL, "ndis_invoice_draft_required") else 0
	if not invoice_required:
		return
	invoice_draft = doc.get("ndis_invoice_draft") if _field_exists(CRM_DEAL, "ndis_invoice_draft") else None
	if not invoice_draft:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Invoice Draft must be created and approved."))
	if not _is_invoice_draft_approved(invoice_draft):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Invoice Draft must be approved."))


def validate_crm_deal_phase17_combined(doc, method=None):
	"""Preserve Phase 2-16 validator chain, then add optional Phase 17 validation."""
	try:
		from ndis_crm.phase16_claim_draft import validate_crm_deal_phase16_combined

		validate_crm_deal_phase16_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase15_billing_draft import validate_crm_deal_phase15_combined

			validate_crm_deal_phase15_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase17(doc, method)


def phase17_health_check():
	print("---- NDIS CRM Phase 17 Health Check ----")
	for dt in [
		INVOICE_DRAFT_LINE,
		INVOICE_DRAFT,
		CLAIM_DRAFT,
		BILLING_DRAFT,
		BILLING_DRAFT_LINE,
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
		"Sales Invoice",
		"Sales Invoice Item",
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
	for field in ["ndis_invoice_draft_required", "ndis_invoice_draft", "invoice_draft_status", "invoice_draft_ready"]:
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
		INTAKE,
	]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_invoice_draft", "invoice_draft_status", "invoice_draft_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Invoice Draft records:", frappe.db.count(INVOICE_DRAFT) if _doctype_exists(INVOICE_DRAFT) else 0)
	print("CRM Deal Phase 17 combined validator should be active through hooks.py.")
	print("Phase 17 boundary: invoice draft only. No Sales Invoice / Payment / Journal / GL / Accounting creation.")
	print("---- End Phase 17 Health Check ----")
