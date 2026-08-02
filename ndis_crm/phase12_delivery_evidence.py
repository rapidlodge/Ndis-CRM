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
SESSION_DRAFT_LINE = "NDIS CRM Service Session Draft Line"

EVIDENCE_REVIEW = "NDIS CRM Service Delivery Evidence Review"
EVIDENCE_LINE = "NDIS CRM Service Delivery Evidence Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Evidence Review", "Evidence Reviewed", "Approved for Downstream Review"]
APPROVED_STATUSES = ["Approved for Downstream Review"]
APPROVED_SESSION_STATUSES = ["Session Draft Approved"]

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
	user_roles = set(frappe.get_roles())
	if not user_roles.intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this service delivery evidence action."))


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


def _existing_evidence_for_session_draft(session_draft):
	if not _doctype_exists(EVIDENCE_REVIEW):
		return None

	if _field_exists(SESSION_DRAFT, "ndis_delivery_evidence_review"):
		existing = frappe.db.get_value(SESSION_DRAFT, session_draft, "ndis_delivery_evidence_review")
		if existing:
			return existing

	return frappe.db.get_value(EVIDENCE_REVIEW, {"service_session_draft": session_draft}, "name")


def _existing_evidence_for_deal(deal):
	if not _doctype_exists(EVIDENCE_REVIEW):
		return None

	if _field_exists(CRM_DEAL, "ndis_delivery_evidence_review"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_delivery_evidence_review")
		if existing:
			return existing

	return frappe.db.get_value(EVIDENCE_REVIEW, {"crm_deal": deal}, "name")


def _get_session_draft_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_service_session_draft"):
		session_draft = frappe.db.get_value(CRM_DEAL, deal, "ndis_service_session_draft")
		if session_draft:
			return session_draft

	if _doctype_exists(SESSION_DRAFT):
		return frappe.db.get_value(SESSION_DRAFT, {"crm_deal": deal}, "name")

	return None


def _is_session_draft_approved(session_draft):
	if not session_draft or not frappe.db.exists(SESSION_DRAFT, session_draft):
		return False

	status, ready = frappe.db.get_value(SESSION_DRAFT, session_draft, ["status", "session_draft_ready"])
	return status in APPROVED_SESSION_STATUSES and bool(ready)


def _is_evidence_approved(evidence_review):
	if not evidence_review or not frappe.db.exists(EVIDENCE_REVIEW, evidence_review):
		return False

	status, ready = frappe.db.get_value(EVIDENCE_REVIEW, evidence_review, ["status", "evidence_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _session_line_key(row):
	return "|".join([
		str(row.get("service_line") or ""),
		str(row.get("session_date") or ""),
		str(row.get("planned_start_time") or ""),
	])


def _append_evidence_line_if_missing(review_doc, row_data):
	existing = {
		row.session_source_key
		for row in review_doc.get("evidence_lines") or []
		if row.get("session_source_key")
	}
	key = row_data.get("session_source_key")

	if key and key in existing:
		return False

	review_doc.append("evidence_lines", row_data)
	return True


def _build_evidence_line_from_session_line(row):
	planned_hours = row.get("planned_hours") or 0
	workers_required = row.get("workers_required") or 1

	try:
		estimated_worker_hours = round(float(planned_hours) * float(workers_required), 2)
	except Exception:
		estimated_worker_hours = 0

	billing_precheck_ready = 1 if row.get("billing_precheck_ready") else 0

	return {
		"session_source_key": _session_line_key(row),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"session_date": row.get("session_date"),
		"planned_start_time": row.get("planned_start_time"),
		"planned_end_time": row.get("planned_end_time"),
		"planned_hours": planned_hours,
		"actual_start_time": row.get("planned_start_time"),
		"actual_end_time": row.get("planned_end_time"),
		"delivered_hours": planned_hours,
		"workers_required": workers_required,
		"estimated_worker_hours": estimated_worker_hours,
		"finance_service_type": row.get("finance_service_type"),
		"support_item": row.get("support_item"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"default_house": row.get("default_house"),
		"delivery_location": row.get("delivery_location"),
		"support_ratio": row.get("support_ratio"),
		"overnight_model": row.get("overnight_model"),
		"requires_roster": row.get("requires_roster"),
		"requires_house": row.get("requires_house"),
		"requires_clinical_review": row.get("requires_clinical_review"),
		"clinical_review_complete": row.get("clinical_review_complete"),
		"transport_required": row.get("transport_required"),
		"worker_skill_requirements": row.get("worker_skill_requirements"),
		"clinical_risk_notes": row.get("clinical_risk_notes"),
		"billing_precheck_required": row.get("billing_precheck_required"),
		"billing_precheck_ready": billing_precheck_ready,
		"participant_attended": 1,
		"service_delivered": 0,
		"progress_note_required": 1,
		"incident_flag": 0,
		"billing_hold": 0 if billing_precheck_ready else 1,
		"payroll_hold": 0,
		"evidence_reviewed": 0,
		"line_ready_for_downstream_review": 0,
		"evidence_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_evidence_lines_from_session_draft(review_doc, session_doc):
	created = 0

	for row in session_doc.get("session_lines") or []:
		if row.get("session_status") not in ["Approved", "Ready"]:
			continue

		data = _build_evidence_line_from_session_line(row)
		if _append_evidence_line_if_missing(review_doc, data):
			created += 1

	return created


def _calculate_review_totals(doc):
	totals = {
		"line_count": len(doc.get("evidence_lines") or []),
		"planned_hours": 0,
		"delivered_hours": 0,
		"estimated_worker_hours": 0,
		"delivered_count": 0,
		"incident_count": 0,
		"billing_hold_count": 0,
		"payroll_hold_count": 0,
	}

	for row in doc.get("evidence_lines") or []:
		for fieldname, total_key in [
			("planned_hours", "planned_hours"),
			("delivered_hours", "delivered_hours"),
			("estimated_worker_hours", "estimated_worker_hours"),
		]:
			try:
				totals[total_key] += float(row.get(fieldname) or 0)
			except Exception:
				pass

		if row.get("service_delivered"):
			totals["delivered_count"] += 1
		if row.get("incident_flag"):
			totals["incident_count"] += 1
		if row.get("billing_hold"):
			totals["billing_hold_count"] += 1
		if row.get("payroll_hold"):
			totals["payroll_hold_count"] += 1

	for key in ["planned_hours", "delivered_hours", "estimated_worker_hours"]:
		totals[key] = round(totals[key], 2)

	return totals


def _line_label(row):
	return row.get("service_line") or row.get("session_source_key") or row.idx


def _calculate_readiness(doc):
	lines = doc.get("evidence_lines") or []
	checks = [
		{"label": "Service Session Draft linked", "complete": bool(doc.get("service_session_draft"))},
		{"label": "Service Session Draft approved", "complete": _is_session_draft_approved(doc.get("service_session_draft"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Evidence Owner assigned", "complete": bool(doc.get("evidence_owner"))},
		{"label": "Review Period Start entered", "complete": bool(doc.get("review_period_start"))},
		{"label": "Review Period End entered", "complete": bool(doc.get("review_period_end"))},
		{"label": "At least one evidence line exists", "complete": bool(lines)},
	]

	line_checks = [
		("All evidence lines have session date", [row for row in lines if not row.get("session_date")]),
		("All evidence lines have actual start/end time", [row for row in lines if not row.get("actual_start_time") or not row.get("actual_end_time")]),
		("All evidence lines have delivered hours and workers required", [row for row in lines if not row.get("delivered_hours") or not row.get("workers_required")]),
		("All evidence lines have support worker reference", [row for row in lines if not row.get("support_worker_user") and not row.get("support_worker_employee") and not row.get("support_worker_name")]),
		("Non-attendance lines have reason", [row for row in lines if not row.get("participant_attended") and not row.get("non_attendance_reason")]),
		("All evidence lines have service delivered confirmation", [row for row in lines if not row.get("service_delivered")]),
		("Progress-note-required lines have progress note", [row for row in lines if row.get("progress_note_required") and not row.get("progress_note")]),
		("All evidence lines have support item and service booking", [row for row in lines if not row.get("support_item") or not row.get("service_booking")]),
		("Billing precheck-ready flags are complete", [row for row in lines if row.get("billing_precheck_required") and not row.get("billing_precheck_ready")]),
		("Incident-flagged lines have incident notes", [row for row in lines if row.get("incident_flag") and not row.get("incident_notes")]),
		("All evidence lines reviewed", [row for row in lines if not row.get("evidence_reviewed")]),
		("All evidence lines marked ready for downstream review", [row for row in lines if not row.get("line_ready_for_downstream_review")]),
		("No billing hold remains", [row for row in lines if row.get("billing_hold")]),
		("No payroll hold remains", [row for row in lines if row.get("payroll_hold")]),
	]

	for label, missing in line_checks:
		checks.append({
			"label": label,
			"complete": not missing,
			"details": [_line_label(row) for row in missing],
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
			label += ": " + ", ".join([str(value) for value in row["details"] if value])
		incomplete.append(label)

	return {
		"total_checks": total,
		"complete_checks": complete,
		"readiness_percent": readiness_percent,
		"evidence_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_totals(doc):
	totals = _calculate_review_totals(doc)

	for fieldname, value in [
		("evidence_line_count", totals["line_count"]),
		("planned_hours_total", totals["planned_hours"]),
		("delivered_hours_total", totals["delivered_hours"]),
		("estimated_worker_hours_total", totals["estimated_worker_hours"]),
		("delivered_session_count", totals["delivered_count"]),
		("incident_count", totals["incident_count"]),
		("billing_hold_count", totals["billing_hold_count"]),
		("payroll_hold_count", totals["payroll_hold_count"]),
	]:
		if _field_exists(EVIDENCE_REVIEW, fieldname):
			doc.set(fieldname, value)

	return totals


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)

	if _field_exists(EVIDENCE_REVIEW, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(EVIDENCE_REVIEW, "evidence_ready"):
		doc.evidence_ready = 1 if summary["evidence_ready"] else 0

	targets = [
		(CRM_DEAL, doc.get("crm_deal")),
		(HANDOVER, doc.get("handover")),
		(FINANCE_ONBOARDING, doc.get("finance_onboarding")),
		(OPERATIONS_SETUP, doc.get("operations_setup")),
		(SCHEDULE_DRAFT, doc.get("service_schedule_draft")),
		(ROSTER_REQUEST, doc.get("roster_build_request")),
		(SERVICE_FILE, doc.get("participant_service_file")),
		(SESSION_DRAFT, doc.get("service_session_draft")),
		(INTAKE, doc.get("participant_intake")),
	]

	for doctype, name in targets:
		if not name:
			continue

		_db_set_if_field(doctype, name, "ndis_delivery_evidence_review", doc.name)
		_db_set_if_field(doctype, name, "delivery_evidence_status", doc.status)
		_db_set_if_field(doctype, name, "delivery_evidence_ready", 1 if summary["evidence_ready"] else 0)

	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_delivery_evidence_review_from_session_draft(session_draft):
	_check_role()

	if not session_draft:
		frappe.throw(_("NDIS CRM Service Session Draft is required."))
	if not frappe.db.exists(SESSION_DRAFT, session_draft):
		frappe.throw(_("NDIS CRM Service Session Draft {0} was not found.").format(session_draft))

	existing = _existing_evidence_for_session_draft(session_draft)
	if existing:
		return {
			"doctype": EVIDENCE_REVIEW,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Service Delivery Evidence Review returned.",
		}

	session_doc = frappe.get_doc(SESSION_DRAFT, session_draft)
	doc = frappe.new_doc(EVIDENCE_REVIEW)
	doc.status = "Draft"
	doc.service_session_draft = session_doc.name
	doc.participant_service_file = session_doc.get("participant_service_file")
	doc.roster_build_request = session_doc.get("roster_build_request")
	doc.service_schedule_draft = session_doc.get("service_schedule_draft")
	doc.operations_setup = session_doc.get("operations_setup")
	doc.finance_onboarding = session_doc.get("finance_onboarding")
	doc.handover = session_doc.get("handover")
	doc.crm_deal = session_doc.get("crm_deal")
	doc.crm_lead = session_doc.get("crm_lead")
	doc.participant_intake = session_doc.get("participant_intake")
	doc.participant_customer = session_doc.get("participant_customer")
	doc.ndis_financial_profile = session_doc.get("ndis_financial_profile")
	doc.participant_name = session_doc.get("participant_name") or session_doc.get("participant_customer") or session_doc.name
	doc.ndis_number = session_doc.get("ndis_number")
	doc.plan_start_date = session_doc.get("plan_start_date")
	doc.plan_end_date = session_doc.get("plan_end_date")
	doc.review_period_start = session_doc.get("generation_start_date")
	doc.review_period_end = session_doc.get("generation_end_date")
	doc.evidence_owner = frappe.session.user
	doc.operations_owner = session_doc.get("operations_owner")
	doc.rostering_owner = session_doc.get("rostering_owner")
	doc.service_manager = session_doc.get("service_manager")
	doc.clinical_owner = session_doc.get("clinical_owner")

	_set_if_field(doc, "default_house", session_doc.get("default_house"))
	_set_if_field(doc, "default_cost_center", session_doc.get("default_cost_center"))

	created_count = _generate_evidence_lines_from_session_draft(doc, session_doc)
	if _field_exists(EVIDENCE_REVIEW, "evidence_line_count"):
		doc.evidence_line_count = created_count

	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.evidence_ready = 1 if summary["evidence_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()

	return {
		"doctype": EVIDENCE_REVIEW,
		"name": doc.name,
		"created": True,
		"evidence_line_count": created_count,
		"message": "NDIS CRM Service Delivery Evidence Review created successfully.",
	}


@frappe.whitelist()
def create_delivery_evidence_review_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_evidence_for_deal(deal)
	if existing:
		return {
			"doctype": EVIDENCE_REVIEW,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Service Delivery Evidence Review returned.",
		}

	session_draft = _get_session_draft_for_deal(deal)
	if not session_draft:
		try:
			from ndis_crm.phase11_service_sessions import create_service_session_draft_from_crm_deal
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Service Session Draft before creating Delivery Evidence Review."))

		result = create_service_session_draft_from_crm_deal(deal)
		session_draft = result.get("name")

	return create_delivery_evidence_review_from_session_draft(session_draft)


@frappe.whitelist()
def generate_evidence_lines(evidence_review):
	_check_role()

	if not evidence_review:
		frappe.throw(_("NDIS CRM Service Delivery Evidence Review is required."))

	doc = frappe.get_doc(EVIDENCE_REVIEW, evidence_review)
	if not doc.get("service_session_draft"):
		frappe.throw(_("Service Session Draft is required."))

	session_doc = frappe.get_doc(SESSION_DRAFT, doc.service_session_draft)
	created_count = _generate_evidence_lines_from_session_draft(doc, session_doc)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"created_count": created_count,
		"summary": summary,
		"message": f"Evidence lines generated. Created: {created_count}.",
	}


@frappe.whitelist()
def validate_evidence_readiness(evidence_review):
	_check_role()

	doc = frappe.get_doc(EVIDENCE_REVIEW, evidence_review)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Delivery evidence readiness validated."}


@frappe.whitelist()
def mark_ready_for_evidence_review(evidence_review):
	_check_role()

	doc = frappe.get_doc(EVIDENCE_REVIEW, evidence_review)
	summary = _calculate_readiness(doc)
	if not summary["evidence_ready"]:
		frappe.throw(_("Cannot mark Ready for Evidence Review. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Ready for Evidence Review"
	doc.readiness_percent = summary["readiness_percent"]
	doc.evidence_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": EVIDENCE_REVIEW,
		"name": doc.name,
		"message": "Delivery Evidence Review marked Ready for Evidence Review.",
	}


@frappe.whitelist()
def approve_evidence_review(evidence_review):
	_check_role()

	doc = frappe.get_doc(EVIDENCE_REVIEW, evidence_review)
	summary = _calculate_readiness(doc)
	if not summary["evidence_ready"]:
		frappe.throw(_("Cannot approve Delivery Evidence Review. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Approved for Downstream Review"
	doc.readiness_percent = summary["readiness_percent"]
	doc.evidence_ready = 1

	for row in doc.get("evidence_lines") or []:
		if row.get("evidence_status") in ["Draft", "Ready"]:
			row.evidence_status = "Approved"

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": EVIDENCE_REVIEW,
		"name": doc.name,
		"message": "Delivery Evidence Review approved for downstream review.",
	}


def validate_evidence_review(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)

	if _field_exists(EVIDENCE_REVIEW, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(EVIDENCE_REVIEW, "evidence_ready"):
		doc.evidence_ready = 1 if summary["evidence_ready"] else 0

	if doc.status in READY_STATUSES and not summary["evidence_ready"]:
		frappe.throw(
			_("Cannot set Delivery Evidence Review to {0}. Incomplete items: {1}").format(
				doc.status,
				"; ".join(summary["incomplete"]),
			)
		)


def on_evidence_review_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Delivery Evidence Review Summary Sync Failed")


def validate_crm_deal_phase12(doc, method=None):
	if doc.status != "Won / Active Client":
		return

	evidence_required = 0
	if _field_exists(CRM_DEAL, "ndis_delivery_evidence_review_required"):
		evidence_required = doc.get("ndis_delivery_evidence_review_required")
	if not evidence_required:
		return

	evidence_review = doc.get("ndis_delivery_evidence_review") if _field_exists(CRM_DEAL, "ndis_delivery_evidence_review") else None
	if not evidence_review:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Delivery Evidence Review must be created and approved."))
	if not _is_evidence_approved(evidence_review):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Delivery Evidence Review must be approved for downstream review."))


def validate_crm_deal_phase12_combined(doc, method=None):
	"""Preserve Phase 2-11 validator chain, then add optional Phase 12 validation."""
	try:
		from ndis_crm.phase11_service_sessions import validate_crm_deal_phase11_combined

		validate_crm_deal_phase11_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase10_service_file import validate_crm_deal_phase10_combined

			validate_crm_deal_phase10_combined(doc, method)
		except ImportError:
			pass

	validate_crm_deal_phase12(doc, method)


def phase12_health_check():
	print("---- NDIS CRM Phase 12 Health Check ----")

	for dt in [
		EVIDENCE_LINE,
		EVIDENCE_REVIEW,
		SESSION_DRAFT,
		SESSION_DRAFT_LINE,
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

	for dt in [PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE, "Employee"]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

	for field in [
		"ndis_delivery_evidence_review_required",
		"ndis_delivery_evidence_review",
		"delivery_evidence_status",
		"delivery_evidence_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, SESSION_DRAFT, INTAKE]:
		for field in ["ndis_delivery_evidence_review", "delivery_evidence_status", "delivery_evidence_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")

	print("NDIS CRM Service Delivery Evidence Review records:", frappe.db.count(EVIDENCE_REVIEW) if _doctype_exists(EVIDENCE_REVIEW) else 0)
	print("CRM Deal Phase 12 combined validator should be active through hooks.py.")
	print("---- End Phase 12 Health Check ----")
