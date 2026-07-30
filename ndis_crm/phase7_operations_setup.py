import frappe
from frappe import _


CRM_DEAL = "CRM Deal"
CRM_LEAD = "CRM Lead"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"

FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
FINANCE_ONBOARDING_SERVICE = "NDIS CRM Finance Onboarding Service"

OPERATIONS_SETUP = "NDIS CRM Operations Setup"
OPERATIONS_REQUIREMENT = "NDIS CRM Operations Service Requirement"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

READY_STATUSES = ["Ready for Rostering", "Roster Setup Started", "Service Delivery Ready", "Active"]
SERVICE_DELIVERY_READY_STATUSES = ["Service Delivery Ready", "Active"]

ALLOWED_ROLES = {
	"System Manager",
	"Sales Manager",
	"Sales User",
	"NDIS CRM Manager",
	"NDIS Intake Officer",
	"NDIS Service Manager",
	"NDIS Plan Management Officer",
}

ROSTER_SERVICE_CODES = {
	"DAILY_LIFE",
	"SIL",
	"COMMUNITY_PARTICIPATION",
	"TRANSPORT",
}

HOUSE_SERVICE_CODES = {
	"SIL",
}

CLINICAL_REVIEW_SERVICE_CODES = {
	"SIL",
	"THERAPY",
	"BEHAVIOUR_SUPPORT",
	"DAILY_LIFE",
}

TRANSPORT_SERVICE_CODES = {
	"TRANSPORT",
	"COMMUNITY_PARTICIPATION",
}


def _check_role():
	user_roles = set(frappe.get_roles())
	if not user_roles.intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this NDIS CRM operations setup action."))


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


def _existing_operations_setup_for_deal(deal_name):
	if not _doctype_exists(OPERATIONS_SETUP):
		return None

	if _field_exists(CRM_DEAL, "ndis_operations_setup"):
		existing = frappe.db.get_value(CRM_DEAL, deal_name, "ndis_operations_setup")
		if existing:
			return existing

	return frappe.db.get_value(OPERATIONS_SETUP, {"crm_deal": deal_name}, "name")


def _existing_operations_setup_for_handover(handover_name):
	if not _doctype_exists(OPERATIONS_SETUP):
		return None

	if _field_exists(HANDOVER, "ndis_operations_setup"):
		existing = frappe.db.get_value(HANDOVER, handover_name, "ndis_operations_setup")
		if existing:
			return existing

	return frappe.db.get_value(OPERATIONS_SETUP, {"handover": handover_name}, "name")


def _existing_operations_setup_for_finance_onboarding(onboarding_name):
	if not _doctype_exists(OPERATIONS_SETUP):
		return None

	if _field_exists(FINANCE_ONBOARDING, "ndis_operations_setup"):
		existing = frappe.db.get_value(FINANCE_ONBOARDING, onboarding_name, "ndis_operations_setup")
		if existing:
			return existing

	return frappe.db.get_value(OPERATIONS_SETUP, {"finance_onboarding": onboarding_name}, "name")


def _get_service_line_doc(service_line):
	if service_line and frappe.db.exists("NDIS Service Line", service_line):
		return frappe.get_doc("NDIS Service Line", service_line)
	return None


def _get_service_code(service_line):
	service_doc = _get_service_line_doc(service_line)
	if service_doc:
		return service_doc.get("service_code") or service_line
	return service_line


def _default_service_model(service_code):
	if service_code == "SIL":
		return "SIL 24/7 Support"

	if service_code == "THERAPY":
		return "Therapy Service"

	if service_code == "TRANSPORT":
		return "Transport Service"

	if service_code == "PLAN_MANAGEMENT":
		return "Plan Management Admin"

	if service_code == "COMMUNITY_PARTICIPATION":
		return "Community Participation Shift"

	if service_code == "BEHAVIOUR_SUPPORT":
		return "Behaviour Support Service"

	return "Support Worker Shift"


