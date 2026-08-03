import frappe
from frappe import _
from frappe.utils import now


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
CLAIM_BATCH_DRAFT_LINE = "NDIS CRM Claim Batch Draft Line"
CLAIM_BATCH_SUBMISSION_RUN = "NDIS CRM Claim Batch Submission Run"
CLAIM_BATCH_SUBMISSION_LINE = "NDIS CRM Claim Batch Submission Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"

SALES_INVOICE = "Sales Invoice"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"

READY_STATUSES = [
	"Ready for Claim Batch Export Review",
	"Claim Batch Submission Run Approved",
	"Claim Batch Export Ready",
]
APPROVED_STATUSES = ["Claim Batch Submission Run Approved", "Claim Batch Export Ready"]
DRAFT_BATCH_CREATED_STATUSES = ["Draft Claim Batches Created"]

ALLOWED_ROLES = {
	"System Manager",
	"Accounts Manager",
	"Accounts User",
	"NDIS CRM Manager",
	"NDIS Plan Management Officer",
}


def _check_role():
	if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
		frappe.throw(_("You do not have permission to perform this claim batch submission action."))


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


def _existing_run_for_claim_batch_draft_run(claim_batch_draft_run):
	if not _doctype_exists(CLAIM_BATCH_SUBMISSION_RUN):
		return None
	if _field_exists(CLAIM_BATCH_DRAFT_RUN, "ndis_claim_batch_submission_run"):
		existing = frappe.db.get_value(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run, "ndis_claim_batch_submission_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_BATCH_SUBMISSION_RUN, {"claim_batch_draft_run": claim_batch_draft_run}, "name")


def _existing_run_for_deal(deal):
	if not _doctype_exists(CLAIM_BATCH_SUBMISSION_RUN):
		return None
	if _field_exists(CRM_DEAL, "ndis_claim_batch_submission_run"):
		existing = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_batch_submission_run")
		if existing:
			return existing
	return frappe.db.get_value(CLAIM_BATCH_SUBMISSION_RUN, {"crm_deal": deal}, "name")


def _get_claim_batch_draft_run_for_deal(deal):
	if _field_exists(CRM_DEAL, "ndis_claim_batch_draft_run"):
		run = frappe.db.get_value(CRM_DEAL, deal, "ndis_claim_batch_draft_run")
		if run:
			return run
	if _doctype_exists(CLAIM_BATCH_DRAFT_RUN):
		return frappe.db.get_value(CLAIM_BATCH_DRAFT_RUN, {"crm_deal": deal}, "name")
	return None


def _is_claim_batch_draft_created(claim_batch_draft_run):
	if not claim_batch_draft_run or not frappe.db.exists(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run):
		return False
	status, ready = frappe.db.get_value(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run, ["status", "claim_batch_draft_run_ready"])
	return status in DRAFT_BATCH_CREATED_STATUSES and bool(ready)


def _is_submission_run_approved(run):
	if not run or not frappe.db.exists(CLAIM_BATCH_SUBMISSION_RUN, run):
		return False
	status, ready = frappe.db.get_value(CLAIM_BATCH_SUBMISSION_RUN, run, ["status", "claim_batch_submission_run_ready"])
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


def _source_key(row):
	return row.get("claim_source_key") or "|".join(
		[
			str(row.get("service_line") or ""),
			str(row.get("ndis_claim_batch") or ""),
			str(row.get("ndis_claim_line") or ""),
			str(row.get("sales_invoice") or ""),
		]
	)


def _append_line_if_missing(doc, row_data):
	existing = {row.claim_batch_source_key for row in doc.get("submission_lines") or [] if row.get("claim_batch_source_key")}
	key = row_data.get("claim_batch_source_key")
	if key and key in existing:
		return False
	doc.append("submission_lines", row_data)
	return True


def _batch_is_draft(claim_batch):
	snapshot = _claim_batch_snapshot(claim_batch)
	return bool(snapshot and int(snapshot.get("docstatus") or 0) == 0)


def _line_is_draft(claim_line):
	if not claim_line:
		return True
	snapshot = _claim_line_snapshot(claim_line)
	return bool(snapshot and int(snapshot.get("docstatus") or 0) == 0)


def _build_submission_line_from_draft_line(row):
	claim_batch = row.get("ndis_claim_batch")
	claim_line = row.get("ndis_claim_line")
	batch_snapshot = _claim_batch_snapshot(claim_batch)
	line_snapshot = _claim_line_snapshot(claim_line) if claim_line else {}
	claim_batch_docstatus = int(batch_snapshot.get("docstatus") or 0) if batch_snapshot else None
	claim_line_docstatus = int(line_snapshot.get("docstatus") or 0) if line_snapshot else None
	source_ready = bool(
		row.get("claim_batch_draft_status") == "Draft Claim Batch Created"
		and row.get("line_ready_for_claim_batch_draft_creation")
		and row.get("claim_batch_draft_creation_ready")
		and not row.get("claim_batch_draft_creation_hold")
		and claim_batch
		and batch_snapshot
		and claim_batch_docstatus == 0
		and _line_is_draft(claim_line)
		and row.get("sales_invoice")
		and row.get("submitted_invoice_ready")
		and row.get("support_item")
		and row.get("service_booking")
		and row.get("plan_budget")
		and row.get("claim_amount")
	)
	return {
		"claim_batch_source_key": _source_key(row),
		"ndis_claim_batch": claim_batch,
		"ndis_claim_line": claim_line,
		"claim_batch_docstatus": claim_batch_docstatus,
		"claim_line_docstatus": claim_line_docstatus,
		"claim_batch_status": batch_snapshot.get("status") or batch_snapshot.get("claim_batch_status") or batch_snapshot.get("batch_status"),
		"claim_line_status": line_snapshot.get("status") or line_snapshot.get("claim_status"),
		"service_line": row.get("service_line"),
		"service_code": row.get("service_code"),
		"service_model": row.get("service_model"),
		"sales_invoice": row.get("sales_invoice"),
		"sales_invoice_docstatus": row.get("sales_invoice_docstatus"),
		"sales_invoice_status": row.get("sales_invoice_status"),
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
		"claim_batch_draft_source_ready": 1 if source_ready else 0,
		"finance_claim_review_complete": 0,
		"export_mapping_review_complete": 0,
		"submission_authorized": 0,
		"claim_export_ready": 0,
		"claim_submission_ready": 0,
		"submission_hold": 0 if source_ready else 1,
		"submission_hold_reason": None if source_ready else "Draft claim batch source is not ready for export/submission review.",
		"line_ready_for_claim_batch_export": 0,
		"submission_status": "Draft",
		"notes": row.get("notes"),
	}


def _generate_lines_from_claim_batch_draft_run(doc, source):
	created = 0
	for row in source.get("claim_batch_draft_lines") or []:
		if row.get("claim_batch_draft_status") != "Draft Claim Batch Created" or not row.get("ndis_claim_batch"):
			continue
		if _append_line_if_missing(doc, _build_submission_line_from_draft_line(row)):
			created += 1
	return created


def _calculate_totals(doc):
	batches = set()
	totals = {
		"submission_line_count": len(doc.get("submission_lines") or []),
		"claim_batch_count": 0,
		"claim_amount_total": 0,
		"claim_batch_export_ready_count": 0,
		"submission_authorized_count": 0,
		"claim_batch_submission_hold_count": 0,
		"missing_claim_batch_count": 0,
		"missing_claim_line_count": 0,
	}
	for row in doc.get("submission_lines") or []:
		totals["claim_amount_total"] += float(row.get("claim_amount") or 0)
		totals["claim_batch_export_ready_count"] += 1 if row.get("line_ready_for_claim_batch_export") else 0
		totals["submission_authorized_count"] += 1 if row.get("submission_authorized") else 0
		totals["claim_batch_submission_hold_count"] += 1 if row.get("submission_hold") else 0
		if row.get("ndis_claim_batch"):
			batches.add(row.get("ndis_claim_batch"))
		else:
			totals["missing_claim_batch_count"] += 1
		if not row.get("ndis_claim_line"):
			totals["missing_claim_line_count"] += 1
	totals["claim_batch_count"] = len(batches)
	totals["claim_amount_total"] = round(totals["claim_amount_total"], 2)
	return totals


def _sync_totals(doc):
	totals = _calculate_totals(doc)
	for fieldname, value in totals.items():
		if _field_exists(CLAIM_BATCH_SUBMISSION_RUN, fieldname):
			doc.set(fieldname, value)
	return totals


def _calculate_readiness(doc):
	lines = doc.get("submission_lines") or []
	checks = [
		("Claim Batch Draft Run linked", bool(doc.get("claim_batch_draft_run")), []),
		("Draft Claim Batch created by Phase 20", _is_claim_batch_draft_created(doc.get("claim_batch_draft_run")), []),
		("NDIS Claim Batch DocType exists", _doctype_exists(NDIS_CLAIM_BATCH), []),
		("NDIS Claim Line DocType exists", _doctype_exists(NDIS_CLAIM_LINE), []),
		("Participant Customer linked", bool(doc.get("participant_customer")), []),
		("Company selected", bool(doc.get("company")), []),
		("Submission Owner assigned", bool(doc.get("claim_batch_submission_owner")), []),
		("At least one claim batch submission line exists", bool(lines), []),
	]
	line_checks = [
		("All lines have NDIS Claim Batch reference", lambda row: row.get("ndis_claim_batch")),
		("All linked NDIS Claim Batches are still Draft", lambda row: not row.get("ndis_claim_batch") or _batch_is_draft(row.get("ndis_claim_batch"))),
		("All linked NDIS Claim Lines are still Draft", lambda row: not row.get("ndis_claim_line") or _line_is_draft(row.get("ndis_claim_line"))),
		("All lines have submitted Sales Invoice reference", lambda row: row.get("sales_invoice")),
		("All lines have support item", lambda row: row.get("support_item")),
		("All lines have service booking", lambda row: row.get("service_booking")),
		("All lines have plan budget", lambda row: row.get("plan_budget")),
		("All lines have claim amount", lambda row: row.get("claim_amount")),
		("Claim batch draft source-ready flags are complete", lambda row: row.get("claim_batch_draft_source_ready")),
		("Finance claim review complete", lambda row: row.get("finance_claim_review_complete")),
		("Export mapping review complete", lambda row: row.get("export_mapping_review_complete")),
		("All lines have submission authorization", lambda row: row.get("submission_authorized")),
		("No claim submission/export hold remains", lambda row: not row.get("submission_hold")),
		("All lines marked ready for claim batch export", lambda row: row.get("line_ready_for_claim_batch_export")),
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
		"claim_batch_submission_run_ready": total > 0 and complete == total,
		"incomplete": incomplete,
	}


def _sync_summary_to_links(doc):
	summary = _calculate_readiness(doc)
	totals = _sync_totals(doc)
	if _field_exists(CLAIM_BATCH_SUBMISSION_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_BATCH_SUBMISSION_RUN, "claim_batch_submission_run_ready"):
		doc.claim_batch_submission_run_ready = 1 if summary["claim_batch_submission_run_ready"] else 0
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
		(INTAKE, doc.get("participant_intake")),
	]:
		if not name:
			continue
		_db_set_if_field(doctype, name, "ndis_claim_batch_submission_run", doc.name)
		_db_set_if_field(doctype, name, "claim_batch_submission_status", doc.status)
		_db_set_if_field(doctype, name, "claim_batch_submission_ready", 1 if summary["claim_batch_submission_run_ready"] else 0)
	return {"readiness": summary, "totals": totals}


