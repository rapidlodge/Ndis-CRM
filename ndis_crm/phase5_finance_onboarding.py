import frappe
from frappe import _


CRM_DEAL = "CRM Deal"
CRM_LEAD = "CRM Lead"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"

FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
FINANCE_ONBOARDING_SERVICE = "NDIS CRM Finance Onboarding Service"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
FUNDING_SOURCE = "NDIS Funding Source"
NDIS_HOUSE = "NDIS House"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"

READY_STATUSES = ["Ready for Finance", "Finance Setup Started", "Budget Setup Complete", "Service Booking Complete", "Completed"]
COMPLETE_STATUSES = ["Completed"]

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
		frappe.throw(_("You do not have permission to perform this NDIS CRM finance onboarding action."))


def _doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
	return bool(
		frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
		or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
	)


def _get(doc, fieldname, default=None):
	if doc and _field_exists(doc.doctype, fieldname):
		return doc.get(fieldname)
	return default


def _set_if_field(doc, fieldname, value):
	if value is not None and _field_exists(doc.doctype, fieldname):
		doc.set(fieldname, value)


def _db_set_if_field(doctype, name, fieldname, value):
	if name and _field_exists(doctype, fieldname):
		frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)


def _get_existing_onboarding_for_handover(handover_name):
	if not _doctype_exists(FINANCE_ONBOARDING):
		return None

	if _field_exists(HANDOVER, "ndis_finance_onboarding"):
		existing = frappe.db.get_value(HANDOVER, handover_name, "ndis_finance_onboarding")
		if existing:
			return existing

	return frappe.db.get_value(FINANCE_ONBOARDING, {"handover": handover_name}, "name")


def _get_existing_onboarding_for_deal(deal_name):
	if not _doctype_exists(FINANCE_ONBOARDING):
		return None

	if _field_exists(CRM_DEAL, "ndis_finance_onboarding"):
		existing = frappe.db.get_value(CRM_DEAL, deal_name, "ndis_finance_onboarding")
		if existing:
			return existing

	return frappe.db.get_value(FINANCE_ONBOARDING, {"crm_deal": deal_name}, "name")


def _participant_name_from_handover(handover_doc):
	return handover_doc.get("participant_name") or handover_doc.name


def _get_service_lines_from_deal(deal_name):
	if not deal_name or not frappe.db.exists(CRM_DEAL, deal_name):
		return []

	deal_doc = frappe.get_doc(CRM_DEAL, deal_name)

	if not _field_exists(CRM_DEAL, "ndis_service_interests"):
		return []

	service_lines = []

	for row in deal_doc.get("ndis_service_interests") or []:
		if row.get("service_line") and row.get("service_line") not in service_lines:
			service_lines.append(row.get("service_line"))

	return service_lines


def _service_interest_lookup(deal_name):
	lookup = {}

	if not deal_name or not frappe.db.exists(CRM_DEAL, deal_name):
		return lookup

	deal_doc = frappe.get_doc(CRM_DEAL, deal_name)

	if not _field_exists(CRM_DEAL, "ndis_service_interests"):
		return lookup

	for row in deal_doc.get("ndis_service_interests") or []:
		if row.get("service_line"):
			lookup[row.get("service_line")] = {
				"priority": row.get("priority"),
				"required_start_date": row.get("required_start_date"),
				"funding_available": row.get("funding_available"),
				"notes": row.get("notes"),
			}

	return lookup


def _build_service_row(service_line, interest_data=None):
	interest_data = interest_data or {}

	if not frappe.db.exists("NDIS Service Line", service_line):
		return None

	service_doc = frappe.get_doc("NDIS Service Line", service_line)

	row = {
		"service_line": service_line,
		"service_code": service_doc.get("service_code"),
		"budget_type": service_doc.get("budget_type"),
		"priority": interest_data.get("priority"),
		"required_start_date": interest_data.get("required_start_date"),
		"funding_available": interest_data.get("funding_available"),
		"requires_plan_budget": 1 if service_doc.get("requires_plan_budget") else 0,
		"requires_service_booking": 1 if service_doc.get("requires_service_booking") else 0,
		"status": "Pending",
		"notes": interest_data.get("notes"),
	}

	if _field_exists("NDIS Service Line", "finance_service_type"):
		row["finance_service_type"] = service_doc.get("finance_service_type")

	if _field_exists("NDIS Service Line", "default_support_item"):
		row["default_support_item"] = service_doc.get("default_support_item")

	return row


def _append_service_rows(onboarding_doc, deal_name):
	existing_services = {row.service_line for row in onboarding_doc.get("service_rows") or []}

	service_lines = _get_service_lines_from_deal(deal_name)
	interest_lookup = _service_interest_lookup(deal_name)

	for service_line in service_lines:
		if service_line in existing_services:
			continue

		row = _build_service_row(service_line, interest_lookup.get(service_line))
		if row:
			onboarding_doc.append("service_rows", row)


def _calculate_readiness(doc):
	checks = [
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "NDIS Participant Financial Profile linked", "complete": bool(doc.get("ndis_financial_profile"))},
		{"label": "Plan Start Date entered", "complete": bool(doc.get("plan_start_date"))},
		{"label": "Plan End Date entered", "complete": bool(doc.get("plan_end_date"))},
	]

	if _doctype_exists(FUNDING_SOURCE) and _field_exists(FINANCE_ONBOARDING, "funding_source"):
		checks.append({"label": "Funding Source confirmed", "complete": bool(doc.get("funding_source"))})

	service_rows = doc.get("service_rows") or []

	checks.append({
		"label": "At least one finance service row exists",
		"complete": bool(service_rows),
	})

	if _doctype_exists(NDIS_SERVICE_TYPE):
		unmapped = [row.service_line for row in service_rows if not row.get("finance_service_type")]
		checks.append({
			"label": "All service rows mapped to NDIS Service Type",
			"complete": not unmapped,
			"details": unmapped,
		})

	missing_budget_amounts = [
		row.service_line
		for row in service_rows
		if row.get("requires_plan_budget") and not row.get("proposed_budget_amount")
	]

	checks.append({
		"label": "Required proposed budget amounts entered",
		"complete": not missing_budget_amounts,
		"details": missing_budget_amounts,
	})

	missing_booking_amounts = [
		row.service_line
		for row in service_rows
		if row.get("requires_service_booking") and not row.get("proposed_service_booking_amount")
	]

	checks.append({
		"label": "Required proposed service booking amounts entered",
		"complete": not missing_booking_amounts,
		"details": missing_booking_amounts,
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
			label += ": " + ", ".join(row["details"])

		incomplete.append(label)

	return {
		"total_checks": total,
		"complete_checks": complete,
		"readiness_percent": readiness_percent,
		"finance_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)

	if _field_exists(FINANCE_ONBOARDING, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(FINANCE_ONBOARDING, "finance_ready"):
		doc.finance_ready = 1 if summary["finance_ready"] else 0

	if doc.get("crm_deal"):
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "ndis_finance_onboarding", doc.name)
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "finance_onboarding_status", doc.status)
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "finance_onboarding_ready", 1 if summary["finance_ready"] else 0)

	if doc.get("handover"):
		_db_set_if_field(HANDOVER, doc.handover, "ndis_finance_onboarding", doc.name)
		_db_set_if_field(HANDOVER, doc.handover, "finance_onboarding_status", doc.status)
		_db_set_if_field(HANDOVER, doc.handover, "finance_onboarding_ready", 1 if summary["finance_ready"] else 0)

	if doc.get("participant_intake"):
		_db_set_if_field(INTAKE, doc.participant_intake, "ndis_finance_onboarding", doc.name)
		_db_set_if_field(INTAKE, doc.participant_intake, "finance_onboarding_status", doc.status)
		_db_set_if_field(INTAKE, doc.participant_intake, "finance_onboarding_ready", 1 if summary["finance_ready"] else 0)

	return summary


@frappe.whitelist()
def create_finance_onboarding_from_handover(handover):
	_check_role()

	if not handover:
		frappe.throw(_("NDIS CRM Handover is required."))

	if not frappe.db.exists(HANDOVER, handover):
		frappe.throw(_("NDIS CRM Handover {0} was not found.").format(handover))

	existing = _get_existing_onboarding_for_handover(handover)
	if existing:
		return {
			"doctype": FINANCE_ONBOARDING,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Finance Onboarding returned.",
		}

	handover_doc = frappe.get_doc(HANDOVER, handover)
	onboarding = frappe.new_doc(FINANCE_ONBOARDING)

	onboarding.status = "Draft"
	onboarding.handover = handover_doc.name
	onboarding.crm_deal = handover_doc.get("crm_deal")
	onboarding.crm_lead = handover_doc.get("crm_lead")
	onboarding.participant_intake = handover_doc.get("participant_intake")
	onboarding.participant_customer = handover_doc.get("participant_customer")
	onboarding.ndis_financial_profile = handover_doc.get("ndis_financial_profile")
	onboarding.participant_name = _participant_name_from_handover(handover_doc)
	onboarding.ndis_number = handover_doc.get("ndis_number")
	onboarding.plan_start_date = handover_doc.get("plan_start_date")
	onboarding.plan_end_date = handover_doc.get("plan_end_date")
	onboarding.plan_management_type = handover_doc.get("plan_management_type")
	onboarding.finance_owner = frappe.session.user

	_set_if_field(onboarding, "funding_source", handover_doc.get("funding_source"))
	_set_if_field(onboarding, "default_house", handover_doc.get("default_house"))
	_set_if_field(onboarding, "default_cost_center", handover_doc.get("default_cost_center"))

	_append_service_rows(onboarding, handover_doc.get("crm_deal"))

	summary = _calculate_readiness(onboarding)
	onboarding.readiness_percent = summary["readiness_percent"]
	onboarding.finance_ready = 1 if summary["finance_ready"] else 0

	onboarding.insert(ignore_permissions=False)

	_db_set_if_field(HANDOVER, handover_doc.name, "ndis_finance_onboarding", onboarding.name)
	_db_set_if_field(HANDOVER, handover_doc.name, "finance_onboarding_status", onboarding.status)
	_db_set_if_field(HANDOVER, handover_doc.name, "finance_onboarding_ready", onboarding.finance_ready)

	if onboarding.get("crm_deal"):
		_db_set_if_field(CRM_DEAL, onboarding.crm_deal, "ndis_finance_onboarding", onboarding.name)
		_db_set_if_field(CRM_DEAL, onboarding.crm_deal, "finance_onboarding_status", onboarding.status)
		_db_set_if_field(CRM_DEAL, onboarding.crm_deal, "finance_onboarding_ready", onboarding.finance_ready)

	if onboarding.get("participant_intake"):
		_db_set_if_field(INTAKE, onboarding.participant_intake, "ndis_finance_onboarding", onboarding.name)
		_db_set_if_field(INTAKE, onboarding.participant_intake, "finance_onboarding_status", onboarding.status)
		_db_set_if_field(INTAKE, onboarding.participant_intake, "finance_onboarding_ready", onboarding.finance_ready)

	frappe.db.commit()

	return {
		"doctype": FINANCE_ONBOARDING,
		"name": onboarding.name,
		"created": True,
		"message": "NDIS CRM Finance Onboarding created successfully.",
	}


@frappe.whitelist()
def create_finance_onboarding_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))

	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _get_existing_onboarding_for_deal(deal)
	if existing:
		return {
			"doctype": FINANCE_ONBOARDING,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Finance Onboarding returned.",
		}

	handover = frappe.db.get_value(HANDOVER, {"crm_deal": deal}, "name")

	if not handover:
		try:
			from ndis_crm.phase4_handover import create_handover_from_crm_deal

			result = create_handover_from_crm_deal(deal)
			handover = result.get("name")
		except ImportError:
			frappe.throw(_("Please create NDIS CRM Handover before creating finance onboarding."))

	return create_finance_onboarding_from_handover(handover)


