import re

import frappe
from frappe import _


CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"

FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
FINANCE_ONBOARDING_SERVICE = "NDIS CRM Finance Onboarding Service"
FINANCE_PROFILE = "NDIS Participant Financial Profile"

PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
FUNDING_SOURCE = "NDIS Funding Source"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"

READY_STATUSES = [
	"Ready for Finance",
	"Finance Setup Started",
	"Budget Setup Complete",
	"Service Booking Complete",
	"Completed",
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
		frappe.throw(_("You do not have permission to perform this NDIS CRM finance record action."))


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


def _safe_id(value, limit=140):
	value = re.sub(r"[^A-Za-z0-9-]+", "-", str(value or "")).strip("-")
	return value[:limit] or "NDIS-CRM"


def _require_finance_doctypes():
	missing = [
		doctype
		for doctype in [
			FINANCE_ONBOARDING,
			FINANCE_ONBOARDING_SERVICE,
			PLAN_BUDGET,
			SERVICE_BOOKING,
			FUNDING_SOURCE,
			NDIS_SERVICE_TYPE,
			NDIS_SUPPORT_ITEM,
		]
		if not _doctype_exists(doctype)
	]

	if missing:
		frappe.throw(_("Missing required finance DocTypes: {0}").format(", ".join(missing)))


def _phase5_readiness(doc):
	if _field_exists(FINANCE_ONBOARDING, "finance_ready") and not doc.get("finance_ready"):
		frappe.throw(_("Finance Onboarding must be marked Ready for Finance before finance records can be created."))

	if doc.status not in READY_STATUSES:
		frappe.throw(
			_("Finance Onboarding status must be Ready for Finance or later. Current status: {0}").format(
				doc.status
			)
		)


def _ensure_ready_for_finance(doc):
	if not doc:
		frappe.throw(_("NDIS CRM Finance Onboarding is required."))

	_phase5_readiness(doc)


def _find_existing_plan_budget(onboarding_name, service_line, fallback_budget_name):
	if _field_exists(PLAN_BUDGET, "ndis_crm_finance_onboarding") and _field_exists(PLAN_BUDGET, "ndis_crm_service_line"):
		existing = frappe.db.get_value(
			PLAN_BUDGET,
			{
				"ndis_crm_finance_onboarding": onboarding_name,
				"ndis_crm_service_line": service_line,
			},
			"name",
		)
		if existing:
			return existing

	return frappe.db.get_value(PLAN_BUDGET, {"budget_name": fallback_budget_name}, "name")


def _find_existing_service_booking(onboarding_name, service_line, fallback_booking_reference):
	if _field_exists(SERVICE_BOOKING, "ndis_crm_finance_onboarding") and _field_exists(SERVICE_BOOKING, "ndis_crm_service_line"):
		existing = frappe.db.get_value(
			SERVICE_BOOKING,
			{
				"ndis_crm_finance_onboarding": onboarding_name,
				"ndis_crm_service_line": service_line,
			},
			"name",
		)
		if existing:
			return existing

	return frappe.db.get_value(SERVICE_BOOKING, {"booking_reference": fallback_booking_reference}, "name")


def _update_finance_creation_summary(doc):
	plan_budget_count = 0
	service_booking_count = 0

	for row in doc.get("service_rows") or []:
		if row.get("draft_plan_budget"):
			plan_budget_count += 1

		if row.get("service_booking"):
			service_booking_count += 1

	required_budget_rows = [row for row in doc.get("service_rows") or [] if row.get("requires_plan_budget")]
	required_booking_rows = [row for row in doc.get("service_rows") or [] if row.get("requires_service_booking")]

	if _field_exists(FINANCE_ONBOARDING, "plan_budget_count"):
		doc.plan_budget_count = plan_budget_count

	if _field_exists(FINANCE_ONBOARDING, "service_booking_count"):
		doc.service_booking_count = service_booking_count

	all_budgets_done = len(required_budget_rows) == plan_budget_count
	all_bookings_done = len(required_booking_rows) == service_booking_count

	if _field_exists(FINANCE_ONBOARDING, "finance_records_created"):
		doc.finance_records_created = 1 if all_budgets_done and all_bookings_done else 0

	if _field_exists(FINANCE_ONBOARDING, "finance_records_summary"):
		doc.finance_records_summary = (
			f"Plan Budgets: {plan_budget_count}/{len(required_budget_rows)}. "
			f"Service Bookings: {service_booking_count}/{len(required_booking_rows)}."
		)

	if doc.get("crm_deal"):
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "finance_plan_budget_count", plan_budget_count)
		_db_set_if_field(CRM_DEAL, doc.crm_deal, "finance_service_booking_count", service_booking_count)

	if doc.get("handover"):
		_db_set_if_field(HANDOVER, doc.handover, "finance_plan_budget_count", plan_budget_count)
		_db_set_if_field(HANDOVER, doc.handover, "finance_service_booking_count", service_booking_count)

	return {
		"plan_budget_count": plan_budget_count,
		"service_booking_count": service_booking_count,
		"total_required_plan_budget": len(required_budget_rows),
		"total_required_service_booking": len(required_booking_rows),
	}