@frappe.whitelist()
def create_claim_batch_submission_run_from_draft_run(claim_batch_draft_run):
	_check_role()
	if not claim_batch_draft_run:
		frappe.throw(_("NDIS CRM Claim Batch Draft Run is required."))
	if not frappe.db.exists(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run):
		frappe.throw(_("NDIS CRM Claim Batch Draft Run {0} was not found.").format(claim_batch_draft_run))
	existing = _existing_run_for_claim_batch_draft_run(claim_batch_draft_run)
	if existing:
		return {"doctype": CLAIM_BATCH_SUBMISSION_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Batch Submission Run returned."}
	source = frappe.get_doc(CLAIM_BATCH_DRAFT_RUN, claim_batch_draft_run)
	doc = frappe.new_doc(CLAIM_BATCH_SUBMISSION_RUN)
	for fieldname in [
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
		"claim_batch_owner",
		"claim_owner",
		"billing_owner",
	]:
		doc.set(fieldname, source.get(fieldname))
	doc.status = "Draft"
	doc.claim_batch_draft_run = source.name
	doc.participant_name = source.get("participant_name") or source.get("participant_customer") or source.name
	doc.claim_batch_submission_owner = frappe.session.user
	doc.claim_export_allowed = 0
	doc.claim_submission_allowed = 0
	created_count = _generate_lines_from_claim_batch_draft_run(doc, source)
	_sync_totals(doc)
	summary = _calculate_readiness(doc)
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_batch_submission_run_ready = 1 if summary["claim_batch_submission_run_ready"] else 0
	doc.insert(ignore_permissions=False)
	_sync_summary_to_links(doc)
	frappe.db.commit()
	return {
		"doctype": CLAIM_BATCH_SUBMISSION_RUN,
		"name": doc.name,
		"created": True,
		"submission_line_count": created_count,
		"message": "NDIS CRM Claim Batch Submission Run created successfully.",
	}


@frappe.whitelist()
def create_claim_batch_submission_run_from_crm_deal(deal):
	_check_role()
	if not deal:
		frappe.throw(_("CRM Deal is required."))
	if not frappe.db.exists(CRM_DEAL, deal):
		frappe.throw(_("CRM Deal {0} was not found.").format(deal))
	existing = _existing_run_for_deal(deal)
	if existing:
		return {"doctype": CLAIM_BATCH_SUBMISSION_RUN, "name": existing, "created": False, "message": "Existing NDIS CRM Claim Batch Submission Run returned."}
	draft_run = _get_claim_batch_draft_run_for_deal(deal)
	if not draft_run:
		frappe.throw(_("Please create NDIS CRM Claim Batch Draft Run before creating Claim Batch Submission Run."))
	return create_claim_batch_submission_run_from_draft_run(draft_run)


@frappe.whitelist()
def generate_claim_batch_submission_lines(claim_batch_submission_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run)
	if not doc.get("claim_batch_draft_run"):
		frappe.throw(_("Claim Batch Draft Run is required."))
	source = frappe.get_doc(CLAIM_BATCH_DRAFT_RUN, doc.claim_batch_draft_run)
	created_count = _generate_lines_from_claim_batch_draft_run(doc, source)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"created_count": created_count, "summary": summary, "message": f"Claim batch submission lines generated. Created: {created_count}."}


