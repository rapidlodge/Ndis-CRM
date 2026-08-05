import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

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
ACTUAL_REMITTANCE_IMPORT_RUN = "NDIS CRM Actual Remittance Import Run"
REMITTANCE_MATCHING_REVIEW_RUN = "NDIS CRM Remittance Matching Review Run"
REMITTANCE_MATCHING_REVIEW_LINE = "NDIS CRM Remittance Matching Review Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_remittance_matching_review_doctypes()
	create_custom_fields_phase26()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 26 Remittance Matching Review bridge installed successfully.")


def doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def ensure_required_doctypes():
	required = [
		CRM_DEAL,
		INTAKE,
		HANDOVER,
		FINANCE_ONBOARDING,
		OPERATIONS_SETUP,
		SCHEDULE_DRAFT,
		ROSTER_REQUEST,
		SERVICE_FILE,
		SESSION_DRAFT,
		EVIDENCE_REVIEW,
		DOWNSTREAM_PREPARATION,
		BILLING_DRAFT,
		CLAIM_DRAFT,
		INVOICE_DRAFT,
		SALES_INVOICE_DRAFT_RUN,
		SALES_INVOICE_SUBMISSION_RUN,
		CLAIM_BATCH_DRAFT_RUN,
		CLAIM_BATCH_SUBMISSION_RUN,
		CLAIM_EXPORT_PREP_RUN,
		CLAIM_LODGEMENT_CONFIRMATION_RUN,
		REMITTANCE_IMPORT_PREP_RUN,
		ACTUAL_REMITTANCE_IMPORT_RUN,
		"Sales Invoice",
		"NDIS Claim Batch",
		"NDIS Claim Line",
		"NDIS Remittance Import",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 26 DocTypes: " + ", ".join(missing))
	print("Required Phase 26 DocTypes found.")


def make_field(label, fieldname, fieldtype, **kwargs):
	field = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype}
	field.update(kwargs)
	return field


