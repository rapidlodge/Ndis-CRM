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
SESSION_DRAFT_LINE = "NDIS CRM Service Session Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_session_doctypes()
	create_custom_fields_phase11()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 11 service delivery session draft bridge installed successfully.")


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
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 11 DocTypes: " + ", ".join(missing))

	print("Required Phase 11 DocTypes found.")


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


def create_session_doctypes():
	create_session_draft_line()
	create_session_draft()


def create_session_draft_line():
	fields = [
		make_field("Service", "service_section", "Section Break"),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Service Status", "service_status", "Data"),
		make_field("Session Plan", "session_plan_section", "Section Break"),
		make_field("Session Date", "session_date", "Date", reqd=1, in_list_view=1),
		make_field("Planned Start Time", "planned_start_time", "Time", in_list_view=1),
		make_field("Planned End Time", "planned_end_time", "Time", in_list_view=1),
		make_field("Planned Hours", "planned_hours", "Float", in_list_view=1),
		make_field("Workers Required", "workers_required", "Int", default=1),
		make_field("Estimated Worker Hours", "estimated_worker_hours", "Float"),
		make_field("Frequency", "frequency", "Data"),
		make_field("Days of Week", "days_of_week", "Data"),
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
		make_field("Support Ratio", "support_ratio", "Data"),
		make_field("Overnight Model", "overnight_model", "Data"),
		make_field("Requires Roster", "requires_roster", "Check", default=1),
		make_field("Requires House", "requires_house", "Check", default=0),
		make_field("Requires Clinical Review", "requires_clinical_review", "Check", default=0),
		make_field("Clinical Review Complete", "clinical_review_complete", "Check", default=0),
		make_field("Transport Required", "transport_required", "Check", default=0),
		make_field("Worker Skill Requirements", "worker_skill_requirements", "Small Text"),
		make_field("Clinical / Risk Notes", "clinical_risk_notes", "Small Text"),
		make_field("Roster Pattern Notes", "roster_pattern_notes", "Small Text"),
		make_field("Readiness / Billing Precheck", "readiness_billing_section", "Section Break"),
		make_field("Billing Precheck Required", "billing_precheck_required", "Check", default=1),
		make_field("Billing Precheck Ready", "billing_precheck_ready", "Check", default=0),
		make_field("Line Ready for Delivery", "line_ready_for_delivery", "Check", default=0, in_list_view=1),
		make_field("Session Status", "session_status", "Select", options="Draft\nReady\nApproved\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]

	create_doctype_if_missing(name=SESSION_DRAFT_LINE, fields=fields, istable=1)


def create_session_draft():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-SESSION-DRAFT-.YYYY.-.#####", default="NDIS-SESSION-DRAFT-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Service Delivery\nSession Draft Approved\nReturned to Service File\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Session Draft Ready", "session_draft_ready", "Check", read_only=1, in_list_view=1),
		make_field("Session Line Count", "session_line_count", "Int", read_only=1),
		make_field("Source Links", "source_links_section", "Section Break"),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
		make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
		make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER),
		make_field("NDIS CRM Finance Onboarding", "finance_onboarding", "Link", options=FINANCE_ONBOARDING),
		make_field("NDIS CRM Operations Setup", "operations_setup", "Link", options=OPERATIONS_SETUP),
		make_field("NDIS CRM Service Schedule Draft", "service_schedule_draft", "Link", options=SCHEDULE_DRAFT),
		make_field("NDIS CRM Roster Build Request", "roster_build_request", "Link", options=ROSTER_REQUEST),
		make_field("NDIS Participant Service File", "participant_service_file", "Link", options=SERVICE_FILE, reqd=1, in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
	]

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
		make_field("Generation Window", "generation_window_section", "Section Break"),
		make_field("Generation Start Date", "generation_start_date", "Date", in_list_view=1),
		make_field("Generation End Date", "generation_end_date", "Date", in_list_view=1),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Session Owner", "session_owner", "Link", options="User", in_list_view=1),
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
		make_field("Session Lines", "session_lines_section", "Section Break"),
		make_field("Session Lines", "session_lines", "Table", options=SESSION_DRAFT_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Session Draft Notes", "session_draft_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=SESSION_DRAFT,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def create_custom_fields_phase11():
	deal_fields = [
		{"fieldname": "service_session_section", "label": "NDIS Service Session Draft", "fieldtype": "Section Break", "insert_after": "participant_service_file_ready"},
		{"fieldname": "ndis_service_session_draft_required", "label": "Service Session Draft Required", "fieldtype": "Check", "default": 1, "insert_after": "service_session_section"},
		{"fieldname": "ndis_service_session_draft", "label": "NDIS CRM Service Session Draft", "fieldtype": "Link", "options": SESSION_DRAFT, "read_only": 1, "insert_after": "ndis_service_session_draft_required"},
		{"fieldname": "service_session_status", "label": "Service Session Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_service_session_draft"},
		{"fieldname": "service_session_ready", "label": "Service Session Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "service_session_status"},
	]
	shared_fields = [
		{"fieldname": "service_session_section", "label": "NDIS Service Session Draft", "fieldtype": "Section Break", "insert_after": "participant_service_file_ready"},
		{"fieldname": "ndis_service_session_draft", "label": "NDIS CRM Service Session Draft", "fieldtype": "Link", "options": SESSION_DRAFT, "read_only": 1, "insert_after": "service_session_section"},
		{"fieldname": "service_session_status", "label": "Service Session Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_service_session_draft"},
		{"fieldname": "service_session_ready", "label": "Service Session Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "service_session_status"},
	]
	service_file_fields = [
		{"fieldname": "service_session_section", "label": "NDIS Service Session Draft", "fieldtype": "Section Break", "insert_after": "service_file_ready"},
		{"fieldname": "ndis_service_session_draft", "label": "NDIS CRM Service Session Draft", "fieldtype": "Link", "options": SESSION_DRAFT, "read_only": 1, "insert_after": "service_session_section"},
		{"fieldname": "service_session_status", "label": "Service Session Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_service_session_draft"},
		{"fieldname": "service_session_ready", "label": "Service Session Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "service_session_status"},
	]

	was_in_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		create_custom_fields(
			{
				CRM_DEAL: deal_fields,
				HANDOVER: shared_fields,
				FINANCE_ONBOARDING: shared_fields,
				OPERATIONS_SETUP: shared_fields,
				SCHEDULE_DRAFT: shared_fields,
				ROSTER_REQUEST: shared_fields,
				SERVICE_FILE: service_file_fields,
				INTAKE: shared_fields,
			},
			update=True,
		)
	finally:
		frappe.flags.in_install = was_in_install

	print("Created / updated Phase 11 service session custom fields.")


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
	deal_script = _deal_script()
	service_file_script = _service_file_script()
	session_draft_script = _session_draft_script()

	upsert_doc(
		"CRM Form Script",
		"NDIS CRM Deal Actions",
		{"dt": CRM_DEAL, "view": "Form", "enabled": 1, "is_standard": 0, "script": deal_script},
	)

	if frappe.db.exists("DocType", "Client Script"):
		upsert_doc(
			"Client Script",
			"NDIS Participant Service File Actions",
			{"dt": SERVICE_FILE, "view": "Form", "enabled": 1, "script": service_file_script},
		)
		upsert_doc(
			"Client Script",
			"NDIS CRM Service Session Draft Actions",
			{"dt": SESSION_DRAFT, "view": "Form", "enabled": 1, "script": session_draft_script},
		)


def _deal_script():
	from ndis_crm.setup.phase10_service_file import _deal_script as phase10_deal_script

	script = phase10_deal_script()
	insert = r''',
      {
        label: "Create Service Session Draft",
        onClick: () => {
          call("ndis_crm.phase11_service_sessions.create_service_session_draft_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Service Session Draft Created" : "Existing Session Draft Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-service-session-draft/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Service Session Draft",
        onClick: () => {
          if (doc.ndis_service_session_draft) {
            window.open(`/app/ndis-crm-service-session-draft/${doc.ndis_service_session_draft}`, "_blank")
          } else {
            createToast({ title: "No Service Session Draft linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _service_file_script():
	from ndis_crm.setup.phase10_service_file import _service_file_script as phase10_service_file_script

	script = phase10_service_file_script()
	insert = r'''

        frm.add_custom_button(__("Create Service Session Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase11_service_sessions.create_service_session_draft_from_service_file",
                args: { service_file: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating service session draft...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Service Session Draft created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Service Session Draft", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_service_session_draft) {
            frm.add_custom_button(__("Open Service Session Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Service Session Draft", frm.doc.ndis_service_session_draft);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.crm_deal)", insert + "\n        if (frm.doc.crm_deal)")


def _session_draft_script():
	return r'''
frappe.ui.form.on("NDIS CRM Service Session Draft", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Session Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase11_service_sessions.generate_session_lines",
                args: { session_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating session lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Session lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Session Draft Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase11_service_sessions.validate_session_draft_readiness",
                args: { session_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating session draft readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Session draft readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Service Delivery"), function () {
            frappe.call({
                method: "ndis_crm.phase11_service_sessions.mark_ready_for_service_delivery",
                args: { session_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for service delivery...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Service Delivery"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Session Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase11_service_sessions.approve_session_draft",
                args: { session_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving service session draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Session Draft approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.participant_service_file) {
            frm.add_custom_button(__("Open Participant Service File"), function () {
                frappe.set_route("Form", "NDIS Participant Service File", frm.doc.participant_service_file);
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