def _validate_budget_row(row):
	missing = []

	if not row.get("finance_service_type"):
		missing.append("Finance Service Type")

	if not row.get("default_support_item"):
		missing.append("Default Support Item")

	if not row.get("proposed_budget_amount"):
		missing.append("Proposed Budget Amount")

	if missing:
		frappe.throw(_("Cannot create Plan Budget for {0}. Missing: {1}").format(row.get("service_line"), ", ".join(missing)))


def _validate_booking_row(row):
	missing = []

	if not row.get("finance_service_type"):
		missing.append("Finance Service Type")

	if not row.get("default_support_item"):
		missing.append("Default Support Item")

	if not row.get("proposed_service_booking_amount"):
		missing.append("Proposed Service Booking Amount")

	if missing:
		frappe.throw(_("Cannot create Service Booking for {0}. Missing: {1}").format(row.get("service_line"), ", ".join(missing)))


def _make_plan_budget(doc, row, idx):
	service_code = _safe_id(row.get("service_code") or row.get("service_line"), 40)
	budget_name = _safe_id(f"CRM-BUD-{doc.name}-{idx}-{service_code}")

	existing = row.get("draft_plan_budget") or _find_existing_plan_budget(
		onboarding_name=doc.name,
		service_line=row.get("service_line"),
		fallback_budget_name=budget_name,
	)

	if existing:
		return existing, False

	budget = frappe.new_doc(PLAN_BUDGET)
	budget.budget_name = budget_name
	budget.participant = doc.participant_customer
	budget.support_category = row.get("budget_type") or row.get("service_line")
	budget.funding_source = doc.get("funding_source")
	budget.plan_start_date = doc.get("plan_start_date")
	budget.plan_end_date = doc.get("plan_end_date")
	budget.budget_amount = row.get("proposed_budget_amount")
	budget.status = "Draft"

	_set_if_field(budget, "service_type", row.get("finance_service_type"))
	_set_if_field(budget, "support_item", row.get("default_support_item"))
	_set_if_field(budget, "budget_control_level", "Service Type")
	_set_if_field(budget, "budget_control_mode", "Warn Only")
	_set_if_field(budget, "ndis_crm_finance_onboarding", doc.name)
	_set_if_field(budget, "ndis_crm_handover", doc.get("handover"))
	_set_if_field(budget, "ndis_crm_deal", doc.get("crm_deal"))
	_set_if_field(budget, "ndis_crm_service_line", row.get("service_line"))
	_set_if_field(budget, "ndis_crm_source_notes", "Created from NDIS CRM Finance Onboarding as draft budget.")

	budget.insert(ignore_permissions=True)

	return budget.name, True


