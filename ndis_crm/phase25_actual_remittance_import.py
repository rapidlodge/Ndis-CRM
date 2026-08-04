import csv
import hashlib
import io
import json
import os
from urllib.parse import unquote

import frappe
from frappe import _
from frappe.utils import now, nowdate


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
REMITTANCE_IMPORT_PREP_RUN = "NDIS CRM Remittance Import Preparation Run"
REMITTANCE_IMPORT_PREP_LINE = "NDIS CRM Remittance Import Preparation Line"
ACTUAL_REMITTANCE_IMPORT_RUN = "NDIS CRM Actual Remittance Import Run"
ACTUAL_REMITTANCE_IMPORT_LINE = "NDIS CRM Actual Remittance Import Line"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"

READY_STATUSES = [
	"Ready for Remittance Import Draft Creation",
	"Actual Remittance Import Run Approved",
	"Draft Remittance Import Created",
]
APPROVED_STATUSES = ["Actual Remittance Import Run Approved", "Draft Remittance Import Created"]
SOURCE_READY_STATUSES = ["Remittance Matching Template Prepared"]
ALLOWED_ROLES = ["System Manager", "Accounts Manager", "Accounts User", "NDIS CRM Manager", "NDIS Plan Management Officer"]

CHAIN_FIELDS = [
	"crm_lead",
	"crm_deal",
	"participant_intake",
	"handover",
	"finance_onboarding",
	"operations_setup",
	"service_schedule_draft",
	"roster_build_request",
	"participant_service_file",
	"service_session_draft",
	"delivery_evidence_review",
	"downstream_preparation",
	"attendance_draft",
	"billing_draft",
	"claim_draft",
	"invoice_draft",
	"sales_invoice_draft_run",
	"sales_invoice_submission_run",
	"claim_batch_draft_run",
	"claim_batch_submission_run",
	"claim_export_preparation_run",
	"claim_lodgement_confirmation_run",
]


def _check_role():
	if frappe.session.user == "Administrator":
		return
	if not any(frappe.has_role(role) for role in ALLOWED_ROLES):
		frappe.throw(_("You are not allowed to manage actual remittance import runs."))


def _doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def _field_exists(doctype, fieldname):
	return bool(frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}) or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}))


def _db_set_if_field(doctype, name, fieldname, value):
	if name and _doctype_exists(doctype) and _field_exists(doctype, fieldname):
		frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)


def _set_if_field(doc, fieldname, value):
	if _field_exists(doc.doctype, fieldname):
		doc.set(fieldname, value)


def _set_first_existing(doc, candidates, value):
	for fieldname in candidates:
		if _field_exists(doc.doctype, fieldname):
			doc.set(fieldname, value)
			return fieldname
	return None


def _to_float(value):
	try:
		return float(value or 0)
	except (TypeError, ValueError):
		return 0


def _normalise_key(value):
	return str(value or "").strip().lower()


def _get_row_value(row, keys):
	for key in keys:
		if key in row and row.get(key) not in (None, ""):
			return row.get(key)
		lower = key.lower()
		for existing_key, value in row.items():
			if str(existing_key).strip().lower() == lower and value not in (None, ""):
				return value
	return None


def _source_key(row):
	for key in ["remittance_source_key", "actual_remittance_source_key"]:
		if row.get(key):
			return row.get(key)
	parts = [
		row.get("service_line"),
		row.get("ndis_claim_batch"),
		row.get("ndis_claim_line"),
		row.get("sales_invoice"),
		row.get("external_lodgement_reference"),
		row.get("external_line_reference"),
	]
	return "|".join(str(part or "").strip() for part in parts if part)


def _existing_run_for_preparation_run(preparation_run):
	linked = frappe.db.get_value(REMITTANCE_IMPORT_PREP_RUN, preparation_run, "ndis_actual_remittance_import_run") if _field_exists(REMITTANCE_IMPORT_PREP_RUN, "ndis_actual_remittance_import_run") else None
	if linked and frappe.db.exists(ACTUAL_REMITTANCE_IMPORT_RUN, linked):
		return linked
	return frappe.db.get_value(ACTUAL_REMITTANCE_IMPORT_RUN, {"remittance_import_preparation_run": preparation_run}, "name")


def _existing_run_for_deal(deal):
	linked = frappe.db.get_value(CRM_DEAL, deal, "ndis_actual_remittance_import_run") if _field_exists(CRM_DEAL, "ndis_actual_remittance_import_run") else None
	if linked and frappe.db.exists(ACTUAL_REMITTANCE_IMPORT_RUN, linked):
		return linked
	return frappe.db.get_value(ACTUAL_REMITTANCE_IMPORT_RUN, {"crm_deal": deal}, "name")


