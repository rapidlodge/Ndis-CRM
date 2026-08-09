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
WRITE_OFF_DRAFT_LINE = "NDIS CRM Write Off Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
NDIS_WRITE_OFF = "NDIS Write Off"


def install():
    ensure_required_doctypes()
    create_write_off_draft_doctypes()
    create_custom_fields_phase33()
    create_optional_ndis_write_off_custom_fields()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 33 Write Off Draft gate installed successfully.")


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
        "Sales Invoice",
        "Payment Entry",
        "NDIS Remittance Import",
        "NDIS Service Line",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 33 DocTypes: " + ", ".join(missing))

    print("Required Phase 33 DocTypes found.")


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


def create_write_off_draft_doctypes():
    create_write_off_draft_line()
    create_write_off_draft_run()


def create_write_off_draft_line():
    fields = [
        make_field("Source", "source_section", "Section Break"),
        make_field("Write Off Draft Source Key", "write_off_draft_source_key", "Data", read_only=1),
        make_field("Target Draft DocType", "target_draft_doctype", "Data", read_only=1),
        make_field("Target Draft Name", "target_draft_name", "Data", read_only=1),
        make_field("Target Draft Docstatus", "target_draft_docstatus", "Int", read_only=1),

        make_field("Document Links", "document_links_section", "Section Break"),
        make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import", in_list_view=1),
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

        make_field("Write Off Draft", "write_off_draft_section", "Section Break"),
        make_field("Proposed Write Off Amount", "proposed_write_off_amount", "Currency", in_list_view=1),
        make_field("Write Off Reason", "write_off_reason", "Small Text"),
        make_field("Write Off Treatment", "write_off_treatment", "Data"),
        make_field("Write Off Basis", "write_off_basis", "Small Text"),
        make_field("Target Draft Mode", "target_draft_mode", "Data", read_only=1),

        make_field("Draft Controls", "draft_controls_section", "Section Break"),
        make_field("Write Off Draft Source Ready", "write_off_draft_source_ready", "Check", default="0"),
        make_field("Write Off Draft Review Complete", "write_off_draft_review_complete", "Check", default="0"),
        make_field("Write Off Draft Authorized", "write_off_draft_authorized", "Check", default="0"),
        make_field("Write Off Submit Authorized", "write_off_submit_authorized", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Journal Entry Authorized", "journal_entry_authorized", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Manual GL Authorized", "manual_gl_authorized", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Recovery Authorized", "recovery_authorized", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Adjustment Authorized", "adjustment_authorized", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Bank Reconciliation Authorized", "bank_reconciliation_authorized", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Write Off Draft Hold", "write_off_draft_hold", "Check", default="1", in_list_view=1),
        make_field("Write Off Draft Hold Reason", "write_off_draft_hold_reason", "Small Text"),

        make_field("Line Status", "line_status_section", "Section Break"),
        make_field("Line Ready for Write Off Draft", "line_ready_for_write_off_draft", "Check", default="0", in_list_view=1),
        make_field("Write Off Draft Line Status", "write_off_draft_line_status", "Select", options="Draft\nReady\nApproved\nCRM Write Off Draft Prepared\nExternal Write Off Draft Created\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=WRITE_OFF_DRAFT_LINE,
        fields=fields,
        istable=1,
    )


def create_write_off_draft_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-WRITEOFF-DRAFT-.YYYY.-.#####", default="NDIS-WRITEOFF-DRAFT-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Write Off Draft Creation\nWrite Off Draft Run Approved\nWrite Off Drafts Created\nReturned to Write Off Preparation\nCancelled", default="Draft", in_list_view=1),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Write Off Draft Run Ready", "write_off_draft_run_ready", "Check", read_only=1, in_list_view=1),
        make_field("No Write Off Draft Candidate Found", "no_write_off_draft_candidate_found", "Check", default="0", read_only=1),
        make_field("Target Draft Mode", "target_draft_mode", "Select", options="CRM Draft Only\nNDIS Write Off Draft If Available", default="CRM Draft Only"),
        make_field("Optional NDIS Write Off DocType Available", "optional_ndis_write_off_doctype_available", "Check", read_only=1),
        make_field("Write Off Draft Creation Allowed", "write_off_draft_creation_allowed", "Check", default="0"),
        make_field("External Write Off Draft Creation Allowed", "external_write_off_draft_creation_allowed", "Check", default="0", description="Only used when Target Draft Mode is NDIS Write Off Draft If Available."),
        make_field("Write Off Submit Allowed", "write_off_submit_allowed", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Journal Entry Creation Allowed", "journal_entry_creation_allowed", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Manual GL Creation Allowed", "manual_gl_creation_allowed", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Recovery Creation Allowed", "recovery_creation_allowed", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Adjustment Creation Allowed", "adjustment_creation_allowed", "Check", default="0", description="Blocked in Phase 33."),
        make_field("Bank Reconciliation Allowed", "bank_reconciliation_allowed", "Check", default="0", description="Blocked in Phase 33."),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Write Off Draft Line Count", "write_off_draft_line_count", "Int", read_only=1),
        make_field("Write Off Draft Amount Total", "write_off_draft_amount_total", "Currency", read_only=1),
        make_field("Write Off Draft Ready Count", "write_off_draft_ready_count", "Int", read_only=1),
        make_field("Write Off Draft Hold Count", "write_off_draft_hold_count", "Int", read_only=1),
        make_field("CRM Write Off Draft Count", "crm_write_off_draft_count", "Int", read_only=1),
        make_field("External Write Off Draft Count", "external_write_off_draft_count", "Int", read_only=1),
        make_field("Blocked Write Off Submit Count", "blocked_write_off_submit_count", "Int", read_only=1),
        make_field("Blocked Journal Entry Count", "blocked_journal_entry_count", "Int", read_only=1),
        make_field("Blocked Manual GL Count", "blocked_manual_gl_count", "Int", read_only=1),
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
        make_field("NDIS CRM Write Off Preparation Run", "write_off_preparation_run", "Link", options=WRITE_OFF_PREPARATION_RUN, reqd=1, in_list_view=1),
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
        make_field("Write Off Draft Owner", "write_off_draft_owner", "Link", options="User", in_list_view=1),
        make_field("Write Off Preparation Owner", "write_off_preparation_owner", "Link", options="User"),
        make_field("Drafted By", "drafted_by", "Link", options="User", read_only=1),
        make_field("Drafted On", "drafted_on", "Datetime", read_only=1),

        make_field("Write Off Draft Lines", "write_off_draft_lines_section", "Section Break"),
        make_field("Write Off Draft Lines", "write_off_draft_lines", "Table", options=WRITE_OFF_DRAFT_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Write Off Draft Notes", "write_off_draft_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=WRITE_OFF_DRAFT_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase33():
    deal_fields = [
        {
            "fieldname": "write_off_draft_section",
            "label": "NDIS Write Off Draft Run",
            "fieldtype": "Section Break",
            "insert_after": "write_off_preparation_ready",
        },
        {
            "fieldname": "ndis_write_off_draft_run_required",
            "label": "Write Off Draft Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "write_off_draft_section",
            "description": "Optional guard only. Write-off draft normally happens after write-off preparation.",
        },
        {
            "fieldname": "ndis_write_off_draft_run",
            "label": "NDIS CRM Write Off Draft Run",
            "fieldtype": "Link",
            "options": WRITE_OFF_DRAFT_RUN,
            "read_only": 1,
            "insert_after": "ndis_write_off_draft_run_required",
        },
        {
            "fieldname": "write_off_draft_status",
            "label": "Write Off Draft Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_write_off_draft_run",
        },
        {
            "fieldname": "write_off_draft_ready",
            "label": "Write Off Draft Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "write_off_draft_status",
        },
    ]

    shared_fields = [
        {
            "fieldname": "write_off_draft_section",
            "label": "NDIS Write Off Draft Run",
            "fieldtype": "Section Break",
            "insert_after": "write_off_preparation_ready",
        },
        {
            "fieldname": "ndis_write_off_draft_run",
            "label": "NDIS CRM Write Off Draft Run",
            "fieldtype": "Link",
            "options": WRITE_OFF_DRAFT_RUN,
            "read_only": 1,
            "insert_after": "write_off_draft_section",
        },
        {
            "fieldname": "write_off_draft_status",
            "label": "Write Off Draft Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_write_off_draft_run",
        },
        {
            "fieldname": "write_off_draft_ready",
            "label": "Write Off Draft Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "write_off_draft_status",
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
        INTAKE: shared_fields,
    }

    if doctype_exists(ATTENDANCE_DRAFT):
        custom_fields[ATTENDANCE_DRAFT] = shared_fields

    create_custom_fields(custom_fields, update=True)
    print("Created / updated Phase 33 write-off draft chain custom fields.")


def create_optional_ndis_write_off_custom_fields():
    if not doctype_exists(NDIS_WRITE_OFF):
        print("NDIS Write Off DocType not found. Skipping optional target custom fields.")
        return

    custom_fields = {
        NDIS_WRITE_OFF: [
            {
                "fieldname": "ndis_crm_write_off_draft_section",
                "label": "NDIS CRM Write Off Draft Control",
                "fieldtype": "Section Break",
                "insert_after": "modified",
            },
            {
                "fieldname": "ndis_crm_write_off_draft_run",
                "label": "NDIS CRM Write Off Draft Run",
                "fieldtype": "Link",
                "options": WRITE_OFF_DRAFT_RUN,
                "read_only": 1,
                "insert_after": "ndis_crm_write_off_draft_section",
            },
            {
                "fieldname": "ndis_crm_write_off_draft_line",
                "label": "NDIS CRM Write Off Draft Line",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "ndis_crm_write_off_draft_run",
            },
            {
                "fieldname": "ndis_crm_submit_blocked",
                "label": "NDIS CRM Submit Blocked",
                "fieldtype": "Check",
                "default": "1",
                "insert_after": "ndis_crm_write_off_draft_line",
            },
        ]
    }

    create_custom_fields(custom_fields, update=True)
    print("Created / updated optional NDIS Write Off Phase 33 custom fields.")


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
        return script.rstrip() + "\n\n" + insert.strip()
    return script[:idx] + insert.strip() + "," + script[idx:]


def _phase33_deal_actions():
    return r'''
// NDIS CRM Phase 33 Deal Actions
{
  label: "Create Write Off Draft Run",
  onClick: () => {
    call("ndis_crm.phase33_write_off_draft.create_write_off_draft_run_from_crm_deal", {
      deal: doc.name
    }).then((data) => {
      if (data && data.name) {
        createToast({
          title: data.created ? "Write Off Draft Run Created" : "Existing Write Off Draft Run Found",
          icon: "check",
          iconClasses: "text-green-600",
        })
        window.open(`/app/ndis-crm-write-off-draft-run/${data.name}`, "_blank")
      }
    })
  }
},
{
  label: "Open Write Off Draft Run",
  onClick: () => {
    if (doc.ndis_write_off_draft_run) {
      window.open(`/app/ndis-crm-write-off-draft-run/${doc.ndis_write_off_draft_run}`, "_blank")
    } else {
      createToast({ title: "No Write Off Draft Run linked yet", icon: "info" })
    }
  }
}
'''.strip()


def _deal_script():
    try:
        from ndis_crm.setup.phase32_write_off_preparation import _deal_script as phase32_deal_script
        script = phase32_deal_script()
    except Exception:
        script = """
function setupForm({ doc, call, createToast }) {
  return {
    actions: [
    ]
  }
}
""".strip()

    if "NDIS CRM Phase 33 Deal Actions" in script:
        return script

    return _append_before_last(script, "\n    ]", _phase33_deal_actions())


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

    preparation_script = r'''
frappe.ui.form.on("NDIS CRM Write Off Preparation Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Create Write Off Draft Run"), function () {
            frappe.call({
                method: "ndis_crm.phase33_write_off_draft.create_write_off_draft_run_from_write_off_preparation_run",
                args: { write_off_preparation_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating write-off draft run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Write Off Draft Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Write Off Draft Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_write_off_draft_run) {
            frm.add_custom_button(__("Open Write Off Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Write Off Draft Run", frm.doc.ndis_write_off_draft_run);
            }, __("Open"));
        }
    }
});
'''.strip()

    run_script = r'''
frappe.ui.form.on("NDIS CRM Write Off Draft Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Write Off Draft Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase33_write_off_draft.generate_write_off_draft_lines",
                args: { write_off_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating write-off draft lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Write-off draft lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Write Off Draft Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase33_write_off_draft.validate_write_off_draft_readiness",
                args: { write_off_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating write-off draft readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Write-off draft readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Draft Creation"), function () {
            frappe.call({
                method: "ndis_crm.phase33_write_off_draft.mark_ready_for_write_off_draft",
                args: { write_off_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for write-off draft creation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for write-off draft creation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Write Off Draft Run"), function () {
            frappe.call({
                method: "ndis_crm.phase33_write_off_draft.approve_write_off_draft_run",
                args: { write_off_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving write-off draft run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Write Off Draft Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Create Write Off Drafts"), function () {
            frappe.confirm(
                __("This creates CRM write-off drafts only by default. Optional NDIS Write Off drafts require compatible DocType and explicit external-draft allowance. It will not submit, create Journal Entry, GL, Payment Entry, recovery, adjustment, or bank reconciliation."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase33_write_off_draft.create_write_off_drafts",
                        args: { write_off_draft_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Creating write-off drafts...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Write-off drafts created"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.write_off_preparation_run) {
            frm.add_custom_button(__("Open Write Off Preparation Run"), function () {
                frappe.set_route("Form", "NDIS CRM Write Off Preparation Run", frm.doc.write_off_preparation_run);
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
            "NDIS CRM Write Off Preparation Phase33 Actions",
            {
                "dt": WRITE_OFF_PREPARATION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": preparation_script,
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Write Off Draft Run Actions",
            {
                "dt": WRITE_OFF_DRAFT_RUN,
                "view": "Form",
                "enabled": 1,
                "script": run_script,
            },
        )