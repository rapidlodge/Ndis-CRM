import frappe
from frappe import _


CRM_LEAD = "CRM Lead"
CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"

HANDOVER = "NDIS CRM Handover"
HANDOVER_ITEM = "NDIS CRM Handover Checklist Item"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
FUNDING_SOURCE = "NDIS Funding Source"
NDIS_HOUSE = "NDIS House"

COMPLETE_CHECKLIST_STATUSES = ["Completed", "Not Required"]
READY_HANDOVER_STATUSES = ["Ready for Operations", "Handed Over", "Accepted"]

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
		frappe.throw(_("You do not have permission to perform this NDIS CRM handover action."))


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


def _first_existing(doctype, names):
	if not _doctype_exists(doctype):
		return None

	for name in names:
		if frappe.db.exists(doctype, name):
			return name

	return frappe.db.get_value(doctype, {}, "name")


def _participant_name_from_deal(deal_doc):
	return (
		_get(deal_doc, "participant_name")
		or _get(deal_doc, "lead_name")
		or _get(deal_doc, "organization_name")
		or deal_doc.name
	)


def _find_intake_for_deal(deal_doc):
	lead = deal_doc.get("lead")

	if lead and _doctype_exists(INTAKE):
		intake = frappe.db.get_value(INTAKE, {"participant_lead": lead}, "name")
		if intake:
			return intake

	if _doctype_exists(INTAKE):
		return frappe.db.get_value(INTAKE, {"opportunity": deal_doc.name}, "name")

	return None


def _existing_handover_for_deal(deal_name):
	if _field_exists(CRM_DEAL, "ndis_handover"):
		existing = frappe.db.get_value(CRM_DEAL, deal_name, "ndis_handover")
		if existing:
			return existing

	if _doctype_exists(HANDOVER):
		return frappe.db.get_value(HANDOVER, {"crm_deal": deal_name}, "name")

	return None


def _get_service_lines_from_deal(deal_doc):
	if not _field_exists(CRM_DEAL, "ndis_service_interests"):
		return []

	service_lines = []

	for row in deal_doc.get("ndis_service_interests") or []:
		if row.get("service_line") and row.get("service_line") not in service_lines:
			service_lines.append(row.get("service_line"))

	return service_lines


def _get_service_codes(service_lines):
	codes = []

	for service_line in service_lines:
		code = frappe.db.get_value("NDIS Service Line", service_line, "service_code") or service_line
		if code and code not in codes:
			codes.append(code)

	return codes


def _base_checklist_items(finance_available=False):
	items = [
		{
			"category": "Compliance",
			"item": "Consent to contact and share information verified",
			"is_required": 1,
			"owner_role": "NDIS Intake Officer",
		},
		{
			"category": "Compliance",
			"item": "Required documents collected and reviewed",
			"is_required": 1,
			"owner_role": "NDIS Intake Officer",
		},
		{
			"category": "Funding",
			"item": "Funding verified against current NDIS plan",
			"is_required": 1,
			"owner_role": "NDIS Service Manager",
		},
		{
			"category": "Agreement",
			"item": "Service agreement signed or confirmed not required",
			"is_required": 1,
			"owner_role": "NDIS Service Manager",
		},
		{
			"category": "Operations",
			"item": "Operations owner assigned",
			"is_required": 1,
			"owner_role": "NDIS Service Manager",
		},
		{
			"category": "CRM",
			"item": "Participant Customer record created or linked",
			"is_required": 1,
			"owner_role": "NDIS CRM Manager",
		},
	]

	if finance_available:
		items.append({
			"category": "Finance",
			"item": "NDIS Participant Financial Profile created or linked",
			"is_required": 1,
			"owner_role": "NDIS Plan Management Officer",
		})

	return items


