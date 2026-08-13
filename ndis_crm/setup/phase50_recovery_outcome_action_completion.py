import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
ROSTER_REQUEST = "NDIS CRM Roster Build Request"
SERVICE_FILE = "NDIS Participant Service File"
SESSION_DRAFT = "NDIS CRM Service Session Draft"
EVIDENCE_REVIEW = "NDIS CRM Service Delivery Evidence Review"
DOWNSTREAM_PREPARATION = "NDIS CRM Downstream Preparation"
ATTENDANCE_DRAFT = "NDIS CRM Attendance Draft"
BILLING_DRAFT = "NDIS CRM Billing Draft"
CLAIM_DRAFT = "NDIS CRM Claim Draft"
INVOICE_DRAFT = "NDIS CRM Invoice Draft"
SALES_INVOICE_DRAFT_RUN = "NDIS CRM Sales Invoice Draft Run"
SALES_INVOICE_SUBMISSION_RUN = "NDIS CRM Sales Invoice Submission Run"
CLAIM_BATCH_DRAFT_RUN = "NDIS CRM Claim Batch Draft Run"
CLAIM_BATCH_SUBMISSION_RUN = "NDIS CRM Claim Batch Submission Run"
CLAIM_EXPORT_PREP_RUN = "NDIS CRM Claim Export Preparation Run"
CLAIM_LODGEMENT_CONFIRMATION_RUN = "NDIS CRM Claim Lodgement Confirmation Run"
REMITTANCE_IMPORT_PREP_RUN = "NDIS CRM Remittance Import Preparation Run"
ACTUAL_REMITTANCE_IMPORT_RUN = "NDIS CRM Actual Remittance Import Run"
REMITTANCE_MATCHING_REVIEW_RUN = "NDIS CRM Remittance Matching Review Run"
PAYMENT_ALLOCATION_PREP_RUN = "NDIS CRM Payment Allocation Preparation Run"
PAYMENT_ENTRY_DRAFT_RUN = "NDIS CRM Payment Entry Draft Run"
PAYMENT_ENTRY_SUBMISSION_RUN = "NDIS CRM Payment Entry Submission Run"
REMITTANCE_IMPORT_FINALISATION_RUN = "NDIS CRM Remittance Import Finalisation Run"
VARIANCE_REJECTION_REVIEW_RUN = "NDIS CRM Variance Rejection Review Run"
WRITE_OFF_PREPARATION_RUN = "NDIS CRM Write Off Preparation Run"
WRITE_OFF_DRAFT_RUN = "NDIS CRM Write Off Draft Run"
WRITE_OFF_JE_DRAFT_RUN = "NDIS CRM Write Off JE Draft Run"
WRITE_OFF_JE_SUBMISSION_RUN = "NDIS CRM Write Off JE Submission Run"
WRITE_OFF_FINALISATION_RUN = "NDIS CRM Write Off Finalisation Run"
RECOVERY_PREPARATION_RUN = "NDIS CRM Recovery Preparation Run"
RECOVERY_CASE_DRAFT_RUN = "NDIS CRM Recovery Case Draft Run"
RECOVERY_CASE_SUBMISSION_RUN = "NDIS CRM Recovery Case Submission Run"
RECOVERY_FOLLOW_UP_PREPARATION_RUN = "NDIS CRM Recovery Follow Up Preparation Run"
RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN = "NDIS CRM Recovery Follow Up Task Draft Run"
RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN = "NDIS CRM Recovery Follow Up Task Activation Run"
RECOVERY_COMMUNICATION_DRAFT_PREPARATION_RUN = "NDIS CRM Recovery Communication Draft Preparation Run"
RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN = "NDIS CRM Recovery Communication Draft Creation Run"
RECOVERY_COMMUNICATION_DISPATCH_RUN = "NDIS CRM Recovery Communication Dispatch Run"
RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN = "NDIS CRM Recovery Communication Outcome Capture Run"
RECOVERY_OUTCOME_ACTION_PREPARATION_RUN = "NDIS CRM Recovery Outcome Action Preparation Run"
RECOVERY_OUTCOME_ACTION_DRAFT_RUN = "NDIS CRM Recovery Outcome Action Draft Run"
RECOVERY_OUTCOME_ACTION_ACTIVATION_RUN = "NDIS CRM Recovery Outcome Action Activation Run"

RECOVERY_OUTCOME_ACTION_COMPLETION_RUN = "NDIS CRM Recovery Outcome Action Completion Run"
RECOVERY_OUTCOME_ACTION_COMPLETION_LINE = "NDIS CRM Recovery Outcome Action Completion Line"

TODO = "ToDo"
TASK = "Task"