def _get_remittance_import_preparation_run_for_deal(deal):
	linked = frappe.db.get_value(CRM_DEAL, deal, "ndis_remittance_import_preparation_run") if _field_exists(CRM_DEAL, "ndis_remittance_import_preparation_run") else None
	if linked and frappe.db.exists(REMITTANCE_IMPORT_PREP_RUN, linked):
		return linked
	return frappe.db.get_value(REMITTANCE_IMPORT_PREP_RUN, {"crm_deal": deal}, "name")


def _is_remittance_preparation_ready(doc):
	return (
		doc.status in SOURCE_READY_STATUSES
		and bool(doc.get("remittance_import_preparation_run_ready"))
		and bool(doc.get("generated_template_file"))
	)


def _copy_chain_fields(target, source):
	for fieldname in CHAIN_FIELDS:
		_set_if_field(target, fieldname, source.get(fieldname))
	for fieldname in [
		"participant_customer",
		"participant_name",
		"ndis_number",
		"service_start_date",
		"service_end_date",
		"claim_window_start",
		"claim_window_end",
		"company",
		"finance_owner",
		"operations_owner",
		"billing_owner",
		"plan_manager",
	]:
		_set_if_field(target, fieldname, source.get(fieldname))


def _file_path_from_url(file_url):
	if not file_url:
		return None
	file_url = unquote(file_url)
	if file_url.startswith("/private/files/"):
		return frappe.get_site_path("private", "files", file_url.split("/private/files/", 1)[1])
	if file_url.startswith("/files/"):
		return frappe.get_site_path("public", "files", file_url.split("/files/", 1)[1])
	if os.path.isabs(file_url):
		return file_url
	return frappe.get_site_path(file_url.lstrip("/"))


def _read_file_bytes(file_url):
	path = _file_path_from_url(file_url)
	if not path or not os.path.exists(path):
		frappe.throw(_("Uploaded remittance file could not be found."))
	with open(path, "rb") as handle:
		content = handle.read()
	return content, os.path.basename(path), hashlib.sha256(content).hexdigest()


def _parse_uploaded_remittance_file(file_url):
	content, filename, digest = _read_file_bytes(file_url)
	text = content.decode("utf-8-sig")
	records = []
	if filename.lower().endswith(".json") or text.lstrip().startswith(("{", "[")):
		payload = json.loads(text)
		if isinstance(payload, dict):
			payload = payload.get("lines") or payload.get("records") or payload.get("remittance_lines") or []
		records = payload
	else:
		records = list(csv.DictReader(io.StringIO(text)))

	rows = []
	for raw in records:
		if not isinstance(raw, dict):
			continue
		row = {
			"source_key": _get_row_value(raw, ["source_key", "remittance_source_key", "actual_remittance_source_key"]),
			"sales_invoice": _get_row_value(raw, ["sales_invoice", "invoice", "invoice_number"]),
			"ndis_claim_batch": _get_row_value(raw, ["ndis_claim_batch", "claim_batch", "batch"]),
			"ndis_claim_line": _get_row_value(raw, ["ndis_claim_line", "claim_line", "line"]),
			"external_lodgement_reference": _get_row_value(raw, ["external_lodgement_reference", "lodgement_reference", "external_lodgement_ref"]),
			"external_line_reference": _get_row_value(raw, ["external_line_reference", "line_reference", "external_line_ref"]),
			"actual_payment_reference": _get_row_value(raw, ["actual_payment_reference", "payment_reference", "remittance_reference"]),
			"actual_payment_date": _get_row_value(raw, ["actual_payment_date", "payment_date", "paid_date"]),
			"actual_remittance_status": _get_row_value(raw, ["actual_remittance_status", "remittance_status", "status"]),
			"rejection_code": _get_row_value(raw, ["rejection_code", "reject_code"]),
			"rejection_reason": _get_row_value(raw, ["rejection_reason", "reject_reason", "reason"]),
			"actual_paid_amount": _to_float(_get_row_value(raw, ["actual_paid_amount", "paid_amount", "amount_paid", "payment_amount"])),
			"actual_rejected_amount": _to_float(_get_row_value(raw, ["actual_rejected_amount", "rejected_amount", "amount_rejected"])),
			"claim_amount": _to_float(_get_row_value(raw, ["claim_amount", "claimed_amount", "amount_claimed"])),
			"raw_payload": json.dumps(raw, sort_keys=True, default=str),
		}
		if not row["source_key"]:
			row["source_key"] = _source_key(row)
		rows.append(row)
	return rows, filename, digest


