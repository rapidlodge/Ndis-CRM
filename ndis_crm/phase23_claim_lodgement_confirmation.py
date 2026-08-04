import frappe
from frappe import _
from frappe.utils import now, nowdate


CRM_DEAL = "CRM Deal"
CRM_LEAD = "CRM Lead"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
ROSTER_REQUEST = "NDIS CRM Roster Build Request"
SERVICE_FILE = "NDIS Participant Service File"
SESSION_DRAFT = "NDIS CRM Service Session Draft"
EVIDENCE_REVIEW = "NDIS CRM Service Delivery Evidence Review"
DOWNSTREAM_PREPARATION = "NDIS CRM Downstream Preparation"
ATTENDANCE_DRAFT = "NDIS CRM Attendance Draft"
BILLING_DRAFT = "NDIS CRM Billing Draft"
CLAIM_DRAFT = "NDIS CRM Claim Draft"
INVOICE_DRAFT = "NDIS CRM Invoice Draft"
SALES_INVOICE_DRAFT_RUN = "NDIS CRM Sales Invoice Draft Run"
SALES_INVOICE_SUBMISSION_RUN = "NDIS CRM Sales Invoice Submission Run"
CLAIM_BATCH_DRAFT_RUN = "NDIS CRM Claim Batch Draft Run"
CLAIM_BATCH_SUBMISSION_RUN = "NDIS CRM Claim Batch Submission Run"
CLAIM_EXPORT_PREP_RUN = "NDIS CRM Claim Export Preparation Run"
CLAIM_EXPORT_PREP_LINE = "NDIS CRM Claim Export Preparation Line"
CLAIM_LODGEMENT_CONFIRMATION_RUN = "NDIS CRM Claim Lodgement Confirmation Run"
CLAIM_LODGEMENT_CONFIRMATION_LINE = "NDIS CRM Claim Lodgement Confirmation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

SALES_INVOICE = "Sales Invoice"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"

READY_STATUSES = ["Ready for Lodgement Confirmation", "Lodgement Confirmation Approved", "Lodgement Confirmed"]
APPROVED_STATUSES = ["Lodgement Confirmation Approved", "Lodgement Confirmed"]
SOURCE_READY_STATUSES = ["Export File Prepared"]

ALLOWED_ROLES = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"NDIS CRM Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this claim lodgement confirmation action."))


def _doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
	return bool(
		frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
		or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
	)


def _db_set_if_field(doctype, name, fieldname, value):
	if name and _field_exists(doctype, fieldname):
		frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)


def _set_if_field(doc, fieldname, value):
	if value is not None and _field_exists(doc.doctype, fieldname):
		doc.set(fieldname, value)
		return True
	return False


def _set_first_existing(doc, fieldnames, value):
	for fieldname in fieldnames:
		if _set_if_field(doc, fieldname, value):
			return fieldname
	return None


def _snapshot(doctype, name, fieldnames):
	if not name or not _doctype_exists(doctype) or not frappe.db.exists(doctype, name):
		return {}
	out = {"name": name}
	for fieldname in fieldnames:
		if _field_exists(doctype, fieldname):
			out[fieldname] = frappe.db.get_value(doctype, name, fieldname)
	return out


def _claim_batch_snapshot(claim_batch):
	return _snapshot(
		NDIS_CLAIM_BATCH,
		claim_batch,
		[
			"docstatus",
			"status",
			"claim_batch_status",
			"batch_status",
			"company",
			"participant",
			"participant_customer",
			"customer",
			"ndis_participant",
			"claim_period_start",
			"claim_period_end",
			"period_start",
			"period_end",
			"from_date",
			"to_date",
			"total_claim_amount",
			"claim_amount_total",
			"total_amount",
			"amount",
			"export_ready",
			"claim_export_ready",
			"lodgement_reference",
			"external_lodgement_reference",
			"portal_reference",
		],
	)