def install():
    ensure_required_doctypes()
    create_recovery_outcome_action_completion_doctypes()
    create_custom_fields_phase50()
    create_optional_action_target_custom_fields()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 50 Recovery Outcome Action Completion gate installed successfully.")


def doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


def safe_create_custom_fields(custom_fields):
    try:
        create_custom_fields(custom_fields, update=True)
    except TypeError:
        create_custom_fields(custom_fields)


def repair_partial_crm_deal_phase50_fields():
    expected = {
        "ndis_recovery_outcome_action_completion_run_required": {
            "fieldtype": "Check",
            "default": "0",
            "options": None,
        },
        "ndis_recovery_outcome_action_completion_run": {
            "fieldtype": "Small Text",
            "options": None,
        },
        "recovery_outcome_action_completion_status": {
            "fieldtype": "Small Text",
            "options": None,
        },
        "recovery_outcome_action_completion_ready": {
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
        changed = False
        for key, value in values.items():
            if custom_field.get(key) != value:
                custom_field.set(key, value)
                changed = True

        if changed:
            custom_field.save(ignore_permissions=True)
            print(f"Repaired CRM Deal Phase 50 field: {custom_field_name}")


def ensure_required_doctypes():
    required = [
        CRM_DEAL,
        INTAKE,
        HANDOVER,
        FINANCE_ONBOARDING,
        OPERATIONS_SETUP,
        SCHEDULE_DRAFT,
        ROSTER_REQUEST,
        SERVICE_FILE,
        SESSION_DRAFT,
        EVIDENCE_REVIEW,
        DOWNSTREAM_PREPARATION,
        BILLING_DRAFT,
        CLAIM_DRAFT,
        INVOICE_DRAFT,
        SALES_INVOICE_DRAFT_RUN,
        SALES_INVOICE_SUBMISSION_RUN,
        CLAIM_BATCH_DRAFT_RUN,
        CLAIM_BATCH_SUBMISSION_RUN,
        CLAIM_EXPORT_PREP_RUN,
        CLAIM_LODGEMENT_CONFIRMATION_RUN,
        REMITTANCE_IMPORT_PREP_RUN,
        ACTUAL_REMITTANCE_IMPORT_RUN,
        REMITTANCE_MATCHING_REVIEW_RUN,
        PAYMENT_ALLOCATION_PREP_RUN,
        PAYMENT_ENTRY_DRAFT_RUN,
        PAYMENT_ENTRY_SUBMISSION_RUN,
        REMITTANCE_IMPORT_FINALISATION_RUN,
        VARIANCE_REJECTION_REVIEW_RUN,
        RECOVERY_PREPARATION_RUN,
        RECOVERY_CASE_DRAFT_RUN,
        RECOVERY_CASE_SUBMISSION_RUN,
        RECOVERY_FOLLOW_UP_PREPARATION_RUN,
        RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN,
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        RECOVERY_COMMUNICATION_DRAFT_PREPARATION_RUN,
        RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN,
        RECOVERY_COMMUNICATION_DISPATCH_RUN,
        RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN,
        RECOVERY_OUTCOME_ACTION_PREPARATION_RUN,
        RECOVERY_OUTCOME_ACTION_DRAFT_RUN,
        RECOVERY_OUTCOME_ACTION_ACTIVATION_RUN,
        "Sales Invoice",
        "Payment Entry",
        "Journal Entry",
        "GL Entry",
        "NDIS Remittance Import",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 50 DocTypes: " + ", ".join(missing))

    print("Required Phase 50 DocTypes found.")


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


def create_recovery_outcome_action_completion_doctypes():
    create_recovery_outcome_action_completion_line()
    create_recovery_outcome_action_completion_run()


def create_recovery_outcome_action_completion_line():
    fields = [
        make_field("Source", "source_section", "Section Break"),
        make_field("Recovery Outcome Action Completion Source Key", "recovery_outcome_action_completion_source_key", "Data", read_only=1),

        make_field("Completion Targets", "completion_targets_section", "Section Break"),
        make_field("Source Target Action Mode Snapshot", "source_target_action_mode_snapshot", "Data", read_only=1),
        make_field("Source Target Action DocType", "source_target_action_doctype", "Data", read_only=1),
        make_field("Source Target Action Name", "source_target_action_name", "Data", read_only=1),
        make_field("Source Target Action Status", "source_target_action_status", "Data", read_only=1),
        make_field("Target Activation Mode Snapshot", "target_activation_mode_snapshot", "Data", read_only=1),
        make_field("Target Completion Mode Snapshot", "target_completion_mode_snapshot", "Data", read_only=1),
        make_field("Target ToDo", "target_todo", "Data", read_only=1),
        make_field("Target ToDo Status", "target_todo_status", "Data", read_only=1),
        make_field("Target Task", "target_task", "Data", read_only=1),
        make_field("Target Task Status", "target_task_status", "Data", read_only=1),

        make_field("Outcome Snapshot", "outcome_snapshot_section", "Section Break"),
        make_field("Outcome Status Snapshot", "outcome_status_snapshot", "Data", read_only=1),
        make_field("Outcome Summary", "outcome_summary", "Small Text"),
        make_field("Response Received On", "response_received_on", "Datetime"),
        make_field("Response Received From", "response_received_from", "Data"),
        make_field("Response Reference", "response_reference", "Data"),
        make_field("Promised Payment Date", "promised_payment_date", "Date"),
        make_field("Promised Payment Amount", "promised_payment_amount", "Currency"),
        make_field("Evidence Requested", "evidence_requested", "Check", default="0"),
        make_field("Dispute Reason", "dispute_reason", "Small Text"),
        make_field("Correct Contact Name", "correct_contact_name", "Data"),
        make_field("Correct Contact Email", "correct_contact_email", "Data"),
        make_field("Correct Contact Phone", "correct_contact_phone", "Data"),
        make_field("Next Action Recommendation", "next_action_recommendation", "Small Text"),

        make_field("Dispatch Snapshot", "dispatch_snapshot_section", "Section Break"),
        make_field("Target Dispatch Mode Snapshot", "target_dispatch_mode_snapshot", "Data", read_only=1),
        make_field("Target Communication", "target_communication", "Data", read_only=1),
        make_field("Target Communication Status", "target_communication_status", "Data", read_only=1),
        make_field("Target Email Queue Status", "target_email_queue_status", "Data", read_only=1),
        make_field("Dispatch Reference", "dispatch_reference", "Small Text", read_only=1),
        make_field("Dispatch Line Status Snapshot", "dispatch_line_status_snapshot", "Data", read_only=1),

        make_field("Recovery Case Snapshot", "case_snapshot_section", "Section Break"),
        make_field("Target Case DocType", "target_case_doctype", "Data", read_only=1),
        make_field("Target Case Name", "target_case_name", "Data", read_only=1),
        make_field("Target Case Docstatus", "target_case_docstatus", "Int", read_only=1),
        make_field("Target Case Status", "target_case_status", "Data", read_only=1),

        make_field("References", "references_section", "Section Break"),
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

        make_field("Action Completion", "action_completion_section", "Section Break"),
        make_field("Recovery Outcome Action Completion Source Ready", "recovery_outcome_action_completion_source_ready", "Check", default="0"),
        make_field("Action Type", "action_type", "Data", in_list_view=1),
        make_field("Action Route", "action_route", "Data", in_list_view=1),
        make_field("Action Priority", "action_priority", "Select", options="High\nNormal\nLow", default="Normal", in_list_view=1),
        make_field("Action Owner", "action_owner", "Link", options="User", in_list_view=1),
        make_field("Action Due Date", "action_due_date", "Date", in_list_view=1),
        make_field("Action Instruction", "action_instruction", "Small Text"),
        make_field("Action Decision Summary", "action_decision_summary", "Small Text"),
        make_field("Action Completion Review Complete", "action_completion_review_complete", "Check", default="0"),
        make_field("Action Completion Authorized", "action_completion_authorized", "Check", default="0"),
        make_field("ToDo Completion Authorized", "todo_completion_authorized", "Check", default="0"),
        make_field("Task Completion Authorized", "task_completion_authorized", "Check", default="0"),
        make_field("Completion Summary", "completion_summary", "Small Text"),
        make_field("Completion Reference", "completion_reference", "Data"),

        make_field("Blocked Downstream Controls", "blocked_downstream_section", "Section Break"),
        make_field("Communication Creation Authorized", "communication_creation_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Email Send Authorized", "email_send_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Event Creation Authorized", "event_creation_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Recovery Case Creation Authorized", "recovery_case_creation_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Journal Entry Authorized", "journal_entry_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Manual GL Authorized", "manual_gl_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Payment Entry Authorized", "payment_entry_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Sales Invoice Authorized", "sales_invoice_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Adjustment Authorized", "adjustment_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Bank Reconciliation Authorized", "bank_reconciliation_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Claim Batch Authorized", "claim_batch_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Claim Line Authorized", "claim_line_authorized", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Remittance Import Authorized", "remittance_import_authorized", "Check", default="0", description="Blocked in Phase 50."),

        make_field("Line Status", "line_status_section", "Section Break"),
        make_field("Recovery Outcome Action Completion Hold", "recovery_outcome_action_completion_hold", "Check", default="1", in_list_view=1),
        make_field("Recovery Outcome Action Completion Hold Reason", "recovery_outcome_action_completion_hold_reason", "Small Text"),
        make_field("Line Ready for Recovery Outcome Action Completion", "line_ready_for_recovery_outcome_action_completion", "Check", default="0", in_list_view=1),
        make_field("Recovery Outcome Action Completion Line Status", "recovery_outcome_action_completion_line_status", "Select", options="Draft\nReady\nApproved\nCRM Action Completed\nReleased ToDo Completed\nReleased Task Completed\nReleased ToDo and Task Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=RECOVERY_OUTCOME_ACTION_COMPLETION_LINE,
        fields=fields,
        istable=1,
    )


def create_recovery_outcome_action_completion_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-RECOVERY-ACTION-COMPLETE-.YYYY.-.#####", default="NDIS-RECOVERY-ACTION-COMPLETE-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Action Completion\nAction Completion Approved\nActions Completed\nReturned to Action Activation\nCancelled", default="Draft", in_list_view=1),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Recovery Outcome Action Completion Run Ready", "recovery_outcome_action_completion_run_ready", "Check", read_only=1, in_list_view=1),
        make_field("No Recovery Outcome Action Completion Candidate Found", "no_recovery_outcome_action_completion_candidate_found", "Check", default="0", read_only=1),

        make_field("Target Action Completion Mode", "target_action_completion_mode", "Select", options="CRM Action Completion Only\nComplete Released ToDo If Available\nComplete Released Task If Available\nComplete Released ToDo and Task If Available", default="CRM Action Completion Only"),
        make_field("Optional ToDo DocType Available", "optional_todo_doctype_available", "Check", read_only=1),
        make_field("Optional Task DocType Available", "optional_task_doctype_available", "Check", read_only=1),

        make_field("Action Completion Allowed", "action_completion_allowed", "Check", default="0"),
        make_field("ToDo Completion Allowed", "todo_completion_allowed", "Check", default="0"),
        make_field("Task Completion Allowed", "task_completion_allowed", "Check", default="0"),

        make_field("Communication Creation Allowed", "communication_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Email Send Allowed", "email_send_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Recovery Case Creation Allowed", "recovery_case_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Journal Entry Creation Allowed", "journal_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Manual GL Creation Allowed", "manual_gl_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Payment Entry Creation Allowed", "payment_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Adjustment Creation Allowed", "adjustment_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Bank Reconciliation Allowed", "bank_reconciliation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Claim Batch Creation Allowed", "claim_batch_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Claim Line Creation Allowed", "claim_line_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),
        make_field("Remittance Import Creation Allowed", "remittance_import_creation_allowed", "Check", default="0", description="Blocked in Phase 50."),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Recovery Outcome Action Completion Line Count", "recovery_outcome_action_completion_line_count", "Int", read_only=1),
        make_field("Recovery Outcome Action Completion Amount Total", "recovery_outcome_action_completion_amount_total", "Currency", read_only=1),
        make_field("Recovery Outcome Action Completion Ready Count", "recovery_outcome_action_completion_ready_count", "Int", read_only=1),
        make_field("Recovery Outcome Action Completion Hold Count", "recovery_outcome_action_completion_hold_count", "Int", read_only=1),
        make_field("CRM Action Completed Count", "crm_action_completed_count", "Int", read_only=1),
        make_field("ToDo Completed Count", "todo_completed_count", "Int", read_only=1),
        make_field("Task Completed Count", "task_completed_count", "Int", read_only=1),
        make_field("Action Completed Count", "action_completed_count", "Int", read_only=1),
        make_field("Blocked Communication Count", "blocked_communication_count", "Int", read_only=1),
        make_field("Blocked Email Send Count", "blocked_email_send_count", "Int", read_only=1),
        make_field("Blocked Event Count", "blocked_event_count", "Int", read_only=1),
        make_field("Blocked Recovery Case Count", "blocked_recovery_case_count", "Int", read_only=1),
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
        make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
        make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
        make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER),
        make_field("NDIS CRM Finance Onboarding", "finance_onboarding", "Link", options=FINANCE_ONBOARDING),
        make_field("NDIS CRM Operations Setup", "operations_setup", "Link", options=OPERATIONS_SETUP),
        make_field("NDIS CRM Service Schedule Draft", "service_schedule_draft", "Link", options=SCHEDULE_DRAFT),
        make_field("NDIS CRM Roster Build Request", "roster_build_request", "Link", options=ROSTER_REQUEST),
        make_field("NDIS Participant Service File", "participant_service_file", "Link", options=SERVICE_FILE),
        make_field("NDIS CRM Service Session Draft", "service_session_draft", "Link", options=SESSION_DRAFT),
        make_field("NDIS CRM Delivery Evidence Review", "delivery_evidence_review", "Link", options=EVIDENCE_REVIEW),
        make_field("NDIS CRM Downstream Preparation", "downstream_preparation", "Link", options=DOWNSTREAM_PREPARATION),
    ]

    if doctype_exists(ATTENDANCE_DRAFT):
        fields.append(make_field("NDIS CRM Attendance Draft", "attendance_draft", "Link", options=ATTENDANCE_DRAFT))
    else:
        fields.append(make_field("NDIS CRM Attendance Draft", "attendance_draft", "Data"))

    fields += [
        make_field("NDIS CRM Billing Draft", "billing_draft", "Link", options=BILLING_DRAFT),
        make_field("NDIS CRM Claim Draft", "claim_draft", "Link", options=CLAIM_DRAFT),
        make_field("NDIS CRM Invoice Draft", "invoice_draft", "Link", options=INVOICE_DRAFT),
        make_field("NDIS CRM Sales Invoice Draft Run", "sales_invoice_draft_run", "Link", options=SALES_INVOICE_DRAFT_RUN),
        make_field("NDIS CRM Sales Invoice Submission Run", "sales_invoice_submission_run", "Link", options=SALES_INVOICE_SUBMISSION_RUN),
        make_field("NDIS CRM Claim Batch Draft Run", "claim_batch_draft_run", "Link", options=CLAIM_BATCH_DRAFT_RUN),
        make_field("NDIS CRM Claim Batch Submission Run", "claim_batch_submission_run", "Link", options=CLAIM_BATCH_SUBMISSION_RUN),
        make_field("NDIS CRM Claim Export Preparation Run", "claim_export_preparation_run", "Link", options=CLAIM_EXPORT_PREP_RUN),
        make_field("NDIS CRM Claim Lodgement Confirmation Run", "claim_lodgement_confirmation_run", "Link", options=CLAIM_LODGEMENT_CONFIRMATION_RUN),
        make_field("NDIS CRM Remittance Import Preparation Run", "remittance_import_preparation_run", "Link", options=REMITTANCE_IMPORT_PREP_RUN),
        make_field("NDIS CRM Actual Remittance Import Run", "actual_remittance_import_run", "Link", options=ACTUAL_REMITTANCE_IMPORT_RUN),
        make_field("NDIS CRM Remittance Matching Review Run", "remittance_matching_review_run", "Link", options=REMITTANCE_MATCHING_REVIEW_RUN),
        make_field("NDIS CRM Payment Allocation Preparation Run", "payment_allocation_preparation_run", "Link", options=PAYMENT_ALLOCATION_PREP_RUN),
        make_field("NDIS CRM Payment Entry Draft Run", "payment_entry_draft_run", "Link", options=PAYMENT_ENTRY_DRAFT_RUN),
        make_field("NDIS CRM Payment Entry Submission Run", "payment_entry_submission_run", "Link", options=PAYMENT_ENTRY_SUBMISSION_RUN),
        make_field("NDIS CRM Remittance Import Finalisation Run", "remittance_import_finalisation_run", "Link", options=REMITTANCE_IMPORT_FINALISATION_RUN),
        make_field("NDIS CRM Variance Rejection Review Run", "variance_rejection_review_run", "Link", options=VARIANCE_REJECTION_REVIEW_RUN),
        make_field("NDIS CRM Write Off Preparation Run", "write_off_preparation_run", "Link", options=WRITE_OFF_PREPARATION_RUN),
        make_field("NDIS CRM Write Off Draft Run", "write_off_draft_run", "Link", options=WRITE_OFF_DRAFT_RUN),
        make_field("NDIS CRM Write Off JE Draft Run", "write_off_je_draft_run", "Link", options=WRITE_OFF_JE_DRAFT_RUN),
        make_field("NDIS CRM Write Off JE Submission Run", "write_off_je_submission_run", "Link", options=WRITE_OFF_JE_SUBMISSION_RUN),
        make_field("NDIS CRM Write Off Finalisation Run", "write_off_finalisation_run", "Link", options=WRITE_OFF_FINALISATION_RUN),
        make_field("NDIS CRM Recovery Preparation Run", "recovery_preparation_run", "Link", options=RECOVERY_PREPARATION_RUN),
        make_field("NDIS CRM Recovery Case Draft Run", "recovery_case_draft_run", "Link", options=RECOVERY_CASE_DRAFT_RUN),
        make_field("NDIS CRM Recovery Case Submission Run", "recovery_case_submission_run", "Link", options=RECOVERY_CASE_SUBMISSION_RUN),
        make_field("NDIS CRM Recovery Follow Up Preparation Run", "recovery_follow_up_preparation_run", "Link", options=RECOVERY_FOLLOW_UP_PREPARATION_RUN),
        make_field("NDIS CRM Recovery Follow Up Task Draft Run", "recovery_follow_up_task_draft_run", "Link", options=RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN),
        make_field("NDIS CRM Recovery Follow Up Task Activation Run", "recovery_follow_up_task_activation_run", "Link", options=RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN),
        make_field("NDIS CRM Recovery Communication Draft Preparation Run", "recovery_communication_draft_preparation_run", "Link", options=RECOVERY_COMMUNICATION_DRAFT_PREPARATION_RUN),
        make_field("NDIS CRM Recovery Communication Draft Creation Run", "recovery_communication_draft_creation_run", "Link", options=RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN),
        make_field("NDIS CRM Recovery Communication Dispatch Run", "recovery_communication_dispatch_run", "Link", options=RECOVERY_COMMUNICATION_DISPATCH_RUN),
        make_field("NDIS CRM Recovery Communication Outcome Capture Run", "recovery_communication_outcome_capture_run", "Link", options=RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN),
        make_field("NDIS CRM Recovery Outcome Action Preparation Run", "recovery_outcome_action_preparation_run", "Link", options=RECOVERY_OUTCOME_ACTION_PREPARATION_RUN),
        make_field("NDIS CRM Recovery Outcome Action Draft Run", "recovery_outcome_action_draft_run", "Link", options=RECOVERY_OUTCOME_ACTION_DRAFT_RUN),
        make_field("NDIS CRM Recovery Outcome Action Activation Run", "recovery_outcome_action_activation_run", "Link", options=RECOVERY_OUTCOME_ACTION_ACTIVATION_RUN, reqd=1, in_list_view=1),
        make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import", in_list_view=1),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
        make_field("NDIS Financial Profile", "ndis_financial_profile", "Data"),

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
        make_field("Recovery Outcome Action Completion Owner", "recovery_outcome_action_completion_owner", "Link", options="User", in_list_view=1),
        make_field("Recovery Outcome Action Activation Owner", "recovery_outcome_action_activation_owner", "Link", options="User"),
        make_field("Completed By", "completed_by", "Link", options="User", read_only=1),
        make_field("Completed On", "completed_on", "Datetime", read_only=1),

        make_field("Recovery Outcome Action Completion Lines", "recovery_outcome_action_completion_lines_section", "Section Break"),
        make_field("Recovery Outcome Action Completion Lines", "recovery_outcome_action_completion_lines", "Table", options=RECOVERY_OUTCOME_ACTION_COMPLETION_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Recovery Outcome Action Completion Notes", "recovery_outcome_action_completion_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=RECOVERY_OUTCOME_ACTION_COMPLETION_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase50():
    deal_fields = [
        {
            "fieldname": "recovery_outcome_action_completion_section",
            "label": "NDIS Recovery Outcome Action Completion Run",
            "fieldtype": "Section Break",
            "insert_after": "recovery_outcome_action_activation_ready",
        },
        {
            "fieldname": "ndis_recovery_outcome_action_completion_run_required",
            "label": "Recovery Outcome Action Completion Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "recovery_outcome_action_completion_section",
        },
        {
            "fieldname": "ndis_recovery_outcome_action_completion_run",
            "label": "NDIS CRM Recovery Outcome Action Completion Run",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "ndis_recovery_outcome_action_completion_run_required",
        },
        {
            "fieldname": "recovery_outcome_action_completion_status",
            "label": "Recovery Outcome Action Completion Status",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "ndis_recovery_outcome_action_completion_run",
        },
        {
            "fieldname": "recovery_outcome_action_completion_ready",
            "label": "Recovery Outcome Action Completion Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "recovery_outcome_action_completion_status",
        },
    ]

    shared_fields = [
        {
            "fieldname": "recovery_outcome_action_completion_section",
            "label": "NDIS Recovery Outcome Action Completion Run",
            "fieldtype": "Section Break",
            "insert_after": "recovery_outcome_action_activation_ready",
        },
        {
            "fieldname": "ndis_recovery_outcome_action_completion_run",
            "label": "NDIS CRM Recovery Outcome Action Completion Run",
            "fieldtype": "Link",
            "options": RECOVERY_OUTCOME_ACTION_COMPLETION_RUN,
            "read_only": 1,
            "insert_after": "recovery_outcome_action_completion_section",
        },
        {
            "fieldname": "recovery_outcome_action_completion_status",
            "label": "Recovery Outcome Action Completion Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_recovery_outcome_action_completion_run",
        },
        {
            "fieldname": "recovery_outcome_action_completion_ready",
            "label": "Recovery Outcome Action Completion Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "recovery_outcome_action_completion_status",
        },
    ]

    custom_fields = {
        CRM_DEAL: deal_fields,
        HANDOVER: shared_fields,
        FINANCE_ONBOARDING: shared_fields,
        OPERATIONS_SETUP: shared_fields,
        SCHEDULE_DRAFT: shared_fields,
        ROSTER_REQUEST: shared_fields,
        SERVICE_FILE: shared_fields,
        SESSION_DRAFT: shared_fields,
        EVIDENCE_REVIEW: shared_fields,
        DOWNSTREAM_PREPARATION: shared_fields,
        BILLING_DRAFT: shared_fields,
        CLAIM_DRAFT: shared_fields,
        INVOICE_DRAFT: shared_fields,
        SALES_INVOICE_DRAFT_RUN: shared_fields,
        SALES_INVOICE_SUBMISSION_RUN: shared_fields,
        CLAIM_BATCH_DRAFT_RUN: shared_fields,
        CLAIM_BATCH_SUBMISSION_RUN: shared_fields,
        CLAIM_EXPORT_PREP_RUN: shared_fields,
        CLAIM_LODGEMENT_CONFIRMATION_RUN: shared_fields,
        REMITTANCE_IMPORT_PREP_RUN: shared_fields,
        ACTUAL_REMITTANCE_IMPORT_RUN: shared_fields,
        REMITTANCE_MATCHING_REVIEW_RUN: shared_fields,
        PAYMENT_ALLOCATION_PREP_RUN: shared_fields,
        PAYMENT_ENTRY_DRAFT_RUN: shared_fields,
        PAYMENT_ENTRY_SUBMISSION_RUN: shared_fields,
        REMITTANCE_IMPORT_FINALISATION_RUN: shared_fields,
        VARIANCE_REJECTION_REVIEW_RUN: shared_fields,
        WRITE_OFF_PREPARATION_RUN: shared_fields,
        WRITE_OFF_DRAFT_RUN: shared_fields,
        WRITE_OFF_JE_DRAFT_RUN: shared_fields,
        WRITE_OFF_JE_SUBMISSION_RUN: shared_fields,
        WRITE_OFF_FINALISATION_RUN: shared_fields,
        RECOVERY_PREPARATION_RUN: shared_fields,
        RECOVERY_CASE_DRAFT_RUN: shared_fields,
        RECOVERY_CASE_SUBMISSION_RUN: shared_fields,
        RECOVERY_FOLLOW_UP_PREPARATION_RUN: shared_fields,
        RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN: shared_fields,
        RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN: shared_fields,
        RECOVERY_COMMUNICATION_DRAFT_PREPARATION_RUN: shared_fields,
        RECOVERY_COMMUNICATION_DRAFT_CREATION_RUN: shared_fields,
        RECOVERY_COMMUNICATION_DISPATCH_RUN: shared_fields,
        RECOVERY_COMMUNICATION_OUTCOME_CAPTURE_RUN: shared_fields,
        RECOVERY_OUTCOME_ACTION_PREPARATION_RUN: shared_fields,
        RECOVERY_OUTCOME_ACTION_DRAFT_RUN: shared_fields,
        RECOVERY_OUTCOME_ACTION_ACTIVATION_RUN: shared_fields,
        INTAKE: shared_fields,
    }

    if doctype_exists(ATTENDANCE_DRAFT):
        custom_fields[ATTENDANCE_DRAFT] = shared_fields

    repair_partial_crm_deal_phase50_fields()
    safe_create_custom_fields(custom_fields)
    print("Created / updated Phase 50 recovery outcome action completion chain custom fields.")


def create_optional_action_target_custom_fields():
    fields = [
        {
            "fieldname": "ndis_crm_recovery_outcome_action_completion_section",
            "label": "NDIS CRM Recovery Outcome Action Completion Control",
            "fieldtype": "Section Break",
            "insert_after": "ndis_crm_action_activation_status",
        },
        {
            "fieldname": "ndis_crm_recovery_outcome_action_completion_run",
            "label": "NDIS CRM Recovery Outcome Action Completion Run",
            "fieldtype": "Link",
            "options": RECOVERY_OUTCOME_ACTION_COMPLETION_RUN,
            "read_only": 1,
            "insert_after": "ndis_crm_recovery_outcome_action_completion_section",
        },
        {
            "fieldname": "ndis_crm_recovery_outcome_action_completion_line",
            "label": "NDIS CRM Recovery Outcome Action Completion Line",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_crm_recovery_outcome_action_completion_run",
        },
        {
            "fieldname": "ndis_crm_action_completion_status",
            "label": "NDIS CRM Action Completion Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_crm_recovery_outcome_action_completion_line",
        },
    ]

    if doctype_exists(TODO):
        safe_create_custom_fields({TODO: fields})
        print("Created / updated optional ToDo Phase 50 completion marker fields.")
    else:
        print("ToDo DocType not found. Skipping optional ToDo completion marker fields.")

    if doctype_exists(TASK):
        safe_create_custom_fields({TASK: fields})
        print("Created / updated optional Task Phase 50 completion marker fields.")
    else:
        print("Task DocType not found. Skipping optional Task completion marker fields.")


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


def _phase50_deal_actions():
    return r'''
// NDIS CRM Phase 50 Deal Actions
{
  label: "Create Recovery Outcome Action Completion Run",
  onClick: () => {
    call("ndis_crm.phase50_recovery_outcome_action_completion.create_recovery_outcome_action_completion_run_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Recovery Outcome Action Completion Run Created" : "Existing Recovery Outcome Action Completion Run Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-recovery-outcome-action-completion-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Recovery Outcome Action Completion Run",
  onClick: () => {
    if (doc.ndis_recovery_outcome_action_completion_run) {
      window.open(`/app/ndis-crm-recovery-outcome-action-completion-run/${doc.ndis_recovery_outcome_action_completion_run}`, "_blank")
    } else {
      createToast({ title: "No Recovery Outcome Action Completion Run linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    try:
        from ndis_crm.setup.phase49_recovery_outcome_action_activation import _deal_script as phase49_deal_script

        script = phase49_deal_script()
    except Exception:
        script = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
    ]
  }
}
'''.strip()

    if "NDIS CRM Phase 50 Deal Actions" in script:
        return script

    return _append_before_last(script, "\n    ]", _phase50_deal_actions())


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

    activation_script = r'''
frappe.ui.form.on("NDIS CRM Recovery Outcome Action Activation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Recovery Outcome Action Completion Run"), function () {
            frappe.call({
                method: "ndis_crm.phase50_recovery_outcome_action_completion.create_recovery_outcome_action_completion_run_from_action_activation_run",
                args: { recovery_outcome_action_activation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating recovery outcome action completion run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Recovery Outcome Action Completion Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Recovery Outcome Action Completion Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_recovery_outcome_action_completion_run) {
            frm.add_custom_button(__("Open Recovery Outcome Action Completion Run"), function () {
                frappe.set_route("Form", "NDIS CRM Recovery Outcome Action Completion Run", frm.doc.ndis_recovery_outcome_action_completion_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Recovery Outcome Action Completion Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Completion Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase50_recovery_outcome_action_completion.generate_recovery_outcome_action_completion_lines",
                args: { recovery_outcome_action_completion_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating action completion lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Action completion lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Completion Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase50_recovery_outcome_action_completion.validate_recovery_outcome_action_completion_readiness",
                args: { recovery_outcome_action_completion_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating action completion readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Action completion readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Completion"), function () {
            frappe.call({
                method: "ndis_crm.phase50_recovery_outcome_action_completion.mark_ready_for_recovery_outcome_action_completion",
                args: { recovery_outcome_action_completion_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for action completion...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for action completion"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Completion Run"), function () {
            frappe.call({
                method: "ndis_crm.phase50_recovery_outcome_action_completion.approve_recovery_outcome_action_completion_run",
                args: { recovery_outcome_action_completion_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving action completion run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Action Completion Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Complete Actions"), function () {
            frappe.confirm(
                __("This completes CRM action records only by default, or existing Phase 49-released ToDo/Task records only when explicitly allowed. It will not create Communication, Email Queue, Event, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or Remittance Import."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase50_recovery_outcome_action_completion.complete_recovery_outcome_actions",
                        args: { recovery_outcome_action_completion_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Completing recovery outcome actions...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Action completion completed"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.recovery_outcome_action_activation_run) {
            frm.add_custom_button(__("Open Action Activation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Recovery Outcome Action Activation Run", frm.doc.recovery_outcome_action_activation_run);
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
            "NDIS CRM Recovery Outcome Action Activation Phase50 Actions",
            {
                "dt": RECOVERY_OUTCOME_ACTION_ACTIVATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": activation_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Recovery Outcome Action Completion Run Actions",
            {
                "dt": RECOVERY_OUTCOME_ACTION_COMPLETION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
