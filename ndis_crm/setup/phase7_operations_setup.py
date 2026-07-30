import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"

OPERATIONS_SETUP = "NDIS CRM Operations Setup"
OPERATIONS_REQUIREMENT = "NDIS CRM Operations Service Requirement"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_operations_doctypes()
	create_custom_fields_phase7()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 7 operations setup bridge installed successfully.")


def doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def ensure_required_doctypes():
	required = [
		CRM_DEAL,
		INTAKE,
		HANDOVER,
		FINANCE_ONBOARDING,
		"NDIS Service Line",
		"NDIS Service Interest",
		"CRM Form Script",
	]

	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 7 DocTypes: " + ", ".join(missing))

	print("Required Phase 7 DocTypes found.")


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


def create_operations_doctypes():
	create_operations_requirement()
	create_operations_setup()


def create_operations_requirement():
	fields = [
		make_field("Service", "service_section", "Section Break"),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Budget Type", "budget_type", "Data", read_only=1),
		make_field(
			"Service Model",
			"service_model",
			"Select",
			options="Support Worker Shift\nSIL 24/7 Support\nCommunity Participation Shift\nTherapy Service\nBehaviour Support Service\nTransport Service\nPlan Management Admin\nOther",
			in_list_view=1,
		),
		make_field("Priority", "priority", "Data"),
		make_field("Required Start Date", "required_start_date", "Date", in_list_view=1),
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
		make_field("Roster / Delivery Requirements", "roster_delivery_section", "Section Break"),
		make_field("Requires Roster", "requires_roster", "Check", default=0),
		make_field("Frequency", "frequency", "Select", options="Daily\nWeekly\nFortnightly\nMonthly\nOnce-off\nAs Required"),
		make_field("Shifts Per Week", "shifts_per_week", "Float"),
		make_field("Hours Per Shift", "hours_per_shift", "Float"),
		make_field("Estimated Weekly Hours", "estimated_weekly_hours", "Float"),
		make_field("Preferred Start Time", "preferred_start_time", "Time"),
		make_field("Preferred End Time", "preferred_end_time", "Time"),
		make_field("Roster Pattern Notes", "roster_pattern_notes", "Small Text"),
		make_field("SIL / Location Requirements", "sil_location_section", "Section Break"),
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
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Pending\nIn Review\nReady\nCompleted\nBlocked\nNot Required", default="Pending", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=OPERATIONS_REQUIREMENT,
		fields=fields,
		istable=1,
	)


