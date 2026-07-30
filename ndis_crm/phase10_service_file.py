import frappe
from frappe import _


CRM_DEAL = "CRM Deal"
CRM_LEAD = "CRM Lead"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
ROSTER_REQUEST = "NDIS CRM Roster Build Request"

SERVICE_FILE = "NDIS Participant Service File"
SERVICE_FILE_SERVICE = "NDIS Participant Service File Service"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Activation", "Active Service File"]
ACTIVE_STATUSES = ["Active Service File"]
ROSTER_ACCEPTED_STATUSES = ["Accepted by Rostering", "Roster Build Complete"]

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
		frappe.throw(_("You do not have permission to perform this participant service file action."))


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


def _existing_service_file_for_deal(deal):
	if not _doctype_exists(SERVICE_FILE):
		return None

	if _field_exists(CRM_DEAL, "ndis_participant_service_file"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_participant_service_file")
		if existing:
			return existing

	return frappe.db.get_value(SERVICE_FILE, {"crm_deal": deal}, "name")


def _existing_service_file_for_roster_request(roster_request):
	if not _doctype_exists(SERVICE_FILE):
		return None

	if _field_exists(ROSTER_REQUEST, "ndis_participant_service_file"):
		existing = frappe.db.get_value(ROSTER_REQUEST, roster_request, "ndis_participant_service_file")
		if existing:
			return existing

	return frappe.db.get_value(SERVICE_FILE, {"roster_build_request": roster_request}, "name")


def _get_roster_request_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_roster_build_request"):
		request = frappe.db.get_value(CRM_DEAL, deal, "ndis_roster_build_request")
		if request:
			return request

	if _doctype_exists(ROSTER_REQUEST):
		return frappe.db.get_value(ROSTER_REQUEST, {"crm_deal": deal}, "name")

	return None


def _is_roster_request_accepted(roster_request):
	if not roster_request or not frappe.db.exists(ROSTER_REQUEST, roster_request):
		return False

	status, ready = frappe.db.get_value(
		ROSTER_REQUEST,
		roster_request,
		["status", "roster_build_ready"],
	)
	return status in ROSTER_ACCEPTED_STATUSES and bool(ready)


def _row_label(row):
	return row.get("service_line") or row.get("service_code") or row.name


def _append_service_if_missing(service_file, row_data):
	if not row_data.get("service_line"):
		return

	existing = {row.service_line for row in service_file.get("services") or []}
	if row_data.get("service_line") in existing:
		return

	service_file.append("services", row_data)


def _base_service_row(service_line):
	if not service_line:
		return {}

	service_code = frappe.db.get_value("NDIS Service Line", service_line, "service_code") or service_line
	budget_type = frappe.db.get_value("NDIS Service Line", service_line, "budget_type")

	return {
		"service_line": service_line,
		"service_code": service_code,
		"budget_type": budget_type,
		"service_status": "Pending Activation",
	}


def _apply_common_service_fields(target, source):
	field_map = {
		"service_model": "service_model",
		"finance_service_type": "finance_service_type",
		"support_item": "support_item",
		"plan_budget": "plan_budget",
		"service_booking": "service_booking",
		"default_house": "default_house",
		"delivery_location": "delivery_location",
		"support_ratio": "support_ratio",
		"overnight_model": "overnight_model",
		"requires_roster": "requires_roster",
		"requires_house": "requires_house",
		"requires_clinical_review": "requires_clinical_review",
		"clinical_review_complete": "clinical_review_complete",
		"transport_required": "transport_required",
		"worker_skill_requirements": "worker_skill_requirements",
		"clinical_risk_notes": "clinical_risk_notes",
		"roster_pattern_notes": "roster_pattern_notes",
		"frequency": "frequency",
		"days_of_week": "days_of_week",
		"shifts_per_week": "shifts_per_week",
		"hours_per_shift": "hours_per_shift",
		"estimated_weekly_hours": "estimated_weekly_hours",
		"workers_required": "workers_required",
		"estimated_worker_hours": "estimated_worker_hours",
		"start_time": "start_time",
		"end_time": "end_time",
	}

	for source_field, target_field in field_map.items():
		value = source.get(source_field)
		if value is not None:
			target[target_field] = value

	if source.get("start_date"):
		target["service_start_date"] = source.get("start_date")

	if source.get("end_date"):
		target["service_end_date"] = source.get("end_date")

	if source.get("notes"):
		target["service_notes"] = source.get("notes")

	return target


def _append_services_from_operations(service_file, operations_setup):
	if not operations_setup or not frappe.db.exists(OPERATIONS_SETUP, operations_setup):
		return

	setup_doc = frappe.get_doc(OPERATIONS_SETUP, operations_setup)
	for row in setup_doc.get("service_requirements") or []:
		data = _base_service_row(row.get("service_line"))
		data = _apply_common_service_fields(data, row)
		data["operations_setup_status"] = "Captured"
		_append_service_if_missing(service_file, data)


def _merge_service_rows(service_file, operations_setup=None, schedule_draft=None, roster_request=None):
	_append_services_from_operations(service_file, operations_setup)

	existing = {row.service_line: row for row in service_file.get("services") or []}
	if schedule_draft and frappe.db.exists(SCHEDULE_DRAFT, schedule_draft):
		schedule_doc = frappe.get_doc(SCHEDULE_DRAFT, schedule_draft)
		for row in schedule_doc.get("schedule_lines") or []:
			service_line = row.get("service_line")
			if service_line in existing:
				_apply_common_service_fields(existing[service_line], row)
				existing[service_line].schedule_status = schedule_doc.status
				existing[service_line].schedule_ready = 1 if schedule_doc.get("schedule_ready") else 0
			else:
				data = _base_service_row(service_line)
				data = _apply_common_service_fields(data, row)
				data["schedule_status"] = schedule_doc.status
				data["schedule_ready"] = 1 if schedule_doc.get("schedule_ready") else 0
				_append_service_if_missing(service_file, data)

	existing = {row.service_line: row for row in service_file.get("services") or []}
	if roster_request and frappe.db.exists(ROSTER_REQUEST, roster_request):
		request_doc = frappe.get_doc(ROSTER_REQUEST, roster_request)
		for row in request_doc.get("request_lines") or []:
			service_line = row.get("service_line")
			if service_line in existing:
				_apply_common_service_fields(existing[service_line], row)
				existing[service_line].roster_request_status = request_doc.status
				existing[service_line].roster_build_ready = 1 if request_doc.get("roster_build_ready") else 0
				if request_doc.status in ROSTER_ACCEPTED_STATUSES:
					existing[service_line].service_status = "Ready to Commence"
			else:
				data = _base_service_row(service_line)
				data = _apply_common_service_fields(data, row)
				data["roster_request_status"] = request_doc.status
				data["roster_build_ready"] = 1 if request_doc.get("roster_build_ready") else 0
				if request_doc.status in ROSTER_ACCEPTED_STATUSES:
					data["service_status"] = "Ready to Commence"
				_append_service_if_missing(service_file, data)


def _calculate_readiness(doc):
	checks = [
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "NDIS Financial Profile linked", "complete": bool(doc.get("ndis_financial_profile"))},
		{"label": "CRM Deal linked", "complete": bool(doc.get("crm_deal"))},
		{
			"label": "Roster Build Request accepted or complete",
			"complete": _is_roster_request_accepted(doc.get("roster_build_request")),
		},
		{"label": "Service File Owner assigned", "complete": bool(doc.get("service_file_owner"))},
		{"label": "Plan Start Date entered", "complete": bool(doc.get("plan_start_date"))},
		{"label": "Plan End Date entered", "complete": bool(doc.get("plan_end_date"))},
	]

	services = doc.get("services") or []
	checks.append({"label": "At least one service row exists", "complete": bool(services)})

	missing_start = [_row_label(row) for row in services if not row.get("service_start_date")]
	checks.append({"label": "All service rows have service start date", "complete": not missing_start, "details": missing_start})

	missing_status = [_row_label(row) for row in services if not row.get("service_status")]
	checks.append({"label": "All service rows have service status", "complete": not missing_status, "details": missing_status})

	missing_finance = [
		_row_label(row)
		for row in services
		if not row.get("finance_service_type") or not row.get("support_item")
	]
	checks.append({
		"label": "All service rows have finance service type and support item",
		"complete": not missing_finance,
		"details": missing_finance,
	})

	missing_booking = [
		_row_label(row)
		for row in services
		if row.get("requires_roster") and not row.get("service_booking")
	]
	checks.append({
		"label": "Roster-required services have service booking",
		"complete": not missing_booking,
		"details": missing_booking,
	})

	missing_roster_ready = [
		_row_label(row)
		for row in services
		if row.get("requires_roster") and not row.get("roster_build_ready")
	]
	checks.append({
		"label": "Roster-required services have accepted roster build",
		"complete": not missing_roster_ready,
		"details": missing_roster_ready,
	})

	missing_house = [
		_row_label(row)
		for row in services
		if row.get("requires_house") and not row.get("default_house")
	]
	checks.append({
		"label": "House-required services have default house",
		"complete": not missing_house,
		"details": missing_house,
	})

	missing_clinical = [
		_row_label(row)
		for row in services
		if row.get("requires_clinical_review") and not row.get("clinical_review_complete")
	]
	checks.append({
		"label": "Clinical-required services have clinical review complete",
		"complete": not missing_clinical,
		"details": missing_clinical,
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
			label += ": " + ", ".join([str(x) for x in row["details"] if x])
		incomplete.append(label)

	return {
		"total_checks": total,
		"complete_checks": complete,
		"readiness_percent": readiness_percent,
		"service_file_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)

	if _field_exists(SERVICE_FILE, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(SERVICE_FILE, "service_file_ready"):
		doc.service_file_ready = 1 if summary["service_file_ready"] else 0

	targets = [
		(CRM_DEAL, doc.get("crm_deal")),
		(HANDOVER, doc.get("handover")),
		(FINANCE_ONBOARDING, doc.get("finance_onboarding")),
		(OPERATIONS_SETUP, doc.get("operations_setup")),
		(SCHEDULE_DRAFT, doc.get("service_schedule_draft")),
		(ROSTER_REQUEST, doc.get("roster_build_request")),
		(INTAKE, doc.get("participant_intake")),
	]

	for doctype, name in targets:
		if not name:
			continue

		_db_set_if_field(doctype, name, "ndis_participant_service_file", doc.name)
		_db_set_if_field(doctype, name, "participant_service_file_status", doc.status)
		_db_set_if_field(doctype, name, "participant_service_file_ready", 1 if summary["service_file_ready"] else 0)

	return summary


@frappe.whitelist()
def create_service_file_from_roster_build_request(roster_build_request):
	_check_role()

	if not roster_build_request:
		frappe.throw(_("NDIS CRM Roster Build Request is required."))

	if not frappe.db.exists(ROSTER_REQUEST, roster_build_request):
		frappe.throw(_("NDIS CRM Roster Build Request {0} was not found.").format(roster_build_request))

	existing = _existing_service_file_for_roster_request(roster_build_request)
	if existing:
		return {
			"doctype": SERVICE_FILE,
			"name": existing,
			"created": False,
			"message": "Existing NDIS Participant Service File returned.",
		}

	request_doc = frappe.get_doc(ROSTER_REQUEST, roster_build_request)

	service_file = frappe.new_doc(SERVICE_FILE)
	service_file.status = "Draft"
	service_file.roster_build_request = request_doc.name
	service_file.service_schedule_draft = request_doc.get("service_schedule_draft")
	service_file.operations_setup = request_doc.get("operations_setup")
	service_file.finance_onboarding = request_doc.get("finance_onboarding")
	service_file.handover = request_doc.get("handover")
	service_file.crm_deal = request_doc.get("crm_deal")
	service_file.crm_lead = request_doc.get("crm_lead")
	service_file.participant_intake = request_doc.get("participant_intake")
	service_file.participant_customer = request_doc.get("participant_customer")
	service_file.ndis_financial_profile = request_doc.get("ndis_financial_profile")
	service_file.participant_name = request_doc.get("participant_name") or request_doc.get("participant_customer") or request_doc.name
	service_file.ndis_number = request_doc.get("ndis_number")
	service_file.plan_start_date = request_doc.get("plan_start_date")
	service_file.plan_end_date = request_doc.get("plan_end_date")
	service_file.service_commencement_date = request_doc.get("target_start_date")
	service_file.service_file_owner = frappe.session.user
	service_file.operations_owner = request_doc.get("operations_owner")
	service_file.rostering_owner = request_doc.get("rostering_owner")
	service_file.service_manager = request_doc.get("service_manager")
	service_file.clinical_owner = request_doc.get("clinical_owner")

	_set_if_field(service_file, "default_house", request_doc.get("default_house"))
	_set_if_field(service_file, "default_cost_center", request_doc.get("default_cost_center"))

	_merge_service_rows(
		service_file=service_file,
		operations_setup=request_doc.get("operations_setup"),
		schedule_draft=request_doc.get("service_schedule_draft"),
		roster_request=request_doc.name,
	)

	summary = _calculate_readiness(service_file)
	service_file.readiness_percent = summary["readiness_percent"]
	service_file.service_file_ready = 1 if summary["service_file_ready"] else 0

	service_file.insert(ignore_permissions=False)
	_sync_summary_to_links(service_file)
	frappe.db.commit()

	return {
		"doctype": SERVICE_FILE,
		"name": service_file.name,
		"created": True,
		"message": "NDIS Participant Service File created successfully.",
	}


@frappe.whitelist()
def create_service_file_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))

	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_service_file_for_deal(deal)
	if existing:
		return {
			"doctype": SERVICE_FILE,
			"name": existing,
			"created": False,
			"message": "Existing NDIS Participant Service File returned.",
		}

	roster_request = _get_roster_request_for_deal(deal)
	if not roster_request:
		try:
			from ndis_crm.phase9_roster_build_request import create_roster_build_request_from_crm_deal

			result = create_roster_build_request_from_crm_deal(deal)
			roster_request = result.get("name")
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Roster Build Request before creating Participant Service File."))

	return create_service_file_from_roster_build_request(roster_request)


@frappe.whitelist()
def validate_service_file_readiness(service_file):
	_check_role()

	doc = frappe.get_doc(SERVICE_FILE, service_file)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Participant Service File readiness validated.",
	}


@frappe.whitelist()
def mark_ready_for_activation(service_file):
	_check_role()

	doc = frappe.get_doc(SERVICE_FILE, service_file)
	summary = _calculate_readiness(doc)

	if not summary["service_file_ready"]:
		frappe.throw(
			_("Cannot mark Ready for Activation. Incomplete items: {0}").format("; ".join(summary["incomplete"]))
		)

	doc.status = "Ready for Activation"
	doc.readiness_percent = summary["readiness_percent"]
	doc.service_file_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": SERVICE_FILE,
		"name": doc.name,
		"message": "Participant Service File marked Ready for Activation.",
	}


