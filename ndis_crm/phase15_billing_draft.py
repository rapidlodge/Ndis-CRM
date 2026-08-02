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
DOWNSTREAM_PREPARATION_LINE = "NDIS CRM Downstream Preparation Line"
ATTENDANCE_DRAFT = "NDIS CRM Attendance Draft"

BILLING_DRAFT = "NDIS CRM Billing Draft"
BILLING_DRAFT_LINE = "NDIS CRM Billing Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Billing Review", "Billing Draft Approved"]
APPROVED_STATUSES = ["Billing Draft Approved"]
APPROVED_DOWNSTREAM_STATUSES = ["Downstream Preparation Approved"]

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
		frappe.throw(_("You do not have permission to perform this billing draft action."))


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


def _existing_billing_draft_for_downstream(downstream_preparation):
	if not _doctype_exists(BILLING_DRAFT):
		return None
	if _field_exists(DOWNSTREAM_PREPARATION, "ndis_billing_draft"):
		existing = frappe.db.get_value(DOWNSTREAM_PREPARATION, downstream_preparation, "ndis_billing_draft")
		if existing:
			return existing
	return frappe.db.get_value(BILLING_DRAFT, {"downstream_preparation": downstream_preparation}, "name")


def _existing_billing_draft_for_attendance(attendance_draft):
	if not _doctype_exists(BILLING_DRAFT):
		return None
	if _field_exists(ATTENDANCE_DRAFT, "ndis_billing_draft"):
		existing = frappe.db.get_value(ATTENDANCE_DRAFT, attendance_draft, "ndis_billing_draft")
		if existing:
			return existing
	return frappe.db.get_value(BILLING_DRAFT, {"attendance_draft": attendance_draft}, "name")


