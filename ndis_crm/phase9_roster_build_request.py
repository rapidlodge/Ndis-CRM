import frappe
from frappe import _


CRM_DEAL = "CRM Deal"
CRM_LEAD = "CRM Lead"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
SCHEDULE_DRAFT_LINE = "NDIS CRM Service Schedule Draft Line"

ROSTER_REQUEST = "NDIS CRM Roster Build Request"
ROSTER_REQUEST_LINE = "NDIS CRM Roster Build Request Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = [
	"Ready for Roster Build",
	"Submitted to Rostering",
	"Accepted by Rostering",
	"Roster Build Complete",
]

ACCEPTED_STATUSES = [
	"Accepted by Rostering",
	"Roster Build Complete",
]

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
		frappe.throw(_("You do not have permission to perform this NDIS CRM roster build action."))


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


def _existing_request_for_schedule(schedule_draft):
	if not _doctype_exists(ROSTER_REQUEST):
		return None

	if _field_exists(SCHEDULE_DRAFT, "ndis_roster_build_request"):
		existing = frappe.db.get_value(SCHEDULE_DRAFT, schedule_draft, "ndis_roster_build_request")
		if existing:
			return existing

	return frappe.db.get_value(ROSTER_REQUEST, {"service_schedule_draft": schedule_draft}, "name")


