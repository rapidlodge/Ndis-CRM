import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"

PERMISSION_WORKFLOW_HARDENING_RUN = "NDIS CRM Permission Workflow Hardening Run"
PERMISSION_WORKFLOW_HARDENING_LINE = "NDIS CRM Permission Workflow Hardening Line"


def install():
    ensure_required_doctypes()
    create_permission_workflow_hardening_doctypes()
    create_custom_fields_phase58()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 58 Permission Workflow Hardening installed successfully.")


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
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        "Role",
        "DocType",
        "DocPerm",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 58 DocTypes: " + ", ".join(missing))

    print("Required Phase 58 DocTypes found.")


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
        {"role": "NDIS CRM Manager", "read": 1, "write": 1, "create": 1, "delete": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1},
        {"role": "NDIS Plan Management Officer", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
        {"role": "Accounts Manager", "read": 1, "write": 1, "create": 1, "email": 1, "export": 1, "print": 1, "report": 1},
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


def create_permission_workflow_hardening_doctypes():
    create_permission_workflow_hardening_line()
    create_permission_workflow_hardening_run()


def create_permission_workflow_hardening_line():
    fields = [
        make_field("Hardening Area", "hardening_area", "Select", options="Role Coverage\nDocType Permission Coverage\nCRM Deal Validator Chain\nOperational Dashboard Readiness\nCare Management Boundary\nBusiness Transaction Boundary\nAccounting Boundary\nFixture Scope\nClient Script Coverage\nMigration Fixture Safety\nRuntime Side Effect Safety\nRepository Hygiene", in_list_view=1),
        make_field("Target DocType", "target_doctype", "Link", options="DocType", in_list_view=1),
        make_field("Expected Control", "expected_control", "Small Text"),

        make_field("Observation", "observation_section", "Section Break"),
        make_field("Observed Status", "observed_status", "Select", options="Pass\nManual Review\nNeeds Attention", in_list_view=1),
        make_field("Observed Result", "observed_result", "Small Text"),
        make_field("Risk Level", "risk_level", "Select", options="High\nMedium\nLow", default="Low", in_list_view=1),

        make_field("Review Controls", "review_section", "Section Break"),
        make_field("Hardening Review Complete", "hardening_review_complete", "Check", default="0"),
        make_field("Hardening Control Verified", "hardening_control_verified", "Check", default="0"),
        make_field("Implementation Required", "implementation_required", "Check", default="0"),
        make_field("Implementation Note", "implementation_note", "Small Text"),
        make_field("Line Ready for Hardening", "line_ready_for_hardening", "Check", default="0", in_list_view=1),
        make_field("Hardening Line Status", "hardening_line_status", "Select", options="Draft\nReady\nApproved\nHardening Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=PERMISSION_WORKFLOW_HARDENING_LINE,
        fields=fields,
        istable=1,
    )


def create_permission_workflow_hardening_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-PERM-WORKFLOW-HARDEN-.YYYY.-.#####", default="NDIS-PERM-WORKFLOW-HARDEN-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Hardening Approval\nHardening Approved\nHardening Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Hardening Mode", "hardening_mode", "Select", options="Assessment and Controlled Readiness Only", default="Assessment and Controlled Readiness Only"),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Hardening Completion %", "hardening_completion_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Permission Workflow Hardening Run Ready", "permission_workflow_hardening_run_ready", "Check", read_only=1, in_list_view=1),

        make_field("Review Controls", "review_controls_section", "Section Break"),
        make_field("Final Hardening Review Complete", "final_hardening_review_complete", "Check", default="0"),
        make_field("Boundary Review Complete", "boundary_review_complete", "Check", default="0"),
        make_field("Fixture Review Complete", "fixture_review_complete", "Check", default="0"),
        make_field("Permission Review Complete", "permission_review_complete", "Check", default="0"),
        make_field("Workflow Review Complete", "workflow_review_complete", "Check", default="0"),
        make_field("Hardening Completion Allowed", "hardening_completion_allowed", "Check", default="0"),

        make_field("Blocked Controls", "blocked_controls_section", "Section Break"),
        make_field("Role Creation Allowed", "role_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Permission Mutation Allowed", "permission_mutation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Workflow Mutation Allowed", "workflow_mutation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Business Record Creation Allowed", "business_record_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Communication Creation Allowed", "communication_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Email Send Allowed", "email_send_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("ToDo Creation Allowed", "todo_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Task Creation Allowed", "task_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Finance Document Creation Allowed", "finance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Claim Document Creation Allowed", "claim_document_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Remittance Document Creation Allowed", "remittance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),
        make_field("Accounting Document Creation Allowed", "accounting_document_creation_allowed", "Check", default="0", description="Blocked in Phase 58."),

        make_field("Source Links", "source_links_section", "Section Break"),
        make_field("CRM Lead", "crm_lead", "Data"),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
        make_field("Participant Service File", "participant_service_file", "Data"),
        make_field("Care Management Integration Run", "care_management_integration_run", "Data"),
        make_field("Operational Dashboard Snapshot Run", "operational_dashboard_snapshot_run", "Link", options=OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, reqd=1, in_list_view=1),

        make_field("Participant Details", "participant_details_section", "Section Break"),
        make_field("Participant Name", "participant_name", "Data", in_list_view=1),
        make_field("NDIS Number", "ndis_number", "Data"),
        make_field("Plan Start Date", "plan_start_date", "Date"),
        make_field("Plan End Date", "plan_end_date", "Date"),
        make_field("Company", "company", "Link", options="Company"),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Hardening Line Count", "hardening_line_count", "Int", read_only=1),
        make_field("Passed Control Count", "passed_control_count", "Int", read_only=1),
        make_field("Manual Review Count", "manual_review_count", "Int", read_only=1),
        make_field("Attention Control Count", "attention_control_count", "Int", read_only=1),
        make_field("Ready Hardening Line Count", "ready_hardening_line_count", "Int", read_only=1),
        make_field("Completed Hardening Line Count", "completed_hardening_line_count", "Int", read_only=1),
        make_field("Implementation Required Count", "implementation_required_count", "Int", read_only=1),
        make_field("High Risk Count", "high_risk_count", "Int", read_only=1),
        make_field("Medium Risk Count", "medium_risk_count", "Int", read_only=1),
        make_field("Low Risk Count", "low_risk_count", "Int", read_only=1),

        make_field("Owners", "owners_section", "Section Break"),
        make_field("Hardening Owner", "hardening_owner", "Link", options="User", in_list_view=1),
        make_field("Completed By", "completed_by", "Link", options="User", read_only=1),
        make_field("Completed On", "completed_on", "Datetime", read_only=1),

        make_field("Hardening Lines", "hardening_lines_section", "Section Break"),
        make_field("Permission Workflow Hardening Lines", "permission_workflow_hardening_lines", "Table", options=PERMISSION_WORKFLOW_HARDENING_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Hardening Notes", "hardening_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=PERMISSION_WORKFLOW_HARDENING_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase58():
    deal_fields = [
        {
            "fieldname": "permission_workflow_hardening_section",
            "label": "NDIS Permission Workflow Hardening",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_permission_workflow_hardening_required",
            "label": "Permission Workflow Hardening Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
        },
        {
            "fieldname": "ndis_permission_workflow_hardening_run",
            "label": "NDIS CRM Permission Workflow Hardening Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "permission_workflow_hardening_status",
            "label": "Permission Workflow Hardening Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "permission_workflow_hardening_ready",
            "label": "Permission Workflow Hardening Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    shared_fields = [
        {
            "fieldname": "permission_workflow_hardening_section",
            "label": "NDIS Permission Workflow Hardening",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_permission_workflow_hardening_run",
            "label": "NDIS CRM Permission Workflow Hardening Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "permission_workflow_hardening_status",
            "label": "Permission Workflow Hardening Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "permission_workflow_hardening_ready",
            "label": "Permission Workflow Hardening Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    custom_fields = {
        CRM_DEAL: deal_fields,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN: shared_fields,
    }

    safe_create_custom_fields(custom_fields)
    print("Created / updated Phase 58 permission workflow hardening custom fields.")


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


def _append_before_last(text, needle, addition):
    index = text.rfind(needle)
    if index == -1:
        return text + addition
    return text[:index] + addition + text[index:]


def _phase58_deal_actions():
    return r'''
// NDIS CRM Phase 58 Deal Actions
{
  label: "Create Permission Workflow Hardening Run",
  onClick: () => {
    call("ndis_crm.phase58_permission_workflow_hardening.create_permission_workflow_hardening_run_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Permission Workflow Hardening Run Created" : "Existing Permission Workflow Hardening Run Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-permission-workflow-hardening-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Permission Workflow Hardening Run",
  onClick: () => {
    if (doc.ndis_permission_workflow_hardening_run) {
      window.open(`/app/ndis-crm-permission-workflow-hardening-run/${doc.ndis_permission_workflow_hardening_run}`, "_blank")
    } else {
      createToast({ title: "No Permission Workflow Hardening Run linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    phase58_actions = _phase58_deal_actions()
    try:
        from ndis_crm.setup.phase57_operational_dashboard_snapshot import _deal_script as phase57_deal_script
        base = phase57_deal_script()
    except Exception:
        base = ""

    if "NDIS CRM Phase 58 Deal Actions" in base:
        return base

    addition = f",\n    {phase58_actions}"
    if "actions: [" in base:
        return _append_before_last(base, "]", addition)

    fallback = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
      __PHASE58_ACTIONS__
    ]
  }
}
'''.strip()
    return fallback.replace("__PHASE58_ACTIONS__", phase58_actions)


def create_or_extend_crm_deal_script():
    existing_script = ""
    if frappe.db.exists("CRM Form Script", "NDIS CRM Deal Actions"):
        existing_script = frappe.db.get_value("CRM Form Script", "NDIS CRM Deal Actions", "script") or ""

    if "NDIS CRM Phase 58 Deal Actions" in existing_script:
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
frappe.ui.form.on("NDIS CRM Operational Dashboard Snapshot Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Permission Workflow Hardening Run"), function () {
            frappe.call({
                method: "ndis_crm.phase58_permission_workflow_hardening.create_permission_workflow_hardening_run_from_dashboard",
                args: { operational_dashboard_snapshot_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating permission workflow hardening run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Permission Workflow Hardening Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Permission Workflow Hardening Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_permission_workflow_hardening_run) {
            frm.add_custom_button(__("Open Permission Workflow Hardening Run"), function () {
                frappe.set_route("Form", "NDIS CRM Permission Workflow Hardening Run", frm.doc.ndis_permission_workflow_hardening_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Permission Workflow Hardening Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Refresh Hardening Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase58_permission_workflow_hardening.refresh_permission_workflow_hardening_lines",
                args: { permission_workflow_hardening_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Refreshing hardening lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Hardening lines refreshed"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Hardening Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase58_permission_workflow_hardening.validate_permission_workflow_hardening_readiness",
                args: { permission_workflow_hardening_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating hardening readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Hardening readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Hardening"), function () {
            frappe.call({
                method: "ndis_crm.phase58_permission_workflow_hardening.mark_ready_for_permission_workflow_hardening",
                args: { permission_workflow_hardening_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for hardening approval...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for hardening approval"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Hardening Run"), function () {
            frappe.call({
                method: "ndis_crm.phase58_permission_workflow_hardening.approve_permission_workflow_hardening_run",
                args: { permission_workflow_hardening_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving hardening run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Hardening Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Complete Hardening"), function () {
            frappe.confirm(
                __("This completes the controlled hardening readiness record. It will not mutate roles, permissions, workflows, business records, communication, task, finance, claim, remittance, payment, journal, or accounting records."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase58_permission_workflow_hardening.complete_permission_workflow_hardening",
                        args: { permission_workflow_hardening_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Completing permission workflow hardening...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Hardening completed"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.operational_dashboard_snapshot_run) {
            frm.add_custom_button(__("Open Operational Dashboard Snapshot"), function () {
                frappe.set_route("Form", "NDIS CRM Operational Dashboard Snapshot Run", frm.doc.operational_dashboard_snapshot_run);
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
            "NDIS CRM Operational Dashboard Phase58 Actions",
            {
                "dt": OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
                "view": "Form",
                "enabled": 1,
                "script": source_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Permission Workflow Hardening Run Actions",
            {
                "dt": PERMISSION_WORKFLOW_HARDENING_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
