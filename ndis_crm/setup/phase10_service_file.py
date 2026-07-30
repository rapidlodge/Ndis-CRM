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
SERVICE_FILE_SERVICE = "NDIS Participant Service File Service"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_service_file_doctypes()
	create_custom_fields_phase10()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 10 active participant service file installed successfully.")


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
		"NDIS Service Line",
		"CRM Form Script",
	]

	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 10 DocTypes: " + ", ".join(missing))

	print("Required Phase 10 DocTypes found.")


def make_field(label, fieldname, fieldtype, **kwargs):
	field = {
		"label": label,
		"fieldname": fieldname,
		"fieldtype": fieldtype,
	}
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
		{
			"role": "NDIS Intake Officer",
			"read": 1,
			"write": 1,
			"create": 1,
			"email": 1,
			"print": 1,
			"report": 1,
		},
		{
			"role": "NDIS Service Manager",
			"read": 1,
			"write": 1,
			"create": 1,
			"email": 1,
			"print": 1,
			"report": 1,
		},
		{
			"role": "NDIS Plan Management Officer",
			"read": 1,
			"write": 1,
			"create": 1,
			"email": 1,
			"print": 1,
			"report": 1,
		},
		{
			"role": "NDIS CRM Read Only",
			"read": 1,
			"export": 1,
			"print": 1,
			"report": 1,
		},
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


def create_service_file_doctypes():
	create_service_file_service()
	create_service_file()


def create_service_file_service():
	fields = [
		make_field("Service", "service_section", "Section Break"),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Budget Type", "budget_type", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data", in_list_view=1),
		make_field("Service Status", "service_status", "Select", options="Pending Activation\nReady to Commence\nActive\nOn Hold\nEnded\nCancelled", default="Pending Activation", in_list_view=1),
		make_field("Service Start Date", "service_start_date", "Date", in_list_view=1),
		make_field("Service End Date", "service_end_date", "Date"),
		make_field("Finance Links", "finance_links_section", "Section Break"),
	]

	if doctype_exists(NDIS_SERVICE_TYPE):
		fields.append(make_field("Finance Service Type", "finance_service_type", "Link", options=NDIS_SERVICE_TYPE))
	else:
		fields.append(make_field("Finance Service Type", "finance_service_type", "Data"))

	if doctype_exists(NDIS_SUPPORT_ITEM):
		fields.append(make_field("Support Item", "support_item", "Link", options=NDIS_SUPPORT_ITEM))
	else:
		fields.append(make_field("Support Item", "support_item", "Data"))

	if doctype_exists(PLAN_BUDGET):
		fields.append(make_field("NDIS Plan Budget", "plan_budget", "Link", options=PLAN_BUDGET))

	if doctype_exists(SERVICE_BOOKING):
		fields.append(make_field("NDIS Service Booking", "service_booking", "Link", options=SERVICE_BOOKING))

	fields += [
		make_field("Delivery / Roster Snapshot", "delivery_roster_section", "Section Break"),
		make_field("Requires Roster", "requires_roster", "Check", default=0),
		make_field("Frequency", "frequency", "Data"),
		make_field("Days of Week", "days_of_week", "Data"),
		make_field("Shifts Per Week", "shifts_per_week", "Float"),
		make_field("Hours Per Shift", "hours_per_shift", "Float"),
		make_field("Estimated Weekly Hours", "estimated_weekly_hours", "Float"),
		make_field("Workers Required", "workers_required", "Int"),
		make_field("Estimated Worker Hours", "estimated_worker_hours", "Float"),
		make_field("Start Time", "start_time", "Time"),
		make_field("End Time", "end_time", "Time"),
		make_field("Location / Risk Snapshot", "location_risk_section", "Section Break"),
		make_field("Requires House", "requires_house", "Check", default=0),
	]

	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))

	fields += [
		make_field("Delivery Location", "delivery_location", "Data"),
		make_field("Support Ratio", "support_ratio", "Data"),
		make_field("Overnight Model", "overnight_model", "Data"),
		make_field("Requires Clinical Review", "requires_clinical_review", "Check", default=0),
		make_field("Clinical Review Complete", "clinical_review_complete", "Check", default=0),
		make_field("Transport Required", "transport_required", "Check", default=0),
		make_field("Worker Skill Requirements", "worker_skill_requirements", "Small Text"),
		make_field("Clinical / Risk Notes", "clinical_risk_notes", "Small Text"),
		make_field("Roster Pattern Notes", "roster_pattern_notes", "Small Text"),
		make_field("Bridge Status", "bridge_status_section", "Section Break"),
		make_field("Operations Setup Status", "operations_setup_status", "Data", read_only=1),
		make_field("Schedule Status", "schedule_status", "Data", read_only=1),
		make_field("Schedule Ready", "schedule_ready", "Check", read_only=1),
		make_field("Roster Request Status", "roster_request_status", "Data", read_only=1),
		make_field("Roster Build Ready", "roster_build_ready", "Check", read_only=1),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Service Notes", "service_notes", "Small Text"),
	]

	create_doctype_if_missing(name=SERVICE_FILE_SERVICE, fields=fields, istable=1)


