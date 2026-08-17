import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"

UAT_REGRESSION_EVIDENCE_PACK_RUN = "NDIS CRM UAT Regression Evidence Pack Run"
PERMISSION_WORKFLOW_HARDENING_RUN = "NDIS CRM Permission Workflow Hardening Run"
OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"
CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"

PRODUCTION_READINESS_FREEZE_RUN = "NDIS CRM Production Readiness Freeze Run"
PRODUCTION_READINESS_FREEZE_LINE = "NDIS CRM Production Readiness Freeze Line"


def install():
    ensure_required_doctypes()
    create_production_readiness_freeze_doctypes()
    create_custom_fields_phase60()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 60 Production Readiness Freeze installed successfully.")


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
        UAT_REGRESSION_EVIDENCE_PACK_RUN,
        PERMISSION_WORKFLOW_HARDENING_RUN,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 60 DocTypes: " + ", ".join(missing))

    print("Required Phase 60 DocTypes found.")


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


def create_production_readiness_freeze_doctypes():
    create_production_readiness_freeze_line()
    create_production_readiness_freeze_run()


def create_production_readiness_freeze_line():
    fields = [
        make_field("Freeze Area", "freeze_area", "Data", in_list_view=1),
        make_field("Freeze Item", "freeze_item", "Data", in_list_view=1),
        make_field("Expected Condition", "expected_condition", "Small Text"),

        make_field("Observed Evidence", "observed_section", "Section Break"),
        make_field("Observed Status", "observed_status", "Select", options="Pass\nManual Review\nNeeds Attention", in_list_view=1),
        make_field("Observed Result", "observed_result", "Small Text"),
        make_field("Risk Level", "risk_level", "Select", options="High\nMedium\nLow", default="Medium", in_list_view=1),
        make_field("Evidence Reference", "evidence_reference", "Small Text"),
        make_field("Review Owner", "review_owner", "Link", options="User"),
        make_field("Reviewed On", "reviewed_on", "Datetime"),

        make_field("Blocker Controls", "blocker_section", "Section Break"),
        make_field("Freeze Review Complete", "freeze_review_complete", "Check", default="0"),
        make_field("Condition Verified", "condition_verified", "Check", default="0"),
        make_field("Blocker Found", "blocker_found", "Check", default="0"),
        make_field("Blocker Summary", "blocker_summary", "Small Text"),
        make_field("Blocker Resolved", "blocker_resolved", "Check", default="0"),
        make_field("Line Ready for Freeze", "line_ready_for_freeze", "Check", default="0", in_list_view=1),
        make_field("Freeze Line Status", "freeze_line_status", "Select", options="Draft\nReady\nApproved\nFreeze Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=PRODUCTION_READINESS_FREEZE_LINE,
        fields=fields,
        istable=1,
    )


def create_production_readiness_freeze_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-PROD-READINESS-FREEZE-.YYYY.-.#####", default="NDIS-PROD-READINESS-FREEZE-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Production Freeze Approval\nProduction Freeze Approved\nProduction Readiness Frozen\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Freeze Mode", "freeze_mode", "Select", options="Readiness Freeze Only", default="Readiness Freeze Only"),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Freeze Completion %", "freeze_completion_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Production Readiness Freeze Run Ready", "production_readiness_freeze_run_ready", "Check", read_only=1, in_list_view=1),

        make_field("Review Controls", "review_controls_section", "Section Break"),
        make_field("Final Production Readiness Review Complete", "final_production_readiness_review_complete", "Check", default="0"),
        make_field("Boundary Freeze Review Complete", "boundary_freeze_review_complete", "Check", default="0"),
        make_field("Regression Freeze Review Complete", "regression_freeze_review_complete", "Check", default="0"),
        make_field("Fixture Freeze Review Complete", "fixture_freeze_review_complete", "Check", default="0"),
        make_field("Repository Freeze Review Complete", "repository_freeze_review_complete", "Check", default="0"),
        make_field("Production Readiness Sign Off Confirmed", "production_readiness_sign_off_confirmed", "Check", default="0"),
        make_field("Production Freeze Completion Allowed", "production_freeze_completion_allowed", "Check", default="0"),

        make_field("Blocked Controls", "blocked_controls_section", "Section Break"),
        make_field("Production Activation Allowed", "production_activation_allowed", "Check", default="0", description="Blocked in Phase 60. This phase freezes readiness only."),
        make_field("Business Record Creation Allowed", "business_record_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Care Management Mutation Allowed", "care_management_mutation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Communication Creation Allowed", "communication_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Email Send Allowed", "email_send_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("ToDo Creation Allowed", "todo_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Task Creation Allowed", "task_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Finance Document Creation Allowed", "finance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Claim Document Creation Allowed", "claim_document_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Remittance Document Creation Allowed", "remittance_document_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),
        make_field("Accounting Document Creation Allowed", "accounting_document_creation_allowed", "Check", default="0", description="Blocked in Phase 60."),

        make_field("Source Links", "source_links_section", "Section Break"),
        make_field("CRM Lead", "crm_lead", "Data"),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
        make_field("Participant Service File", "participant_service_file", "Data"),
        make_field("Care Management Integration Run", "care_management_integration_run", "Data"),
        make_field("Operational Dashboard Snapshot Run", "operational_dashboard_snapshot_run", "Link", options=OPERATIONAL_DASHBOARD_SNAPSHOT_RUN),
        make_field("Permission Workflow Hardening Run", "permission_workflow_hardening_run", "Link", options=PERMISSION_WORKFLOW_HARDENING_RUN),
        make_field("UAT Regression Evidence Pack Run", "uat_regression_evidence_pack_run", "Link", options=UAT_REGRESSION_EVIDENCE_PACK_RUN, reqd=1, in_list_view=1),

        make_field("Participant Details", "participant_details_section", "Section Break"),
        make_field("Participant Name", "participant_name", "Data", in_list_view=1),
        make_field("NDIS Number", "ndis_number", "Data"),
        make_field("Plan Start Date", "plan_start_date", "Date"),
        make_field("Plan End Date", "plan_end_date", "Date"),
        make_field("Company", "company", "Link", options="Company"),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Freeze Line Count", "freeze_line_count", "Int", read_only=1),
        make_field("Passed Condition Count", "passed_condition_count", "Int", read_only=1),
        make_field("Manual Review Count", "manual_review_count", "Int", read_only=1),
        make_field("Attention Condition Count", "attention_condition_count", "Int", read_only=1),
        make_field("Ready Freeze Line Count", "ready_freeze_line_count", "Int", read_only=1),
        make_field("Completed Freeze Line Count", "completed_freeze_line_count", "Int", read_only=1),
        make_field("Blocker Found Count", "blocker_found_count", "Int", read_only=1),
        make_field("Blocker Resolved Count", "blocker_resolved_count", "Int", read_only=1),
        make_field("High Risk Count", "high_risk_count", "Int", read_only=1),
        make_field("Medium Risk Count", "medium_risk_count", "Int", read_only=1),
        make_field("Low Risk Count", "low_risk_count", "Int", read_only=1),

        make_field("Owners", "owners_section", "Section Break"),
        make_field("Freeze Owner", "freeze_owner", "Link", options="User", in_list_view=1),
        make_field("Completed By", "completed_by", "Link", options="User", read_only=1),
        make_field("Completed On", "completed_on", "Datetime", read_only=1),

        make_field("Freeze Lines", "freeze_lines_section", "Section Break"),
        make_field("Production Readiness Freeze Lines", "production_readiness_freeze_lines", "Table", options=PRODUCTION_READINESS_FREEZE_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Production Readiness Freeze Notes", "production_readiness_freeze_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=PRODUCTION_READINESS_FREEZE_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase60():
    deal_fields = [
        {
            "fieldname": "production_readiness_freeze_section",
            "label": "NDIS Production Readiness Freeze",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_production_readiness_freeze_required",
            "label": "Production Readiness Freeze Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
        },
        {
            "fieldname": "ndis_production_readiness_freeze_run",
            "label": "NDIS CRM Production Readiness Freeze Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "production_readiness_freeze_status",
            "label": "Production Readiness Freeze Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "production_readiness_freeze_ready",
            "label": "Production Readiness Freeze Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    shared_fields = [
        {
            "fieldname": "production_readiness_freeze_section",
            "label": "NDIS Production Readiness Freeze",
            "fieldtype": "Section Break",
        },
        {
            "fieldname": "ndis_production_readiness_freeze_run",
            "label": "NDIS CRM Production Readiness Freeze Run",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "production_readiness_freeze_status",
            "label": "Production Readiness Freeze Status",
            "fieldtype": "Small Text",
            "read_only": 1,
        },
        {
            "fieldname": "production_readiness_freeze_ready",
            "label": "Production Readiness Freeze Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "default": "0",
        },
    ]

    custom_fields = {
        CRM_DEAL: deal_fields,
        UAT_REGRESSION_EVIDENCE_PACK_RUN: shared_fields,
        PERMISSION_WORKFLOW_HARDENING_RUN: shared_fields,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN: shared_fields,
    }

    if doctype_exists(CARE_MANAGEMENT_INTEGRATION_RUN):
        custom_fields[CARE_MANAGEMENT_INTEGRATION_RUN] = shared_fields

    safe_create_custom_fields(custom_fields)
    print("Created / updated Phase 60 production readiness freeze custom fields.")


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


def _phase60_deal_actions():
    return r'''
// NDIS CRM Phase 60 Deal Actions
{
  label: "Create Production Readiness Freeze",
  onClick: () => {
    call("ndis_crm.phase60_production_readiness_freeze.create_production_readiness_freeze_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Production Readiness Freeze Created" : "Existing Production Readiness Freeze Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-production-readiness-freeze-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Production Readiness Freeze",
  onClick: () => {
    if (doc.ndis_production_readiness_freeze_run) {
      window.open(`/app/ndis-crm-production-readiness-freeze-run/${doc.ndis_production_readiness_freeze_run}`, "_blank")
    } else {
      createToast({ title: "No Production Readiness Freeze linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    phase60_actions = _phase60_deal_actions()
    try:
        from ndis_crm.setup.phase59_uat_regression_evidence_pack import _deal_script as phase59_deal_script
        base = phase59_deal_script()
    except Exception:
        base = ""

    if "NDIS CRM Phase 60 Deal Actions" in base:
        return base

    addition = f",\n    {phase60_actions}"
    if "actions: [" in base:
        return _append_before_last(base, "]", addition)

    fallback = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
      __PHASE60_ACTIONS__
    ]
  }
}
'''.strip()
    return fallback.replace("__PHASE60_ACTIONS__", phase60_actions)


def create_or_extend_crm_deal_script():
    existing_script = ""
    if frappe.db.exists("CRM Form Script", "NDIS CRM Deal Actions"):
        existing_script = frappe.db.get_value("CRM Form Script", "NDIS CRM Deal Actions", "script") or ""

    if "NDIS CRM Phase 60 Deal Actions" in existing_script:
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
frappe.ui.form.on("NDIS CRM UAT Regression Evidence Pack Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Production Readiness Freeze"), function () {
            frappe.call({
                method: "ndis_crm.phase60_production_readiness_freeze.create_production_readiness_freeze_from_uat",
                args: { uat_regression_evidence_pack_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating production readiness freeze...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Production Readiness Freeze created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Production Readiness Freeze Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_production_readiness_freeze_run) {
            frm.add_custom_button(__("Open Production Readiness Freeze"), function () {
                frappe.set_route("Form", "NDIS CRM Production Readiness Freeze Run", frm.doc.ndis_production_readiness_freeze_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Production Readiness Freeze Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Refresh Freeze Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase60_production_readiness_freeze.refresh_production_readiness_freeze_lines",
                args: { production_readiness_freeze_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Refreshing production readiness freeze lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Freeze lines refreshed"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Production Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase60_production_readiness_freeze.validate_production_readiness_freeze",
                args: { production_readiness_freeze_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating production readiness freeze...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Production readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Freeze Approval"), function () {
            frappe.call({
                method: "ndis_crm.phase60_production_readiness_freeze.mark_ready_for_production_freeze",
                args: { production_readiness_freeze_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for production freeze approval...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for production freeze approval"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Production Freeze"), function () {
            frappe.call({
                method: "ndis_crm.phase60_production_readiness_freeze.approve_production_readiness_freeze",
                args: { production_readiness_freeze_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving production readiness freeze...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Production freeze approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Complete Production Readiness Freeze"), function () {
            frappe.confirm(
                __("This freezes V1 readiness only. It will not enable production mode or create/update business, Care Management, communication, task, finance, claim, remittance, payment, journal, accounting, adjustment, or bank reconciliation records."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase60_production_readiness_freeze.complete_production_readiness_freeze",
                        args: { production_readiness_freeze_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Completing production readiness freeze...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Production readiness frozen"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.uat_regression_evidence_pack_run) {
            frm.add_custom_button(__("Open UAT Evidence Pack"), function () {
                frappe.set_route("Form", "NDIS CRM UAT Regression Evidence Pack Run", frm.doc.uat_regression_evidence_pack_run);
            }, __("Open"));
        }

        if (frm.doc.permission_workflow_hardening_run) {
            frm.add_custom_button(__("Open Permission Workflow Hardening"), function () {
                frappe.set_route("Form", "NDIS CRM Permission Workflow Hardening Run", frm.doc.permission_workflow_hardening_run);
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
            "NDIS CRM UAT Regression Evidence Phase60 Actions",
            {
                "dt": UAT_REGRESSION_EVIDENCE_PACK_RUN,
                "view": "Form",
                "enabled": 1,
                "script": source_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Production Readiness Freeze Run Actions",
            {
                "dt": PRODUCTION_READINESS_FREEZE_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