def _service_specific_checklist_items(service_codes):
	service_map = {
		"DAILY_LIFE": [
			("Operations", "Daily support schedule confirmed", "NDIS Service Manager"),
			("Rostering", "Support worker skill requirements captured", "NDIS Service Manager"),
			("Clinical", "Medication prompts / personal care risks reviewed", "NDIS Service Manager"),
		],
		"SIL": [
			("SIL", "SIL house or vacancy confirmed", "NDIS Service Manager"),
			("SIL", "Support ratio and overnight model confirmed", "NDIS Service Manager"),
			("Rostering", "SIL roster / support model reviewed", "NDIS Service Manager"),
			("Clinical", "Behaviour support and risk information reviewed", "NDIS Service Manager"),
			("Clinical", "Medication and manual handling requirements reviewed", "NDIS Service Manager"),
		],
		"COMMUNITY_PARTICIPATION": [
			("Operations", "Community access goals and activity needs confirmed", "NDIS Service Manager"),
			("Transport", "Transport requirement checked for community shifts", "NDIS Service Manager"),
		],
		"THERAPY": [
			("Clinical", "Therapy discipline confirmed", "NDIS Service Manager"),
			("Clinical", "Therapist or clinical owner assigned", "NDIS Service Manager"),
			("Clinical", "Referral / report requirements reviewed", "NDIS Service Manager"),
		],
		"SUPPORT_COORDINATION": [
			("Support Coordination", "Support coordinator assigned", "NDIS Service Manager"),
			("Support Coordination", "Provider gaps and crisis risks captured", "NDIS Service Manager"),
		],
		"BEHAVIOUR_SUPPORT": [
			("Behaviour Support", "Behaviour support practitioner assigned", "NDIS Service Manager"),
			("Behaviour Support", "BSP / restrictive practice status reviewed", "NDIS Service Manager"),
			("Behaviour Support", "Incident history reviewed where available", "NDIS Service Manager"),
		],
		"TRANSPORT": [
			("Transport", "Transport schedule, destination and frequency confirmed", "NDIS Service Manager"),
			("Transport", "Vehicle / worker transport requirements reviewed", "NDIS Service Manager"),
		],
		"ASSISTIVE_TECHNOLOGY": [
			("Assistive Technology", "AT assessment and quote pathway confirmed", "NDIS Service Manager"),
			("Finance", "Supplier / quote details captured for finance follow-up", "NDIS Plan Management Officer"),
		],
		"PLAN_MANAGEMENT": [
			("Plan Management", "Invoice receiving channel confirmed", "NDIS Plan Management Officer"),
			("Plan Management", "Statement preference confirmed", "NDIS Plan Management Officer"),
			("Plan Management", "Previous plan manager transition details captured", "NDIS Plan Management Officer"),
		],
	}

	items = []

	for code in service_codes:
		for category, item, owner_role in service_map.get(code, []):
			items.append({
				"category": category,
				"item": item,
				"is_required": 1,
				"owner_role": owner_role,
			})

	return items


def _append_checklist_items(handover_doc, service_lines):
	existing_items = {row.item for row in handover_doc.get("checklist_items") or []}
	finance_available = _doctype_exists(FINANCE_PROFILE)
	service_codes = _get_service_codes(service_lines)

	checklist = _base_checklist_items(finance_available=finance_available)
	checklist += _service_specific_checklist_items(service_codes)

	for row in checklist:
		if row["item"] in existing_items:
			continue

		handover_doc.append("checklist_items", {
			"category": row["category"],
			"item": row["item"],
			"is_required": row["is_required"],
			"status": "Pending",
			"owner_role": row["owner_role"],
		})


def _calculate_readiness(handover_doc):
	required_items = [row for row in handover_doc.get("checklist_items") or [] if row.get("is_required")]
	complete_items = [row for row in required_items if row.get("status") in COMPLETE_CHECKLIST_STATUSES]

	total_required = len(required_items)
	complete_required = len(complete_items)
	percent = round((complete_required / total_required) * 100, 2) if total_required else 0

	incomplete_items = [
		row.get("item")
		for row in required_items
		if row.get("status") not in COMPLETE_CHECKLIST_STATUSES
	]

	return {
		"total_required": total_required,
		"complete_required": complete_required,
		"readiness_percent": percent,
		"handover_ready": total_required > 0 and complete_required == total_required,
		"incomplete_items": incomplete_items,
	}


def _sync_handover_summary_to_links(handover_doc):
	summary = _calculate_readiness(handover_doc)

	if _field_exists(HANDOVER, "readiness_percent"):
		handover_doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(HANDOVER, "handover_ready"):
		handover_doc.handover_ready = 1 if summary["handover_ready"] else 0

	if handover_doc.get("crm_deal"):
		_db_set_if_field(CRM_DEAL, handover_doc.crm_deal, "handover_readiness_percent", summary["readiness_percent"])
		_db_set_if_field(CRM_DEAL, handover_doc.crm_deal, "handover_ready", 1 if summary["handover_ready"] else 0)
		_db_set_if_field(CRM_DEAL, handover_doc.crm_deal, "ndis_handover", handover_doc.name)

	if handover_doc.get("participant_intake"):
		_db_set_if_field(INTAKE, handover_doc.participant_intake, "handover_readiness_percent", summary["readiness_percent"])
		_db_set_if_field(INTAKE, handover_doc.participant_intake, "handover_ready", 1 if summary["handover_ready"] else 0)
		_db_set_if_field(INTAKE, handover_doc.participant_intake, "ndis_handover", handover_doc.name)

	return summary


