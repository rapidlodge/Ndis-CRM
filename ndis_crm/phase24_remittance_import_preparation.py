import csv
import hashlib
import io
import json

import frappe
from frappe import _
from frappe.utils import add_days, now, nowdate
from frappe.utils.file_manager import save_file


CRM_DEAL = "CRM Deal"
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
CLAIM_LODGEMENT_CONFIRMATION_RUN = "NDIS CRM Claim Lodgement Confirmation Run"
CLAIM_LODGEMENT_CONFIRMATION_LINE = "NDIS CRM Claim Lodgement Confirmation Line"
REMITTANCE_IMPORT_PREP_RUN = "NDIS CRM Remittance Import Preparation Run"
REMITTANCE_IMPORT_PREP_LINE = "NDIS CRM Remittance Import Preparation Line"

SALES_INVOICE = "Sales Invoice"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"
FINANCE_PROFILE = "NDIS Participant Financial Profile"

SOURCE_READY_STATUSES = {"Lodgement Confirmed"}
READY_STATUSES = {
	"Ready for Remittance Import Preparation",
	"Remittance Import Preparation Approved",
	"Remittance Matching Template Prepared",
}
APPROVED_STATUSES = {
	"Remittance Import Preparation Approved",
	"Remittance Matching Template Prepared",
}
ALLOWED_ROLES = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"NDIS CRM Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this remittance import preparation action."))


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


def _get_value_if_field(doctype, name, fieldname):
	if name and _field_exists(doctype, fieldname):
		return frappe.db.get_value(doctype, name, fieldname)
	return None


def _existing_run_for_lodgement_confirmation_run(claim_lodgement_confirmation_run):
	if not _doctype_exists(REMITTANCE_IMPORT_PREP_RUN):
		return None
	existing = _get_value_if_field(
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		claim_lodgement_confirmation_run,
		"ndis_remittance_import_preparation_run",
	)
	return existing or frappe.db.get_value(
		REMITTANCE_IMPORT_PREP_RUN,
		{"claim_lodgement_confirmation_run": claim_lodgement_confirmation_run},
		"name",
	)


def _existing_run_for_deal(deal):
	if not _doctype_exists(REMITTANCE_IMPORT_PREP_RUN):
		return None
	existing = _get_value_if_field(CRM_DEAL, deal, "ndis_remittance_import_preparation_run")
	return existing or frappe.db.get_value(REMITTANCE_IMPORT_PREP_RUN, {"crm_deal": deal}, "name")


def _get_lodgement_confirmation_run_for_deal(deal):
	return _get_value_if_field(CRM_DEAL, deal, "ndis_claim_lodgement_confirmation_run") or frappe.db.get_value(
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		{"crm_deal": deal},
		"name",
	)


def _is_lodgement_confirmed(run):
	if not run or not frappe.db.exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, run):
		return False
	status, ready = frappe.db.get_value(
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		run,
		["status", "claim_lodgement_confirmation_run_ready"],
	)
	return status in SOURCE_READY_STATUSES and bool(ready)


def _is_remittance_import_prep_approved(run):
	if not run or not frappe.db.exists(REMITTANCE_IMPORT_PREP_RUN, run):
		return False
	status, ready = frappe.db.get_value(
		REMITTANCE_IMPORT_PREP_RUN,
		run,
		["status", "remittance_import_preparation_run_ready"],
	)
	return status in APPROVED_STATUSES and bool(ready)


def _snapshot(doctype, name, fields):
	if not name or not _doctype_exists(doctype) or not frappe.db.exists(doctype, name):
		return {}
	out = {"name": name}
	for fieldname in fields:
		if _field_exists(doctype, fieldname):
			out[fieldname] = frappe.db.get_value(doctype, name, fieldname)
	return out