def _existing_billing_draft_for_deal(deal):
	if not _doctype_exists(BILLING_DRAFT):
		return None
	if _field_exists(CRM_DEAL, "ndis_billing_draft"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_billing_draft")
		if existing:
			return existing
	return frappe.db.get_value(BILLING_DRAFT, {"crm_deal": deal}, "name")


def _get_downstream_preparation_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_downstream_preparation"):
		downstream = frappe.db.get_value(CRM_DEAL, deal, "ndis_downstream_preparation")
		if downstream:
			return downstream
	if _doctype_exists(DOWNSTREAM_PREPARATION):
		return frappe.db.get_value(DOWNSTREAM_PREPARATION, {"crm_deal": deal}, "name")
	return None


def _is_downstream_approved(downstream_preparation):
	if not downstream_preparation or not frappe.db.exists(DOWNSTREAM_PREPARATION, downstream_preparation):
		return False
	status, ready = frappe.db.get_value(DOWNSTREAM_PREPARATION, downstream_preparation, ["status", "downstream_ready"])
	return status in APPROVED_DOWNSTREAM_STATUSES and bool(ready)


def _is_billing_draft_approved(billing_draft):
	if not billing_draft or not frappe.db.exists(BILLING_DRAFT, billing_draft):
		return False
	status, ready = frappe.db.get_value(BILLING_DRAFT, billing_draft, ["status", "billing_draft_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _preparation_line_key(row):
	return row.get("evidence_source_key") or "|".join([
		str(row.get("service_line") or ""),
		str(row.get("session_date") or ""),
		str(row.get("actual_start_time") or ""),
	])


def _append_billing_line_if_missing(draft_doc, row_data):
	existing = {
		row.preparation_source_key
		for row in draft_doc.get("billing_lines") or []
		if row.get("preparation_source_key")
	}
	key = row_data.get("preparation_source_key")
	if key and key in existing:
		return False
	draft_doc.append("billing_lines", row_data)
	return True


def _get_support_item_rate_and_gst(support_item):
	if not support_item or not _doctype_exists(NDIS_SUPPORT_ITEM):
		return {"rate": 0, "gst_treatment": None, "rate_source": "Manual Required"}
	try:
		values = frappe.db.get_value(NDIS_SUPPORT_ITEM, support_item, ["price_limit", "gst_treatment"], as_dict=True)
		if not values:
			return {"rate": 0, "gst_treatment": None, "rate_source": "Manual Required"}
		return {
			"rate": values.get("price_limit") or 0,
			"gst_treatment": values.get("gst_treatment"),
			"rate_source": "NDIS Support Item Price Limit" if values.get("price_limit") else "Manual Required",
		}
	except Exception:
		return {"rate": 0, "gst_treatment": None, "rate_source": "Manual Required"}


def _calculate_amount(quantity, rate):
	try:
		return round(float(quantity or 0) * float(rate or 0), 2)
	except Exception:
		return 0


def _billing_source_ready(row):
	return bool(
		row.get("billing_preparation_required")
		and row.get("billing_preparation_ready")
		and not row.get("billing_hold")
		and row.get("service_delivered")
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("delivered_hours")
	)


def _invoice_group_key(row):
	return "|".join([
		str(row.get("participant_customer") or ""),
		str(row.get("service_booking") or ""),
		str(row.get("support_item") or ""),
		str(row.get("session_date") or ""),
	])


def _build_billing_line_from_preparation(row):
	quantity = row.get("delivered_hours") or 0
	support_item_data = _get_support_item_rate_and_gst(row.get("support_item"))
	rate = support_item_data.get("rate") or 0
	amount = _calculate_amount(quantity, rate)
	billing_ready = 1 if _billing_source_ready(row) and amount > 0 else 0
	return {
		"preparation_source_key": _preparation_line_key(row),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"session_date": row.get("session_date"),
		"billable_date": row.get("session_date"),
		"actual_start_time": row.get("actual_start_time"),
		"actual_end_time": row.get("actual_end_time"),
		"delivered_hours": row.get("delivered_hours"),
		"billable_quantity": quantity,
		"billing_unit": "Hour",
		"billing_rate": rate,
		"billing_amount": amount,
		"rate_source": support_item_data.get("rate_source"),
		"gst_treatment": support_item_data.get("gst_treatment"),
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
		"requires_roster": row.get("requires_roster"),
		"requires_house": row.get("requires_house"),
		"requires_clinical_review": row.get("requires_clinical_review"),
		"clinical_review_complete": row.get("clinical_review_complete"),
		"transport_required": row.get("transport_required"),
		"worker_skill_requirements": row.get("worker_skill_requirements"),
		"billing_preparation_required": row.get("billing_preparation_required"),
		"billing_preparation_ready": billing_ready,
		"claim_preparation_ready": row.get("claim_preparation_ready"),
		"billing_hold": row.get("billing_hold") or (0 if billing_ready else 1),
		"claim_hold": row.get("claim_hold"),
		"invoice_group_key": _invoice_group_key(row),
		"line_ready_for_invoice_draft": 0,
		"billing_draft_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_downstream_preparation(draft_doc, downstream_doc):
	created = 0
	for row in downstream_doc.get("preparation_lines") or []:
		if row.get("preparation_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("billing_preparation_required"):
			continue
		if not row.get("line_ready_for_downstream_creation"):
			continue
		if _append_billing_line_if_missing(draft_doc, _build_billing_line_from_preparation(row)):
			created += 1
	return created


def _line_label(row):
	return row.get("service_line") or row.get("preparation_source_key") or row.idx


def _calculate_totals(doc):
	totals = {
		"billing_line_count": len(doc.get("billing_lines") or []),
		"billable_quantity_total": 0,
		"billing_amount_total": 0,
		"billing_ready_count": 0,
		"billing_approved_count": 0,
		"billing_hold_count": 0,
		"manual_rate_count": 0,
		"missing_service_booking_count": 0,
	}
	for row in doc.get("billing_lines") or []:
		for source, target in [("billable_quantity", "billable_quantity_total"), ("billing_amount", "billing_amount_total")]:
			try:
				totals[target] += float(row.get(source) or 0)
			except Exception:
				pass
		if row.get("line_ready_for_invoice_draft"):
			totals["billing_ready_count"] += 1
		if row.get("billing_draft_status") == "Approved":
			totals["billing_approved_count"] += 1
		if row.get("billing_hold"):
			totals["billing_hold_count"] += 1
		if row.get("rate_source") == "Manual Required" or not row.get("billing_rate"):
			totals["manual_rate_count"] += 1
		if not row.get("service_booking"):
			totals["missing_service_booking_count"] += 1
	totals["billable_quantity_total"] = round(totals["billable_quantity_total"], 2)
	totals["billing_amount_total"] = round(totals["billing_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(BILLING_DRAFT, fieldname):
			doc.set(fieldname, value)
	return totals


def _calculate_readiness(doc):
	lines = doc.get("billing_lines") or []
	checks = [
		{"label": "Downstream Preparation linked", "complete": bool(doc.get("downstream_preparation"))},
		{"label": "Downstream Preparation approved", "complete": _is_downstream_approved(doc.get("downstream_preparation"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Billing Owner assigned", "complete": bool(doc.get("billing_owner"))},
		{"label": "Billing Period Start entered", "complete": bool(doc.get("billing_period_start"))},
		{"label": "Billing Period End entered", "complete": bool(doc.get("billing_period_end"))},
		{"label": "At least one billing draft line exists", "complete": bool(lines)},
	]
	line_checks = [
		("All billing lines have billable date", [row for row in lines if not row.get("billable_date")]),
		("All billing lines have billable quantity", [row for row in lines if not row.get("billable_quantity")]),
		("All billing lines have billing rate", [row for row in lines if not row.get("billing_rate")]),
		("All billing lines have billing amount", [row for row in lines if not row.get("billing_amount")]),
		("All billing lines have support item", [row for row in lines if not row.get("support_item")]),
		("All billing lines have service booking", [row for row in lines if not row.get("service_booking")]),
		("All billing lines have plan budget", [row for row in lines if not row.get("plan_budget")]),
		("All billing lines have invoice group key", [row for row in lines if not row.get("invoice_group_key")]),
		("Billing preparation-ready flags are complete", [row for row in lines if row.get("billing_preparation_required") and not row.get("billing_preparation_ready")]),
		("No billing hold remains", [row for row in lines if row.get("billing_hold")]),
		("All billing lines marked ready for invoice draft", [row for row in lines if not row.get("line_ready_for_invoice_draft")]),
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
		"billing_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(BILLING_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(BILLING_DRAFT, "billing_draft_ready"):
		doc.billing_draft_ready = 1 if summary["billing_ready"] else 0

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
		(INTAKE, doc.get("participant_intake")),
	]:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_billing_draft", doc.name)
		_db_set_if_field(doctype, name, "billing_draft_status", doc.status)
		_db_set_if_field(doctype, name, "billing_draft_ready", 1 if summary["billing_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_billing_draft_from_downstream_preparation(downstream_preparation):
	_check_role()
	if not downstream_preparation:
		frappe.throw(_("NDIS CRM Downstream Preparation is required."))
	if not frappe.db.exists(DOWNSTREAM_PREPARATION, downstream_preparation):
		frappe.throw(_("NDIS CRM Downstream Preparation {0} was not found.").format(downstream_preparation))

	existing = _existing_billing_draft_for_downstream(downstream_preparation)
	if existing:
		return {"doctype": BILLING_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Billing Draft returned."}

	downstream_doc = frappe.get_doc(DOWNSTREAM_PREPARATION, downstream_preparation)
	doc = frappe.new_doc(BILLING_DRAFT)
	doc.status = "Draft"
	doc.downstream_preparation = downstream_doc.name
	if _doctype_exists(ATTENDANCE_DRAFT):
		attendance_draft = frappe.db.get_value(ATTENDANCE_DRAFT, {"downstream_preparation": downstream_doc.name}, "name")
		if attendance_draft:
			doc.attendance_draft = attendance_draft
	for target, source in [
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
		("preparation_owner", "preparation_owner"),
		("operations_owner", "operations_owner"),
		("rostering_owner", "rostering_owner"),
		("service_manager", "service_manager"),
		("clinical_owner", "clinical_owner"),
	]:
		doc.set(target, downstream_doc.get(source))
	doc.participant_name = downstream_doc.get("participant_name") or downstream_doc.get("participant_customer") or downstream_doc.name
	doc.billing_period_start = downstream_doc.get("preparation_period_start")
	doc.billing_period_end = downstream_doc.get("preparation_period_end")
	doc.billing_owner = frappe.session.user
	doc.invoice_creation_allowed = 0
	_set_if_field(doc, "default_house", downstream_doc.get("default_house"))
	_set_if_field(doc, "default_cost_center", downstream_doc.get("default_cost_center"))

	created_count = _generate_lines_from_downstream_preparation(doc, downstream_doc)
	if _field_exists(BILLING_DRAFT, "billing_line_count"):
		doc.billing_line_count = created_count
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.billing_draft_ready = 1 if summary["billing_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": BILLING_DRAFT,
		"name": doc.name,
		"created": True,
		"billing_line_count": created_count,
		"message": "NDIS CRM Billing Draft created successfully.",
	}


@frappe.whitelist()
def create_billing_draft_from_attendance_draft(attendance_draft):
	_check_role()
	if not attendance_draft:
		frappe.throw(_("NDIS CRM Attendance Draft is required."))
	if not frappe.db.exists(ATTENDANCE_DRAFT, attendance_draft):
		frappe.throw(_("NDIS CRM Attendance Draft {0} was not found.").format(attendance_draft))

	existing = _existing_billing_draft_for_attendance(attendance_draft)
	if existing:
		return {"doctype": BILLING_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Billing Draft returned."}

	downstream_preparation = frappe.db.get_value(ATTENDANCE_DRAFT, attendance_draft, "downstream_preparation")
	if not downstream_preparation:
		frappe.throw(_("Attendance Draft must be linked to Downstream Preparation."))
	result = create_billing_draft_from_downstream_preparation(downstream_preparation)
	if result.get("name"):
		_db_set_if_field(BILLING_DRAFT, result.get("name"), "attendance_draft", attendance_draft)
		_db_set_if_field(ATTENDANCE_DRAFT, attendance_draft, "ndis_billing_draft", result.get("name"))
	return result


@frappe.whitelist()
def create_billing_draft_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_billing_draft_for_deal(deal)
	if existing:
		return {"doctype": BILLING_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Billing Draft returned."}

	downstream = _get_downstream_preparation_for_deal(deal)
	if not downstream:
		try:
			from ndis_crm.phase13_downstream_preparation import create_downstream_preparation_from_crm_deal
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Downstream Preparation before creating Billing Draft."))
		result = create_downstream_preparation_from_crm_deal(deal)
		downstream = result.get("name")
	return create_billing_draft_from_downstream_preparation(downstream)


@frappe.whitelist()
def generate_billing_lines(billing_draft):
	_check_role()
	doc = frappe.get_doc(BILLING_DRAFT, billing_draft)
	if not doc.get("downstream_preparation"):
		frappe.throw(_("Downstream Preparation is required."))
	downstream_doc = frappe.get_doc(DOWNSTREAM_PREPARATION, doc.downstream_preparation)
	created_count = _generate_lines_from_downstream_preparation(doc, downstream_doc)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Billing lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_billing_draft_readiness(billing_draft):
	_check_role()
	doc = frappe.get_doc(BILLING_DRAFT, billing_draft)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Billing draft readiness validated."}


@frappe.whitelist()
def mark_ready_for_billing_review(billing_draft):
	_check_role()
	doc = frappe.get_doc(BILLING_DRAFT, billing_draft)
	summary = _calculate_readiness(doc)
	if not summary["billing_ready"]:
		frappe.throw(_("Cannot mark Ready for Billing Review. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Billing Review"
	doc.readiness_percent = summary["readiness_percent"]
	doc.billing_draft_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": BILLING_DRAFT, "name": doc.name, "message": "Billing Draft marked Ready for Billing Review."}


@frappe.whitelist()
def approve_billing_draft(billing_draft):
	_check_role()
	doc = frappe.get_doc(BILLING_DRAFT, billing_draft)
	summary = _calculate_readiness(doc)
	if not summary["billing_ready"]:
		frappe.throw(_("Cannot approve Billing Draft. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Billing Draft Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.billing_draft_ready = 1
	doc.invoice_creation_allowed = 0
	for row in doc.get("billing_lines") or []:
		if row.get("billing_draft_status") in ["Draft", "Ready"]:
			row.billing_draft_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": BILLING_DRAFT, "name": doc.name, "message": "Billing Draft approved. No Sales Invoice was created."}


def validate_billing_draft(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(BILLING_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(BILLING_DRAFT, "billing_draft_ready"):
		doc.billing_draft_ready = 1 if summary["billing_ready"] else 0
	if doc.status in READY_STATUSES and not summary["billing_ready"]:
		frappe.throw(_("Cannot set Billing Draft to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.get("invoice_creation_allowed"):
		frappe.throw(_("Invoice creation is not allowed in Phase 15. This phase is billing draft only."))


def on_billing_draft_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Billing Draft Summary Sync Failed")


def validate_crm_deal_phase15(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	billing_required = doc.get("ndis_billing_draft_required") if _field_exists(CRM_DEAL, "ndis_billing_draft_required") else 0
	if not billing_required:
		return
	billing_draft = doc.get("ndis_billing_draft") if _field_exists(CRM_DEAL, "ndis_billing_draft") else None
	if not billing_draft:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Billing Draft must be created and approved."))
	if not _is_billing_draft_approved(billing_draft):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Billing Draft must be approved."))


def validate_crm_deal_phase15_combined(doc, method=None):
	"""Preserve Phase 2-14 validator chain, then add optional Phase 15 validation."""
	try:
		from ndis_crm.phase14_attendance_draft import validate_crm_deal_phase14_combined

		validate_crm_deal_phase14_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase13_downstream_preparation import validate_crm_deal_phase13_combined

			validate_crm_deal_phase13_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase15(doc, method)


def phase15_health_check():
	print("---- NDIS CRM Phase 15 Health Check ----")
	for dt in [
		BILLING_DRAFT_LINE,
		BILLING_DRAFT,
		ATTENDANCE_DRAFT,
		DOWNSTREAM_PREPARATION,
		DOWNSTREAM_PREPARATION_LINE,
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
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'MISSING'}")
	for dt in ["Sales Invoice", "Sales Invoice Item", "Payment Entry", "Journal Entry", "GL Entry", PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in ["ndis_billing_draft_required", "ndis_billing_draft", "billing_draft_status", "billing_draft_ready"]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")
	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, SESSION_DRAFT, EVIDENCE_REVIEW, DOWNSTREAM_PREPARATION, ATTENDANCE_DRAFT, INTAKE]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_billing_draft", "billing_draft_status", "billing_draft_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Billing Draft records:", frappe.db.count(BILLING_DRAFT) if _doctype_exists(BILLING_DRAFT) else 0)
	print("CRM Deal Phase 15 combined validator should be active through hooks.py.")
	print("Phase 15 boundary: billing draft only. No Sales Invoice / Claim / Accounting creation.")
	print("---- End Phase 15 Health Check ----")
