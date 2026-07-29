import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"

HANDOVER = "NDIS CRM Handover"
HANDOVER_ITEM = "NDIS CRM Handover Checklist Item"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
FUNDING_SOURCE = "NDIS Funding Source"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_handover_doctypes()
	create_handover_custom_fields()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 4 handover installed successfully.")


def doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def ensure_required_doctypes():
	required = [
		CRM_DEAL,
		INTAKE,
		"Customer",
		"NDIS Service Line",
		"NDIS Service Interest",
		"CRM Form Script",
	]

	missing = [dt for dt in required if not doctype_exists(dt)]

	if missing:
		frappe.throw("Missing required DocTypes: " + ", ".join(missing))

	print("Required Phase 4 DocTypes found.")


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


def create_handover_doctypes():
	create_handover_checklist_item()
	create_handover()


def create_handover_checklist_item():
	fields = [
		make_field("Category", "category", "Data", in_list_view=1),
		make_field("Checklist Item", "item", "Data", reqd=1, in_list_view=1),
		make_field("Required?", "is_required", "Check", default=1, in_list_view=1),
		make_field("Status", "status", "Select", options="Pending\nIn Progress\nCompleted\nNot Required\nBlocked", default="Pending", in_list_view=1),
		make_field("Owner Role", "owner_role", "Link", options="Role"),
		make_field("Completed By", "completed_by", "Link", options="User"),
		make_field("Completed On", "completed_on", "Datetime"),
		make_field("Notes", "notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=HANDOVER_ITEM,
		fields=fields,
		istable=1,
	)


def create_handover():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-HANDOVER-.YYYY.-.#####", default="NDIS-HANDOVER-.YYYY.-.#####", reqd=1),
		make_field("Handover Status", "handover_status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nChecklist Pending\nReady for Operations\nHanded Over\nAccepted\nRejected", default="Draft", in_list_view=1),
		make_field("Handover Type", "handover_type", "Data", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Handover Ready", "handover_ready", "Check", read_only=1, in_list_view=1),
		make_field("CRM Links", "crm_links_section", "Section Break"),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead", in_list_view=1),
		make_field("CRM Deal", "crm_deal", "Link", options="CRM Deal", reqd=1, in_list_view=1),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options="NDIS Participant Intake", in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
	]

	if doctype_exists(FINANCE_PROFILE):
		fields.append(
			make_field("NDIS Financial Profile", "ndis_financial_profile", "Link", options=FINANCE_PROFILE, in_list_view=1)
		)

	fields += [
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Date of Birth", "date_of_birth", "Date"),
		make_field("Plan Details", "plan_details_section", "Section Break"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Plan Management Type", "plan_management_type", "Select", options="NDIA Managed\nPlan Managed\nSelf Managed\nMixed\nUnknown"),
	]

	if doctype_exists(FUNDING_SOURCE):
		fields.append(make_field("Funding Source", "funding_source", "Link", options=FUNDING_SOURCE))

	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))

	fields += [
		make_field("Default Cost Center", "default_cost_center", "Link", options="Cost Center"),
		make_field("Deal Readiness Snapshot", "deal_readiness_snapshot_section", "Section Break"),
		make_field("Funding Verified", "funding_verified", "Check", read_only=1),
		make_field("Service Agreement Status", "service_agreement_status", "Data", read_only=1),
		make_field("Required Documents Collected", "required_documents_collected", "Check", read_only=1),
		make_field("Team Assignment", "team_assignment_section", "Section Break"),
		make_field("Operations Owner", "operations_owner", "Link", options="User"),
		make_field("Finance Owner", "finance_owner", "Link", options="User"),
		make_field("Rostering Owner", "rostering_owner", "Link", options="User"),
		make_field("Clinical Owner", "clinical_owner", "Link", options="User"),
		make_field("Target Start Date", "target_start_date", "Date"),
		make_field("Checklist", "checklist_section", "Section Break"),
		make_field("Checklist Items", "checklist_items", "Table", options=HANDOVER_ITEM),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Handover Notes", "handover_notes", "Small Text"),
		make_field("Rejection / Return Notes", "rejection_notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=HANDOVER,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def create_handover_custom_fields():
	deal_fields = [
		{
			"fieldname": "handover_control_section",
			"label": "NDIS Handover Control",
			"fieldtype": "Section Break",
			"insert_after": "document_summary",
		},
		{
			"fieldname": "ndis_handover",
			"label": "NDIS CRM Handover",
			"fieldtype": "Link",
			"options": HANDOVER,
			"read_only": 1,
			"insert_after": "handover_control_section",
		},
		{
			"fieldname": "handover_readiness_percent",
			"label": "Handover Readiness %",
			"fieldtype": "Percent",
			"read_only": 1,
			"insert_after": "ndis_handover",
		},
		{
			"fieldname": "handover_ready",
			"label": "Handover Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "handover_readiness_percent",
		},
	]

	intake_fields = [
		{
			"fieldname": "handover_control_section",
			"label": "NDIS Handover Control",
			"fieldtype": "Section Break",
			"insert_after": "document_summary",
		},
		{
			"fieldname": "ndis_handover",
			"label": "NDIS CRM Handover",
			"fieldtype": "Link",
			"options": HANDOVER,
			"read_only": 1,
			"insert_after": "handover_control_section",
		},
		{
			"fieldname": "participant_customer",
			"label": "Participant Customer",
			"fieldtype": "Link",
			"options": "Customer",
			"read_only": 1,
			"insert_after": "ndis_handover",
		},
		{
			"fieldname": "handover_readiness_percent",
			"label": "Handover Readiness %",
			"fieldtype": "Percent",
			"read_only": 1,
			"insert_after": "participant_customer",
		},
		{
			"fieldname": "handover_ready",
			"label": "Handover Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "handover_readiness_percent",
		},
	]

	if doctype_exists(FINANCE_PROFILE):
		deal_fields.append({
			"fieldname": "ndis_financial_profile",
			"label": "NDIS Participant Financial Profile",
			"fieldtype": "Link",
			"options": FINANCE_PROFILE,
			"read_only": 1,
			"insert_after": "handover_ready",
		})

		intake_fields.append({
			"fieldname": "ndis_financial_profile",
			"label": "NDIS Participant Financial Profile",
			"fieldtype": "Link",
			"options": FINANCE_PROFILE,
			"read_only": 1,
			"insert_after": "handover_ready",
		})

	if doctype_exists(FUNDING_SOURCE):
		deal_fields.append({
			"fieldname": "ndis_default_funding_source",
			"label": "Default NDIS Funding Source",
			"fieldtype": "Link",
			"options": FUNDING_SOURCE,
			"insert_after": "ndis_financial_profile" if doctype_exists(FINANCE_PROFILE) else "handover_ready",
		})

	if doctype_exists(NDIS_HOUSE):
		deal_fields.append({
			"fieldname": "ndis_default_house",
			"label": "Default NDIS House",
			"fieldtype": "Link",
			"options": NDIS_HOUSE,
			"insert_after": "ndis_default_funding_source" if doctype_exists(FUNDING_SOURCE) else "handover_ready",
		})

	deal_fields.append({
		"fieldname": "ndis_default_cost_center",
		"label": "Default NDIS Cost Center",
		"fieldtype": "Link",
		"options": "Cost Center",
		"insert_after": "ndis_default_house" if doctype_exists(NDIS_HOUSE) else "handover_ready",
	})

	create_custom_fields(
		{
			CRM_DEAL: deal_fields,
			INTAKE: intake_fields,
		},
		update=True,
	)

	print("Created / updated Phase 4 handover custom fields.")


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
            createToast({
              title: "No CRM Lead linked to this Deal",
              icon: "info",
            })
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
            createToast({
              title: "No NDIS Handover linked yet",
              icon: "info",
            })
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
                args: {
                    handover: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Creating or linking Customer...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Customer linked"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create NDIS Financial Profile"), function () {
            frappe.call({
                method: "ndis_crm.phase4_handover.create_financial_profile_from_handover",
                args: {
                    handover: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Creating NDIS Financial Profile...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("NDIS Financial Profile linked"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Recalculate Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase4_handover.recalculate_handover_readiness",
                args: {
                    handover: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Recalculating handover readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Readiness recalculated"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Operations"), function () {
            frappe.call({
                method: "ndis_crm.phase4_handover.mark_handover_ready",
                args: {
                    handover: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Marking handover ready...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Handover ready"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.crm_deal) {
            frm.add_custom_button(__("Open CRM Deal"), function () {
                window.open(`/crm/deals/${frm.doc.crm_deal}`, "_blank");
            }, __("Open"));
        }
    },

    checklist_items_on_form_rendered(frm) {
        frm.trigger("set_completed_defaults");
    },

    set_completed_defaults(frm) {
        let row = frm.open_grid_row && frm.open_grid_row.doc;
        if (!row) {
            return;
        }

        if (row.status === "Completed" && !row.completed_on) {
            row.completed_on = frappe.datetime.now_datetime();
            row.completed_by = frappe.session.user;
            frm.refresh_field("checklist_items");
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
				"dt": "NDIS CRM Handover",
				"view": "Form",
				"enabled": 1,
				"script": handover_script,
			},
		)