def _sales_invoice_snapshot(sales_invoice):
	return _snapshot(
		SALES_INVOICE,
		sales_invoice,
		["docstatus", "customer", "company", "posting_date", "due_date", "grand_total", "rounded_total", "outstanding_amount", "status"],
	)


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
			"claim_period_start",
			"claim_period_end",
			"total_claim_amount",
			"claim_amount_total",
			"amount",
			"lodgement_reference",
			"external_lodgement_reference",
			"portal_reference",
			"external_batch_reference",
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
			"lodgement_reference",
			"external_lodgement_reference",
			"portal_reference",
		],
	)


def _source_key(row):
	return row.get("lodgement_source_key") or "|".join(
		[
			str(row.get("service_line") or ""),
			str(row.get("ndis_claim_batch") or ""),
			str(row.get("ndis_claim_line") or ""),
			str(row.get("sales_invoice") or ""),
			str(row.get("external_lodgement_reference") or ""),
		]
	)


def _append_line_if_missing(doc, row_data):
	existing = {row.remittance_source_key for row in doc.get("remittance_lines") or [] if row.get("remittance_source_key")}
	key = row_data.get("remittance_source_key")
	if key and key in existing:
		return False
	doc.append("remittance_lines", row_data)
	return True


def _build_remittance_line_from_lodgement_line(row, lodgement_doc):
	claim_batch = row.get("ndis_claim_batch")
	claim_line = row.get("ndis_claim_line")
	sales_invoice = row.get("sales_invoice")
	batch_snapshot = _claim_batch_snapshot(claim_batch)
	line_snapshot = _claim_line_snapshot(claim_line)
	invoice_snapshot = _sales_invoice_snapshot(sales_invoice)
	sales_invoice_docstatus = int(invoice_snapshot.get("docstatus") or 0) if invoice_snapshot else row.get("sales_invoice_docstatus")
	claim_amount = row.get("claim_amount") or line_snapshot.get("claim_amount") or line_snapshot.get("amount") or 0
	external_reference = (
		row.get("external_lodgement_reference")
		or lodgement_doc.get("external_lodgement_reference")
		or batch_snapshot.get("external_lodgement_reference")
		or batch_snapshot.get("lodgement_reference")
		or batch_snapshot.get("portal_reference")
	)
	source_ready = bool(
		lodgement_doc.get("status") == "Lodgement Confirmed"
		and row.get("confirmation_status") == "Lodgement Confirmed"
		and row.get("lodgement_confirmed")
		and not row.get("confirmation_hold")
		and external_reference
		and claim_batch
		and batch_snapshot
		and sales_invoice
		and sales_invoice_docstatus == 1
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("plan_budget")
		and claim_amount
	)
	return {
		"remittance_source_key": _source_key(row),
		"ndis_claim_batch": claim_batch,
		"ndis_claim_line": claim_line,
		"claim_batch_status": batch_snapshot.get("status") or batch_snapshot.get("claim_batch_status") or batch_snapshot.get("batch_status"),
		"claim_line_status": line_snapshot.get("status") or line_snapshot.get("claim_status"),
		"sales_invoice": sales_invoice,
		"sales_invoice_docstatus": sales_invoice_docstatus,
		"sales_invoice_status": invoice_snapshot.get("status") or row.get("sales_invoice_status"),
		"sales_invoice_outstanding_amount": invoice_snapshot.get("outstanding_amount"),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"service_date": row.get("service_date"),
		"claim_quantity": row.get("claim_quantity"),
		"claim_unit": row.get("claim_unit") or "Hour",
		"claim_rate": row.get("claim_rate"),
		"claim_amount": claim_amount,
		"expected_paid_amount": claim_amount,
		"expected_rejected_amount": 0,
		"support_item": row.get("support_item"),
		"finance_service_type": row.get("finance_service_type"),
		"plan_budget": row.get("plan_budget"),
		"service_booking": row.get("service_booking"),
		"funding_source": row.get("funding_source"),
		"default_house": row.get("default_house"),
		"invoice_group_key": row.get("invoice_group_key"),
		"external_lodgement_reference": external_reference,
		"external_batch_reference": lodgement_doc.get("external_batch_reference"),
		"external_line_reference": row.get("external_line_reference"),
		"portal_status": row.get("portal_status"),
		"expected_payment_date": row.get("expected_payment_date") or lodgement_doc.get("expected_payment_date") or add_days(nowdate(), 7),
		"lodgement_date": lodgement_doc.get("lodgement_date"),
		"lodgement_evidence_file": lodgement_doc.get("lodgement_evidence_file"),
		"lodgement_confirmation_source_ready": 1 if source_ready else 0,
		"finance_remittance_review_complete": 0,
		"remittance_mapping_review_complete": 0,
		"remittance_template_authorized": 0,
		"payment_entry_authorized": 0,
		"write_off_authorized": 0,
		"recovery_authorized": 0,
		"remittance_hold": 0 if source_ready else 1,
		"remittance_hold_reason": None if source_ready else "Lodgement confirmation source is not ready for remittance preparation.",
		"line_ready_for_remittance_import_template": 0,
		"remittance_line_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_lodgement_run(doc, source):
	created = 0
	for row in source.get("lodgement_lines") or []:
		if row.get("confirmation_status") != "Lodgement Confirmed" or not row.get("lodgement_confirmed"):
			continue
		if _append_line_if_missing(doc, _build_remittance_line_from_lodgement_line(row, source)):
			created += 1
	return created


def _calculate_totals(doc):
	totals = {
		"remittance_line_count": len(doc.get("remittance_lines") or []),
		"claim_batch_count": 0,
		"claim_amount_total": 0,
		"expected_paid_amount_total": 0,
		"expected_rejected_amount_total": 0,
		"remittance_ready_count": 0,
		"remittance_template_line_count": 0,
		"remittance_hold_count": 0,
		"missing_lodgement_reference_count": 0,
		"blocked_payment_authorization_count": 0,
		"blocked_write_off_authorization_count": 0,
		"blocked_recovery_authorization_count": 0,
	}
	batches = set()
	for row in doc.get("remittance_lines") or []:
		totals["claim_amount_total"] += float(row.get("claim_amount") or 0)
		totals["expected_paid_amount_total"] += float(row.get("expected_paid_amount") or 0)
		totals["expected_rejected_amount_total"] += float(row.get("expected_rejected_amount") or 0)
		totals["remittance_ready_count"] += 1 if row.get("line_ready_for_remittance_import_template") else 0
		totals["remittance_template_line_count"] += 1 if row.get("remittance_template_line_included") else 0
		totals["remittance_hold_count"] += 1 if row.get("remittance_hold") else 0
		totals["missing_lodgement_reference_count"] += 1 if not row.get("external_lodgement_reference") else 0
		totals["blocked_payment_authorization_count"] += 1 if row.get("payment_entry_authorized") else 0
		totals["blocked_write_off_authorization_count"] += 1 if row.get("write_off_authorized") else 0
		totals["blocked_recovery_authorization_count"] += 1 if row.get("recovery_authorized") else 0
		if row.get("ndis_claim_batch"):
			batches.add(row.get("ndis_claim_batch"))
	totals["claim_batch_count"] = len(batches)
	for fieldname in ["claim_amount_total", "expected_paid_amount_total", "expected_rejected_amount_total"]:
		totals[fieldname] = round(totals[fieldname], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(REMITTANCE_IMPORT_PREP_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _calculate_readiness(doc):
	lines = doc.get("remittance_lines") or []
	checks = [
		("Claim Lodgement Confirmation Run linked", bool(doc.get("claim_lodgement_confirmation_run")), None),
		("Claim lodgement confirmed", _is_lodgement_confirmed(doc.get("claim_lodgement_confirmation_run")), None),
		("Participant Customer linked", bool(doc.get("participant_customer")), None),
		("Company selected", bool(doc.get("company")), None),
		("Remittance Owner assigned", bool(doc.get("remittance_owner")), None),
		("Template Format selected", bool(doc.get("template_format")), None),
		("Expected Remittance Date entered", bool(doc.get("expected_remittance_date")), None),
		("At least one remittance preparation line exists", bool(lines), None),
		("All lines have NDIS Claim Batch reference", not [r.service_line for r in lines if not r.get("ndis_claim_batch")], [r.service_line for r in lines if not r.get("ndis_claim_batch")]),
		("All lines have Sales Invoice reference", not [r.service_line for r in lines if not r.get("sales_invoice")], [r.service_line for r in lines if not r.get("sales_invoice")]),
		("All lines have external lodgement reference", not [r.service_line for r in lines if not r.get("external_lodgement_reference")], [r.service_line for r in lines if not r.get("external_lodgement_reference")]),
		("All lines have claim amount", not [r.service_line for r in lines if not r.get("claim_amount")], [r.service_line for r in lines if not r.get("claim_amount")]),
		("All lines have expected paid amount", not [r.service_line for r in lines if r.get("expected_paid_amount") is None], [r.service_line for r in lines if r.get("expected_paid_amount") is None]),
		("Lodgement confirmation source-ready flags are complete", not [r.service_line for r in lines if not r.get("lodgement_confirmation_source_ready")], [r.service_line for r in lines if not r.get("lodgement_confirmation_source_ready")]),
		("Finance remittance review complete", not [r.service_line for r in lines if not r.get("finance_remittance_review_complete")], [r.service_line for r in lines if not r.get("finance_remittance_review_complete")]),
		("Remittance mapping review complete", not [r.service_line for r in lines if not r.get("remittance_mapping_review_complete")], [r.service_line for r in lines if not r.get("remittance_mapping_review_complete")]),
		("Remittance template authorization complete", not [r.service_line for r in lines if not r.get("remittance_template_authorized")], [r.service_line for r in lines if not r.get("remittance_template_authorized")]),
		("Payment Entry authorization remains blocked in Phase 24", not [r.service_line for r in lines if r.get("payment_entry_authorized")], [r.service_line for r in lines if r.get("payment_entry_authorized")]),
		("Write-off authorization remains blocked in Phase 24", not [r.service_line for r in lines if r.get("write_off_authorized")], [r.service_line for r in lines if r.get("write_off_authorized")]),
		("Recovery authorization remains blocked in Phase 24", not [r.service_line for r in lines if r.get("recovery_authorized")], [r.service_line for r in lines if r.get("recovery_authorized")]),
		("No remittance preparation hold remains", not [r.service_line for r in lines if r.get("remittance_hold")], [r.service_line for r in lines if r.get("remittance_hold")]),
		("All lines marked ready for remittance import template", not [r.service_line for r in lines if not r.get("line_ready_for_remittance_import_template")], [r.service_line for r in lines if not r.get("line_ready_for_remittance_import_template")]),
	]
	complete = len([row for row in checks if row[1]])
	total = len(checks)
	incomplete = []
	for label, done, details in checks:
		if done:
			continue
		if details:
			label += ": " + ", ".join(str(x) for x in details if x)
		incomplete.append(label)
	return {
		"total_checks": total,
		"complete_checks": complete,
		"readiness_percent": round((complete / total) * 100, 2) if total else 0,
		"remittance_import_preparation_run_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(REMITTANCE_IMPORT_PREP_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(REMITTANCE_IMPORT_PREP_RUN, "remittance_import_preparation_run_ready"):
		doc.remittance_import_preparation_run_ready = 1 if summary["remittance_import_preparation_run_ready"] else 0
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
		(CLAIM_EXPORT_PREP_RUN, doc.get("claim_export_preparation_run")),
		(CLAIM_LODGEMENT_CONFIRMATION_RUN, doc.get("claim_lodgement_confirmation_run")),
		(INTAKE, doc.get("participant_intake")),
	]:
		_db_set_if_field(doctype, name, "ndis_remittance_import_preparation_run", doc.name)
		_db_set_if_field(doctype, name, "remittance_import_preparation_status", doc.status)
		_db_set_if_field(doctype, name, "remittance_import_preparation_ready", 1 if summary["remittance_import_preparation_run_ready"] else 0)
	return {"readiness": summary, "totals": totals}


def _copy_source_fields(doc, source):
	fields = [
		"claim_export_preparation_run",
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
		"external_lodgement_reference",
		"external_batch_reference",
		"lodgement_date",
		"lodgement_evidence_file",
		"claim_lodgement_owner",
		"claim_export_owner",
		"claim_batch_owner",
		"claim_owner",
		"billing_owner",
	]
	for fieldname in fields:
		if _field_exists(REMITTANCE_IMPORT_PREP_RUN, fieldname):
			doc.set(fieldname, source.get(fieldname))
	doc.generated_export_file = source.get("generated_file")
	doc.generated_export_file_hash = source.get("generated_file_hash")


@frappe.whitelist()
def create_remittance_import_preparation_run_from_lodgement_confirmation_run(claim_lodgement_confirmation_run):
	_check_role()
	if not claim_lodgement_confirmation_run:
		frappe.throw(_("NDIS CRM Claim Lodgement Confirmation Run is required."))
	if not frappe.db.exists(CLAIM_LODGEMENT_CONFIRMATION_RUN, claim_lodgement_confirmation_run):
		frappe.throw(_("NDIS CRM Claim Lodgement Confirmation Run {0} was not found.").format(claim_lodgement_confirmation_run))
	if not _is_lodgement_confirmed(claim_lodgement_confirmation_run):
		frappe.throw(_("Claim Lodgement Confirmation Run must be Lodgement Confirmed and ready before remittance preparation."))
	existing = _existing_run_for_lodgement_confirmation_run(claim_lodgement_confirmation_run)
	if existing:
		return {"doctype": REMITTANCE_IMPORT_PREP_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Remittance Import Preparation Run returned."}
	source = frappe.get_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN, claim_lodgement_confirmation_run)
	doc = frappe.new_doc(REMITTANCE_IMPORT_PREP_RUN)
	doc.status = "Draft"
	doc.claim_lodgement_confirmation_run = source.name
	_copy_source_fields(doc, source)
	doc.participant_name = doc.get("participant_name") or source.get("participant_customer") or source.name
	doc.remittance_owner = frappe.session.user
	doc.template_format = "CSV Matching Template"
	doc.expected_remittance_date = add_days(source.get("lodgement_date") or nowdate(), 7)
	doc.remittance_template_generation_allowed = 0
	doc.actual_remittance_import_allowed = 0
	doc.payment_entry_creation_allowed = 0
	created_count = _generate_lines_from_lodgement_run(doc, source)
	doc.remittance_line_count = created_count
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_import_preparation_run_ready = 1 if summary["remittance_import_preparation_run_ready"] else 0
	_sync_totals(doc)
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": REMITTANCE_IMPORT_PREP_RUN,
		"name": doc.name,
		"created": True,
		"remittance_line_count": created_count,
		"message": "NDIS CRM Remittance Import Preparation Run created successfully.",
	}


@frappe.whitelist()
def create_remittance_import_preparation_run_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))
	existing = _existing_run_for_deal(deal)
	if existing:
		return {"doctype": REMITTANCE_IMPORT_PREP_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Remittance Import Preparation Run returned."}
	source_run = _get_lodgement_confirmation_run_for_deal(deal)
	if not source_run:
		frappe.throw(_("Please create and confirm NDIS CRM Claim Lodgement Confirmation Run before creating Remittance Import Preparation Run."))
	return create_remittance_import_preparation_run_from_lodgement_confirmation_run(source_run)


@frappe.whitelist()
def generate_remittance_import_preparation_lines(remittance_import_preparation_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, remittance_import_preparation_run)
	if not doc.get("claim_lodgement_confirmation_run"):
		frappe.throw(_("Claim Lodgement Confirmation Run is required."))
	source = frappe.get_doc(CLAIM_LODGEMENT_CONFIRMATION_RUN, doc.claim_lodgement_confirmation_run)
	created_count = _generate_lines_from_lodgement_run(doc, source)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Remittance import preparation lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_remittance_import_preparation_readiness(remittance_import_preparation_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, remittance_import_preparation_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Remittance Import Preparation Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_remittance_import_preparation(remittance_import_preparation_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, remittance_import_preparation_run)
	summary = _calculate_readiness(doc)
	if not summary["remittance_import_preparation_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Remittance Import Preparation. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Remittance Import Preparation"
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_import_preparation_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": REMITTANCE_IMPORT_PREP_RUN, "name": doc.name, "message": "Remittance Import Preparation Run marked Ready."}


@frappe.whitelist()
def approve_remittance_import_preparation_run(remittance_import_preparation_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, remittance_import_preparation_run)
	summary = _calculate_readiness(doc)
	if not summary["remittance_import_preparation_run_ready"]:
		frappe.throw(_("Cannot approve Remittance Import Preparation Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Remittance Import Preparation Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_import_preparation_run_ready = 1
	doc.remittance_template_generation_allowed = 0
	doc.actual_remittance_import_allowed = 0
	doc.payment_entry_creation_allowed = 0
	for row in doc.get("remittance_lines") or []:
		if row.get("remittance_line_status") in ["Draft", "Ready"]:
			row.remittance_line_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": REMITTANCE_IMPORT_PREP_RUN, "name": doc.name, "message": "Remittance Import Preparation Run approved. No remittance import or payment action was performed."}


def _ready_lines_for_template(doc):
	return [
		row
		for row in doc.get("remittance_lines") or []
		if row.get("remittance_line_status") in ["Approved", "Ready"]
		and row.get("line_ready_for_remittance_import_template")
		and row.get("remittance_template_authorized")
		and not row.get("payment_entry_authorized")
		and not row.get("write_off_authorized")
		and not row.get("recovery_authorized")
		and not row.get("remittance_hold")
	]


def _build_template_rows(doc, ready_lines):
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
				"external_lodgement_reference": row.get("external_lodgement_reference"),
				"external_batch_reference": row.get("external_batch_reference"),
				"external_line_reference": row.get("external_line_reference"),
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
				"expected_paid_amount": row.get("expected_paid_amount"),
				"expected_rejected_amount": row.get("expected_rejected_amount"),
				"expected_payment_date": row.get("expected_payment_date"),
				"source_key": row.get("remittance_source_key"),
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
	return json.dumps(
		{
			"generated_at": now(),
			"note": "Remittance matching preparation payload only. Not imported, posted, paid, written off, or recovered.",
			"rows": rows,
		},
		indent=2,
		default=str,
	)


@frappe.whitelist()
def generate_remittance_matching_template(remittance_import_preparation_run):
	_check_role()
	doc = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, remittance_import_preparation_run)
	if doc.status != "Remittance Import Preparation Approved":
		frappe.throw(_("Remittance Import Preparation Run must be approved before generating a matching template."))
	if not doc.get("remittance_template_generation_allowed"):
		frappe.throw(_("Tick Remittance Template Generation Allowed before generating the template."))
	if doc.get("actual_remittance_import_allowed"):
		frappe.throw(_("Actual Remittance Import Allowed must remain unticked in Phase 24."))
	if doc.get("payment_entry_creation_allowed"):
		frappe.throw(_("Payment Entry Creation Allowed must remain unticked in Phase 24."))
	summary = _calculate_readiness(doc)
	if not summary["remittance_import_preparation_run_ready"]:
		frappe.throw(_("Cannot generate remittance template. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	ready_lines = _ready_lines_for_template(doc)
	if not ready_lines:
		frappe.throw(_("No ready remittance lines found for template generation."))
	rows = _build_template_rows(doc, ready_lines)
	if (doc.get("template_format") or "CSV Matching Template") == "JSON Matching Payload":
		content = _make_json_content(rows)
		extension = "json"
	else:
		content = _make_csv_content(rows)
		extension = "csv"
	content_bytes = content.encode("utf-8")
	file_hash = hashlib.sha256(content_bytes).hexdigest()
	file_name = f"{doc.name}-remittance-matching-template.{extension}"
	file_doc = save_file(file_name, content_bytes, REMITTANCE_IMPORT_PREP_RUN, doc.name, is_private=1)
	for row in ready_lines:
		row.remittance_template_line_included = 1
		row.remittance_line_status = "Template Prepared"
	doc.status = "Remittance Matching Template Prepared"
	doc.remittance_template_generation_allowed = 0
	doc.actual_remittance_import_allowed = 0
	doc.payment_entry_creation_allowed = 0
	doc.generated_template_file = file_doc.file_url
	doc.generated_template_file_name = file_name
	doc.generated_template_file_hash = file_hash
	doc.generated_template_file_on = now()
	doc.generated_template_file_by = frappe.session.user
	doc.generated_payload_preview = content[:10000]
	_sync_totals(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"file_url": file_doc.file_url,
		"file_name": file_name,
		"sha256": file_hash,
		"line_count": len(ready_lines),
		"message": "Remittance matching template generated. No remittance import, payment entry, journal, write-off, recovery, or manual GL was created.",
	}


def validate_remittance_import_preparation_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.remittance_import_preparation_run_ready = 1 if summary["remittance_import_preparation_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["remittance_import_preparation_run_ready"]:
		frappe.throw(_("Cannot set Remittance Import Preparation Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Remittance Import Preparation Approved" and doc.get("remittance_template_generation_allowed"):
		frappe.throw(_("Remittance Template Generation Allowed can only be ticked after the run is approved."))
	if doc.get("actual_remittance_import_allowed"):
		frappe.throw(_("Actual remittance import is not allowed in Phase 24."))
	if doc.get("payment_entry_creation_allowed"):
		frappe.throw(_("Payment Entry creation is not allowed in Phase 24."))


def on_remittance_import_preparation_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Remittance Import Preparation Run Summary Sync Failed")


def validate_crm_deal_phase24(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	required = doc.get("ndis_remittance_import_preparation_run_required") if _field_exists(CRM_DEAL, "ndis_remittance_import_preparation_run_required") else 0
	if not required:
		return
	run = doc.get("ndis_remittance_import_preparation_run") if _field_exists(CRM_DEAL, "ndis_remittance_import_preparation_run") else None
	if not run:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Remittance Import Preparation Run must be created and approved."))
	if not _is_remittance_import_prep_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Remittance Import Preparation Run must be approved."))


def validate_crm_deal_phase24_combined(doc, method=None):
	try:
		from ndis_crm.phase23_claim_lodgement_confirmation import validate_crm_deal_phase23_combined

		validate_crm_deal_phase23_combined(doc, method)
	except ImportError:
		try:
			from ndis_crm.phase22_claim_export_preparation import validate_crm_deal_phase22_combined

			validate_crm_deal_phase22_combined(doc, method)
		except ImportError:
			pass
	validate_crm_deal_phase24(doc, method)


def phase24_health_check():
	print("---- NDIS CRM Phase 24 Health Check ----")
	for dt in [
		REMITTANCE_IMPORT_PREP_LINE,
		REMITTANCE_IMPORT_PREP_RUN,
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		CLAIM_LODGEMENT_CONFIRMATION_LINE,
		CLAIM_EXPORT_PREP_RUN,
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
	for dt in [NDIS_REMITTANCE_IMPORT, "Payment Entry", "Journal Entry", "GL Entry", "NDIS Recovery Case", "NDIS Write Off", PLAN_BUDGET, SERVICE_BOOKING, NDIS_SERVICE_TYPE, NDIS_SUPPORT_ITEM, NDIS_HOUSE, FINANCE_PROFILE]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in [
		"ndis_remittance_import_preparation_run_required",
		"ndis_remittance_import_preparation_run",
		"remittance_import_preparation_status",
		"remittance_import_preparation_ready",
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
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		INTAKE,
	]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_remittance_import_preparation_run", "remittance_import_preparation_status", "remittance_import_preparation_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	print("NDIS CRM Remittance Import Preparation Run records:", frappe.db.count(REMITTANCE_IMPORT_PREP_RUN) if _doctype_exists(REMITTANCE_IMPORT_PREP_RUN) else 0)
	print("Phase 24 may generate a private remittance matching template/payload only.")
	print("Phase 24 does not import remittance, create Payment Entry, journal, write-off, recovery, or manually post GL.")
	print("---- End Phase 24 Health Check ----")
