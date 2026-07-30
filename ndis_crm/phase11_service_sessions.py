import frappe
from frappe import _
from frappe.utils import add_days, date_diff, getdate, nowdate


CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
ROSTER_REQUEST = "NDIS CRM Roster Build Request"
SERVICE_FILE = "NDIS Participant Service File"
SERVICE_FILE_SERVICE = "NDIS Participant Service File Service"

SESSION_DRAFT = "NDIS CRM Service Session Draft"
SESSION_DRAFT_LINE = "NDIS CRM Service Session Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Service Delivery", "Session Draft Approved"]
APPROVED_STATUSES = ["Session Draft Approved"]
ACTIVE_SERVICE_FILE_STATUSES = ["Active Service File"]

WEEKDAY_MAP = {
	"monday": 0,
	"mon": 0,
	"tuesday": 1,
	"tue": 1,
	"wednesday": 2,
	"wed": 2,
	"thursday": 3,
	"thu": 3,
	"friday": 4,
	"fri": 4,
	"saturday": 5,
	"sat": 5,
	"sunday": 6,
	"sun": 6,
}

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
		frappe.throw(_("You do not have permission to perform this NDIS service session action."))


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


def _existing_session_draft_for_service_file(service_file):
	if not _doctype_exists(SESSION_DRAFT):
		return None

	if _field_exists(SERVICE_FILE, "ndis_service_session_draft"):
		existing = frappe.db.get_value(SERVICE_FILE, service_file, "ndis_service_session_draft")
		if existing:
			return existing

	return frappe.db.get_value(SESSION_DRAFT, {"participant_service_file": service_file}, "name")