def _get_handover_for_deal(deal_name):
	if _field_exists(CRM_DEAL, "ndis_handover"):
		handover = frappe.db.get_value(CRM_DEAL, deal_name, "ndis_handover")
		if handover:
			return handover

	if _doctype_exists(HANDOVER):
		return frappe.db.get_value(HANDOVER, {"crm_deal": deal_name}, "name")

	return None


def _get_finance_onboarding_for_deal(deal_name):
	if _field_exists(CRM_DEAL, "ndis_finance_onboarding"):
		onboarding = frappe.db.get_value(CRM_DEAL, deal_name, "ndis_finance_onboarding")
		if onboarding:
			return onboarding

	if _doctype_exists(FINANCE_ONBOARDING):
		return frappe.db.get_value(FINANCE_ONBOARDING, {"crm_deal": deal_name}, "name")

	return None


def _append_requirement_if_missing(setup_doc, row_data):
	existing = {row.service_line for row in setup_doc.get("service_requirements") or []}

	if row_data.get("service_line") in existing:
		return

	setup_doc.append("service_requirements", row_data)


def _build_requirement_from_finance_row(row):
	service_line = row.get("service_line")
	service_code = row.get("service_code") or _get_service_code(service_line)

	return {
		"service_line": service_line,
		"service_code": service_code,
		"service_model": _default_service_model(service_code),
		"priority": row.get("priority"),
		"required_start_date": row.get("required_start_date"),
		"budget_type": row.get("budget_type"),
		"finance_service_type": row.get("finance_service_type"),
		"support_item": row.get("default_support_item"),
		"plan_budget": row.get("draft_plan_budget"),
		"service_booking": row.get("service_booking"),
		"requires_roster": 1 if service_code in ROSTER_SERVICE_CODES else 0,
		"requires_house": 1 if service_code in HOUSE_SERVICE_CODES else 0,
		"requires_clinical_review": 1 if service_code in CLINICAL_REVIEW_SERVICE_CODES else 0,
		"transport_required": 1 if service_code in TRANSPORT_SERVICE_CODES else 0,
		"status": "Pending",
		"notes": row.get("notes"),
	}


def _build_requirement_from_deal_interest(row):
	service_line = row.get("service_line")
	service_doc = _get_service_line_doc(service_line)
	service_code = service_doc.get("service_code") if service_doc else service_line

	data = {
		"service_line": service_line,
		"service_code": service_code,
		"service_model": _default_service_model(service_code),
		"priority": row.get("priority"),
		"required_start_date": row.get("required_start_date"),
		"budget_type": service_doc.get("budget_type") if service_doc else None,
		"requires_roster": 1 if service_code in ROSTER_SERVICE_CODES else 0,
		"requires_house": 1 if service_code in HOUSE_SERVICE_CODES else 0,
		"requires_clinical_review": 1 if service_code in CLINICAL_REVIEW_SERVICE_CODES else 0,
		"transport_required": 1 if service_code in TRANSPORT_SERVICE_CODES else 0,
		"status": "Pending",
		"notes": row.get("notes"),
	}

	if service_doc:
		if _field_exists("NDIS Service Line", "finance_service_type"):
			data["finance_service_type"] = service_doc.get("finance_service_type")

		if _field_exists("NDIS Service Line", "default_support_item"):
			data["support_item"] = service_doc.get("default_support_item")

	return data


def _append_requirements_from_finance_onboarding(setup_doc, onboarding_name):
	if not onboarding_name or not frappe.db.exists(FINANCE_ONBOARDING, onboarding_name):
		return

	onboarding_doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding_name)

	for row in onboarding_doc.get("service_rows") or []:
		requirement = _build_requirement_from_finance_row(row)
		_append_requirement_if_missing(setup_doc, requirement)


