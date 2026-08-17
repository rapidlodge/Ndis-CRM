import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
PERMISSION_WORKFLOW_HARDENING_RUN = "NDIS CRM Permission Workflow Hardening Run"
OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"
CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"

UAT_REGRESSION_EVIDENCE_PACK_RUN = "NDIS CRM UAT Regression Evidence Pack Run"
UAT_REGRESSION_EVIDENCE_PACK_LINE = "NDIS CRM UAT Regression Evidence Pack Line"


def install():
    ensure_required_doctypes()
    create_uat_regression_evidence_pack_doctypes()
    create_custom_fields_phase59()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 59 UAT Regression Evidence Pack installed successfully.")


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
        PERMISSION_WORKFLOW_HARDENING_RUN,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 59 DocTypes: " + ", ".join(missing))

    print("Required Phase 59 DocTypes found.")


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


def create_uat_regression_evidence_pack_doctypes():
    create_uat_regression_evidence_pack_line()
    create_uat_regression_evidence_pack_run()


def create_uat_regression_evidence_pack_line():
    fields = [
        make_field("UAT Area", "uat_area", "Data", in_list_view=1),
        make_field("UAT Scenario", "uat_scenario", "Data", in_list_view=1),
        make_field("Expected Result", "expected_result", "Small Text"),

        make_field("Observed Evidence", "observed_section", "Section Break"),
        make_field("Observed Status", "observed_status", "Select", options="Pass\nManual Review\nNeeds Attention", in_list_view=1),
        make_field("Observed Result", "observed_result", "Small Text"),
        make_field("Risk Level", "risk_level", "Select", options="High\nMedium\nLow", default="Medium", in_list_view=1),
        make_field("Evidence Reference", "evidence_reference", "Small Text"),
        make_field("Tester", "tester", "Link", options="User"),
        make_field("Tested On", "tested_on", "Datetime"),

        make_field("Issue Controls", "issue_section", "Section Break"),
        make_field("UAT Review Complete", "uat_review_complete", "Check", default="0"),
        make_field("UAT Evidence Recorded", "uat_evidence_recorded", "Check", default="0"),
        make_field("Issue Found", "issue_found", "Check", default="0"),
        make_field("Issue Summary", "issue_summary", "Small Text"),
        make_field("Issue Resolved", "issue_resolved", "Check", default="0"),
        make_field("Line Ready for UAT Sign Off", "line_ready_for_uat_sign_off", "Check", default="0", in_list_view=1),
        make_field("UAT Line Status", "uat_line_status", "Select", options="Draft\nReady\nApproved\nUAT Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=UAT_REGRESSION_EVIDENCE_PACK_LINE,
        fields=fields,
        istable=1,
    )


def create_uat_regression_evidence_pack_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-UAT-REGRESSION-.YYYY.-.#####", default="NDIS-UAT-REGRESSION-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for UAT Sign Off\nUAT Evidence Approved\nUAT Evidence Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("UAT Mode", "uat_mode", "Select", options="Controlled Evidence Pack Only", default="Controlled Evidence Pack Only"),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("UAT Completion %", "uat_completion_percent", "Percent", read_only=1, in_list_view=1),
        make_field("UAT Regression Evidence Pack Run Ready", "uat_regression_evidence_pack_run_ready", "Check", read_only=1, in_list_view=1),

        make_field("Review Controls", "review_controls_section", "Section Break"),
        make_field("Final UAT Review Complete", "final_uat_review_complete", "Check", default="0"),
        make_field("Boundary Evidence Review Complete", "boundary_evidence_review_complete", "Check", default="0"),
        make_field("Regression Evidence Review Complete", "regression_evidence_review_complete", "Check", default="0"),
        make_field("Fixture Evidence Review Complete", "fixture_evidence_review_complete", "Check", default="0"),
        make_field("Repository Evidence Review Complete", "repository_evidence_review_complete", "Check", default="0"),
        make_field("UAT Completion Allowed", "uat_completion_allowed", "Check", default="0"),

        make_field("Blocked Controls", "blocked_controls_section", "Section Break"),
        make_field("Business Record Creation Allowed", "business_record_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Care Management Mutation Allowed", "care_management_mutation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Communication Creation Allowed", "communication_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Email Send Allowed", "email_send_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("ToDo Creation Allowed", "todo_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Task Creation Allowed", "task_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Finance Document Creation Allowed", "finance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Claim Document Creation Allowed", "claim_document_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Remittance Document Creation Allowed", "remittance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),
        make_field("Accounting Document Creation Allowed", "accounting_document_creation_allowed", "Check", default="0", description="Blocked in Phase 59."),

        make_field("Source Links", "source_links_section", "Section Break"),
        make_field("CRM Lead", "crm_lead", "Data"),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
        make_field("Participant Service File", "participant_service_file", "Data"),
        make_field("Care Management Integration Run", "care_management_integration_run", "Data"),
        make_field("Operational Dashboard Snapshot Run", "operational_dashboard_snapshot_run", "Link", options=OPERATIONAL_DASHBOARD_SNAPSHOT_RUN),
        make_field("Permission Workflow Hardening Run", "permission_workflow_hardening_run", "Link", options=PERMISSION_WORKFLOW_HARDENING_RUN, reqd=1, in_list_view=1),

        make_field("Participant Details", "participant_details_section", "Section Break"),
        make_field("Participant Name", "participant_name", "Data", in_list_view=1),
        make_field("NDIS Number", "ndis_number", "Data"),
        make_field("Plan Start Date", "plan_start_date", "Date"),
        make_field("Plan End Date", "plan_end_date", "Date"),
        make_field("Company", "company", "Link", options="Company"),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("UAT Line Count", "uat_line_count", "Int", read_only=1),
        make_field("Passed UAT Count", "passed_uat_count", "Int", read_only=1),
        make_field("Manual Review Count", "manual_review_count", "Int", read_only=1),
        make_field("Attention UAT Count", "attention_uat_count", "Int", read_only=1),
        make_field("Ready UAT Line Count", "ready_uat_line_count", "Int", read_only=1),
        make_field("Completed UAT Line Count", "completed_uat_line_count", "Int", read_only=1),
        make_field("Issue Found Count", "issue_found_count", "Int", read_only=1),
        make_field("Issue Resolved Count", "issue_resolved_count", "Int", read_only=1),
        make_field("High Risk Count", "high_risk_count", "Int", read_only=1),
        make_field("Medium Risk Count", "medium_risk_count", "Int", read_only=1),
        make_field("Low Risk Count", "low_risk_count", "Int", read_only=1),

        make_field("Owners", "owners_section", "Section Break"),
        make_field("UAT Owner", "uat_owner", "Link", options="User", in_list_view=1),
        make_field("Completed By", "completed_by", "Link", options="User", read_only=1),
        make_field("Completed On", "completed_on", "Datetime", read_only=1),

        make_field("UAT Evidence Lines", "uat_lines_section", "Section Break"),
        make_field("UAT Regression Evidence Lines", "uat_regression_evidence_lines", "Table", options=UAT_REGRESSION_EVIDENCE_PACK_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("UAT Notes", "uat_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=UAT_REGRESSION_EVIDENCE_PACK_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase59():
    deal_fields = [
        {
            "fieldname": "uat_regression_evidence_pack_section",
            "label": "NDIS UAT Regression Evidence Pack",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_uat_regression_evidence_pack_required",
            "label": "UAT Regression Evidence Pack Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
        },
        {
            "fieldname": "ndis_uat_regression_evidence_pack_run",
            "label": "NDIS CRM UAT Regression Evidence Pack Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "uat_regression_evidence_pack_status",
            "label": "UAT Regression Evidence Pack Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "uat_regression_evidence_pack_ready",
            "label": "UAT Regression Evidence Pack Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    shared_fields = [
        {
            "fieldname": "uat_regression_evidence_pack_section",
            "label": "NDIS UAT Regression Evidence Pack",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_uat_regression_evidence_pack_run",
            "label": "NDIS CRM UAT Regression Evidence Pack Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "uat_regression_evidence_pack_status",
            "label": "UAT Regression Evidence Pack Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "uat_regression_evidence_pack_ready",
            "label": "UAT Regression Evidence Pack Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    custom_fields = {
        CRM_DEAL: deal_fields,
        PERMISSION_WORKFLOW_HARDENING_RUN: shared_fields,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN: shared_fields,
    }

    if doctype_exists(CARE_MANAGEMENT_INTEGRATION_RUN):
        custom_fields[CARE_MANAGEMENT_INTEGRATION_RUN] = shared_fields

    safe_create_custom_fields(custom_fields)
    print("Created / updated Phase 59 UAT regression evidence custom fields.")


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


def _phase59_deal_actions():
    return r'''
// NDIS CRM Phase 59 Deal Actions
{
  label: "Create UAT Regression Evidence Pack",
  onClick: () => {
    call("ndis_crm.phase59_uat_regression_evidence_pack.create_uat_regression_evidence_pack_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "UAT Regression Evidence Pack Created" : "Existing UAT Regression Evidence Pack Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-uat-regression-evidence-pack-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open UAT Regression Evidence Pack",
  onClick: () => {
    if (doc.ndis_uat_regression_evidence_pack_run) {
      window.open(`/app/ndis-crm-uat-regression-evidence-pack-run/${doc.ndis_uat_regression_evidence_pack_run}`, "_blank")
    } else {
      createToast({ title: "No UAT Regression Evidence Pack linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    phase59_actions = _phase59_deal_actions()
    try:
        from ndis_crm.setup.phase58_permission_workflow_hardening import _deal_script as phase58_deal_script
        base = phase58_deal_script()
    except Exception:
        base = ""

    if "NDIS CRM Phase 59 Deal Actions" in base:
        return base

    addition = f",\n    {phase59_actions}"
    if "actions: [" in base:
        return _append_before_last(base, "]", addition)

    fallback = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
      __PHASE59_ACTIONS__
    ]
  }
}
'''.strip()
    return fallback.replace("__PHASE59_ACTIONS__", phase59_actions)


def create_or_extend_crm_deal_script():
    existing_script = ""
    if frappe.db.exists("CRM Form Script", "NDIS CRM Deal Actions"):
        existing_script = frappe.db.get_value("CRM Form Script", "NDIS CRM Deal Actions", "script") or ""

    if "NDIS CRM Phase 59 Deal Actions" in existing_script:
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
frappe.ui.form.on("NDIS CRM Permission Workflow Hardening Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create UAT Regression Evidence Pack"), function () {
            frappe.call({
                method: "ndis_crm.phase59_uat_regression_evidence_pack.create_uat_regression_evidence_pack_from_hardening",
                args: { permission_workflow_hardening_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating UAT regression evidence pack...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("UAT Regression Evidence Pack created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM UAT Regression Evidence Pack Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_uat_regression_evidence_pack_run) {
            frm.add_custom_button(__("Open UAT Regression Evidence Pack"), function () {
                frappe.set_route("Form", "NDIS CRM UAT Regression Evidence Pack Run", frm.doc.ndis_uat_regression_evidence_pack_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM UAT Regression Evidence Pack Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Refresh UAT Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase59_uat_regression_evidence_pack.refresh_uat_regression_evidence_lines",
                args: { uat_regression_evidence_pack_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Refreshing UAT regression evidence lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("UAT lines refreshed"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate UAT Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase59_uat_regression_evidence_pack.validate_uat_regression_evidence_readiness",
                args: { uat_regression_evidence_pack_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating UAT readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("UAT readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for UAT Sign Off"), function () {
            frappe.call({
                method: "ndis_crm.phase59_uat_regression_evidence_pack.mark_ready_for_uat_sign_off",
                args: { uat_regression_evidence_pack_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for UAT sign off...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for UAT sign off"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve UAT Evidence"), function () {
            frappe.call({
                method: "ndis_crm.phase59_uat_regression_evidence_pack.approve_uat_regression_evidence_pack",
                args: { uat_regression_evidence_pack_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving UAT evidence pack...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("UAT evidence approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Complete UAT Evidence Pack"), function () {
            frappe.confirm(
                __("This completes the controlled UAT evidence pack. It will not create or update business, Care Management, communication, task, finance, claim, remittance, payment, journal, accounting, adjustment, or bank reconciliation records."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase59_uat_regression_evidence_pack.complete_uat_regression_evidence_pack",
                        args: { uat_regression_evidence_pack_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Completing UAT evidence pack...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("UAT evidence pack completed"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.permission_workflow_hardening_run) {
            frm.add_custom_button(__("Open Permission Workflow Hardening"), function () {
                frappe.set_route("Form", "NDIS CRM Permission Workflow Hardening Run", frm.doc.permission_workflow_hardening_run);
            }, __("Open"));
        }

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
            "NDIS CRM Permission Workflow Hardening Phase59 Actions",
            {
                "dt": PERMISSION_WORKFLOW_HARDENING_RUN,
                "view": "Form",
                "enabled": 1,
                "script": source_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM UAT Regression Evidence Pack Run Actions",
            {
                "dt": UAT_REGRESSION_EVIDENCE_PACK_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