def _existing_session_draft_for_deal(deal):
	if not _doctype_exists(SESSION_DRAFT):
		return None

	if _field_exists(CRM_DEAL, "ndis_service_session_draft"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_service_session_draft")
		if existing:
			return existing

	return frappe.db.get_value(SESSION_DRAFT, {"crm_deal": deal}, "name")


def _get_service_file_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_participant_service_file"):
		service_file = frappe.db.get_value(CRM_DEAL, deal, "ndis_participant_service_file")
		if service_file:
			return service_file

	if _doctype_exists(SERVICE_FILE):
		return frappe.db.get_value(SERVICE_FILE, {"crm_deal": deal}, "name")

	return None


def _is_service_file_active(service_file):
	if not service_file or not frappe.db.exists(SERVICE_FILE, service_file):
		return False

	status, ready = frappe.db.get_value(SERVICE_FILE, service_file, ["status", "service_file_ready"])
	return status in ACTIVE_SERVICE_FILE_STATUSES and bool(ready)


def _is_session_draft_approved(session_draft):
	if not session_draft or not frappe.db.exists(SESSION_DRAFT, session_draft):
		return False

	status, ready = frappe.db.get_value(SESSION_DRAFT, session_draft, ["status", "session_draft_ready"])
	return status in APPROVED_STATUSES and bool(ready)


def _parse_days_of_week(days_text):
	if not days_text:
		return []

	parts = [
		part.strip().lower()
		for part in str(days_text).replace("/", ",").replace("|", ",").replace(";", ",").split(",")
		if part.strip()
	]
	days = []

	for part in parts:
		if part in WEEKDAY_MAP and WEEKDAY_MAP[part] not in days:
			days.append(WEEKDAY_MAP[part])

	return days


def _date_range(start_date, end_date):
	start = getdate(start_date)
	end = getdate(end_date)
	total_days = date_diff(end, start)

	if total_days < 0:
		frappe.throw(_("Generation End Date cannot be before Generation Start Date."))

	for offset in range(total_days + 1):
		yield add_days(start, offset)


def _default_generation_dates(service_file_doc, weeks=4):
	start = service_file_doc.get("service_commencement_date") or service_file_doc.get("plan_start_date") or nowdate()
	end = add_days(getdate(start), (int(weeks or 4) * 7) - 1)
	plan_end = service_file_doc.get("plan_end_date")

	if plan_end and getdate(end) > getdate(plan_end):
		end = getdate(plan_end)

	return getdate(start), getdate(end)


def _service_row_active(row):
	return row.get("service_status") in ["Ready to Commence", "Active"]


def _should_include_service_row(row):
	if not row.get("requires_roster"):
		return False
	if not _service_row_active(row):
		return False
	return True


def _session_exists(draft_name, service_line, session_date, start_time):
	return frappe.db.exists(
		SESSION_DRAFT_LINE,
		{
			"parent": draft_name,
			"parenttype": SESSION_DRAFT,
			"service_line": service_line,
			"session_date": session_date,
			"planned_start_time": start_time,
		},
	)


def _append_session_line(draft_doc, service_row, session_date):
	if draft_doc.name and _session_exists(
		draft_doc.name,
		service_row.get("service_line"),
		session_date,
		service_row.get("start_time"),
	):
		return False

	planned_hours = service_row.get("hours_per_shift") or 0
	workers_required = service_row.get("workers_required") or 1

	try:
		estimated_worker_hours = round(float(planned_hours) * float(workers_required), 2)
	except Exception:
		estimated_worker_hours = 0

	draft_doc.append(
		"session_lines",
		{
			"service_line": service_row.get("service_line"),
			"service_code": service_row.get("service_code"),
			"service_model": service_row.get("service_model"),
			"service_status": service_row.get("service_status"),
			"session_date": session_date,
			"planned_start_time": service_row.get("start_time"),
			"planned_end_time": service_row.get("end_time"),
			"planned_hours": planned_hours,
			"workers_required": workers_required,
			"estimated_worker_hours": estimated_worker_hours,
			"frequency": service_row.get("frequency"),
			"days_of_week": service_row.get("days_of_week"),
			"finance_service_type": service_row.get("finance_service_type"),
			"support_item": service_row.get("support_item"),
			"plan_budget": service_row.get("plan_budget"),
			"service_booking": service_row.get("service_booking"),
			"default_house": service_row.get("default_house"),
			"delivery_location": service_row.get("delivery_location"),
			"support_ratio": service_row.get("support_ratio"),
			"overnight_model": service_row.get("overnight_model"),
			"requires_roster": service_row.get("requires_roster"),
			"requires_house": service_row.get("requires_house"),
			"requires_clinical_review": service_row.get("requires_clinical_review"),
			"clinical_review_complete": service_row.get("clinical_review_complete"),
			"transport_required": service_row.get("transport_required"),
			"worker_skill_requirements": service_row.get("worker_skill_requirements"),
			"clinical_risk_notes": service_row.get("clinical_risk_notes"),
			"roster_pattern_notes": service_row.get("roster_pattern_notes"),
			"billing_precheck_required": 1,
			"billing_precheck_ready": 1 if service_row.get("service_booking") and service_row.get("support_item") else 0,
			"line_ready_for_delivery": 0,
			"session_status": "Draft",
			"notes": service_row.get("service_notes"),
		},
	)
	return True


def _generate_lines_from_service_file(draft_doc, service_file_doc, start_date, end_date):
	created = 0

	for service_row in service_file_doc.get("services") or []:
		if not _should_include_service_row(service_row):
			continue

		frequency = service_row.get("frequency") or "Weekly"

		if frequency == "As Required":
			if _append_session_line(draft_doc, service_row, start_date):
				created += 1
			continue

		if frequency == "Once-off":
			session_date = service_row.get("service_start_date") or start_date
			if getdate(start_date) <= getdate(session_date) <= getdate(end_date):
				if _append_session_line(draft_doc, service_row, getdate(session_date)):
					created += 1
			continue

		allowed_days = _parse_days_of_week(service_row.get("days_of_week"))
		if frequency in ["Weekly", "Fortnightly"] and not allowed_days:
			continue

		for current_date in _date_range(start_date, end_date):
			current_weekday = getdate(current_date).weekday()
			include = False

			if frequency == "Daily":
				include = True
			elif frequency == "Weekly":
				include = current_weekday in allowed_days
			elif frequency == "Fortnightly":
				weeks_from_start = date_diff(current_date, start_date) // 7
				include = current_weekday in allowed_days and weeks_from_start % 2 == 0
			elif frequency == "Monthly":
				service_start = service_row.get("service_start_date") or start_date
				include = getdate(current_date).day == getdate(service_start).day

			if include and _append_session_line(draft_doc, service_row, current_date):
				created += 1

	return created


def _line_label(row):
	return row.get("service_line") or row.get("service_code") or row.name


def _calculate_readiness(doc):
	checks = [
		{"label": "Participant Service File linked", "complete": bool(doc.get("participant_service_file"))},
		{"label": "Participant Service File active", "complete": _is_service_file_active(doc.get("participant_service_file"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Session Owner assigned", "complete": bool(doc.get("session_owner"))},
		{"label": "Generation Start Date entered", "complete": bool(doc.get("generation_start_date"))},
		{"label": "Generation End Date entered", "complete": bool(doc.get("generation_end_date"))},
	]

	lines = doc.get("session_lines") or []
	checks.append({"label": "At least one session draft line exists", "complete": bool(lines)})

	missing_date = [_line_label(row) for row in lines if not row.get("session_date")]
	checks.append({"label": "All session lines have session date", "complete": not missing_date, "details": missing_date})

	missing_time = [
		_line_label(row)
		for row in lines
		if not row.get("planned_start_time") or not row.get("planned_end_time")
	]
	checks.append({"label": "All session lines have planned start/end time", "complete": not missing_time, "details": missing_time})

	missing_hours = [
		_line_label(row)
		for row in lines
		if not row.get("planned_hours") or not row.get("workers_required")
	]
	checks.append({"label": "All session lines have planned hours and workers required", "complete": not missing_hours, "details": missing_hours})

	missing_finance = [
		_line_label(row)
		for row in lines
		if not row.get("support_item") or not row.get("service_booking")
	]
	checks.append({"label": "All session lines have support item and service booking", "complete": not missing_finance, "details": missing_finance})

	missing_house = [
		_line_label(row)
		for row in lines
		if row.get("requires_house") and not row.get("default_house")
	]
	checks.append({"label": "House-required session lines have default house", "complete": not missing_house, "details": missing_house})

	missing_clinical = [
		_line_label(row)
		for row in lines
		if row.get("requires_clinical_review") and not row.get("clinical_review_complete")
	]
	checks.append({
		"label": "Clinical-required session lines have clinical review complete",
		"complete": not missing_clinical,
		"details": missing_clinical,
	})

	missing_skills = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster") and not row.get("worker_skill_requirements")
	]
	checks.append({
		"label": "Roster-required session lines have worker skill requirements",
		"complete": not missing_skills,
		"details": missing_skills,
	})

	not_billing_ready = [
		_line_label(row)
		for row in lines
		if row.get("billing_precheck_required") and not row.get("billing_precheck_ready")
	]
	checks.append({
		"label": "Billing precheck-ready flags are complete",
		"complete": not not_billing_ready,
		"details": not_billing_ready,
	})

	not_line_ready = [_line_label(row) for row in lines if not row.get("line_ready_for_delivery")]
	checks.append({"label": "All session lines marked ready for delivery", "complete": not not_line_ready, "details": not_line_ready})

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
		"session_draft_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)

	if _field_exists(SESSION_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(SESSION_DRAFT, "session_draft_ready"):
		doc.session_draft_ready = 1 if summary["session_draft_ready"] else 0

	if _field_exists(SESSION_DRAFT, "session_line_count"):
		doc.session_line_count = len(doc.get("session_lines") or [])

	targets = [
		(CRM_DEAL, doc.get("crm_deal")),
		(HANDOVER, doc.get("handover")),
		(FINANCE_ONBOARDING, doc.get("finance_onboarding")),
		(OPERATIONS_SETUP, doc.get("operations_setup")),
		(SCHEDULE_DRAFT, doc.get("service_schedule_draft")),
		(ROSTER_REQUEST, doc.get("roster_build_request")),
		(SERVICE_FILE, doc.get("participant_service_file")),
		(INTAKE, doc.get("participant_intake")),
	]

	for doctype, name in targets:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_service_session_draft", doc.name)
		_db_set_if_field(doctype, name, "service_session_status", doc.status)
		_db_set_if_field(doctype, name, "service_session_ready", 1 if summary["session_draft_ready"] else 0)

	return summary


@frappe.whitelist()
def create_service_session_draft_from_service_file(service_file, weeks=4):
	_check_role()

	if not service_file:
		frappe.throw(_("NDIS Participant Service File is required."))

	if not frappe.db.exists(SERVICE_FILE, service_file):
		frappe.throw(_("NDIS Participant Service File {0} was not found.").format(service_file))

	existing = _existing_session_draft_for_service_file(service_file)
	if existing:
		return {
			"doctype": SESSION_DRAFT,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Service Session Draft returned.",
		}

	service_file_doc = frappe.get_doc(SERVICE_FILE, service_file)
	start_date, end_date = _default_generation_dates(service_file_doc, weeks=weeks)

	doc = frappe.new_doc(SESSION_DRAFT)
	doc.status = "Draft"
	doc.participant_service_file = service_file_doc.name
	doc.roster_build_request = service_file_doc.get("roster_build_request")
	doc.service_schedule_draft = service_file_doc.get("service_schedule_draft")
	doc.operations_setup = service_file_doc.get("operations_setup")
	doc.finance_onboarding = service_file_doc.get("finance_onboarding")
	doc.handover = service_file_doc.get("handover")
	doc.crm_deal = service_file_doc.get("crm_deal")
	doc.crm_lead = service_file_doc.get("crm_lead")
	doc.participant_intake = service_file_doc.get("participant_intake")
	doc.participant_customer = service_file_doc.get("participant_customer")
	doc.ndis_financial_profile = service_file_doc.get("ndis_financial_profile")
	doc.participant_name = service_file_doc.get("participant_name") or service_file_doc.get("participant_customer") or service_file_doc.name
	doc.ndis_number = service_file_doc.get("ndis_number")
	doc.plan_start_date = service_file_doc.get("plan_start_date")
	doc.plan_end_date = service_file_doc.get("plan_end_date")
	doc.generation_start_date = start_date
	doc.generation_end_date = end_date
	doc.session_owner = frappe.session.user
	doc.operations_owner = service_file_doc.get("operations_owner")
	doc.rostering_owner = service_file_doc.get("rostering_owner")
	doc.service_manager = service_file_doc.get("service_manager")
	doc.clinical_owner = service_file_doc.get("clinical_owner")

	_set_if_field(doc, "default_house", service_file_doc.get("default_house"))
	_set_if_field(doc, "default_cost_center", service_file_doc.get("default_cost_center"))

	created_count = _generate_lines_from_service_file(doc, service_file_doc, start_date, end_date)
	if _field_exists(SESSION_DRAFT, "session_line_count"):
		doc.session_line_count = created_count

	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.session_draft_ready = 1 if summary["session_draft_ready"] else 0

	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()

	return {
		"doctype": SESSION_DRAFT,
		"name": doc.name,
		"created": True,
		"session_line_count": created_count,
		"message": "NDIS CRM Service Session Draft created successfully.",
	}


@frappe.whitelist()
def create_service_session_draft_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))

	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_session_draft_for_deal(deal)
	if existing:
		return {
			"doctype": SESSION_DRAFT,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Service Session Draft returned.",
		}

	service_file = _get_service_file_for_deal(deal)
	if not service_file:
		try:
			from ndis_crm.phase10_service_file import create_service_file_from_crm_deal

			result = create_service_file_from_crm_deal(deal)
			service_file = result.get("name")
		except ImportError:
			frappe.throw(_("Please create NDIS Participant Service File before creating Service Session Draft."))

	return create_service_session_draft_from_service_file(service_file)


@frappe.whitelist()
def generate_session_lines(session_draft):
	_check_role()

	if not session_draft:
		frappe.throw(_("NDIS CRM Service Session Draft is required."))

	doc = frappe.get_doc(SESSION_DRAFT, session_draft)
	if not doc.get("participant_service_file"):
		frappe.throw(_("Participant Service File is required."))

	service_file_doc = frappe.get_doc(SERVICE_FILE, doc.participant_service_file)
	start_date = doc.get("generation_start_date")
	end_date = doc.get("generation_end_date")

	if not start_date or not end_date:
		start_date, end_date = _default_generation_dates(service_file_doc)
		doc.generation_start_date = start_date
		doc.generation_end_date = end_date

	created_count = _generate_lines_from_service_file(doc, service_file_doc, start_date, end_date)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"created_count": created_count,
		"summary": summary,
		"message": f"Session lines generated. Created: {created_count}.",
	}


@frappe.whitelist()
def validate_session_draft_readiness(session_draft):
	_check_role()

	doc = frappe.get_doc(SESSION_DRAFT, session_draft)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Service session draft readiness validated.",
	}


