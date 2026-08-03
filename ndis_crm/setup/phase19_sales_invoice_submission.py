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
SALES_INVOICE_SUBMISSION_LINE = "NDIS CRM Sales Invoice Submission Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_submission_doctypes()
	create_custom_fields_phase19()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 19 Sales Invoice submission gate installed successfully.")


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
		INVOICE_DRAFT,
		SALES_INVOICE_DRAFT_RUN,
		"Sales Invoice",
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 19 DocTypes: " + ", ".join(missing))
	print("Required Phase 19 DocTypes found.")


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


def create_submission_doctypes():
	create_submission_line()
	create_submission_run()


def create_submission_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Sales Invoice Source Key", "sales_invoice_source_key", "Data", read_only=1),
		make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", in_list_view=1),
		make_field("Sales Invoice Docstatus", "sales_invoice_docstatus", "Int", read_only=1),
		make_field("Sales Invoice Status", "sales_invoice_status", "Data", read_only=1),
		make_field("Customer", "customer", "Link", options="Customer", read_only=1),
		make_field("Company", "company", "Link", options="Company", read_only=1),
		make_field("Posting Date", "posting_date", "Date", read_only=1),
		make_field("Due Date", "due_date", "Date", read_only=1),
		make_field("Sales Invoice Total", "sales_invoice_total", "Currency", read_only=1),
		make_field("Service Snapshot", "service_snapshot_section", "Section Break"),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Invoice Group Key", "invoice_group_key", "Data"),
		make_field("Invoice Date", "invoice_date", "Date"),
		make_field("Invoice Quantity", "invoice_quantity", "Float"),
		make_field("Invoice Rate", "invoice_rate", "Currency"),
		make_field("Invoice Amount", "invoice_amount", "Currency"),
		make_field("ERPNext Mapping Snapshot", "erpnext_mapping_section", "Section Break"),
		make_field("ERPNext Item Code", "erp_item_code", "Link", options="Item"),
		make_field("Income Account", "income_account", "Link", options="Account"),
		make_field("Cost Center", "cost_center", "Link", options="Cost Center"),
		make_field("NDIS Finance Snapshot", "ndis_finance_section", "Section Break"),
		make_field("Support Item", "support_item", "Link" if doctype_exists(NDIS_SUPPORT_ITEM) else "Data", options=NDIS_SUPPORT_ITEM if doctype_exists(NDIS_SUPPORT_ITEM) else None),
		make_field("Finance Service Type", "finance_service_type", "Link" if doctype_exists(NDIS_SERVICE_TYPE) else "Data", options=NDIS_SERVICE_TYPE if doctype_exists(NDIS_SERVICE_TYPE) else None),
	]
	if doctype_exists(PLAN_BUDGET):
		fields.append(make_field("NDIS Plan Budget", "plan_budget", "Link", options=PLAN_BUDGET))
	if doctype_exists(SERVICE_BOOKING):
		fields.append(make_field("NDIS Service Booking", "service_booking", "Link", options=SERVICE_BOOKING))
	fields += [
		make_field("Funding Source", "funding_source", "Data"),
		make_field("Default House", "default_house", "Link" if doctype_exists(NDIS_HOUSE) else "Data", options=NDIS_HOUSE if doctype_exists(NDIS_HOUSE) else None),
		make_field("Submission Controls", "submission_controls_section", "Section Break"),
		make_field("Billing Preparation Ready", "billing_preparation_ready", "Check", default=0),
		make_field("Submission Precheck Ready", "submission_precheck_ready", "Check", default=0, in_list_view=1),
		make_field("Finance Submission Review Complete", "finance_submission_review_complete", "Check", default=0),
		make_field("Submit Authorized", "submit_authorized", "Check", default=0, in_list_view=1),
		make_field("Submission Hold", "submission_hold", "Check", default=1, in_list_view=1),
		make_field("Submission Hold Reason", "submission_hold_reason", "Small Text"),
		make_field("Line Ready for Sales Invoice Submit", "line_ready_for_sales_invoice_submit", "Check", default=0, in_list_view=1),
		make_field("Submission Status", "submission_status", "Select", options="Draft\nReady\nApproved\nSubmitted\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Submitted By", "submitted_by", "Link", options="User", read_only=1),
		make_field("Submitted On", "submitted_on", "Datetime", read_only=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(name=SALES_INVOICE_SUBMISSION_LINE, fields=fields, istable=1)


def create_submission_run():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-SI-SUB-RUN-.YYYY.-.#####", default="NDIS-SI-SUB-RUN-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Sales Invoice Submission\nSales Invoice Submission Run Approved\nSales Invoices Submitted\nReturned to Sales Invoice Draft Run\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Sales Invoice Submission Run Ready", "sales_invoice_submission_run_ready", "Check", read_only=1, in_list_view=1),
		make_field("Submission Allowed", "submission_allowed", "Check", default=0, description="Must be ticked manually after approval before Sales Invoices are submitted."),
		make_field("Submission Summary", "submission_summary_section", "Section Break"),
		make_field("Submission Line Count", "submission_line_count", "Int", read_only=1),
		make_field("Sales Invoice Amount Total", "sales_invoice_amount_total", "Currency", read_only=1),
		make_field("Draft Sales Invoice Count", "draft_sales_invoice_count", "Int", read_only=1),
		make_field("Submitted Sales Invoice Count", "submitted_sales_invoice_count", "Int", read_only=1),
		make_field("Sales Invoice Submit Ready Count", "sales_invoice_submit_ready_count", "Int", read_only=1),
		make_field("Sales Invoice Submission Hold Count", "sales_invoice_submission_hold_count", "Int", read_only=1),
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
		make_field("NDIS CRM Claim Draft", "claim_draft", "Link" if doctype_exists(CLAIM_DRAFT) else "Data", options=CLAIM_DRAFT if doctype_exists(CLAIM_DRAFT) else None),
		make_field("NDIS CRM Invoice Draft", "invoice_draft", "Link", options=INVOICE_DRAFT),
		make_field("NDIS CRM Sales Invoice Draft Run", "sales_invoice_draft_run", "Link", options=SALES_INVOICE_DRAFT_RUN, reqd=1, in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
		make_field("NDIS Financial Profile", "ndis_financial_profile", "Link" if doctype_exists(FINANCE_PROFILE) else "Data", options=FINANCE_PROFILE if doctype_exists(FINANCE_PROFILE) else None),
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Company", "company", "Link", options="Company"),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Submission Owner", "submission_owner", "Link", options="User", in_list_view=1),
		make_field("Sales Invoice Owner", "sales_invoice_owner", "Link", options="User"),
		make_field("Invoice Owner", "invoice_owner", "Link", options="User"),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Submission Lines", "submission_lines_section", "Section Break"),
		make_field("Submission Lines", "submission_lines", "Table", options=SALES_INVOICE_SUBMISSION_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Submission Notes", "submission_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(
		name=SALES_INVOICE_SUBMISSION_RUN,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def _link_fields(insert_after):
	return [
		{"fieldname": "sales_invoice_submission_section", "label": "NDIS Sales Invoice Submission Run", "fieldtype": "Section Break", "insert_after": insert_after},
		{"fieldname": "ndis_sales_invoice_submission_run", "label": "NDIS CRM Sales Invoice Submission Run", "fieldtype": "Link", "options": SALES_INVOICE_SUBMISSION_RUN, "read_only": 1, "insert_after": "sales_invoice_submission_section"},
		{"fieldname": "sales_invoice_submission_status", "label": "Sales Invoice Submission Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_sales_invoice_submission_run"},
		{"fieldname": "sales_invoice_submission_ready", "label": "Sales Invoice Submission Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "sales_invoice_submission_status"},
	]


def create_custom_fields_phase19():
	deal_fields = [
		{"fieldname": "sales_invoice_submission_section", "label": "NDIS Sales Invoice Submission Run", "fieldtype": "Section Break", "insert_after": "sales_invoice_draft_run_ready"},
		{
			"fieldname": "ndis_sales_invoice_submission_run_required",
			"label": "Sales Invoice Submission Run Required Before Active Deal",
			"fieldtype": "Check",
			"default": 0,
			"insert_after": "sales_invoice_submission_section",
			"description": "Optional guard only. Normally submission happens after participant activation and draft invoice creation.",
		},
		{"fieldname": "ndis_sales_invoice_submission_run", "label": "NDIS CRM Sales Invoice Submission Run", "fieldtype": "Link", "options": SALES_INVOICE_SUBMISSION_RUN, "read_only": 1, "insert_after": "ndis_sales_invoice_submission_run_required"},
		{"fieldname": "sales_invoice_submission_status", "label": "Sales Invoice Submission Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_sales_invoice_submission_run"},
		{"fieldname": "sales_invoice_submission_ready", "label": "Sales Invoice Submission Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "sales_invoice_submission_status"},
	]
	shared_fields = _link_fields("sales_invoice_draft_run_ready")
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
		INVOICE_DRAFT: shared_fields,
		SALES_INVOICE_DRAFT_RUN: shared_fields,
		INTAKE: shared_fields,
	}
	if doctype_exists(ATTENDANCE_DRAFT):
		custom_fields[ATTENDANCE_DRAFT] = shared_fields
	if doctype_exists(CLAIM_DRAFT):
		custom_fields[CLAIM_DRAFT] = shared_fields
	was_in_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		create_custom_fields(custom_fields, update=True)
	finally:
		frappe.flags.in_install = was_in_install
	print("Created / updated Phase 19 Sales Invoice submission custom fields.")


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
		upsert_doc("Client Script", "NDIS CRM Sales Invoice Draft Run Actions", {"dt": SALES_INVOICE_DRAFT_RUN, "view": "Form", "enabled": 1, "script": _draft_run_script()})
		upsert_doc("Client Script", "NDIS CRM Sales Invoice Submission Run Actions", {"dt": SALES_INVOICE_SUBMISSION_RUN, "view": "Form", "enabled": 1, "script": _submission_script()})


def _deal_script():
	from ndis_crm.setup.phase18_sales_invoice_draft import _deal_script as phase18_deal_script

	script = phase18_deal_script()
	insert = r''',
      {
        label: "Create Sales Invoice Submission Run",
        onClick: () => {
          call("ndis_crm.phase19_sales_invoice_submission.create_sales_invoice_submission_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Sales Invoice Submission Run Created" : "Existing Submission Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-sales-invoice-submission-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Sales Invoice Submission Run",
        onClick: () => {
          if (doc.ndis_sales_invoice_submission_run) {
            window.open(`/app/ndis-crm-sales-invoice-submission-run/${doc.ndis_sales_invoice_submission_run}`, "_blank")
          } else {
            createToast({ title: "No Sales Invoice Submission Run linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _draft_run_script():
	from ndis_crm.setup.phase18_sales_invoice_draft import _sales_invoice_run_script as phase18_run_script

	script = phase18_run_script()
	insert = r'''

        frm.add_custom_button(__("Create Sales Invoice Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase19_sales_invoice_submission.create_sales_invoice_submission_run_from_draft_run",
                args: { sales_invoice_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating Sales Invoice Submission Run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Sales Invoice Submission Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Sales Invoice Submission Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_sales_invoice_submission_run) {
            frm.add_custom_button(__("Open Sales Invoice Submission Run"), function () {
                frappe.set_route("Form", "NDIS CRM Sales Invoice Submission Run", frm.doc.ndis_sales_invoice_submission_run);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.invoice_draft)", insert + "\n        if (frm.doc.invoice_draft)")


def _submission_script():
	return r'''
frappe.ui.form.on("NDIS CRM Sales Invoice Submission Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Submission Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase19_sales_invoice_submission.generate_sales_invoice_submission_lines",
                args: { sales_invoice_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating submission lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Submission Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase19_sales_invoice_submission.validate_sales_invoice_submission_readiness",
                args: { sales_invoice_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating submission readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Submission"), function () {
            frappe.call({
                method: "ndis_crm.phase19_sales_invoice_submission.mark_ready_for_sales_invoice_submission",
                args: { sales_invoice_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for submission...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for submission"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase19_sales_invoice_submission.approve_sales_invoice_submission_run",
                args: { sales_invoice_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving submission run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Submit Sales Invoices"), function () {
            frappe.confirm(
                __("This will submit ERPNext Sales Invoices. ERPNext may create normal Sales Invoice accounting entries. This action will not create Payment Entries, Journal Entries, manual GL Entries, or Claim Batches."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase19_sales_invoice_submission.submit_sales_invoices",
                        args: { sales_invoice_submission_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Submitting Sales Invoices...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Sales Invoices submitted"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.sales_invoice_draft_run) {
            frm.add_custom_button(__("Open Sales Invoice Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Sales Invoice Draft Run", frm.doc.sales_invoice_draft_run);
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