@frappe.whitelist()
def create_handover_from_crm_deal(deal):
	_check_role()

	if not deal:
		frappe.throw(_("CRM Deal is required."))

	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))

	existing = _existing_handover_for_deal(deal)
	if existing:
		return {
			"doctype": HANDOVER,
			"name": existing,
			"created": False,
			"message": "Existing NDIS CRM Handover returned.",
		}

	deal_doc = frappe.get_doc(CRM_DEAL, deal)
	participant_name = _participant_name_from_deal(deal_doc)
	intake = _find_intake_for_deal(deal_doc)
	service_lines = _get_service_lines_from_deal(deal_doc)

	handover = frappe.new_doc(HANDOVER)
	handover.status = "Checklist Pending"
	handover.handover_type = _get(deal_doc, "pipeline_type") or _get(deal_doc, "opportunity_type_ndis") or "General Intake"
	handover.crm_deal = deal_doc.name
	handover.crm_lead = deal_doc.get("lead")
	handover.participant_intake = intake
	handover.participant_name = participant_name
	handover.ndis_number = _get(deal_doc, "ndis_number")
	handover.date_of_birth = _get(deal_doc, "participant_dob")
	handover.plan_start_date = _get(deal_doc, "plan_start_date")
	handover.plan_end_date = _get(deal_doc, "plan_end_date")
	handover.plan_management_type = _get(deal_doc, "plan_management_type")
	handover.target_start_date = _get(deal_doc, "estimated_start_date")
	handover.funding_verified = 1 if _get(deal_doc, "funding_verified") else 0
	handover.service_agreement_status = _get(deal_doc, "service_agreement_status")
	handover.required_documents_collected = 1 if _get(deal_doc, "required_documents_collected") else 0
	handover.participant_customer = _get(deal_doc, "participant_customer")

	_set_if_field(handover, "funding_source", _get(deal_doc, "ndis_default_funding_source"))
	_set_if_field(handover, "default_house", _get(deal_doc, "ndis_default_house"))
	_set_if_field(handover, "default_cost_center", _get(deal_doc, "ndis_default_cost_center"))

	_append_checklist_items(handover, service_lines)

	summary = _calculate_readiness(handover)
	handover.readiness_percent = summary["readiness_percent"]
	handover.handover_ready = 1 if summary["handover_ready"] else 0

	handover.insert(ignore_permissions=False)

	_db_set_if_field(CRM_DEAL, deal_doc.name, "ndis_handover", handover.name)
	_db_set_if_field(CRM_DEAL, deal_doc.name, "handover_readiness_percent", handover.readiness_percent)
	_db_set_if_field(CRM_DEAL, deal_doc.name, "handover_ready", handover.handover_ready)

	if intake:
		_db_set_if_field(INTAKE, intake, "ndis_handover", handover.name)
		_db_set_if_field(INTAKE, intake, "handover_readiness_percent", handover.readiness_percent)
		_db_set_if_field(INTAKE, intake, "handover_ready", handover.handover_ready)

	frappe.db.commit()

	return {
		"doctype": HANDOVER,
		"name": handover.name,
		"created": True,
		"message": "NDIS CRM Handover created successfully.",
	}


@frappe.whitelist()
def create_customer_from_handover(handover):
	_check_role()

	if not handover:
		frappe.throw(_("NDIS CRM Handover is required."))

	doc = frappe.get_doc(HANDOVER, handover)

	if doc.get("participant_customer"):
		return {
			"doctype": "Customer",
			"name": doc.participant_customer,
			"created": False,
			"message": "Existing Customer returned.",
		}

	customer = frappe.new_doc("Customer")
	customer.customer_name = doc.get("participant_name") or doc.name
	customer.customer_type = "Individual"

	customer_group = _first_existing("Customer Group", ["Individual", "All Customer Groups", "Commercial"])
	territory = _first_existing("Territory", ["All Territories", "Australia"])

	_set_if_field(customer, "customer_group", customer_group)
	_set_if_field(customer, "territory", territory)
	_set_if_field(customer, "custom_is_ndis_participant", 1)
	_set_if_field(customer, "custom_ndis_number", doc.get("ndis_number"))
	_set_if_field(customer, "custom_ndis_funding_source", doc.get("funding_source"))
	_set_if_field(customer, "custom_ndis_default_house", doc.get("default_house"))

	customer.insert(ignore_permissions=True)

	doc.participant_customer = customer.name
	doc.save(ignore_permissions=True)

	if doc.get("crm_deal"):
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "participant_customer", customer.name)

	if doc.get("participant_intake"):
		_db_set_if_field(INTAKE, doc.participant_intake, "participant_customer", customer.name)

	frappe.db.commit()

	return {
		"doctype": "Customer",
		"name": customer.name,
		"created": True,
		"message": "Customer created and linked successfully.",
	}


