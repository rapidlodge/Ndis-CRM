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
RECOVERY_FOLLOW_UP_TASK_ACTIVATION_LINE = "NDIS CRM Recovery Follow Up Task Activation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
TODO = "ToDo"
TASK = "Task"


def install():
    ensure_required_doctypes()
    create_recovery_follow_up_task_activation_doctypes()
    create_custom_fields_phase42()
    create_optional_todo_task_custom_fields()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 42 Recovery Follow Up Task Activation gate installed successfully.")


def doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


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
        "Sales Invoice",
        "Payment Entry",
        "Journal Entry",
        "GL Entry",
        "NDIS Remittance Import",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 42 DocTypes: " + ", ".join(missing))

    print("Required Phase 42 DocTypes found.")


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


def create_recovery_follow_up_task_activation_doctypes():
    create_recovery_follow_up_task_activation_line()
    create_recovery_follow_up_task_activation_run()


def create_recovery_follow_up_task_activation_line():
    target_todo_field = make_field("Target ToDo", "target_todo", "Link", options="ToDo", read_only=1) if doctype_exists(TODO) else make_field("Target ToDo", "target_todo", "Data", read_only=1)
    target_task_field = make_field("Target Task", "target_task", "Link", options="Task", read_only=1) if doctype_exists(TASK) else make_field("Target Task", "target_task", "Data", read_only=1)

    fields = [
        make_field("Source", "source_section", "Section Break"),
        make_field("Recovery Follow Up Task Activation Source Key", "recovery_follow_up_task_activation_source_key", "Data", read_only=1),

        make_field("Task Targets", "task_targets_section", "Section Break"),
        make_field("Target Task Mode Snapshot", "target_task_mode_snapshot", "Data", read_only=1),
        target_todo_field,
        make_field("Target ToDo Status", "target_todo_status", "Data", read_only=1),
        target_task_field,
        make_field("Target Task Status", "target_task_status", "Data", read_only=1),

        make_field("Target Recovery Case", "target_case_section", "Section Break"),
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
        make_field("Recovery Route", "recovery_route", "Data", in_list_view=1),
        make_field("Recovery Reason", "recovery_reason", "Small Text"),
        make_field("Recovery Party Type", "recovery_party_type", "Data", default="Customer"),
        make_field("Recovery Party", "recovery_party", "Link", options="Customer"),
        make_field("Recovery Contact Name", "recovery_contact_name", "Data"),
        make_field("Recovery Contact Email", "recovery_contact_email", "Data"),
        make_field("Recovery Due Date", "recovery_due_date", "Date"),

        make_field("Follow Up Plan", "follow_up_plan_section", "Section Break"),
        make_field("Follow Up Action Type", "follow_up_action_type", "Data", in_list_view=1),
        make_field("Follow Up Priority", "follow_up_priority", "Data", in_list_view=1),
        make_field("Follow Up Owner", "follow_up_owner", "Link", options="User", in_list_view=1),
        make_field("Follow Up Due Date", "follow_up_due_date", "Date", in_list_view=1),
        make_field("Follow Up Channel", "follow_up_channel", "Data"),
        make_field("Follow Up Instruction", "follow_up_instruction", "Small Text"),
        make_field("Follow Up Message Draft", "follow_up_message_draft", "Small Text"),
        make_field("Task Subject", "task_subject", "Data", in_list_view=1),
        make_field("Task Description", "task_description", "Long Text"),
        make_field("Task Reference DocType", "task_reference_doctype", "Data"),
        make_field("Task Reference Name", "task_reference_name", "Data"),

        make_field("Activation Controls", "activation_controls_section", "Section Break"),
        make_field("Recovery Follow Up Task Activation Source Ready", "recovery_follow_up_task_activation_source_ready", "Check", default="0"),
        make_field("Task Activation Review Complete", "task_activation_review_complete", "Check", default="0"),
        make_field("Task Activation Authorized", "task_activation_authorized", "Check", default="0"),
        make_field("Task Completion Authorized", "task_completion_authorized", "Check", default="0"),

        make_field("Event Creation Authorized", "event_creation_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Email Creation Authorized", "email_creation_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Journal Entry Authorized", "journal_entry_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Manual GL Authorized", "manual_gl_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Payment Entry Authorized", "payment_entry_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Sales Invoice Authorized", "sales_invoice_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Adjustment Authorized", "adjustment_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Bank Reconciliation Authorized", "bank_reconciliation_authorized", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Recovery Follow Up Task Activation Hold", "recovery_follow_up_task_activation_hold", "Check", default="1", in_list_view=1),
        make_field("Recovery Follow Up Task Activation Hold Reason", "recovery_follow_up_task_activation_hold_reason", "Small Text"),

        make_field("Line Status", "line_status_section", "Section Break"),
        make_field("Line Ready for Recovery Follow Up Task Activation", "line_ready_for_recovery_follow_up_task_activation", "Check", default="0", in_list_view=1),
        make_field("Recovery Follow Up Task Activation Line Status", "recovery_follow_up_task_activation_line_status", "Select", options="Draft\nReady\nApproved\nCRM Task Activated\nToDo Activated\nTask Activated\nToDo and Task Activated\nToDo Completed\nTask Completed\nToDo and Task Completed\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=RECOVERY_FOLLOW_UP_TASK_ACTIVATION_LINE,
        fields=fields,
        istable=1,
    )


def create_recovery_follow_up_task_activation_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-RECOVERY-FOLLOWUP-TASK-ACT-.YYYY.-.#####", default="NDIS-RECOVERY-FOLLOWUP-TASK-ACT-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Follow Up Task Activation\nFollow Up Task Activation Run Approved\nFollow Up Tasks Activated\nFollow Up Tasks Completed\nReturned to Task Draft\nCancelled", default="Draft", in_list_view=1),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Recovery Follow Up Task Activation Run Ready", "recovery_follow_up_task_activation_run_ready", "Check", read_only=1, in_list_view=1),
        make_field("No Follow Up Task Activation Candidate Found", "no_follow_up_task_activation_candidate_found", "Check", default="0", read_only=1),

        make_field("Target Task Action Mode", "target_task_action_mode", "Select", options="Activate Tasks Only\nComplete Tasks If Authorized", default="Activate Tasks Only"),
        make_field("Follow Up Task Activation Allowed", "follow_up_task_activation_allowed", "Check", default="0"),
        make_field("Follow Up Task Completion Allowed", "follow_up_task_completion_allowed", "Check", default="0"),

        make_field("Event Creation Allowed", "event_creation_allowed", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Email Creation Allowed", "email_creation_allowed", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Journal Entry Creation Allowed", "journal_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Manual GL Creation Allowed", "manual_gl_creation_allowed", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Payment Entry Creation Allowed", "payment_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Adjustment Creation Allowed", "adjustment_creation_allowed", "Check", default="0", description="Blocked in Phase 42."),
        make_field("Bank Reconciliation Allowed", "bank_reconciliation_allowed", "Check", default="0", description="Blocked in Phase 42."),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Recovery Follow Up Task Activation Line Count", "recovery_follow_up_task_activation_line_count", "Int", read_only=1),
        make_field("Recovery Follow Up Task Activation Amount Total", "recovery_follow_up_task_activation_amount_total", "Currency", read_only=1),
        make_field("Recovery Follow Up Task Activation Ready Count", "recovery_follow_up_task_activation_ready_count", "Int", read_only=1),
        make_field("Recovery Follow Up Task Activation Hold Count", "recovery_follow_up_task_activation_hold_count", "Int", read_only=1),
        make_field("CRM Task Activated Count", "crm_task_activated_count", "Int", read_only=1),
        make_field("ToDo Activated Count", "todo_activated_count", "Int", read_only=1),
        make_field("Task Activated Count", "task_activated_count", "Int", read_only=1),
        make_field("ToDo Completed Count", "todo_completed_count", "Int", read_only=1),
        make_field("Task Completed Count", "task_completed_count", "Int", read_only=1),
        make_field("Blocked Event Count", "blocked_event_count", "Int", read_only=1),
        make_field("Blocked Email Count", "blocked_email_count", "Int", read_only=1),
        make_field("Blocked Journal Entry Count", "blocked_journal_entry_count", "Int", read_only=1),
        make_field("Blocked Manual GL Count", "blocked_manual_gl_count", "Int", read_only=1),
        make_field("Blocked Payment Entry Count", "blocked_payment_entry_count", "Int", read_only=1),
        make_field("Blocked Sales Invoice Count", "blocked_sales_invoice_count", "Int", read_only=1),
        make_field("Blocked Adjustment Count", "blocked_adjustment_count", "Int", read_only=1),
        make_field("Blocked Bank Reconciliation Count", "blocked_bank_reconciliation_count", "Int", read_only=1),

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
        make_field("NDIS CRM Recovery Follow Up Task Draft Run", "recovery_follow_up_task_draft_run", "Link", options=RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN, reqd=1, in_list_view=1),
        make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import", in_list_view=1),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
    ]

    if doctype_exists(FINANCE_PROFILE):
        fields.append(make_field("NDIS Financial Profile", "ndis_financial_profile", "Link", options=FINANCE_PROFILE))
    else:
        fields.append(make_field("NDIS Financial Profile", "ndis_financial_profile", "Data"))

    fields += [
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
        make_field("Recovery Follow Up Task Activation Owner", "recovery_follow_up_task_activation_owner", "Link", options="User", in_list_view=1),
        make_field("Recovery Follow Up Task Draft Owner", "recovery_follow_up_task_draft_owner", "Link", options="User"),
        make_field("Activated By", "activated_by", "Link", options="User", read_only=1),
        make_field("Activated On", "activated_on", "Datetime", read_only=1),

        make_field("Recovery Follow Up Task Activation Lines", "recovery_follow_up_task_activation_lines_section", "Section Break"),
        make_field("Recovery Follow Up Task Activation Lines", "recovery_follow_up_task_activation_lines", "Table", options=RECOVERY_FOLLOW_UP_TASK_ACTIVATION_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Recovery Follow Up Task Activation Notes", "recovery_follow_up_task_activation_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase42():
    # CRM Deal uses Small Text for run/status fields to avoid MariaDB row-size pressure.
    deal_fields = [
        {
            "fieldname": "recovery_follow_up_task_activation_section",
            "label": "NDIS Recovery Follow Up Task Activation Run",
            "fieldtype": "Section Break",
            "insert_after": "recovery_follow_up_task_draft_ready",
        },
        {
            "fieldname": "ndis_recovery_follow_up_task_activation_run_required",
            "label": "Recovery Follow Up Task Activation Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "recovery_follow_up_task_activation_section",
            "description": "Optional guard only. Task activation normally happens after recovery follow-up task draft.",
        },
        {
            "fieldname": "ndis_recovery_follow_up_task_activation_run",
            "label": "NDIS CRM Recovery Follow Up Task Activation Run",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "ndis_recovery_follow_up_task_activation_run_required",
        },
        {
            "fieldname": "recovery_follow_up_task_activation_status",
            "label": "Recovery Follow Up Task Activation Status",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "ndis_recovery_follow_up_task_activation_run",
        },
        {
            "fieldname": "recovery_follow_up_task_activation_ready",
            "label": "Recovery Follow Up Task Activation Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "recovery_follow_up_task_activation_status",
        },
    ]

    shared_fields = [
        {
            "fieldname": "recovery_follow_up_task_activation_section",
            "label": "NDIS Recovery Follow Up Task Activation Run",
            "fieldtype": "Section Break",
            "insert_after": "recovery_follow_up_task_draft_ready",
        },
        {
            "fieldname": "ndis_recovery_follow_up_task_activation_run",
            "label": "NDIS CRM Recovery Follow Up Task Activation Run",
            "fieldtype": "Link",
            "options": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
            "read_only": 1,
            "insert_after": "recovery_follow_up_task_activation_section",
        },
        {
            "fieldname": "recovery_follow_up_task_activation_status",
            "label": "Recovery Follow Up Task Activation Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_recovery_follow_up_task_activation_run",
        },
        {
            "fieldname": "recovery_follow_up_task_activation_ready",
            "label": "Recovery Follow Up Task Activation Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "recovery_follow_up_task_activation_status",
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
        INTAKE: shared_fields,
    }

    if doctype_exists(ATTENDANCE_DRAFT):
        custom_fields[ATTENDANCE_DRAFT] = shared_fields

    repair_partial_crm_deal_phase42_fields()
    create_custom_fields(custom_fields, update=True)
    print("Created / updated Phase 42 recovery follow-up task activation chain custom fields.")


def repair_partial_crm_deal_phase42_fields():
    for fieldname in [
        "ndis_recovery_follow_up_task_activation_run",
        "recovery_follow_up_task_activation_status",
    ]:
        name = frappe.db.get_value("Custom Field", {"dt": CRM_DEAL, "fieldname": fieldname}, "name")
        if not name or frappe.db.has_column(CRM_DEAL, fieldname):
            continue

        frappe.db.set_value(
            "Custom Field",
            name,
            {
                "fieldtype": "Small Text",
                "options": None,
            },
            update_modified=False,
        )


def create_optional_todo_task_custom_fields():
    optional_fields = [
        {
            "fieldname": "ndis_crm_recovery_follow_up_task_activation_section",
            "label": "NDIS CRM Recovery Follow Up Task Activation Control",
            "fieldtype": "Section Break",
            "insert_after": "ndis_crm_completion_blocked",
        },
        {
            "fieldname": "ndis_crm_recovery_follow_up_task_activation_run",
            "label": "NDIS CRM Recovery Follow Up Task Activation Run",
            "fieldtype": "Link",
            "options": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
            "read_only": 1,
            "insert_after": "ndis_crm_recovery_follow_up_task_activation_section",
        },
        {
            "fieldname": "ndis_crm_recovery_follow_up_task_activation_line",
            "label": "NDIS CRM Recovery Follow Up Task Activation Line",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_crm_recovery_follow_up_task_activation_run",
        },
        {
            "fieldname": "ndis_crm_task_activation_status",
            "label": "NDIS CRM Task Activation Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_crm_recovery_follow_up_task_activation_line",
        },
    ]

    custom_fields = {}

    if doctype_exists(TODO):
        custom_fields[TODO] = optional_fields

    if doctype_exists(TASK):
        custom_fields[TASK] = optional_fields

    if custom_fields:
        create_custom_fields(custom_fields, update=True)
        print("Created / updated optional ToDo/Task Phase 42 custom fields.")
    else:
        print("ToDo/Task DocTypes not found. Skipping optional Phase 42 target custom fields.")


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

    if not prefix.endswith("[") and not prefix.endswith(","):
        insert = ",\n" + insert.strip()

    return prefix + insert + suffix


def _phase42_deal_actions():
    return r'''
// NDIS CRM Phase 42 Deal Actions
{
  label: "Create Recovery Follow Up Task Activation Run",
  onClick: () => {
    call("ndis_crm.phase42_recovery_follow_up_task_activation.create_recovery_follow_up_task_activation_run_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Recovery Follow Up Task Activation Run Created" : "Existing Recovery Follow Up Task Activation Run Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-recovery-follow-up-task-activation-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Recovery Follow Up Task Activation Run",
  onClick: () => {
    if (doc.ndis_recovery_follow_up_task_activation_run) {
      window.open(`/app/ndis-crm-recovery-follow-up-task-activation-run/${doc.ndis_recovery_follow_up_task_activation_run}`, "_blank")
    } else {
      createToast({ title: "No Recovery Follow Up Task Activation Run linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    try:
        from ndis_crm.setup.phase41_recovery_follow_up_task_draft import _deal_script as phase41_deal_script
        script = phase41_deal_script()
    except Exception:
        script = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
    ]
  }
}
'''.strip()

    if "NDIS CRM Phase 42 Deal Actions" in script:
        return script

    return _append_before_last(script, "\n    ]", _phase42_deal_actions())


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

    draft_script = r'''
frappe.ui.form.on("NDIS CRM Recovery Follow Up Task Draft Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Recovery Follow Up Task Activation Run"), function () {
            frappe.call({
                method: "ndis_crm.phase42_recovery_follow_up_task_activation.create_recovery_follow_up_task_activation_run_from_task_draft_run",
                args: { recovery_follow_up_task_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating recovery follow-up task activation run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Recovery Follow Up Task Activation Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Recovery Follow Up Task Activation Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_recovery_follow_up_task_activation_run) {
            frm.add_custom_button(__("Open Recovery Follow Up Task Activation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Recovery Follow Up Task Activation Run", frm.doc.ndis_recovery_follow_up_task_activation_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Recovery Follow Up Task Activation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Activation Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase42_recovery_follow_up_task_activation.generate_recovery_follow_up_task_activation_lines",
                args: { recovery_follow_up_task_activation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating recovery follow-up task activation lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Activation lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Activation Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase42_recovery_follow_up_task_activation.validate_recovery_follow_up_task_activation_readiness",
                args: { recovery_follow_up_task_activation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating activation readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Activation readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Activation"), function () {
            frappe.call({
                method: "ndis_crm.phase42_recovery_follow_up_task_activation.mark_ready_for_recovery_follow_up_task_activation",
                args: { recovery_follow_up_task_activation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for activation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for task activation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Activation Run"), function () {
            frappe.call({
                method: "ndis_crm.phase42_recovery_follow_up_task_activation.approve_recovery_follow_up_task_activation_run",
                args: { recovery_follow_up_task_activation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving activation run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Activation Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Activate / Complete Follow Up Tasks"), function () {
            frappe.confirm(
                __("This releases or completes existing Phase 41 ToDo/Task drafts only. It will not create ToDo, Task, Event, Email/Communication, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or Remittance Import."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase42_recovery_follow_up_task_activation.activate_or_complete_follow_up_tasks",
                        args: { recovery_follow_up_task_activation_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Activating / completing follow-up tasks...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Follow-up tasks activated / completed"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.recovery_follow_up_task_draft_run) {
            frm.add_custom_button(__("Open Follow Up Task Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Recovery Follow Up Task Draft Run", frm.doc.recovery_follow_up_task_draft_run);
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
            "NDIS CRM Recovery Follow Up Task Draft Phase42 Actions",
            {
                "dt": RECOVERY_FOLLOW_UP_TASK_DRAFT_RUN,
                "view": "Form",
                "enabled": 1,
                "script": draft_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Recovery Follow Up Task Activation Run Actions",
            {
                "dt": RECOVERY_FOLLOW_UP_TASK_ACTIVATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )
