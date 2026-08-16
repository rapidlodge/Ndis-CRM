import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"

POST_CLOSURE_ROUTING_PREPARATION_RUN = "NDIS CRM Post Closure Routing Preparation Run"
POST_CLOSURE_ROUTING_PREPARATION_LINE = "NDIS CRM Post Closure Routing Preparation Line"

POST_CLOSURE_ROUTING_FINALISATION_RUN = "NDIS CRM Post Closure Routing Finalisation Run"
POST_CLOSURE_ROUTING_FINALISATION_LINE = "NDIS CRM Post Closure Routing Finalisation Line"

RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN = "NDIS CRM Recovery Outcome Closure Finalisation Run"
RECOVERY_OUTCOME_CLOSURE_DRAFT_RUN = "NDIS CRM Recovery Outcome Closure Draft Run"
RECOVERY_OUTCOME_CLOSURE_PREPARATION_RUN = "NDIS CRM Recovery Outcome Closure Preparation Run"
RECOVERY_OUTCOME_ACTION_COMPLETION_RUN = "NDIS CRM Recovery Outcome Action Completion Run"


def install():
    ensure_required_doctypes()
    create_post_closure_routing_finalisation_doctypes()
    create_custom_fields_phase55()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 55 Post Closure Routing Finalisation gate installed successfully.")


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
        POST_CLOSURE_ROUTING_PREPARATION_RUN,
        POST_CLOSURE_ROUTING_PREPARATION_LINE,
        RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN,
        "Sales Invoice",
        "Payment Entry",
        "Journal Entry",
        "GL Entry",
        "NDIS Remittance Import",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 55 DocTypes: " + ", ".join(missing))

    print("Required Phase 55 DocTypes found.")


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


def create_post_closure_routing_finalisation_doctypes():
    create_post_closure_routing_finalisation_line()
    create_post_closure_routing_finalisation_run()