@frappe.whitelist()
def validate_claim_batch_submission_readiness(claim_batch_submission_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run)
	summary = _sync_summary_to_links(doc)
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"summary": summary, "message": "Claim Batch Submission Run readiness validated."}


@frappe.whitelist()
def mark_ready_for_claim_batch_export_review(claim_batch_submission_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_batch_submission_run_ready"]:
		frappe.throw(_("Cannot mark Ready for Claim Batch Export Review. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Ready for Claim Batch Export Review"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_batch_submission_run_ready = 1
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_BATCH_SUBMISSION_RUN, "name": doc.name, "message": "Claim Batch Submission Run marked Ready for Claim Batch Export Review."}


@frappe.whitelist()
def approve_claim_batch_submission_run(claim_batch_submission_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run)
	summary = _calculate_readiness(doc)
	if not summary["claim_batch_submission_run_ready"]:
		frappe.throw(_("Cannot approve Claim Batch Submission Run. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	doc.status = "Claim Batch Submission Run Approved"
	doc.readiness_percent = summary["readiness_percent"]
	doc.claim_batch_submission_run_ready = 1
	doc.claim_export_allowed = 0
	doc.claim_submission_allowed = 0
	for row in doc.get("submission_lines") or []:
		if row.get("submission_status") in ["Draft", "Ready"]:
			row.submission_status = "Approved"
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"doctype": CLAIM_BATCH_SUBMISSION_RUN, "name": doc.name, "message": "Claim Batch Submission Run approved. No claim export or submission was performed."}


@frappe.whitelist()
def mark_claim_batch_export_ready(claim_batch_submission_run):
	_check_role()
	doc = frappe.get_doc(CLAIM_BATCH_SUBMISSION_RUN, claim_batch_submission_run)
	if doc.status != "Claim Batch Submission Run Approved":
		frappe.throw(_("Claim Batch Submission Run must be approved before marking export-ready."))
	if not doc.get("claim_export_allowed"):
		frappe.throw(_("Tick Claim Export Allowed before marking the claim batch export-ready."))
	summary = _calculate_readiness(doc)
	if not summary["claim_batch_submission_run_ready"]:
		frappe.throw(_("Cannot mark Claim Batch Export Ready. Incomplete items: {0}").format("; ".join(summary["incomplete"])))
	claim_batches = set()
	for row in doc.get("submission_lines") or []:
		if row.get("ndis_claim_batch"):
			claim_batches.add(row.get("ndis_claim_batch"))
		row.claim_export_ready = 1
		row.claim_submission_ready = 0
		row.submission_status = "Export Ready"
		row.prepared_by = frappe.session.user
		row.prepared_on = now()
	for claim_batch in claim_batches:
		if frappe.db.exists(NDIS_CLAIM_BATCH, claim_batch):
			batch = frappe.get_doc(NDIS_CLAIM_BATCH, claim_batch)
			_set_first_existing(batch, ["status", "claim_batch_status", "batch_status"], "Export Ready")
			_set_first_existing(batch, ["export_ready", "claim_export_ready"], 1)
			_set_first_existing(batch, ["export_ready_on", "claim_export_ready_on"], now())
			_set_first_existing(batch, ["export_ready_by", "claim_export_ready_by"], frappe.session.user)
			batch.save(ignore_permissions=True)
	doc.status = "Claim Batch Export Ready"
	doc.claim_export_allowed = 0
	doc.claim_submission_allowed = 0
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"claim_batches": list(claim_batches),
		"message": "Claim Batch marked export-ready only. No export file, portal lodgement, payment, journal, remittance, write-off, or recovery record was created.",
	}


def validate_claim_batch_submission_run(doc, method=None):
	summary = _calculate_readiness(doc)
	_sync_totals(doc)
	if _field_exists(CLAIM_BATCH_SUBMISSION_RUN, "readiness_percent"):
		doc.readiness_percent = summary["readiness_percent"]
	if _field_exists(CLAIM_BATCH_SUBMISSION_RUN, "claim_batch_submission_run_ready"):
		doc.claim_batch_submission_run_ready = 1 if summary["claim_batch_submission_run_ready"] else 0
	if doc.status in READY_STATUSES and not summary["claim_batch_submission_run_ready"]:
		frappe.throw(_("Cannot set Claim Batch Submission Run to {0}. Incomplete items: {1}").format(doc.status, "; ".join(summary["incomplete"])))
	if doc.status != "Claim Batch Submission Run Approved":
		if doc.get("claim_export_allowed"):
			frappe.throw(_("Claim Export Allowed can only be ticked after the run is approved."))
		if doc.get("claim_submission_allowed"):
			frappe.throw(_("Claim Submission Allowed can only be ticked after the run is approved."))
	if doc.get("claim_submission_allowed"):
		frappe.throw(_("Actual claim submission is not allowed in Phase 21. This phase only prepares export/submission readiness."))


def on_claim_batch_submission_run_update(doc, method=None):
	try:
		_sync_summary_to_links(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "NDIS CRM Claim Batch Submission Run Summary Sync Failed")


def validate_crm_deal_phase21(doc, method=None):
	if doc.status != "Won / Active Client":
		return
	required = doc.get("ndis_claim_batch_submission_run_required") if _field_exists(CRM_DEAL, "ndis_claim_batch_submission_run_required") else 0
	if not required:
		return
	run = doc.get("ndis_claim_batch_submission_run") if _field_exists(CRM_DEAL, "ndis_claim_batch_submission_run") else None
	if not run:
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Batch Submission Run must be created and approved."))
	if not _is_submission_run_approved(run):
		frappe.throw(_("Cannot mark CRM Deal as Won / Active Client. NDIS Claim Batch Submission Run must be approved."))


def validate_crm_deal_phase21_combined(doc, method=None):
	try:
		from ndis_crm.phase20_claim_batch_draft import validate_crm_deal_phase20_combined

		validate_crm_deal_phase20_combined(doc, method)
	except ImportError:
		pass
	validate_crm_deal_phase21(doc, method)


def phase21_health_check():
	print("---- NDIS CRM Phase 21 Health Check ----")
	for dt in [
		CLAIM_BATCH_SUBMISSION_LINE,
		CLAIM_BATCH_SUBMISSION_RUN,
		CLAIM_BATCH_DRAFT_RUN,
		CLAIM_BATCH_DRAFT_LINE,
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
	]:
		print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")
	for field in [
		"ndis_claim_batch_submission_run_required",
		"ndis_claim_batch_submission_run",
		"claim_batch_submission_status",
		"claim_batch_submission_ready",
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
		INTAKE,
	]:
		if not _doctype_exists(doctype):
			print(f"{doctype}: OPTIONAL / MISSING")
			continue
		for field in ["ndis_claim_batch_submission_run", "claim_batch_submission_status", "claim_batch_submission_ready"]:
			print(f"{doctype} field {field}: {'OK' if _field_exists(doctype, field) else 'MISSING'}")
	count = frappe.db.count(CLAIM_BATCH_SUBMISSION_RUN) if _doctype_exists(CLAIM_BATCH_SUBMISSION_RUN) else 0
	print("NDIS CRM Claim Batch Submission Run records:", count)
	print("Phase 21 creates a claim batch export/submission gate only.")
	print("Phase 21 does not export, submit, remit, pay, journal, write off, recover, or manually post GL.")
	print("---- End Phase 21 Health Check ----")