def _match_actual_row(expected_row, actual_rows):
	keys = [
		("source_key", _source_key(expected_row)),
		("sales_invoice", expected_row.get("sales_invoice")),
		("ndis_claim_line", expected_row.get("ndis_claim_line")),
		("external_line_reference", expected_row.get("external_line_reference")),
		("external_lodgement_reference", expected_row.get("external_lodgement_reference")),
	]
	for fieldname, expected in keys:
		if not expected:
			continue
		for actual in actual_rows:
			if _normalise_key(actual.get(fieldname)) == _normalise_key(expected):
				return actual
	return None


def _build_actual_line(preparation_line, actual_rows=None):
	actual_rows = actual_rows or []
	actual = _match_actual_row(preparation_line, actual_rows)
	expected_paid = _to_float(preparation_line.get("expected_paid_amount") or preparation_line.get("claim_amount"))
	actual_paid = _to_float(actual.get("actual_paid_amount")) if actual else 0
	source_ready = bool(
		preparation_line.get("remittance_line_status") == "Template Prepared"
		and preparation_line.get("remittance_template_line_included")
		and preparation_line.get("line_ready_for_remittance_import_template")
		and not preparation_line.get("remittance_hold")
		and preparation_line.get("external_lodgement_reference")
		and preparation_line.get("sales_invoice")
		and preparation_line.get("ndis_claim_batch")
		and _to_float(preparation_line.get("claim_amount")) > 0
	)
	line = {
		"actual_remittance_source_key": _source_key(preparation_line),
		"remittance_source_key": preparation_line.get("remittance_source_key"),
		"ndis_claim_batch": preparation_line.get("ndis_claim_batch"),
		"ndis_claim_line": preparation_line.get("ndis_claim_line"),
		"claim_batch_status": preparation_line.get("claim_batch_status"),
		"claim_line_status": preparation_line.get("claim_line_status"),
		"sales_invoice": preparation_line.get("sales_invoice"),
		"sales_invoice_docstatus": preparation_line.get("sales_invoice_docstatus"),
		"sales_invoice_status": preparation_line.get("sales_invoice_status"),
		"sales_invoice_outstanding_amount": preparation_line.get("sales_invoice_outstanding_amount"),
		"service_line": preparation_line.get("service_line"),
		"service_code": preparation_line.get("service_code"),
		"service_model": preparation_line.get("service_model"),
		"service_date": preparation_line.get("service_date"),
		"claim_quantity": preparation_line.get("claim_quantity"),
		"claim_unit": preparation_line.get("claim_unit"),
		"claim_rate": preparation_line.get("claim_rate"),
		"claim_amount": preparation_line.get("claim_amount"),
		"expected_paid_amount": expected_paid,
		"expected_rejected_amount": preparation_line.get("expected_rejected_amount"),
		"actual_paid_amount": actual_paid,
		"actual_rejected_amount": _to_float(actual.get("actual_rejected_amount")) if actual else 0,
		"variance_amount": actual_paid - expected_paid,
		"support_item": preparation_line.get("support_item"),
		"finance_service_type": preparation_line.get("finance_service_type"),
		"plan_budget": preparation_line.get("plan_budget"),
		"service_booking": preparation_line.get("service_booking"),
		"funding_source": preparation_line.get("funding_source"),
		"default_house": preparation_line.get("default_house"),
		"invoice_group_key": preparation_line.get("invoice_group_key"),
		"external_lodgement_reference": preparation_line.get("external_lodgement_reference"),
		"external_batch_reference": preparation_line.get("external_batch_reference"),
		"external_line_reference": preparation_line.get("external_line_reference"),
		"portal_status": preparation_line.get("portal_status"),
		"actual_payment_reference": actual.get("actual_payment_reference") if actual else None,
		"actual_payment_date": actual.get("actual_payment_date") if actual else None,
		"actual_remittance_status": actual.get("actual_remittance_status") if actual else None,
		"rejection_code": actual.get("rejection_code") if actual else None,
		"rejection_reason": actual.get("rejection_reason") if actual else None,
		"raw_actual_remittance_payload": actual.get("raw_payload") if actual else None,
		"remittance_preparation_source_ready": 1 if source_ready else 0,
		"actual_file_matched": 1 if actual else 0,
		"actual_remittance_review_complete": 0,
		"remittance_import_mapping_ready": 0,
		"remittance_import_draft_authorized": 0,
		"payment_entry_authorized": 0,
		"journal_authorized": 0,
		"write_off_authorized": 0,
		"recovery_authorized": 0,
		"actual_remittance_hold": 0 if source_ready and actual else 1,
		"actual_remittance_hold_reason": None if source_ready and actual else "Source line is not ready or uploaded remittance row is not matched.",
		"line_ready_for_remittance_import_draft": 0,
		"actual_remittance_line_status": "Draft",
	}
	return line