def _append_requirements_from_deal(setup_doc, deal_name):
	if not deal_name or not frappe.db.exists(CRM_DEAL, deal_name):
		return

	deal_doc = frappe.get_doc(CRM_DEAL, deal_name)

	if not _field_exists(CRM_DEAL, "ndis_service_interests"):
		return

	for row in deal_doc.get("ndis_service_interests") or []:
		requirement = _build_requirement_from_deal_interest(row)
		_append_requirement_if_missing(setup_doc, requirement)


def _refresh_header_requirement_flags(setup_doc):
	service_rows = setup_doc.get("service_requirements") or []
	if _field_exists(OPERATIONS_SETUP, "clinical_review_required"):
		setup_doc.clinical_review_required = 1 if any(row.get("requires_clinical_review") for row in service_rows) else 0


def _calculate_readiness(doc):
	_refresh_header_requirement_flags(doc)
	checks = []

	checks.append({"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))})
	checks.append({"label": "CRM Handover linked", "complete": bool(doc.get("handover"))})
	checks.append({"label": "Operations Owner assigned", "complete": bool(doc.get("operations_owner"))})
	checks.append({"label": "Target Start Date entered", "complete": bool(doc.get("target_start_date"))})
	checks.append({"label": "Roster requirements confirmed", "complete": bool(doc.get("roster_requirements_confirmed"))})
	checks.append({"label": "Worker skill requirements confirmed", "complete": bool(doc.get("worker_skill_requirements_confirmed"))})

	if doc.get("clinical_review_required"):
		checks.append({"label": "Clinical review complete", "complete": bool(doc.get("clinical_review_complete"))})

	if doc.get("finance_setup_required"):
		checks.append({"label": "Finance setup confirmed", "complete": bool(doc.get("finance_setup_confirmed"))})

	service_rows = doc.get("service_requirements") or []
	checks.append({"label": "At least one service requirement row exists", "complete": bool(service_rows)})

	missing_service_model = [row.service_line for row in service_rows if not row.get("service_model")]
	checks.append({
		"label": "All service rows have service model",
		"complete": not missing_service_model,
		"details": missing_service_model,
	})

	missing_start_date = [row.service_line for row in service_rows if not row.get("required_start_date")]
	checks.append({
		"label": "All service rows have required start date",
		"complete": not missing_start_date,
		"details": missing_start_date,
	})

	missing_roster_detail = [
		row.service_line
		for row in service_rows
		if row.get("requires_roster")
		and (not row.get("frequency") or not row.get("shifts_per_week") or not row.get("hours_per_shift"))
	]
	checks.append({
		"label": "Roster-required rows have frequency, shifts per week and hours per shift",
		"complete": not missing_roster_detail,
		"details": missing_roster_detail,
	})

	missing_house = [row.service_line for row in service_rows if row.get("requires_house") and not row.get("default_house")]
	checks.append({
		"label": "House-required rows have default house",
		"complete": not missing_house,
		"details": missing_house,
	})

	missing_clinical = [
		row.service_line
		for row in service_rows
		if row.get("requires_clinical_review") and not row.get("clinical_review_complete")
	]
	checks.append({
		"label": "Clinical-required rows have clinical review complete",
		"complete": not missing_clinical,
		"details": missing_clinical,
	})

	missing_worker_skills = [
		row.service_line
		for row in service_rows
		if row.get("requires_roster") and not row.get("worker_skill_requirements")
	]
	checks.append({
		"label": "Roster-required rows have worker skill requirements",
		"complete": not missing_worker_skills,
		"details": missing_worker_skills,
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
		"operations_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)

	if _field_exists(OPERATIONS_SETUP, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(OPERATIONS_SETUP, "operations_ready"):
		doc.operations_ready = 1 if summary["operations_ready"] else 0

	if doc.get("crm_deal"):
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "ndis_operations_setup", doc.name)
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "operations_setup_status", doc.status)
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "operations_setup_ready", 1 if summary["operations_ready"] else 0)

	if doc.get("handover"):
		_db_set_if_field(HANDOVER, doc.handover, "ndis_operations_setup", doc.name)
		_db_set_if_field(HANDOVER, doc.handover, "operations_setup_status", doc.status)
		_db_set_if_field(HANDOVER, doc.handover, "operations_setup_ready", 1 if summary["operations_ready"] else 0)

	if doc.get("finance_onboarding"):
		_db_set_if_field(FINANCE_ONBOARDING, doc.finance_onboarding, "ndis_operations_setup", doc.name)
		_db_set_if_field(FINANCE_ONBOARDING, doc.finance_onboarding, "operations_setup_status", doc.status)
		_db_set_if_field(FINANCE_ONBOARDING, doc.finance_onboarding, "operations_setup_ready", 1 if summary["operations_ready"] else 0)

	if doc.get("participant_intake"):
		_db_set_if_field(INTAKE, doc.participant_intake, "ndis_operations_setup", doc.name)
		_db_set_if_field(INTAKE, doc.participant_intake, "operations_setup_status", doc.status)
		_db_set_if_field(INTAKE, doc.participant_intake, "operations_setup_ready", 1 if summary["operations_ready"] else 0)

	return summary


def _make_operations_setup_base():
	setup = frappe.new_doc(OPERATIONS_SETUP)
	setup.status = "Draft"
	setup.operations_owner = frappe.session.user
	return setup


def _populate_from_handover(setup, handover_doc):
	setup.handover = handover_doc.name
	setup.crm_deal = handover_doc.get("crm_deal")
	setup.crm_lead = handover_doc.get("crm_lead")
	setup.participant_intake = handover_doc.get("participant_intake")
	setup.participant_customer = handover_doc.get("participant_customer")
	setup.ndis_financial_profile = handover_doc.get("ndis_financial_profile")
	setup.participant_name = handover_doc.get("participant_name")
	setup.ndis_number = handover_doc.get("ndis_number")
	setup.plan_start_date = handover_doc.get("plan_start_date")
	setup.plan_end_date = handover_doc.get("plan_end_date")
	setup.target_start_date = handover_doc.get("target_start_date") or handover_doc.get("plan_start_date")
	setup.finance_setup_required = 1

	_set_if_field(setup, "default_house", handover_doc.get("default_house"))
	_set_if_field(setup, "default_cost_center", handover_doc.get("default_cost_center"))


def _populate_from_finance_onboarding(setup, onboarding_doc):
	setup.finance_onboarding = onboarding_doc.name
	setup.handover = onboarding_doc.get("handover")
	setup.crm_deal = onboarding_doc.get("crm_deal")
	setup.crm_lead = onboarding_doc.get("crm_lead")
	setup.participant_intake = onboarding_doc.get("participant_intake")
	setup.participant_customer = onboarding_doc.get("participant_customer")
	setup.ndis_financial_profile = onboarding_doc.get("ndis_financial_profile")
	setup.participant_name = onboarding_doc.get("participant_name")
	setup.ndis_number = onboarding_doc.get("ndis_number")
	setup.plan_start_date = onboarding_doc.get("plan_start_date")
	setup.plan_end_date = onboarding_doc.get("plan_end_date")
	setup.target_start_date = onboarding_doc.get("plan_start_date")
	setup.finance_setup_required = 1
	setup.finance_setup_confirmed = 1 if onboarding_doc.status == "Completed" else 0

	_set_if_field(setup, "default_house", onboarding_doc.get("default_house"))
	_set_if_field(setup, "default_cost_center", onboarding_doc.get("default_cost_center"))


@frappe.whitelist()
def create_operations_setup_from_finance_onboarding(onboarding):
	_check_role()

	if not onboarding:
		frappe.throw(_("NDIS CRM Finance Onboarding is required."))

	if not frappe.db.exists(FINANCE_ONBOARDING, onboarding):
		frappe.throw(_("NDIS CRM Finance Onboarding {0} was not found.").format(onboarding))

	existing = _existing_operations_setup_for_finance_onboarding(onboarding)
	if existing:
		return {
			"doctype": OPERATIONS_SETUP,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Operations Setup returned.",
		}

	onboarding_doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)
	setup = _make_operations_setup_base()
	_populate_from_finance_onboarding(setup, onboarding_doc)
	_append_requirements_from_finance_onboarding(setup, onboarding_doc.name)

	if not setup.get("participant_name"):
		setup.participant_name = setup.get("participant_customer") or "Operations Setup"

	summary = _calculate_readiness(setup)
	setup.readiness_percent = summary["readiness_percent"]
	setup.operations_ready = 1 if summary["operations_ready"] else 0

	setup.insert(ignore_permissions=False)
	_sync_summary_to_links(setup)
	frappe.db.commit()

	return {
		"doctype": OPERATIONS_SETUP,
		"name": setup.name,
		"created": True,
		"message": "NDIS CRM Operations Setup created successfully.",
	}


@frappe.whitelist()
def create_operations_setup_from_handover(handover):
	_check_role()

	if not handover:
		frappe.throw(_("NDIS CRM Handover is required."))

	if not frappe.db.exists(HANDOVER, handover):
		frappe.throw(_("NDIS CRM Handover {0} was not found.").format(handover))

	existing = _existing_operations_setup_for_handover(handover)
	if existing:
		return {
			"doctype": OPERATIONS_SETUP,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Operations Setup returned.",
		}

	handover_doc = frappe.get_doc(HANDOVER, handover)
	finance_onboarding = handover_doc.get("ndis_finance_onboarding") if _field_exists(HANDOVER, "ndis_finance_onboarding") else None

	if finance_onboarding and frappe.db.exists(FINANCE_ONBOARDING, finance_onboarding):
		return create_operations_setup_from_finance_onboarding(finance_onboarding)

	setup = _make_operations_setup_base()
	_populate_from_handover(setup, handover_doc)
	_append_requirements_from_deal(setup, handover_doc.get("crm_deal"))

	if not setup.get("participant_name"):
		setup.participant_name = setup.get("participant_customer") or "Operations Setup"

	summary = _calculate_readiness(setup)
	setup.readiness_percent = summary["readiness_percent"]
	setup.operations_ready = 1 if summary["operations_ready"] else 0

	setup.insert(ignore_permissions=False)
	_sync_summary_to_links(setup)
	frappe.db.commit()

	return {
		"doctype": OPERATIONS_SETUP,
		"name": setup.name,
		"created": True,
		"message": "NDIS CRM Operations Setup created successfully.",
	}


@frappe.whitelist()
def create_operations_setup_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))

	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_operations_setup_for_deal(deal)
	if existing:
		return {
			"doctype": OPERATIONS_SETUP,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Operations Setup returned.",
		}

	finance_onboarding = _get_finance_onboarding_for_deal(deal)
	if finance_onboarding:
		return create_operations_setup_from_finance_onboarding(finance_onboarding)

	handover = _get_handover_for_deal(deal)
	if handover:
		return create_operations_setup_from_handover(handover)

	try:
		from ndis_crm.phase4_handover import create_handover_from_crm_deal

		result = create_handover_from_crm_deal(deal)
		handover = result.get("name")
		return create_operations_setup_from_handover(handover)
	except ImportError:
		frappe.throw(_("Please create NDIS CRM Handover before creating Operations Setup."))


