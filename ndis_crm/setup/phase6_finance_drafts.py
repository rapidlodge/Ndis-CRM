import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CRM_DEAL = "CRM Deal"
HANDOVER = "NDIS CRM Handover"
INTAKE = "NDIS Participant Intake"

FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
FINANCE_ONBOARDING_SERVICE = "NDIS CRM Finance Onboarding Service"

PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"


def install():
	ensure_required_doctypes()
	create_custom_fields_phase6()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 6 finance budget/service booking bridge installed successfully.")


def doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def ensure_required_doctypes():
	required = [
		FINANCE_ONBOARDING,
		FINANCE_ONBOARDING_SERVICE,
		PLAN_BUDGET,
		SERVICE_BOOKING,
		"NDIS Service Type",
		"NDIS Support Item",
		"NDIS Funding Source",
		"CRM Form Script",
	]

	missing = [dt for dt in required if not doctype_exists(dt)]

	if missing:
		frappe.throw("Missing required Phase 6 DocTypes: " + ", ".join(missing))

	print("Required Phase 6 DocTypes found.")


def create_custom_fields_phase6():
	onboarding_fields = [
		{
			"fieldname": "finance_record_creation_section",
			"label": "Finance Record Creation",
			"fieldtype": "Section Break",
			"insert_after": "finance_setup_notes",
		},
		{
			"fieldname": "allow_service_booking_creation",
			"label": "Allow Service Booking Creation",
			"fieldtype": "Check",
			"default": 0,
			"insert_after": "finance_record_creation_section",
			"description": "Tick only after finance confirms service bookings should be created. Service Booking records are Active in ndis_finance.",
		},
		{
			"fieldname": "plan_budget_count",
			"label": "Plan Budget Count",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "allow_service_booking_creation",
		},
		{
			"fieldname": "service_booking_count",
			"label": "Service Booking Count",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "plan_budget_count",
		},
		{
			"fieldname": "finance_records_created",
			"label": "Finance Records Created",
			"fieldtype": "Check",
			"read_only": 1,
			"insert_after": "service_booking_count",
		},
		{
			"fieldname": "finance_records_summary",
			"label": "Finance Records Summary",
			"fieldtype": "Small Text",
			"read_only": 1,
			"insert_after": "finance_records_created",
		},
	]

	onboarding_service_fields = [
		{
			"fieldname": "created_finance_records_section",
			"label": "Created Finance Records",
			"fieldtype": "Section Break",
			"insert_after": "notes",
		},
		{
			"fieldname": "draft_plan_budget",
			"label": "Draft NDIS Plan Budget",
			"fieldtype": "Link",
			"options": PLAN_BUDGET,
			"read_only": 1,
			"insert_after": "created_finance_records_section",
		},
		{
			"fieldname": "service_booking",
			"label": "NDIS Service Booking",
			"fieldtype": "Link",
			"options": SERVICE_BOOKING,
			"read_only": 1,
			"insert_after": "draft_plan_budget",
		},
		{
			"fieldname": "finance_record_status",
			"label": "Finance Record Status",
			"fieldtype": "Select",
			"options": "Not Started\nDraft Plan Budget Created\nService Booking Created\nBudget and Booking Created\nSkipped\nError",
			"default": "Not Started",
			"insert_after": "service_booking",
		},
		{
			"fieldname": "finance_creation_notes",
			"label": "Finance Creation Notes",
			"fieldtype": "Small Text",
			"insert_after": "finance_record_status",
		},
	]

	finance_source_fields = [
		{
			"fieldname": "ndis_crm_source_section",
			"label": "NDIS CRM Source",
			"fieldtype": "Section Break",
			"insert_after": "status",
		},
		{
			"fieldname": "ndis_crm_finance_onboarding",
			"label": "NDIS CRM Finance Onboarding",
			"fieldtype": "Link",
			"options": FINANCE_ONBOARDING,
			"read_only": 1,
			"insert_after": "ndis_crm_source_section",
		},
		{
			"fieldname": "ndis_crm_handover",
			"label": "NDIS CRM Handover",
			"fieldtype": "Link",
			"options": HANDOVER,
			"read_only": 1,
			"insert_after": "ndis_crm_finance_onboarding",
		},
		{
			"fieldname": "ndis_crm_deal",
			"label": "CRM Deal",
			"fieldtype": "Link",
			"options": CRM_DEAL,
			"read_only": 1,
			"insert_after": "ndis_crm_handover",
		},
		{
			"fieldname": "ndis_crm_service_line",
			"label": "NDIS CRM Service Line",
			"fieldtype": "Link",
			"options": "NDIS Service Line",
			"read_only": 1,
			"insert_after": "ndis_crm_deal",
		},
		{
			"fieldname": "ndis_crm_source_notes",
			"label": "NDIS CRM Source Notes",
			"fieldtype": "Small Text",
			"read_only": 1,
			"insert_after": "ndis_crm_service_line",
		},
	]

	service_booking_extra_fields = [
		{
			"fieldname": "ndis_crm_plan_budget",
			"label": "NDIS CRM Plan Budget",
			"fieldtype": "Link",
			"options": PLAN_BUDGET,
			"read_only": 1,
			"insert_after": "ndis_crm_service_line",
		},
	]

	deal_fields = [
		{
			"fieldname": "finance_records_section",
			"label": "NDIS Finance Records",
			"fieldtype": "Section Break",
			"insert_after": "finance_onboarding_ready",
		},
		{
			"fieldname": "finance_plan_budget_count",
			"label": "Finance Plan Budget Count",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "finance_records_section",
		},
		{
			"fieldname": "finance_service_booking_count",
			"label": "Finance Service Booking Count",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "finance_plan_budget_count",
		},
	]

	handover_fields = [
		{
			"fieldname": "finance_records_section",
			"label": "NDIS Finance Records",
			"fieldtype": "Section Break",
			"insert_after": "finance_onboarding_ready",
		},
		{
			"fieldname": "finance_plan_budget_count",
			"label": "Finance Plan Budget Count",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "finance_records_section",
		},
		{
			"fieldname": "finance_service_booking_count",
			"label": "Finance Service Booking Count",
			"fieldtype": "Int",
			"read_only": 1,
			"insert_after": "finance_plan_budget_count",
		},
	]

	create_custom_fields(
		{
			FINANCE_ONBOARDING: onboarding_fields,
			FINANCE_ONBOARDING_SERVICE: onboarding_service_fields,
			PLAN_BUDGET: finance_source_fields,
			SERVICE_BOOKING: finance_source_fields + service_booking_extra_fields,
			CRM_DEAL: deal_fields,
			HANDOVER: handover_fields,
		},
		update=True,
	)

	print("Created / updated Phase 6 custom fields.")


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

        frm.add_custom_button(__("Create Draft Plan Budgets"), function () {
            frappe.call({
                method: "ndis_crm.phase6_finance_drafts.create_draft_plan_budgets_from_onboarding",
                args: {
                    onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Creating draft plan budgets...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Draft plan budgets created"),
                        indicator: "green"
                    });
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
                        args: {
                            onboarding: frm.doc.name
                        },
                        freeze: true,
                        freeze_message: __("Creating service bookings...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({
                                message: r.message.message || __("Service bookings created"),
                                indicator: "green"
                            });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Finance Records"));

        frm.add_custom_button(__("Recalculate Finance Records"), function () {
            frappe.call({
                method: "ndis_crm.phase6_finance_drafts.recalculate_finance_record_summary",
                args: {
                    onboarding: frm.doc.name
                },
                freeze: true,
                freeze_message: __("Recalculating finance records...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({
                        message: r.message.message || __("Finance records recalculated"),
                        indicator: "green"
                    });
                    frm.reload_doc();
                }
            });
        }, __("Finance Records"));

        frm.add_custom_button(__("Open Plan Budgets"), function () {
            frappe.route_options = {
                ndis_crm_finance_onboarding: frm.doc.name
            };
            frappe.set_route("List", "NDIS Plan Budget");
        }, __("Open"));

        frm.add_custom_button(__("Open Service Bookings"), function () {
            frappe.route_options = {
                ndis_crm_finance_onboarding: frm.doc.name
            };
            frappe.set_route("List", "NDIS Service Booking");
        }, __("Open"));

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
		"Client Script",
		"NDIS CRM Finance Onboarding Actions",
		{
			"dt": FINANCE_ONBOARDING,
			"view": "Form",
			"enabled": 1,
			"script": finance_onboarding_script,
		},
	)