def _append_line_if_missing(run_doc, line_data):
	key = line_data.get("actual_remittance_source_key")
	for row in run_doc.actual_remittance_lines:
		if row.get("actual_remittance_source_key") == key:
			for fieldname, value in line_data.items():
				row.set(fieldname, value)
			return row
	row = run_doc.append("actual_remittance_lines", {})
	for fieldname, value in line_data.items():
		row.set(fieldname, value)
	return row


def _generate_lines_from_preparation_run(run_doc, actual_rows=None):
	prep = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, run_doc.remittance_import_preparation_run)
	for row in prep.get("remittance_lines", []):
		if row.get("remittance_line_status") == "Template Prepared" and row.get("remittance_template_line_included"):
			_append_line_if_missing(run_doc, _build_actual_line(row, actual_rows))


def _apply_actual_file_to_existing_lines(run_doc, actual_rows):
	for row in run_doc.actual_remittance_lines:
		actual = _match_actual_row(row, actual_rows)
		if not actual:
			row.actual_file_matched = 0
			row.actual_remittance_hold = 1
			row.actual_remittance_hold_reason = "Uploaded remittance row is not matched."
			continue
		row.actual_file_matched = 1
		row.actual_paid_amount = _to_float(actual.get("actual_paid_amount"))
		row.actual_rejected_amount = _to_float(actual.get("actual_rejected_amount"))
		row.variance_amount = _to_float(row.actual_paid_amount) - _to_float(row.expected_paid_amount)
		row.actual_payment_reference = actual.get("actual_payment_reference")
		row.actual_payment_date = actual.get("actual_payment_date")
		row.actual_remittance_status = actual.get("actual_remittance_status")
		row.rejection_code = actual.get("rejection_code")
		row.rejection_reason = actual.get("rejection_reason")
		row.raw_actual_remittance_payload = actual.get("raw_payload")
		if row.remittance_preparation_source_ready:
			row.actual_remittance_hold = 0
			row.actual_remittance_hold_reason = None


def _calculate_totals(run_doc):
	lines = list(run_doc.actual_remittance_lines or [])
	return {
		"actual_remittance_line_count": len(lines),
		"claim_batch_count": len({row.ndis_claim_batch for row in lines if row.ndis_claim_batch}),
		"claim_amount_total": sum(_to_float(row.claim_amount) for row in lines),
		"expected_paid_amount_total": sum(_to_float(row.expected_paid_amount) for row in lines),
		"actual_paid_amount_total": sum(_to_float(row.actual_paid_amount) for row in lines),
		"actual_rejected_amount_total": sum(_to_float(row.actual_rejected_amount) for row in lines),
		"variance_amount_total": sum(_to_float(row.variance_amount) for row in lines),
		"actual_file_matched_count": sum(1 for row in lines if row.actual_file_matched),
		"remittance_import_ready_count": sum(1 for row in lines if row.line_ready_for_remittance_import_draft),
		"draft_remittance_import_line_count": sum(1 for row in lines if row.ndis_remittance_import),
		"actual_remittance_hold_count": sum(1 for row in lines if row.actual_remittance_hold),
		"blocked_payment_authorization_count": sum(1 for row in lines if row.payment_entry_authorized),
		"blocked_journal_authorization_count": sum(1 for row in lines if row.journal_authorized),
		"blocked_write_off_authorization_count": sum(1 for row in lines if row.write_off_authorized),
		"blocked_recovery_authorization_count": sum(1 for row in lines if row.recovery_authorized),
	}


def _calculate_readiness(run_doc):
	items = []
	prep = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, run_doc.remittance_import_preparation_run) if run_doc.remittance_import_preparation_run else None
	items.append(("Source remittance preparation run is ready", bool(prep and _is_remittance_preparation_ready(prep))))
	items.append(("Uploaded actual remittance file is attached and parsed", bool(run_doc.uploaded_remittance_file and run_doc.uploaded_file_sha256)))
	items.append(("NDIS Remittance Import DocType exists", _doctype_exists(NDIS_REMITTANCE_IMPORT)))
	items.append(("Participant, company, owner, and import date are present", bool(run_doc.participant_customer and run_doc.company and run_doc.finance_owner and run_doc.actual_remittance_import_date)))
	items.append(("Actual remittance lines exist", bool(run_doc.actual_remittance_lines)))
	for row in run_doc.actual_remittance_lines or []:
		prefix = row.idx or row.actual_remittance_source_key or "line"
		items.extend([
			(f"Line {prefix}: source line is ready", bool(row.remittance_preparation_source_ready)),
			(f"Line {prefix}: uploaded remittance row matched", bool(row.actual_file_matched)),
			(f"Line {prefix}: claim batch, invoice, and external reference present", bool(row.ndis_claim_batch and row.sales_invoice and row.external_lodgement_reference)),
			(f"Line {prefix}: actual paid amount available", row.actual_paid_amount is not None),
			(f"Line {prefix}: review complete", bool(row.actual_remittance_review_complete)),
			(f"Line {prefix}: mapping ready", bool(row.remittance_import_mapping_ready)),
			(f"Line {prefix}: draft authorized", bool(row.remittance_import_draft_authorized)),
			(f"Line {prefix}: no payment, journal, write-off, or recovery authorization", not any([row.payment_entry_authorized, row.journal_authorized, row.write_off_authorized, row.recovery_authorized])),
			(f"Line {prefix}: no actual remittance hold", not row.actual_remittance_hold),
			(f"Line {prefix}: ready for draft import", bool(row.line_ready_for_remittance_import_draft)),
		])
	missing = [label for label, ok in items if not ok]
	percent = 100 if not items else round(((len(items) - len(missing)) / len(items)) * 100, 2)
	return percent, missing