@frappe.whitelist()
def create_financial_profile_from_handover(handover):
	_check_role()

	if not _doctype_exists(FINANCE_PROFILE):
		frappe.throw(_("NDIS Finance is not installed or NDIS Participant Financial Profile DocType is missing."))

	doc = frappe.get_doc(HANDOVER, handover)

	if not doc.get("participant_customer"):
		create_customer_from_handover(handover)
		doc.reload()

	existing = frappe.db.get_value(
		FINANCE_PROFILE,
		{"participant": doc.participant_customer},
		"name",
	)

	if existing:
		_set_if_field(doc, "ndis_financial_profile", existing)
		doc.save(ignore_permissions=True)

		if doc.get("crm_deal"):
			_db_set_if_field(CRM_DEAL, doc.crm_deal, "ndis_financial_profile", existing)

		if doc.get("participant_intake"):
			_db_set_if_field(INTAKE, doc.participant_intake, "ndis_financial_profile", existing)

		_db_set_if_field("Customer", doc.participant_customer, "custom_ndis_financial_profile", existing)
		frappe.db.commit()

		return {
			"doctype": FINANCE_PROFILE,
			"name": existing,
			"created": False,
			"message": "Existing NDIS Participant Financial Profile linked.",
		}

	profile = frappe.new_doc(FINANCE_PROFILE)
	_set_if_field(profile, "profile_name", f"{doc.participant_name} - NDIS Financial Profile")
	_set_if_field(profile, "participant", doc.participant_customer)
	_set_if_field(profile, "ndis_number", doc.get("ndis_number"))
	_set_if_field(profile, "funding_source", doc.get("funding_source"))
	_set_if_field(profile, "plan_start_date", doc.get("plan_start_date"))
	_set_if_field(profile, "plan_end_date", doc.get("plan_end_date"))
	_set_if_field(profile, "default_house", doc.get("default_house"))
	_set_if_field(profile, "default_cost_center", doc.get("default_cost_center"))
	_set_if_field(profile, "billing_hold", 0)
	_set_if_field(profile, "active", 1)

	profile.insert(ignore_permissions=True)

	_set_if_field(doc, "ndis_financial_profile", profile.name)
	doc.save(ignore_permissions=True)

	if doc.get("crm_deal"):
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "ndis_financial_profile", profile.name)

	if doc.get("participant_intake"):
		_db_set_if_field(INTAKE, doc.participant_intake, "ndis_financial_profile", profile.name)

	_db_set_if_field("Customer", doc.participant_customer, "custom_ndis_financial_profile", profile.name)

	frappe.db.commit()

	return {
		"doctype": FINANCE_PROFILE,
		"name": profile.name,
		"created": True,
		"message": "NDIS Participant Financial Profile created successfully.",
	}


@frappe.whitelist()
def recalculate_handover_readiness(handover):
	_check_role()

	doc = frappe.get_doc(HANDOVER, handover)
	summary = _sync_handover_summary_to_links(doc)
	doc.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Handover readiness recalculated.",
	}


@frappe.whitelist()
def mark_handover_ready(handover):
	_check_role()

	doc = frappe.get_doc(HANDOVER, handover)
	summary = _calculate_readiness(doc)

	if not summary["handover_ready"]:
		frappe.throw(
			_("Cannot mark handover as ready. Incomplete checklist items: {0}").format(
				", ".join(summary["incomplete_items"])
			)
		)

	doc.status = "Ready for Operations"
	doc.readiness_percent = summary["readiness_percent"]
	doc.handover_ready = 1
	doc.save(ignore_permissions=True)

	if doc.get("crm_deal"):
		deal_doc = frappe.get_doc(CRM_DEAL, doc.crm_deal)
		_set_if_field(deal_doc, "handover_status", "Ready")
		_set_if_field(deal_doc, "ndis_handover", doc.name)
		_set_if_field(deal_doc, "handover_readiness_percent", 100)
		_set_if_field(deal_doc, "handover_ready", 1)

		if deal_doc.status != "Handover to Operations":
			deal_doc.status = "Handover to Operations"

		deal_doc.save(ignore_permissions=True)

	frappe.db.commit()

	return {
		"doctype": HANDOVER,
		"name": doc.name,
		"message": "Handover marked Ready for Operations.",
	}