def _existing_request_for_deal(deal):
	if not _doctype_exists(ROSTER_REQUEST):
		return None

	if _field_exists(CRM_DEAL, "ndis_roster_build_request"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_roster_build_request")
		if existing:
			return existing

	return frappe.db.get_value(ROSTER_REQUEST, {"crm_deal": deal}, "name")


def _get_schedule_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_service_schedule_draft"):
		schedule = frappe.db.get_value(CRM_DEAL, deal, "ndis_service_schedule_draft")
		if schedule:
			return schedule

	if _doctype_exists(SCHEDULE_DRAFT):
		return frappe.db.get_value(SCHEDULE_DRAFT, {"crm_deal": deal}, "name")

	return None


def _is_schedule_approved(schedule_name):
	if not schedule_name or not frappe.db.exists(SCHEDULE_DRAFT, schedule_name):
		return False

	status, ready = frappe.db.get_value(SCHEDULE_DRAFT, schedule_name, ["status", "schedule_ready"])
	return status == "Schedule Approved" and bool(ready)


def _calculate_line_worker_hours(line):
	try:
		weekly_hours = float(line.get("estimated_weekly_hours") or 0)
		workers = float(line.get("workers_required") or 0)
		return round(weekly_hours * workers, 2)
	except Exception:
		return 0


def _normalize_line_defaults(line):
	if line.get("shifts_per_week") and line.get("hours_per_shift"):
		try:
			line.estimated_weekly_hours = round(float(line.shifts_per_week) * float(line.hours_per_shift), 2)
		except Exception:
			line.estimated_weekly_hours = 0

	if line.get("workers_required") and line.get("estimated_weekly_hours"):
		line.estimated_worker_hours = _calculate_line_worker_hours(line)


def _append_request_line_if_missing(request_doc, row_data):
	existing = {row.service_line for row in request_doc.get("request_lines") or []}
	if row_data.get("service_line") in existing:
		return
	request_doc.append("request_lines", row_data)


def _build_line_from_schedule_line(row):
	return {
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"priority": row.get("priority"),
		"finance_service_type": row.get("finance_service_type"),
		"support_item": row.get("support_item"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"requires_roster": row.get("requires_roster"),
		"start_date": row.get("start_date"),
		"end_date": row.get("end_date"),
		"frequency": row.get("frequency"),
		"days_of_week": row.get("days_of_week"),
		"shifts_per_week": row.get("shifts_per_week"),
		"hours_per_shift": row.get("hours_per_shift"),
		"estimated_weekly_hours": row.get("estimated_weekly_hours"),
		"workers_required": row.get("workers_required"),
		"estimated_worker_hours": row.get("estimated_worker_hours"),
		"start_time": row.get("start_time"),
		"end_time": row.get("end_time"),
		"flexible_time_window": row.get("flexible_time_window"),
		"preferred_time_notes": row.get("preferred_time_notes"),
		"requires_house": row.get("requires_house"),
		"default_house": row.get("default_house"),
		"delivery_location": row.get("delivery_location"),
		"support_ratio": row.get("support_ratio"),
		"overnight_model": row.get("overnight_model"),
		"requires_clinical_review": row.get("requires_clinical_review"),
		"clinical_review_complete": row.get("clinical_review_complete"),
		"transport_required": row.get("transport_required"),
		"worker_skill_requirements": row.get("worker_skill_requirements"),
		"clinical_risk_notes": row.get("clinical_risk_notes"),
		"roster_pattern_notes": row.get("roster_pattern_notes"),
		"ready_for_roster_build": row.get("ready_for_roster_build"),
		"line_ready_for_roster_build": row.get("ready_for_roster_build"),
		"status": "Pending",
		"notes": row.get("notes"),
	}


def _append_lines_from_schedule(request_doc, schedule_doc):
	for row in schedule_doc.get("schedule_lines") or []:
		if not row.get("requires_roster"):
			continue
		_append_request_line_if_missing(request_doc, _build_line_from_schedule_line(row))


def _line_label(row):
	return row.get("service_line") or row.get("service_model") or row.name


def _calculate_readiness(doc):
	checks = [
		{"label": "Service Schedule Draft linked", "complete": bool(doc.get("service_schedule_draft"))},
		{"label": "Service Schedule Draft approved", "complete": _is_schedule_approved(doc.get("service_schedule_draft"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Roster Owner assigned", "complete": bool(doc.get("rostering_owner"))},
		{"label": "Target Roster Build Date entered", "complete": bool(doc.get("target_roster_build_date"))},
	]

	lines = doc.get("request_lines") or []
	checks.append({"label": "At least one roster build request line exists", "complete": bool(lines)})

	missing_start_date = [_line_label(row) for row in lines if row.get("requires_roster") and not row.get("start_date")]
	checks.append({"label": "Roster-required lines have start date", "complete": not missing_start_date, "details": missing_start_date})

	missing_end_date = [_line_label(row) for row in lines if row.get("requires_roster") and not row.get("end_date")]
	checks.append({"label": "Roster-required lines have end date", "complete": not missing_end_date, "details": missing_end_date})

	missing_frequency = [_line_label(row) for row in lines if row.get("requires_roster") and not row.get("frequency")]
	checks.append({"label": "Roster-required lines have frequency", "complete": not missing_frequency, "details": missing_frequency})

	missing_days = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster") and row.get("frequency") in ["Weekly", "Fortnightly"] and not row.get("days_of_week")
	]
	checks.append({"label": "Weekly/fortnightly lines have days of week", "complete": not missing_days, "details": missing_days})

	missing_counts = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster") and (not row.get("shifts_per_week") or not row.get("hours_per_shift") or not row.get("workers_required"))
	]
	checks.append({"label": "Roster-required lines have shifts, hours and workers required", "complete": not missing_counts, "details": missing_counts})

	missing_time = [_line_label(row) for row in lines if row.get("requires_roster") and (not row.get("start_time") or not row.get("end_time"))]
	checks.append({"label": "Roster-required lines have start and end time", "complete": not missing_time, "details": missing_time})

	missing_skills = [_line_label(row) for row in lines if row.get("requires_roster") and not row.get("worker_skill_requirements")]
	checks.append({"label": "Roster-required lines have worker skill requirements", "complete": not missing_skills, "details": missing_skills})

	missing_house = [_line_label(row) for row in lines if row.get("requires_house") and not row.get("default_house")]
	checks.append({"label": "House-required lines have default house", "complete": not missing_house, "details": missing_house})

	missing_sil = [
		_line_label(row)
		for row in lines
		if row.get("service_code") == "SIL" and (not row.get("support_ratio") or not row.get("overnight_model"))
	]
	checks.append({"label": "SIL lines have support ratio and overnight model", "complete": not missing_sil, "details": missing_sil})

	missing_clinical = [
		_line_label(row)
		for row in lines
		if row.get("requires_clinical_review") and not row.get("clinical_review_complete")
	]
	checks.append({"label": "Clinical-required lines have clinical review complete", "complete": not missing_clinical, "details": missing_clinical})

	missing_line_ready = [_line_label(row) for row in lines if row.get("requires_roster") and not row.get("line_ready_for_roster_build")]
	checks.append({"label": "Roster-required lines marked line ready for roster build", "complete": not missing_line_ready, "details": missing_line_ready})

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
		"roster_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)

	if _field_exists(ROSTER_REQUEST, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(ROSTER_REQUEST, "roster_build_ready"):
		doc.roster_build_ready = 1 if summary["roster_ready"] else 0

	targets = [
		(CRM_DEAL, doc.get("crm_deal")),
		(HANDOVER, doc.get("handover")),
		(FINANCE_ONBOARDING, doc.get("finance_onboarding")),
		(OPERATIONS_SETUP, doc.get("operations_setup")),
		(SCHEDULE_DRAFT, doc.get("service_schedule_draft")),
		(INTAKE, doc.get("participant_intake")),
	]

	for doctype, name in targets:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_roster_build_request", doc.name)
		_db_set_if_field(doctype, name, "roster_build_status", doc.status)
		_db_set_if_field(doctype, name, "roster_build_ready", 1 if summary["roster_ready"] else 0)

	return summary


@frappe.whitelist()
def create_roster_build_request_from_schedule_draft(schedule_draft):
	_check_role()

	if not schedule_draft:
		frappe.throw(_("NDIS CRM Service Schedule Draft is required."))

	if not frappe.db.exists(SCHEDULE_DRAFT, schedule_draft):
		frappe.throw(_("NDIS CRM Service Schedule Draft {0} was not found.").format(schedule_draft))

	existing = _existing_request_for_schedule(schedule_draft)
	if existing:
		return {
			"doctype": ROSTER_REQUEST,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Roster Build Request returned.",
		}

	schedule_doc = frappe.get_doc(SCHEDULE_DRAFT, schedule_draft)

	request = frappe.new_doc(ROSTER_REQUEST)
	request.status = "Draft"
	request.service_schedule_draft = schedule_doc.name
	request.operations_setup = schedule_doc.get("operations_setup")
	request.finance_onboarding = schedule_doc.get("finance_onboarding")
	request.handover = schedule_doc.get("handover")
	request.crm_deal = schedule_doc.get("crm_deal")
	request.crm_lead = schedule_doc.get("crm_lead")
	request.participant_intake = schedule_doc.get("participant_intake")
	request.participant_customer = schedule_doc.get("participant_customer")
	request.ndis_financial_profile = schedule_doc.get("ndis_financial_profile")
	request.participant_name = schedule_doc.get("participant_name") or schedule_doc.get("participant_customer") or schedule_doc.name
	request.ndis_number = schedule_doc.get("ndis_number")
	request.plan_start_date = schedule_doc.get("plan_start_date")
	request.plan_end_date = schedule_doc.get("plan_end_date")
	request.target_start_date = schedule_doc.get("target_start_date")
	request.target_roster_build_date = schedule_doc.get("target_start_date")
	request.schedule_owner = schedule_doc.get("schedule_owner")
	request.operations_owner = schedule_doc.get("operations_owner")
	request.rostering_owner = schedule_doc.get("rostering_owner") or frappe.session.user
	request.service_manager = schedule_doc.get("service_manager")
	request.clinical_owner = schedule_doc.get("clinical_owner")

	_set_if_field(request, "default_house", schedule_doc.get("default_house"))
	_set_if_field(request, "default_cost_center", schedule_doc.get("default_cost_center"))

	_append_lines_from_schedule(request, schedule_doc)

	summary = _calculate_readiness(request)
	request.readiness_percent = summary["readiness_percent"]
	request.roster_build_ready = 1 if summary["roster_ready"] else 0
	request.insert(ignore_permissions=False)
	_sync_summary_to_links(request)
	frappe.db.commit()

	return {
		"doctype": ROSTER_REQUEST,
		"name": request.name,
		"created": True,
		"message": "NDIS CRM Roster Build Request created successfully.",
	}


@frappe.whitelist()
def create_roster_build_request_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))

	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_request_for_deal(deal)
	if existing:
		return {
			"doctype": ROSTER_REQUEST,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Roster Build Request returned.",
		}

	schedule_draft = _get_schedule_for_deal(deal)
	if not schedule_draft:
		try:
			from ndis_crm.phase8_service_schedule import create_service_schedule_from_crm_deal

			result = create_service_schedule_from_crm_deal(deal)
			schedule_draft = result.get("name")
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Service Schedule Draft before creating Roster Build Request."))

	return create_roster_build_request_from_schedule_draft(schedule_draft)


@frappe.whitelist()
def validate_roster_build_readiness(roster_build_request):
	_check_role()

	doc = frappe.get_doc(ROSTER_REQUEST, roster_build_request)
	for row in doc.get("request_lines") or []:
		_normalize_line_defaults(row)

	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Roster build readiness validated.",
	}


@frappe.whitelist()
def mark_ready_for_roster_build(roster_build_request):
	_check_role()

	doc = frappe.get_doc(ROSTER_REQUEST, roster_build_request)
	for row in doc.get("request_lines") or []:
		_normalize_line_defaults(row)

	summary = _calculate_readiness(doc)
	if not summary["roster_ready"]:
		frappe.throw(_("Cannot mark Ready for Roster Build. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Ready for Roster Build"
	doc.readiness_percent = summary["readiness_percent"]
	doc.roster_build_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": ROSTER_REQUEST,
		"name": doc.name,
		"message": "Roster Build Request marked Ready for Roster Build.",
	}


@frappe.whitelist()
def mark_accepted_by_rostering(roster_build_request):
	_check_role()

	doc = frappe.get_doc(ROSTER_REQUEST, roster_build_request)
	for row in doc.get("request_lines") or []:
		_normalize_line_defaults(row)

	summary = _calculate_readiness(doc)
	if not summary["roster_ready"]:
		frappe.throw(_("Cannot mark Accepted by Rostering. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Accepted by Rostering"
	doc.readiness_percent = summary["readiness_percent"]
	doc.roster_build_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": ROSTER_REQUEST,
		"name": doc.name,
		"message": "Roster Build Request accepted by rostering.",
	}


@frappe.whitelist()
def mark_roster_build_request_complete(roster_build_request):
	_check_role()

	doc = frappe.get_doc(ROSTER_REQUEST, roster_build_request)
	for row in doc.get("request_lines") or []:
		_normalize_line_defaults(row)

	summary = _calculate_readiness(doc)
	if not summary["roster_ready"]:
		frappe.throw(_("Cannot complete Roster Build Request. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Roster Build Complete"
	doc.readiness_percent = summary["readiness_percent"]
	doc.roster_build_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": ROSTER_REQUEST,
		"name": doc.name,
		"message": "Roster Build Request marked complete.",
	}


def validate_roster_build_request(doc, method=None):
	for row in doc.get("request_lines") or []:
		_normalize_line_defaults(row)

	summary = _calculate_readiness(doc)

	if _field_exists(ROSTER_REQUEST, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(ROSTER_REQUEST, "roster_build_ready"):
		doc.roster_build_ready = 1 if summary["roster_ready"] else 0

	if doc.status in READY_STATUSES and not summary["roster_ready"]:
		frappe.throw(_("Cannot set Roster Build Request to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))


def on_roster_build_request_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Roster Build Request Summary Sync Failed")


def validate_crm_deal_phase9(doc, method=None):
	if doc.status != "Won / Active Client":
		return

	roster_required = 1
	if _field_exists(CRM_DEAL, "ndis_roster_build_request_required"):
		roster_required = doc.get("ndis_roster_build_request_required")

	if not roster_required:
		return

	roster_request = doc.get("ndis_roster_build_request") if _field_exists(CRM_DEAL, "ndis_roster_build_request") else None
	if not roster_request:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Roster Build Request must be created and accepted."))

	status = frappe.db.get_value(ROSTER_REQUEST, roster_request, "status")
	ready = frappe.db.get_value(ROSTER_REQUEST, roster_request, "roster_build_ready")
	if status not in ACCEPTED_STATUSES or not ready:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Roster Build Request must be Accepted by Rostering or Roster Build Complete."))


def validate_crm_deal_phase9_combined(doc, method=None):
	"""
	Preserve Phase 2-8 validator chain, then add Phase 9 roster build request validation.
	"""
	try:
		from ndis_crm.phase8_service_schedule import validate_crm_deal_phase8_combined

		validate_crm_deal_phase8_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase7_operations_setup import validate_crm_deal_phase7_combined

			validate_crm_deal_phase7_combined(doc, method)
		except ImportError:
			try:
				from ndis_crm.phase5_finance_onboarding import validate_crm_deal_phase5_combined

				validate_crm_deal_phase5_combined(doc, method)
			except ImportError:
				pass

	validate_crm_deal_phase9(doc, method)


def phase9_health_check():
	print("---- NDIS CRM Phase 9 Health Check ----")

	for dt in [
		ROSTER_REQUEST_LINE,
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

	for dt in [
		PLAN_BUDGET,
		SERVICE_BOOKING,
		NDIS_SERVICE_TYPE,
		NDIS_SUPPORT_ITEM,
		NDIS_HOUSE,
		FINANCE_PROFILE,
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

	for field in [
		"ndis_roster_build_request_required",
		"ndis_roster_build_request",
		"roster_build_status",
		"roster_build_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, INTAKE]:
		for field in [
			"ndis_roster_build_request",
			"roster_build_status",
			"roster_build_ready",
		]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")

	print("NDIS CRM Roster Build Request records:", frappe.db.count(ROSTER_REQUEST) if _doctype_exists(ROSTER_REQUEST) else 0)
	print("CRM Deal Phase 9 combined validator should be active through hooks.py.")
	print("---- End Phase 9 Health Check ----")