def _update_totals_and_readiness(run_doc):
	for fieldname, value in _calculate_totals(run_doc).items():
		run_doc.set(fieldname, value)
	percent, missing = _calculate_readiness(run_doc) if run_doc.remittance_import_preparation_run else (0, ["Missing source remittance preparation run"])
	run_doc.readiness_percent = percent
	run_doc.actual_remittance_import_run_ready = 1 if not missing else 0
	run_doc.readiness_notes = "\n".join(missing)
	return missing


def _sync_summary_to_links(run_doc):
	for doctype, name in [
		(CRM_DEAL, run_doc.crm_deal),
		(INTAKE, run_doc.participant_intake),
		(HANDOVER, run_doc.handover),
		(FINANCE_ONBOARDING, run_doc.finance_onboarding),
		(OPERATIONS_SETUP, run_doc.operations_setup),
		(SCHEDULE_DRAFT, run_doc.service_schedule_draft),
		(ROSTER_REQUEST, run_doc.roster_build_request),
		(SERVICE_FILE, run_doc.participant_service_file),
		(SESSION_DRAFT, run_doc.service_session_draft),
		(EVIDENCE_REVIEW, run_doc.delivery_evidence_review),
		(DOWNSTREAM_PREPARATION, run_doc.downstream_preparation),
		(ATTENDANCE_DRAFT, run_doc.attendance_draft),
		(BILLING_DRAFT, run_doc.billing_draft),
		(CLAIM_DRAFT, run_doc.claim_draft),
		(INVOICE_DRAFT, run_doc.invoice_draft),
		(SALES_INVOICE_DRAFT_RUN, run_doc.sales_invoice_draft_run),
		(SALES_INVOICE_SUBMISSION_RUN, run_doc.sales_invoice_submission_run),
		(CLAIM_BATCH_DRAFT_RUN, run_doc.claim_batch_draft_run),
		(CLAIM_BATCH_SUBMISSION_RUN, run_doc.claim_batch_submission_run),
		(CLAIM_EXPORT_PREP_RUN, run_doc.claim_export_preparation_run),
		(CLAIM_LODGEMENT_CONFIRMATION_RUN, run_doc.claim_lodgement_confirmation_run),
		(REMITTANCE_IMPORT_PREP_RUN, run_doc.remittance_import_preparation_run),
	]:
		_db_set_if_field(doctype, name, "ndis_actual_remittance_import_run", run_doc.name)
		_db_set_if_field(doctype, name, "ndis_actual_remittance_import_status", run_doc.status)
		_db_set_if_field(doctype, name, "ndis_actual_remittance_import_ready", run_doc.actual_remittance_import_run_ready)


@frappe.whitelist()
def create_actual_remittance_import_run_from_preparation_run(remittance_import_preparation_run):
	_check_role()
	existing = _existing_run_for_preparation_run(remittance_import_preparation_run)
	if existing:
		return {"name": existing, "created": False, "message": "Existing Actual Remittance Import Run found."}
	prep = frappe.get_doc(REMITTANCE_IMPORT_PREP_RUN, remittance_import_preparation_run)
	if not _is_remittance_preparation_ready(prep):
		frappe.throw(_("Remittance Import Preparation Run must be prepared before creating an Actual Remittance Import Run."))
	run_doc = frappe.new_doc(ACTUAL_REMITTANCE_IMPORT_RUN)
	run_doc.remittance_import_preparation_run = prep.name
	run_doc.status = "Draft"
	run_doc.actual_remittance_import_date = nowdate()
	run_doc.remittance_import_draft_creation_allowed = 0
	run_doc.payment_entry_creation_allowed = 0
	run_doc.journal_creation_allowed = 0
	run_doc.write_off_creation_allowed = 0
	run_doc.recovery_creation_allowed = 0
	run_doc.generated_template_file = prep.get("generated_template_file")
	run_doc.generated_template_file_hash = prep.get("generated_template_file_hash")
	_copy_chain_fields(run_doc, prep)
	_generate_lines_from_preparation_run(run_doc)
	_update_totals_and_readiness(run_doc)
	run_doc.insert(ignore_permissions=True)
	_sync_summary_to_links(run_doc)
	frappe.db.commit()
	return {"name": run_doc.name, "created": True, "message": "Actual Remittance Import Run created."}