def create_operations_setup():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-OPS-SETUP-.YYYY.-.#####", default="NDIS-OPS-SETUP-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field(
			"Status",
			"status",
			"Select",
			options="Draft\nIn Review\nReady for Rostering\nRoster Setup Started\nService Delivery Ready\nActive\nReturned to CRM\nCancelled",
			default="Draft",
			in_list_view=1,
		),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Operations Ready", "operations_ready", "Check", read_only=1, in_list_view=1),
		make_field("Source Links", "source_links_section", "Section Break"),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
		make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
		make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER, in_list_view=1),
		make_field("NDIS CRM Finance Onboarding", "finance_onboarding", "Link", options=FINANCE_ONBOARDING, in_list_view=1),
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
		make_field("Operations Assignment", "operations_assignment_section", "Section Break"),
		make_field("Operations Owner", "operations_owner", "Link", options="User", in_list_view=1),
		make_field("Rostering Owner", "rostering_owner", "Link", options="User"),
		make_field("Service Manager", "service_manager", "Link", options="User"),
		make_field("Clinical Owner", "clinical_owner", "Link", options="User"),
		make_field("Target Start Date", "target_start_date", "Date", in_list_view=1),
		make_field("Default Cost Center", "default_cost_center", "Link", options="Cost Center"),
	]

	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))

	fields += [
		make_field("Readiness Controls", "readiness_controls_section", "Section Break"),
		make_field("Finance Setup Required", "finance_setup_required", "Check", default=1),
		make_field("Finance Setup Confirmed", "finance_setup_confirmed", "Check", default=0),
		make_field("Roster Requirements Confirmed", "roster_requirements_confirmed", "Check", default=0),
		make_field("Worker Skill Requirements Confirmed", "worker_skill_requirements_confirmed", "Check", default=0),
		make_field("Clinical Review Required", "clinical_review_required", "Check", default=0),
		make_field("Clinical Review Complete", "clinical_review_complete", "Check", default=0),
		make_field("Service Requirements", "service_requirements_section", "Section Break"),
		make_field("Service Requirements", "service_requirements", "Table", options=OPERATIONS_REQUIREMENT),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Operations Notes", "operations_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=OPERATIONS_SETUP,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def create_custom_fields_phase7():
	deal_fields = [
		{
			"fieldname": "operations_setup_section",
			"label": "NDIS Operations Setup",
			"fieldtype": "Section Break",
			"insert_after": "finance_service_booking_count",
		},
		{
			"fieldname": "ndis_operations_setup_required",
			"label": "Operations Setup Required",
			"fieldtype": "Check",
			"default": 1,
			"insert_after": "operations_setup_section",
		},
		{
			"fieldname": "ndis_operations_setup",
			"label": "NDIS CRM Operations Setup",
			"fieldtype": "Link",
			"options": OPERATIONS_SETUP,
			"read_only": 1,
			"insert_after": "ndis_operations_setup_required",
		},
		{
			"fieldname": "operations_setup_status",
			"label": "Operations Setup Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_operations_setup",
		},
		{
			"fieldname": "operations_setup_ready",
			"label": "Operations Setup Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "operations_setup_status",
		},
	]

	shared_link_fields = [
		{
			"fieldname": "operations_setup_section",
			"label": "NDIS Operations Setup",
			"fieldtype": "Section Break",
			"insert_after": "finance_service_booking_count",
		},
		{
			"fieldname": "ndis_operations_setup",
			"label": "NDIS CRM Operations Setup",
			"fieldtype": "Link",
			"options": OPERATIONS_SETUP,
			"read_only": 1,
			"insert_after": "operations_setup_section",
		},
		{
			"fieldname": "operations_setup_status",
			"label": "Operations Setup Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_operations_setup",
		},
		{
			"fieldname": "operations_setup_ready",
			"label": "Operations Setup Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "operations_setup_status",
		},
	]

	finance_onboarding_fields = [
		{
			"fieldname": "operations_setup_section",
			"label": "NDIS Operations Setup",
			"fieldtype": "Section Break",
			"insert_after": "finance_records_summary",
		},
		{
			"fieldname": "ndis_operations_setup",
			"label": "NDIS CRM Operations Setup",
			"fieldtype": "Link",
			"options": OPERATIONS_SETUP,
			"read_only": 1,
			"insert_after": "operations_setup_section",
		},
		{
			"fieldname": "operations_setup_status",
			"label": "Operations Setup Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_operations_setup",
		},
		{
			"fieldname": "operations_setup_ready",
			"label": "Operations Setup Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "operations_setup_status",
		},
	]

	intake_fields = [
		{
			"fieldname": "operations_setup_section",
			"label": "NDIS Operations Setup",
			"fieldtype": "Section Break",
			"insert_after": "finance_onboarding_ready",
		},
		{
			"fieldname": "ndis_operations_setup",
			"label": "NDIS CRM Operations Setup",
			"fieldtype": "Link",
			"options": OPERATIONS_SETUP,
			"read_only": 1,
			"insert_after": "operations_setup_section",
		},
		{
			"fieldname": "operations_setup_status",
			"label": "Operations Setup Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_operations_setup",
		},
		{
			"fieldname": "operations_setup_ready",
			"label": "Operations Setup Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "operations_setup_status",
		},
	]

	was_in_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		create_custom_fields(
			{
				CRM_DEAL: deal_fields,
				HANDOVER: shared_link_fields,
				FINANCE_ONBOARDING: finance_onboarding_fields,
				INTAKE: intake_fields,
			},
			update=True,
		)
	finally:
		frappe.flags.in_install = was_in_install

	print("Created / updated Phase 7 operations setup custom fields.")


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
      }
    ]
  }
}
'''.strip()

	handover_script = r'''