def _claim_line_snapshot(claim_line):
	return _snapshot(
		NDIS_CLAIM_LINE,
		claim_line,
		[
			"docstatus",
			"status",
			"claim_status",
			"claim_batch",
			"batch",
			"ndis_claim_batch",
			"sales_invoice",
			"support_item",
			"ndis_support_item",
			"service_booking",
			"ndis_service_booking",
			"plan_budget",
			"ndis_plan_budget",
			"quantity",
			"claim_quantity",
			"qty",
			"rate",
			"claim_rate",
			"amount",
			"claim_amount",
			"service_date",
			"claim_date",
			"date",
			"lodgement_reference",
			"external_lodgement_reference",
			"portal_reference",
		],
	)


def _sales_invoice_snapshot(sales_invoice):
	if not sales_invoice or not _doctype_exists(SALES_INVOICE) or not frappe.db.exists(SALES_INVOICE, sales_invoice):
		return {}
	return frappe.db.get_value(
		SALES_INVOICE,
		sales_invoice,
		["name", "docstatus", "customer", "company", "posting_date", "due_date", "grand_total", "rounded_total", "status"],
		as_dict=True,
	) or {}


def _existing_run_for_export_preparation_run(claim_export_preparation_run):
	if not _doctype_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN):
		return None
	if _field_exists(CLAIM_EXPORT_PREP_RUN, "ndis_claim_lodgement_confirmation_run"):
		existing = frappe.db.get_value(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run, "ndis_claim_lodgement_confirmation_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_LODGEMENT_CONFIRMATION_RUN, {"claim_export_preparation_run": claim_export_preparation_run}, "name")


def _existing_run_for_deal(deal):
	if not _doctype_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN):
		return None
	if _field_exists(CRM_DEAL, "ndis_claim_lodgement_confirmation_run"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_lodgement_confirmation_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_LODGEMENT_CONFIRMATION_RUN, {"crm_deal": deal}, "name")


def _get_claim_export_preparation_run_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_claim_export_preparation_run"):
		run = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_export_preparation_run")
		if run:
			return run
	if _doctype_exists(CLAIM_EXPORT_PREP_RUN):
		return frappe.db.get_value(CLAIM_EXPORT_PREP_RUN, {"crm_deal": deal}, "name")
	return None


def _is_claim_export_file_prepared(run):
	if not run or not frappe.db.exists(CLAIM_EXPORT_PREP_RUN, run):
		return False
	status, ready, generated_file = frappe.db.get_value(
		CLAIM_EXPORT_PREP_RUN,
		run,
		["status", "claim_export_preparation_run_ready", "generated_file"],
	)
	return status in SOURCE_READY_STATUSES and bool(ready) and bool(generated_file)


def _is_lodgement_confirmation_approved(run):
	if not run or not frappe.db.exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, run):
		return False
	status, ready = frappe.db.get_value(
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		run,
		["status", "claim_lodgement_confirmation_run_ready"],
	)
	return status in APPROVED_STATUSES and bool(ready)


def _source_key(row):
	return row.get("export_source_key") or "|".join(
		[
			str(row.get("service_line") or ""),
			str(row.get("ndis_claim_batch") or ""),
			str(row.get("ndis_claim_line") or ""),
			str(row.get("sales_invoice") or ""),
		]
	)


def _append_line_if_missing(doc, row_data):
	existing = {row.lodgement_source_key for row in doc.get("lodgement_lines") or [] if row.get("lodgement_source_key")}
	key = row_data.get("lodgement_source_key")
	if key and key in existing:
		return False
	doc.append("lodgement_lines", row_data)
	return True