@frappe.whitelist()
def create_actual_remittance_import_run_from_crm_deal(deal):
	_check_role()
	existing = _existing_run_for_deal(deal)
	if existing:
		return {"name": existing, "created": False, "message": "Existing Actual Remittance Import Run found."}
	preparation_run = _get_remittance_import_preparation_run_for_deal(deal)
	if not preparation_run:
		frappe.throw(_("No Remittance Import Preparation Run is linked to this CRM Deal."))
	return create_actual_remittance_import_run_from_preparation_run(preparation_run)


@frappe.whitelist()
def parse_uploaded_actual_remittance_file(actual_remittance_import_run):
	_check_role()
	run_doc = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run)
	if not run_doc.uploaded_remittance_file:
		frappe.throw(_("Attach an Uploaded Remittance File first."))
	actual_rows, filename, digest = _parse_uploaded_remittance_file(run_doc.uploaded_remittance_file)
	run_doc.uploaded_file_name = filename
	run_doc.uploaded_file_sha256 = digest
	run_doc.uploaded_file_line_count = len(actual_rows)
	run_doc.uploaded_file_parsed_on = now()
	run_doc.uploaded_file_parsed_by = frappe.session.user
	if not run_doc.actual_remittance_lines:
		_generate_lines_from_preparation_run(run_doc, actual_rows)
	else:
		_apply_actual_file_to_existing_lines(run_doc, actual_rows)
	_update_totals_and_readiness(run_doc)
	run_doc.save(ignore_permissions=True)
	_sync_summary_to_links(run_doc)
	frappe.db.commit()
	return {"name": run_doc.name, "message": "Uploaded actual remittance file parsed."}


@frappe.whitelist()
def generate_actual_remittance_import_lines(actual_remittance_import_run):
	_check_role()
	run_doc = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run)
	actual_rows = []
	if run_doc.uploaded_remittance_file:
		actual_rows, filename, digest = _parse_uploaded_remittance_file(run_doc.uploaded_remittance_file)
		run_doc.uploaded_file_name = filename
		run_doc.uploaded_file_sha256 = digest
		run_doc.uploaded_file_line_count = len(actual_rows)
		run_doc.uploaded_file_parsed_on = now()
		run_doc.uploaded_file_parsed_by = frappe.session.user
	_generate_lines_from_preparation_run(run_doc, actual_rows)
	_update_totals_and_readiness(run_doc)
	run_doc.save(ignore_permissions=True)
	_sync_summary_to_links(run_doc)
	frappe.db.commit()
	return {"name": run_doc.name, "message": "Actual remittance import lines generated."}


@frappe.whitelist()
def validate_actual_remittance_import_readiness(actual_remittance_import_run):
	run_doc = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run)
	missing = _update_totals_and_readiness(run_doc)
	run_doc.save(ignore_permissions=True)
	_sync_summary_to_links(run_doc)
	frappe.db.commit()
	return {"name": run_doc.name, "ready": not missing, "missing": missing, "message": "Actual remittance readiness validated."}


@frappe.whitelist()
def mark_ready_for_remittance_import_draft_creation(actual_remittance_import_run):
	_check_role()
	run_doc = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run)
	missing = _update_totals_and_readiness(run_doc)
	if missing:
		frappe.throw(_("Actual remittance import run is not ready: {0}").format("; ".join(missing[:10])))
	run_doc.status = "Ready for Remittance Import Draft Creation"
	run_doc.save(ignore_permissions=True)
	_sync_summary_to_links(run_doc)
	frappe.db.commit()
	return {"name": run_doc.name, "message": "Ready for remittance import draft creation."}


@frappe.whitelist()
def approve_actual_remittance_import_run(actual_remittance_import_run):
	_check_role()
	run_doc = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run)
	if run_doc.status != "Ready for Remittance Import Draft Creation":
		frappe.throw(_("Only a ready Actual Remittance Import Run can be approved."))
	missing = _update_totals_and_readiness(run_doc)
	if missing:
		frappe.throw(_("Actual remittance import run is not ready: {0}").format("; ".join(missing[:10])))
	run_doc.status = "Actual Remittance Import Run Approved"
	run_doc.remittance_import_draft_creation_allowed = 0
	run_doc.payment_entry_creation_allowed = 0
	run_doc.journal_creation_allowed = 0
	run_doc.write_off_creation_allowed = 0
	run_doc.recovery_creation_allowed = 0
	run_doc.save(ignore_permissions=True)
	_sync_summary_to_links(run_doc)
	frappe.db.commit()
	return {"name": run_doc.name, "message": "Actual Remittance Import Run approved."}


