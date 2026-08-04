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
REMITTANCE_IMPORT_PREP_LINE = "NDIS CRM Remittance Import Preparation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_remittance_import_preparation_doctypes()
	create_custom_fields_phase24()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 24 Remittance Import Preparation bridge installed successfully.")


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
		"Sales Invoice",
		"NDIS Claim Batch",
		"NDIS Claim Line",
		"NDIS Service Line",
		"CRM Form Script",
		"File",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 24 DocTypes: " + ", ".join(missing))
	print("Required Phase 24 DocTypes found.")


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
	doc = frappe.get_doc(
		{
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
		}
	)
	for field in fields:
		doc.append("fields", field)
	if not istable:
		for perm in standard_permissions():
			doc.append("permissions", perm)
	doc.insert(ignore_permissions=True)
	print(f"Created DocType: {name}")


def create_remittance_import_preparation_doctypes():
	create_remittance_import_preparation_line()
	create_remittance_import_preparation_run()


def create_remittance_import_preparation_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Remittance Source Key", "remittance_source_key", "Data", read_only=1),
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
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Service Date", "service_date", "Date", in_list_view=1),
		make_field("Claim Quantity", "claim_quantity", "Float"),
		make_field("Claim Unit", "claim_unit", "Data", default="Hour"),
		make_field("Claim Rate", "claim_rate", "Currency"),
		make_field("Claim Amount", "claim_amount", "Currency", in_list_view=1),
		make_field("Expected Paid Amount", "expected_paid_amount", "Currency", in_list_view=1),
		make_field("Expected Rejected Amount", "expected_rejected_amount", "Currency", default=0),
		make_field("NDIS Finance Snapshot", "ndis_finance_snapshot_section", "Section Break"),
		make_field("Support Item", "support_item", "Link" if doctype_exists(NDIS_SUPPORT_ITEM) else "Data", options=NDIS_SUPPORT_ITEM if doctype_exists(NDIS_SUPPORT_ITEM) else None),
		make_field("Finance Service Type", "finance_service_type", "Link" if doctype_exists(NDIS_SERVICE_TYPE) else "Data", options=NDIS_SERVICE_TYPE if doctype_exists(NDIS_SERVICE_TYPE) else None),
		make_field("NDIS Plan Budget", "plan_budget", "Link" if doctype_exists(PLAN_BUDGET) else "Data", options=PLAN_BUDGET if doctype_exists(PLAN_BUDGET) else None),
		make_field("NDIS Service Booking", "service_booking", "Link" if doctype_exists(SERVICE_BOOKING) else "Data", options=SERVICE_BOOKING if doctype_exists(SERVICE_BOOKING) else None),
		make_field("Funding Source", "funding_source", "Data"),
		make_field("Default House", "default_house", "Link" if doctype_exists(NDIS_HOUSE) else "Data", options=NDIS_HOUSE if doctype_exists(NDIS_HOUSE) else None),
		make_field("Invoice Group Key", "invoice_group_key", "Data"),
		make_field("Lodgement Snapshot", "lodgement_snapshot_section", "Section Break"),
		make_field("External Lodgement Reference", "external_lodgement_reference", "Data", in_list_view=1),
		make_field("External Batch Reference", "external_batch_reference", "Data"),
		make_field("External Line Reference", "external_line_reference", "Data"),
		make_field("Portal Status", "portal_status", "Data"),
		make_field("Expected Payment Date", "expected_payment_date", "Date"),
		make_field("Lodgement Date", "lodgement_date", "Date"),
		make_field("Lodgement Evidence File", "lodgement_evidence_file", "Attach"),
		make_field("Preparation Controls", "preparation_controls_section", "Section Break"),
		make_field("Lodgement Confirmation Source Ready", "lodgement_confirmation_source_ready", "Check", default=0),
		make_field("Finance Remittance Review Complete", "finance_remittance_review_complete", "Check", default=0),
		make_field("Remittance Mapping Review Complete", "remittance_mapping_review_complete", "Check", default=0),
		make_field("Remittance Template Authorized", "remittance_template_authorized", "Check", default=0),
		make_field("Payment Entry Authorized", "payment_entry_authorized", "Check", default=0, description="Blocked in Phase 24."),
		make_field("Write Off Authorized", "write_off_authorized", "Check", default=0, description="Blocked in Phase 24."),
		make_field("Recovery Authorized", "recovery_authorized", "Check", default=0, description="Blocked in Phase 24."),
		make_field("Remittance Hold", "remittance_hold", "Check", default=1, in_list_view=1),
		make_field("Remittance Hold Reason", "remittance_hold_reason", "Small Text"),
		make_field("Line Status", "line_status_section", "Section Break"),
		make_field("Line Ready for Remittance Import Template", "line_ready_for_remittance_import_template", "Check", default=0, in_list_view=1),
		make_field("Remittance Template Line Included", "remittance_template_line_included", "Check", default=0, read_only=1),
		make_field("Remittance Line Status", "remittance_line_status", "Select", options="Draft\nReady\nApproved\nTemplate Prepared\nImported\nMatched\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(REMITTANCE_IMPORT_PREP_LINE, fields, istable=1)


def create_remittance_import_preparation_run():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-REMIT-PREP-.YYYY.-.#####", default="NDIS-REMIT-PREP-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Remittance Import Preparation\nRemittance Import Preparation Approved\nRemittance Matching Template Prepared\nReturned to Lodgement Confirmation\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Remittance Import Preparation Run Ready", "remittance_import_preparation_run_ready", "Check", read_only=1, in_list_view=1),
		make_field("Template Format", "template_format", "Select", options="CSV Matching Template\nJSON Matching Payload", default="CSV Matching Template"),
		make_field("Remittance Template Generation Allowed", "remittance_template_generation_allowed", "Check", default=0),
		make_field("Actual Remittance Import Allowed", "actual_remittance_import_allowed", "Check", default=0, description="Blocked in Phase 24."),
		make_field("Payment Entry Creation Allowed", "payment_entry_creation_allowed", "Check", default=0, description="Blocked in Phase 24."),
		make_field("Generated Template", "generated_template_section", "Section Break"),
		make_field("Generated Template File", "generated_template_file", "Attach", read_only=1),
		make_field("Generated Template File Name", "generated_template_file_name", "Data", read_only=1),
		make_field("Generated Template File SHA256", "generated_template_file_hash", "Data", read_only=1),
		make_field("Generated Template File On", "generated_template_file_on", "Datetime", read_only=1),
		make_field("Generated Template File By", "generated_template_file_by", "Link", options="User", read_only=1),
		make_field("Generated Payload Preview", "generated_payload_preview", "Code", read_only=1),
		make_field("Summary", "summary_section", "Section Break"),
		make_field("Remittance Line Count", "remittance_line_count", "Int", read_only=1),
		make_field("Claim Batch Count", "claim_batch_count", "Int", read_only=1),
		make_field("Claim Amount Total", "claim_amount_total", "Currency", read_only=1),
		make_field("Expected Paid Amount Total", "expected_paid_amount_total", "Currency", read_only=1),
		make_field("Expected Rejected Amount Total", "expected_rejected_amount_total", "Currency", read_only=1),
		make_field("Remittance Ready Count", "remittance_ready_count", "Int", read_only=1),
		make_field("Remittance Template Line Count", "remittance_template_line_count", "Int", read_only=1),
		make_field("Remittance Hold Count", "remittance_hold_count", "Int", read_only=1),
		make_field("Missing Lodgement Reference Count", "missing_lodgement_reference_count", "Int", read_only=1),
		make_field("Blocked Payment Authorization Count", "blocked_payment_authorization_count", "Int", read_only=1),
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
		make_field("NDIS CRM Claim Lodgement Confirmation Run", "claim_lodgement_confirmation_run", "Link", options=CLAIM_LODGEMENT_CONFIRMATION_RUN, reqd=1, in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
		make_field("NDIS Financial Profile", "ndis_financial_profile", "Link" if doctype_exists(FINANCE_PROFILE) else "Data", options=FINANCE_PROFILE if doctype_exists(FINANCE_PROFILE) else None),
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Company", "company", "Link", options="Company"),
		make_field("Claim / Remittance Window", "claim_remittance_window_section", "Section Break"),
		make_field("Claim Period Start", "claim_period_start", "Date"),
		make_field("Claim Period End", "claim_period_end", "Date"),
		make_field("Lodgement Date", "lodgement_date", "Date"),
		make_field("Expected Remittance Date", "expected_remittance_date", "Date"),
		make_field("External Reference Snapshot", "external_reference_section", "Section Break"),
		make_field("External Lodgement Reference", "external_lodgement_reference", "Data"),
		make_field("External Batch Reference", "external_batch_reference", "Data"),
		make_field("Generated Export File", "generated_export_file", "Attach", read_only=1),
		make_field("Generated Export File SHA256", "generated_export_file_hash", "Data", read_only=1),
		make_field("Lodgement Evidence File", "lodgement_evidence_file", "Attach"),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Remittance Owner", "remittance_owner", "Link", options="User", in_list_view=1),
		make_field("Claim Lodgement Owner", "claim_lodgement_owner", "Link", options="User"),
		make_field("Claim Export Owner", "claim_export_owner", "Link", options="User"),
		make_field("Claim Batch Owner", "claim_batch_owner", "Link", options="User"),
		make_field("Claim Owner", "claim_owner", "Link", options="User"),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Remittance Lines", "remittance_lines_section", "Section Break"),
		make_field("Remittance Lines", "remittance_lines", "Table", options=REMITTANCE_IMPORT_PREP_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Remittance Preparation Notes", "remittance_preparation_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(REMITTANCE_IMPORT_PREP_RUN, fields, autoname="naming_series:", title_field="participant_name")


def create_custom_fields_phase24():
	deal_fields = [
		{"fieldname": "remittance_import_preparation_section", "label": "NDIS Remittance Import Preparation Run", "fieldtype": "Section Break", "insert_after": "claim_lodgement_confirmation_ready"},
		{"fieldname": "ndis_remittance_import_preparation_run_required", "label": "Remittance Import Preparation Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "remittance_import_preparation_section", "description": "Optional guard only. Remittance preparation normally happens after claim lodgement confirmation."},
		{"fieldname": "ndis_remittance_import_preparation_run", "label": "NDIS CRM Remittance Import Preparation Run", "fieldtype": "Link", "options": REMITTANCE_IMPORT_PREP_RUN, "read_only": 1, "insert_after": "ndis_remittance_import_preparation_run_required"},
		{"fieldname": "remittance_import_preparation_status", "label": "Remittance Import Preparation Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_remittance_import_preparation_run"},
		{"fieldname": "remittance_import_preparation_ready", "label": "Remittance Import Preparation Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "remittance_import_preparation_status"},
	]
	shared_fields = [
		{"fieldname": "remittance_import_preparation_section", "label": "NDIS Remittance Import Preparation Run", "fieldtype": "Section Break", "insert_after": "claim_lodgement_confirmation_ready"},
		{"fieldname": "ndis_remittance_import_preparation_run", "label": "NDIS CRM Remittance Import Preparation Run", "fieldtype": "Link", "options": REMITTANCE_IMPORT_PREP_RUN, "read_only": 1, "insert_after": "remittance_import_preparation_section"},
		{"fieldname": "remittance_import_preparation_status", "label": "Remittance Import Preparation Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_remittance_import_preparation_run"},
		{"fieldname": "remittance_import_preparation_ready", "label": "Remittance Import Preparation Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "remittance_import_preparation_status"},
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
		INTAKE: shared_fields,
	}
	if doctype_exists(ATTENDANCE_DRAFT):
		custom_fields[ATTENDANCE_DRAFT] = shared_fields
	create_custom_fields(custom_fields, update=True)
	print("Created / updated Phase 24 remittance import preparation custom fields.")


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
		upsert_doc("Client Script", "NDIS CRM Claim Lodgement Confirmation Run Actions", {"dt": CLAIM_LODGEMENT_CONFIRMATION_RUN, "view": "Form", "enabled": 1, "script": _lodgement_script()})
		upsert_doc("Client Script", "NDIS CRM Remittance Import Preparation Run Actions", {"dt": REMITTANCE_IMPORT_PREP_RUN, "view": "Form", "enabled": 1, "script": _run_script()})


def _deal_script():
	try:
		from ndis_crm.setup.phase23_claim_lodgement_confirmation import _deal_script as previous_script

		script = previous_script()
	except Exception:
		script = "function setupForm({ doc, call, createToast }) {\n  return { actions: [] }\n}"
	insert = r'''
      {
        label: "Create Remittance Import Preparation Run",
        onClick: () => {
          call("ndis_crm.phase24_remittance_import_preparation.create_remittance_import_preparation_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Remittance Import Preparation Run Created" : "Existing Remittance Preparation Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-remittance-import-preparation-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Remittance Import Preparation Run",
        onClick: () => {
          if (doc.ndis_remittance_import_preparation_run) {
            window.open(`/app/ndis-crm-remittance-import-preparation-run/${doc.ndis_remittance_import_preparation_run}`, "_blank")
          } else {
            createToast({ title: "No Remittance Import Preparation Run linked yet", icon: "info" })
          }
        }
      }
'''.rstrip()
	return script.replace("\n    ]", ",\n" + insert + "\n    ]", 1)


def _lodgement_script():
	try:
		from ndis_crm.setup.phase23_claim_lodgement_confirmation import _run_script as previous_script

		script = previous_script()
	except Exception:
		script = 'frappe.ui.form.on("NDIS CRM Claim Lodgement Confirmation Run", { refresh(frm) { if (frm.is_new()) { return; } } });'
	insert = r'''

        frm.add_custom_button(__("Create Remittance Import Preparation Run"), function () {
            frappe.call({
                method: "ndis_crm.phase24_remittance_import_preparation.create_remittance_import_preparation_run_from_lodgement_confirmation_run",
                args: { claim_lodgement_confirmation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating remittance import preparation run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Remittance Import Preparation Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Remittance Import Preparation Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_remittance_import_preparation_run) {
            frm.add_custom_button(__("Open Remittance Import Preparation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Remittance Import Preparation Run", frm.doc.ndis_remittance_import_preparation_run);
            }, __("Open"));
        }
'''
	return script.replace("\n    }\n});", insert + "\n    }\n});", 1)


def _run_script():
	return r'''
frappe.ui.form.on("NDIS CRM Remittance Import Preparation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Remittance Preparation Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase24_remittance_import_preparation.generate_remittance_import_preparation_lines",
                args: { remittance_import_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating remittance preparation lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Remittance preparation lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Remittance Preparation Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase24_remittance_import_preparation.validate_remittance_import_preparation_readiness",
                args: { remittance_import_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating remittance preparation readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Remittance preparation readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Remittance Preparation"), function () {
            frappe.call({
                method: "ndis_crm.phase24_remittance_import_preparation.mark_ready_for_remittance_import_preparation",
                args: { remittance_import_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for remittance preparation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for remittance preparation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Remittance Preparation Run"), function () {
            frappe.call({
                method: "ndis_crm.phase24_remittance_import_preparation.approve_remittance_import_preparation_run",
                args: { remittance_import_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving remittance preparation run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Remittance Import Preparation Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Generate Remittance Matching Template"), function () {
            frappe.confirm(
                __("This will generate a private remittance matching template/payload only. It will not import remittance, create Payment Entry, journal, write-off, recovery, or manual GL."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase24_remittance_import_preparation.generate_remittance_matching_template",
                        args: { remittance_import_preparation_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Generating remittance matching template...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Remittance matching template generated"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.claim_lodgement_confirmation_run) {
            frm.add_custom_button(__("Open Lodgement Confirmation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Lodgement Confirmation Run", frm.doc.claim_lodgement_confirmation_run);
            }, __("Open"));
        }

        if (frm.doc.generated_template_file) {
            frm.add_custom_button(__("Open Generated Template"), function () {
                window.open(frm.doc.generated_template_file, "_blank");
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