@frappe.whitelist()
def validate_operations_readiness(operations_setup):
	_check_role()

	doc = frappe.get_doc(OPERATIONS_SETUP, operations_setup)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Operations setup readiness validated.",
	}


@frappe.whitelist()
def mark_ready_for_rostering(operations_setup):
	_check_role()

	doc = frappe.get_doc(OPERATIONS_SETUP, operations_setup)
	summary = _calculate_readiness(doc)

	if not summary["operations_ready"]:
		frappe.throw(_("Cannot mark Ready for Rostering. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Ready for Rostering"
	doc.readiness_percent = summary["readiness_percent"]
	doc.operations_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": OPERATIONS_SETUP,
		"name": doc.name,
		"message": "Operations Setup marked Ready for Rostering.",
	}


@frappe.whitelist()
def mark_service_delivery_ready(operations_setup):
	_check_role()

	doc = frappe.get_doc(OPERATIONS_SETUP, operations_setup)
	summary = _calculate_readiness(doc)

	if not summary["operations_ready"]:
		frappe.throw(_("Cannot mark Service Delivery Ready. Incomplete items: {0}").format("; ".join(summary["incomplete"])))

	doc.status = "Service Delivery Ready"
	doc.readiness_percent = summary["readiness_percent"]
	doc.operations_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"doctype": OPERATIONS_SETUP,
		"name": doc.name,
		"message": "Operations Setup marked Service Delivery Ready.",
	}