def _ready_lines_for_import_draft(run_doc):
	return [
		row
		for row in run_doc.actual_remittance_lines or []
		if row.line_ready_for_remittance_import_draft
		and row.remittance_import_draft_authorized
		and row.actual_file_matched
		and not row.actual_remittance_hold
	]


def _get_remittance_import_child_table_field():
	meta = frappe.get_meta(NDIS_REMITTANCE_IMPORT)
	for field in meta.fields:
		if field.fieldtype == "Table":
			return field.fieldname
	return None


def _missing_required_fields(doc):
	missing = []
	for field in frappe.get_meta(doc.doctype).fields:
		if field.reqd and not doc.get(field.fieldname) and field.fieldtype not in ("Section Break", "Column Break", "Tab Break"):
			missing.append(field.label or field.fieldname)
	return missing


def _set_remittance_import_header_fields(import_doc, run_doc):
	_set_first_existing(import_doc, ["crm_deal", "deal"], run_doc.crm_deal)
	_set_first_existing(import_doc, ["participant_customer", "customer"], run_doc.participant_customer)
	_set_first_existing(import_doc, ["participant_name"], run_doc.participant_name)
	_set_first_existing(import_doc, ["ndis_number"], run_doc.ndis_number)
	_set_first_existing(import_doc, ["company"], run_doc.company)
	_set_first_existing(import_doc, ["posting_date", "remittance_date", "import_date"], run_doc.actual_remittance_import_date)
	_set_first_existing(import_doc, ["reference_no", "payment_reference", "actual_payment_reference"], run_doc.actual_payment_reference)
	_set_first_existing(import_doc, ["source_run", "actual_remittance_import_run", "ndis_actual_remittance_import_run"], run_doc.name)
	_set_first_existing(import_doc, ["status"], "Draft")
	_set_first_existing(import_doc, ["notes", "remarks"], "Draft created by NDIS CRM Phase 25. No payment, journal, write-off, recovery, bank reconciliation, manual GL, or submit/post action has been performed.")


def _set_remittance_import_line_fields(child, run_doc, row):
	for candidates, value in [
		(("sales_invoice", "invoice"), row.sales_invoice),
		(("claim_batch", "ndis_claim_batch"), row.ndis_claim_batch),
		(("claim_line", "ndis_claim_line"), row.ndis_claim_line),
		(("external_lodgement_reference", "lodgement_reference"), row.external_lodgement_reference),
		(("external_line_reference", "line_reference"), row.external_line_reference),
		(("claim_amount", "claimed_amount"), row.claim_amount),
		(("expected_paid_amount",), row.expected_paid_amount),
		(("paid_amount", "actual_paid_amount", "amount"), row.actual_paid_amount),
		(("rejected_amount", "actual_rejected_amount"), row.actual_rejected_amount),
		(("variance_amount",), row.variance_amount),
		(("payment_reference", "actual_payment_reference"), row.actual_payment_reference),
		(("payment_date", "actual_payment_date"), row.actual_payment_date),
		(("rejection_code",), row.rejection_code),
		(("rejection_reason",), row.rejection_reason),
	]:
		_set_first_existing(child, list(candidates), value)


def _create_ndis_remittance_import_draft(run_doc, ready_lines):
	import_doc = frappe.new_doc(NDIS_REMITTANCE_IMPORT)
	_set_remittance_import_header_fields(import_doc, run_doc)
	child_field = _get_remittance_import_child_table_field()
	if child_field:
		for row in ready_lines:
			child = import_doc.append(child_field, {})
			_set_remittance_import_line_fields(child, run_doc, row)
	missing = _missing_required_fields(import_doc)
	if missing:
		frappe.throw(_("Cannot create draft NDIS Remittance Import. Missing required fields: {0}").format(", ".join(missing)))
	import_doc.insert(ignore_permissions=True)
	if import_doc.docstatus != 0:
		frappe.throw(_("Phase 25 may only create a Draft NDIS Remittance Import."))
	for row in ready_lines:
		row.ndis_remittance_import = import_doc.name
		row.actual_remittance_line_status = "Draft Remittance Import Created"
	return import_doc


