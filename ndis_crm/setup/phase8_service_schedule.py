import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"

SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
SCHEDULE_DRAFT_LINE = "NDIS CRM Service Schedule Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_schedule_doctypes()
	create_custom_fields_phase8()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 8 service schedule draft bridge installed successfully.")


def doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def ensure_required_doctypes():
	required = [
		CRM_DEAL,
		INTAKE,
		HANDOVER,
		FINANCE_ONBOARDING,
		OPERATIONS_SETUP,
		"NDIS Service Line",
		"CRM Form Script",
	]

	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 8 DocTypes: " + ", ".join(missing))

	print("Required Phase 8 DocTypes found.")


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


def create_schedule_doctypes():
	create_schedule_draft_line()
	create_schedule_draft()


def create_schedule_draft_line():
	fields = [
		make_field("Service", "service_section", "Section Break"),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data", in_list_view=1),
		make_field("Priority", "priority", "Data"),
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
		make_field("Schedule Pattern", "schedule_pattern_section", "Section Break"),
		make_field("Requires Roster", "requires_roster", "Check", default=0, in_list_view=1),
		make_field("Start Date", "start_date", "Date", in_list_view=1),
		make_field("End Date", "end_date", "Date"),
		make_field("Frequency", "frequency", "Select", options="Daily\nWeekly\nFortnightly\nMonthly\nOnce-off\nAs Required", in_list_view=1),
		make_field("Days of Week", "days_of_week", "Data", description="Example: Monday, Wednesday, Friday"),
		make_field("Shifts Per Week", "shifts_per_week", "Float"),
		make_field("Hours Per Shift", "hours_per_shift", "Float"),
		make_field("Estimated Weekly Hours", "estimated_weekly_hours", "Float", read_only=1),
		make_field("Workers Required", "workers_required", "Int", default=1),
		make_field("Estimated Worker Hours", "estimated_worker_hours", "Float", read_only=1),
		make_field("Time Window", "time_window_section", "Section Break"),
		make_field("Start Time", "start_time", "Time"),
		make_field("End Time", "end_time", "Time"),
		make_field("Flexible Time Window", "flexible_time_window", "Check", default=0),
		make_field("Preferred Time Notes", "preferred_time_notes", "Small Text"),
		make_field("Location / SIL", "location_sil_section", "Section Break"),
		make_field("Requires House", "requires_house", "Check", default=0),
	]

	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))

	fields += [
		make_field("Delivery Location", "delivery_location", "Data"),
		make_field("Support Ratio", "support_ratio", "Select", options="\n1:1\n1:2\n1:3\n1:4\nShared\nOther"),
		make_field("Overnight Model", "overnight_model", "Select", options="\nNone\nSleepover\nActive Overnight\nMixed"),
		make_field("Clinical / Worker Requirements", "clinical_worker_section", "Section Break"),
		make_field("Requires Clinical Review", "requires_clinical_review", "Check", default=0),
		make_field("Clinical Review Complete", "clinical_review_complete", "Check", default=0),
		make_field("Transport Required", "transport_required", "Check", default=0),
		make_field("Worker Skill Requirements", "worker_skill_requirements", "Small Text"),
		make_field("Clinical / Risk Notes", "clinical_risk_notes", "Small Text"),
		make_field("Roster Pattern Notes", "roster_pattern_notes", "Small Text"),
		make_field("Readiness", "readiness_section", "Section Break"),
		make_field("Ready for Roster Build", "ready_for_roster_build", "Check", default=0, in_list_view=1),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Roster Build\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=SCHEDULE_DRAFT_LINE,
		fields=fields,
		istable=1,
	)


