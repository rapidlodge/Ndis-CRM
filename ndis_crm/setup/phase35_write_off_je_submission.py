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
WRITE_OFF_JE_SUBMISSION_LINE = "NDIS CRM Write Off JE Submission Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"


def install():
    ensure_required_doctypes()
    create_write_off_je_submission_doctypes()
    create_custom_fields_phase35()
    create_journal_entry_custom_fields()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 35 Write Off Journal Entry Submission gate installed successfully.")


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
        WRITE_OFF_PREPARATION_RUN,
        WRITE_OFF_DRAFT_RUN,
        WRITE_OFF_JE_DRAFT_RUN,
        "Sales Invoice",
        "Payment Entry",
        "Journal Entry",
        "GL Entry",
        "NDIS Remittance Import",
        "NDIS Service Line",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 35 DocTypes: " + ", ".join(missing))

    print("Required Phase 35 DocTypes found.")


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


def create_write_off_je_submission_doctypes():
    create_write_off_je_submission_line()
    create_write_off_je_submission_run()


def create_write_off_je_submission_line():
    fields = [
        make_field("Source", "source_section", "Section Break"),
        make_field("Write Off JE Submission Source Key", "write_off_je_submission_source_key", "Data", read_only=1),

        make_field("Journal Entry", "journal_entry_section", "Section Break"),
        make_field("Journal Entry", "journal_entry", "Link", options="Journal Entry", in_list_view=1),
        make_field("Journal Entry Docstatus", "journal_entry_docstatus", "Int", read_only=1, in_list_view=1),
        make_field("Journal Entry Status", "journal_entry_status", "Data", read_only=1),
        make_field("Journal Entry Posting Date", "journal_entry_posting_date", "Date", read_only=1),
        make_field("Journal Entry Total Debit", "journal_entry_total_debit", "Currency", read_only=1),
        make_field("Journal Entry Total Credit", "journal_entry_total_credit", "Currency", read_only=1),
        make_field("GL Entry Count", "gl_entry_count", "Int", read_only=1),

        make_field("Source Write Off Draft", "source_write_off_draft_section", "Section Break"),
        make_field("Source Write Off Draft DocType", "source_write_off_draft_doctype", "Data", read_only=1),
        make_field("Source Write Off Draft Name", "source_write_off_draft_name", "Data", read_only=1),
        make_field("Source Write Off Draft Docstatus", "source_write_off_draft_docstatus", "Int", read_only=1),

        make_field("Document Links", "document_links_section", "Section Break"),
        make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import"),
        make_field("NDIS Remittance Import Docstatus", "ndis_remittance_import_docstatus", "Int", read_only=1),
        make_field("NDIS Remittance Import Status", "ndis_remittance_import_status", "Data", read_only=1),
        make_field("Payment Entry", "payment_entry", "Link", options="Payment Entry"),
        make_field("Payment Entry Docstatus", "payment_entry_docstatus", "Int", read_only=1),
        make_field("Payment Entry Status", "payment_entry_status", "Data", read_only=1),
        make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", in_list_view=1),
        make_field("Sales Invoice Docstatus", "sales_invoice_docstatus", "Int", read_only=1),
        make_field("Sales Invoice Status", "sales_invoice_status", "Data", read_only=1),
        make_field("Sales Invoice Outstanding Amount", "sales_invoice_outstanding_amount", "Currency", read_only=1),
        make_field("NDIS Claim Batch", "ndis_claim_batch", "Link", options="NDIS Claim Batch"),
        make_field("NDIS Claim Line", "ndis_claim_line", "Link", options="NDIS Claim Line"),

        make_field("Service Snapshot", "service_snapshot_section", "Section Break"),
        make_field("Service Line", "service_line", "Link", options="NDIS Service Line", in_list_view=1),
        make_field("Service Code", "service_code", "Data", read_only=1),
        make_field("Service Model", "service_model", "Data"),
        make_field("Service Date", "service_date", "Date"),
        make_field("Support Item", "support_item", "Data"),
        make_field("Finance Service Type", "finance_service_type", "Data"),
        make_field("NDIS Plan Budget", "plan_budget", "Data"),
        make_field("NDIS Service Booking", "service_booking", "Data"),
        make_field("Funding Source", "funding_source", "Data"),
        make_field("Default House", "default_house", "Data"),

        make_field("External References", "external_references_section", "Section Break"),
        make_field("External Lodgement Reference", "external_lodgement_reference", "Data"),
        make_field("External Batch Reference", "external_batch_reference", "Data"),
        make_field("External Line Reference", "external_line_reference", "Data"),
        make_field("Actual Payment Reference", "actual_payment_reference", "Data"),
        make_field("Actual Payment Date", "actual_payment_date", "Date"),

        make_field("Write Off Source", "write_off_source_section", "Section Break"),
        make_field("Review Category", "review_category", "Data", read_only=1),
        make_field("Recommended Resolution", "recommended_resolution", "Data", read_only=1),
        make_field("Matching Result", "matching_result", "Data", read_only=1),
        make_field("Allocation Type", "allocation_type", "Data", read_only=1),
        make_field("Claim Amount", "claim_amount", "Currency"),
        make_field("Expected Paid Amount", "expected_paid_amount", "Currency"),
        make_field("Actual Paid Amount", "actual_paid_amount", "Currency"),
        make_field("Actual Rejected Amount", "actual_rejected_amount", "Currency"),
        make_field("Variance Amount", "variance_amount", "Currency"),
        make_field("Short Paid Amount", "short_paid_amount", "Currency"),
        make_field("Rejected Amount", "rejected_amount", "Currency"),

        make_field("Write Off JE Values", "write_off_je_values_section", "Section Break"),
        make_field("Proposed Write Off Amount", "proposed_write_off_amount", "Currency", in_list_view=1),
        make_field("Write Off Reason", "write_off_reason", "Small Text"),
        make_field("Write Off Treatment", "write_off_treatment", "Data"),
        make_field("Write Off Basis", "write_off_basis", "Small Text"),
        make_field("Write Off Expense Account", "write_off_expense_account", "Link", options="Account", read_only=1),
        make_field("Receivable Account", "receivable_account", "Link", options="Account", read_only=1),
        make_field("Party Type", "party_type", "Data", read_only=1),
        make_field("Party", "party", "Link", options="Customer", read_only=1),
        make_field("Cost Center", "cost_center", "Link", options="Cost Center", read_only=1),

        make_field("Submission Controls", "submission_controls_section", "Section Break"),
        make_field("Write Off JE Submission Source Ready", "write_off_je_submission_source_ready", "Check", default="0"),
        make_field("Journal Entry Submission Review Complete", "journal_entry_submission_review_complete", "Check", default="0"),
        make_field("Journal Entry Submission Authorized", "journal_entry_submission_authorized", "Check", default="0"),
        make_field("Manual GL Authorized", "manual_gl_authorized", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Payment Entry Authorized", "payment_entry_authorized", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Write Off Submit Authorized", "write_off_submit_authorized", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Recovery Authorized", "recovery_authorized", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Adjustment Authorized", "adjustment_authorized", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Bank Reconciliation Authorized", "bank_reconciliation_authorized", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Write Off JE Submission Hold", "write_off_je_submission_hold", "Check", default="1", in_list_view=1),
        make_field("Write Off JE Submission Hold Reason", "write_off_je_submission_hold_reason", "Small Text"),

        make_field("Line Status", "line_status_section", "Section Break"),
        make_field("Line Ready for Journal Entry Submission", "line_ready_for_journal_entry_submission", "Check", default="0", in_list_view=1),
        make_field("Write Off JE Submission Line Status", "write_off_je_submission_line_status", "Select", options="Draft\nReady\nApproved\nJournal Entry Submitted\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=WRITE_OFF_JE_SUBMISSION_LINE,
        fields=fields,
        istable=1,
    )


def create_write_off_je_submission_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-WRITEOFF-JE-SUB-.YYYY.-.#####", default="NDIS-WRITEOFF-JE-SUB-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Journal Entry Submission\nJournal Entry Submission Run Approved\nJournal Entries Submitted\nReturned to JE Draft\nCancelled", default="Draft", in_list_view=1),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Write Off JE Submission Run Ready", "write_off_je_submission_run_ready", "Check", read_only=1, in_list_view=1),
        make_field("No Write Off JE Submission Candidate Found", "no_write_off_je_submission_candidate_found", "Check", default="0", read_only=1),
        make_field("Journal Entry Submission Allowed", "journal_entry_submission_allowed", "Check", default="0"),
        make_field("Manual GL Creation Allowed", "manual_gl_creation_allowed", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Payment Entry Creation Allowed", "payment_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Write Off Submit Allowed", "write_off_submit_allowed", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Recovery Creation Allowed", "recovery_creation_allowed", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Adjustment Creation Allowed", "adjustment_creation_allowed", "Check", default="0", description="Blocked in Phase 35."),
        make_field("Bank Reconciliation Allowed", "bank_reconciliation_allowed", "Check", default="0", description="Blocked in Phase 35."),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Write Off JE Submission Line Count", "write_off_je_submission_line_count", "Int", read_only=1),
        make_field("Write Off JE Submission Amount Total", "write_off_je_submission_amount_total", "Currency", read_only=1),
        make_field("Write Off JE Submission Ready Count", "write_off_je_submission_ready_count", "Int", read_only=1),
        make_field("Write Off JE Submission Hold Count", "write_off_je_submission_hold_count", "Int", read_only=1),
        make_field("Draft Journal Entry Count", "draft_journal_entry_count", "Int", read_only=1),
        make_field("Submitted Journal Entry Count", "submitted_journal_entry_count", "Int", read_only=1),
        make_field("Standard GL Entry Count", "standard_gl_entry_count", "Int", read_only=1),
        make_field("Blocked Manual GL Count", "blocked_manual_gl_count", "Int", read_only=1),
        make_field("Blocked Payment Entry Count", "blocked_payment_entry_count", "Int", read_only=1),
        make_field("Blocked Write Off Submit Count", "blocked_write_off_submit_count", "Int", read_only=1),
        make_field("Blocked Recovery Authorization Count", "blocked_recovery_authorization_count", "Int", read_only=1),
        make_field("Blocked Adjustment Authorization Count", "blocked_adjustment_authorization_count", "Int", read_only=1),
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
        make_field("NDIS CRM Write Off JE Draft Run", "write_off_je_draft_run", "Link", options=WRITE_OFF_JE_DRAFT_RUN, reqd=1, in_list_view=1),
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
        make_field("Write Off JE Submission Owner", "write_off_je_submission_owner", "Link", options="User", in_list_view=1),
        make_field("Write Off JE Draft Owner", "write_off_je_draft_owner", "Link", options="User"),
        make_field("Submitted By", "submitted_by", "Link", options="User", read_only=1),
        make_field("Submitted On", "submitted_on", "Datetime", read_only=1),

        make_field("Write Off JE Submission Lines", "write_off_je_submission_lines_section", "Section Break"),
        make_field("Write Off JE Submission Lines", "write_off_je_submission_lines", "Table", options=WRITE_OFF_JE_SUBMISSION_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Write Off JE Submission Notes", "write_off_je_submission_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=WRITE_OFF_JE_SUBMISSION_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase35():
    deal_fields = [
        {
            "fieldname": "write_off_je_submission_section",
            "label": "NDIS Write Off JE Submission Run",
            "fieldtype": "Section Break",
            "insert_after": "write_off_je_draft_ready",
        },
        {
            "fieldname": "ndis_write_off_je_submission_run_required",
            "label": "Write Off JE Submission Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "write_off_je_submission_section",
            "description": "Optional guard only. Write-off JE submission normally happens after JE draft creation.",
        },
        {
            "fieldname": "ndis_write_off_je_submission_run",
            "label": "NDIS CRM Write Off JE Submission Run",
            "fieldtype": "Link",
            "options": WRITE_OFF_JE_SUBMISSION_RUN,
            "read_only": 1,
            "insert_after": "ndis_write_off_je_submission_run_required",
        },
        {
            "fieldname": "write_off_je_submission_status",
            "label": "Write Off JE Submission Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_write_off_je_submission_run",
        },
        {
            "fieldname": "write_off_je_submission_ready",
            "label": "Write Off JE Submission Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "write_off_je_submission_status",
        },
    ]

    shared_fields = [
        {
            "fieldname": "write_off_je_submission_section",
            "label": "NDIS Write Off JE Submission Run",
            "fieldtype": "Section Break",
            "insert_after": "write_off_je_draft_ready",
        },
        {
            "fieldname": "ndis_write_off_je_submission_run",
            "label": "NDIS CRM Write Off JE Submission Run",
            "fieldtype": "Link",
            "options": WRITE_OFF_JE_SUBMISSION_RUN,
            "read_only": 1,
            "insert_after": "write_off_je_submission_section",
        },
        {
            "fieldname": "write_off_je_submission_status",
            "label": "Write Off JE Submission Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_write_off_je_submission_run",
        },
        {
            "fieldname": "write_off_je_submission_ready",
            "label": "Write Off JE Submission Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "write_off_je_submission_status",
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
        INTAKE: shared_fields,
    }

    if doctype_exists(ATTENDANCE_DRAFT):
        custom_fields[ATTENDANCE_DRAFT] = shared_fields

    create_custom_fields(custom_fields, update=True)
    print("Created / updated Phase 35 write-off JE submission chain custom fields.")


def create_journal_entry_custom_fields():
    custom_fields = {
        "Journal Entry": [
            {
                "fieldname": "ndis_crm_write_off_je_submission_section",
                "label": "NDIS CRM Write Off JE Submission Control",
                "fieldtype": "Section Break",
                "insert_after": "ndis_crm_submit_blocked",
            },
            {
                "fieldname": "ndis_crm_write_off_je_submission_run",
                "label": "NDIS CRM Write Off JE Submission Run",
                "fieldtype": "Link",
                "options": WRITE_OFF_JE_SUBMISSION_RUN,
                "read_only": 1,
                "insert_after": "ndis_crm_write_off_je_submission_section",
            },
            {
                "fieldname": "ndis_crm_write_off_je_submission_line",
                "label": "NDIS CRM Write Off JE Submission Line",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "ndis_crm_write_off_je_submission_run",
            },
            {
                "fieldname": "ndis_crm_submission_gate_status",
                "label": "NDIS CRM Submission Gate Status",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "ndis_crm_write_off_je_submission_line",
            },
        ]
    }

    create_custom_fields(custom_fields, update=True)
    print("Created / updated Phase 35 Journal Entry submission guard custom fields.")


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

    prefix = script[:idx].rstrip()
    suffix = script[idx:]

    if not prefix.endswith("[") and not prefix.endswith(","):
        insert = ",\n" + insert.strip()

    return prefix + insert + suffix


def _phase35_deal_actions():
    return r'''
// NDIS CRM Phase 35 Deal Actions
{
  label: "Create Write Off JE Submission Run",
  onClick: () => {
    call("ndis_crm.phase35_write_off_je_submission.create_write_off_je_submission_run_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Write Off JE Submission Run Created" : "Existing Write Off JE Submission Run Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-write-off-je-submission-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Write Off JE Submission Run",
  onClick: () => {
    if (doc.ndis_write_off_je_submission_run) {
      window.open(`/app/ndis-crm-write-off-je-submission-run/${doc.ndis_write_off_je_submission_run}`, "_blank")
    } else {
      createToast({ title: "No Write Off JE Submission Run linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    try:
        from ndis_crm.setup.phase34_write_off_je_draft import _deal_script as phase34_deal_script
        script = phase34_deal_script()
    except Exception:
        script = '''
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
    ]
  }
}
'''.strip()

    if "NDIS CRM Phase 35 Deal Actions" in script:
        return script

    return _append_before_last(script, "\n    ]", _phase35_deal_actions())


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

    je_draft_script = r'''
frappe.ui.form.on("NDIS CRM Write Off JE Draft Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Write Off JE Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase35_write_off_je_submission.create_write_off_je_submission_run_from_je_draft_run",
                args: { write_off_je_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating write-off JE submission run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Write Off JE Submission Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Write Off JE Submission Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_write_off_je_submission_run) {
            frm.add_custom_button(__("Open Write Off JE Submission Run"), function () {
                frappe.set_route("Form", "NDIS CRM Write Off JE Submission Run", frm.doc.ndis_write_off_je_submission_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Write Off JE Submission Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Submission Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase35_write_off_je_submission.generate_write_off_je_submission_lines",
                args: { write_off_je_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating write-off JE submission lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Submission Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase35_write_off_je_submission.validate_write_off_je_submission_readiness",
                args: { write_off_je_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating write-off JE submission readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Submission readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Submission"), function () {
            frappe.call({
                method: "ndis_crm.phase35_write_off_je_submission.mark_ready_for_write_off_je_submission",
                args: { write_off_je_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for Journal Entry submission...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Journal Entry submission"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase35_write_off_je_submission.approve_write_off_je_submission_run",
                args: { write_off_je_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving Journal Entry submission run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Write Off JE Submission Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Submit Journal Entries"), function () {
            frappe.confirm(
                __("This submits existing linked draft Journal Entries only. Standard ERPNext GL Entries may be created by Journal Entry submit. It will not create manual GL, Payment Entry, recovery, adjustment, bank reconciliation, Sales Invoice, Claim Batch, Claim Line, or Remittance Import."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase35_write_off_je_submission.submit_journal_entries",
                        args: { write_off_je_submission_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Submitting Journal Entries...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Journal Entries submitted"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.write_off_je_draft_run) {
            frm.add_custom_button(__("Open Write Off JE Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Write Off JE Draft Run", frm.doc.write_off_je_draft_run);
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
            "NDIS CRM Write Off JE Draft Phase35 Actions",
            {
                "dt": WRITE_OFF_JE_DRAFT_RUN,
                "view": "Form",
                "enabled": 1,
                "script": je_draft_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Write Off JE Submission Run Actions",
            {
                "dt": WRITE_OFF_JE_SUBMISSION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )