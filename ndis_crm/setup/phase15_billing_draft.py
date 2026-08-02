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
BILLING_DRAFT_LINE = "NDIS CRM Billing Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_billing_draft_doctypes()
	create_custom_fields_phase15()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 15 billing draft bridge installed successfully.")


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
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 15 DocTypes: " + ", ".join(missing))
	print("Required Phase 15 DocTypes found.")


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


def create_billing_draft_doctypes():
	create_billing_draft_line()
	create_billing_draft()


def create_billing_draft_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Preparation Source Key", "preparation_source_key", "Data", read_only=1),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Billable Service", "billable_service_section", "Section Break"),
		make_field("Session Date", "session_date", "Date", in_list_view=1),
		make_field("Billable Date", "billable_date", "Date", reqd=1, in_list_view=1),
		make_field("Actual Start Time", "actual_start_time", "Time"),
		make_field("Actual End Time", "actual_end_time", "Time"),
		make_field("Delivered Hours", "delivered_hours", "Float"),
		make_field("Billable Quantity", "billable_quantity", "Float", reqd=1, in_list_view=1),
		make_field("Billing Unit", "billing_unit", "Data", default="Hour"),
		make_field("Billing Rate", "billing_rate", "Currency", reqd=1, in_list_view=1),
		make_field("Billing Amount", "billing_amount", "Currency", read_only=1, in_list_view=1),
		make_field("Rate Source", "rate_source", "Data"),
		make_field("GST Treatment", "gst_treatment", "Data"),
		make_field("Worker / Evidence Snapshot", "worker_evidence_section", "Section Break"),
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

	fields.append(make_field("Location / Risk", "location_risk_section", "Section Break"))
	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))
	fields += [
		make_field("Delivery Location", "delivery_location", "Data"),
		make_field("Requires Roster", "requires_roster", "Check", default=1),
		make_field("Requires House", "requires_house", "Check", default=0),
		make_field("Requires Clinical Review", "requires_clinical_review", "Check", default=0),
		make_field("Clinical Review Complete", "clinical_review_complete", "Check", default=0),
		make_field("Transport Required", "transport_required", "Check", default=0),
		make_field("Worker Skill Requirements", "worker_skill_requirements", "Small Text"),
		make_field("Billing / Claim Preparation", "billing_claim_prep_section", "Section Break"),
		make_field("Billing Preparation Required", "billing_preparation_required", "Check", default=1),
		make_field("Billing Preparation Ready", "billing_preparation_ready", "Check", default=0, in_list_view=1),
		make_field("Claim Preparation Ready", "claim_preparation_ready", "Check", default=0),
		make_field("Billing Hold", "billing_hold", "Check", default=0, in_list_view=1),
		make_field("Claim Hold", "claim_hold", "Check", default=0),
		make_field("Invoice Group Key", "invoice_group_key", "Data"),
		make_field("Proposed Invoice Reference", "proposed_invoice_reference", "Data"),
		make_field("Review Status", "review_status_section", "Section Break"),
		make_field("Line Ready for Invoice Draft", "line_ready_for_invoice_draft", "Check", default=0, in_list_view=1),
		make_field("Billing Draft Status", "billing_draft_status", "Select", options="Draft\nReady\nApproved\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(name=BILLING_DRAFT_LINE, fields=fields, istable=1)


def create_billing_draft():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-BILL-DRAFT-.YYYY.-.#####", default="NDIS-BILL-DRAFT-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Billing Review\nBilling Draft Approved\nReturned to Downstream Preparation\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Billing Draft Ready", "billing_draft_ready", "Check", read_only=1, in_list_view=1),
		make_field("Invoice Creation Allowed", "invoice_creation_allowed", "Check", default=0, read_only=1, description="Always blocked in Phase 15."),
		make_field("Billing Summary", "billing_summary_section", "Section Break"),
		make_field("Billing Line Count", "billing_line_count", "Int", read_only=1),
		make_field("Billable Quantity Total", "billable_quantity_total", "Float", read_only=1),
		make_field("Billing Amount Total", "billing_amount_total", "Currency", read_only=1),
		make_field("Billing Ready Count", "billing_ready_count", "Int", read_only=1),
		make_field("Billing Approved Count", "billing_approved_count", "Int", read_only=1),
		make_field("Billing Hold Count", "billing_hold_count", "Int", read_only=1),
		make_field("Manual Rate Count", "manual_rate_count", "Int", read_only=1),
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
		make_field("NDIS CRM Downstream Preparation", "downstream_preparation", "Link", options=DOWNSTREAM_PREPARATION, reqd=1, in_list_view=1),
	]
	if doctype_exists(ATTENDANCE_DRAFT):
		fields.append(make_field("NDIS CRM Attendance Draft", "attendance_draft", "Link", options=ATTENDANCE_DRAFT))
	else:
		fields.append(make_field("NDIS CRM Attendance Draft", "attendance_draft", "Data"))
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
		make_field("Billing Window", "billing_window_section", "Section Break"),
		make_field("Billing Period Start", "billing_period_start", "Date", in_list_view=1),
		make_field("Billing Period End", "billing_period_end", "Date", in_list_view=1),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Billing Owner", "billing_owner", "Link", options="User", in_list_view=1),
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
		make_field("Billing Lines", "billing_lines_section", "Section Break"),
		make_field("Billing Lines", "billing_lines", "Table", options=BILLING_DRAFT_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Billing Draft Notes", "billing_draft_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(name=BILLING_DRAFT, fields=fields, autoname="naming_series:", title_field="participant_name")


def create_custom_fields_phase15():
	deal_fields = [
		{"fieldname": "billing_draft_section", "label": "NDIS Billing Draft", "fieldtype": "Section Break", "insert_after": "attendance_draft_ready"},
		{"fieldname": "ndis_billing_draft_required", "label": "Billing Draft Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "billing_draft_section", "description": "Optional guard only. Normally billing draft happens after participant activation and service delivery."},
		{"fieldname": "ndis_billing_draft", "label": "NDIS CRM Billing Draft", "fieldtype": "Link", "options": BILLING_DRAFT, "read_only": 1, "insert_after": "ndis_billing_draft_required"},
		{"fieldname": "billing_draft_status", "label": "Billing Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_billing_draft"},
		{"fieldname": "billing_draft_ready", "label": "Billing Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "billing_draft_status"},
	]
	shared_fields = [
		{"fieldname": "billing_draft_section", "label": "NDIS Billing Draft", "fieldtype": "Section Break", "insert_after": "attendance_draft_ready"},
		{"fieldname": "ndis_billing_draft", "label": "NDIS CRM Billing Draft", "fieldtype": "Link", "options": BILLING_DRAFT, "read_only": 1, "insert_after": "billing_draft_section"},
		{"fieldname": "billing_draft_status", "label": "Billing Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_billing_draft"},
		{"fieldname": "billing_draft_ready", "label": "Billing Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "billing_draft_status"},
	]
	downstream_fields = [
		{"fieldname": "billing_draft_section", "label": "NDIS Billing Draft", "fieldtype": "Section Break", "insert_after": "downstream_ready"},
		{"fieldname": "ndis_billing_draft", "label": "NDIS CRM Billing Draft", "fieldtype": "Link", "options": BILLING_DRAFT, "read_only": 1, "insert_after": "billing_draft_section"},
		{"fieldname": "billing_draft_status", "label": "Billing Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_billing_draft"},
		{"fieldname": "billing_draft_ready", "label": "Billing Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "billing_draft_status"},
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
		DOWNSTREAM_PREPARATION: downstream_fields,
		INTAKE: shared_fields,
	}
	if doctype_exists(ATTENDANCE_DRAFT):
		custom_fields[ATTENDANCE_DRAFT] = shared_fields

	was_in_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		create_custom_fields(custom_fields, update=True)
	finally:
		frappe.flags.in_install = was_in_install
	print("Created / updated Phase 15 billing draft custom fields.")


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
			"NDIS CRM Downstream Preparation Actions",
			{"dt": DOWNSTREAM_PREPARATION, "view": "Form", "enabled": 1, "script": _downstream_script()},
		)
		if doctype_exists(ATTENDANCE_DRAFT):
			upsert_doc(
				"Client Script",
				"NDIS CRM Attendance Draft Actions",
				{"dt": ATTENDANCE_DRAFT, "view": "Form", "enabled": 1, "script": _attendance_script()},
			)
		upsert_doc(
			"Client Script",
			"NDIS CRM Billing Draft Actions",
			{"dt": BILLING_DRAFT, "view": "Form", "enabled": 1, "script": _billing_script()},
		)


def _deal_script():
	from ndis_crm.setup.phase14_attendance_draft import _deal_script as phase14_deal_script

	script = phase14_deal_script()
	insert = r''',
      {
        label: "Create Billing Draft",
        onClick: () => {
          call("ndis_crm.phase15_billing_draft.create_billing_draft_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Billing Draft Created" : "Existing Billing Draft Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-billing-draft/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Billing Draft",
        onClick: () => {
          if (doc.ndis_billing_draft) {
            window.open(`/app/ndis-crm-billing-draft/${doc.ndis_billing_draft}`, "_blank")
          } else {
            createToast({ title: "No Billing Draft linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _downstream_script():
	from ndis_crm.setup.phase14_attendance_draft import _downstream_script as phase14_downstream_script

	script = phase14_downstream_script()
	insert = r'''

        frm.add_custom_button(__("Create Billing Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase15_billing_draft.create_billing_draft_from_downstream_preparation",
                args: { downstream_preparation: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating billing draft...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Billing Draft created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Billing Draft", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_billing_draft) {
            frm.add_custom_button(__("Open Billing Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Billing Draft", frm.doc.ndis_billing_draft);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.ndis_attendance_draft)", insert + "\n        if (frm.doc.ndis_attendance_draft)")


def _attendance_script():
	from ndis_crm.setup.phase14_attendance_draft import _attendance_script as phase14_attendance_script

	script = phase14_attendance_script()
	insert = r'''

        frm.add_custom_button(__("Create Billing Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase15_billing_draft.create_billing_draft_from_attendance_draft",
                args: { attendance_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating billing draft...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Billing Draft created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Billing Draft", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_billing_draft) {
            frm.add_custom_button(__("Open Billing Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Billing Draft", frm.doc.ndis_billing_draft);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.downstream_preparation)", insert + "\n        if (frm.doc.downstream_preparation)")


def _billing_script():
	return r'''
frappe.ui.form.on("NDIS CRM Billing Draft", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Billing Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase15_billing_draft.generate_billing_lines",
                args: { billing_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating billing lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Billing lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Billing Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase15_billing_draft.validate_billing_draft_readiness",
                args: { billing_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating billing draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Billing draft validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Billing Review"), function () {
            frappe.call({
                method: "ndis_crm.phase15_billing_draft.mark_ready_for_billing_review",
                args: { billing_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for billing review...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for billing review"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Billing Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase15_billing_draft.approve_billing_draft",
                args: { billing_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving billing draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Billing Draft approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.downstream_preparation) {
            frm.add_custom_button(__("Open Downstream Preparation"), function () {
                frappe.set_route("Form", "NDIS CRM Downstream Preparation", frm.doc.downstream_preparation);
            }, __("Open"));
        }

        if (frm.doc.attendance_draft) {
            frm.add_custom_button(__("Open Attendance Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Attendance Draft", frm.doc.attendance_draft);
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
