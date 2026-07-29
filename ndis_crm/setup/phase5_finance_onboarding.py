import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"

FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
FINANCE_ONBOARDING_SERVICE = "NDIS CRM Finance Onboarding Service"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
FUNDING_SOURCE = "NDIS Funding Source"
NDIS_HOUSE = "NDIS House"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"


def install():
	ensure_required_doctypes()
	create_finance_onboarding_doctypes()
	create_custom_fields_phase5()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 5 finance onboarding bridge installed successfully.")


def doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def ensure_required_doctypes():
	required = [
		CRM_DEAL,
		INTAKE,
		HANDOVER,
		"NDIS Service Line",
		"NDIS Service Interest",
		"Customer",
		"CRM Form Script",
	]

	missing = [dt for dt in required if not doctype_exists(dt)]

	if missing:
		frappe.throw("Missing required DocTypes: " + ", ".join(missing))

	print("Required Phase 5 DocTypes found.")


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


def create_finance_onboarding_doctypes():
	create_finance_onboarding_service()
	create_finance_onboarding()


def create_finance_onboarding_service():
	fields = [
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Budget Type", "budget_type", "Data", read_only=1, in_list_view=1),
		make_field("Priority", "priority", "Data"),
		make_field("Required Start Date", "required_start_date", "Date", in_list_view=1),
		make_field("Funding Available", "funding_available", "Data"),
	]

	if doctype_exists(NDIS_SERVICE_TYPE):
		fields.append(make_field("Finance Service Type", "finance_service_type", "Link", options=NDIS_SERVICE_TYPE, in_list_view=1))
	else:
		fields.append(make_field("Finance Service Type", "finance_service_type", "Data", in_list_view=1))

	if doctype_exists(NDIS_SUPPORT_ITEM):
		fields.append(make_field("Default Support Item", "default_support_item", "Link", options=NDIS_SUPPORT_ITEM, in_list_view=1))
	else:
		fields.append(make_field("Default Support Item", "default_support_item", "Data", in_list_view=1))

	fields += [
		make_field("Budget / Booking", "budget_booking_section", "Section Break"),
		make_field("Requires Plan Budget", "requires_plan_budget", "Check", default=1),
		make_field("Proposed Budget Amount", "proposed_budget_amount", "Currency"),
		make_field("Requires Service Booking", "requires_service_booking", "Check", default=1),
		make_field("Proposed Service Booking Amount", "proposed_service_booking_amount", "Currency"),
		make_field("Status", "status", "Select", options="Pending\nMapped\nBudget Amount Confirmed\nService Booking Amount Confirmed\nReady\nCompleted", default="Pending", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=FINANCE_ONBOARDING_SERVICE,
		fields=fields,
		istable=1,
	)


def create_finance_onboarding():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-FIN-ONB-.YYYY.-.#####", default="NDIS-FIN-ONB-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Finance\nFinance Setup Started\nBudget Setup Complete\nService Booking Complete\nCompleted\nReturned to CRM\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Finance Ready", "finance_ready", "Check", read_only=1, in_list_view=1),
		make_field("Source Links", "source_links_section", "Section Break"),
		make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER, reqd=1, in_list_view=1),
		make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
	]

	if doctype_exists(FINANCE_PROFILE):
		fields.append(make_field("NDIS Participant Financial Profile", "ndis_financial_profile", "Link", options=FINANCE_PROFILE, in_list_view=1))
	else:
		fields.append(make_field("NDIS Participant Financial Profile", "ndis_financial_profile", "Data", in_list_view=1))

	fields += [
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan and Finance Details", "plan_finance_section", "Section Break"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Plan Management Type", "plan_management_type", "Select", options="NDIA Managed\nPlan Managed\nSelf Managed\nMixed\nUnknown"),
	]

	if doctype_exists(FUNDING_SOURCE):
		fields.append(make_field("Funding Source", "funding_source", "Link", options=FUNDING_SOURCE))
	else:
		fields.append(make_field("Funding Source", "funding_source", "Data"))

	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))

	fields += [
		make_field("Default Cost Center", "default_cost_center", "Link", options="Cost Center"),
		make_field("Finance Owner", "finance_owner", "Link", options="User"),
		make_field("Target Finance Setup Date", "target_finance_setup_date", "Date"),
		make_field("Service Setup Rows", "service_setup_section", "Section Break"),
		make_field("Service Rows", "service_rows", "Table", options=FINANCE_ONBOARDING_SERVICE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Finance Setup Notes", "finance_setup_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]

	create_doctype_if_missing(
		name=FINANCE_ONBOARDING,
		fields=fields,
		autoname="naming_series:",
		title_field="participant_name",
	)


def create_custom_fields_phase5():
	service_line_fields = [
		{
			"fieldname": "finance_mapping_section",
			"label": "NDIS Finance Mapping",
			"fieldtype": "Section Break",
			"insert_after": "requires_billing_setup",
		},
	]

	if doctype_exists(NDIS_SERVICE_TYPE):
		service_line_fields.append({
			"fieldname": "finance_service_type",
			"label": "Finance Service Type",
			"fieldtype": "Link",
			"options": NDIS_SERVICE_TYPE,
			"insert_after": "finance_mapping_section",
		})
	else:
		service_line_fields.append({
			"fieldname": "finance_service_type",
			"label": "Finance Service Type",
			"fieldtype": "Data",
			"insert_after": "finance_mapping_section",
		})

	if doctype_exists(NDIS_SUPPORT_ITEM):
		service_line_fields.append({
			"fieldname": "default_support_item",
			"label": "Default Support Item",
			"fieldtype": "Link",
			"options": NDIS_SUPPORT_ITEM,
			"insert_after": "finance_service_type",
		})
	else:
		service_line_fields.append({
			"fieldname": "default_support_item",
			"label": "Default Support Item",
			"fieldtype": "Data",
			"insert_after": "finance_service_type",
		})

	service_line_fields += [
		{
			"fieldname": "requires_plan_budget",
			"label": "Requires Plan Budget",
			"fieldtype": "Check",
			"default": 1,
			"insert_after": "default_support_item",
		},
		{
			"fieldname": "requires_service_booking",
			"label": "Requires Service Booking",
			"fieldtype": "Check",
			"default": 1,
			"insert_after": "requires_plan_budget",
		},
	]

	deal_fields = [
		{
			"fieldname": "finance_onboarding_section",
			"label": "NDIS Finance Onboarding",
			"fieldtype": "Section Break",
			"insert_after": "ndis_default_cost_center",
		},
		{
			"fieldname": "ndis_finance_onboarding_required",
			"label": "Finance Onboarding Required",
			"fieldtype": "Check",
			"default": 1,
			"insert_after": "finance_onboarding_section",
		},
		{
			"fieldname": "ndis_finance_onboarding",
			"label": "NDIS CRM Finance Onboarding",
			"fieldtype": "Link",
			"options": FINANCE_ONBOARDING,
			"read_only": 1,
			"insert_after": "ndis_finance_onboarding_required",
		},
		{
			"fieldname": "finance_onboarding_status",
			"label": "Finance Onboarding Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_finance_onboarding",
		},
		{
			"fieldname": "finance_onboarding_ready",
			"label": "Finance Onboarding Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "finance_onboarding_status",
		},
	]

	handover_fields = [
		{
			"fieldname": "finance_onboarding_section",
			"label": "NDIS Finance Onboarding",
			"fieldtype": "Section Break",
			"insert_after": "default_cost_center",
		},
		{
			"fieldname": "ndis_finance_onboarding",
			"label": "NDIS CRM Finance Onboarding",
			"fieldtype": "Link",
			"options": FINANCE_ONBOARDING,
			"read_only": 1,
			"insert_after": "finance_onboarding_section",
		},
		{
			"fieldname": "finance_onboarding_status",
			"label": "Finance Onboarding Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_finance_onboarding",
		},
		{
			"fieldname": "finance_onboarding_ready",
			"label": "Finance Onboarding Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "finance_onboarding_status",
		},
	]

	intake_fields = [
		{
			"fieldname": "finance_onboarding_section",
			"label": "NDIS Finance Onboarding",
			"fieldtype": "Section Break",
			"insert_after": "ndis_financial_profile",
		},
		{
			"fieldname": "ndis_finance_onboarding",
			"label": "NDIS CRM Finance Onboarding",
			"fieldtype": "Link",
			"options": FINANCE_ONBOARDING,
			"read_only": 1,
			"insert_after": "finance_onboarding_section",
		},
		{
			"fieldname": "finance_onboarding_status",
			"label": "Finance Onboarding Status",
			"fieldtype": "Data",
			"read_only": 1,
			"insert_after": "ndis_finance_onboarding",
		},
		{
			"fieldname": "finance_onboarding_ready",
			"label": "Finance Onboarding Ready",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "finance_onboarding_status",
		},
	]

	create_custom_fields(
		{
			"NDIS Service Line": service_line_fields,
			CRM_DEAL: deal_fields,
			HANDOVER: handover_fields,
			INTAKE: intake_fields,
		},
		update=True,
	)

	print("Created / updated Phase 5 custom fields.")


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
            createToast({
              title: "No Finance Onboarding linked yet",
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

        frm.add_custom_button(__("Create Finance Onboarding"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.create_finance_onboarding_from_handover",
                args: {
                    handover: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Creating Finance Onboarding...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({
                        message: r.message.message || __("Finance Onboarding created"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Finance Onboarding", r.message.name);
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

        if (frm.doc.ndis_finance_onboarding) {
            frm.add_custom_button(__("Open Finance Onboarding"), function () {
                frappe.set_route("Form", "NDIS CRM Finance Onboarding", frm.doc.ndis_finance_onboarding);
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
                args: {
                    onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Creating or linking financial profile...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Financial Profile linked"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Finance Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.validate_finance_onboarding_readiness",
                args: {
                    onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Validating finance readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Finance readiness validated"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Finance"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.mark_ready_for_finance",
                args: {
                    onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Marking ready for finance...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Ready for Finance"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Finance Setup Complete"), function () {
            frappe.call({
                method: "ndis_crm.phase5_finance_onboarding.mark_finance_setup_complete",
                args: {
                    onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Completing finance setup...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Finance setup completed"),
                        indicator: "green"
                    });
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

		upsert_doc(
			"Client Script",
			"NDIS CRM Finance Onboarding Actions",
			{
				"dt": "NDIS CRM Finance Onboarding",
				"view": "Form",
				"enabled": 1,
				"script": finance_onboarding_script,
			},
		)