def _make_service_booking(doc, row, idx):
	service_code = _safe_id(row.get("service_code") or row.get("service_line"), 40)
	booking_reference = _safe_id(f"CRM-SB-{doc.name}-{idx}-{service_code}")

	existing = row.get("service_booking") or _find_existing_service_booking(
		onboarding_name=doc.name,
		service_line=row.get("service_line"),
		fallback_booking_reference=booking_reference,
	)

	if existing:
		return existing, False

	booking = frappe.new_doc(SERVICE_BOOKING)
	booking.booking_reference = booking_reference
	booking.participant = doc.participant_customer
	booking.support_item = row.get("default_support_item")
	booking.funding_source = doc.get("funding_source")
	booking.start_date = row.get("required_start_date") or doc.get("plan_start_date")
	booking.end_date = doc.get("plan_end_date")
	booking.booking_amount = row.get("proposed_service_booking_amount")
	booking.status = "Active"

	_set_if_field(booking, "service_type", row.get("finance_service_type"))
	_set_if_field(booking, "support_category", row.get("budget_type") or row.get("service_line"))
	_set_if_field(booking, "booking_control_mode", "Warn Only")
	_set_if_field(booking, "ndis_crm_finance_onboarding", doc.name)
	_set_if_field(booking, "ndis_crm_handover", doc.get("handover"))
	_set_if_field(booking, "ndis_crm_deal", doc.get("crm_deal"))
	_set_if_field(booking, "ndis_crm_service_line", row.get("service_line"))
	_set_if_field(booking, "ndis_crm_plan_budget", row.get("draft_plan_budget"))
	_set_if_field(booking, "ndis_crm_source_notes", "Created from NDIS CRM Finance Onboarding after explicit approval.")

	booking.insert(ignore_permissions=True)

	return booking.name, True


@frappe.whitelist()
def create_draft_plan_budgets_from_onboarding(onboarding):
	_check_role()
	_require_finance_doctypes()

	if not onboarding:
		frappe.throw(_("NDIS CRM Finance Onboarding is required."))

	doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)
	_ensure_ready_for_finance(doc)

	if not doc.get("participant_customer"):
		frappe.throw(_("Participant Customer is required."))

	if not doc.get("funding_source"):
		frappe.throw(_("Funding Source is required."))

	created = []
	existing = []

	for idx, row in enumerate(doc.get("service_rows") or [], start=1):
		if not row.get("requires_plan_budget"):
			if _field_exists(FINANCE_ONBOARDING_SERVICE, "finance_record_status"):
				row.finance_record_status = "Skipped"
			continue

		_validate_budget_row(row)
		budget_name, was_created = _make_plan_budget(doc, row, idx)

		if _field_exists(FINANCE_ONBOARDING_SERVICE, "draft_plan_budget"):
			row.draft_plan_budget = budget_name

		if _field_exists(FINANCE_ONBOARDING_SERVICE, "finance_record_status"):
			row.finance_record_status = "Budget and Booking Created" if row.get("service_booking") else "Draft Plan Budget Created"

		if was_created:
			created.append(budget_name)
		else:
			existing.append(budget_name)

	if doc.status in ["Draft", "In Review", "Ready for Finance", "Finance Setup Started"]:
		doc.status = "Budget Setup Complete"

	summary = _update_finance_creation_summary(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"created_count": len(created),
		"existing_count": len(existing),
		"created": created,
		"existing": existing,
		"summary": summary,
		"message": f"Draft Plan Budgets processed. Created: {len(created)}, Existing: {len(existing)}.",
	}


