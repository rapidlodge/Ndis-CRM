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
ATTENDANCE_DRAFT_LINE = "NDIS CRM Attendance Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Attendance Creation", "Attendance Draft Approved"]
APPROVED_STATUSES = ["Attendance Draft Approved"]
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
		frappe.throw(_("You do not have permission to perform this attendance draft action."))


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


def _existing_attendance_draft_for_downstream(downstream_preparation):
	if not _doctype_exists(ATTENDANCE_DRAFT):
		return None
	if _field_exists(DOWNSTREAM_PREPARATION, "ndis_attendance_draft"):
		existing = frappe.db.get_value(DOWNSTREAM_PREPARATION, downstream_preparation, "ndis_attendance_draft")
		if existing:
			return existing
	return frappe.db.get_value(ATTENDANCE_DRAFT, {"downstream_preparation": downstream_preparation}, "name")


def _existing_attendance_draft_for_deal(deal):
	if not _doctype_exists(ATTENDANCE_DRAFT):
		return None
	if _field_exists(CRM_DEAL, "ndis_attendance_draft"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_attendance_draft")
		if existing:
			return existing
	return frappe.db.get_value(ATTENDANCE_DRAFT, {"crm_deal": deal}, "name")


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


def _is_attendance_draft_approved(attendance_draft):
	if not attendance_draft or not frappe.db.exists(ATTENDANCE_DRAFT, attendance_draft):
		return False
	status, ready = frappe.db.get_value(ATTENDANCE_DRAFT, attendance_draft, ["status", "attendance_draft_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _preparation_line_key(row):
	return row.get("evidence_source_key") or "|".join([
		str(row.get("service_line") or ""),
		str(row.get("session_date") or ""),
		str(row.get("actual_start_time") or ""),
	])


def _worker_reference_exists(row):
	return bool(row.get("support_worker_user") or row.get("support_worker_employee") or row.get("support_worker_name"))


def _append_attendance_line_if_missing(draft_doc, row_data):
	existing = {
		row.preparation_source_key
		for row in draft_doc.get("attendance_lines") or []
		if row.get("preparation_source_key")
	}
	key = row_data.get("preparation_source_key")
	if key and key in existing:
		return False
	draft_doc.append("attendance_lines", row_data)
	return True


def _build_attendance_line_from_preparation(row):
	worker_reference_ready = 1 if _worker_reference_exists(row) else 0
	employee_mapping_ready = 1 if row.get("support_worker_employee") else 0
	service_delivered = 1 if row.get("service_delivered") else 0
	return {
		"preparation_source_key": _preparation_line_key(row),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"session_date": row.get("session_date"),
		"attendance_date": row.get("session_date"),
		"actual_start_time": row.get("actual_start_time"),
		"actual_end_time": row.get("actual_end_time"),
		"attendance_hours": row.get("delivered_hours"),
		"delivered_hours": row.get("delivered_hours"),
		"workers_required": row.get("workers_required"),
		"estimated_worker_hours": row.get("estimated_worker_hours"),
		"support_worker_user": row.get("support_worker_user"),
		"support_worker_employee": row.get("support_worker_employee"),
		"support_worker_name": row.get("support_worker_name"),
		"worker_reference_ready": worker_reference_ready,
		"employee_mapping_ready": employee_mapping_ready,
		"participant_attended": 1 if row.get("participant_attended") else 0,
		"non_attendance_reason": row.get("non_attendance_reason"),
		"service_delivered": service_delivered,
		"proposed_attendance_status": "Present" if service_delivered else "Absent",
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
		"attendance_preparation_ready": row.get("attendance_preparation_ready"),
		"attendance_hold": row.get("attendance_hold"),
		"billing_preparation_ready": row.get("billing_preparation_ready"),
		"payroll_preparation_ready": row.get("payroll_preparation_ready"),
		"claim_preparation_ready": row.get("claim_preparation_ready"),
		"line_ready_for_attendance_creation": 0,
		"attendance_draft_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_downstream_preparation(draft_doc, downstream_doc):
	created = 0
	for row in downstream_doc.get("preparation_lines") or []:
		if row.get("preparation_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("attendance_preparation_required"):
			continue
		if not row.get("line_ready_for_downstream_creation"):
			continue
		if _append_attendance_line_if_missing(draft_doc, _build_attendance_line_from_preparation(row)):
			created += 1
	return created


def _line_label(row):
	return row.get("service_line") or row.get("preparation_source_key") or row.idx


def _calculate_totals(doc):
	totals = {
		"attendance_line_count": len(doc.get("attendance_lines") or []),
		"attendance_hours_total": 0,
		"estimated_worker_hours_total": 0,
		"attendance_ready_count": 0,
		"attendance_approved_count": 0,
		"attendance_hold_count": 0,
		"employee_missing_count": 0,
	}
	for row in doc.get("attendance_lines") or []:
		for source, target in [("attendance_hours", "attendance_hours_total"), ("estimated_worker_hours", "estimated_worker_hours_total")]:
			try:
				totals[target] += float(row.get(source) or 0)
			except Exception:
				pass
		if row.get("line_ready_for_attendance_creation"):
			totals["attendance_ready_count"] += 1
		if row.get("attendance_draft_status") == "Approved":
			totals["attendance_approved_count"] += 1
		if row.get("attendance_hold"):
			totals["attendance_hold_count"] += 1
		if not row.get("support_worker_employee"):
			totals["employee_missing_count"] += 1
	totals["attendance_hours_total"] = round(totals["attendance_hours_total"], 2)
	totals["estimated_worker_hours_total"] = round(totals["estimated_worker_hours_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(ATTENDANCE_DRAFT, fieldname):
			doc.set(fieldname, value)
	return totals


def _calculate_readiness(doc):
	lines = doc.get("attendance_lines") or []
	checks = [
		{"label": "Downstream Preparation linked", "complete": bool(doc.get("downstream_preparation"))},
		{"label": "Downstream Preparation approved", "complete": _is_downstream_approved(doc.get("downstream_preparation"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Attendance Owner assigned", "complete": bool(doc.get("attendance_owner"))},
		{"label": "Attendance Period Start entered", "complete": bool(doc.get("attendance_period_start"))},
		{"label": "Attendance Period End entered", "complete": bool(doc.get("attendance_period_end"))},
		{"label": "At least one attendance draft line exists", "complete": bool(lines)},
	]
	line_checks = [
		("All attendance lines have attendance date", [row for row in lines if not row.get("attendance_date")]),
		("All attendance lines have actual start/end time", [row for row in lines if not row.get("actual_start_time") or not row.get("actual_end_time")]),
		("All attendance lines have attendance hours", [row for row in lines if not row.get("attendance_hours")]),
		("All attendance lines have support worker reference", [row for row in lines if not _worker_reference_exists(row)]),
		("Attendance preparation-ready flags are complete", [row for row in lines if not row.get("attendance_preparation_ready")]),
		("All attendance lines have service delivered confirmation", [row for row in lines if not row.get("service_delivered")]),
		("All attendance lines have proposed attendance status", [row for row in lines if not row.get("proposed_attendance_status")]),
		("All attendance lines marked ready for attendance creation", [row for row in lines if not row.get("line_ready_for_attendance_creation")]),
		("No attendance hold remains", [row for row in lines if row.get("attendance_hold")]),
	]
	if doc.get("employee_required_for_attendance"):
		line_checks.insert(4, ("Employee mapping complete for attendance creation", [row for row in lines if not row.get("support_worker_employee")]))
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
		"attendance_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(ATTENDANCE_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(ATTENDANCE_DRAFT, "attendance_draft_ready"):
		doc.attendance_draft_ready = 1 if summary["attendance_ready"] else 0

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
		(INTAKE, doc.get("participant_intake")),
	]:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_attendance_draft", doc.name)
		_db_set_if_field(doctype, name, "attendance_draft_status", doc.status)
		_db_set_if_field(doctype, name, "attendance_draft_ready", 1 if summary["attendance_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_attendance_draft_from_downstream_preparation(downstream_preparation):
	_check_role()
	if not downstream_preparation:
		frappe.throw(_("NDIS CRM Downstream Preparation is required."))
	if not frappe.db.exists(DOWNSTREAM_PREPARATION, downstream_preparation):
		frappe.throw(_("NDIS CRM Downstream Preparation {0} was not found.").format(downstream_preparation))

	existing = _existing_attendance_draft_for_downstream(downstream_preparation)
	if existing:
		return {"doctype": ATTENDANCE_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Attendance Draft returned."}

	downstream_doc = frappe.get_doc(DOWNSTREAM_PREPARATION, downstream_preparation)
	doc = frappe.new_doc(ATTENDANCE_DRAFT)
	doc.status = "Draft"
	doc.downstream_preparation = downstream_doc.name
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
	doc.attendance_period_start = downstream_doc.get("preparation_period_start")
	doc.attendance_period_end = downstream_doc.get("preparation_period_end")
	doc.attendance_owner = frappe.session.user
	doc.employee_required_for_attendance = 1
	_set_if_field(doc, "default_house", downstream_doc.get("default_house"))
	_set_if_field(doc, "default_cost_center", downstream_doc.get("default_cost_center"))

	created_count = _generate_lines_from_downstream_preparation(doc, downstream_doc)
	if _field_exists(ATTENDANCE_DRAFT, "attendance_line_count"):
		doc.attendance_line_count = created_count
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.attendance_draft_ready = 1 if summary["attendance_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": ATTENDANCE_DRAFT,
		"name": doc.name,
		"created": True,
		"attendance_line_count": created_count,
		"message": "NDIS CRM Attendance Draft created successfully.",
	}


@frappe.whitelist()
def create_attendance_draft_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_attendance_draft_for_deal(deal)
	if existing:
		return {"doctype": ATTENDANCE_DRAFT, "name": existing, "created": False, "message": "Existing NDIS CRM Attendance Draft returned."}

	downstream = _get_downstream_preparation_for_deal(deal)
	if not downstream:
		try:
			from ndis_crm.phase13_downstream_preparation import create_downstream_preparation_from_crm_deal
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Downstream Preparation before creating Attendance Draft."))
		result = create_downstream_preparation_from_crm_deal(deal)
		downstream = result.get("name")
	return create_attendance_draft_from_downstream_preparation(downstream)


@frappe.whitelist()
def generate_attendance_lines(attendance_draft):
	_check_role()
	doc = frappe.get_doc(ATTENDANCE_DRAFT, attendance_draft)
	if not doc.get("downstream_preparation"):
		frappe.throw(_("Downstream Preparation is required."))
	downstream_doc = frappe.get_doc(DOWNSTREAM_PREPARATION, doc.downstream_preparation)
	created_count = _generate_lines_from_downstream_preparation(doc, downstream_doc)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Attendance lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_attendance_draft_readiness(attendance_draft):
	_check_role()
	doc = frappe.get_doc(ATTENDANCE_DRAFT, attendance_draft)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Attendance draft readiness validated."}


@frappe.whitelist()
def mark_ready_for_attendance_creation(attendance_draft):
	_check_role()
	doc = frappe.get_doc(ATTENDANCE_DRAFT, attendance_draft)
	summary = _calculate_readiness(doc)
	if not summary["attendance_ready"]:
		frappe.throw(_("Cannot mark Ready for Attendance Creation. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Attendance Creation"
	doc.readiness_percent = summary["readiness_percent"]
	doc.attendance_draft_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": ATTENDANCE_DRAFT, "name": doc.name, "message": "Attendance Draft marked Ready for Attendance Creation."}


@frappe.whitelist()
def approve_attendance_draft(attendance_draft):
	_check_role()
	doc = frappe.get_doc(ATTENDANCE_DRAFT, attendance_draft)
	summary = _calculate_readiness(doc)
	if not summary["attendance_ready"]:
		frappe.throw(_("Cannot approve Attendance Draft. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Attendance Draft Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.attendance_draft_ready = 1
	for row in doc.get("attendance_lines") or []:
		if row.get("attendance_draft_status") in ["Draft", "Ready"]:
			row.attendance_draft_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": ATTENDANCE_DRAFT, "name": doc.name, "message": "Attendance Draft approved."}


def validate_attendance_draft(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(ATTENDANCE_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(ATTENDANCE_DRAFT, "attendance_draft_ready"):
		doc.attendance_draft_ready = 1 if summary["attendance_ready"] else 0
	if doc.status in READY_STATUSES and not summary["attendance_ready"]:
		frappe.throw(_("Cannot set Attendance Draft to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))


def on_attendance_draft_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Attendance Draft Summary Sync Failed")


def validate_crm_deal_phase14(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	attendance_required = doc.get("ndis_attendance_draft_required") if _field_exists(CRM_DEAL, "ndis_attendance_draft_required") else 0
	if not attendance_required:
		return
	attendance_draft = doc.get("ndis_attendance_draft") if _field_exists(CRM_DEAL, "ndis_attendance_draft") else None
	if not attendance_draft:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Attendance Draft must be created and approved."))
	if not _is_attendance_draft_approved(attendance_draft):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Attendance Draft must be approved."))


def validate_crm_deal_phase14_combined(doc, method=None):
	"""Preserve Phase 2-13 validator chain, then add optional Phase 14 validation."""
	try:
		from ndis_crm.phase13_downstream_preparation import validate_crm_deal_phase13_combined

		validate_crm_deal_phase13_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase12_delivery_evidence import validate_crm_deal_phase12_combined

			validate_crm_deal_phase12_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase14(doc, method)


def phase14_health_check():
	print("---- NDIS CRM Phase 14 Health Check ----")
	for dt in [
		ATTENDANCE_DRAFT_LINE,
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
	for dt in ["Attendance", "Employee", PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in ["ndis_attendance_draft_required", "ndis_attendance_draft", "attendance_draft_status", "attendance_draft_ready"]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")
	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, SESSION_DRAFT, EVIDENCE_REVIEW, DOWNSTREAM_PREPARATION, INTAKE]:
		for field in ["ndis_attendance_draft", "attendance_draft_status", "attendance_draft_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Attendance Draft records:", frappe.db.count(ATTENDANCE_DRAFT) if _doctype_exists(ATTENDANCE_DRAFT) else 0)
	print("CRM Deal Phase 14 combined validator should be active through hooks.py.")
	print("---- End Phase 14 Health Check ----")
