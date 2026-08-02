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
INVOICE_DRAFT_LINE = "NDIS CRM Invoice Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_invoice_draft_doctypes()
	create_custom_fields_phase17()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 17 invoice draft bridge installed successfully.")


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
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 17 DocTypes: " + ", ".join(missing))
	print("Required Phase 17 DocTypes found.")


def make_field(label, fieldname, fieldtype, **kwargs):
	field = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype}
	field.update(kwargs)
	return field


def standard_permissions():
	return [
		{
			"role": "System Manager",
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 1,
			"email": 1,
			"export": 1,
			"print": 1,
			"report": 1,
			"share": 1,
		},
		{
			"role": "NDIS CRM Manager",
			"read": 1,
			"write": 1,
			"create": 1,
			"delete": 1,
			"email": 1,
			"export": 1,
			"print": 1,
			"report": 1,
			"share": 1,
		},
		{"role": "NDIS Intake Officer", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
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


def create_invoice_draft_doctypes():
	create_invoice_draft_line()
	create_invoice_draft()


def create_invoice_draft_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Billing Source Key", "billing_source_key", "Data", read_only=1),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Invoice Grouping", "invoice_grouping_section", "Section Break"),
		make_field("Invoice Group Key", "invoice_group_key", "Data", in_list_view=1),
		make_field("Proposed Invoice Reference", "proposed_invoice_reference", "Data"),
		make_field("Sales Invoice Reference", "sales_invoice_reference", "Data", read_only=1),
		make_field("Invoice Service", "invoice_service_section", "Section Break"),
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
		make_field("Evidence Snapshot", "evidence_snapshot_section", "Section Break"),
		make_field("Support Worker User", "support_worker_user", "Link", options="User"),
	]
	if doctype_exists("Employee"):
		fields.append(make_field("Support Worker Employee", "support_worker_employee", "Link", options="Employee"))
	else:
		fields.append(make_field("Support Worker Employee", "support_worker_employee", "Data"))
	fields += [
		make_field("Support Worker Name", "support_worker_name", "Data"),
		make_field("Participant Attended", "participant_attended", "Check", default=1),
		make_field("Service Delivered", "service_delivered", "Check", default=1),
		make_field("Progress Note", "progress_note", "Text Editor"),
		make_field("Incident Flag", "incident_flag", "Check", default=0),
		make_field("Incident Notes", "incident_notes", "Small Text"),
		make_field("Finance Links", "finance_links_section", "Section Break"),
	]
	if doctype_exists(NDIS_SERVICE_TYPE):
		fields.append(make_field("Finance Service Type", "finance_service_type", "Link", options=NDIS_SERVICE_TYPE))
	else:
		fields.append(make_field("Finance Service Type", "finance_service_type", "Data"))
	if doctype_exists(NDIS_SUPPORT_ITEM):
		fields.append(make_field("Support Item", "support_item", "Link", options=NDIS_SUPPORT_ITEM, in_list_view=1))
	else:
		fields.append(make_field("Support Item", "support_item", "Data", in_list_view=1))
	if doctype_exists(PLAN_BUDGET):
		fields.append(make_field("NDIS Plan Budget", "plan_budget", "Link", options=PLAN_BUDGET))
	if doctype_exists(SERVICE_BOOKING):
		fields.append(make_field("NDIS Service Booking", "service_booking", "Link", options=SERVICE_BOOKING, in_list_view=1))

	fields.append(make_field("Location Snapshot", "location_snapshot_section", "Section Break"))
	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))
	fields += [
		make_field("Delivery Location", "delivery_location", "Data"),
		make_field("Readiness / Holds", "readiness_holds_section", "Section Break"),
		make_field("Billing Preparation Required", "billing_preparation_required", "Check", default=1),
		make_field("Billing Preparation Ready", "billing_preparation_ready", "Check", default=0, in_list_view=1),
		make_field("Claim Preparation Ready", "claim_preparation_ready", "Check", default=0),
		make_field("Billing Hold", "billing_hold", "Check", default=0, in_list_view=1),
		make_field("Billing Hold Reason", "billing_hold_reason", "Small Text"),
		make_field("Sales Invoice Creation Ready", "sales_invoice_creation_ready", "Check", default=0),
		make_field("Sales Invoice Creation Hold", "sales_invoice_creation_hold", "Check", default=1),
		make_field("Review Status", "review_status_section", "Section Break"),
		make_field("Line Ready for Sales Invoice Creation", "line_ready_for_sales_invoice_creation", "Check", default=0, in_list_view=1),
		make_field("Invoice Draft Status", "invoice_draft_status", "Select", options="Draft\nReady\nApproved\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(name=INVOICE_DRAFT_LINE, fields=fields, istable=1)


def create_invoice_draft():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-INVOICE-DRAFT-.YYYY.-.#####", default="NDIS-INVOICE-DRAFT-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Invoice Review\nInvoice Draft Approved\nReturned to Billing Draft\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Invoice Draft Ready", "invoice_draft_ready", "Check", read_only=1, in_list_view=1),
		make_field("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed", "Check", default=0, read_only=1, description="Always blocked in Phase 17."),
		make_field("Invoice Summary", "invoice_summary_section", "Section Break"),
		make_field("Invoice Line Count", "invoice_line_count", "Int", read_only=1),
		make_field("Invoice Quantity Total", "invoice_quantity_total", "Float", read_only=1),
		make_field("Invoice Amount Total", "invoice_amount_total", "Currency", read_only=1),
		make_field("Invoice Ready Count", "invoice_ready_count", "Int", read_only=1),
		make_field("Invoice Approved Count", "invoice_approved_count", "Int", read_only=1),
		make_field("Invoice Hold Count", "invoice_hold_count", "Int", read_only=1),
		make_field("Missing Customer Count", "missing_customer_count", "Int", read_only=1),
		make_field("Missing Support Item Count", "missing_support_item_count", "Int", read_only=1),
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
	]
	if doctype_exists(ATTENDANCE_DRAFT):
		fields.append(make_field("NDIS CRM Attendance Draft", "attendance_draft", "Link", options=ATTENDANCE_DRAFT))
	else:
		fields.append(make_field("NDIS CRM Attendance Draft", "attendance_draft", "Data"))
	fields.append(make_field("NDIS CRM Billing Draft", "billing_draft", "Link", options=BILLING_DRAFT, reqd=1, in_list_view=1))
	if doctype_exists(CLAIM_DRAFT):
		fields.append(make_field("NDIS CRM Claim Draft", "claim_draft", "Link", options=CLAIM_DRAFT))
	else:
		fields.append(make_field("NDIS CRM Claim Draft", "claim_draft", "Data"))
	fields.append(make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1))
	if doctype_exists(FINANCE_PROFILE):
		fields.append(make_field("NDIS Financial Profile", "ndis_financial_profile", "Link", options=FINANCE_PROFILE))
	else:
		fields.append(make_field("NDIS Financial Profile", "ndis_financial_profile", "Data"))
	fields += [
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Invoice Window", "invoice_window_section", "Section Break"),
		make_field("Invoice Period Start", "invoice_period_start", "Date", in_list_view=1),
		make_field("Invoice Period End", "invoice_period_end", "Date", in_list_view=1),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Invoice Owner", "invoice_owner", "Link", options="User", in_list_view=1),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Preparation Owner", "preparation_owner", "Link", options="User"),
		make_field("Operations Owner", "operations_owner", "Link", options="User"),
		make_field("Rostering Owner", "rostering_owner", "Link", options="User"),
		make_field("Service Manager", "service_manager", "Link", options="User"),
		make_field("Clinical Owner", "clinical_owner", "Link", options="User"),
		make_field("Default Cost Center", "default_cost_center", "Link", options="Cost Center"),
	]
	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))
	fields += [
		make_field("Invoice Lines", "invoice_lines_section", "Section Break"),
		make_field("Invoice Lines", "invoice_lines", "Table", options=INVOICE_DRAFT_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Invoice Draft Notes", "invoice_draft_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(name=INVOICE_DRAFT, fields=fields, autoname="naming_series:", title_field="participant_name")


def create_custom_fields_phase17():
	deal_fields = [
		{"fieldname": "invoice_draft_section", "label": "NDIS Invoice Draft", "fieldtype": "Section Break", "insert_after": "claim_draft_ready"},
		{"fieldname": "ndis_invoice_draft_required", "label": "Invoice Draft Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "invoice_draft_section", "description": "Optional guard only. Normally invoice draft happens after participant activation, service delivery, and billing draft approval."},
		{"fieldname": "ndis_invoice_draft", "label": "NDIS CRM Invoice Draft", "fieldtype": "Link", "options": INVOICE_DRAFT, "read_only": 1, "insert_after": "ndis_invoice_draft_required"},
		{"fieldname": "invoice_draft_status", "label": "Invoice Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_invoice_draft"},
		{"fieldname": "invoice_draft_ready", "label": "Invoice Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "invoice_draft_status"},
	]
	shared_fields = [
		{"fieldname": "invoice_draft_section", "label": "NDIS Invoice Draft", "fieldtype": "Section Break", "insert_after": "claim_draft_ready"},
		{"fieldname": "ndis_invoice_draft", "label": "NDIS CRM Invoice Draft", "fieldtype": "Link", "options": INVOICE_DRAFT, "read_only": 1, "insert_after": "invoice_draft_section"},
		{"fieldname": "invoice_draft_status", "label": "Invoice Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_invoice_draft"},
		{"fieldname": "invoice_draft_ready", "label": "Invoice Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "invoice_draft_status"},
	]
	billing_fields = [
		{"fieldname": "invoice_draft_section", "label": "NDIS Invoice Draft", "fieldtype": "Section Break", "insert_after": "billing_draft_ready"},
		{"fieldname": "ndis_invoice_draft", "label": "NDIS CRM Invoice Draft", "fieldtype": "Link", "options": INVOICE_DRAFT, "read_only": 1, "insert_after": "invoice_draft_section"},
		{"fieldname": "invoice_draft_status", "label": "Invoice Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_invoice_draft"},
		{"fieldname": "invoice_draft_ready", "label": "Invoice Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "invoice_draft_status"},
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
		BILLING_DRAFT: billing_fields,
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
	print("Created / updated Phase 17 invoice draft custom fields.")


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
			"NDIS CRM Billing Draft Actions",
			{"dt": BILLING_DRAFT, "view": "Form", "enabled": 1, "script": _billing_script()},
		)
		if doctype_exists(CLAIM_DRAFT):
			upsert_doc(
				"Client Script",
				"NDIS CRM Claim Draft Actions",
				{"dt": CLAIM_DRAFT, "view": "Form", "enabled": 1, "script": _claim_script()},
			)
		upsert_doc(
			"Client Script",
			"NDIS CRM Invoice Draft Actions",
			{"dt": INVOICE_DRAFT, "view": "Form", "enabled": 1, "script": _invoice_script()},
		)


def _deal_script():
	from ndis_crm.setup.phase16_claim_draft import _deal_script as phase16_deal_script

	script = phase16_deal_script()
	insert = r''',
      {
        label: "Create Invoice Draft",
        onClick: () => {
          call("ndis_crm.phase17_invoice_draft.create_invoice_draft_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Invoice Draft Created" : "Existing Invoice Draft Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-invoice-draft/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Invoice Draft",
        onClick: () => {
          if (doc.ndis_invoice_draft) {
            window.open(`/app/ndis-crm-invoice-draft/${doc.ndis_invoice_draft}`, "_blank")
          } else {
            createToast({ title: "No Invoice Draft linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _billing_script():
	from ndis_crm.setup.phase16_claim_draft import _billing_script as phase16_billing_script

	script = phase16_billing_script()
	insert = r'''

        frm.add_custom_button(__("Create Invoice Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase17_invoice_draft.create_invoice_draft_from_billing_draft",
                args: { billing_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating invoice draft...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Invoice Draft created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Invoice Draft", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_invoice_draft) {
            frm.add_custom_button(__("Open Invoice Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Invoice Draft", frm.doc.ndis_invoice_draft);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.ndis_claim_draft)", insert + "\n        if (frm.doc.ndis_claim_draft)")


def _claim_script():
	from ndis_crm.setup.phase16_claim_draft import _claim_script as phase16_claim_script

	script = phase16_claim_script()
	insert = r'''

        frm.add_custom_button(__("Create Invoice Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase17_invoice_draft.create_invoice_draft_from_claim_draft",
                args: { claim_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating invoice draft...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Invoice Draft created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Invoice Draft", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_invoice_draft) {
            frm.add_custom_button(__("Open Invoice Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Invoice Draft", frm.doc.ndis_invoice_draft);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.billing_draft)", insert + "\n        if (frm.doc.billing_draft)")


def _invoice_script():
	return r'''
frappe.ui.form.on("NDIS CRM Invoice Draft", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Invoice Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase17_invoice_draft.generate_invoice_lines",
                args: { invoice_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating invoice lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Invoice lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Invoice Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase17_invoice_draft.validate_invoice_draft_readiness",
                args: { invoice_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating invoice draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Invoice draft validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Invoice Review"), function () {
            frappe.call({
                method: "ndis_crm.phase17_invoice_draft.mark_ready_for_invoice_review",
                args: { invoice_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for invoice review...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for invoice review"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Invoice Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase17_invoice_draft.approve_invoice_draft",
                args: { invoice_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving invoice draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Invoice Draft approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.billing_draft) {
            frm.add_custom_button(__("Open Billing Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Billing Draft", frm.doc.billing_draft);
            }, __("Open"));
        }

        if (frm.doc.claim_draft) {
            frm.add_custom_button(__("Open Claim Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Draft", frm.doc.claim_draft);
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