def create_service_file():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-SERVICE-FILE-.YYYY.-.#####", default="NDIS-SERVICE-FILE-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nReady for Activation\nActive Service File\nOn Hold\nClosed\nReturned to Pre-Service", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Service File Ready", "service_file_ready", "Check", read_only=1, in_list_view=1),
		make_field("Source Links", "source_links_section", "Section Break"),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
		make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
		make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER),
		make_field("NDIS CRM Finance Onboarding", "finance_onboarding", "Link", options=FINANCE_ONBOARDING),
		make_field("NDIS CRM Operations Setup", "operations_setup", "Link", options=OPERATIONS_SETUP),
		make_field("NDIS CRM Service Schedule Draft", "service_schedule_draft", "Link", options=SCHEDULE_DRAFT),
		make_field("NDIS CRM Roster Build Request", "roster_build_request", "Link", options=ROSTER_REQUEST, reqd=1, in_list_view=1),
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
		make_field("Service Commencement Date", "service_commencement_date", "Date", in_list_view=1),
		make_field("Ownership", "ownership_section", "Section Break"),
		make_field("Service File Owner", "service_file_owner", "Link", options="User", in_list_view=1),
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
		make_field("Services", "services_section", "Section Break"),
		make_field("Services", "services", "Table", options=SERVICE_FILE_SERVICE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Service File Notes", "service_file_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=SERVICE_FILE,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def create_custom_fields_phase10():
	deal_fields = [
		{"fieldname": "participant_service_file_section", "label": "NDIS Participant Service File", "fieldtype": "Section Break", "insert_after": "roster_build_ready"},
		{"fieldname": "ndis_participant_service_file_required", "label": "Participant Service File Required", "fieldtype": "Check", "default": 1, "insert_after": "participant_service_file_section"},
		{"fieldname": "ndis_participant_service_file", "label": "NDIS Participant Service File", "fieldtype": "Link", "options": SERVICE_FILE, "read_only": 1, "insert_after": "ndis_participant_service_file_required"},
		{"fieldname": "participant_service_file_status", "label": "Participant Service File Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_participant_service_file"},
		{"fieldname": "participant_service_file_ready", "label": "Participant Service File Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "participant_service_file_status"},
	]
	shared_fields = [
		{"fieldname": "participant_service_file_section", "label": "NDIS Participant Service File", "fieldtype": "Section Break", "insert_after": "roster_build_ready"},
		{"fieldname": "ndis_participant_service_file", "label": "NDIS Participant Service File", "fieldtype": "Link", "options": SERVICE_FILE, "read_only": 1, "insert_after": "participant_service_file_section"},
		{"fieldname": "participant_service_file_status", "label": "Participant Service File Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_participant_service_file"},
		{"fieldname": "participant_service_file_ready", "label": "Participant Service File Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "participant_service_file_status"},
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
				INTAKE: shared_fields,
			},
			update=True,
		)
	finally:
		frappe.flags.in_install = was_in_install

	print("Created / updated Phase 10 participant service file custom fields.")


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
	roster_request_script = _roster_request_script()
	service_file_script = _service_file_script()

	upsert_doc(
		"CRM Form Script",
		"NDIS CRM Deal Actions",
		{
			"dt": CRM_DEAL,
			"view": "Form",
			"enabled": 1,
			"is_standard": 0,
			"script": deal_script,
		},
	)

	if frappe.db.exists("DocType", "Client Script"):
		upsert_doc(
			"Client Script",
			"NDIS CRM Roster Build Request Actions",
			{"dt": ROSTER_REQUEST, "view": "Form", "enabled": 1, "script": roster_request_script},
		)
		upsert_doc(
			"Client Script",
			"NDIS Participant Service File Actions",
			{"dt": SERVICE_FILE, "view": "Form", "enabled": 1, "script": service_file_script},
		)


def _deal_script():
	from ndis_crm.setup.phase9_roster_build_request import _deal_script as phase9_deal_script

	script = phase9_deal_script()
	insert = r''',
      {
        label: "Create Participant Service File",
        onClick: () => {
          call("ndis_crm.phase10_service_file.create_service_file_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Participant Service File Created" : "Existing Service File Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-participant-service-file/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Participant Service File",
        onClick: () => {
          if (doc.ndis_participant_service_file) {
            window.open(`/app/ndis-participant-service-file/${doc.ndis_participant_service_file}`, "_blank")
          } else {
            createToast({ title: "No Participant Service File linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _roster_request_script():
	from ndis_crm.setup.phase9_roster_build_request import _roster_request_script as phase9_roster_request_script

	script = phase9_roster_request_script()
	insert = r'''

        frm.add_custom_button(__("Create Participant Service File"), function () {
            frappe.call({
                method: "ndis_crm.phase10_service_file.create_service_file_from_roster_build_request",
                args: { roster_build_request: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating participant service file...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Participant Service File created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS Participant Service File", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_participant_service_file) {
            frm.add_custom_button(__("Open Participant Service File"), function () {
                frappe.set_route("Form", "NDIS Participant Service File", frm.doc.ndis_participant_service_file);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.service_schedule_draft)", insert + "\n        if (frm.doc.service_schedule_draft)")


def _service_file_script():
	return r'''
frappe.ui.form.on("NDIS Participant Service File", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Validate Service File Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase10_service_file.validate_service_file_readiness",
                args: { service_file: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating service file readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Service file readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Activation"), function () {
            frappe.call({
                method: "ndis_crm.phase10_service_file.mark_ready_for_activation",
                args: { service_file: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for activation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Activation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Activate Service File"), function () {
            frappe.confirm(
                __("This activates the Participant Service File as the live operational reference. It does not create roster, payroll, invoice, claim, or accounting records."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase10_service_file.activate_service_file",
                        args: { service_file: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Activating service file...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Service file activated"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.crm_deal) {
            frm.add_custom_button(__("Open CRM Deal"), function () {
                window.open(`/crm/deals/${frm.doc.crm_deal}`, "_blank");
            }, __("Open"));
        }

        if (frm.doc.roster_build_request) {
            frm.add_custom_button(__("Open Roster Build Request"), function () {
                frappe.set_route("Form", "NDIS CRM Roster Build Request", frm.doc.roster_build_request);
            }, __("Open"));
        }

        if (frm.doc.service_schedule_draft) {
            frm.add_custom_button(__("Open Service Schedule Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Service Schedule Draft", frm.doc.service_schedule_draft);
            }, __("Open"));
        }
    }
});
'''.strip()
