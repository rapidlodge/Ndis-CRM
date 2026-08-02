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
EVIDENCE_LINE = "NDIS CRM Service Delivery Evidence Line"

DOWNSTREAM_PREPARATION = "NDIS CRM Downstream Preparation"
DOWNSTREAM_PREPARATION_LINE = "NDIS CRM Downstream Preparation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Downstream Processing", "Downstream Preparation Approved"]
APPROVED_STATUSES = ["Downstream Preparation Approved"]
APPROVED_EVIDENCE_STATUSES = ["Approved for Downstream Review"]

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
		frappe.throw(_("You do not have permission to perform this downstream preparation action."))


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


def _existing_preparation_for_evidence(evidence_review):
	if not _doctype_exists(DOWNSTREAM_PREPARATION):
		return None
	if _field_exists(EVIDENCE_REVIEW, "ndis_downstream_preparation"):
		existing = frappe.db.get_value(EVIDENCE_REVIEW, evidence_review, "ndis_downstream_preparation")
		if existing:
			return existing
	return frappe.db.get_value(DOWNSTREAM_PREPARATION, {"delivery_evidence_review": evidence_review}, "name")


def _existing_preparation_for_deal(deal):
	if not _doctype_exists(DOWNSTREAM_PREPARATION):
		return None
	if _field_exists(CRM_DEAL, "ndis_downstream_preparation"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_downstream_preparation")
		if existing:
			return existing
	return frappe.db.get_value(DOWNSTREAM_PREPARATION, {"crm_deal": deal}, "name")


def _get_evidence_review_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_delivery_evidence_review"):
		evidence = frappe.db.get_value(CRM_DEAL, deal, "ndis_delivery_evidence_review")
		if evidence:
			return evidence
	if _doctype_exists(EVIDENCE_REVIEW):
		return frappe.db.get_value(EVIDENCE_REVIEW, {"crm_deal": deal}, "name")
	return None


def _is_evidence_approved(evidence_review):
	if not evidence_review or not frappe.db.exists(EVIDENCE_REVIEW, evidence_review):
		return False
	status, ready = frappe.db.get_value(EVIDENCE_REVIEW, evidence_review, ["status", "evidence_ready"])
	return status in APPROVED_EVIDENCE_STATUSES and bool(ready)


def _is_preparation_approved(preparation):
	if not preparation or not frappe.db.exists(DOWNSTREAM_PREPARATION, preparation):
		return False
	status, ready = frappe.db.get_value(DOWNSTREAM_PREPARATION, preparation, ["status", "downstream_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _evidence_line_key(row):
	return row.get("session_source_key") or "|".join([
		str(row.get("service_line") or ""),
		str(row.get("session_date") or ""),
		str(row.get("actual_start_time") or row.get("planned_start_time") or ""),
	])


def _append_preparation_line_if_missing(prep_doc, row_data):
	existing = {
		row.evidence_source_key
		for row in prep_doc.get("preparation_lines") or []
		if row.get("evidence_source_key")
	}
	key = row_data.get("evidence_source_key")
	if key and key in existing:
		return False
	prep_doc.append("preparation_lines", row_data)
	return True


def _worker_reference_exists(row):
	return bool(row.get("support_worker_user") or row.get("support_worker_employee") or row.get("support_worker_name"))


def _billing_source_ready(row):
	return bool(row.get("service_delivered") and row.get("support_item") and row.get("service_booking") and not row.get("billing_hold"))


def _payroll_source_ready(row):
	return bool(row.get("service_delivered") and row.get("delivered_hours") and _worker_reference_exists(row) and not row.get("payroll_hold"))


def _attendance_source_ready(row):
	return bool(row.get("session_date") and row.get("actual_start_time") and row.get("actual_end_time") and row.get("service_delivered") and _worker_reference_exists(row))


def _claim_source_ready(row):
	return bool(_billing_source_ready(row) and row.get("finance_service_type") and row.get("plan_budget"))


def _build_preparation_line_from_evidence(row):
	attendance_ready = 1 if _attendance_source_ready(row) else 0
	billing_ready = 1 if _billing_source_ready(row) else 0
	payroll_ready = 1 if _payroll_source_ready(row) else 0
	claim_ready = 1 if _claim_source_ready(row) else 0
	service_delivered = 1 if row.get("service_delivered") else 0

	return {
		"evidence_source_key": _evidence_line_key(row),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"session_date": row.get("session_date"),
		"actual_start_time": row.get("actual_start_time"),
		"actual_end_time": row.get("actual_end_time"),
		"delivered_hours": row.get("delivered_hours"),
		"workers_required": row.get("workers_required"),
		"estimated_worker_hours": row.get("estimated_worker_hours"),
		"support_worker_user": row.get("support_worker_user"),
		"support_worker_employee": row.get("support_worker_employee"),
		"support_worker_name": row.get("support_worker_name"),
		"participant_attended": row.get("participant_attended"),
		"non_attendance_reason": row.get("non_attendance_reason"),
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
		"billing_precheck_ready": row.get("billing_precheck_ready"),
		"evidence_status": row.get("evidence_status"),
		"attendance_preparation_required": service_delivered,
		"billing_preparation_required": service_delivered,
		"payroll_preparation_required": service_delivered,
		"claim_preparation_required": service_delivered,
		"attendance_preparation_ready": attendance_ready,
		"billing_preparation_ready": billing_ready,
		"payroll_preparation_ready": payroll_ready,
		"claim_preparation_ready": claim_ready,
		"attendance_hold": 0 if attendance_ready else 1,
		"billing_hold": row.get("billing_hold") or (0 if billing_ready else 1),
		"payroll_hold": row.get("payroll_hold") or (0 if payroll_ready else 1),
		"claim_hold": 0 if claim_ready else 1,
		"line_ready_for_downstream_creation": 0,
		"preparation_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_evidence_review(prep_doc, evidence_doc):
	created = 0
	for row in evidence_doc.get("evidence_lines") or []:
		if row.get("evidence_status") not in ["Approved", "Reviewed", "Ready"]:
			continue
		if not row.get("line_ready_for_downstream_review"):
			continue
		if _append_preparation_line_if_missing(prep_doc, _build_preparation_line_from_evidence(row)):
			created += 1
	return created


def _calculate_totals(doc):
	totals = {
		"preparation_line_count": len(doc.get("preparation_lines") or []),
		"delivered_hours_total": 0,
		"estimated_worker_hours_total": 0,
		"attendance_ready_count": 0,
		"billing_ready_count": 0,
		"payroll_ready_count": 0,
		"claim_ready_count": 0,
		"attendance_hold_count": 0,
		"billing_hold_count": 0,
		"payroll_hold_count": 0,
		"claim_hold_count": 0,
	}
	for row in doc.get("preparation_lines") or []:
		for fieldname in ["delivered_hours", "estimated_worker_hours"]:
			try:
				totals[f"{fieldname}_total"] += float(row.get(fieldname) or 0)
			except Exception:
				pass
		for key in ["attendance", "billing", "payroll", "claim"]:
			if row.get(f"{key}_preparation_ready"):
				totals[f"{key}_ready_count"] += 1
			if row.get(f"{key}_hold"):
				totals[f"{key}_hold_count"] += 1
	totals["delivered_hours_total"] = round(totals["delivered_hours_total"], 2)
	totals["estimated_worker_hours_total"] = round(totals["estimated_worker_hours_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(DOWNSTREAM_PREPARATION, fieldname):
			doc.set(fieldname, value)
	return totals


def _line_label(row):
	return row.get("service_line") or row.get("evidence_source_key") or row.idx


def _calculate_readiness(doc):
	lines = doc.get("preparation_lines") or []
	checks = [
		{"label": "Delivery Evidence Review linked", "complete": bool(doc.get("delivery_evidence_review"))},
		{"label": "Delivery Evidence Review approved", "complete": _is_evidence_approved(doc.get("delivery_evidence_review"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Preparation Owner assigned", "complete": bool(doc.get("preparation_owner"))},
		{"label": "Preparation Period Start entered", "complete": bool(doc.get("preparation_period_start"))},
		{"label": "Preparation Period End entered", "complete": bool(doc.get("preparation_period_end"))},
		{"label": "At least one preparation line exists", "complete": bool(lines)},
	]
	line_checks = [
		("All preparation lines have session date", [row for row in lines if not row.get("session_date")]),
		("All preparation lines have actual start/end time", [row for row in lines if not row.get("actual_start_time") or not row.get("actual_end_time")]),
		("All preparation lines have delivered hours", [row for row in lines if not row.get("delivered_hours")]),
		("Payroll-required lines have support worker reference", [row for row in lines if row.get("payroll_preparation_required") and not _worker_reference_exists(row)]),
		("Billing-required lines have support item and service booking", [row for row in lines if row.get("billing_preparation_required") and (not row.get("support_item") or not row.get("service_booking"))]),
		("Claim-required lines have finance type, plan budget and service booking", [row for row in lines if row.get("claim_preparation_required") and (not row.get("finance_service_type") or not row.get("plan_budget") or not row.get("service_booking"))]),
		("Attendance preparation-ready flags are complete", [row for row in lines if row.get("attendance_preparation_required") and not row.get("attendance_preparation_ready")]),
		("Billing preparation-ready flags are complete", [row for row in lines if row.get("billing_preparation_required") and not row.get("billing_preparation_ready")]),
		("Payroll preparation-ready flags are complete", [row for row in lines if row.get("payroll_preparation_required") and not row.get("payroll_preparation_ready")]),
		("Claim preparation-ready flags are complete", [row for row in lines if row.get("claim_preparation_required") and not row.get("claim_preparation_ready")]),
		("All preparation lines marked ready for downstream creation", [row for row in lines if not row.get("line_ready_for_downstream_creation")]),
	]
	for label, missing in line_checks:
		checks.append({"label": label, "complete": not missing, "details": [_line_label(row) for row in missing]})

	holds = []
	for row in lines:
		for key in ["attendance", "billing", "payroll", "claim"]:
			if row.get(f"{key}_hold"):
				holds.append(f"{_line_label(row)}: {key}")
	checks.append({"label": "No downstream preparation holds remain", "complete": not holds, "details": holds})

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
		"downstream_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(DOWNSTREAM_PREPARATION, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(DOWNSTREAM_PREPARATION, "downstream_ready"):
		doc.downstream_ready = 1 if summary["downstream_ready"] else 0

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
		(INTAKE, doc.get("participant_intake")),
	]:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_downstream_preparation", doc.name)
		_db_set_if_field(doctype, name, "downstream_preparation_status", doc.status)
		_db_set_if_field(doctype, name, "downstream_preparation_ready", 1 if summary["downstream_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_downstream_preparation_from_evidence_review(evidence_review):
	_check_role()
	if not evidence_review:
		frappe.throw(_("NDIS CRM Service Delivery Evidence Review is required."))
	if not frappe.db.exists(EVIDENCE_REVIEW, evidence_review):
		frappe.throw(_("NDIS CRM Service Delivery Evidence Review {0} was not found.").format(evidence_review))

	existing = _existing_preparation_for_evidence(evidence_review)
	if existing:
		return {"doctype": DOWNSTREAM_PREPARATION, "name": existing, "created": False, "message": "Existing NDIS CRM Downstream Preparation returned."}

	evidence_doc = frappe.get_doc(EVIDENCE_REVIEW, evidence_review)
	doc = frappe.new_doc(DOWNSTREAM_PREPARATION)
	doc.status = "Draft"
	doc.delivery_evidence_review = evidence_doc.name
	for target, source in [
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
		("operations_owner", "operations_owner"),
		("rostering_owner", "rostering_owner"),
		("service_manager", "service_manager"),
		("clinical_owner", "clinical_owner"),
	]:
		doc.set(target, evidence_doc.get(source))
	doc.participant_name = evidence_doc.get("participant_name") or evidence_doc.get("participant_customer") or evidence_doc.name
	doc.preparation_period_start = evidence_doc.get("review_period_start")
	doc.preparation_period_end = evidence_doc.get("review_period_end")
	doc.preparation_owner = frappe.session.user
	_set_if_field(doc, "default_house", evidence_doc.get("default_house"))
	_set_if_field(doc, "default_cost_center", evidence_doc.get("default_cost_center"))

	created_count = _generate_lines_from_evidence_review(doc, evidence_doc)
	if _field_exists(DOWNSTREAM_PREPARATION, "preparation_line_count"):
		doc.preparation_line_count = created_count
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.downstream_ready = 1 if summary["downstream_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": DOWNSTREAM_PREPARATION,
		"name": doc.name,
		"created": True,
		"preparation_line_count": created_count,
		"message": "NDIS CRM Downstream Preparation created successfully.",
	}


@frappe.whitelist()
def create_downstream_preparation_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_preparation_for_deal(deal)
	if existing:
		return {"doctype": DOWNSTREAM_PREPARATION, "name": existing, "created": False, "message": "Existing NDIS CRM Downstream Preparation returned."}

	evidence_review = _get_evidence_review_for_deal(deal)
	if not evidence_review:
		try:
			from ndis_crm.phase12_delivery_evidence import create_delivery_evidence_review_from_crm_deal
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Service Delivery Evidence Review before creating Downstream Preparation."))
		result = create_delivery_evidence_review_from_crm_deal(deal)
		evidence_review = result.get("name")
	return create_downstream_preparation_from_evidence_review(evidence_review)


@frappe.whitelist()
def generate_preparation_lines(downstream_preparation):
	_check_role()
	doc = frappe.get_doc(DOWNSTREAM_PREPARATION, downstream_preparation)
	if not doc.get("delivery_evidence_review"):
		frappe.throw(_("Delivery Evidence Review is required."))
	evidence_doc = frappe.get_doc(EVIDENCE_REVIEW, doc.delivery_evidence_review)
	created_count = _generate_lines_from_evidence_review(doc, evidence_doc)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Preparation lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_downstream_preparation_readiness(downstream_preparation):
	_check_role()
	doc = frappe.get_doc(DOWNSTREAM_PREPARATION, downstream_preparation)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Downstream preparation readiness validated."}


@frappe.whitelist()
def mark_ready_for_downstream_processing(downstream_preparation):
	_check_role()
	doc = frappe.get_doc(DOWNSTREAM_PREPARATION, downstream_preparation)
	summary = _calculate_readiness(doc)
	if not summary["downstream_ready"]:
		frappe.throw(_("Cannot mark Ready for Downstream Processing. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Downstream Processing"
	doc.readiness_percent = summary["readiness_percent"]
	doc.downstream_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": DOWNSTREAM_PREPARATION, "name": doc.name, "message": "Downstream Preparation marked Ready for Downstream Processing."}


@frappe.whitelist()
def approve_downstream_preparation(downstream_preparation):
	_check_role()
	doc = frappe.get_doc(DOWNSTREAM_PREPARATION, downstream_preparation)
	summary = _calculate_readiness(doc)
	if not summary["downstream_ready"]:
		frappe.throw(_("Cannot approve Downstream Preparation. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Downstream Preparation Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.downstream_ready = 1
	for row in doc.get("preparation_lines") or []:
		if row.get("preparation_status") in ["Draft", "Ready"]:
			row.preparation_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": DOWNSTREAM_PREPARATION, "name": doc.name, "message": "Downstream Preparation approved."}


def validate_downstream_preparation(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(DOWNSTREAM_PREPARATION, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(DOWNSTREAM_PREPARATION, "downstream_ready"):
		doc.downstream_ready = 1 if summary["downstream_ready"] else 0
	if doc.status in READY_STATUSES and not summary["downstream_ready"]:
		frappe.throw(_("Cannot set Downstream Preparation to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))


def on_downstream_preparation_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Downstream Preparation Summary Sync Failed")


def validate_crm_deal_phase13(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	preparation_required = doc.get("ndis_downstream_preparation_required") if _field_exists(CRM_DEAL, "ndis_downstream_preparation_required") else 0
	if not preparation_required:
		return
	preparation = doc.get("ndis_downstream_preparation") if _field_exists(CRM_DEAL, "ndis_downstream_preparation") else None
	if not preparation:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Downstream Preparation must be created and approved."))
	if not _is_preparation_approved(preparation):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Downstream Preparation must be approved."))


def validate_crm_deal_phase13_combined(doc, method=None):
	"""Preserve Phase 2-12 validator chain, then add optional Phase 13 validation."""
	try:
		from ndis_crm.phase12_delivery_evidence import validate_crm_deal_phase12_combined

		validate_crm_deal_phase12_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase11_service_sessions import validate_crm_deal_phase11_combined

			validate_crm_deal_phase11_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase13(doc, method)


def phase13_health_check():
	print("---- NDIS CRM Phase 13 Health Check ----")
	for dt in [
		DOWNSTREAM_PREPARATION_LINE,
		DOWNSTREAM_PREPARATION,
		EVIDENCE_REVIEW,
		EVIDENCE_LINE,
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
	for dt in [PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE, "Employee", "Attendance", "Timesheet", "Sales Invoice", "Payroll Entry", "Salary Slip"]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in ["ndis_downstream_preparation_required", "ndis_downstream_preparation", "downstream_preparation_status", "downstream_preparation_ready"]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")
	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, SESSION_DRAFT, EVIDENCE_REVIEW, INTAKE]:
		for field in ["ndis_downstream_preparation", "downstream_preparation_status", "downstream_preparation_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Downstream Preparation records:", frappe.db.count(DOWNSTREAM_PREPARATION) if _doctype_exists(DOWNSTREAM_PREPARATION) else 0)
	print("CRM Deal Phase 13 combined validator should be active through hooks.py.")
	print("---- End Phase 13 Health Check ----")