@frappe.whitelist()
def create_financial_profile_from_onboarding(onboarding):
	_check_role()

	if not onboarding:
		frappe.throw(_("NDIS CRM Finance Onboarding is required."))

	doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)

	if doc.get("ndis_financial_profile"):
		return {
			"doctype": FINANCE_PROFILE,
			"name": doc.ndis_financial_profile,
			"created": False,
			"message": "Existing NDIS Participant Financial Profile returned.",
		}

	if not doc.get("handover"):
		frappe.throw(_("Finance Onboarding must be linked to a Handover before creating a financial profile."))

	try:
		from ndis_crm.phase4_handover import create_financial_profile_from_handover
	except ImportError:
		frappe.throw(_("Phase 4 handover financial profile bridge is not available."))

	result = create_financial_profile_from_handover(doc.handover)
	profile_name = result.get("name")

	doc.reload()
	doc.ndis_financial_profile = profile_name
	doc.save(ignore_permissions=True)

	frappe.db.commit()

	return result


@frappe.whitelist()
def validate_finance_onboarding_readiness(onboarding):
	_check_role()

	doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Finance onboarding readiness validated.",
	}


@frappe.whitelist()
def mark_ready_for_finance(onboarding):
	_check_role()

	doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)
	summary = _calculate_readiness(doc)

	if not summary["finance_ready"]:
		frappe.throw(
			_("Cannot mark Ready for Finance. Incomplete items: {0}").format(
				"; ".join(summary["incomplete"])
			)
		)

	doc.status = "Ready for Finance"
	doc.readiness_percent = summary["readiness_percent"]
	doc.finance_ready = 1
	doc.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"doctype": FINANCE_ONBOARDING,
		"name": doc.name,
		"message": "Finance Onboarding marked Ready for Finance.",
	}


