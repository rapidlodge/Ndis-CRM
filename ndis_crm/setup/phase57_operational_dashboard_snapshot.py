import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
PARTICIPANT_SERVICE_FILE = "NDIS Participant Service File"
CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"
POST_CLOSURE_ROUTING_FINALISATION_RUN = "NDIS CRM Post Closure Routing Finalisation Run"

OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"
OPERATIONAL_DASHBOARD_SNAPSHOT_LINE = "NDIS CRM Operational Dashboard Snapshot Line"


def install():
    ensure_required_doctypes()
    create_operational_dashboard_snapshot_doctypes()
    create_custom_fields_phase57()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 57 Operational Dashboard Snapshot installed successfully.")


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
        CARE_MANAGEMENT_INTEGRATION_RUN,
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        "Customer",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 57 DocTypes: " + ", ".join(missing))

    print("Required Phase 57 DocTypes found.")


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


def create_operational_dashboard_snapshot_doctypes():
    create_operational_dashboard_snapshot_line()
    create_operational_dashboard_snapshot_run()


def create_operational_dashboard_snapshot_line():
    fields = [
        make_field("Module Area", "module_area", "Data", in_list_view=1),
        make_field("Module Stage", "module_stage", "Data", in_list_view=1),
        make_field("Source", "source_section", "Section Break"),
        make_field("Source DocType", "source_doctype", "Data"),
        make_field("Source Record", "source_record", "Data", in_list_view=1),
        make_field("Source Status", "source_status", "Small Text", in_list_view=1),
        make_field("Source Ready", "source_ready", "Check", default="0", in_list_view=1),
        make_field("Stage Category", "stage_category", "Select", options="Ready / Complete\nIn Progress\nNeeds Attention\nNot Started", in_list_view=1),
        make_field("Action Required", "action_required", "Small Text"),

        make_field("Review", "review_section", "Section Break"),
        make_field("Snapshot Review Complete", "snapshot_review_complete", "Check", default="0"),
        make_field("Snapshot Data Verified", "snapshot_data_verified", "Check", default="0"),
        make_field("Line Ready for Dashboard", "line_ready_for_dashboard", "Check", default="0", in_list_view=1),
        make_field("Dashboard Line Status", "dashboard_line_status", "Select", options="Draft\nReady\nApproved\nDashboard Line Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=OPERATIONAL_DASHBOARD_SNAPSHOT_LINE,
        fields=fields,
        istable=1,
    )


def create_operational_dashboard_snapshot_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-OPS-DASH-SNAPSHOT-.YYYY.-.#####", default="NDIS-OPS-DASH-SNAPSHOT-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Dashboard Completion\nDashboard Snapshot Approved\nDashboard Snapshot Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Snapshot Mode", "snapshot_mode", "Select", options="Read Only Operational Snapshot", default="Read Only Operational Snapshot"),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Overall Completion %", "overall_completion_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Operational Dashboard Snapshot Run Ready", "operational_dashboard_snapshot_run_ready", "Check", read_only=1, in_list_view=1),

        make_field("Dashboard Review Complete", "dashboard_review_complete", "Check", default="0"),
        make_field("Dashboard Data Verified", "dashboard_data_verified", "Check", default="0"),
        make_field("Dashboard Completion Allowed", "dashboard_completion_allowed", "Check", default="0"),

        make_field("Blocked Controls", "blocked_controls_section", "Section Break"),
        make_field("Record Creation Allowed", "record_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Record Update Allowed", "record_update_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Communication Creation Allowed", "communication_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Email Send Allowed", "email_send_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("ToDo Creation Allowed", "todo_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Task Creation Allowed", "task_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Finance Document Creation Allowed", "finance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Claim Document Creation Allowed", "claim_document_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Remittance Document Creation Allowed", "remittance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),
        make_field("Accounting Document Creation Allowed", "accounting_document_creation_allowed", "Check", default="0", description="Blocked in Phase 57."),

        make_field("Source Links", "source_links_section", "Section Break"),
        make_field("CRM Lead", "crm_lead", "Data"),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1, reqd=1),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
        make_field("Participant Service File", "participant_service_file", "Link", options=PARTICIPANT_SERVICE_FILE, in_list_view=1),
        make_field("Care Management Integration Run", "care_management_integration_run", "Link", options=CARE_MANAGEMENT_INTEGRATION_RUN),
        make_field("Post Closure Routing Finalisation Run", "post_closure_routing_finalisation_run", "Link", options=POST_CLOSURE_ROUTING_FINALISATION_RUN),

        make_field("Participant Details", "participant_details_section", "Section Break"),
        make_field("Participant Name", "participant_name", "Data", in_list_view=1),
        make_field("NDIS Number", "ndis_number", "Data"),
        make_field("Plan Start Date", "plan_start_date", "Date"),
        make_field("Plan End Date", "plan_end_date", "Date"),
        make_field("Company", "company", "Link", options="Company"),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Snapshot Line Count", "snapshot_line_count", "Int", read_only=1),
        make_field("Ready Stage Count", "ready_stage_count", "Int", read_only=1),
        make_field("In Progress Stage Count", "in_progress_stage_count", "Int", read_only=1),
        make_field("Attention Stage Count", "attention_stage_count", "Int", read_only=1),
        make_field("Not Started Stage Count", "not_started_stage_count", "Int", read_only=1),
        make_field("Linked Stage Count", "linked_stage_count", "Int", read_only=1),
        make_field("Dashboard Completed Line Count", "dashboard_completed_line_count", "Int", read_only=1),

        make_field("Area Summary", "area_summary_section", "Section Break"),
        make_field("CRM Stage Count", "crm_stage_count", "Int", read_only=1),
        make_field("Finance Stage Count", "finance_stage_count", "Int", read_only=1),
        make_field("Operations Stage Count", "operations_stage_count", "Int", read_only=1),
        make_field("Care Management Stage Count", "care_management_stage_count", "Int", read_only=1),
        make_field("Service Delivery Stage Count", "service_delivery_stage_count", "Int", read_only=1),
        make_field("Billing Stage Count", "billing_stage_count", "Int", read_only=1),
        make_field("Claim Stage Count", "claim_stage_count", "Int", read_only=1),
        make_field("Invoice Stage Count", "invoice_stage_count", "Int", read_only=1),
        make_field("Remittance Stage Count", "remittance_stage_count", "Int", read_only=1),
        make_field("Payment Stage Count", "payment_stage_count", "Int", read_only=1),
        make_field("Variance Stage Count", "variance_stage_count", "Int", read_only=1),
        make_field("Write Off Stage Count", "write_off_stage_count", "Int", read_only=1),
        make_field("Recovery Stage Count", "recovery_stage_count", "Int", read_only=1),
        make_field("Post Closure Stage Count", "post_closure_stage_count", "Int", read_only=1),

        make_field("Blocked Summary", "blocked_summary_section", "Section Break"),
        make_field("Blocked Record Creation Count", "blocked_record_creation_count", "Int", read_only=1),
        make_field("Blocked Record Update Count", "blocked_record_update_count", "Int", read_only=1),
        make_field("Blocked Communication Count", "blocked_communication_count", "Int", read_only=1),
        make_field("Blocked Email Send Count", "blocked_email_send_count", "Int", read_only=1),
        make_field("Blocked Event Count", "blocked_event_count", "Int", read_only=1),
        make_field("Blocked ToDo Count", "blocked_todo_count", "Int", read_only=1),
        make_field("Blocked Task Count", "blocked_task_count", "Int", read_only=1),
        make_field("Blocked Finance Creation Count", "blocked_finance_creation_count", "Int", read_only=1),
        make_field("Blocked Claim Creation Count", "blocked_claim_creation_count", "Int", read_only=1),
        make_field("Blocked Remittance Creation Count", "blocked_remittance_creation_count", "Int", read_only=1),
        make_field("Blocked Accounting Creation Count", "blocked_accounting_creation_count", "Int", read_only=1),

        make_field("Owners", "owners_section", "Section Break"),
        make_field("Operational Dashboard Owner", "operational_dashboard_owner", "Link", options="User", in_list_view=1),
        make_field("Completed By", "completed_by", "Link", options="User", read_only=1),
        make_field("Completed On", "completed_on", "Datetime", read_only=1),

        make_field("Snapshot Lines", "snapshot_lines_section", "Section Break"),
        make_field("Operational Dashboard Snapshot Lines", "operational_dashboard_snapshot_lines", "Table", options=OPERATIONAL_DASHBOARD_SNAPSHOT_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Dashboard Notes", "dashboard_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase57():
    deal_fields = [
        {
            "fieldname": "operational_dashboard_snapshot_section",
            "label": "NDIS Operational Dashboard Snapshot",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_operational_dashboard_snapshot_required",
            "label": "Operational Dashboard Snapshot Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
        },
        {
            "fieldname": "ndis_operational_dashboard_snapshot_run",
            "label": "NDIS CRM Operational Dashboard Snapshot Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "operational_dashboard_snapshot_status",
            "label": "Operational Dashboard Snapshot Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "operational_dashboard_snapshot_ready",
            "label": "Operational Dashboard Snapshot Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    shared_fields = [
        {
            "fieldname": "operational_dashboard_snapshot_section",
            "label": "NDIS Operational Dashboard Snapshot",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_operational_dashboard_snapshot_run",
            "label": "NDIS CRM Operational Dashboard Snapshot Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "operational_dashboard_snapshot_status",
            "label": "Operational Dashboard Snapshot Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "operational_dashboard_snapshot_ready",
            "label": "Operational Dashboard Snapshot Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    custom_fields = {
        CRM_DEAL: deal_fields,
        PARTICIPANT_SERVICE_FILE: shared_fields,
        CARE_MANAGEMENT_INTEGRATION_RUN: shared_fields,
        POST_CLOSURE_ROUTING_FINALISATION_RUN: shared_fields,
    }

    safe_create_custom_fields(custom_fields)
    print("Created / updated Phase 57 operational dashboard snapshot custom fields.")


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


def _phase57_deal_actions():
    return r'''
// NDIS CRM Phase 57 Deal Actions
{
  label: "Create Operational Dashboard Snapshot",
  onClick: () => {
    call("ndis_crm.phase57_operational_dashboard_snapshot.create_operational_dashboard_snapshot_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Operational Dashboard Snapshot Created" : "Existing Operational Dashboard Snapshot Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-operational-dashboard-snapshot-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Operational Dashboard Snapshot",
  onClick: () => {
    if (doc.ndis_operational_dashboard_snapshot_run) {
      window.open(`/app/ndis-crm-operational-dashboard-snapshot-run/${doc.ndis_operational_dashboard_snapshot_run}`, "_blank")
    } else {
      createToast({ title: "No Operational Dashboard Snapshot linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    phase57_actions = _phase57_deal_actions()
    try:
        from ndis_crm.setup.phase56_care_management_integration import _deal_script as phase56_deal_script

        base = phase56_deal_script()
    except Exception:
        base = ""

    if "NDIS CRM Phase 57 Deal Actions" in base:
        return base

    addition = f",\n    {phase57_actions}"
    if "actions: [" in base:
        return _append_before_last(base, "]", addition)

    fallback = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
      __PHASE57_ACTIONS__
    ]
  }
}
'''.strip()
    return fallback.replace("__PHASE57_ACTIONS__", phase57_actions)


def create_or_extend_crm_deal_script():
    existing_script = ""
    if frappe.db.exists("CRM Form Script", "NDIS CRM Deal Actions"):
        existing_script = frappe.db.get_value("CRM Form Script", "NDIS CRM Deal Actions", "script") or ""

    if "NDIS CRM Phase 57 Deal Actions" in existing_script:
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
frappe.ui.form.on("NDIS CRM Care Management Integration Run", {
    refresh(frm) {
        if (frm.is_new() || !frm.doc.crm_deal) {
            return;
        }

        frm.add_custom_button(__("Create Operational Dashboard Snapshot"), function () {
            frappe.call({
                method: "ndis_crm.phase57_operational_dashboard_snapshot.create_operational_dashboard_snapshot_from_crm_deal",
                args: { deal: frm.doc.crm_deal },
                freeze: true,
                freeze_message: __("Creating operational dashboard snapshot...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Operational Dashboard Snapshot created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Operational Dashboard Snapshot Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_operational_dashboard_snapshot_run) {
            frm.add_custom_button(__("Open Operational Dashboard Snapshot"), function () {
                frappe.set_route("Form", "NDIS CRM Operational Dashboard Snapshot Run", frm.doc.ndis_operational_dashboard_snapshot_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Operational Dashboard Snapshot Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Refresh Snapshot Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase57_operational_dashboard_snapshot.refresh_operational_dashboard_snapshot_lines",
                args: { operational_dashboard_snapshot_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Refreshing operational dashboard snapshot lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Snapshot lines refreshed"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Dashboard Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase57_operational_dashboard_snapshot.validate_operational_dashboard_snapshot_readiness",
                args: { operational_dashboard_snapshot_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating dashboard readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Dashboard readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Dashboard"), function () {
            frappe.call({
                method: "ndis_crm.phase57_operational_dashboard_snapshot.mark_ready_for_operational_dashboard_snapshot",
                args: { operational_dashboard_snapshot_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for dashboard completion...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for dashboard completion"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Dashboard Snapshot"), function () {
            frappe.call({
                method: "ndis_crm.phase57_operational_dashboard_snapshot.approve_operational_dashboard_snapshot_run",
                args: { operational_dashboard_snapshot_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving dashboard snapshot...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Dashboard Snapshot approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Complete Dashboard Snapshot"), function () {
            frappe.confirm(
                __("This completes the read-only operational dashboard snapshot. It will not create or update Care Management, communication, task, finance, claim, remittance, payment, journal, adjustment, or bank reconciliation records."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase57_operational_dashboard_snapshot.complete_operational_dashboard_snapshot",
                        args: { operational_dashboard_snapshot_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Completing dashboard snapshot...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Dashboard snapshot completed"), indicator: "green" });
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

        if (frm.doc.care_management_integration_run) {
            frm.add_custom_button(__("Open Care Management Integration"), function () {
                frappe.set_route("Form", "NDIS CRM Care Management Integration Run", frm.doc.care_management_integration_run);
            }, __("Open"));
        }

        if (frm.doc.participant_service_file) {
            frm.add_custom_button(__("Open Participant Service File"), function () {
                frappe.set_route("Form", "NDIS Participant Service File", frm.doc.participant_service_file);
            }, __("Open"));
        }
    }
});
'''.strip()

    if frappe.db.exists("DocType", "Client Script"):
        upsert_doc(
            "Client Script",
            "NDIS CRM Care Management Integration Phase57 Actions",
            {
                "dt": CARE_MANAGEMENT_INTEGRATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": source_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Operational Dashboard Snapshot Run Actions",
            {
                "dt": OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
