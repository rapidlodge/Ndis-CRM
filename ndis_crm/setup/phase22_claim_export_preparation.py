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
CLAIM_EXPORT_PREP_LINE = "NDIS CRM Claim Export Preparation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_export_preparation_doctypes()
	create_custom_fields_phase22()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 22 Claim Export Preparation bridge installed successfully.")


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
		"Sales Invoice",
		"NDIS Claim Batch",
		"NDIS Claim Line",
		"NDIS Service Line",
		"CRM Form Script",
		"File",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 22 DocTypes: " + ", ".join(missing))
	print("Required Phase 22 DocTypes found.")


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


def create_export_preparation_doctypes():
	create_export_preparation_line()
	create_export_preparation_run()


def create_export_preparation_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Export Source Key", "export_source_key", "Data", read_only=1),
		make_field("NDIS Claim Batch", "ndis_claim_batch", "Link", options="NDIS Claim Batch", in_list_view=1),
		make_field("NDIS Claim Line", "ndis_claim_line", "Link", options="NDIS Claim Line"),
		make_field("Claim Batch Docstatus", "claim_batch_docstatus", "Int", read_only=1),
		make_field("Claim Line Docstatus", "claim_line_docstatus", "Int", read_only=1),
		make_field("Claim Batch Status", "claim_batch_status", "Data", read_only=1),
		make_field("Claim Line Status", "claim_line_status", "Data", read_only=1),
		make_field("Sales Invoice Snapshot", "sales_invoice_snapshot_section", "Section Break"),
		make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", in_list_view=1),
		make_field("Sales Invoice Docstatus", "sales_invoice_docstatus", "Int", read_only=1),
		make_field("Sales Invoice Status", "sales_invoice_status", "Data", read_only=1),
		make_field("Service Snapshot", "service_snapshot_section", "Section Break"),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Service Date", "service_date", "Date", in_list_view=1),
		make_field("Claim Quantity", "claim_quantity", "Float"),
		make_field("Claim Unit", "claim_unit", "Data", default="Hour"),
		make_field("Claim Rate", "claim_rate", "Currency"),
		make_field("Claim Amount", "claim_amount", "Currency", in_list_view=1),
		make_field("NDIS Finance Snapshot", "ndis_finance_snapshot_section", "Section Break"),
		make_field("Support Item", "support_item", "Link" if doctype_exists(NDIS_SUPPORT_ITEM) else "Data", options=NDIS_SUPPORT_ITEM if doctype_exists(NDIS_SUPPORT_ITEM) else None),
		make_field("Finance Service Type", "finance_service_type", "Link" if doctype_exists(NDIS_SERVICE_TYPE) else "Data", options=NDIS_SERVICE_TYPE if doctype_exists(NDIS_SERVICE_TYPE) else None),
		make_field("NDIS Plan Budget", "plan_budget", "Link" if doctype_exists(PLAN_BUDGET) else "Data", options=PLAN_BUDGET if doctype_exists(PLAN_BUDGET) else None),
		make_field("NDIS Service Booking", "service_booking", "Link" if doctype_exists(SERVICE_BOOKING) else "Data", options=SERVICE_BOOKING if doctype_exists(SERVICE_BOOKING) else None),
		make_field("Funding Source", "funding_source", "Data"),
		make_field("Default House", "default_house", "Link" if doctype_exists(NDIS_HOUSE) else "Data", options=NDIS_HOUSE if doctype_exists(NDIS_HOUSE) else None),
		make_field("Invoice Group Key", "invoice_group_key", "Data"),
		make_field("Export Controls", "export_controls_section", "Section Break"),
		make_field("Claim Batch Export Source Ready", "claim_batch_export_source_ready", "Check", default=0),
		make_field("Export Schema Review Complete", "export_schema_review_complete", "Check", default=0),
		make_field("Export File Authorized", "export_file_authorized", "Check", default=0),
		make_field("Portal Submission Authorized", "portal_submission_authorized", "Check", default=0, description="Blocked in Phase 22."),
		make_field("Claim Export Ready", "claim_export_ready", "Check", default=0),
		make_field("Claim Submission Ready", "claim_submission_ready", "Check", default=0),
		make_field("Export Hold", "export_hold", "Check", default=1, in_list_view=1),
		make_field("Export Hold Reason", "export_hold_reason", "Small Text"),
		make_field("Line Status", "line_status_section", "Section Break"),
		make_field("Line Ready for Export File", "line_ready_for_export_file", "Check", default=0, in_list_view=1),
		make_field("Export File Line Included", "export_file_line_included", "Check", default=0, read_only=1),
		make_field("Export Line Status", "export_line_status", "Select", options="Draft\nReady\nApproved\nExport File Prepared\nExported\nSubmitted\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(CLAIM_EXPORT_PREP_LINE, fields, istable=1)


def create_export_preparation_run():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-CLAIM-EXPORT-PREP-.YYYY.-.#####", default="NDIS-CLAIM-EXPORT-PREP-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Export File Preparation\nExport Preparation Approved\nExport File Prepared\nReturned to Claim Batch Submission Run\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Claim Export Preparation Run Ready", "claim_export_preparation_run_ready", "Check", read_only=1, in_list_view=1),
		make_field("Export Format", "export_format", "Select", options="CSV Review File\nJSON Review Payload", default="CSV Review File"),
		make_field("Export File Generation Allowed", "export_file_generation_allowed", "Check", default=0),
		make_field("Portal Lodgement Allowed", "portal_lodgement_allowed", "Check", default=0, description="Blocked in Phase 22."),
		make_field("Generated File", "generated_file_section", "Section Break"),
		make_field("Generated File", "generated_file", "Attach", read_only=1),
		make_field("Generated File Name", "generated_file_name", "Data", read_only=1),
		make_field("Generated File SHA256", "generated_file_hash", "Data", read_only=1),
		make_field("Generated File On", "generated_file_on", "Datetime", read_only=1),
		make_field("Generated File By", "generated_file_by", "Link", options="User", read_only=1),
		make_field("Generated Payload Preview", "generated_payload_preview", "Code", read_only=1),
		make_field("Summary", "summary_section", "Section Break"),
		make_field("Export Line Count", "export_line_count", "Int", read_only=1),
		make_field("Claim Batch Count", "claim_batch_count", "Int", read_only=1),
		make_field("Claim Amount Total", "claim_amount_total", "Currency", read_only=1),
		make_field("Export Ready Count", "export_ready_count", "Int", read_only=1),
		make_field("Export File Line Count", "export_file_line_count", "Int", read_only=1),
		make_field("Export Hold Count", "export_hold_count", "Int", read_only=1),
		make_field("Missing Claim Batch Count", "missing_claim_batch_count", "Int", read_only=1),
		make_field("Missing Sales Invoice Count", "missing_sales_invoice_count", "Int", read_only=1),
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
		make_field("NDIS CRM Claim Batch Submission Run", "claim_batch_submission_run", "Link", options=CLAIM_BATCH_SUBMISSION_RUN, reqd=1, in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
		make_field("NDIS Financial Profile", "ndis_financial_profile", "Link" if doctype_exists(FINANCE_PROFILE) else "Data", options=FINANCE_PROFILE if doctype_exists(FINANCE_PROFILE) else None),
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Company", "company", "Link", options="Company"),
		make_field("Claim Window", "claim_window_section", "Section Break"),
		make_field("Claim Period Start", "claim_period_start", "Date"),
		make_field("Claim Period End", "claim_period_end", "Date"),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Claim Export Owner", "claim_export_owner", "Link", options="User", in_list_view=1),
		make_field("Claim Batch Submission Owner", "claim_batch_submission_owner", "Link", options="User"),
		make_field("Claim Batch Owner", "claim_batch_owner", "Link", options="User"),
		make_field("Claim Owner", "claim_owner", "Link", options="User"),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Export Lines", "export_lines_section", "Section Break"),
		make_field("Export Lines", "export_lines", "Table", options=CLAIM_EXPORT_PREP_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Export Preparation Notes", "export_preparation_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(CLAIM_EXPORT_PREP_RUN, fields, autoname="naming_series:", title_field="participant_name")


def _link_fields(insert_after):
	return [
		{"fieldname": "claim_export_preparation_section", "label": "NDIS Claim Export Preparation Run", "fieldtype": "Section Break", "insert_after": insert_after},
		{"fieldname": "ndis_claim_export_preparation_run", "label": "NDIS CRM Claim Export Preparation Run", "fieldtype": "Link", "options": CLAIM_EXPORT_PREP_RUN, "read_only": 1, "insert_after": "claim_export_preparation_section"},
		{"fieldname": "claim_export_preparation_status", "label": "Claim Export Preparation Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_claim_export_preparation_run"},
		{"fieldname": "claim_export_preparation_ready", "label": "Claim Export Preparation Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "claim_export_preparation_status"},
	]


def create_custom_fields_phase22():
	deal_fields = [
		{"fieldname": "claim_export_preparation_section", "label": "NDIS Claim Export Preparation Run", "fieldtype": "Section Break", "insert_after": "claim_batch_submission_ready"},
		{"fieldname": "ndis_claim_export_preparation_run_required", "label": "Claim Export Preparation Run Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "claim_export_preparation_section", "description": "Optional guard only. Claim export preparation normally happens after claim batch export readiness."},
		{"fieldname": "ndis_claim_export_preparation_run", "label": "NDIS CRM Claim Export Preparation Run", "fieldtype": "Link", "options": CLAIM_EXPORT_PREP_RUN, "read_only": 1, "insert_after": "ndis_claim_export_preparation_run_required"},
		{"fieldname": "claim_export_preparation_status", "label": "Claim Export Preparation Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_claim_export_preparation_run"},
		{"fieldname": "claim_export_preparation_ready", "label": "Claim Export Preparation Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "claim_export_preparation_status"},
	]
	custom_fields = {
		CRM_DEAL: deal_fields,
		HANDOVER: _link_fields("claim_batch_submission_ready"),
		FINANCE_ONBOARDING: _link_fields("claim_batch_submission_ready"),
		OPERATIONS_SETUP: _link_fields("claim_batch_submission_ready"),
		SCHEDULE_DRAFT: _link_fields("claim_batch_submission_ready"),
		ROSTER_REQUEST: _link_fields("claim_batch_submission_ready"),
		SERVICE_FILE: _link_fields("claim_batch_submission_ready"),
		SESSION_DRAFT: _link_fields("claim_batch_submission_ready"),
		EVIDENCE_REVIEW: _link_fields("claim_batch_submission_ready"),
		DOWNSTREAM_PREPARATION: _link_fields("claim_batch_submission_ready"),
		BILLING_DRAFT: _link_fields("claim_batch_submission_ready"),
		CLAIM_DRAFT: _link_fields("claim_batch_submission_ready"),
		INVOICE_DRAFT: _link_fields("claim_batch_submission_ready"),
		SALES_INVOICE_DRAFT_RUN: _link_fields("claim_batch_submission_ready"),
		SALES_INVOICE_SUBMISSION_RUN: _link_fields("claim_batch_submission_ready"),
		CLAIM_BATCH_DRAFT_RUN: _link_fields("claim_batch_submission_ready"),
		CLAIM_BATCH_SUBMISSION_RUN: _link_fields("claim_batch_submission_ready"),
		INTAKE: _link_fields("claim_batch_submission_ready"),
	}
	if doctype_exists(ATTENDANCE_DRAFT):
		custom_fields[ATTENDANCE_DRAFT] = _link_fields("claim_batch_submission_ready")
	frappe.flags.in_install = True
	try:
		create_custom_fields(custom_fields, update=True)
	finally:
		frappe.flags.in_install = False
	print("Created / updated Phase 22 claim export preparation custom fields.")


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
		upsert_doc("Client Script", "NDIS CRM Claim Batch Submission Run Actions", {"dt": CLAIM_BATCH_SUBMISSION_RUN, "view": "Form", "enabled": 1, "script": _submission_script()})
		upsert_doc("Client Script", "NDIS CRM Claim Export Preparation Run Actions", {"dt": CLAIM_EXPORT_PREP_RUN, "view": "Form", "enabled": 1, "script": _run_script()})


def _deal_script():
	try:
		from ndis_crm.setup.phase21_claim_batch_submission import _deal_script as previous_script

		script = previous_script()
	except Exception:
		script = "function setupForm({ doc, call, createToast }) {\n  return { actions: [] }\n}"
	insert = r'''
      {
        label: "Create Claim Export Preparation Run",
        onClick: () => {
          call("ndis_crm.phase22_claim_export_preparation.create_claim_export_preparation_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Claim Export Preparation Run Created" : "Existing Export Preparation Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-claim-export-preparation-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Claim Export Preparation Run",
        onClick: () => {
          if (doc.ndis_claim_export_preparation_run) {
            window.open(`/app/ndis-crm-claim-export-preparation-run/${doc.ndis_claim_export_preparation_run}`, "_blank")
          } else {
            createToast({ title: "No Claim Export Preparation Run linked yet", icon: "info" })
          }
        }
      }
'''.rstrip()
	return script.replace("\n    ]", ",\n" + insert + "\n    ]", 1)


def _submission_script():
	try:
		from ndis_crm.setup.phase21_claim_batch_submission import _run_script as previous_script

		script = previous_script()
	except Exception:
		script = 'frappe.ui.form.on("NDIS CRM Claim Batch Submission Run", { refresh(frm) { if (frm.is_new()) { return; } } });'
	insert = r'''

        frm.add_custom_button(__("Create Claim Export Preparation Run"), function () {
            frappe.call({
                method: "ndis_crm.phase22_claim_export_preparation.create_claim_export_preparation_run_from_submission_run",
                args: { claim_batch_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating claim export preparation run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Claim Export Preparation Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Claim Export Preparation Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_claim_export_preparation_run) {
            frm.add_custom_button(__("Open Claim Export Preparation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Export Preparation Run", frm.doc.ndis_claim_export_preparation_run);
            }, __("Open"));
        }
'''
	return script.replace("\n    }\n});", insert + "\n    }\n});", 1)


def _run_script():
	return r'''
frappe.ui.form.on("NDIS CRM Claim Export Preparation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Export Preparation Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase22_claim_export_preparation.generate_claim_export_preparation_lines",
                args: { claim_export_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating export preparation lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Export preparation lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Export Preparation Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase22_claim_export_preparation.validate_claim_export_preparation_readiness",
                args: { claim_export_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating export preparation readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Export preparation readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Export File Preparation"), function () {
            frappe.call({
                method: "ndis_crm.phase22_claim_export_preparation.mark_ready_for_export_file_preparation",
                args: { claim_export_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for export file preparation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for export file preparation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Export Preparation Run"), function () {
            frappe.call({
                method: "ndis_crm.phase22_claim_export_preparation.approve_claim_export_preparation_run",
                args: { claim_export_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving export preparation run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Export Preparation Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Generate Claim Export Review File"), function () {
            frappe.confirm(
                __("This will generate a private claim export review file/payload only. It will not lodge claims, submit to a portal, create payments, journals, remittance, write-off, recovery, or manual GL."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase22_claim_export_preparation.generate_claim_export_file",
                        args: { claim_export_preparation_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Generating claim export review file...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Claim export review file generated"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.claim_batch_submission_run) {
            frm.add_custom_button(__("Open Claim Batch Submission Run"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Batch Submission Run", frm.doc.claim_batch_submission_run);
            }, __("Open"));
        }

        if (frm.doc.generated_file) {
            frm.add_custom_button(__("Open Generated File"), function () {
                window.open(frm.doc.generated_file, "_blank");
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
