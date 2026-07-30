import frappe
from frappe import _


CRM_DEAL = "CRM Deal"
CRM_LEAD = "CRM Lead"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
OPERATIONS_REQUIREMENT = "NDIS CRM Operations Service Requirement"

SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
SCHEDULE_DRAFT_LINE = "NDIS CRM Service Schedule Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Roster Build", "Roster Build Started", "Schedule Approved"]
APPROVED_STATUSES = ["Schedule Approved"]

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
		frappe.throw(_("You do not have permission to perform this NDIS CRM service schedule action."))


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


def _existing_schedule_for_operations_setup(operations_setup):
	if not _doctype_exists(SCHEDULE_DRAFT):
		return None

	if _field_exists(OPERATIONS_SETUP, "ndis_service_schedule_draft"):
		existing = frappe.db.get_value(OPERATIONS_SETUP, operations_setup, "ndis_service_schedule_draft")
		if existing:
			return existing

	return frappe.db.get_value(SCHEDULE_DRAFT, {"operations_setup": operations_setup}, "name")


def _existing_schedule_for_deal(deal_name):
	if not _doctype_exists(SCHEDULE_DRAFT):
		return None

	if _field_exists(CRM_DEAL, "ndis_service_schedule_draft"):
		existing = frappe.db.get_value(CRM_DEAL, deal_name, "ndis_service_schedule_draft")
		if existing:
			return existing

	return frappe.db.get_value(SCHEDULE_DRAFT, {"crm_deal": deal_name}, "name")


def _get_operations_setup_for_deal(deal_name):
	if _field_exists(CRM_DEAL, "ndis_operations_setup"):
		setup = frappe.db.get_value(CRM_DEAL, deal_name, "ndis_operations_setup")
		if setup:
			return setup

	if _doctype_exists(OPERATIONS_SETUP):
		return frappe.db.get_value(OPERATIONS_SETUP, {"crm_deal": deal_name}, "name")

	return None


def _calculate_line_hours(line):
	try:
		shifts = float(line.get("shifts_per_week") or 0)
		hours = float(line.get("hours_per_shift") or 0)
		return round(shifts * hours, 2)
	except Exception:
		return 0


def _normalize_line_defaults(line):
	if line.get("shifts_per_week") and line.get("hours_per_shift"):
		line.estimated_weekly_hours = _calculate_line_hours(line)

	if line.get("workers_required") and line.get("estimated_weekly_hours"):
		try:
			line.estimated_worker_hours = round(
				float(line.workers_required) * float(line.estimated_weekly_hours),
				2,
			)
		except Exception:
			line.estimated_worker_hours = 0


def _append_schedule_line_if_missing(schedule_doc, row_data):
	existing = {row.service_line for row in schedule_doc.get("schedule_lines") or []}
	if row_data.get("service_line") in existing:
		return
	schedule_doc.append("schedule_lines", row_data)