def validate_operations_setup(doc, method=None):
	summary = _calculate_readiness(doc)

	if _field_exists(OPERATIONS_SETUP, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(OPERATIONS_SETUP, "operations_ready"):
		doc.operations_ready = 1 if summary["operations_ready"] else 0

	if doc.status in READY_STATUSES and not summary["operations_ready"]:
		frappe.throw(_("Cannot set Operations Setup to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))


def on_operations_setup_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Operations Setup Summary Sync Failed")


def validate_crm_deal_phase7(doc, method=None):
	if doc.status != "Won / Active Client":
		return

	operations_required = 1
	if _field_exists(CRM_DEAL, "ndis_operations_setup_required"):
		operations_required = doc.get("ndis_operations_setup_required")

	if not operations_required:
		return

	operations_setup = doc.get("ndis_operations_setup") if _field_exists(CRM_DEAL, "ndis_operations_setup") else None
	if not operations_setup:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Operations Setup must be created and ready."))

	status = frappe.db.get_value(OPERATIONS_SETUP, operations_setup, "status")
	operations_ready = frappe.db.get_value(OPERATIONS_SETUP, operations_setup, "operations_ready")

	if status not in SERVICE_DELIVERY_READY_STATUSES or not operations_ready:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Operations Setup must be Service Delivery Ready or Active."))


def validate_crm_deal_phase7_combined(doc, method=None):
	"""
	Preserve Phase 2 through Phase 5 validators, then add Phase 7 operations setup validation.
	"""
	try:
		from ndis_crm.phase5_finance_onboarding import validate_crm_deal_phase5_combined

		validate_crm_deal_phase5_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase4_handover import validate_crm_deal_phase4_combined

			validate_crm_deal_phase4_combined(doc, method)
		except ImportError:
			try:
				from ndis_crm.phase3_documents import validate_crm_deal_combined

				validate_crm_deal_combined(doc, method)
			except ImportError:
				try:
					from ndis_crm.phase2_api import validate_crm_deal

					validate_crm_deal(doc, method)
				except ImportError:
					pass

	validate_crm_deal_phase7(doc, method)


def phase7_health_check():
	print("---- NDIS CRM Phase 7 Health Check ----")

	for dt in [
		OPERATIONS_REQUIREMENT,
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
		"ndis_operations_setup_required",
		"ndis_operations_setup",
		"operations_setup_status",
		"operations_setup_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

	for field in [
		"ndis_operations_setup",
		"operations_setup_status",
		"operations_setup_ready",
	]:
		print(f"{HANDOVER} field {field}: {'OK' if _field_exists(HANDOVER, field) else 'MISSING'}")
		print(f"{FINANCE_ONBOARDING} field {field}: {'OK' if _field_exists(FINANCE_ONBOARDING, field) else 'MISSING'}")
		print(f"{INTAKE} field {field}: {'OK' if _field_exists(INTAKE, field) else 'MISSING'}")

	print("NDIS CRM Operations Setup records:", frappe.db.count(OPERATIONS_SETUP) if _doctype_exists(OPERATIONS_SETUP) else 0)
	print("CRM Deal Phase 7 combined validator should be active through hooks.py.")
	print("---- End Phase 7 Health Check ----")
