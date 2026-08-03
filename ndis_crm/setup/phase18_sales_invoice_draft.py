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
SALES_INVOICE_DRAFT_LINE = "NDIS CRM Sales Invoice Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_sales_invoice_draft_doctypes()
	create_custom_fields_phase18()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 18 Sales Invoice draft bridge installed successfully.")


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
		"Sales Invoice",
		"Sales Invoice Item",
		"Item",
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 18 DocTypes: " + ", ".join(missing))
	print("Required Phase 18 DocTypes found.")


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
		{"role": "NDIS Service Manager", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
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


def create_sales_invoice_draft_doctypes():
	create_sales_invoice_draft_line()
	create_sales_invoice_draft_run()


def create_sales_invoice_draft_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Invoice Source Key", "invoice_source_key", "Data", read_only=1),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Invoice Grouping", "invoice_grouping_section", "Section Break"),
		make_field("Invoice Group Key", "invoice_group_key", "Data", in_list_view=1),
		make_field("Proposed Invoice Reference", "proposed_invoice_reference", "Data"),
		make_field("Invoice Source", "invoice_source_section", "Section Break"),
		make_field("Invoice Date", "invoice_date", "Date", reqd=1, in_list_view=1),
		make_field("Billable Date", "billable_date", "Date"),
		make_field("Session Date", "session_date", "Date"),
		make_field("Actual Start Time", "actual_start_time", "Time"),
		make_field("Actual End Time", "actual_end_time", "Time"),
		make_field("Delivered Hours", "delivered_hours", "Float"),
		make_field("Invoice Quantity", "invoice_quantity", "Float", reqd=1, in_list_view=1),
		make_field("Invoice Unit", "invoice_unit", "Data", default="Hour"),
		make_field("Invoice Rate", "invoice_rate", "Currency", reqd=1, in_list_view=1),
		make_field("Invoice Amount", "invoice_amount", "Currency", reqd=1, in_list_view=1),
		make_field("GST Treatment", "gst_treatment", "Data"),
		make_field("Rate Source", "rate_source", "Data"),
		make_field("ERPNext Sales Invoice Mapping", "erpnext_mapping_section", "Section Break"),
		make_field("ERPNext Item Code", "erp_item_code", "Link", options="Item", in_list_view=1),
		make_field("Item Ready", "item_ready", "Check", default=0),
		make_field("Income Account", "income_account", "Link", options="Account"),
		make_field("Cost Center", "cost_center", "Link", options="Cost Center"),
		make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", read_only=1, in_list_view=1),
		make_field("Evidence Snapshot", "evidence_snapshot_section", "Section Break"),
		make_field("Support Worker User", "support_worker_user", "Link", options="User"),
		make_field("Support Worker Employee", "support_worker_employee", "Link" if doctype_exists("Employee") else "Data", options="Employee" if doctype_exists("Employee") else None),
		make_field("Support Worker Name", "support_worker_name", "Data"),
		make_field("Participant Attended", "participant_attended", "Check", default=1),
		make_field("Service Delivered", "service_delivered", "Check", default=1),
		make_field("Progress Note", "progress_note", "Text Editor"),
		make_field("Incident Flag", "incident_flag", "Check", default=0),
		make_field("Incident Notes", "incident_notes", "Small Text"),
		make_field("Finance Links", "finance_links_section", "Section Break"),
		make_field("Finance Service Type", "finance_service_type", "Link" if doctype_exists(NDIS_SERVICE_TYPE) else "Data", options=NDIS_SERVICE_TYPE if doctype_exists(NDIS_SERVICE_TYPE) else None),
		make_field("Support Item", "support_item", "Link" if doctype_exists(NDIS_SUPPORT_ITEM) else "Data", options=NDIS_SUPPORT_ITEM if doctype_exists(NDIS_SUPPORT_ITEM) else None, in_list_view=1),
	]
	if doctype_exists(PLAN_BUDGET):
		fields.append(make_field("NDIS Plan Budget", "plan_budget", "Link", options=PLAN_BUDGET))
	if doctype_exists(SERVICE_BOOKING):
		fields.append(make_field("NDIS Service Booking", "service_booking", "Link", options=SERVICE_BOOKING, in_list_view=1))
	fields += [
		make_field("Funding Source", "funding_source", "Data"),
		make_field("Location Snapshot", "location_snapshot_section", "Section Break"),
		make_field("Default House", "default_house", "Link" if doctype_exists(NDIS_HOUSE) else "Data", options=NDIS_HOUSE if doctype_exists(NDIS_HOUSE) else None),
		make_field("Delivery Location", "delivery_location", "Data"),
		make_field("Readiness / Holds", "readiness_holds_section", "Section Break"),
		make_field("Billing Preparation Ready", "billing_preparation_ready", "Check", default=0, in_list_view=1),
		make_field("Claim Preparation Ready", "claim_preparation_ready", "Check", default=0),
		make_field("Billing Hold", "billing_hold", "Check", default=0, in_list_view=1),
		make_field("Billing Hold Reason", "billing_hold_reason", "Small Text"),
		make_field("Sales Invoice Draft Creation Ready", "sales_invoice_draft_creation_ready", "Check", default=0),
		make_field("Sales Invoice Draft Creation Hold", "sales_invoice_draft_creation_hold", "Check", default=1),
		make_field("Review Status", "review_status_section", "Section Break"),
		make_field("Line Ready for Draft Sales Invoice Creation", "line_ready_for_draft_sales_invoice_creation", "Check", default=0, in_list_view=1),
		make_field("Sales Invoice Draft Status", "sales_invoice_draft_status", "Select", options="Draft\nReady\nApproved\nDraft Sales Invoice Created\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(name=SALES_INVOICE_DRAFT_LINE, fields=fields, istable=1)


def create_sales_invoice_draft_run():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-SI-DRAFT-RUN-.YYYY.-.#####", default="NDIS-SI-DRAFT-RUN-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Sales Invoice Draft Creation\nSales Invoice Draft Run Approved\nDraft Sales Invoices Created\nReturned to Invoice Draft\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Sales Invoice Draft Run Ready", "sales_invoice_draft_run_ready", "Check", read_only=1, in_list_view=1),
		make_field("Sales Invoice Draft Creation Allowed", "sales_invoice_draft_creation_allowed", "Check", default=0, description="Must be ticked manually after approval before Draft Sales Invoices are created."),
		make_field("Enable NDIS Finance Invoice Controls", "enable_ndis_finance_invoice_controls", "Check", default=1),
		make_field("Sales Invoice Defaults", "sales_invoice_defaults_section", "Section Break"),
		make_field("Company", "company", "Link", options="Company", in_list_view=1),
		make_field("Posting Date", "posting_date", "Date", in_list_view=1),
		make_field("Due Date", "due_date", "Date", in_list_view=1),
		make_field("Receivable Account", "receivable_account", "Link", options="Account"),
		make_field("Default Income Account", "default_income_account", "Link", options="Account"),
		make_field("Default Item Code", "default_item_code", "Link", options="Item"),
		make_field("Default Cost Center", "default_cost_center", "Link", options="Cost Center"),
		make_field("Sales Invoice Draft Summary", "sales_invoice_summary_section", "Section Break"),
		make_field("Sales Invoice Draft Line Count", "sales_invoice_draft_line_count", "Int", read_only=1),
		make_field("Invoice Quantity Total", "invoice_quantity_total", "Float", read_only=1),
		make_field("Invoice Amount Total", "invoice_amount_total", "Currency", read_only=1),
		make_field("Sales Invoice Ready Count", "sales_invoice_ready_count", "Int", read_only=1),
		make_field("Draft Sales Invoice Created Count", "draft_sales_invoice_created_count", "Int", read_only=1),
		make_field("Sales Invoice Draft Hold Count", "sales_invoice_draft_hold_count", "Int", read_only=1),
		make_field("Missing Item Count", "missing_item_count", "Int", read_only=1),
		make_field("Missing Income Account Count", "missing_income_account_count", "Int", read_only=1),
		make_field("Missing Service Booking Count", "missing_service_booking_count", "Int", read_only=1),
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
		make_field("NDIS CRM Invoice Draft", "invoice_draft", "Link", options=INVOICE_DRAFT, reqd=1, in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
		make_field("NDIS Financial Profile", "ndis_financial_profile", "Link" if doctype_exists(FINANCE_PROFILE) else "Data", options=FINANCE_PROFILE if doctype_exists(FINANCE_PROFILE) else None),
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Invoice Window", "invoice_window_section", "Section Break"),
		make_field("Invoice Period Start", "invoice_period_start", "Date", in_list_view=1),
		make_field("Invoice Period End", "invoice_period_end", "Date", in_list_view=1),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Sales Invoice Owner", "sales_invoice_owner", "Link", options="User", in_list_view=1),
		make_field("Invoice Owner", "invoice_owner", "Link", options="User"),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Preparation Owner", "preparation_owner", "Link", options="User"),
		make_field("Operations Owner", "operations_owner", "Link", options="User"),
		make_field("Rostering Owner", "rostering_owner", "Link", options="User"),
		make_field("Service Manager", "service_manager", "Link", options="User"),
		make_field("Clinical Owner", "clinical_owner", "Link", options="User"),
		make_field("Default House", "default_house", "Link" if doctype_exists(NDIS_HOUSE) else "Data", options=NDIS_HOUSE if doctype_exists(NDIS_HOUSE) else None),
		make_field("Sales Invoice Draft Lines", "sales_invoice_draft_lines_section", "Section Break"),
		make_field("Sales Invoice Draft Lines", "sales_invoice_draft_lines", "Table", options=SALES_INVOICE_DRAFT_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Sales Invoice Draft Run Notes", "sales_invoice_draft_run_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(
		name=SALES_INVOICE_DRAFT_RUN,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def _phase18_link_fields(insert_after):
	return [
		{"fieldname": "sales_invoice_draft_run_section", "label": "NDIS Sales Invoice Draft Run", "fieldtype": "Section Break", "insert_after": insert_after},
		{"fieldname": "ndis_sales_invoice_draft_run", "label": "NDIS CRM Sales Invoice Draft Run", "fieldtype": "Link", "options": SALES_INVOICE_DRAFT_RUN, "read_only": 1, "insert_after": "sales_invoice_draft_run_section"},
		{"fieldname": "sales_invoice_draft_run_status", "label": "Sales Invoice Draft Run Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_sales_invoice_draft_run"},
		{"fieldname": "sales_invoice_draft_run_ready", "label": "Sales Invoice Draft Run Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "sales_invoice_draft_run_status"},
	]


def create_custom_fields_phase18():
	deal_fields = [
		{"fieldname": "sales_invoice_draft_run_section", "label": "NDIS Sales Invoice Draft Run", "fieldtype": "Section Break", "insert_after": "invoice_draft_ready"},
		{
			"fieldname": "ndis_sales_invoice_draft_run_required",
			"label": "Sales Invoice Draft Run Required Before Active Deal",
			"fieldtype": "Check",
			"default": 0,
			"insert_after": "sales_invoice_draft_run_section",
			"description": "Optional guard only. Normally Sales Invoice draft runs happen after service delivery and invoice draft approval.",
		},
		{"fieldname": "ndis_sales_invoice_draft_run", "label": "NDIS CRM Sales Invoice Draft Run", "fieldtype": "Link", "options": SALES_INVOICE_DRAFT_RUN, "read_only": 1, "insert_after": "ndis_sales_invoice_draft_run_required"},
		{"fieldname": "sales_invoice_draft_run_status", "label": "Sales Invoice Draft Run Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_sales_invoice_draft_run"},
		{"fieldname": "sales_invoice_draft_run_ready", "label": "Sales Invoice Draft Run Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "sales_invoice_draft_run_status"},
	]
	shared_fields = _phase18_link_fields("invoice_draft_ready")
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
	print("Created / updated Phase 18 Sales Invoice draft run custom fields.")


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
	upsert_doc(
		"CRM Form Script",
		"NDIS CRM Deal Actions",
		{"dt": CRM_DEAL, "view": "Form", "enabled": 1, "is_standard": 0, "script": _deal_script()},
	)
	if frappe.db.exists("DocType", "Client Script"):
		upsert_doc(
			"Client Script",
			"NDIS CRM Invoice Draft Actions",
			{"dt": INVOICE_DRAFT, "view": "Form", "enabled": 1, "script": _invoice_script()},
		)
		upsert_doc(
			"Client Script",
			"NDIS CRM Sales Invoice Draft Run Actions",
			{"dt": SALES_INVOICE_DRAFT_RUN, "view": "Form", "enabled": 1, "script": _sales_invoice_run_script()},
		)


def _deal_script():
	from ndis_crm.setup.phase17_invoice_draft import _deal_script as phase17_deal_script

	script = phase17_deal_script()
	insert = r''',
      {
        label: "Create Sales Invoice Draft Run",
        onClick: () => {
          call("ndis_crm.phase18_sales_invoice_draft.create_sales_invoice_draft_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Sales Invoice Draft Run Created" : "Existing Sales Invoice Draft Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-sales-invoice-draft-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Sales Invoice Draft Run",
        onClick: () => {
          if (doc.ndis_sales_invoice_draft_run) {
            window.open(`/app/ndis-crm-sales-invoice-draft-run/${doc.ndis_sales_invoice_draft_run}`, "_blank")
          } else {
            createToast({ title: "No Sales Invoice Draft Run linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _invoice_script():
	from ndis_crm.setup.phase17_invoice_draft import _invoice_script as phase17_invoice_script

	script = phase17_invoice_script()
	insert = r'''

        frm.add_custom_button(__("Create Sales Invoice Draft Run"), function () {
            frappe.call({
                method: "ndis_crm.phase18_sales_invoice_draft.create_sales_invoice_draft_run_from_invoice_draft",
                args: { invoice_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating Sales Invoice draft run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Sales Invoice Draft Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Sales Invoice Draft Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_sales_invoice_draft_run) {
            frm.add_custom_button(__("Open Sales Invoice Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Sales Invoice Draft Run", frm.doc.ndis_sales_invoice_draft_run);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.billing_draft)", insert + "\n        if (frm.doc.billing_draft)")


def _sales_invoice_run_script():
	return r'''
frappe.ui.form.on("NDIS CRM Sales Invoice Draft Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Sales Invoice Draft Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase18_sales_invoice_draft.generate_sales_invoice_draft_lines",
                args: { sales_invoice_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating Sales Invoice draft lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Sales Invoice draft lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Sales Invoice Draft Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase18_sales_invoice_draft.validate_sales_invoice_draft_run_readiness",
                args: { sales_invoice_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating Sales Invoice draft readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Sales Invoice Draft Run validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Sales Invoice Draft Creation"), function () {
            frappe.call({
                method: "ndis_crm.phase18_sales_invoice_draft.mark_ready_for_sales_invoice_draft_creation",
                args: { sales_invoice_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for Sales Invoice draft creation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Sales Invoice draft creation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Sales Invoice Draft Run"), function () {
            frappe.call({
                method: "ndis_crm.phase18_sales_invoice_draft.approve_sales_invoice_draft_run",
                args: { sales_invoice_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving Sales Invoice Draft Run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Sales Invoice Draft Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create Draft Sales Invoices"), function () {
            frappe.confirm(
                __("This will create ERPNext Sales Invoice records in Draft status only. It will not submit invoices or create payments, journals, GL entries, claims, or accounting postings."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase18_sales_invoice_draft.create_draft_sales_invoices",
                        args: { sales_invoice_draft_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Creating Draft Sales Invoices...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Draft Sales Invoices created"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.invoice_draft) {
            frm.add_custom_button(__("Open Invoice Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Invoice Draft", frm.doc.invoice_draft);
            }, __("Open"));
        }

        if (frm.doc.billing_draft) {
            frm.add_custom_button(__("Open Billing Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Billing Draft", frm.doc.billing_draft);
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