def create_schedule_draft():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-SCH-DRAFT-.YYYY.-.#####", default="NDIS-SCH-DRAFT-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Roster Build\nRoster Build Started\nSchedule Approved\nReturned to Operations\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Schedule Ready", "schedule_ready", "Check", read_only=1, in_list_view=1),
		make_field("Source Links", "source_links_section", "Section Break"),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
		make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
		make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER),
		make_field("NDIS CRM Finance Onboarding", "finance_onboarding", "Link", options=FINANCE_ONBOARDING),
		make_field("NDIS CRM Operations Setup", "operations_setup", "Link", options=OPERATIONS_SETUP, reqd=1, in_list_view=1),
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
		make_field("Target Start Date", "target_start_date", "Date", in_list_view=1),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Schedule Owner", "schedule_owner", "Link", options="User", in_list_view=1),
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
		make_field("Schedule Lines", "schedule_lines_section", "Section Break"),
		make_field("Schedule Lines", "schedule_lines", "Table", options=SCHEDULE_DRAFT_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Schedule Notes", "schedule_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=SCHEDULE_DRAFT,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def create_custom_fields_phase8():
	deal_fields = [
		{
			"fieldname": "service_schedule_section",
			"label": "NDIS Service Schedule Draft",
			"fieldtype": "Section Break",
			"insert_after": "operations_setup_ready",
		},
		{
			"fieldname": "ndis_service_schedule_required",
			"label": "Service Schedule Draft Required",
			"fieldtype": "Check",
			"default": 1,
			"insert_after": "service_schedule_section",
		},
		{
			"fieldname": "ndis_service_schedule_draft",
			"label": "NDIS CRM Service Schedule Draft",
			"fieldtype": "Link",
			"options": SCHEDULE_DRAFT,
			"read_only": 1,
			"insert_after": "ndis_service_schedule_required",
		},
		{
			"fieldname": "service_schedule_status",
			"label": "Service Schedule Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_service_schedule_draft",
		},
		{
			"fieldname": "service_schedule_ready",
			"label": "Service Schedule Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "service_schedule_status",
		},
	]

	shared_fields = [
		{
			"fieldname": "service_schedule_section",
			"label": "NDIS Service Schedule Draft",
			"fieldtype": "Section Break",
			"insert_after": "operations_setup_ready",
		},
		{
			"fieldname": "ndis_service_schedule_draft",
			"label": "NDIS CRM Service Schedule Draft",
			"fieldtype": "Link",
			"options": SCHEDULE_DRAFT,
			"read_only": 1,
			"insert_after": "service_schedule_section",
		},
		{
			"fieldname": "service_schedule_status",
			"label": "Service Schedule Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_service_schedule_draft",
		},
		{
			"fieldname": "service_schedule_ready",
			"label": "Service Schedule Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "service_schedule_status",
		},
	]

	operations_fields = [
		{
			"fieldname": "service_schedule_section",
			"label": "NDIS Service Schedule Draft",
			"fieldtype": "Section Break",
			"insert_after": "operations_ready",
		},
		{
			"fieldname": "ndis_service_schedule_draft",
			"label": "NDIS CRM Service Schedule Draft",
			"fieldtype": "Link",
			"options": SCHEDULE_DRAFT,
			"read_only": 1,
			"insert_after": "service_schedule_section",
		},
		{
			"fieldname": "service_schedule_status",
			"label": "Service Schedule Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_service_schedule_draft",
		},
		{
			"fieldname": "service_schedule_ready",
			"label": "Service Schedule Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "service_schedule_status",
		},
	]

	was_in_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		create_custom_fields(
			{
				CRM_DEAL: deal_fields,
				HANDOVER: shared_fields,
				FINANCE_ONBOARDING: shared_fields,
				OPERATIONS_SETUP: operations_fields,
				INTAKE: shared_fields,
			},
			update=True,
		)
	finally:
		frappe.flags.in_install = was_in_install

	print("Created / updated Phase 8 service schedule custom fields.")


def upsert_doc(doctype, name, values):
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for key, value in values.items():
			doc.set(key, value)
		doc.save(ignore_permissions=True)
		print(f"Updated {doctype}: {name}")
	else:
		doc = frappe.get_doc({
			"doctype": doctype,
			"name": name,
			**values,
		})
		doc.insert(ignore_permissions=True)
		print(f"Created {doctype}: {name}")


def create_form_scripts():
	deal_script = r'''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
      {
        label: "Open Linked CRM Lead",
        onClick: () => {
          if (doc.lead) {
            window.open(`/crm/leads/${doc.lead}`, "_blank")
          } else {
            createToast({ title: "No CRM Lead linked to this Deal", icon: "info" })
          }
        }
      },
      {
        label: "Generate Document Requests",
        onClick: () => {
          call("ndis_crm.phase3_documents.generate_document_requests_for_crm_deal", {
            deal: doc.name
          }).then((data) => {
            createToast({
              title: data && data.message ? data.message : "Document requests generated",
              icon: "check",
              iconClasses: "text-green-600",
            })
            window.open(`/app/ndis-document-request?crm_deal=${encodeURIComponent(doc.name)}`, "_blank")
          })
        }
      },
      {
        label: "Open Document Requests",
        onClick: () => {
          window.open(`/app/ndis-document-request?crm_deal=${encodeURIComponent(doc.name)}`, "_blank")
        }
      },
      {
        label: "Create NDIS Handover",
        onClick: () => {
          call("ndis_crm.phase4_handover.create_handover_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "NDIS Handover Created" : "Existing NDIS Handover Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-handover/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open NDIS Handover",
        onClick: () => {
          if (doc.ndis_handover) {
            window.open(`/app/ndis-crm-handover/${doc.ndis_handover}`, "_blank")
          } else {
            createToast({ title: "No NDIS Handover linked yet", icon: "info" })
          }
        }
      },
      {
        label: "Create Finance Onboarding",
        onClick: () => {
          call("ndis_crm.phase5_finance_onboarding.create_finance_onboarding_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Finance Onboarding Created" : "Existing Finance Onboarding Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-finance-onboarding/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Finance Onboarding",
        onClick: () => {
          if (doc.ndis_finance_onboarding) {
            window.open(`/app/ndis-crm-finance-onboarding/${doc.ndis_finance_onboarding}`, "_blank")
          } else {
            createToast({ title: "No Finance Onboarding linked yet", icon: "info" })
          }
        }
      },
      {
        label: "Create Operations Setup",
        onClick: () => {
          call("ndis_crm.phase7_operations_setup.create_operations_setup_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Operations Setup Created" : "Existing Operations Setup Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-operations-setup/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Operations Setup",
        onClick: () => {
          if (doc.ndis_operations_setup) {
            window.open(`/app/ndis-crm-operations-setup/${doc.ndis_operations_setup}`, "_blank")
          } else {
            createToast({ title: "No Operations Setup linked yet", icon: "info" })
          }
        }
      },
      {
        label: "Create Service Schedule Draft",
        onClick: () => {
          call("ndis_crm.phase8_service_schedule.create_service_schedule_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Service Schedule Draft Created" : "Existing Schedule Draft Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-service-schedule-draft/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Service Schedule Draft",
        onClick: () => {
          if (doc.ndis_service_schedule_draft) {
            window.open(`/app/ndis-crm-service-schedule-draft/${doc.ndis_service_schedule_draft}`, "_blank")
          } else {
            createToast({ title: "No Service Schedule Draft linked yet", icon: "info" })
          }
        }
      }
    ]
  }
}
'''.strip()

	operations_setup_script = r'''
frappe.ui.form.on("NDIS CRM Operations Setup", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Validate Operations Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase7_operations_setup.validate_operations_readiness",
                args: { operations_setup: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating operations readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Operations readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Rostering"), function () {
            frappe.call({
                method: "ndis_crm.phase7_operations_setup.mark_ready_for_rostering",
                args: { operations_setup: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for rostering...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Rostering"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Service Delivery Ready"), function () {
            frappe.call({
                method: "ndis_crm.phase7_operations_setup.mark_service_delivery_ready",
                args: { operations_setup: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking service delivery ready...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Service Delivery Ready"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create Service Schedule Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase8_service_schedule.create_service_schedule_from_operations_setup",
                args: { operations_setup: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating service schedule draft...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Service Schedule Draft created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Service Schedule Draft", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_service_schedule_draft) {
            frm.add_custom_button(__("Open Service Schedule Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Service Schedule Draft", frm.doc.ndis_service_schedule_draft);
            }, __("Open"));
        }

        if (frm.doc.crm_deal) {
            frm.add_custom_button(__("Open CRM Deal"), function () {
                window.open(`/crm/deals/${frm.doc.crm_deal}`, "_blank");
            }, __("Open"));
        }

        if (frm.doc.handover) {
            frm.add_custom_button(__("Open Handover"), function () {
                frappe.set_route("Form", "NDIS CRM Handover", frm.doc.handover);
            }, __("Open"));
        }

        if (frm.doc.finance_onboarding) {
            frm.add_custom_button(__("Open Finance Onboarding"), function () {
                frappe.set_route("Form", "NDIS CRM Finance Onboarding", frm.doc.finance_onboarding);
            }, __("Open"));
        }
    }
});
'''.strip()

	schedule_draft_script = r'''
frappe.ui.form.on("NDIS CRM Service Schedule Draft", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Validate Schedule Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase8_service_schedule.validate_schedule_readiness",
                args: { schedule_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating schedule readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Schedule readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Roster Build"), function () {
            frappe.call({
                method: "ndis_crm.phase8_service_schedule.mark_ready_for_roster_build",
                args: { schedule_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for roster build...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Roster Build"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Schedule Approved"), function () {
            frappe.call({
                method: "ndis_crm.phase8_service_schedule.mark_schedule_approved",
                args: { schedule_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving service schedule draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Schedule approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.operations_setup) {
            frm.add_custom_button(__("Open Operations Setup"), function () {
                frappe.set_route("Form", "NDIS CRM Operations Setup", frm.doc.operations_setup);
            }, __("Open"));
        }

        if (frm.doc.crm_deal) {
            frm.add_custom_button(__("Open CRM Deal"), function () {
                window.open(`/crm/deals/${frm.doc.crm_deal}`, "_blank");
            }, __("Open"));
        }

        if (frm.doc.handover) {
            frm.add_custom_button(__("Open Handover"), function () {
                frappe.set_route("Form", "NDIS CRM Handover", frm.doc.handover);
            }, __("Open"));
        }

        if (frm.doc.finance_onboarding) {
            frm.add_custom_button(__("Open Finance Onboarding"), function () {
                frappe.set_route("Form", "NDIS CRM Finance Onboarding", frm.doc.finance_onboarding);
            }, __("Open"));
        }
    }
});
'''.strip()

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
			"NDIS CRM Operations Setup Actions",
			{
				"dt": OPERATIONS_SETUP,
				"view": "Form",
				"enabled": 1,
				"script": operations_setup_script,
			},
		)
		upsert_doc(
			"Client Script",
			"NDIS CRM Service Schedule Draft Actions",
			{
				"dt": SCHEDULE_DRAFT,
				"view": "Form",
				"enabled": 1,
				"script": schedule_draft_script,
			},
		)
