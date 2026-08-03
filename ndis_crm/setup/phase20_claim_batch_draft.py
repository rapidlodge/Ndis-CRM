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
CLAIM_BATCH_DRAFT_LINE = "NDIS CRM Claim Batch Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_claim_batch_draft_doctypes()
	create_custom_fields_phase20()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 20 Claim Batch draft bridge installed successfully.")


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
		"Sales Invoice",
		"NDIS Claim Batch",
		"NDIS Claim Line",
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 20 DocTypes: " + ", ".join(missing))
	print("Required Phase 20 DocTypes found.")


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


def create_claim_batch_draft_doctypes():
	create_claim_batch_draft_line()
	create_claim_batch_draft_run()


def create_claim_batch_draft_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Claim Source Key", "claim_source_key", "Data", read_only=1),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Submitted Sales Invoice", "submitted_sales_invoice_section", "Section Break"),
		make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", in_list_view=1),
		make_field("Sales Invoice Docstatus", "sales_invoice_docstatus", "Int", read_only=1),
		make_field("Sales Invoice Status", "sales_invoice_status", "Data", read_only=1),
		make_field("Claim Source", "claim_source_section", "Section Break"),
		make_field("Service Date", "service_date", "Date", in_list_view=1),
		make_field("Billable Date", "billable_date", "Date"),
		make_field("Claim Quantity", "claim_quantity", "Float", in_list_view=1),
		make_field("Claim Unit", "claim_unit", "Data", default="Hour"),
		make_field("Claim Rate", "claim_rate", "Currency"),
		make_field("Claim Amount", "claim_amount", "Currency", in_list_view=1),
		make_field("GST Treatment", "gst_treatment", "Data"),
		make_field("Rate Source", "rate_source", "Data"),
		make_field("Finance Links", "finance_links_section", "Section Break"),
		make_field("Finance Service Type", "finance_service_type", "Link" if doctype_exists(NDIS_SERVICE_TYPE) else "Data", options=NDIS_SERVICE_TYPE if doctype_exists(NDIS_SERVICE_TYPE) else None),
		make_field("Support Item", "support_item", "Link" if doctype_exists(NDIS_SUPPORT_ITEM) else "Data", options=NDIS_SUPPORT_ITEM if doctype_exists(NDIS_SUPPORT_ITEM) else None, in_list_view=1),
		make_field("NDIS Plan Budget", "plan_budget", "Link" if doctype_exists(PLAN_BUDGET) else "Data", options=PLAN_BUDGET if doctype_exists(PLAN_BUDGET) else None),
		make_field("NDIS Service Booking", "service_booking", "Link" if doctype_exists(SERVICE_BOOKING) else "Data", options=SERVICE_BOOKING if doctype_exists(SERVICE_BOOKING) else None, in_list_view=1),
		make_field("Funding Source", "funding_source", "Data"),
		make_field("Default House", "default_house", "Link" if doctype_exists(NDIS_HOUSE) else "Data", options=NDIS_HOUSE if doctype_exists(NDIS_HOUSE) else None),
		make_field("Delivery Location", "delivery_location", "Data"),
		make_field("Evidence Snapshot", "evidence_snapshot_section", "Section Break"),
		make_field("Participant Attended", "participant_attended", "Check", default=1),
		make_field("Service Delivered", "service_delivered", "Check", default=1),
		make_field("Support Worker User", "support_worker_user", "Link", options="User"),
		make_field("Support Worker Employee", "support_worker_employee", "Link" if doctype_exists("Employee") else "Data", options="Employee" if doctype_exists("Employee") else None),
		make_field("Support Worker Name", "support_worker_name", "Data"),
		make_field("Progress Note", "progress_note", "Text Editor"),
		make_field("Incident Flag", "incident_flag", "Check", default=0),
		make_field("Incident Notes", "incident_notes", "Small Text"),
		make_field("Readiness / Holds", "readiness_holds_section", "Section Break"),
		make_field("Invoice Group Key", "invoice_group_key", "Data"),
		make_field("Invoice Draft Reference", "invoice_draft_reference", "Data"),
		make_field("Claim Preparation Ready", "claim_preparation_ready", "Check", default=0),
		make_field("Submitted Invoice Ready", "submitted_invoice_ready", "Check", default=0),
		make_field("Claim Batch Mapping Ready", "claim_batch_mapping_ready", "Check", default=0),
		make_field("Claim Batch Draft Creation Ready", "claim_batch_draft_creation_ready", "Check", default=0),
		make_field("Claim Batch Draft Creation Hold", "claim_batch_draft_creation_hold", "Check", default=1),
		make_field("Claim Batch Draft Creation Hold Reason", "claim_batch_draft_creation_hold_reason", "Small Text"),
		make_field("Draft Output Links", "draft_output_section", "Section Break"),
		make_field("NDIS Claim Batch", "ndis_claim_batch", "Link", options="NDIS Claim Batch", read_only=1, in_list_view=1),
		make_field("NDIS Claim Line", "ndis_claim_line", "Link", options="NDIS Claim Line", read_only=1),
		make_field("Review Status", "review_status_section", "Section Break"),
		make_field("Line Ready for Claim Batch Draft Creation", "line_ready_for_claim_batch_draft_creation", "Check", default=0, in_list_view=1),
		make_field("Claim Batch Draft Status", "claim_batch_draft_status", "Select", options="Draft\nReady\nApproved\nDraft Claim Batch Created\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(CLAIM_BATCH_DRAFT_LINE, fields, istable=1)


def create_claim_batch_draft_run():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-CLAIM-BATCH-DRAFT-RUN-.YYYY.-.#####", default="NDIS-CLAIM-BATCH-DRAFT-RUN-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Claim Batch Draft Creation\nClaim Batch Draft Run Approved\nDraft Claim Batches Created\nReturned to Claim Draft\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Claim Batch Draft Run Ready", "claim_batch_draft_run_ready", "Check", read_only=1, in_list_view=1),
		make_field("Claim Batch Draft Creation Allowed", "claim_batch_draft_creation_allowed", "Check", default=0),
		make_field("Claim Batch Summary", "claim_batch_summary_section", "Section Break"),
		make_field("Claim Batch Draft Line Count", "claim_batch_draft_line_count", "Int", read_only=1),
		make_field("Claim Quantity Total", "claim_quantity_total", "Float", read_only=1),
		make_field("Claim Amount Total", "claim_amount_total", "Currency", read_only=1),
		make_field("Claim Batch Ready Count", "claim_batch_ready_count", "Int", read_only=1),
		make_field("Draft Claim Line Created Count", "draft_claim_line_created_count", "Int", read_only=1),
		make_field("Claim Batch Draft Hold Count", "claim_batch_draft_hold_count", "Int", read_only=1),
		make_field("Missing Sales Invoice Count", "missing_sales_invoice_count", "Int", read_only=1),
		make_field("Missing Service Booking Count", "missing_service_booking_count", "Int", read_only=1),
		make_field("Missing Support Item Count", "missing_support_item_count", "Int", read_only=1),
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
		make_field("NDIS CRM Claim Draft", "claim_draft", "Link", options=CLAIM_DRAFT, reqd=1, in_list_view=1),
		make_field("NDIS CRM Invoice Draft", "invoice_draft", "Link", options=INVOICE_DRAFT),
		make_field("NDIS CRM Sales Invoice Draft Run", "sales_invoice_draft_run", "Link", options=SALES_INVOICE_DRAFT_RUN),
		make_field("NDIS CRM Sales Invoice Submission Run", "sales_invoice_submission_run", "Link", options=SALES_INVOICE_SUBMISSION_RUN, in_list_view=1),
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
		make_field("Claim Batch Owner", "claim_batch_owner", "Link", options="User", in_list_view=1),
		make_field("Claim Owner", "claim_owner", "Link", options="User"),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Claim Batch Draft Lines", "claim_batch_draft_lines_section", "Section Break"),
		make_field("Claim Batch Draft Lines", "claim_batch_draft_lines", "Table", options=CLAIM_BATCH_DRAFT_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Claim Batch Draft Run Notes", "claim_batch_draft_run_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(CLAIM_BATCH_DRAFT_RUN, fields, autoname="naming_series:", title_field="participant_name")


def _link_fields(insert_after):
	return [
		{"fieldname": "claim_batch_draft_section", "label": "NDIS Claim Batch Draft Run", "fieldtype": "Section Break", "insert_after": insert_after},
		{"fieldname": "ndis_claim_batch_draft_run", "label": "NDIS CRM Claim Batch Draft Run", "fieldtype": "Link", "options": CLAIM_BATCH_DRAFT_RUN, "read_only": 1, "insert_after": "claim_batch_draft_section"},
		{"fieldname": "claim_batch_draft_status", "label": "Claim Batch Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_claim_batch_draft_run"},
		{"fieldname": "claim_batch_draft_ready", "label": "Claim Batch Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "claim_batch_draft_status"},
	]


def create_custom_fields_phase20():
	deal_fields = [
		{"fieldname": "claim_batch_draft_section", "label": "NDIS Claim Batch Draft Run", "fieldtype": "Section Break", "insert_after": "sales_invoice_submission_ready"},
		{"fieldname": "ndis_claim_batch_draft_run_required", "label": "Claim Batch Draft Run Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "claim_batch_draft_section"},
		{"fieldname": "ndis_claim_batch_draft_run", "label": "NDIS CRM Claim Batch Draft Run", "fieldtype": "Link", "options": CLAIM_BATCH_DRAFT_RUN, "read_only": 1, "insert_after": "ndis_claim_batch_draft_run_required"},
		{"fieldname": "claim_batch_draft_status", "label": "Claim Batch Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_claim_batch_draft_run"},
		{"fieldname": "claim_batch_draft_ready", "label": "Claim Batch Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "claim_batch_draft_status"},
	]
	custom_fields = {
		CRM_DEAL: deal_fields,
		HANDOVER: _link_fields("sales_invoice_submission_ready"),
		FINANCE_ONBOARDING: _link_fields("sales_invoice_submission_ready"),
		OPERATIONS_SETUP: _link_fields("sales_invoice_submission_ready"),
		SCHEDULE_DRAFT: _link_fields("sales_invoice_submission_ready"),
		ROSTER_REQUEST: _link_fields("sales_invoice_submission_ready"),
		SERVICE_FILE: _link_fields("sales_invoice_submission_ready"),
		SESSION_DRAFT: _link_fields("sales_invoice_submission_ready"),
		EVIDENCE_REVIEW: _link_fields("sales_invoice_submission_ready"),
		DOWNSTREAM_PREPARATION: _link_fields("sales_invoice_submission_ready"),
		BILLING_DRAFT: _link_fields("sales_invoice_submission_ready"),
		CLAIM_DRAFT: _link_fields("claim_draft_ready"),
		INVOICE_DRAFT: _link_fields("sales_invoice_submission_ready"),
		SALES_INVOICE_DRAFT_RUN: _link_fields("sales_invoice_submission_ready"),
		SALES_INVOICE_SUBMISSION_RUN: _link_fields("sales_invoice_submission_ready"),
		INTAKE: _link_fields("sales_invoice_submission_ready"),
	}
	if doctype_exists(ATTENDANCE_DRAFT):
		custom_fields[ATTENDANCE_DRAFT] = _link_fields("sales_invoice_submission_ready")
	frappe.flags.in_install = True
	try:
		create_custom_fields(custom_fields, update=True)
	finally:
		frappe.flags.in_install = False
	print("Created / updated Phase 20 claim batch draft custom fields.")


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
		upsert_doc("Client Script", "NDIS CRM Claim Draft Actions", {"dt": CLAIM_DRAFT, "view": "Form", "enabled": 1, "script": _claim_script()})
		upsert_doc("Client Script", "NDIS CRM Sales Invoice Submission Run Actions", {"dt": SALES_INVOICE_SUBMISSION_RUN, "view": "Form", "enabled": 1, "script": _submission_script()})
		upsert_doc("Client Script", "NDIS CRM Claim Batch Draft Run Actions", {"dt": CLAIM_BATCH_DRAFT_RUN, "view": "Form", "enabled": 1, "script": _run_script()})


def _deal_script():
	try:
		from ndis_crm.setup.phase19_sales_invoice_submission import _deal_script as previous_script

		script = previous_script()
	except Exception:
		script = "function setupForm({ doc, call, createToast }) {\n  return { actions: [] }\n}"
	insert = r'''
      {
        label: "Create Claim Batch Draft Run",
        onClick: () => {
          call("ndis_crm.phase20_claim_batch_draft.create_claim_batch_draft_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Claim Batch Draft Run Created" : "Existing Claim Batch Draft Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-claim-batch-draft-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Claim Batch Draft Run",
        onClick: () => {
          if (doc.ndis_claim_batch_draft_run) {
            window.open(`/app/ndis-crm-claim-batch-draft-run/${doc.ndis_claim_batch_draft_run}`, "_blank")
          } else {
            createToast({ title: "No Claim Batch Draft Run linked yet", icon: "info" })
          }
        }
      }
'''.rstrip()
	return script.replace("\n    ]", ",\n" + insert + "\n    ]", 1)


def _claim_script():
	try:
		from ndis_crm.setup.phase16_claim_draft import _claim_script as previous_script

		script = previous_script()
	except Exception:
		script = 'frappe.ui.form.on("NDIS CRM Claim Draft", { refresh(frm) { if (frm.is_new()) { return; } } });'
	insert = r'''

        frm.add_custom_button(__("Create Claim Batch Draft Run"), function () {
            frappe.call({
                method: "ndis_crm.phase20_claim_batch_draft.create_claim_batch_draft_run_from_claim_draft",
                args: { claim_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating claim batch draft run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Claim Batch Draft Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Claim Batch Draft Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_claim_batch_draft_run) {
            frm.add_custom_button(__("Open Claim Batch Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Batch Draft Run", frm.doc.ndis_claim_batch_draft_run);
            }, __("Open"));
        }
'''
	return script.replace("\n    }\n});", insert + "\n    }\n});", 1)


def _submission_script():
	try:
		from ndis_crm.setup.phase19_sales_invoice_submission import _submission_script as previous_script

		script = previous_script()
	except Exception:
		script = 'frappe.ui.form.on("NDIS CRM Sales Invoice Submission Run", { refresh(frm) { if (frm.is_new()) { return; } } });'
	insert = r'''

        frm.add_custom_button(__("Create Claim Batch Draft Run"), function () {
            if (!frm.doc.claim_draft) {
                frappe.msgprint(__("No Claim Draft is linked to this submission run."));
                return;
            }
            frappe.call({
                method: "ndis_crm.phase20_claim_batch_draft.create_claim_batch_draft_run_from_claim_draft",
                args: { claim_draft: frm.doc.claim_draft },
                freeze: true,
                freeze_message: __("Creating claim batch draft run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Claim Batch Draft Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Claim Batch Draft Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_claim_batch_draft_run) {
            frm.add_custom_button(__("Open Claim Batch Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Batch Draft Run", frm.doc.ndis_claim_batch_draft_run);
            }, __("Open"));
        }
'''
	return script.replace("\n    }\n});", insert + "\n    }\n});", 1)


def _run_script():
	return r'''
frappe.ui.form.on("NDIS CRM Claim Batch Draft Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Claim Batch Draft Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase20_claim_batch_draft.generate_claim_batch_draft_lines",
                args: { claim_batch_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating claim batch draft lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Claim batch draft lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Claim Batch Draft Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase20_claim_batch_draft.validate_claim_batch_draft_run_readiness",
                args: { claim_batch_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating claim batch draft readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Claim Batch Draft Run validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Claim Batch Draft Creation"), function () {
            frappe.call({
                method: "ndis_crm.phase20_claim_batch_draft.mark_ready_for_claim_batch_draft_creation",
                args: { claim_batch_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for claim batch draft creation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for claim batch draft creation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Claim Batch Draft Run"), function () {
            frappe.call({
                method: "ndis_crm.phase20_claim_batch_draft.approve_claim_batch_draft_run",
                args: { claim_batch_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving claim batch draft run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Claim Batch Draft Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create Draft Claim Batch"), function () {
            frappe.confirm(
                __("This will create NDIS Claim Batch / Claim Line records in Draft only. It will not export, submit, remit, create payments, journals, manual GL, write-offs, or recovery cases."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase20_claim_batch_draft.create_draft_claim_batches",
                        args: { claim_batch_draft_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Creating draft claim batch...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Draft claim batch created"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.claim_draft) {
            frm.add_custom_button(__("Open Claim Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Draft", frm.doc.claim_draft);
            }, __("Open"));
        }

        if (frm.doc.sales_invoice_submission_run) {
            frm.add_custom_button(__("Open Sales Invoice Submission Run"), function () {
                frappe.set_route("Form", "NDIS CRM Sales Invoice Submission Run", frm.doc.sales_invoice_submission_run);
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