def validate_handover(doc, method=None):
	summary = _calculate_readiness(doc)

	if _field_exists(HANDOVER, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]

	if _field_exists(HANDOVER, "handover_ready"):
		doc.handover_ready = 1 if summary["handover_ready"] else 0

	if doc.status in READY_HANDOVER_STATUSES and not summary["handover_ready"]:
		frappe.throw(
			_("Cannot set handover to {0}. Incomplete checklist items: {1}").format(
				doc.status,
				", ".join(summary["incomplete_items"]),
			)
		)


def on_handover_update(doc, method=None):
	try:
		_sync_handover_summary_to_links(doc)
	except Exception:
		frappe.log_error(
			frappe.get_traceback(),
			"NDIS CRM Handover Summary Sync Failed",
		)


def validate_crm_deal_phase4(doc, method=None):
	if doc.status not in ["Handover to Operations", "Won / Active Client"]:
		return

	errors = []

	if _field_exists(CRM_DEAL, "funding_verified") and not doc.get("funding_verified"):
		errors.append("Funding must be verified.")

	if _field_exists(CRM_DEAL, "required_documents_collected") and not doc.get("required_documents_collected"):
		errors.append("Required documents must be collected.")

	if _field_exists(CRM_DEAL, "service_agreement_status"):
		if doc.get("service_agreement_status") not in ["Signed", "Not Required"]:
			errors.append("Service Agreement Status must be Signed or Not Required.")

	handover_name = doc.get("ndis_handover") if _field_exists(CRM_DEAL, "ndis_handover") else None

	if not handover_name:
		errors.append("NDIS CRM Handover must be created and linked.")
	else:
		handover_status = frappe.db.get_value(HANDOVER, handover_name, "status")
		handover_ready = frappe.db.get_value(HANDOVER, handover_name, "handover_ready")

		if doc.status == "Handover to Operations":
			if handover_status not in READY_HANDOVER_STATUSES or not handover_ready:
				errors.append("NDIS CRM Handover must be Ready for Operations.")

		if doc.status == "Won / Active Client":
			if handover_status not in ["Handed Over", "Accepted"]:
				errors.append("NDIS CRM Handover must be Handed Over or Accepted before marking Deal as Won / Active Client.")

	if errors:
		frappe.throw(_("Cannot move CRM Deal to {0}: {1}").format(doc.status, " ".join(errors)))


def validate_crm_deal_phase4_combined(doc, method=None):
	"""
	Keep Phase 2 and Phase 3 validations alive, then add Phase 4 handover validation.
	"""
	try:
		from ndis_crm.phase3_documents import validate_crm_deal_combined

		validate_crm_deal_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase2_api import validate_crm_deal

			validate_crm_deal(doc, method)
		except ImportError:
			pass

	validate_crm_deal_phase4(doc, method)


def phase4_health_check():
	print("---- NDIS CRM Phase 4 Health Check ----")

	for dt in [
		HANDOVER_ITEM,
		HANDOVER,
		CRM_LEAD,
		CRM_DEAL,
		INTAKE,
		"Customer",
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'MISSING'}")

	print(f"{FINANCE_PROFILE}: {'OK' if _doctype_exists(FINANCE_PROFILE) else 'OPTIONAL / MISSING'}")
	print(f"{FUNDING_SOURCE}: {'OK' if _doctype_exists(FUNDING_SOURCE) else 'OPTIONAL / MISSING'}")
	print(f"{NDIS_HOUSE}: {'OK' if _doctype_exists(NDIS_HOUSE) else 'OPTIONAL / MISSING'}")

	for field in [
		"ndis_handover",
		"handover_readiness_percent",
		"handover_ready",
		"ndis_financial_profile",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING / OPTIONAL'}")

	print("NDIS CRM Handover records:", frappe.db.count(HANDOVER) if _doctype_exists(HANDOVER) else 0)
	print("CRM Deal Phase 4 combined validator should be active through hooks.py.")
	print("---- End Phase 4 Health Check ----")