@frappe.whitelist()
def mark_ready_for_service_delivery(session_draft):
	_check_role()

	doc = frappe.get_doc(SESSION_DRAFT, session_draft)
	summary = _calculate_readiness(doc)
	if not summary["session_draft_ready"]:
		frappe.throw(
			_("Cannot mark Ready for Service Delivery. Incomplete items: {0}").format("; ".join(summary["incomplete"]))
		)

	doc.status = "Ready for Service Delivery"
	doc.readiness_percent = summary["readiness_percent"]
	doc.session_draft_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": SESSION_DRAFT,
		"name": doc.name,
		"message": "Service Session Draft marked Ready for Service Delivery.",
	}


@frappe.whitelist()
def approve_session_draft(session_draft):
	_check_role()

	doc = frappe.get_doc(SESSION_DRAFT, session_draft)
	summary = _calculate_readiness(doc)
	if not summary["session_draft_ready"]:
		frappe.throw(_("Cannot approve Service Session Draft. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Session Draft Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.session_draft_ready = 1

	for row in doc.get("session_lines") or []:
		if row.get("session_status") == "Draft":
			row.session_status = "Approved"

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": SESSION_DRAFT,
		"name": doc.name,
		"message": "Service Session Draft approved.",
	}


def validate_session_draft(doc, method=None):
	summary = _calculate_readiness(doc)

	if _field_exists(SESSION_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(SESSION_DRAFT, "session_draft_ready"):
		doc.session_draft_ready = 1 if summary["session_draft_ready"] else 0

	if _field_exists(SESSION_DRAFT, "session_line_count"):
		doc.session_line_count = len(doc.get("session_lines") or [])

	if doc.status in READY_STATUSES and not summary["session_draft_ready"]:
		frappe.throw(
			_("Cannot set Service Session Draft to {0}. Incomplete items: {1}").format(
				doc.status,
				"; ".join(summary["incomplete"]),
			)
		)


def on_session_draft_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Service Session Draft Summary Sync Failed")


def validate_crm_deal_phase11(doc, method=None):
	if doc.status != "Won / Active Client":
		return

	session_draft_required = 1
	if _field_exists(CRM_DEAL, "ndis_service_session_draft_required"):
		session_draft_required = doc.get("ndis_service_session_draft_required")

	if not session_draft_required:
		return

	session_draft = doc.get("ndis_service_session_draft") if _field_exists(CRM_DEAL, "ndis_service_session_draft") else None
	if not session_draft:
		frappe.throw(
			_("Cannot mark CRM Deal as Won / Active Client. NDIS Service Session Draft must be created and approved.")
		)

	if not _is_session_draft_approved(session_draft):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Service Session Draft must be approved."))


def validate_crm_deal_phase11_combined(doc, method=None):
	try:
		from ndis_crm.phase10_service_file import validate_crm_deal_phase10_combined

		validate_crm_deal_phase10_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase9_roster_build_request import validate_crm_deal_phase9_combined

			validate_crm_deal_phase9_combined(doc, method)
		except ImportError:
			try:
				from ndis_crm.phase8_service_schedule import validate_crm_deal_phase8_combined

				validate_crm_deal_phase8_combined(doc, method)
			except ImportError:
				pass

	validate_crm_deal_phase11(doc, method)


def phase11_health_check():
	print("---- NDIS CRM Phase 11 Health Check ----")

	for dt in [
		SESSION_DRAFT_LINE,
		SESSION_DRAFT,
		SERVICE_FILE,
		SERVICE_FILE_SERVICE,
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
		"ndis_service_session_draft_required",
		"ndis_service_session_draft",
		"service_session_status",
		"service_session_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, SERVICE_FILE, INTAKE]:
		for field in [
			"ndis_service_session_draft",
			"service_session_status",
			"service_session_ready",
		]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")

	print("NDIS CRM Service Session Draft records:", frappe.db.count(SESSION_DRAFT) if _doctype_exists(SESSION_DRAFT) else 0)
	print("CRM Deal Phase 11 combined validator should be active through hooks.py.")
	print("---- End Phase 11 Health Check ----")