@frappe.whitelist()
def mark_finance_setup_complete(onboarding):
	_check_role()

	doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)

	if doc.status not in READY_STATUSES:
		frappe.throw(_("Finance Onboarding must be Ready for Finance before it can be completed."))

	doc.status = "Completed"
	doc.finance_ready = 1
	doc.readiness_percent = 100
	doc.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"doctype": FINANCE_ONBOARDING,
		"name": doc.name,
		"message": "Finance setup marked Completed.",
	}


def validate_finance_onboarding(doc, method=None):
	summary = _calculate_readiness(doc)

	if _field_exists(FINANCE_ONBOARDING, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(FINANCE_ONBOARDING, "finance_ready"):
		doc.finance_ready = 1 if summary["finance_ready"] else 0

	if doc.status in READY_STATUSES and not summary["finance_ready"]:
		frappe.throw(
			_("Cannot set Finance Onboarding to {0}. Incomplete items: {1}").format(
				doc.status,
				"; ".join(summary["incomplete"]),
			)
		)


def on_finance_onboarding_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"NDIS CRM Finance Onboarding Summary Sync Failed",
		)


def validate_crm_deal_phase5(doc, method=None):
	if doc.status != "Won / Active Client":
		return

	finance_required = 1

	if _field_exists(CRM_DEAL, "ndis_finance_onboarding_required"):
		finance_required = doc.get("ndis_finance_onboarding_required")

	if not finance_required:
		return

	onboarding_name = doc.get("ndis_finance_onboarding") if _field_exists(CRM_DEAL, "ndis_finance_onboarding") else None

	if not onboarding_name:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Finance Onboarding must be created and completed."))

	status = frappe.db.get_value(FINANCE_ONBOARDING, onboarding_name, "status")

	if status not in COMPLETE_STATUSES:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Finance Onboarding must be Completed."))


def validate_crm_deal_phase5_combined(doc, method=None):
	"""
	Preserve Phase 2, Phase 3, and Phase 4 validators, then add Phase 5 finance onboarding validation.
	"""
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

	validate_crm_deal_phase5(doc, method)


def phase5_health_check():
	print("---- NDIS CRM Phase 5 Health Check ----")

	for dt in [
		FINANCE_ONBOARDING_SERVICE,
		FINANCE_ONBOARDING,
		HANDOVER,
		CRM_DEAL,
		INTAKE,
		"NDIS Service Line",
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'MISSING'}")

	for dt in [
		FINANCE_PROFILE,
		FUNDING_SOURCE,
		NDIS_HOUSE,
		NDIS_SERVICE_TYPE,
		NDIS_SUPPORT_ITEM,
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

	for field in [
		"finance_service_type",
		"default_support_item",
		"requires_plan_budget",
		"requires_service_booking",
	]:
		print(f"NDIS Service Line field {field}: {'OK' if _field_exists('NDIS Service Line', field) else 'MISSING / OPTIONAL'}")

	for field in [
		"ndis_finance_onboarding_required",
		"ndis_finance_onboarding",
		"finance_onboarding_status",
		"finance_onboarding_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

	print("NDIS CRM Finance Onboarding records:", frappe.db.count(FINANCE_ONBOARDING) if _doctype_exists(FINANCE_ONBOARDING) else 0)
	print("CRM Deal Phase 5 combined validator should be active through hooks.py.")
	print("---- End Phase 5 Health Check ----")