frappe.ui.form.on("NDIS CRM Handover", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create / Link Customer"), function () {
            frappe.call({
                method: "ndis_crm.phase4_handover.create_customer_from_handover",
                args: { handover: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating or linking Customer...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Customer linked"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create NDIS Financial Profile"), function () {
            frappe.call({
                method: "ndis_crm.phase4_handover.create_financial_profile_from_handover",
                args: { handover: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating NDIS Financial Profile...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("NDIS Financial Profile linked"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create Finance Onboarding"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.create_finance_onboarding_from_handover",
                args: { handover: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating Finance Onboarding...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Finance Onboarding created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Finance Onboarding", r.message.name);
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create Operations Setup"), function () {
            frappe.call({
                method: "ndis_crm.phase7_operations_setup.create_operations_setup_from_handover",
                args: { handover: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating Operations Setup...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Operations Setup created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Operations Setup", r.message.name);
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Recalculate Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase4_handover.recalculate_handover_readiness",
                args: { handover: frm.doc.name },
                freeze: true,
                freeze_message: __("Recalculating handover readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Readiness recalculated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Operations"), function () {
            frappe.call({
                method: "ndis_crm.phase4_handover.mark_handover_ready",
                args: { handover: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking handover ready...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Handover ready"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_finance_onboarding) {
            frm.add_custom_button(__("Open Finance Onboarding"), function () {
                frappe.set_route("Form", "NDIS CRM Finance Onboarding", frm.doc.ndis_finance_onboarding);
            }, __("Open"));
        }

        if (frm.doc.ndis_operations_setup) {
            frm.add_custom_button(__("Open Operations Setup"), function () {
                frappe.set_route("Form", "NDIS CRM Operations Setup", frm.doc.ndis_operations_setup);
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

	finance_onboarding_script = r'''
frappe.ui.form.on("NDIS CRM Finance Onboarding", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create / Link Financial Profile"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.create_financial_profile_from_onboarding",
                args: { onboarding: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating or linking financial profile...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Financial Profile linked"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Finance Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.validate_finance_onboarding_readiness",
                args: { onboarding: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating finance readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Finance readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Finance"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.mark_ready_for_finance",
                args: { onboarding: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for finance...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Finance"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create Draft Plan Budgets"), function () {
            frappe.call({
                method: "ndis_crm.phase6_finance_drafts.create_draft_plan_budgets_from_onboarding",
                args: { onboarding: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating draft plan budgets...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Draft plan budgets created"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Finance Records"));

        frm.add_custom_button(__("Create Service Bookings"), function () {
            frappe.confirm(
                __("This will create Active NDIS Service Booking records. Continue only after finance approval."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase6_finance_drafts.create_service_bookings_from_onboarding",
                        args: { onboarding: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Creating service bookings...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Service bookings created"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Finance Records"));

        frm.add_custom_button(__("Recalculate Finance Records"), function () {
            frappe.call({
                method: "ndis_crm.phase6_finance_drafts.recalculate_finance_record_summary",
                args: { onboarding: frm.doc.name },
                freeze: true,
                freeze_message: __("Recalculating finance records...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Finance records recalculated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Finance Records"));

        frm.add_custom_button(__("Create Operations Setup"), function () {
            frappe.call({
                method: "ndis_crm.phase7_operations_setup.create_operations_setup_from_finance_onboarding",
                args: { onboarding: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating operations setup...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Operations Setup created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Operations Setup", r.message.name);
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Open Plan Budgets"), function () {
            frappe.route_options = { ndis_crm_finance_onboarding: frm.doc.name };
            frappe.set_route("List", "NDIS Plan Budget");
        }, __("Open"));

        frm.add_custom_button(__("Open Service Bookings"), function () {
            frappe.route_options = { ndis_crm_finance_onboarding: frm.doc.name };
            frappe.set_route("List", "NDIS Service Booking");
        }, __("Open"));

        if (frm.doc.ndis_operations_setup) {
            frm.add_custom_button(__("Open Operations Setup"), function () {
                frappe.set_route("Form", "NDIS CRM Operations Setup", frm.doc.ndis_operations_setup);
            }, __("Open"));
        }

        frm.add_custom_button(__("Mark Finance Setup Complete"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.mark_finance_setup_complete",
                args: { onboarding: frm.doc.name },
                freeze: true,
                freeze_message: __("Completing finance setup...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Finance setup completed"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.handover) {
            frm.add_custom_button(__("Open Handover"), function () {
                frappe.set_route("Form", "NDIS CRM Handover", frm.doc.handover);
            }, __("Open"));
        }

        if (frm.doc.crm_deal) {
            frm.add_custom_button(__("Open CRM Deal"), function () {
                window.open(`/crm/deals/${frm.doc.crm_deal}`, "_blank");
            }, __("Open"));
        }

        if (frm.doc.ndis_financial_profile) {
            frm.add_custom_button(__("Open Financial Profile"), function () {
                frappe.set_route("Form", "NDIS Participant Financial Profile", frm.doc.ndis_financial_profile);
            }, __("Open"));
        }
    }
});
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
			"dt": "CRM Deal",
			"view": "Form",
			"enabled": 1,
			"is_standard": 0,
			"script": deal_script,
		},
	)

	if frappe.db.exists("DocType", "Client Script"):
		upsert_doc(
			"Client Script",
			"NDIS CRM Handover Actions",
			{
				"dt": HANDOVER,
				"view": "Form",
				"enabled": 1,
				"script": handover_script,
			},
		)

		upsert_doc(
			"Client Script",
			"NDIS CRM Finance Onboarding Actions",
			{
				"dt": FINANCE_ONBOARDING,
				"view": "Form",
				"enabled": 1,
				"script": finance_onboarding_script,
			},
		)

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