@frappe.whitelist()
def create_service_bookings_from_onboarding(onboarding):
	_check_role()
	_require_finance_doctypes()

	if not onboarding:
		frappe.throw(_("NDIS CRM Finance Onboarding is required."))

	doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)
	_ensure_ready_for_finance(doc)

	if not doc.get("allow_service_booking_creation"):
		frappe.throw(_("Service Booking creation is blocked. Tick Allow Service Booking Creation first."))

	if not doc.get("participant_customer"):
		frappe.throw(_("Participant Customer is required."))

	if not doc.get("funding_source"):
		frappe.throw(_("Funding Source is required."))

	created = []
	existing = []

	for idx, row in enumerate(doc.get("service_rows") or [], start=1):
		if not row.get("requires_service_booking"):
			continue

		_validate_booking_row(row)

		if row.get("requires_plan_budget") and not row.get("draft_plan_budget"):
			frappe.throw(_("Create/link Draft Plan Budget first for service row: {0}").format(row.get("service_line")))

		booking_name, was_created = _make_service_booking(doc, row, idx)

		if _field_exists(FINANCE_ONBOARDING_SERVICE, "service_booking"):
			row.service_booking = booking_name

		if _field_exists(FINANCE_ONBOARDING_SERVICE, "finance_record_status"):
			row.finance_record_status = "Budget and Booking Created" if row.get("draft_plan_budget") else "Service Booking Created"

		if was_created:
			created.append(booking_name)
		else:
			existing.append(booking_name)

	doc.status = "Service Booking Complete"
	summary = _update_finance_creation_summary(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"created_count": len(created),
		"existing_count": len(existing),
		"created": created,
		"existing": existing,
		"summary": summary,
		"message": f"Service Bookings processed. Created: {len(created)}, Existing: {len(existing)}.",
	}


@frappe.whitelist()
def recalculate_finance_record_summary(onboarding):
	_check_role()

	doc = frappe.get_doc(FINANCE_ONBOARDING, onboarding)
	summary = _update_finance_creation_summary(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"summary": summary,
		"message": "Finance record summary recalculated.",
	}


def validate_finance_onboarding_phase6(doc, method=None):
	_update_finance_creation_summary(doc)


def validate_finance_onboarding_phase6_combined(doc, method=None):
	try:
		from ndis_crm.phase5_finance_onboarding import validate_finance_onboarding

		validate_finance_onboarding(doc, method)
	except ImportError:
		pass

	validate_finance_onboarding_phase6(doc, method)


def on_finance_onboarding_phase6_update(doc, method=None):
	try:
		_update_finance_creation_summary(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Finance Draft Summary Update Failed")

	try:
		from ndis_crm.phase5_finance_onboarding import on_finance_onboarding_update

		on_finance_onboarding_update(doc, method)
	except ImportError:
		pass


def phase6_health_check():
	print("---- NDIS CRM Phase 6 Health Check ----")

	for dt in [
		FINANCE_ONBOARDING,
		FINANCE_ONBOARDING_SERVICE,
		PLAN_BUDGET,
		SERVICE_BOOKING,
		NDIS_SERVICE_TYPE,
		NDIS_SUPPORT_ITEM,
		FUNDING_SOURCE,
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'MISSING'}")

	for field in [
		"allow_service_booking_creation",
		"plan_budget_count",
		"service_booking_count",
		"finance_records_created",
		"finance_records_summary",
	]:
		print(f"{FINANCE_ONBOARDING} field {field}: {'OK' if _field_exists(FINANCE_ONBOARDING, field) else 'MISSING'}")

	for field in [
		"draft_plan_budget",
		"service_booking",
		"finance_record_status",
		"finance_creation_notes",
	]:
		print(f"{FINANCE_ONBOARDING_SERVICE} field {field}: {'OK' if _field_exists(FINANCE_ONBOARDING_SERVICE, field) else 'MISSING'}")

	for field in [
		"ndis_crm_finance_onboarding",
		"ndis_crm_handover",
		"ndis_crm_deal",
		"ndis_crm_service_line",
	]:
		print(f"{PLAN_BUDGET} field {field}: {'OK' if _field_exists(PLAN_BUDGET, field) else 'MISSING'}")
		print(f"{SERVICE_BOOKING} field {field}: {'OK' if _field_exists(SERVICE_BOOKING, field) else 'MISSING'}")

	print("NDIS CRM Finance Onboarding records:", frappe.db.count(FINANCE_ONBOARDING))
	print("NDIS Plan Budget records:", frappe.db.count(PLAN_BUDGET))
	print("NDIS Service Booking records:", frappe.db.count(SERVICE_BOOKING))
	print("---- End Phase 6 Health Check ----")
