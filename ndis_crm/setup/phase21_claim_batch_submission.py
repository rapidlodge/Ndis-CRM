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
CLAIM_BATCH_SUBMISSION_LINE = "NDIS CRM Claim Batch Submission Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_submission_doctypes()
	create_custom_fields_phase21()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 21 Claim Batch submission/export gate installed successfully.")


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
		"Sales Invoice",
		"NDIS Claim Batch",
		"NDIS Claim Line",
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 21 DocTypes: " + ", ".join(missing))
	print("Required Phase 21 DocTypes found.")


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


def create_submission_doctypes():
	create_submission_line()
	create_submission_run()


def create_submission_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Claim Batch Source Key", "claim_batch_source_key", "Data", read_only=1),
		make_field("NDIS Claim Batch", "ndis_claim_batch", "Link", options="NDIS Claim Batch", in_list_view=1),
		make_field("NDIS Claim Line", "ndis_claim_line", "Link", options="NDIS Claim Line"),
		make_field("Claim Batch Docstatus", "claim_batch_docstatus", "Int", read_only=1),
		make_field("Claim Line Docstatus", "claim_line_docstatus", "Int", read_only=1),
		make_field("Claim Batch Status", "claim_batch_status", "Data", read_only=1),
		make_field("Claim Line Status", "claim_line_status", "Data", read_only=1),
		make_field("Service Snapshot", "service_snapshot_section", "Section Break"),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", in_list_view=1),
		make_field("Sales Invoice Docstatus", "sales_invoice_docstatus", "Int", read_only=1),
		make_field("Sales Invoice Status", "sales_invoice_status", "Data", read_only=1),
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
		make_field("Review Controls", "review_controls_section", "Section Break"),
		make_field("Claim Batch Draft Source Ready", "claim_batch_draft_source_ready", "Check", default=0),
		make_field("Finance Claim Review Complete", "finance_claim_review_complete", "Check", default=0),
		make_field("Export Mapping Review Complete", "export_mapping_review_complete", "Check", default=0),
		make_field("Submission Authorized", "submission_authorized", "Check", default=0),
		make_field("Claim Export Ready", "claim_export_ready", "Check", default=0),
		make_field("Claim Submission Ready", "claim_submission_ready", "Check", default=0),
		make_field("Submission Hold", "submission_hold", "Check", default=1, in_list_view=1),
		make_field("Submission Hold Reason", "submission_hold_reason", "Small Text"),
		make_field("Line Status", "line_status_section", "Section Break"),
		make_field("Line Ready for Claim Batch Export", "line_ready_for_claim_batch_export", "Check", default=0, in_list_view=1),
		make_field("Submission Status", "submission_status", "Select", options="Draft\nReady\nApproved\nExport Ready\nExported\nSubmitted\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Prepared By", "prepared_by", "Link", options="User", read_only=1),
		make_field("Prepared On", "prepared_on", "Datetime", read_only=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(CLAIM_BATCH_SUBMISSION_LINE, fields, istable=1)


def create_submission_run():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-CLAIM-SUB-RUN-.YYYY.-.#####", default="NDIS-CLAIM-SUB-RUN-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Claim Batch Export Review\nClaim Batch Submission Run Approved\nClaim Batch Export Ready\nReturned to Claim Batch Draft Run\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Claim Batch Submission Run Ready", "claim_batch_submission_run_ready", "Check", read_only=1, in_list_view=1),
		make_field("Claim Export Allowed", "claim_export_allowed", "Check", default=0, description="Must be ticked manually after approval before marking claim batch export-ready."),
		make_field("Claim Submission Allowed", "claim_submission_allowed", "Check", default=0, description="Blocked in Phase 21. Actual submission belongs to a later phase."),
		make_field("Summary", "summary_section", "Section Break"),
		make_field("Submission Line Count", "submission_line_count", "Int", read_only=1),
		make_field("Claim Batch Count", "claim_batch_count", "Int", read_only=1),
		make_field("Claim Amount Total", "claim_amount_total", "Currency", read_only=1),
		make_field("Claim Batch Export Ready Count", "claim_batch_export_ready_count", "Int", read_only=1),
		make_field("Submission Authorized Count", "submission_authorized_count", "Int", read_only=1),
		make_field("Claim Batch Submission Hold Count", "claim_batch_submission_hold_count", "Int", read_only=1),
		make_field("Missing Claim Batch Count", "missing_claim_batch_count", "Int", read_only=1),
		make_field("Missing Claim Line Count", "missing_claim_line_count", "Int", read_only=1),
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
		make_field("NDIS CRM Claim Batch Draft Run", "claim_batch_draft_run", "Link", options=CLAIM_BATCH_DRAFT_RUN, reqd=1, in_list_view=1),
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
		make_field("Claim Batch Submission Owner", "claim_batch_submission_owner", "Link", options="User", in_list_view=1),
		make_field("Claim Batch Owner", "claim_batch_owner", "Link", options="User"),
		make_field("Claim Owner", "claim_owner", "Link", options="User"),
		make_field("Billing Owner", "billing_owner", "Link", options="User"),
		make_field("Submission Lines", "submission_lines_section", "Section Break"),
		make_field("Submission Lines", "submission_lines", "Table", options=CLAIM_BATCH_SUBMISSION_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Submission Notes", "submission_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(CLAIM_BATCH_SUBMISSION_RUN, fields, autoname="naming_series:", title_field="participant_name")


def _link_fields(insert_after):
	return [
		{"fieldname": "claim_batch_submission_section", "label": "NDIS Claim Batch Submission Run", "fieldtype": "Section Break", "insert_after": insert_after},
		{"fieldname": "ndis_claim_batch_submission_run", "label": "NDIS CRM Claim Batch Submission Run", "fieldtype": "Link", "options": CLAIM_BATCH_SUBMISSION_RUN, "read_only": 1, "insert_after": "claim_batch_submission_section"},
		{"fieldname": "claim_batch_submission_status", "label": "Claim Batch Submission Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_claim_batch_submission_run"},
		{"fieldname": "claim_batch_submission_ready", "label": "Claim Batch Submission Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "claim_batch_submission_status"},
	]


def create_custom_fields_phase21():
	deal_fields = [
		{"fieldname": "claim_batch_submission_section", "label": "NDIS Claim Batch Submission Run", "fieldtype": "Section Break", "insert_after": "claim_batch_draft_ready"},
		{"fieldname": "ndis_claim_batch_submission_run_required", "label": "Claim Batch Submission Run Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "claim_batch_submission_section", "description": "Optional guard only. Normally claim submission/export happens after service delivery, invoice submission, and draft claim batch creation."},
		{"fieldname": "ndis_claim_batch_submission_run", "label": "NDIS CRM Claim Batch Submission Run", "fieldtype": "Link", "options": CLAIM_BATCH_SUBMISSION_RUN, "read_only": 1, "insert_after": "ndis_claim_batch_submission_run_required"},
		{"fieldname": "claim_batch_submission_status", "label": "Claim Batch Submission Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_claim_batch_submission_run"},
		{"fieldname": "claim_batch_submission_ready", "label": "Claim Batch Submission Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "claim_batch_submission_status"},
	]
	custom_fields = {
		CRM_DEAL: deal_fields,
		HANDOVER: _link_fields("claim_batch_draft_ready"),
		FINANCE_ONBOARDING: _link_fields("claim_batch_draft_ready"),
		OPERATIONS_SETUP: _link_fields("claim_batch_draft_ready"),
		SCHEDULE_DRAFT: _link_fields("claim_batch_draft_ready"),
		ROSTER_REQUEST: _link_fields("claim_batch_draft_ready"),
		SERVICE_FILE: _link_fields("claim_batch_draft_ready"),
		SESSION_DRAFT: _link_fields("claim_batch_draft_ready"),
		EVIDENCE_REVIEW: _link_fields("claim_batch_draft_ready"),
		DOWNSTREAM_PREPARATION: _link_fields("claim_batch_draft_ready"),
		BILLING_DRAFT: _link_fields("claim_batch_draft_ready"),
		CLAIM_DRAFT: _link_fields("claim_batch_draft_ready"),
		INVOICE_DRAFT: _link_fields("claim_batch_draft_ready"),
		SALES_INVOICE_DRAFT_RUN: _link_fields("claim_batch_draft_ready"),
		SALES_INVOICE_SUBMISSION_RUN: _link_fields("claim_batch_draft_ready"),
		CLAIM_BATCH_DRAFT_RUN: _link_fields("claim_batch_draft_ready"),
		INTAKE: _link_fields("claim_batch_draft_ready"),
	}
	if doctype_exists(ATTENDANCE_DRAFT):
		custom_fields[ATTENDANCE_DRAFT] = _link_fields("claim_batch_draft_ready")
	frappe.flags.in_install = True
	try:
		create_custom_fields(custom_fields, update=True)
	finally:
		frappe.flags.in_install = False
	print("Created / updated Phase 21 claim batch submission custom fields.")


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
		upsert_doc("Client Script", "NDIS CRM Claim Batch Draft Run Actions", {"dt": CLAIM_BATCH_DRAFT_RUN, "view": "Form", "enabled": 1, "script": _draft_run_script()})
		upsert_doc("Client Script", "NDIS CRM Claim Batch Submission Run Actions", {"dt": CLAIM_BATCH_SUBMISSION_RUN, "view": "Form", "enabled": 1, "script": _run_script()})


def _deal_script():
	try:
		from ndis_crm.setup.phase20_claim_batch_draft import _deal_script as previous_script

		script = previous_script()
	except Exception:
		script = "function setupForm({ doc, call, createToast }) {\n  return { actions: [] }\n}"
	insert = r'''
      {
        label: "Create Claim Batch Submission Run",
        onClick: () => {
          call("ndis_crm.phase21_claim_batch_submission.create_claim_batch_submission_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Claim Batch Submission Run Created" : "Existing Submission Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-claim-batch-submission-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Claim Batch Submission Run",
        onClick: () => {
          if (doc.ndis_claim_batch_submission_run) {
            window.open(`/app/ndis-crm-claim-batch-submission-run/${doc.ndis_claim_batch_submission_run}`, "_blank")
          } else {
            createToast({ title: "No Claim Batch Submission Run linked yet", icon: "info" })
          }
        }
      }
'''.rstrip()
	return script.replace("\n    ]", ",\n" + insert + "\n    ]", 1)


def _draft_run_script():
	try:
		from ndis_crm.setup.phase20_claim_batch_draft import _run_script as previous_script

		script = previous_script()
	except Exception:
		script = 'frappe.ui.form.on("NDIS CRM Claim Batch Draft Run", { refresh(frm) { if (frm.is_new()) { return; } } });'
	insert = r'''

        frm.add_custom_button(__("Create Claim Batch Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase21_claim_batch_submission.create_claim_batch_submission_run_from_draft_run",
                args: { claim_batch_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating claim batch submission run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Claim Batch Submission Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Claim Batch Submission Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_claim_batch_submission_run) {
            frm.add_custom_button(__("Open Claim Batch Submission Run"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Batch Submission Run", frm.doc.ndis_claim_batch_submission_run);
            }, __("Open"));
        }
'''
	return script.replace("\n    }\n});", insert + "\n    }\n});", 1)


def _run_script():
	return r'''
frappe.ui.form.on("NDIS CRM Claim Batch Submission Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Submission Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase21_claim_batch_submission.generate_claim_batch_submission_lines",
                args: { claim_batch_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating claim batch submission lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Submission Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase21_claim_batch_submission.validate_claim_batch_submission_readiness",
                args: { claim_batch_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating claim batch submission readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Export Review"), function () {
            frappe.call({
                method: "ndis_crm.phase21_claim_batch_submission.mark_ready_for_claim_batch_export_review",
                args: { claim_batch_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for export review...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for export review"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase21_claim_batch_submission.approve_claim_batch_submission_run",
                args: { claim_batch_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving submission run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Claim Batch Export Ready"), function () {
            frappe.confirm(
                __("This will only mark the draft claim batch as export-ready. It will not create an export file, lodge the claim, create payment, journal, manual GL, remittance, write-off, or recovery."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase21_claim_batch_submission.mark_claim_batch_export_ready",
                        args: { claim_batch_submission_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Marking claim batch export-ready...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Claim Batch marked export-ready"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.claim_batch_draft_run) {
            frm.add_custom_button(__("Open Claim Batch Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Claim Batch Draft Run", frm.doc.claim_batch_draft_run);
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
