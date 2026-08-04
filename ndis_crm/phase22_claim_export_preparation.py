import csv
import hashlib
import io
import json

import frappe
from frappe import _
from frappe.utils import now
from frappe.utils.file_manager import save_file


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
CLAIM_BATCH_SUBMISSION_LINE = "NDIS CRM Claim Batch Submission Line"
CLAIM_EXPORT_PREP_RUN = "NDIS CRM Claim Export Preparation Run"
CLAIM_EXPORT_PREP_LINE = "NDIS CRM Claim Export Preparation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

SALES_INVOICE = "Sales Invoice"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"

READY_STATUSES = ["Ready for Export File Preparation", "Export Preparation Approved", "Export File Prepared"]
APPROVED_STATUSES = ["Export Preparation Approved", "Export File Prepared"]
SOURCE_READY_STATUSES = ["Claim Batch Export Ready"]

ALLOWED_ROLES = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"NDIS CRM Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this claim export preparation action."))


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


def _existing_run_for_claim_batch_submission_run(claim_batch_submission_run):
	if not _doctype_exists(CLAIM_EXPORT_PREP_RUN):
		return None
	if _field_exists(CLAIM_BATCH_SUBMISSION_RUN, "ndis_claim_export_preparation_run"):
		existing = frappe.db.get_value(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run, "ndis_claim_export_preparation_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_EXPORT_PREP_RUN, {"claim_batch_submission_run": claim_batch_submission_run}, "name")


def _existing_run_for_deal(deal):
	if not _doctype_exists(CLAIM_EXPORT_PREP_RUN):
		return None
	if _field_exists(CRM_DEAL, "ndis_claim_export_preparation_run"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_export_preparation_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_EXPORT_PREP_RUN, {"crm_deal": deal}, "name")


def _get_claim_batch_submission_run_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_claim_batch_submission_run"):
		run = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_batch_submission_run")
		if run:
			return run
	if _doctype_exists(CLAIM_BATCH_SUBMISSION_RUN):
		return frappe.db.get_value(CLAIM_BATCH_SUBMISSION_RUN, {"crm_deal": deal}, "name")
	return None


def _is_claim_batch_submission_export_ready(run):
	if not run or not frappe.db.exists(CLAIM_BATCH_SUBMISSION_RUN, run):
		return False
	status, ready = frappe.db.get_value(CLAIM_BATCH_SUBMISSION_RUN, run, ["status", "claim_batch_submission_run_ready"])
	return status in SOURCE_READY_STATUSES and bool(ready)


def _is_claim_export_prep_approved(run):
	if not run or not frappe.db.exists(CLAIM_EXPORT_PREP_RUN, run):
		return False
	status, ready = frappe.db.get_value(CLAIM_EXPORT_PREP_RUN, run, ["status", "claim_export_preparation_run_ready"])
	return status in APPROVED_STATUSES and bool(ready)


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
			"participant_customer",
			"customer",
			"claim_period_start",
			"claim_period_end",
			"total_claim_amount",
			"claim_amount_total",
			"total_amount",
			"amount",
			"export_ready",
			"claim_export_ready",
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
			"sales_invoice",
			"support_item",
			"service_booking",
			"plan_budget",
			"qty",
			"rate",
			"claim_amount",
			"service_date",
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


def _source_key(row):
	return row.get("claim_batch_source_key") or "|".join(
		[
			str(row.get("service_line") or ""),
			str(row.get("ndis_claim_batch") or ""),
			str(row.get("ndis_claim_line") or ""),
			str(row.get("sales_invoice") or ""),
		]
	)


def _append_line_if_missing(doc, row_data):
	existing = {row.export_source_key for row in doc.get("export_lines") or [] if row.get("export_source_key")}
	key = row_data.get("export_source_key")
	if key and key in existing:
		return False
	doc.append("export_lines", row_data)
	return True


def _batch_is_export_ready(claim_batch):
	snapshot = _claim_batch_snapshot(claim_batch)
	if not snapshot or int(snapshot.get("docstatus") or 0) != 0:
		return False
	status = snapshot.get("status") or snapshot.get("claim_batch_status") or snapshot.get("batch_status")
	explicit_ready = snapshot.get("export_ready") or snapshot.get("claim_export_ready")
	return bool(explicit_ready or status in ["Export Ready", "Claim Batch Export Ready", "Draft"])


def _line_is_draft_or_missing(claim_line):
	if not claim_line:
		return True
	snapshot = _claim_line_snapshot(claim_line)
	return bool(snapshot and int(snapshot.get("docstatus") or 0) == 0)


def _build_export_line_from_submission_line(row):
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
		row.get("submission_status") == "Export Ready"
		and row.get("claim_export_ready")
		and row.get("line_ready_for_claim_batch_export")
		and row.get("submission_authorized")
		and not row.get("submission_hold")
		and claim_batch
		and _batch_is_export_ready(claim_batch)
		and _line_is_draft_or_missing(claim_line)
		and sales_invoice
		and sales_invoice_docstatus == 1
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("plan_budget")
		and row.get("claim_amount")
	)
	return {
		"export_source_key": _source_key(row),
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
		"claim_batch_export_source_ready": 1 if source_ready else 0,
		"export_schema_review_complete": 0,
		"export_file_authorized": 0,
		"portal_submission_authorized": 0,
		"claim_export_ready": 0,
		"claim_submission_ready": 0,
		"export_hold": 0 if source_ready else 1,
		"export_hold_reason": None if source_ready else "Claim batch export source is not ready for export file preparation.",
		"line_ready_for_export_file": 0,
		"export_file_line_included": 0,
		"export_line_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_submission_run(doc, source):
	created = 0
	for row in source.get("submission_lines") or []:
		if row.get("submission_status") != "Export Ready" or not row.get("claim_export_ready"):
			continue
		if _append_line_if_missing(doc, _build_export_line_from_submission_line(row)):
			created += 1
	return created


def _calculate_totals(doc):
	batches = set()
	totals = {
		"export_line_count": len(doc.get("export_lines") or []),
		"claim_batch_count": 0,
		"claim_amount_total": 0,
		"export_ready_count": 0,
		"export_file_line_count": 0,
		"export_hold_count": 0,
		"missing_claim_batch_count": 0,
		"missing_sales_invoice_count": 0,
	}
	for row in doc.get("export_lines") or []:
		totals["claim_amount_total"] += float(row.get("claim_amount") or 0)
		totals["export_ready_count"] += 1 if row.get("line_ready_for_export_file") else 0
		totals["export_file_line_count"] += 1 if row.get("export_file_line_included") else 0
		totals["export_hold_count"] += 1 if row.get("export_hold") else 0
		if row.get("ndis_claim_batch"):
			batches.add(row.get("ndis_claim_batch"))
		else:
			totals["missing_claim_batch_count"] += 1
		if not row.get("sales_invoice"):
			totals["missing_sales_invoice_count"] += 1
	totals["claim_batch_count"] = len(batches)
	totals["claim_amount_total"] = round(totals["claim_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(CLAIM_EXPORT_PREP_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _calculate_readiness(doc):
	lines = doc.get("export_lines") or []
	checks = [
		("Claim Batch Submission Run linked", bool(doc.get("claim_batch_submission_run")), []),
		("Claim Batch Submission Run export-ready", _is_claim_batch_submission_export_ready(doc.get("claim_batch_submission_run")), []),
		("NDIS Claim Batch DocType exists", _doctype_exists(NDIS_CLAIM_BATCH), []),
		("NDIS Claim Line DocType exists", _doctype_exists(NDIS_CLAIM_LINE), []),
		("Participant Customer linked", bool(doc.get("participant_customer")), []),
		("Company selected", bool(doc.get("company")), []),
		("Export Owner assigned", bool(doc.get("claim_export_owner")), []),
		("Export Format selected", bool(doc.get("export_format")), []),
		("At least one export preparation line exists", bool(lines), []),
	]
	line_checks = [
		("All lines have NDIS Claim Batch reference", lambda row: row.get("ndis_claim_batch")),
		("All linked NDIS Claim Batches are export-ready/draft", lambda row: not row.get("ndis_claim_batch") or _batch_is_export_ready(row.get("ndis_claim_batch"))),
		("All linked NDIS Claim Lines are still Draft", lambda row: not row.get("ndis_claim_line") or _line_is_draft_or_missing(row.get("ndis_claim_line"))),
		("All lines have submitted Sales Invoice reference", lambda row: row.get("sales_invoice")),
		("All linked Sales Invoices are submitted", lambda row: not row.get("sales_invoice") or int((_sales_invoice_snapshot(row.get("sales_invoice")).get("docstatus") or 0)) == 1),
		("All lines have support item", lambda row: row.get("support_item")),
		("All lines have service booking", lambda row: row.get("service_booking")),
		("All lines have plan budget", lambda row: row.get("plan_budget")),
		("All lines have claim amount", lambda row: row.get("claim_amount")),
		("Claim batch export source-ready flags are complete", lambda row: row.get("claim_batch_export_source_ready")),
		("Export schema review complete", lambda row: row.get("export_schema_review_complete")),
		("Export file authorization complete", lambda row: row.get("export_file_authorized")),
		("Portal submission authorization remains blocked in Phase 22", lambda row: not row.get("portal_submission_authorized")),
		("No export preparation hold remains", lambda row: not row.get("export_hold")),
		("All lines marked ready for export file", lambda row: row.get("line_ready_for_export_file")),
	]
	for label, predicate in line_checks:
		missing = [row.get("service_line") or row.idx for row in lines if not predicate(row)]
		checks.append((label, not missing, missing))
	total = len(checks)
	complete = len([row for row in checks if row[1]])
	incomplete = []
	for label, is_complete, details in checks:
		if is_complete:
			continue
		if details:
			label += ": " + ", ".join([str(x) for x in details if x])
		incomplete.append(label)
	return {
		"total_checks": total,
		"complete_checks": complete,
		"readiness_percent": round((complete / total) * 100, 2) if total else 0,
		"claim_export_preparation_run_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(CLAIM_EXPORT_PREP_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_EXPORT_PREP_RUN, "claim_export_preparation_run_ready"):
		doc.claim_export_preparation_run_ready = 1 if summary["claim_export_preparation_run_ready"] else 0
	for doctype, name in [
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
		(INTAKE, doc.get("participant_intake")),
	]:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_claim_export_preparation_run", doc.name)
		_db_set_if_field(doctype, name, "claim_export_preparation_status", doc.status)
		_db_set_if_field(doctype, name, "claim_export_preparation_ready", 1 if summary["claim_export_preparation_run_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_claim_export_preparation_run_from_submission_run(claim_batch_submission_run):
	_check_role()
	if not claim_batch_submission_run:
		frappe.throw(_("NDIS CRM Claim Batch Submission Run is required."))
	if not frappe.db.exists(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run):
		frappe.throw(_("NDIS CRM Claim Batch Submission Run {0} was not found.").format(claim_batch_submission_run))
	existing = _existing_run_for_claim_batch_submission_run(claim_batch_submission_run)
	if existing:
		return {"doctype": CLAIM_EXPORT_PREP_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Export Preparation Run returned."}
	source = frappe.get_doc(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run)
	doc = frappe.new_doc(CLAIM_EXPORT_PREP_RUN)
	for fieldname in [
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
		"ndis_number",
		"plan_start_date",
		"plan_end_date",
		"claim_period_start",
		"claim_period_end",
		"company",
		"claim_batch_submission_owner",
		"claim_batch_owner",
		"claim_owner",
		"billing_owner",
	]:
		doc.set(fieldname, source.get(fieldname))
	doc.status = "Draft"
	doc.claim_batch_submission_run = source.name
	doc.participant_name = source.get("participant_name") or source.get("participant_customer") or source.name
	doc.claim_export_owner = frappe.session.user
	doc.export_format = "CSV Review File"
	doc.export_file_generation_allowed = 0
	doc.portal_lodgement_allowed = 0
	created_count = _generate_lines_from_submission_run(doc, source)
	_sync_totals(doc)
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_export_preparation_run_ready = 1 if summary["claim_export_preparation_run_ready"] else 0
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": CLAIM_EXPORT_PREP_RUN,
		"name": doc.name,
		"created": True,
		"export_line_count": created_count,
		"message": "NDIS CRM Claim Export Preparation Run created successfully.",
	}


@frappe.whitelist()
def create_claim_export_preparation_run_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))
	existing = _existing_run_for_deal(deal)
	if existing:
		return {"doctype": CLAIM_EXPORT_PREP_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Export Preparation Run returned."}
	source_run = _get_claim_batch_submission_run_for_deal(deal)
	if not source_run:
		frappe.throw(_("Please create and mark NDIS CRM Claim Batch Submission Run export-ready before creating Claim Export Preparation Run."))
	return create_claim_export_preparation_run_from_submission_run(source_run)


@frappe.whitelist()
def generate_claim_export_preparation_lines(claim_export_preparation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run)
	if not doc.get("claim_batch_submission_run"):
		frappe.throw(_("Claim Batch Submission Run is required."))
	source = frappe.get_doc(CLAIM_BATCH_SUBMISSION_RUN, doc.claim_batch_submission_run)
	created_count = _generate_lines_from_submission_run(doc, source)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Claim export preparation lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_claim_export_preparation_readiness(claim_export_preparation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Claim Export Preparation Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_export_file_preparation(claim_export_preparation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_export_preparation_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Export File Preparation. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Export File Preparation"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_export_preparation_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_EXPORT_PREP_RUN, "name": doc.name, "message": "Claim Export Preparation Run marked Ready for Export File Preparation."}


@frappe.whitelist()
def approve_claim_export_preparation_run(claim_export_preparation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_export_preparation_run_ready"]:
		frappe.throw(_("Cannot approve Claim Export Preparation Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Export Preparation Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_export_preparation_run_ready = 1
	doc.export_file_generation_allowed = 0
	doc.portal_lodgement_allowed = 0
	for row in doc.get("export_lines") or []:
		if row.get("export_line_status") in ["Draft", "Ready"]:
			row.export_line_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_EXPORT_PREP_RUN, "name": doc.name, "message": "Claim Export Preparation Run approved. No export file or portal lodgement was performed."}


def _ready_lines_for_export_file(doc):
	ready = []
	for row in doc.get("export_lines") or []:
		if row.get("export_line_status") not in ["Approved", "Ready"]:
			continue
		if not row.get("line_ready_for_export_file") or not row.get("export_file_authorized"):
			continue
		if row.get("portal_submission_authorized") or row.get("export_hold"):
			continue
		ready.append(row)
	return ready


def _build_export_rows(doc, ready_lines):
	rows = []
	for idx, row in enumerate(ready_lines, start=1):
		rows.append(
			{
				"run": doc.name,
				"line_no": idx,
				"participant_customer": doc.get("participant_customer"),
				"participant_name": doc.get("participant_name"),
				"ndis_number": doc.get("ndis_number"),
				"claim_batch": row.get("ndis_claim_batch"),
				"claim_line": row.get("ndis_claim_line"),
				"sales_invoice": row.get("sales_invoice"),
				"service_date": row.get("service_date"),
				"support_item": row.get("support_item"),
				"service_booking": row.get("service_booking"),
				"plan_budget": row.get("plan_budget"),
				"funding_source": row.get("funding_source"),
				"finance_service_type": row.get("finance_service_type"),
				"claim_quantity": row.get("claim_quantity"),
				"claim_unit": row.get("claim_unit"),
				"claim_rate": row.get("claim_rate"),
				"claim_amount": row.get("claim_amount"),
				"invoice_group_key": row.get("invoice_group_key"),
				"source_key": row.get("export_source_key"),
			}
		)
	return rows


def _make_csv_content(rows):
	if not rows:
		return ""
	buffer = io.StringIO()
	writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
	writer.writeheader()
	writer.writerows(rows)
	return buffer.getvalue()


def _make_json_content(rows):
	return json.dumps({"generated_at": now(), "note": "Review/export-preparation payload only. Not lodged or submitted.", "rows": rows}, indent=2, default=str)


@frappe.whitelist()
def generate_claim_export_file(claim_export_preparation_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_EXPORT_PREP_RUN, claim_export_preparation_run)
	if doc.status != "Export Preparation Approved":
		frappe.throw(_("Claim Export Preparation Run must be approved before generating an export file."))
	if not doc.get("export_file_generation_allowed"):
		frappe.throw(_("Tick Export File Generation Allowed before generating the export file."))
	if doc.get("portal_lodgement_allowed"):
		frappe.throw(_("Portal Lodgement Allowed must remain unticked in Phase 22."))
	summary = _calculate_readiness(doc)
	if not summary["claim_export_preparation_run_ready"]:
		frappe.throw(_("Cannot generate export file. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	ready_lines = _ready_lines_for_export_file(doc)
	if not ready_lines:
		frappe.throw(_("No ready export lines found for file generation."))
	rows = _build_export_rows(doc, ready_lines)
	if (doc.get("export_format") or "CSV Review File") == "JSON Review Payload":
		content = _make_json_content(rows)
		extension = "json"
	else:
		content = _make_csv_content(rows)
		extension = "csv"
	content_bytes = content.encode("utf-8")
	file_hash = hashlib.sha256(content_bytes).hexdigest()
	file_name = f"{doc.name}-claim-export-review.{extension}"
	file_doc = save_file(file_name, content_bytes, CLAIM_EXPORT_PREP_RUN, doc.name, is_private=1)
	for row in ready_lines:
		row.export_file_line_included = 1
		row.claim_export_ready = 1
		row.claim_submission_ready = 0
		row.export_line_status = "Export File Prepared"
	doc.status = "Export File Prepared"
	doc.export_file_generation_allowed = 0
	doc.portal_lodgement_allowed = 0
	doc.generated_file = file_doc.file_url
	doc.generated_file_name = file_name
	doc.generated_file_hash = file_hash
	doc.generated_file_on = now()
	doc.generated_file_by = frappe.session.user
	doc.generated_payload_preview = content[:10000]
	_sync_totals(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"file_url": file_doc.file_url,
		"file_name": file_name,
		"sha256": file_hash,
		"line_count": len(ready_lines),
		"message": "Claim export review file generated. No portal lodgement, claim submission, payment, journal, remittance, write-off, recovery, or manual GL was created.",
	}


def validate_claim_export_preparation_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(CLAIM_EXPORT_PREP_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_EXPORT_PREP_RUN, "claim_export_preparation_run_ready"):
		doc.claim_export_preparation_run_ready = 1 if summary["claim_export_preparation_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["claim_export_preparation_run_ready"]:
		frappe.throw(_("Cannot set Claim Export Preparation Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Export Preparation Approved" and doc.get("export_file_generation_allowed"):
		frappe.throw(_("Export File Generation Allowed can only be ticked after the run is approved."))
	if doc.get("portal_lodgement_allowed"):
		frappe.throw(_("Portal lodgement is not allowed in Phase 22."))


def on_claim_export_preparation_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Claim Export Preparation Run Summary Sync Failed")


def validate_crm_deal_phase22(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	required = doc.get("ndis_claim_export_preparation_run_required") if _field_exists(CRM_DEAL, "ndis_claim_export_preparation_run_required") else 0
	if not required:
		return
	run = doc.get("ndis_claim_export_preparation_run") if _field_exists(CRM_DEAL, "ndis_claim_export_preparation_run") else None
	if not run:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Export Preparation Run must be created and approved."))
	if not _is_claim_export_prep_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Export Preparation Run must be approved."))


def validate_crm_deal_phase22_combined(doc, method=None):
	try:
		from ndis_crm.phase21_claim_batch_submission import validate_crm_deal_phase21_combined

		validate_crm_deal_phase21_combined(doc, method)
	except ImportError:
		pass
	validate_crm_deal_phase22(doc, method)


def phase22_health_check():
	print("---- NDIS CRM Phase 22 Health Check ----")
	for dt in [
		CLAIM_EXPORT_PREP_LINE,
		CLAIM_EXPORT_PREP_RUN,
		CLAIM_BATCH_SUBMISSION_RUN,
		CLAIM_BATCH_SUBMISSION_LINE,
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
	for field in [
		"ndis_claim_export_preparation_run_required",
		"ndis_claim_export_preparation_run",
		"claim_export_preparation_status",
		"claim_export_preparation_ready",
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
		INTAKE,
	]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_claim_export_preparation_run", "claim_export_preparation_status", "claim_export_preparation_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	count = frappe.db.count(CLAIM_EXPORT_PREP_RUN) if _doctype_exists(CLAIM_EXPORT_PREP_RUN) else 0
	print("NDIS CRM Claim Export Preparation Run records:", count)
	print("Phase 22 may generate a private review file/payload only.")
	print("Phase 22 does not lodge, submit, remit, pay, journal, write off, recover, or manually post GL.")
	print("---- End Phase 22 Health Check ----")