def _build_lodgement_line_from_export_line(row, export_doc):
	claim_batch = row.get("ndis_claim_batch")
	claim_line = row.get("ndis_claim_line")
	sales_invoice = row.get("sales_invoice")
	batch_snapshot = _claim_batch_snapshot(claim_batch)
	line_snapshot = _claim_line_snapshot(claim_line) if claim_line else {}
	invoice_snapshot = _sales_invoice_snapshot(sales_invoice)
	claim_batch_docstatus = int(batch_snapshot.get("docstatus") or 0) if batch_snapshot else None
	claim_line_docstatus = int(line_snapshot.get("docstatus") or 0) if line_snapshot else None
	sales_invoice_docstatus = int(invoice_snapshot.get("docstatus") or 0) if invoice_snapshot else row.get("sales_invoice_docstatus")
	source_ready = bool(
		export_doc.get("status") == "Export File Prepared"
		and export_doc.get("generated_file")
		and row.get("export_line_status") == "Export File Prepared"
		and row.get("export_file_line_included")
		and row.get("claim_export_ready")
		and not row.get("portal_submission_authorized")
		and not row.get("export_hold")
		and claim_batch
		and batch_snapshot
		and sales_invoice
		and sales_invoice_docstatus == 1
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("plan_budget")
		and row.get("claim_amount")
	)
	return {
		"lodgement_source_key": _source_key(row),
		"ndis_claim_batch": claim_batch,
		"ndis_claim_line": claim_line,
		"claim_batch_docstatus": claim_batch_docstatus,
		"claim_line_docstatus": claim_line_docstatus,
		"claim_batch_status": batch_snapshot.get("status") or batch_snapshot.get("claim_batch_status") or batch_snapshot.get("batch_status"),
		"claim_line_status": line_snapshot.get("status") or line_snapshot.get("claim_status"),
		"sales_invoice": sales_invoice,
		"sales_invoice_docstatus": sales_invoice_docstatus,
		"sales_invoice_status": invoice_snapshot.get("status") or row.get("sales_invoice_status"),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"service_date": row.get("service_date"),
		"claim_quantity": row.get("claim_quantity"),
		"claim_unit": row.get("claim_unit") or "Hour",
		"claim_rate": row.get("claim_rate"),
		"claim_amount": row.get("claim_amount"),
		"support_item": row.get("support_item"),
		"finance_service_type": row.get("finance_service_type"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"funding_source": row.get("funding_source"),
		"default_house": row.get("default_house"),
		"invoice_group_key": row.get("invoice_group_key"),
		"generated_file": export_doc.get("generated_file"),
		"generated_file_hash": export_doc.get("generated_file_hash"),
		"export_file_source_ready": 1 if source_ready else 0,
		"lodgement_confirmation_review_complete": 0,
		"external_lodgement_reference": None,
		"external_line_reference": None,
		"portal_status": None,
		"expected_payment_date": None,
		"lodgement_confirmed": 0,
		"confirmation_hold": 0 if source_ready else 1,
		"confirmation_hold_reason": None if source_ready else "Export file source is not ready for lodgement confirmation.",
		"line_ready_for_lodgement_confirmation": 0,
		"confirmation_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_export_preparation_run(doc, source):
	created = 0
	for row in source.get("export_lines") or []:
		if row.get("export_line_status") != "Export File Prepared":
			continue
		if not row.get("export_file_line_included"):
			continue
		if _append_line_if_missing(doc, _build_lodgement_line_from_export_line(row, source)):
			created += 1
	return created


def _calculate_totals(doc):
	totals = {
		"lodgement_line_count": len(doc.get("lodgement_lines") or []),
		"claim_batch_count": 0,
		"claim_amount_total": 0,
		"lodgement_ready_count": 0,
		"lodgement_confirmed_count": 0,
		"lodgement_hold_count": 0,
		"missing_claim_batch_count": 0,
		"missing_lodgement_reference_count": 0,
	}
	batches = set()
	for row in doc.get("lodgement_lines") or []:
		try:
			totals["claim_amount_total"] += float(row.get("claim_amount") or 0)
		except Exception:
			pass
		if row.get("line_ready_for_lodgement_confirmation"):
			totals["lodgement_ready_count"] += 1
		if row.get("lodgement_confirmed"):
			totals["lodgement_confirmed_count"] += 1
		if row.get("confirmation_hold"):
			totals["lodgement_hold_count"] += 1
		if row.get("ndis_claim_batch"):
			batches.add(row.get("ndis_claim_batch"))
		else:
			totals["missing_claim_batch_count"] += 1
		if not (row.get("external_lodgement_reference") or doc.get("external_lodgement_reference")):
			totals["missing_lodgement_reference_count"] += 1
	totals["claim_batch_count"] = len(batches)
	totals["claim_amount_total"] = round(totals["claim_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _line_ids(rows, condition):
	return [row.get("service_line") or row.get("ndis_claim_line") or row.get("ndis_claim_batch") for row in rows if condition(row)]


def _calculate_readiness(doc):
	checks = [
		{"label": "Claim Export Preparation Run linked", "complete": bool(doc.get("claim_export_preparation_run"))},
		{"label": "Claim Export file prepared", "complete": _is_claim_export_file_prepared(doc.get("claim_export_preparation_run"))},
		{"label": "Generated export file linked", "complete": bool(doc.get("generated_file"))},
		{"label": "NDIS Claim Batch DocType exists", "complete": _doctype_exists(NDIS_CLAIM_BATCH)},
		{"label": "Participant Customer linked", "complete": bool(doc.get("participant_customer"))},
		{"label": "Company selected", "complete": bool(doc.get("company"))},
		{"label": "Lodgement Owner assigned", "complete": bool(doc.get("claim_lodgement_owner"))},
		{"label": "Lodgement Method selected", "complete": bool(doc.get("lodgement_method"))},
		{"label": "External Lodgement Reference entered", "complete": bool(doc.get("external_lodgement_reference"))},
		{"label": "Lodgement Date entered", "complete": bool(doc.get("lodgement_date"))},
	]
	lines = doc.get("lodgement_lines") or []
	checks.append({"label": "At least one lodgement confirmation line exists", "complete": bool(lines)})
	line_checks = [
		("All lines have NDIS Claim Batch reference", lambda row: row.get("ndis_claim_batch")),
		("All lines have Sales Invoice reference", lambda row: row.get("sales_invoice")),
		("All lines have claim amount", lambda row: row.get("claim_amount")),
		("Export file source-ready flags are complete", lambda row: row.get("export_file_source_ready")),
		("Lodgement confirmation review complete", lambda row: row.get("lodgement_confirmation_review_complete")),
		("All lines have lodgement reference through header or line", lambda row: row.get("external_lodgement_reference") or doc.get("external_lodgement_reference")),
		("No lodgement confirmation hold remains", lambda row: not row.get("confirmation_hold")),
		("All lines marked ready for lodgement confirmation", lambda row: row.get("line_ready_for_lodgement_confirmation")),
	]
	for label, condition in line_checks:
		missing = _line_ids(lines, lambda row, condition=condition: not condition(row))
		checks.append({"label": label, "complete": not missing, "details": missing})
	total = len(checks)
	complete = len([row for row in checks if row["complete"]])
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
		"readiness_percent": round((complete / total) * 100, 2) if total else 0,
		"claim_lodgement_confirmation_run_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, "claim_lodgement_confirmation_run_ready"):
		doc.claim_lodgement_confirmation_run_ready = 1 if summary["claim_lodgement_confirmation_run_ready"] else 0
	targets = [
		(CRM_DEAL, doc.get("crm_deal")),
		(HANDOVER, doc.get("handover")),
		(FINANCE_ONBOARDING, doc.get("finance_onboarding")),
		(OPERATIONS_SETUP, doc.get("operations_setup")),
		(SCHEDULE_DRAFT, doc.get("service_schedule_draft")),
		(ROSTER_REQUEST, doc.get("roster_build_request")),
		(SERVICE_FILE, doc.get("participant_service_file")),
		(SESSION_DRAFT, doc.get("service_session_draft")),
		(EVIDENCE_REVIEW, doc.get("delivery_evidence_review")),
		(DOWNSTREAM_PREPARATION, doc.get("downstream_preparation")),
		(ATTENDANCE_DRAFT, doc.get("attendance_draft")),
		(BILLING_DRAFT, doc.get("billing_draft")),
		(CLAIM_DRAFT, doc.get("claim_draft")),
		(INVOICE_DRAFT, doc.get("invoice_draft")),
		(SALES_INVOICE_DRAFT_RUN, doc.get("sales_invoice_draft_run")),
		(SALES_INVOICE_SUBMISSION_RUN, doc.get("sales_invoice_submission_run")),
		(CLAIM_BATCH_DRAFT_RUN, doc.get("claim_batch_draft_run")),
		(CLAIM_BATCH_SUBMISSION_RUN, doc.get("claim_batch_submission_run")),
		(CLAIM_EXPORT_PREP_RUN, doc.get("claim_export_preparation_run")),
		(INTAKE, doc.get("participant_intake")),
	]
	for doctype, name in targets:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_claim_lodgement_confirmation_run", doc.name)
		_db_set_if_field(doctype, name, "claim_lodgement_confirmation_status", doc.status)
		_db_set_if_field(doctype, name, "claim_lodgement_confirmation_ready", 1 if summary["claim_lodgement_confirmation_run_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_claim_lodgement_confirmation_run_from_export_preparation_run(claim_export_preparation_run):
	_check_role()
	if not claim_export_preparation_run:
		frappe.throw(_("NDIS CRM Claim Export Preparation Run is required."))
	if not frappe.db.exists(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run):
		frappe.throw(_("NDIS CRM Claim Export Preparation Run {0} was not found.").format(claim_export_preparation_run))
	existing = _existing_run_for_export_preparation_run(claim_export_preparation_run)
	if existing:
		return {"doctype": CLAIM_LODGEMENT_CONFIRMATION_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Lodgement Confirmation Run returned."}
	source = frappe.get_doc(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run)
	doc = frappe.new_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN)
	doc.status = "Draft"
	for fieldname in [
		"claim_batch_submission_run",
		"claim_batch_draft_run",
		"sales_invoice_submission_run",
		"sales_invoice_draft_run",
		"invoice_draft",
		"claim_draft",
		"billing_draft",
		"attendance_draft",
		"downstream_preparation",
		"delivery_evidence_review",
		"service_session_draft",
		"participant_service_file",
		"roster_build_request",
		"service_schedule_draft",
		"operations_setup",
		"finance_onboarding",
		"handover",
		"crm_deal",
		"crm_lead",
		"participant_intake",
		"participant_customer",
		"ndis_financial_profile",
		"participant_name",
		"ndis_number",
		"plan_start_date",
		"plan_end_date",
		"claim_period_start",
		"claim_period_end",
		"company",
		"generated_file",
		"generated_file_name",
		"generated_file_hash",
		"claim_export_owner",
		"claim_batch_submission_owner",
		"claim_batch_owner",
		"claim_owner",
		"billing_owner",
	]:
		if _field_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, fieldname):
			doc.set(fieldname, source.get(fieldname))
	doc.claim_export_preparation_run = source.name
	doc.participant_name = doc.get("participant_name") or source.get("participant_customer") or source.name
	doc.claim_lodgement_owner = frappe.session.user
	doc.lodgement_method = "Manual Portal Upload"
	doc.lodgement_date = nowdate()
	doc.confirmation_allowed = 0
	doc.payment_matching_allowed = 0
	created_count = _generate_lines_from_export_preparation_run(doc, source)
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_lodgement_confirmation_run_ready = 1 if summary["claim_lodgement_confirmation_run_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": CLAIM_LODGEMENT_CONFIRMATION_RUN,
		"name": doc.name,
		"created": True,
		"lodgement_line_count": created_count,
		"message": "NDIS CRM Claim Lodgement Confirmation Run created successfully.",
	}


@frappe.whitelist()
def create_claim_lodgement_confirmation_run_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))
	existing = _existing_run_for_deal(deal)
	if existing:
		return {"doctype": CLAIM_LODGEMENT_CONFIRMATION_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Lodgement Confirmation Run returned."}
	source_run = _get_claim_export_preparation_run_for_deal(deal)
	if not source_run:
		frappe.throw(_("Please create and prepare NDIS CRM Claim Export Preparation Run before creating Claim Lodgement Confirmation Run."))
	return create_claim_lodgement_confirmation_run_from_export_preparation_run(source_run)


@frappe.whitelist()
def generate_claim_lodgement_confirmation_lines(claim_lodgement_confirmation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN, claim_lodgement_confirmation_run)
	if not doc.get("claim_export_preparation_run"):
		frappe.throw(_("Claim Export Preparation Run is required."))
	source = frappe.get_doc(CLAIM_EXPORT_PREP_RUN, doc.claim_export_preparation_run)
	created_count = _generate_lines_from_export_preparation_run(doc, source)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Claim lodgement confirmation lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_claim_lodgement_confirmation_readiness(claim_lodgement_confirmation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN, claim_lodgement_confirmation_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Claim Lodgement Confirmation Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_lodgement_confirmation(claim_lodgement_confirmation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN, claim_lodgement_confirmation_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_lodgement_confirmation_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Lodgement Confirmation. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Lodgement Confirmation"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_lodgement_confirmation_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_LODGEMENT_CONFIRMATION_RUN, "name": doc.name, "message": "Claim Lodgement Confirmation Run marked Ready for Lodgement Confirmation."}


@frappe.whitelist()
def approve_claim_lodgement_confirmation_run(claim_lodgement_confirmation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN, claim_lodgement_confirmation_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_lodgement_confirmation_run_ready"]:
		frappe.throw(_("Cannot approve Claim Lodgement Confirmation Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Lodgement Confirmation Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_lodgement_confirmation_run_ready = 1
	doc.confirmation_allowed = 0
	doc.payment_matching_allowed = 0
	for row in doc.get("lodgement_lines") or []:
		if row.get("confirmation_status") in ["Draft", "Ready"]:
			row.confirmation_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_LODGEMENT_CONFIRMATION_RUN, "name": doc.name, "message": "Claim Lodgement Confirmation Run approved. Lodgement has not been confirmed yet."}


def _ready_lines_for_confirmation(doc):
	ready = []
	for row in doc.get("lodgement_lines") or []:
		if row.get("confirmation_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("line_ready_for_lodgement_confirmation"):
			continue
		if not row.get("lodgement_confirmation_review_complete"):
			continue
		if row.get("confirmation_hold"):
			continue
		if not (row.get("external_lodgement_reference") or doc.get("external_lodgement_reference")):
			continue
		ready.append(row)
	return ready


def _update_external_lodgement_on_claim_docs(doc, ready_lines):
	claim_batches = {row.get("ndis_claim_batch") for row in ready_lines if row.get("ndis_claim_batch")}
	claim_lines = {row.get("ndis_claim_line") for row in ready_lines if row.get("ndis_claim_line")}
	for claim_batch in claim_batches:
		if not frappe.db.exists(NDIS_CLAIM_BATCH, claim_batch):
			continue
		batch = frappe.get_doc(NDIS_CLAIM_BATCH, claim_batch)
		_set_first_existing(batch, ["status", "claim_batch_status", "batch_status"], "Lodgement Confirmed")
		_set_first_existing(batch, ["lodgement_confirmed", "claim_lodgement_confirmed"], 1)
		_set_first_existing(batch, ["lodgement_date", "external_lodgement_date", "submitted_on", "submission_date"], doc.get("lodgement_date"))
		_set_first_existing(batch, ["lodgement_reference", "external_lodgement_reference", "portal_reference", "submission_reference"], doc.get("external_lodgement_reference"))
		_set_first_existing(batch, ["external_batch_reference", "portal_batch_reference", "batch_reference"], doc.get("external_batch_reference"))
		_set_first_existing(batch, ["lodgement_method", "submission_method"], doc.get("lodgement_method"))
		_set_first_existing(batch, ["lodgement_evidence_file", "submission_evidence_file"], doc.get("lodgement_evidence_file"))
		_set_first_existing(batch, ["notes", "remarks"], f"Lodgement confirmed externally via {doc.doctype} {doc.name}. No portal/API lodgement was performed by Phase 23.")
		batch.save(ignore_permissions=True)
	for claim_line in claim_lines:
		if not frappe.db.exists(NDIS_CLAIM_LINE, claim_line):
			continue
		line = frappe.get_doc(NDIS_CLAIM_LINE, claim_line)
		_set_first_existing(line, ["status", "claim_status"], "Lodgement Confirmed")
		_set_first_existing(line, ["lodgement_confirmed", "claim_lodgement_confirmed"], 1)
		_set_first_existing(line, ["lodgement_date", "external_lodgement_date", "submitted_on", "submission_date"], doc.get("lodgement_date"))
		_set_first_existing(line, ["lodgement_reference", "external_lodgement_reference", "portal_reference", "submission_reference"], doc.get("external_lodgement_reference"))
		_set_first_existing(line, ["external_batch_reference", "portal_batch_reference", "batch_reference"], doc.get("external_batch_reference"))
		_set_first_existing(line, ["lodgement_method", "submission_method"], doc.get("lodgement_method"))
		line.save(ignore_permissions=True)
	return list(claim_batches), list(claim_lines)


@frappe.whitelist()
def confirm_external_claim_lodgement(claim_lodgement_confirmation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN, claim_lodgement_confirmation_run)
	if doc.status != "Lodgement Confirmation Approved":
		frappe.throw(_("Claim Lodgement Confirmation Run must be approved before confirmation."))
	if not doc.get("confirmation_allowed"):
		frappe.throw(_("Tick Confirmation Allowed before confirming external lodgement."))
	if doc.get("payment_matching_allowed"):
		frappe.throw(_("Payment Matching Allowed must remain unticked in Phase 23."))
	summary = _calculate_readiness(doc)
	if not summary["claim_lodgement_confirmation_run_ready"]:
		frappe.throw(_("Cannot confirm lodgement. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	ready_lines = _ready_lines_for_confirmation(doc)
	if not ready_lines:
		frappe.throw(_("No ready lodgement confirmation lines found."))
	claim_batches, claim_lines = _update_external_lodgement_on_claim_docs(doc, ready_lines)
	for row in ready_lines:
		row.lodgement_confirmed = 1
		row.confirmation_status = "Lodgement Confirmed"
		row.external_lodgement_reference = row.get("external_lodgement_reference") or doc.get("external_lodgement_reference")
		row.portal_status = row.get("portal_status") or "Externally Lodged"
	doc.status = "Lodgement Confirmed"
	doc.confirmation_allowed = 0
	doc.payment_matching_allowed = 0
	doc.confirmed_by = frappe.session.user
	doc.confirmed_on = now()
	_sync_totals(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"claim_batches": claim_batches,
		"claim_lines": claim_lines,
		"confirmed_line_count": len(ready_lines),
		"message": "External claim lodgement confirmed. No portal/API lodgement, payment, journal, remittance, write-off, recovery, or manual GL was created.",
	}


def validate_claim_lodgement_confirmation_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, "claim_lodgement_confirmation_run_ready"):
		doc.claim_lodgement_confirmation_run_ready = 1 if summary["claim_lodgement_confirmation_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["claim_lodgement_confirmation_run_ready"]:
		frappe.throw(_("Cannot set Claim Lodgement Confirmation Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Lodgement Confirmation Approved" and doc.get("confirmation_allowed"):
		frappe.throw(_("Confirmation Allowed can only be ticked after the run is approved."))
	if doc.get("payment_matching_allowed"):
		frappe.throw(_("Payment matching is not allowed in Phase 23."))


def on_claim_lodgement_confirmation_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Claim Lodgement Confirmation Run Summary Sync Failed")


def validate_crm_deal_phase23(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	required = doc.get("ndis_claim_lodgement_confirmation_run_required") if _field_exists(CRM_DEAL, "ndis_claim_lodgement_confirmation_run_required") else 0
	if not required:
		return
	run = doc.get("ndis_claim_lodgement_confirmation_run") if _field_exists(CRM_DEAL, "ndis_claim_lodgement_confirmation_run") else None
	if not run:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Lodgement Confirmation Run must be created and approved."))
	if not _is_lodgement_confirmation_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Lodgement Confirmation Run must be approved."))


def validate_crm_deal_phase23_combined(doc, method=None):
	try:
		from ndis_crm.phase22_claim_export_preparation import validate_crm_deal_phase22_combined

		validate_crm_deal_phase22_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase21_claim_batch_submission import validate_crm_deal_phase21_combined

			validate_crm_deal_phase21_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase23(doc, method)


def phase23_health_check():
	print("---- NDIS CRM Phase 23 Health Check ----")
	for dt in [
		CLAIM_LODGEMENT_CONFIRMATION_LINE,
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		CLAIM_EXPORT_PREP_RUN,
		CLAIM_EXPORT_PREP_LINE,
		CLAIM_BATCH_SUBMISSION_RUN,
		CLAIM_BATCH_DRAFT_RUN,
		CLAIM_DRAFT,
		SALES_INVOICE_SUBMISSION_RUN,
		SALES_INVOICE_DRAFT_RUN,
		INVOICE_DRAFT,
		BILLING_DRAFT,
		ATTENDANCE_DRAFT,
		DOWNSTREAM_PREPARATION,
		EVIDENCE_REVIEW,
		SESSION_DRAFT,
		SERVICE_FILE,
		ROSTER_REQUEST,
		SCHEDULE_DRAFT,
		OPERATIONS_SETUP,
		CRM_DEAL,
		HANDOVER,
		FINANCE_ONBOARDING,
		INTAKE,
		NDIS_CLAIM_BATCH,
		NDIS_CLAIM_LINE,
		SALES_INVOICE,
		"File",
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for dt in ["Payment Entry", "Journal Entry", "GL Entry", "NDIS Remittance Import", "NDIS Recovery Case", "NDIS Write Off", PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in [
		"ndis_claim_lodgement_confirmation_run_required",
		"ndis_claim_lodgement_confirmation_run",
		"claim_lodgement_confirmation_status",
		"claim_lodgement_confirmation_ready",
	]:
		print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")
	for doctype in [
		HANDOVER,
		FINANCE_ONBOARDING,
		OPERATIONS_SETUP,
		SCHEDULE_DRAFT,
		ROSTER_REQUEST,
		SERVICE_FILE,
		SESSION_DRAFT,
		EVIDENCE_REVIEW,
		DOWNSTREAM_PREPARATION,
		ATTENDANCE_DRAFT,
		BILLING_DRAFT,
		CLAIM_DRAFT,
		INVOICE_DRAFT,
		SALES_INVOICE_DRAFT_RUN,
		SALES_INVOICE_SUBMISSION_RUN,
		CLAIM_BATCH_DRAFT_RUN,
		CLAIM_BATCH_SUBMISSION_RUN,
		CLAIM_EXPORT_PREP_RUN,
		INTAKE,
	]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_claim_lodgement_confirmation_run", "claim_lodgement_confirmation_status", "claim_lodgement_confirmation_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	count = frappe.db.count(CLAIM_LODGEMENT_CONFIRMATION_RUN) if _doctype_exists(CLAIM_LODGEMENT_CONFIRMATION_RUN) else 0
	print("NDIS CRM Claim Lodgement Confirmation Run records:", count)
	print("Phase 23 records external/manual lodgement confirmation only.")
	print("Phase 23 does not lodge, submit by API, remit, pay, journal, write off, recover, or manually post GL.")
	print("---- End Phase 23 Health Check ----")