def create_post_closure_routing_finalisation_line():
    fields = [
        make_field("Source", "source_section", "Section Break"),
        make_field("Post Closure Routing Finalisation Source Key", "post_closure_routing_finalisation_source_key", "Data", read_only=1),

        make_field("Source Routing", "source_routing_section", "Section Break"),
        make_field("Source Routing DocType", "source_routing_doctype", "Data", read_only=1),
        make_field("Source Routing Name", "source_routing_name", "Data", read_only=1),
        make_field("Source Routing Status", "source_routing_status", "Data", read_only=1),
        make_field("Target Final Routing DocType", "target_final_routing_doctype", "Data", read_only=1),
        make_field("Target Final Routing Name", "target_final_routing_name", "Data", read_only=1),
        make_field("Target Final Routing Status", "target_final_routing_status", "Data", read_only=1),

        make_field("Existing Recovery Case Snapshot", "case_snapshot_section", "Section Break"),
        make_field("Target Case DocType", "target_case_doctype", "Data", read_only=1),
        make_field("Target Case Name", "target_case_name", "Data", read_only=1),
        make_field("Target Case Docstatus", "target_case_docstatus", "Int", read_only=1),
        make_field("Target Case Status", "target_case_status", "Data", read_only=1),

        make_field("Financial References", "financial_refs_section", "Section Break"),
        make_field("Service Line", "service_line", "Data", in_list_view=1),
        make_field("Service Code", "service_code", "Data"),
        make_field("Service Date", "service_date", "Date"),
        make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice"),
        make_field("Payment Entry", "payment_entry", "Link", options="Payment Entry"),
        make_field("Journal Entry", "journal_entry", "Link", options="Journal Entry"),
        make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import"),
        make_field("NDIS Claim Batch", "ndis_claim_batch", "Link", options="NDIS Claim Batch"),
        make_field("NDIS Claim Line", "ndis_claim_line", "Link", options="NDIS Claim Line"),

        make_field("Recovery Values", "recovery_values_section", "Section Break"),
        make_field("Proposed Recovery Amount", "proposed_recovery_amount", "Currency", in_list_view=1),
        make_field("Recovery Type", "recovery_type", "Data", in_list_view=1),
        make_field("Recovery Route", "recovery_route", "Data"),
        make_field("Recovery Reason", "recovery_reason", "Small Text"),
        make_field("Recovery Party Type", "recovery_party_type", "Data", default="Customer"),
        make_field("Recovery Party", "recovery_party", "Link", options="Customer"),
        make_field("Recovery Contact Name", "recovery_contact_name", "Data"),
        make_field("Recovery Contact Email", "recovery_contact_email", "Data"),
        make_field("Recovery Due Date", "recovery_due_date", "Date"),

        make_field("Recipient Snapshot", "recipient_snapshot_section", "Section Break"),
        make_field("Recipient Name", "recipient_name", "Data"),
        make_field("Recipient Email", "recipient_email", "Data"),
        make_field("Recipient Phone", "recipient_phone", "Data"),

        make_field("Outcome Snapshot", "outcome_snapshot_section", "Section Break"),
        make_field("Outcome Status Snapshot", "outcome_status_snapshot", "Data", read_only=1),
        make_field("Outcome Summary", "outcome_summary", "Small Text"),
        make_field("Response Reference", "response_reference", "Data"),
        make_field("Promised Payment Date", "promised_payment_date", "Date"),
        make_field("Promised Payment Amount", "promised_payment_amount", "Currency"),
        make_field("Evidence Requested", "evidence_requested", "Check", default="0"),
        make_field("Dispute Reason", "dispute_reason", "Small Text"),
        make_field("Correct Contact Name", "correct_contact_name", "Data"),
        make_field("Correct Contact Email", "correct_contact_email", "Data"),
        make_field("Correct Contact Phone", "correct_contact_phone", "Data"),

        make_field("Closure Snapshot", "closure_snapshot_section", "Section Break"),
        make_field("Closure Decision", "closure_decision", "Data"),
        make_field("Closure Route", "closure_route", "Data"),
        make_field("Closure Priority", "closure_priority", "Data"),
        make_field("Closure Owner", "closure_owner", "Link", options="User"),
        make_field("Closure Due Date", "closure_due_date", "Date"),
        make_field("Final Closure Outcome", "final_closure_outcome", "Data"),
        make_field("Final Closure Summary", "final_closure_summary", "Small Text"),

        make_field("Post Closure Routing Snapshot", "post_closure_routing_section", "Section Break"),
        make_field("Post Closure Routing Finalisation Source Ready", "post_closure_routing_finalisation_source_ready", "Check", default="0"),
        make_field("Post Closure Route", "post_closure_route", "Data", in_list_view=1),
        make_field("Post Closure Route Priority", "post_closure_route_priority", "Data"),
        make_field("Post Closure Route Owner", "post_closure_route_owner", "Link", options="User", in_list_view=1),
        make_field("Post Closure Route Due Date", "post_closure_route_due_date", "Date"),
        make_field("Post Closure Route Instruction", "post_closure_route_instruction", "Small Text"),
        make_field("Post Closure Route Decision Summary", "post_closure_route_decision_summary", "Small Text"),

        make_field("Routing Finalisation", "routing_finalisation_section", "Section Break"),
        make_field("Final Routing Result", "final_routing_result", "Select", options="Recovery Cycle Closed in CRM\nRepeat Follow-Up Route Finalised\nPayment Promise Monitoring Route Finalised\nEvidence Follow-Up Route Finalised\nDispute Review Route Finalised\nContact Correction Route Finalised\nEscalation Route Finalised\nManual Review Route Finalised", in_list_view=1),
        make_field("Final Routing Summary", "final_routing_summary", "Small Text"),
        make_field("Routing Finalisation Review Complete", "routing_finalisation_review_complete", "Check", default="0"),
        make_field("Routing Finalisation Authorized", "routing_finalisation_authorized", "Check", default="0"),
        make_field("Routing Finalisation Recorded", "routing_finalisation_recorded", "Check", default="0"),

        make_field("Blocked Downstream Controls", "blocked_downstream_section", "Section Break"),
        make_field("Actual Recovery Case Closure Authorized", "actual_recovery_case_closure_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Communication Creation Authorized", "communication_creation_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Email Send Authorized", "email_send_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Event Creation Authorized", "event_creation_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("ToDo Creation Authorized", "todo_creation_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Task Creation Authorized", "task_creation_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Recovery Case Creation Authorized", "recovery_case_creation_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Journal Entry Authorized", "journal_entry_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Manual GL Authorized", "manual_gl_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Payment Entry Authorized", "payment_entry_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Sales Invoice Authorized", "sales_invoice_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Adjustment Authorized", "adjustment_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Bank Reconciliation Authorized", "bank_reconciliation_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Claim Batch Authorized", "claim_batch_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Claim Line Authorized", "claim_line_authorized", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Remittance Import Authorized", "remittance_import_authorized", "Check", default="0", description="Blocked in Phase 55."),

        make_field("Line Status", "line_status_section", "Section Break"),
        make_field("Post Closure Routing Finalisation Hold", "post_closure_routing_finalisation_hold", "Check", default="1", in_list_view=1),
        make_field("Post Closure Routing Finalisation Hold Reason", "post_closure_routing_finalisation_hold_reason", "Small Text"),
        make_field("Line Ready for Post Closure Routing Finalisation", "line_ready_for_post_closure_routing_finalisation", "Check", default="0", in_list_view=1),
        make_field("Post Closure Routing Finalisation Line Status", "post_closure_routing_finalisation_line_status", "Select", options="Draft\nReady\nApproved\nRoute Finalised\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=POST_CLOSURE_ROUTING_FINALISATION_LINE,
        fields=fields,
        istable=1,
    )


def create_post_closure_routing_finalisation_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-POST-CLOSURE-ROUTE-FINAL-.YYYY.-.#####", default="NDIS-POST-CLOSURE-ROUTE-FINAL-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Routing Finalisation\nRouting Finalisation Approved\nPost Closure Routing Finalised\nReturned to Routing Preparation\nCancelled", default="Draft", in_list_view=1),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Post Closure Routing Finalisation Run Ready", "post_closure_routing_finalisation_run_ready", "Check", read_only=1, in_list_view=1),
        make_field("No Post Closure Routing Finalisation Candidate Found", "no_post_closure_routing_finalisation_candidate_found", "Check", default="0", read_only=1),

        make_field("Target Routing Finalisation Mode", "target_routing_finalisation_mode", "Select", options="CRM Routing Finalisation Only", default="CRM Routing Finalisation Only"),
        make_field("Routing Finalisation Allowed", "routing_finalisation_allowed", "Check", default="0"),

        make_field("Actual Recovery Case Closure Allowed", "actual_recovery_case_closure_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Communication Creation Allowed", "communication_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Email Send Allowed", "email_send_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("ToDo Creation Allowed", "todo_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Task Creation Allowed", "task_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Recovery Case Creation Allowed", "recovery_case_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Journal Entry Creation Allowed", "journal_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Manual GL Creation Allowed", "manual_gl_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Payment Entry Creation Allowed", "payment_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Adjustment Creation Allowed", "adjustment_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Bank Reconciliation Allowed", "bank_reconciliation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Claim Batch Creation Allowed", "claim_batch_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Claim Line Creation Allowed", "claim_line_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),
        make_field("Remittance Import Creation Allowed", "remittance_import_creation_allowed", "Check", default="0", description="Blocked in Phase 55."),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Post Closure Routing Finalisation Line Count", "post_closure_routing_finalisation_line_count", "Int", read_only=1),
        make_field("Post Closure Routing Finalisation Amount Total", "post_closure_routing_finalisation_amount_total", "Currency", read_only=1),
        make_field("Post Closure Routing Finalisation Ready Count", "post_closure_routing_finalisation_ready_count", "Int", read_only=1),
        make_field("Post Closure Routing Finalisation Hold Count", "post_closure_routing_finalisation_hold_count", "Int", read_only=1),
        make_field("Routing Finalised Count", "routing_finalised_count", "Int", read_only=1),
        make_field("Recovery Cycle Closed Count", "recovery_cycle_closed_count", "Int", read_only=1),
        make_field("Repeat Follow Up Route Finalised Count", "repeat_follow_up_route_finalised_count", "Int", read_only=1),
        make_field("Payment Promise Monitoring Route Finalised Count", "payment_promise_monitoring_route_finalised_count", "Int", read_only=1),
        make_field("Evidence Follow Up Route Finalised Count", "evidence_follow_up_route_finalised_count", "Int", read_only=1),
        make_field("Dispute Review Route Finalised Count", "dispute_review_route_finalised_count", "Int", read_only=1),
        make_field("Contact Correction Route Finalised Count", "contact_correction_route_finalised_count", "Int", read_only=1),
        make_field("Escalation Route Finalised Count", "escalation_route_finalised_count", "Int", read_only=1),
        make_field("Manual Review Route Finalised Count", "manual_review_route_finalised_count", "Int", read_only=1),
        make_field("Blocked Actual Recovery Case Closure Count", "blocked_actual_recovery_case_closure_count", "Int", read_only=1),
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
        make_field("NDIS Financial Profile", "ndis_financial_profile", "Data"),
        make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import"),

        make_field("Post Closure Routing Preparation Run", "post_closure_routing_preparation_run", "Link", options=POST_CLOSURE_ROUTING_PREPARATION_RUN, reqd=1, in_list_view=1),
        make_field("Recovery Outcome Closure Finalisation Run", "recovery_outcome_closure_finalisation_run", "Link", options=RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN),
        make_field("Recovery Outcome Closure Draft Run", "recovery_outcome_closure_draft_run", "Link", options=RECOVERY_OUTCOME_CLOSURE_DRAFT_RUN),
        make_field("Recovery Outcome Closure Preparation Run", "recovery_outcome_closure_preparation_run", "Link", options=RECOVERY_OUTCOME_CLOSURE_PREPARATION_RUN),
        make_field("Recovery Outcome Action Completion Run", "recovery_outcome_action_completion_run", "Link", options=RECOVERY_OUTCOME_ACTION_COMPLETION_RUN),

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
        make_field("Post Closure Routing Finalisation Owner", "post_closure_routing_finalisation_owner", "Link", options="User", in_list_view=1),
        make_field("Post Closure Routing Preparation Owner", "post_closure_routing_preparation_owner", "Link", options="User"),
        make_field("Finalised By", "finalised_by", "Link", options="User", read_only=1),
        make_field("Finalised On", "finalised_on", "Datetime", read_only=1),

        make_field("Post Closure Routing Finalisation Lines", "post_closure_routing_finalisation_lines_section", "Section Break"),
        make_field("Post Closure Routing Finalisation Lines", "post_closure_routing_finalisation_lines", "Table", options=POST_CLOSURE_ROUTING_FINALISATION_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Post Closure Routing Finalisation Notes", "post_closure_routing_finalisation_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=POST_CLOSURE_ROUTING_FINALISATION_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def _delete_custom_field_if_exists(doctype, fieldname, message):
    custom_field_name = f"{doctype}-{fieldname}"
    if frappe.db.exists("Custom Field", custom_field_name):
        frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True, force=True)
        print(message.format(custom_field_name=custom_field_name))


def repair_partial_crm_deal_phase55_fields():
    expected = {
        "ndis_post_closure_routing_final_run_required": {
            "fieldtype": "Check",
            "default": "0",
            "options": None,
        },
        "ndis_post_closure_routing_final_run": {
            "fieldtype": "Small Text",
            "options": None,
        },
        "post_closure_routing_finalisation_status": {
            "fieldtype": "Small Text",
            "options": None,
        },
        "post_closure_routing_finalisation_ready": {
            "fieldtype": "Check",
            "default": "0",
            "options": None,
        },
    }

    for fieldname, values in expected.items():
        custom_field_name = f"{CRM_DEAL}-{fieldname}"
        if not frappe.db.exists("Custom Field", custom_field_name):
            continue

        custom_field = frappe.get_doc("Custom Field", custom_field_name)
        for key, value in values.items():
            custom_field.set(key, value)
        custom_field.save(ignore_permissions=True)
        print(f"Repaired CRM Deal Phase 55 field: {custom_field_name}")


def repair_partial_shared_phase55_fields(shared_doctypes):
    expected = {
        "ndis_post_closure_routing_final_run": {
            "fieldtype": "Small Text",
            "options": None,
        },
        "post_closure_routing_finalisation_status": {
            "fieldtype": "Small Text",
            "options": None,
        },
        "post_closure_routing_finalisation_ready": {
            "fieldtype": "Check",
            "default": "0",
            "options": None,
        },
    }

    for doctype in shared_doctypes:
        for fieldname, values in expected.items():
            custom_field_name = f"{doctype}-{fieldname}"
            if not frappe.db.exists("Custom Field", custom_field_name):
                continue

            custom_field = frappe.get_doc("Custom Field", custom_field_name)
            if custom_field.get("fieldtype") != values.get("fieldtype"):
                frappe.delete_doc("Custom Field", custom_field_name, ignore_permissions=True, force=True)
                print(f"Removed incompatible shared Phase 55 field: {custom_field_name}")
                continue

            for key, value in values.items():
                custom_field.set(key, value)
            custom_field.save(ignore_permissions=True)
            print(f"Repaired shared Phase 55 field: {custom_field_name}")


def remove_partial_intake_phase55_fields():
    for fieldname in (
        "ndis_post_closure_routing_final_run",
        "post_closure_routing_finalisation_status",
        "post_closure_routing_finalisation_ready",
        "post_closure_routing_finalisation_section",
    ):
        _delete_custom_field_if_exists(
            "NDIS Participant Intake",
            fieldname,
            "Removed unsupported Intake Phase 55 field: {custom_field_name}",
        )


def create_custom_fields_phase55():
    deal_fields = [
        {
            "fieldname": "post_closure_routing_finalisation_section",
            "label": "NDIS Post Closure Routing Finalisation Run",
            "fieldtype": "Section Break",
            "insert_after": "post_closure_routing_preparation_ready",
        },
        {
            "fieldname": "ndis_post_closure_routing_final_run_required",
            "label": "Post Closure Routing Finalisation Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "post_closure_routing_finalisation_section",
        },
        {
            "fieldname": "ndis_post_closure_routing_final_run",
            "label": "NDIS CRM Post Closure Routing Finalisation Run",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "ndis_post_closure_routing_final_run_required",
        },
        {
            "fieldname": "post_closure_routing_finalisation_status",
            "label": "Post Closure Routing Finalisation Status",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "ndis_post_closure_routing_final_run",
        },
        {
            "fieldname": "post_closure_routing_finalisation_ready",
            "label": "Post Closure Routing Finalisation Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "post_closure_routing_finalisation_status",
        },
    ]

    shared_fields = [
        {
            "fieldname": "post_closure_routing_finalisation_section",
            "label": "NDIS Post Closure Routing Finalisation Run",
            "fieldtype": "Section Break",
            "insert_after": "post_closure_routing_preparation_ready",
        },
        {
            "fieldname": "ndis_post_closure_routing_final_run",
            "label": "NDIS CRM Post Closure Routing Finalisation Run",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "post_closure_routing_finalisation_section",
        },
        {
            "fieldname": "post_closure_routing_finalisation_status",
            "label": "Post Closure Routing Finalisation Status",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "ndis_post_closure_routing_final_run",
        },
        {
            "fieldname": "post_closure_routing_finalisation_ready",
            "label": "Post Closure Routing Finalisation Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "post_closure_routing_finalisation_status",
        },
    ]

    shared_doctypes = [
        POST_CLOSURE_ROUTING_PREPARATION_RUN,
        RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN,
        RECOVERY_OUTCOME_CLOSURE_DRAFT_RUN,
        RECOVERY_OUTCOME_CLOSURE_PREPARATION_RUN,
        RECOVERY_OUTCOME_ACTION_COMPLETION_RUN,
    ]

    custom_fields = {
        CRM_DEAL: deal_fields,
    }

    for doctype in shared_doctypes:
        custom_fields[doctype] = shared_fields

    repair_partial_crm_deal_phase55_fields()
    repair_partial_shared_phase55_fields(shared_doctypes)
    remove_partial_intake_phase55_fields()
    safe_create_custom_fields(custom_fields)
    print("Created / updated Phase 55 post-closure routing finalisation custom fields.")


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


def _append_before_last(script, anchor, insert):
    idx = script.rfind(anchor)
    if idx == -1:
        return script.rstrip() + "\n" + insert.strip() + "\n"

    prefix = script[:idx]
    suffix = script[idx:]
    insert_text = insert.strip()
    if not prefix.rstrip().endswith(("[", ",")):
        insert_text = ",\n" + insert_text

    return prefix + insert_text + suffix


def _phase55_deal_actions():
    return r'''
// NDIS CRM Phase 55 Deal Actions
{
  label: "Create Post Closure Routing Finalisation Run",
  onClick: () => {
    call("ndis_crm.phase55_post_closure_routing_finalisation.create_post_closure_routing_finalisation_run_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Post Closure Routing Finalisation Run Created" : "Existing Post Closure Routing Finalisation Run Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-post-closure-routing-finalisation-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Post Closure Routing Finalisation Run",
  onClick: () => {
    if (doc.ndis_post_closure_routing_final_run) {
      window.open(`/app/ndis-crm-post-closure-routing-finalisation-run/${doc.ndis_post_closure_routing_final_run}`, "_blank")
    } else {
      createToast({ title: "No Post Closure Routing Finalisation Run linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    try:
        from ndis_crm.setup.phase54_recovery_outcome_post_closure_routing_preparation import _deal_script as phase54_deal_script

        script = phase54_deal_script()
    except Exception:
        script = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
    ]
  }
}
'''.strip()

    if "NDIS CRM Phase 55 Deal Actions" in script:
        return script

    return _append_before_last(script, "\n    ]", _phase55_deal_actions())


def create_or_extend_crm_deal_script():
    upsert_doc(
        "CRM Form Script",
        "NDIS CRM Deal Actions",
        {
            "dt": "CRM Deal",
            "view": "Form",
            "enabled": 1,
            "is_standard": 0,
            "script": _deal_script(),
        },
    )


def create_form_scripts():
    create_or_extend_crm_deal_script()

    prep_script = r'''
frappe.ui.form.on("NDIS CRM Post Closure Routing Preparation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Post Closure Routing Finalisation Run"), function () {
            frappe.call({
                method: "ndis_crm.phase55_post_closure_routing_finalisation.create_post_closure_routing_finalisation_run_from_preparation_run",
                args: { post_closure_routing_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating post-closure routing finalisation run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Post Closure Routing Finalisation Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Post Closure Routing Finalisation Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_post_closure_routing_final_run) {
            frm.add_custom_button(__("Open Post Closure Routing Finalisation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Post Closure Routing Finalisation Run", frm.doc.ndis_post_closure_routing_final_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Post Closure Routing Finalisation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Finalisation Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase55_post_closure_routing_finalisation.generate_post_closure_routing_finalisation_lines",
                args: { post_closure_routing_finalisation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating routing finalisation lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Routing finalisation lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Finalisation Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase55_post_closure_routing_finalisation.validate_post_closure_routing_finalisation_readiness",
                args: { post_closure_routing_finalisation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating routing finalisation readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Routing finalisation readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Finalisation"), function () {
            frappe.call({
                method: "ndis_crm.phase55_post_closure_routing_finalisation.mark_ready_for_post_closure_routing_finalisation",
                args: { post_closure_routing_finalisation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for routing finalisation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for routing finalisation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Routing Finalisation"), function () {
            frappe.call({
                method: "ndis_crm.phase55_post_closure_routing_finalisation.approve_post_closure_routing_finalisation_run",
                args: { post_closure_routing_finalisation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving routing finalisation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Routing Finalisation approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Finalise Post Closure Routing"), function () {
            frappe.confirm(
                __("This finalises CRM-only post-closure routing. It will not close recovery cases, create communications, tasks, emails, accounting, claim, remittance, adjustment, or bank reconciliation records."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase55_post_closure_routing_finalisation.finalise_post_closure_routing",
                        args: { post_closure_routing_finalisation_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Finalising post-closure routing...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Post-closure routing finalised"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.post_closure_routing_preparation_run) {
            frm.add_custom_button(__("Open Routing Preparation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Post Closure Routing Preparation Run", frm.doc.post_closure_routing_preparation_run);
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
            "NDIS CRM Post Closure Routing Preparation Phase55 Actions",
            {
                "dt": POST_CLOSURE_ROUTING_PREPARATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": prep_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Post Closure Routing Finalisation Run Actions",
            {
                "dt": POST_CLOSURE_ROUTING_FINALISATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