def _build_line_from_operations_requirement(row, setup_doc):
	data = {
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"priority": row.get("priority"),
		"start_date": row.get("required_start_date") or setup_doc.get("target_start_date"),
		"end_date": setup_doc.get("plan_end_date"),
		"finance_service_type": row.get("finance_service_type"),
		"support_item": row.get("support_item"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"requires_roster": row.get("requires_roster"),
		"requires_house": row.get("requires_house"),
		"requires_clinical_review": row.get("requires_clinical_review"),
		"clinical_review_complete": row.get("clinical_review_complete"),
		"transport_required": row.get("transport_required"),
		"default_house": row.get("default_house") or setup_doc.get("default_house"),
		"delivery_location": row.get("delivery_location"),
		"support_ratio": row.get("support_ratio"),
		"overnight_model": row.get("overnight_model"),
		"frequency": row.get("frequency"),
		"shifts_per_week": row.get("shifts_per_week"),
		"hours_per_shift": row.get("hours_per_shift"),
		"start_time": row.get("preferred_start_time"),
		"end_time": row.get("preferred_end_time"),
		"worker_skill_requirements": row.get("worker_skill_requirements"),
		"roster_pattern_notes": row.get("roster_pattern_notes"),
		"clinical_risk_notes": row.get("clinical_risk_notes"),
		"status": "Draft",
		"notes": row.get("notes"),
	}

	if row.get("requires_roster"):
		data["workers_required"] = 1

	if row.get("estimated_weekly_hours"):
		data["estimated_weekly_hours"] = row.get("estimated_weekly_hours")
	elif row.get("shifts_per_week") and row.get("hours_per_shift"):
		data["estimated_weekly_hours"] = float(row.get("shifts_per_week") or 0) * float(row.get("hours_per_shift") or 0)

	if data.get("workers_required") and data.get("estimated_weekly_hours"):
		data["estimated_worker_hours"] = float(data.get("workers_required") or 0) * float(data.get("estimated_weekly_hours") or 0)

	return data


def _append_lines_from_operations_setup(schedule_doc, setup_doc):
	for row in setup_doc.get("service_requirements") or []:
		if not row.get("requires_roster") and row.get("service_model") == "Plan Management Admin":
			continue

		line = _build_line_from_operations_requirement(row, setup_doc)
		_append_schedule_line_if_missing(schedule_doc, line)


def _line_label(row):
	return row.get("service_line") or row.get("service_model") or row.name


def _calculate_readiness(doc):
	checks = [
		{"label": "Operations Setup linked", "complete": bool(doc.get("operations_setup"))},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Schedule Owner assigned", "complete": bool(doc.get("schedule_owner"))},
		{"label": "Target Start Date entered", "complete": bool(doc.get("target_start_date"))},
	]

	lines = doc.get("schedule_lines") or []
	checks.append({"label": "At least one schedule line exists", "complete": bool(lines)})

	missing_start_date = [_line_label(row) for row in lines if not row.get("start_date")]
	checks.append({
		"label": "All schedule lines have start date",
		"complete": not missing_start_date,
		"details": missing_start_date,
	})

	missing_end_date = [_line_label(row) for row in lines if not row.get("end_date")]
	checks.append({
		"label": "All schedule lines have end date",
		"complete": not missing_end_date,
		"details": missing_end_date,
	})

	missing_frequency = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster") and not row.get("frequency")
	]
	checks.append({
		"label": "Roster-required lines have frequency",
		"complete": not missing_frequency,
		"details": missing_frequency,
	})

	missing_weekly_days = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster")
		and row.get("frequency") in ["Weekly", "Fortnightly"]
		and not row.get("days_of_week")
	]
	checks.append({
		"label": "Weekly/fortnightly lines have days of week",
		"complete": not missing_weekly_days,
		"details": missing_weekly_days,
	})

	missing_shift_counts = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster")
		and (not row.get("shifts_per_week") or not row.get("hours_per_shift") or not row.get("workers_required"))
	]
	checks.append({
		"label": "Roster-required lines have shifts, hours and workers required",
		"complete": not missing_shift_counts,
		"details": missing_shift_counts,
	})

	missing_time = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster") and (not row.get("start_time") or not row.get("end_time"))
	]
	checks.append({
		"label": "Roster-required lines have start and end time",
		"complete": not missing_time,
		"details": missing_time,
	})

	missing_house = [_line_label(row) for row in lines if row.get("requires_house") and not row.get("default_house")]
	checks.append({
		"label": "House-required lines have default house",
		"complete": not missing_house,
		"details": missing_house,
	})

	missing_sil_detail = [
		_line_label(row)
		for row in lines
		if row.get("service_code") == "SIL" and (not row.get("support_ratio") or not row.get("overnight_model"))
	]
	checks.append({
		"label": "SIL lines have support ratio and overnight model",
		"complete": not missing_sil_detail,
		"details": missing_sil_detail,
	})

	missing_clinical = [
		_line_label(row)
		for row in lines
		if row.get("requires_clinical_review") and not row.get("clinical_review_complete")
	]
	checks.append({
		"label": "Clinical-required lines have clinical review complete",
		"complete": not missing_clinical,
		"details": missing_clinical,
	})

	missing_skills = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster") and not row.get("worker_skill_requirements")
	]
	checks.append({
		"label": "Roster-required lines have worker skill requirements",
		"complete": not missing_skills,
		"details": missing_skills,
	})

	not_ready_lines = [
		_line_label(row)
		for row in lines
		if row.get("requires_roster") and not row.get("ready_for_roster_build")
	]
	checks.append({
		"label": "Roster-required lines marked ready for roster build",
		"complete": not not_ready_lines,
		"details": not_ready_lines,
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
		"schedule_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)

	if _field_exists(SCHEDULE_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(SCHEDULE_DRAFT, "schedule_ready"):
		doc.schedule_ready = 1 if summary["schedule_ready"] else 0

	targets = [
		(CRM_DEAL, doc.get("crm_deal")),
		(HANDOVER, doc.get("handover")),
		(FINANCE_ONBOARDING, doc.get("finance_onboarding")),
		(OPERATIONS_SETUP, doc.get("operations_setup")),
		(INTAKE, doc.get("participant_intake")),
	]

	for doctype, name in targets:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_service_schedule_draft", doc.name)
		_db_set_if_field(doctype, name, "service_schedule_status", doc.status)
		_db_set_if_field(doctype, name, "service_schedule_ready", 1 if summary["schedule_ready"] else 0)

	return summary


@frappe.whitelist()
def create_service_schedule_from_operations_setup(operations_setup):
	_check_role()

	if not operations_setup:
		frappe.throw(_("NDIS CRM Operations Setup is required."))

	if not frappe.db.exists(OPERATIONS_SETUP, operations_setup):
		frappe.throw(_("NDIS CRM Operations Setup {0} was not found.").format(operations_setup))

	existing = _existing_schedule_for_operations_setup(operations_setup)
	if existing:
		return {
			"doctype": SCHEDULE_DRAFT,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Service Schedule Draft returned.",
		}

	setup_doc = frappe.get_doc(OPERATIONS_SETUP, operations_setup)

	schedule = frappe.new_doc(SCHEDULE_DRAFT)
	schedule.status = "Draft"
	schedule.operations_setup = setup_doc.name
	schedule.finance_onboarding = setup_doc.get("finance_onboarding")
	schedule.handover = setup_doc.get("handover")
	schedule.crm_deal = setup_doc.get("crm_deal")
	schedule.crm_lead = setup_doc.get("crm_lead")
	schedule.participant_intake = setup_doc.get("participant_intake")
	schedule.participant_customer = setup_doc.get("participant_customer")
	schedule.ndis_financial_profile = setup_doc.get("ndis_financial_profile")
	schedule.participant_name = setup_doc.get("participant_name") or setup_doc.get("participant_customer") or setup_doc.name
	schedule.ndis_number = setup_doc.get("ndis_number")
	schedule.plan_start_date = setup_doc.get("plan_start_date")
	schedule.plan_end_date = setup_doc.get("plan_end_date")
	schedule.target_start_date = setup_doc.get("target_start_date") or setup_doc.get("plan_start_date")
	schedule.schedule_owner = frappe.session.user
	schedule.operations_owner = setup_doc.get("operations_owner")
	schedule.rostering_owner = setup_doc.get("rostering_owner")
	schedule.service_manager = setup_doc.get("service_manager")
	schedule.clinical_owner = setup_doc.get("clinical_owner")

	_set_if_field(schedule, "default_house", setup_doc.get("default_house"))
	_set_if_field(schedule, "default_cost_center", setup_doc.get("default_cost_center"))

	_append_lines_from_operations_setup(schedule, setup_doc)

	summary = _calculate_readiness(schedule)
	schedule.readiness_percent = summary["readiness_percent"]
	schedule.schedule_ready = 1 if summary["schedule_ready"] else 0
	schedule.insert(ignore_permissions=False)
	_sync_summary_to_links(schedule)
	frappe.db.commit()

	return {
		"doctype": SCHEDULE_DRAFT,
		"name": schedule.name,
		"created": True,
		"message": "NDIS CRM Service Schedule Draft created successfully.",
	}


@frappe.whitelist()
def create_service_schedule_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))

	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_schedule_for_deal(deal)
	if existing:
		return {
			"doctype": SCHEDULE_DRAFT,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Service Schedule Draft returned.",
		}

	operations_setup = _get_operations_setup_for_deal(deal)
	if not operations_setup:
		try:
			from ndis_crm.phase7_operations_setup import create_operations_setup_from_crm_deal

			result = create_operations_setup_from_crm_deal(deal)
			operations_setup = result.get("name")
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Operations Setup before creating Service Schedule Draft."))

	return create_service_schedule_from_operations_setup(operations_setup)


@frappe.whitelist()
def validate_schedule_readiness(schedule_draft):
	_check_role()

	doc = frappe.get_doc(SCHEDULE_DRAFT, schedule_draft)
	for row in doc.get("schedule_lines") or []:
		_normalize_line_defaults(row)

	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Service schedule readiness validated.",
	}