def standard_permissions():
	return [
		{"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1},
		{"role": "Accounts Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1},
		{"role": "Accounts User", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
		{"role": "NDIS CRM Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1},
		{"role": "NDIS Plan Management Officer", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
		{"role": "NDIS CRM Read Only", "read": 1, "export": 1, "print": 1, "report": 1},
	]


def create_doctype_if_missing(name, fields, autoname=None, title_field=None, istable=0):
	if frappe.db.exists("DocType", name):
		print(f"DocType already exists: {name}")
		return
	doc = frappe.get_doc({
		"doctype": "DocType",
		"name": name,
		"module": MODULE_NAME,
		"custom": 0,
		"istable": istable,
		"editable_grid": 1 if istable else 0,
		"track_changes": 1,
		"allow_rename": 1,
		"autoname": autoname,
		"title_field": title_field,
	})
	for field in fields:
		doc.append("fields", field)
	if not istable:
		for perm in standard_permissions():
			doc.append("permissions", perm)
	doc.insert(ignore_permissions=True)
	print(f"Created DocType: {name}")


def optional_link(doctype):
	return ("Link", doctype) if doctype_exists(doctype) else ("Data", None)


def create_remittance_matching_review_doctypes():
	create_matching_review_line()
	create_matching_review_run()


def create_matching_review_line():
	support_type, support_options = optional_link(NDIS_SUPPORT_ITEM)
	service_type, service_options = optional_link(NDIS_SERVICE_TYPE)
	budget_type, budget_options = optional_link(PLAN_BUDGET)
	booking_type, booking_options = optional_link(SERVICE_BOOKING)
	house_type, house_options = optional_link(NDIS_HOUSE)
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Matching Source Key", "matching_source_key", "Data", read_only=1),
		make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import", in_list_view=1),
		make_field("NDIS Remittance Import Docstatus", "ndis_remittance_import_docstatus", "Int", read_only=1),
		make_field("NDIS Remittance Import Status", "ndis_remittance_import_status", "Data", read_only=1),
		make_field("Claim Links", "claim_links_section", "Section Break"),
		make_field("NDIS Claim Batch", "ndis_claim_batch", "Link", options="NDIS Claim Batch", in_list_view=1),
		make_field("NDIS Claim Line", "ndis_claim_line", "Link", options="NDIS Claim Line"),
		make_field("Claim Batch Status", "claim_batch_status", "Data", read_only=1),
		make_field("Claim Line Status", "claim_line_status", "Data", read_only=1),
		make_field("Sales Invoice Snapshot", "sales_invoice_snapshot_section", "Section Break"),
		make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", in_list_view=1),
		make_field("Sales Invoice Docstatus", "sales_invoice_docstatus", "Int", read_only=1),
		make_field("Sales Invoice Status", "sales_invoice_status", "Data", read_only=1),
		make_field("Sales Invoice Outstanding Amount", "sales_invoice_outstanding_amount", "Currency", read_only=1),
		make_field("Service Snapshot", "service_snapshot_section", "Section Break"),
		make_field("Service Line", "service_line", "Link" if doctype_exists("NDIS Service Line") else "Data", options="NDIS Service Line" if doctype_exists("NDIS Service Line") else None, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Service Date", "service_date", "Date", in_list_view=1),
		make_field("Claim Quantity", "claim_quantity", "Float"),
		make_field("Claim Unit", "claim_unit", "Data", default="Hour"),
		make_field("Claim Rate", "claim_rate", "Currency"),
		make_field("Claim Amount", "claim_amount", "Currency", in_list_view=1),
		make_field("Expected Paid Amount", "expected_paid_amount", "Currency"),
		make_field("Expected Rejected Amount", "expected_rejected_amount", "Currency"),
		make_field("Actual Paid Amount", "actual_paid_amount", "Currency", in_list_view=1),
		make_field("Actual Rejected Amount", "actual_rejected_amount", "Currency"),
		make_field("Variance Amount", "variance_amount", "Currency", read_only=1),
		make_field("NDIS Finance Snapshot", "ndis_finance_snapshot_section", "Section Break"),
		make_field("Support Item", "support_item", support_type, options=support_options),
		make_field("Finance Service Type", "finance_service_type", service_type, options=service_options),
		make_field("NDIS Plan Budget", "plan_budget", budget_type, options=budget_options),
		make_field("NDIS Service Booking", "service_booking", booking_type, options=booking_options),
		make_field("Funding Source", "funding_source", "Data"),
		make_field("Default House", "default_house", house_type, options=house_options),
		make_field("Invoice Group Key", "invoice_group_key", "Data"),
		make_field("Actual Remittance Snapshot", "actual_remittance_snapshot_section", "Section Break"),
		make_field("External Lodgement Reference", "external_lodgement_reference", "Data"),
		make_field("External Batch Reference", "external_batch_reference", "Data"),
		make_field("External Line Reference", "external_line_reference", "Data"),
		make_field("Actual Payment Reference", "actual_payment_reference", "Data"),
		make_field("Actual Payment Date", "actual_payment_date", "Date"),
		make_field("Actual Remittance Status", "actual_remittance_status", "Data"),
		make_field("Rejection Code", "rejection_code", "Data"),
		make_field("Rejection Reason", "rejection_reason", "Small Text"),
		make_field("Matching Decision", "matching_decision_section", "Section Break"),
		make_field("Remittance Import Source Ready", "remittance_import_source_ready", "Check", default=0),
		make_field("Matching Result", "matching_result", "Select", options="Full Payment Match\nPartial Payment\nRejected\nOverpayment\nUnderpayment\nUnmatched\nManual Review", in_list_view=1),
		make_field("Matching Reason", "matching_reason", "Small Text"),
		make_field("Recommended Next Action", "recommended_next_action", "Data", read_only=1),
		make_field("Matching Review Complete", "matching_review_complete", "Check", default=0),
		make_field("Matching Decision Authorized", "matching_decision_authorized", "Check", default=0),
		make_field("Blocked Future Actions", "blocked_future_actions_section", "Section Break"),
		make_field("Payment Allocation Authorized", "payment_allocation_authorized", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Journal Authorized", "journal_authorized", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Write Off Authorized", "write_off_authorized", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Recovery Authorized", "recovery_authorized", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Matching Hold", "matching_hold", "Check", default=1, in_list_view=1),
		make_field("Matching Hold Reason", "matching_hold_reason", "Small Text"),
		make_field("Line Status", "line_status_section", "Section Break"),
		make_field("Line Ready for Matching Completion", "line_ready_for_matching_completion", "Check", default=0, in_list_view=1),
		make_field("Matching Line Status", "matching_line_status", "Select", options="Draft\nReady\nApproved\nMatching Review Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(REMITTANCE_MATCHING_REVIEW_LINE, fields, istable=1)


def create_matching_review_run():
	profile_type, profile_options = optional_link(FINANCE_PROFILE)
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-REMIT-MATCH-.YYYY.-.#####", default="NDIS-REMIT-MATCH-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Matching Decision Review\nRemittance Matching Review Approved\nMatching Review Completed\nReturned to Actual Remittance Import\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Remittance Matching Review Run Ready", "remittance_matching_review_run_ready", "Check", read_only=1, in_list_view=1),
		make_field("Matching Completion Allowed", "matching_completion_allowed", "Check", default=0),
		make_field("Payment Allocation Allowed", "payment_allocation_allowed", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Journal Creation Allowed", "journal_creation_allowed", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Write Off Creation Allowed", "write_off_creation_allowed", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Recovery Creation Allowed", "recovery_creation_allowed", "Check", default=0, description="Blocked in Phase 26."),
		make_field("Output", "output_section", "Section Break"),
		make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import", read_only=1),
		make_field("Uploaded Remittance File", "uploaded_remittance_file", "Attach", read_only=1),
		make_field("Uploaded File SHA256", "uploaded_file_hash", "Data", read_only=1),
		make_field("Summary", "summary_section", "Section Break"),
		make_field("Matching Line Count", "matching_line_count", "Int", read_only=1),
		make_field("Claim Batch Count", "claim_batch_count", "Int", read_only=1),
		make_field("Claim Amount Total", "claim_amount_total", "Currency", read_only=1),
		make_field("Expected Paid Amount Total", "expected_paid_amount_total", "Currency", read_only=1),
		make_field("Actual Paid Amount Total", "actual_paid_amount_total", "Currency", read_only=1),
		make_field("Actual Rejected Amount Total", "actual_rejected_amount_total", "Currency", read_only=1),
		make_field("Variance Amount Total", "variance_amount_total", "Currency", read_only=1),
		make_field("Full Match Count", "full_match_count", "Int", read_only=1),
		make_field("Partial Payment Count", "partial_payment_count", "Int", read_only=1),
		make_field("Rejected Count", "rejected_count", "Int", read_only=1),
		make_field("Overpayment Count", "overpayment_count", "Int", read_only=1),
		make_field("Underpayment Count", "underpayment_count", "Int", read_only=1),
		make_field("Unmatched Count", "unmatched_count", "Int", read_only=1),
		make_field("Manual Review Count", "manual_review_count", "Int", read_only=1),
		make_field("Matching Ready Count", "matching_ready_count", "Int", read_only=1),
		make_field("Matching Hold Count", "matching_hold_count", "Int", read_only=1),
		make_field("Blocked Payment Authorization Count", "blocked_payment_authorization_count", "Int", read_only=1),
		make_field("Blocked Journal Authorization Count", "blocked_journal_authorization_count", "Int", read_only=1),
		make_field("Blocked Write Off Authorization Count", "blocked_write_off_authorization_count", "Int", read_only=1),
		make_field("Blocked Recovery Authorization Count", "blocked_recovery_authorization_count", "Int", read_only=1),
		make_field("Source Links", "source_links_section", "Section Break"),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
		make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
		make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER),
		make_field("NDIS CRM Finance Onboarding", "finance_onboarding", "Link", options=FINANCE_ONBOARDING),
		make_field("NDIS CRM Operations Setup", "operations_setup", "Link", options=OPERATIONS_SETUP),
		make_field("NDIS CRM Service Schedule Draft", "service_schedule_draft", "Link", options=SCHEDULE_DRAFT),
		make_field("NDIS CRM Roster Build Request", "roster_build_request", "Link", options=ROSTER_REQUEST),
		make_field("NDIS Participant Service File", "participant_service_file", "Link", options=SERVICE_FILE),
		make_field("NDIS CRM Service Session Draft", "service_session_draft", "Link", options=SESSION_DRAFT),
		make_field("NDIS CRM Delivery Evidence Review", "delivery_evidence_review", "Link", options=EVIDENCE_REVIEW),
		make_field("NDIS CRM Downstream Preparation", "downstream_preparation", "Link", options=DOWNSTREAM_PREPARATION),
		make_field("NDIS CRM Attendance Draft", "attendance_draft", "Link" if doctype_exists(ATTENDANCE_DRAFT) else "Data", options=ATTENDANCE_DRAFT if doctype_exists(ATTENDANCE_DRAFT) else None),
		make_field("NDIS CRM Billing Draft", "billing_draft", "Link", options=BILLING_DRAFT),
		make_field("NDIS CRM Claim Draft", "claim_draft", "Link", options=CLAIM_DRAFT),
		make_field("NDIS CRM Invoice Draft", "invoice_draft", "Link", options=INVOICE_DRAFT),
		make_field("NDIS CRM Sales Invoice Draft Run", "sales_invoice_draft_run", "Link", options=SALES_INVOICE_DRAFT_RUN),
		make_field("NDIS CRM Sales Invoice Submission Run", "sales_invoice_submission_run", "Link", options=SALES_INVOICE_SUBMISSION_RUN),
		make_field("NDIS CRM Claim Batch Draft Run", "claim_batch_draft_run", "Link", options=CLAIM_BATCH_DRAFT_RUN),
		make_field("NDIS CRM Claim Batch Submission Run", "claim_batch_submission_run", "Link", options=CLAIM_BATCH_SUBMISSION_RUN),
		make_field("NDIS CRM Claim Export Preparation Run", "claim_export_preparation_run", "Link", options=CLAIM_EXPORT_PREP_RUN),
		make_field("NDIS CRM Claim Lodgement Confirmation Run", "claim_lodgement_confirmation_run", "Link", options=CLAIM_LODGEMENT_CONFIRMATION_RUN),
		make_field("NDIS CRM Remittance Import Preparation Run", "remittance_import_preparation_run", "Link", options=REMITTANCE_IMPORT_PREP_RUN),
		make_field("NDIS CRM Actual Remittance Import Run", "actual_remittance_import_run", "Link", options=ACTUAL_REMITTANCE_IMPORT_RUN, reqd=1, in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
		make_field("NDIS Financial Profile", "ndis_financial_profile", profile_type, options=profile_options),
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Company", "company", "Link", options="Company"),
		make_field("Remittance Details", "remittance_details_section", "Section Break"),
		make_field("Actual Remittance Import Date", "actual_remittance_import_date", "Date"),
		make_field("External Lodgement Reference", "external_lodgement_reference", "Data"),
		make_field("External Batch Reference", "external_batch_reference", "Data"),
		make_field("Actual Payment Reference", "actual_payment_reference", "Data"),
		make_field("Claim Window", "claim_window_section", "Section Break"),
		make_field("Claim Period Start", "claim_period_start", "Date"),
		make_field("Claim Period End", "claim_period_end", "Date"),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Matching Review Owner", "matching_review_owner", "Link", options="User", in_list_view=1),
		make_field("Actual Remittance Owner", "actual_remittance_owner", "Link", options="User"),
		make_field("Remittance Owner", "remittance_owner", "Link", options="User"),
		make_field("Claim Lodgement Owner", "claim_lodgement_owner", "Link", options="User"),
		make_field("Claim Owner", "claim_owner", "Link", options="User"),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Completed By", "completed_by", "Link", options="User", read_only=1),
		make_field("Completed On", "completed_on", "Datetime", read_only=1),
		make_field("Matching Lines", "matching_lines_section", "Section Break"),
		make_field("Matching Lines", "matching_lines", "Table", options=REMITTANCE_MATCHING_REVIEW_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Matching Review Notes", "matching_review_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(REMITTANCE_MATCHING_REVIEW_RUN, fields, autoname="naming_series:", title_field="participant_name")


def create_custom_fields_phase26():
	deal_fields = [
		make_field("NDIS Remittance Matching Review Run", "remittance_matching_review_section", "Section Break", insert_after="actual_remittance_import_ready"),
		make_field("Remittance Matching Review Required Before Active Deal", "ndis_remittance_matching_review_run_required", "Check", default=0),
		make_field("NDIS CRM Remittance Matching Review Run", "ndis_remittance_matching_review_run", "Link", options=REMITTANCE_MATCHING_REVIEW_RUN, read_only=1),
		make_field("Remittance Matching Review Status", "remittance_matching_review_status", "Data", read_only=1),
		make_field("Remittance Matching Review Ready", "remittance_matching_review_ready", "Check", read_only=1),
	]
	shared_fields = [
		make_field("NDIS Remittance Matching Review Run", "remittance_matching_review_section", "Section Break", insert_after="actual_remittance_import_ready"),
		make_field("NDIS CRM Remittance Matching Review Run", "ndis_remittance_matching_review_run", "Link", options=REMITTANCE_MATCHING_REVIEW_RUN, read_only=1),
		make_field("Remittance Matching Review Status", "remittance_matching_review_status", "Data", read_only=1),
		make_field("Remittance Matching Review Ready", "remittance_matching_review_ready", "Check", read_only=1),
	]
	custom_fields = {
		CRM_DEAL: deal_fields,
		HANDOVER: shared_fields,
		FINANCE_ONBOARDING: shared_fields,
		OPERATIONS_SETUP: shared_fields,
		SCHEDULE_DRAFT: shared_fields,
		ROSTER_REQUEST: shared_fields,
		SERVICE_FILE: shared_fields,
		SESSION_DRAFT: shared_fields,
		EVIDENCE_REVIEW: shared_fields,
		DOWNSTREAM_PREPARATION: shared_fields,
		BILLING_DRAFT: shared_fields,
		CLAIM_DRAFT: shared_fields,
		INVOICE_DRAFT: shared_fields,
		SALES_INVOICE_DRAFT_RUN: shared_fields,
		SALES_INVOICE_SUBMISSION_RUN: shared_fields,
		CLAIM_BATCH_DRAFT_RUN: shared_fields,
		CLAIM_BATCH_SUBMISSION_RUN: shared_fields,
		CLAIM_EXPORT_PREP_RUN: shared_fields,
		CLAIM_LODGEMENT_CONFIRMATION_RUN: shared_fields,
		REMITTANCE_IMPORT_PREP_RUN: shared_fields,
		ACTUAL_REMITTANCE_IMPORT_RUN: shared_fields,
		INTAKE: shared_fields,
	}
	if doctype_exists(ATTENDANCE_DRAFT):
		custom_fields[ATTENDANCE_DRAFT] = shared_fields
	create_custom_fields(custom_fields, update=True)
	print("Created / updated Phase 26 remittance matching review custom fields.")


def upsert_doc(doctype, name, values):
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for key, value in values.items():
			doc.set(key, value)
		doc.save(ignore_permissions=True)
		print(f"Updated {doctype}: {name}")
	else:
		doc = frappe.get_doc({"doctype": doctype, "name": name, **values})
		doc.insert(ignore_permissions=True)
		print(f"Created {doctype}: {name}")


def create_form_scripts():
	upsert_doc("CRM Form Script", "NDIS CRM Deal Actions", {"dt": CRM_DEAL, "view": "Form", "enabled": 1, "is_standard": 0, "script": _deal_script()})
	if frappe.db.exists("DocType", "Client Script"):
		upsert_doc("Client Script", "NDIS CRM Actual Remittance Import Run Actions", {"dt": ACTUAL_REMITTANCE_IMPORT_RUN, "view": "Form", "enabled": 1, "script": _actual_import_script()})
		upsert_doc("Client Script", "NDIS CRM Remittance Matching Review Run Actions", {"dt": REMITTANCE_MATCHING_REVIEW_RUN, "view": "Form", "enabled": 1, "script": _run_script()})


def _deal_script():
	try:
		from ndis_crm.setup.phase25_actual_remittance_import import _deal_script as previous_script

		script = previous_script()
	except Exception:
		script = "function setupForm({ doc, call, createToast }) {\n  return { actions: [] }\n}"
	insert = r'''
      {
        label: "Create Remittance Matching Review Run",
        onClick: () => {
          call("ndis_crm.phase26_remittance_matching_review.create_remittance_matching_review_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Remittance Matching Review Run Created" : "Existing Matching Review Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-remittance-matching-review-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Remittance Matching Review Run",
        onClick: () => {
          if (doc.ndis_remittance_matching_review_run) {
            window.open(`/app/ndis-crm-remittance-matching-review-run/${doc.ndis_remittance_matching_review_run}`, "_blank")
          } else {
            createToast({ title: "No Remittance Matching Review Run linked yet", icon: "info" })
          }
        }
      }
'''.rstrip()
	return script.replace("\n    ]", ",\n" + insert + "\n    ]", 1)


def _actual_import_script():
	try:
		from ndis_crm.setup.phase25_actual_remittance_import import _run_script as previous_script

		script = previous_script()
	except Exception:
		script = 'frappe.ui.form.on("NDIS CRM Actual Remittance Import Run", { refresh(frm) { if (frm.is_new()) { return; } } });'
	insert = r'''

        frm.add_custom_button(__("Create Remittance Matching Review Run"), function () {
            frappe.call({
                method: "ndis_crm.phase26_remittance_matching_review.create_remittance_matching_review_run_from_actual_remittance_import_run",
                args: { actual_remittance_import_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating remittance matching review run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Remittance Matching Review Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Remittance Matching Review Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_remittance_matching_review_run) {
            frm.add_custom_button(__("Open Remittance Matching Review Run"), function () {
                frappe.set_route("Form", "NDIS CRM Remittance Matching Review Run", frm.doc.ndis_remittance_matching_review_run);
            }, __("Open"));
        }
'''
	return script.replace("\n    }\n});", insert + "\n    }\n});", 1)


def _run_script():
	return r'''
frappe.ui.form.on("NDIS CRM Remittance Matching Review Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        const callAction = (label, method, freeze_message) => {
            frappe.call({
                method,
                args: { remittance_matching_review_run: frm.doc.name },
                freeze: true,
                freeze_message
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || label, indicator: "green" });
                    frm.reload_doc();
                }
            });
        };

        frm.add_custom_button(__("Generate Matching Review Lines"), function () {
            callAction(__("Matching review lines generated"), "ndis_crm.phase26_remittance_matching_review.generate_remittance_matching_review_lines", __("Generating matching review lines..."));
        }, __("Actions"));

        frm.add_custom_button(__("Validate Matching Review Readiness"), function () {
            callAction(__("Matching review readiness validated"), "ndis_crm.phase26_remittance_matching_review.validate_remittance_matching_review_readiness", __("Validating matching review readiness..."));
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Matching Decision Review"), function () {
            callAction(__("Ready for matching decision review"), "ndis_crm.phase26_remittance_matching_review.mark_ready_for_matching_decision_review", __("Marking ready for matching decision review..."));
        }, __("Actions"));

        frm.add_custom_button(__("Approve Matching Review Run"), function () {
            callAction(__("Matching Review Run approved"), "ndis_crm.phase26_remittance_matching_review.approve_remittance_matching_review_run", __("Approving matching review run..."));
        }, __("Actions"));

        frm.add_custom_button(__("Complete Matching Review"), function () {
            frappe.confirm(
                __("This completes the matching review only. It will not create Payment Entry, Journal Entry, write-off, recovery, bank reconciliation, manual GL, or submit/post anything."),
                function () {
                    callAction(__("Matching review completed"), "ndis_crm.phase26_remittance_matching_review.complete_remittance_matching_review", __("Completing matching review..."));
                }
            );
        }, __("Actions"));

        if (frm.doc.actual_remittance_import_run) {
            frm.add_custom_button(__("Open Actual Remittance Import Run"), function () {
                frappe.set_route("Form", "NDIS CRM Actual Remittance Import Run", frm.doc.actual_remittance_import_run);
            }, __("Open"));
        }

        if (frm.doc.ndis_remittance_import) {
            frm.add_custom_button(__("Open NDIS Remittance Import"), function () {
                frappe.set_route("Form", "NDIS Remittance Import", frm.doc.ndis_remittance_import);
            }, __("Open"));
        }

        if (frm.doc.crm_deal) {
            frm.add_custom_button(__("Open CRM Deal"), function () {
                window.open(`/crm/deals/${frm.doc.crm_deal}`, "_blank");
            }, __("Open"));
        }
    }
});
'''.strip()