@frappe.whitelist()
def activate_service_file(service_file):
	_check_role()

	doc = frappe.get_doc(SERVICE_FILE, service_file)
	summary = _calculate_readiness(doc)

	if not summary["service_file_ready"]:
		frappe.throw(
			_("Cannot activate Participant Service File. Incomplete items: {0}").format("; ".join(summary["incomplete"]))
		)

	doc.status = "Active Service File"
	doc.readiness_percent = summary["readiness_percent"]
	doc.service_file_ready = 1

	for row in doc.get("services") or []:
		if row.get("service_status") in ["Pending Activation", "Ready to Commence"]:
			row.service_status = "Active"

	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": SERVICE_FILE,
		"name": doc.name,
		"message": "Participant Service File activated.",
	}


def validate_service_file(doc, method=None):
	summary = _calculate_readiness(doc)

	if _field_exists(SERVICE_FILE, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(SERVICE_FILE, "service_file_ready"):
		doc.service_file_ready = 1 if summary["service_file_ready"] else 0

	if doc.status in READY_STATUSES and not summary["service_file_ready"]:
		frappe.throw(
			_("Cannot set Participant Service File to {0}. Incomplete items: {1}").format(
				doc.status,
				"; ".join(summary["incomplete"]),
			)
		)


def on_service_file_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS Participant Service File Summary Sync Failed")


def validate_crm_deal_phase10(doc, method=None):
	if doc.status != "Won / Active Client":
		return

	service_file_required = 1
	if _field_exists(CRM_DEAL, "ndis_participant_service_file_required"):
		service_file_required = doc.get("ndis_participant_service_file_required")

	if not service_file_required:
		return

	service_file = doc.get("ndis_participant_service_file") if _field_exists(CRM_DEAL, "ndis_participant_service_file") else None
	if not service_file:
		frappe.throw(
			_("Cannot mark CRM Deal as Won / Active Client. NDIS Participant Service File must be created and active.")
		)

	status, ready = frappe.db.get_value(SERVICE_FILE, service_file, ["status", "service_file_ready"])
	if status not in ACTIVE_STATUSES or not ready:
		frappe.throw(
			_("Cannot mark CRM Deal as Won / Active Client. NDIS Participant Service File must be Active Service File.")
		)


def validate_crm_deal_phase10_combined(doc, method=None):
	try:
		from ndis_crm.phase9_roster_build_request import validate_crm_deal_phase9_combined

		validate_crm_deal_phase9_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase8_service_schedule import validate_crm_deal_phase8_combined

			validate_crm_deal_phase8_combined(doc, method)
		except ImportError:
			try:
				from ndis_crm.phase7_operations_setup import validate_crm_deal_phase7_combined

				validate_crm_deal_phase7_combined(doc, method)
			except ImportError:
				pass

	validate_crm_deal_phase10(doc, method)


def phase10_health_check():
	print("---- NDIS CRM Phase 10 Health Check ----")

	for dt in [
		SERVICE_FILE_SERVICE,
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
		"ndis_participant_service_file_required",
		"ndis_participant_service_file",
		"participant_service_file_status",
		"participant_service_file_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, SCHEDULE_DRAFT, ROSTER_REQUEST, INTAKE]:
		for field in [
			"ndis_participant_service_file",
			"participant_service_file_status",
			"participant_service_file_ready",
		]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")

	print("NDIS Participant Service File records:", frappe.db.count(SERVICE_FILE) if _doctype_exists(SERVICE_FILE) else 0)
	print("CRM Deal Phase 10 combined validator should be active through hooks.py.")
	print("---- End Phase 10 Health Check ----")
