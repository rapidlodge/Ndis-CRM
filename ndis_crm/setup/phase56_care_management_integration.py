import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
PARTICIPANT_SERVICE_FILE = "NDIS Participant Service File"

POST_CLOSURE_ROUTING_FINALISATION_RUN = "NDIS CRM Post Closure Routing Finalisation Run"
POST_CLOSURE_ROUTING_PREPARATION_RUN = "NDIS CRM Post Closure Routing Preparation Run"
RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN = "NDIS CRM Recovery Outcome Closure Finalisation Run"

CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"
CARE_MANAGEMENT_INTEGRATION_LINE = "NDIS CRM Care Management Integration Line"


def install():
    ensure_required_doctypes()
    create_care_management_integration_doctypes()
    create_custom_fields_phase56()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 56 Care Management Integration bridge installed successfully.")


def doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


def safe_create_custom_fields(custom_fields):
    try:
        create_custom_fields(custom_fields, update=True)
    except TypeError:
        create_custom_fields(custom_fields)


def ensure_required_doctypes():
    required = [
        CRM_DEAL,
        PARTICIPANT_SERVICE_FILE,
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        "Customer",
        "DocType",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 56 DocTypes: " + ", ".join(missing))

    print("Required Phase 56 DocTypes found.")


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


def create_care_management_integration_doctypes():
    create_care_management_integration_line()
    create_care_management_integration_run()


def create_care_management_integration_line():
    fields = [
        make_field("Integration Area", "integration_area", "Select", options="Care Management Profile\nCare Plan / Daily Activity Plan\nMedication Plan\nIncident Management\nNDIS Task Library\nStaff Assignment / Responsibility\nService Delivery / Shift Execution\nProgress Notes / Evidence", in_list_view=1),
        make_field("Integration Description", "integration_description", "Small Text"),
        make_field("Record Required", "record_required", "Check", default="0", in_list_view=1),

        make_field("Target Care Management Record", "target_care_section", "Section Break"),
        make_field("Target Care DocType", "target_care_doctype", "Link", options="DocType", in_list_view=1),
        make_field("Target Care Record", "target_care_record", "Dynamic Link", options="target_care_doctype", in_list_view=1),
        make_field("Target Care Record Title", "target_care_record_title", "Data"),
        make_field("Target Care Record Status", "target_care_record_status", "Data", in_list_view=1),
        make_field("Target Care Record Owner", "target_care_record_owner", "Link", options="User"),
        make_field("Target Care Last Checked On", "target_care_last_checked_on", "Datetime", read_only=1),

        make_field("Participant Snapshot", "participant_section", "Section Break"),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer"),
        make_field("Participant Service File", "participant_service_file", "Link", options=PARTICIPANT_SERVICE_FILE),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL),
        make_field("Participant Name", "participant_name", "Data"),
        make_field("NDIS Number", "ndis_number", "Data"),

        make_field("Integration Controls", "integration_controls_section", "Section Break"),
        make_field("Integration Source Ready", "integration_source_ready", "Check", default="0"),
        make_field("Link Confirmed", "link_confirmed", "Check", default="0"),
        make_field("Data Scope Confirmed", "data_scope_confirmed", "Check", default="0"),
        make_field("No Duplicate Record Confirmed", "no_duplicate_record_confirmed", "Check", default="0"),
        make_field("Read Only Bridge Confirmed", "read_only_bridge_confirmed", "Check", default="0"),
        make_field("Owner Confirmed", "owner_confirmed", "Check", default="0"),
        make_field("Operational Visibility Confirmed", "operational_visibility_confirmed", "Check", default="0"),
        make_field("Integration Authorized", "integration_authorized", "Check", default="0"),

        make_field("Blocked Controls", "blocked_controls_section", "Section Break"),
        make_field("Care Management Record Creation Authorized", "care_management_record_creation_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Care Management Record Update Authorized", "care_management_record_update_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Care Management Record Delete Authorized", "care_management_record_delete_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Communication Creation Authorized", "communication_creation_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Email Send Authorized", "email_send_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Event Creation Authorized", "event_creation_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("ToDo Creation Authorized", "todo_creation_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Task Creation Authorized", "task_creation_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Recovery Case Creation Authorized", "recovery_case_creation_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Journal Entry Authorized", "journal_entry_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Manual GL Authorized", "manual_gl_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Payment Entry Authorized", "payment_entry_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Sales Invoice Authorized", "sales_invoice_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Adjustment Authorized", "adjustment_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Bank Reconciliation Authorized", "bank_reconciliation_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Claim Batch Authorized", "claim_batch_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Claim Line Authorized", "claim_line_authorized", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Remittance Import Authorized", "remittance_import_authorized", "Check", default="0", description="Blocked in Phase 56."),

        make_field("Line Status", "line_status_section", "Section Break"),
        make_field("Integration Hold", "integration_hold", "Check", default="0", in_list_view=1),
        make_field("Integration Hold Reason", "integration_hold_reason", "Small Text"),
        make_field("Line Ready for Integration", "line_ready_for_integration", "Check", default="0", in_list_view=1),
        make_field("Integration Line Status", "integration_line_status", "Select", options="Draft\nReady\nApproved\nIntegration Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=CARE_MANAGEMENT_INTEGRATION_LINE,
        fields=fields,
        istable=1,
    )


def create_care_management_integration_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-CARE-MGMT-INTEGRATION-.YYYY.-.#####", default="NDIS-CARE-MGMT-INTEGRATION-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Integration\nIntegration Approved\nIntegration Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Care Management Integration Run Ready", "care_management_integration_run_ready", "Check", read_only=1, in_list_view=1),
        make_field("Integration Mode", "integration_mode", "Select", options="Reference Existing Care Management Records Only", default="Reference Existing Care Management Records Only"),
        make_field("Integration Completion Allowed", "integration_completion_allowed", "Check", default="0"),

        make_field("Blocked Run Controls", "blocked_run_controls_section", "Section Break"),
        make_field("Care Management Record Creation Allowed", "care_management_record_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Care Management Record Update Allowed", "care_management_record_update_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Care Management Record Delete Allowed", "care_management_record_delete_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Communication Creation Allowed", "communication_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Email Send Allowed", "email_send_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("ToDo Creation Allowed", "todo_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Task Creation Allowed", "task_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Recovery Case Creation Allowed", "recovery_case_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Journal Entry Creation Allowed", "journal_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Manual GL Creation Allowed", "manual_gl_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Payment Entry Creation Allowed", "payment_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Adjustment Creation Allowed", "adjustment_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Bank Reconciliation Allowed", "bank_reconciliation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Claim Batch Creation Allowed", "claim_batch_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Claim Line Creation Allowed", "claim_line_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),
        make_field("Remittance Import Creation Allowed", "remittance_import_creation_allowed", "Check", default="0", description="Blocked in Phase 56."),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Integration Line Count", "integration_line_count", "Int", read_only=1),
        make_field("Required Integration Line Count", "required_integration_line_count", "Int", read_only=1),
        make_field("Linked Integration Line Count", "linked_integration_line_count", "Int", read_only=1),
        make_field("Ready Integration Line Count", "ready_integration_line_count", "Int", read_only=1),
        make_field("Hold Integration Line Count", "hold_integration_line_count", "Int", read_only=1),
        make_field("Integration Completed Count", "integration_completed_count", "Int", read_only=1),
        make_field("Care Profile Linked Count", "care_profile_linked_count", "Int", read_only=1),
        make_field("Care Plan Linked Count", "care_plan_linked_count", "Int", read_only=1),
        make_field("Medication Plan Linked Count", "medication_plan_linked_count", "Int", read_only=1),
        make_field("Incident Management Linked Count", "incident_management_linked_count", "Int", read_only=1),
        make_field("Task Library Linked Count", "task_library_linked_count", "Int", read_only=1),
        make_field("Staff Assignment Linked Count", "staff_assignment_linked_count", "Int", read_only=1),
        make_field("Service Delivery Linked Count", "service_delivery_linked_count", "Int", read_only=1),
        make_field("Progress Notes Linked Count", "progress_notes_linked_count", "Int", read_only=1),

        make_field("Blocked Summary", "blocked_summary_section", "Section Break"),
        make_field("Blocked Care Create Count", "blocked_care_create_count", "Int", read_only=1),
        make_field("Blocked Care Update Count", "blocked_care_update_count", "Int", read_only=1),
        make_field("Blocked Care Delete Count", "blocked_care_delete_count", "Int", read_only=1),
        make_field("Blocked Communication Count", "blocked_communication_count", "Int", read_only=1),
        make_field("Blocked Email Send Count", "blocked_email_send_count", "Int", read_only=1),
        make_field("Blocked Event Count", "blocked_event_count", "Int", read_only=1),
        make_field("Blocked ToDo Count", "blocked_todo_count", "Int", read_only=1),
        make_field("Blocked Task Count", "blocked_task_count", "Int", read_only=1),
        make_field("Blocked Recovery Case Creation Count", "blocked_recovery_case_creation_count", "Int", read_only=1),
        make_field("Blocked Journal Entry Count", "blocked_journal_entry_count", "Int", read_only=1),
        make_field("Blocked Manual GL Count", "blocked_manual_gl_count", "Int", read_only=1),
        make_field("Blocked Payment Entry Count", "blocked_payment_entry_count", "Int", read_only=1),
        make_field("Blocked Sales Invoice Count", "blocked_sales_invoice_count", "Int", read_only=1),
        make_field("Blocked Adjustment Count", "blocked_adjustment_count", "Int", read_only=1),
        make_field("Blocked Bank Reconciliation Count", "blocked_bank_reconciliation_count", "Int", read_only=1),
        make_field("Blocked Claim Batch Count", "blocked_claim_batch_count", "Int", read_only=1),
        make_field("Blocked Claim Line Count", "blocked_claim_line_count", "Int", read_only=1),
        make_field("Blocked Remittance Import Count", "blocked_remittance_import_count", "Int", read_only=1),

        make_field("Source Links", "source_links_section", "Section Break"),
        make_field("CRM Lead", "crm_lead", "Data"),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
        make_field("Participant Intake", "participant_intake", "Data"),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
        make_field("Participant Service File", "participant_service_file", "Link", options=PARTICIPANT_SERVICE_FILE, in_list_view=1),
        make_field("NDIS Financial Profile", "ndis_financial_profile", "Data"),

        make_field("Post Closure Routing Finalisation Run", "post_closure_routing_finalisation_run", "Link", options=POST_CLOSURE_ROUTING_FINALISATION_RUN, reqd=1, in_list_view=1),
        make_field("Post Closure Routing Preparation Run", "post_closure_routing_preparation_run", "Link", options=POST_CLOSURE_ROUTING_PREPARATION_RUN),
        make_field("Recovery Outcome Closure Finalisation Run", "recovery_outcome_closure_finalisation_run", "Link", options=RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN),
        make_field("Recovery Outcome Closure Draft Run", "recovery_outcome_closure_draft_run", "Data"),
        make_field("Recovery Outcome Closure Preparation Run", "recovery_outcome_closure_preparation_run", "Data"),
        make_field("Recovery Outcome Action Completion Run", "recovery_outcome_action_completion_run", "Data"),

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
        make_field("Care Management Integration Owner", "care_management_integration_owner", "Link", options="User", in_list_view=1),
        make_field("Post Closure Routing Finalisation Owner", "post_closure_routing_finalisation_owner", "Link", options="User"),
        make_field("Completed By", "completed_by", "Link", options="User", read_only=1),
        make_field("Completed On", "completed_on", "Datetime", read_only=1),

        make_field("Care Management Integration Lines", "care_management_integration_lines_section", "Section Break"),
        make_field("Care Management Integration Lines", "care_management_integration_lines", "Table", options=CARE_MANAGEMENT_INTEGRATION_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Care Management Integration Notes", "care_management_integration_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=CARE_MANAGEMENT_INTEGRATION_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase56():
    deal_fields = [
        {
            "fieldname": "care_management_integration_section",
            "label": "NDIS Care Management Integration",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_care_management_integration_required",
            "label": "Care Management Integration Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
        },
        {
            "fieldname": "ndis_care_management_integration_run",
            "label": "NDIS CRM Care Management Integration Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "care_management_integration_status",
            "label": "Care Management Integration Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "care_management_integration_ready",
            "label": "Care Management Integration Ready",
            "fieldtype": "Check",
            "default": "0",
            "read_only": 1,
        },
    ]

    shared_fields = [
        {
            "fieldname": "care_management_integration_section",
            "label": "NDIS Care Management Integration",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_care_management_integration_run",
            "label": "NDIS CRM Care Management Integration Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "care_management_integration_status",
            "label": "Care Management Integration Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "care_management_integration_ready",
            "label": "Care Management Integration Ready",
            "fieldtype": "Check",
            "default": "0",
            "read_only": 1,
        },
    ]

    custom_fields = {
        CRM_DEAL: deal_fields,
        PARTICIPANT_SERVICE_FILE: shared_fields,
        POST_CLOSURE_ROUTING_FINALISATION_RUN: shared_fields,
        POST_CLOSURE_ROUTING_PREPARATION_RUN: shared_fields,
        RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN: shared_fields,
    }

    safe_create_custom_fields(custom_fields)
    print("Created / updated Phase 56 care management integration custom fields.")


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


def _append_before_last(source, marker, addition):
    index = source.rfind(marker)
    if index == -1:
        return source.rstrip() + "\n" + addition

    return source[:index].rstrip() + addition + "\n" + source[index:]


def _phase56_deal_actions():
    return r'''
// NDIS CRM Phase 56 Deal Actions
{
  label: "Create Care Management Integration Run",
  onClick: () => {
    call("ndis_crm.phase56_care_management_integration.create_care_management_integration_run_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Care Management Integration Run Created" : "Existing Care Management Integration Run Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-care-management-integration-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Care Management Integration Run",
  onClick: () => {
    if (doc.ndis_care_management_integration_run) {
      window.open(`/app/ndis-crm-care-management-integration-run/${doc.ndis_care_management_integration_run}`, "_blank")
    } else {
      createToast({ title: "No Care Management Integration Run linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    phase56_actions = _phase56_deal_actions()
    try:
        from ndis_crm.setup.phase55_post_closure_routing_finalisation import _deal_script as phase55_deal_script

        base = phase55_deal_script()
    except Exception:
        base = ""

    if "NDIS CRM Phase 56 Deal Actions" in base:
        return base

    addition = f",\n    {phase56_actions}"
    if "actions: [" in base:
        return _append_before_last(base, "]", addition)

    fallback = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
      __PHASE56_ACTIONS__
    ]
  }
}
'''.strip()
    return fallback.replace("__PHASE56_ACTIONS__", phase56_actions)


def create_or_extend_crm_deal_script():
    existing_script = ""
    if frappe.db.exists("CRM Form Script", "NDIS CRM Deal Actions"):
        existing_script = frappe.db.get_value("CRM Form Script", "NDIS CRM Deal Actions", "script") or ""

    if "NDIS CRM Phase 56 Deal Actions" in existing_script:
        final_script = existing_script
    else:
        final_script = _deal_script()

    upsert_doc(
        "CRM Form Script",
        "NDIS CRM Deal Actions",
        {
            "dt": "CRM Deal",
            "view": "Form",
            "enabled": 1,
            "is_standard": 0,
            "script": final_script,
        },
    )


def create_form_scripts():
    create_or_extend_crm_deal_script()

    source_script = r'''
frappe.ui.form.on("NDIS CRM Post Closure Routing Finalisation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Care Management Integration Run"), function () {
            frappe.call({
                method: "ndis_crm.phase56_care_management_integration.create_care_management_integration_run_from_post_closure_finalisation",
                args: { post_closure_routing_finalisation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating care management integration run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Care Management Integration Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Care Management Integration Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_care_management_integration_run) {
            frm.add_custom_button(__("Open Care Management Integration Run"), function () {
                frappe.set_route("Form", "NDIS CRM Care Management Integration Run", frm.doc.ndis_care_management_integration_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Care Management Integration Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Integration Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase56_care_management_integration.generate_care_management_integration_lines",
                args: { care_management_integration_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating care management integration lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Integration lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Integration Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase56_care_management_integration.validate_care_management_integration_readiness",
                args: { care_management_integration_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating care management integration readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Integration readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Integration"), function () {
            frappe.call({
                method: "ndis_crm.phase56_care_management_integration.mark_ready_for_care_management_integration",
                args: { care_management_integration_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for integration...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for integration"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Integration Run"), function () {
            frappe.call({
                method: "ndis_crm.phase56_care_management_integration.approve_care_management_integration_run",
                args: { care_management_integration_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving integration run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Integration Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Complete Integration Bridge"), function () {
            frappe.confirm(
                __("This completes reference-only integration. It will not create or update Care Management records, communications, tasks, emails, accounting, claims, remittance, adjustment, or bank reconciliation records."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase56_care_management_integration.complete_care_management_integration",
                        args: { care_management_integration_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Completing care management integration...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Care Management Integration completed"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.post_closure_routing_finalisation_run) {
            frm.add_custom_button(__("Open Post Closure Routing Finalisation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Post Closure Routing Finalisation Run", frm.doc.post_closure_routing_finalisation_run);
            }, __("Open"));
        }

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

    if frappe.db.exists("DocType", "Client Script"):
        upsert_doc(
            "Client Script",
            "NDIS CRM Post Closure Routing Finalisation Phase56 Actions",
            {
                "dt": POST_CLOSURE_ROUTING_FINALISATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": source_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Care Management Integration Run Actions",
            {
                "dt": CARE_MANAGEMENT_INTEGRATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