@frappe.whitelist()
def mark_ready_for_roster_build(schedule_draft):
	_check_role()

	doc = frappe.get_doc(SCHEDULE_DRAFT, schedule_draft)
	for row in doc.get("schedule_lines") or []:
		_normalize_line_defaults(row)

	summary = _calculate_readiness(doc)
	if not summary["schedule_ready"]:
		frappe.throw(_("Cannot mark Ready for Roster Build. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Ready for Roster Build"
	doc.readiness_percent = summary["readiness_percent"]
	doc.schedule_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": SCHEDULE_DRAFT,
		"name": doc.name,
		"message": "Service Schedule Draft marked Ready for Roster Build.",
	}


@frappe.whitelist()
def mark_schedule_approved(schedule_draft):
	_check_role()

	doc = frappe.get_doc(SCHEDULE_DRAFT, schedule_draft)
	for row in doc.get("schedule_lines") or []:
		_normalize_line_defaults(row)

	summary = _calculate_readiness(doc)
	if not summary["schedule_ready"]:
		frappe.throw(_("Cannot approve schedule. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Schedule Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.schedule_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": SCHEDULE_DRAFT,
		"name": doc.name,
		"message": "Service Schedule Draft approved.",
	}


def validate_schedule_draft(doc, method=None):
	for row in doc.get("schedule_lines") or []:
		_normalize_line_defaults(row)

	summary = _calculate_readiness(doc)

	if _field_exists(SCHEDULE_DRAFT, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(SCHEDULE_DRAFT, "schedule_ready"):
		doc.schedule_ready = 1 if summary["schedule_ready"] else 0

	if doc.status in READY_STATUSES and not summary["schedule_ready"]:
		frappe.throw(_("Cannot set Service Schedule Draft to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))


def on_schedule_draft_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Service Schedule Draft Summary Sync Failed")


def validate_crm_deal_phase8(doc, method=None):
	if doc.status != "Won / Active Client":
		return

	schedule_required = 1
	if _field_exists(CRM_DEAL, "ndis_service_schedule_required"):
		schedule_required = doc.get("ndis_service_schedule_required")

	if not schedule_required:
		return

	schedule_draft = doc.get("ndis_service_schedule_draft") if _field_exists(CRM_DEAL, "ndis_service_schedule_draft") else None
	if not schedule_draft:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Service Schedule Draft must be created and approved."))

	status = frappe.db.get_value(SCHEDULE_DRAFT, schedule_draft, "status")
	schedule_ready = frappe.db.get_value(SCHEDULE_DRAFT, schedule_draft, "schedule_ready")
	if status not in APPROVED_STATUSES or not schedule_ready:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Service Schedule Draft must be Schedule Approved."))


def validate_crm_deal_phase8_combined(doc, method=None):
	"""
	Preserve Phase 2-7 validator chain, then add Phase 8 service schedule validation.
	"""
	try:
		from ndis_crm.phase7_operations_setup import validate_crm_deal_phase7_combined

		validate_crm_deal_phase7_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase5_finance_onboarding import validate_crm_deal_phase5_combined

			validate_crm_deal_phase5_combined(doc, method)
		except ImportError:
			try:
				from ndis_crm.phase4_handover import validate_crm_deal_phase4_combined

				validate_crm_deal_phase4_combined(doc, method)
			except ImportError:
				pass

	validate_crm_deal_phase8(doc, method)


def phase8_health_check():
	print("---- NDIS CRM Phase 8 Health Check ----")

	for dt in [
		SCHEDULE_DRAFT_LINE,
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
		"ndis_service_schedule_required",
		"ndis_service_schedule_draft",
		"service_schedule_status",
		"service_schedule_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

	for doctype in [HANDOVER, FINANCE_ONBOARDING, OPERATIONS_SETUP, INTAKE]:
		for field in [
			"ndis_service_schedule_draft",
			"service_schedule_status",
			"service_schedule_ready",
		]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")

	print("NDIS CRM Service Schedule Draft records:", frappe.db.count(SCHEDULE_DRAFT) if _doctype_exists(SCHEDULE_DRAFT) else 0)
	print("CRM Deal Phase 8 combined validator should be active through hooks.py.")
	print("---- End Phase 8 Health Check ----")