@frappe.whitelist()
def create_draft_ndis_remittance_import(actual_remittance_import_run):
	_check_role()
	run_doc = frappe.get_doc(ACTUAL_REMITTANCE_IMPORT_RUN, actual_remittance_import_run)
	if run_doc.status != "Actual Remittance Import Run Approved":
		frappe.throw(_("Only an approved Actual Remittance Import Run can create a draft NDIS Remittance Import."))
	if not run_doc.remittance_import_draft_creation_allowed:
		frappe.throw(_("Tick Remittance Import Draft Creation Allowed before creating the draft."))
	if any([run_doc.payment_entry_creation_allowed, run_doc.journal_creation_allowed, run_doc.write_off_creation_allowed, run_doc.recovery_creation_allowed]):
		frappe.throw(_("Payment Entry, Journal Entry, write-off, and recovery creation are blocked in Phase 25."))
	missing = _update_totals_and_readiness(run_doc)
	if missing:
		frappe.throw(_("Actual remittance import run is not ready: {0}").format("; ".join(missing[:10])))
	ready_lines = _ready_lines_for_import_draft(run_doc)
	if not ready_lines:
		frappe.throw(_("No lines are ready for draft remittance import creation."))
	import_doc = _create_ndis_remittance_import_draft(run_doc, ready_lines)
	run_doc.ndis_remittance_import = import_doc.name
	run_doc.status = "Draft Remittance Import Created"
	run_doc.remittance_import_draft_creation_allowed = 0
	run_doc.payment_entry_creation_allowed = 0
	run_doc.journal_creation_allowed = 0
	run_doc.write_off_creation_allowed = 0
	run_doc.recovery_creation_allowed = 0
	_update_totals_and_readiness(run_doc)
	run_doc.save(ignore_permissions=True)
	_sync_summary_to_links(run_doc)
	frappe.db.commit()
	return {"name": run_doc.name, "ndis_remittance_import": import_doc.name, "message": "Draft NDIS Remittance Import created."}


def validate_actual_remittance_import_run(doc, method=None):
	if any([doc.payment_entry_creation_allowed, doc.journal_creation_allowed, doc.write_off_creation_allowed, doc.recovery_creation_allowed]):
		frappe.throw(_("Phase 25 blocks Payment Entry, Journal Entry, write-off, and recovery creation."))
	if doc.status in READY_STATUSES:
		missing = _update_totals_and_readiness(doc)
		if missing:
			frappe.throw(_("Actual remittance import run is not ready: {0}").format("; ".join(missing[:10])))
	else:
		_update_totals_and_readiness(doc)


def on_actual_remittance_import_run_update(doc, method=None):
	_sync_summary_to_links(doc)


def validate_crm_deal_phase25(doc, method=None):
	if doc.get("ndis_actual_remittance_import_run_required") and not doc.get("ndis_actual_remittance_import_run"):
		if doc.get("status") in ("Won", "Active"):
			frappe.throw(_("Actual Remittance Import Run is required before this CRM Deal can continue."))


def validate_crm_deal_phase25_combined(doc, method=None):
	try:
		from ndis_crm.phase24_remittance_import_preparation import validate_crm_deal_phase24_combined

		validate_crm_deal_phase24_combined(doc, method=method)
	except ImportError:
		pass
	validate_crm_deal_phase25(doc, method=method)


@frappe.whitelist()
def phase25_health_check():
	required = [
		ACTUAL_REMITTANCE_IMPORT_RUN,
		ACTUAL_REMITTANCE_IMPORT_LINE,
		REMITTANCE_IMPORT_PREP_RUN,
		REMITTANCE_IMPORT_PREP_LINE,
		NDIS_REMITTANCE_IMPORT,
	]
	missing = [doctype for doctype in required if not _doctype_exists(doctype)]
	if missing:
		frappe.throw("Missing Phase 25 DocTypes: " + ", ".join(missing))
	for doctype in [CRM_DEAL, REMITTANCE_IMPORT_PREP_RUN, INTAKE]:
		for fieldname in ["ndis_actual_remittance_import_run", "ndis_actual_remittance_import_status", "ndis_actual_remittance_import_ready"]:
			if not _field_exists(doctype, fieldname):
				frappe.throw(f"Missing Phase 25 field {doctype}.{fieldname}")
	if not _get_remittance_import_child_table_field():
		print("NDIS Remittance Import has no child table detected; draft header creation remains guarded.")
	print("Phase 25 health check passed. Actual remittance import bridge creates draft NDIS Remittance Import only; no payment, journal, manual GL, write-off, recovery, bank reconciliation, invoice, claim batch, or claim line creation is performed.")
	return {
		"status": "ok",
		"actual_remittance_import_runs": frappe.db.count(ACTUAL_REMITTANCE_IMPORT_RUN),
		"actual_remittance_import_lines": frappe.db.count(ACTUAL_REMITTANCE_IMPORT_LINE),
		"boundary": "draft_remittance_import_only",
	}
