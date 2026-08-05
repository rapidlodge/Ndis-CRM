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
PAYMENT_ENTRY_SUBMISSION_LINE = "NDIS CRM Payment Entry Submission Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"


def install():
    ensure_required_doctypes()
    create_payment_entry_submission_doctypes()
    create_custom_fields_phase29()
    create_payment_entry_submission_custom_fields()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 29 Payment Entry Submission gate installed successfully.")


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
        "Sales Invoice",
        "Payment Entry",
        "Payment Entry Reference",
        "NDIS Remittance Import",
        "NDIS Service Line",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not doctype_exists(dt)]
    if missing:
        frappe.throw("Missing required Phase 29 DocTypes: " + ", ".join(missing))

    print("Required Phase 29 DocTypes found.")


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


def create_payment_entry_submission_doctypes():
    create_payment_entry_submission_line()
    create_payment_entry_submission_run()


def create_payment_entry_submission_line():
    fields = [
        make_field("Source", "source_section", "Section Break"),
        make_field("Payment Entry Submission Source Key", "payment_entry_submission_source_key", "Data", read_only=1),
        make_field("Payment Entry", "payment_entry", "Link", options="Payment Entry", in_list_view=1),
        make_field("Payment Entry Docstatus", "payment_entry_docstatus", "Int", read_only=1),
        make_field("Payment Entry Status", "payment_entry_status", "Data", read_only=1),
        make_field("Payment Entry Type", "payment_entry_type", "Data", read_only=1),
        make_field("Party Type", "party_type", "Data", read_only=1),
        make_field("Party", "party", "Link", options="Customer", read_only=1),
        make_field("Payment Entry Posting Date", "payment_entry_posting_date", "Date", read_only=1),
        make_field("Payment Entry Reference No", "payment_entry_reference_no", "Data", read_only=1),
        make_field("Payment Entry Reference Date", "payment_entry_reference_date", "Date", read_only=1),
        make_field("Proposed Payment Amount", "proposed_payment_amount", "Currency", in_list_view=1),
        make_field("Paid Amount", "paid_amount", "Currency", read_only=1),
        make_field("Received Amount", "received_amount", "Currency", read_only=1),

        make_field("Invoice / Remittance", "invoice_remittance_section", "Section Break"),
        make_field("Sales Invoice", "sales_invoice", "Link", options="Sales Invoice", in_list_view=1),
        make_field("Sales Invoice Docstatus", "sales_invoice_docstatus", "Int", read_only=1),
        make_field("Sales Invoice Status", "sales_invoice_status", "Data", read_only=1),
        make_field("Sales Invoice Outstanding Amount", "sales_invoice_outstanding_amount", "Currency", read_only=1),
        make_field("NDIS Remittance Import", "ndis_remittance_import", "Link", options="NDIS Remittance Import"),
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

        make_field("Submission Controls", "submission_controls_section", "Section Break"),
        make_field("Submission Source Ready", "submission_source_ready", "Check", default=0),
        make_field("Payment Entry Submission Review Complete", "payment_entry_submission_review_complete", "Check", default=0),
        make_field("Payment Entry Submission Authorized", "payment_entry_submission_authorized", "Check", default=0),
        make_field("Payment Entry Submit Authorized", "payment_entry_submit_authorized", "Check", default=0, description="Legacy direct submit flag remains blocked. Use run-level Payment Entry Submission Allowed."),
        make_field("Journal Authorized", "journal_authorized", "Check", default=0, description="Blocked in Phase 29."),
        make_field("Write Off Authorized", "write_off_authorized", "Check", default=0, description="Blocked in Phase 29."),
        make_field("Recovery Authorized", "recovery_authorized", "Check", default=0, description="Blocked in Phase 29."),
        make_field("Bank Reconciliation Authorized", "bank_reconciliation_authorized", "Check", default=0, description="Blocked in Phase 29."),
        make_field("Submission Hold", "submission_hold", "Check", default=1, in_list_view=1),
        make_field("Submission Hold Reason", "submission_hold_reason", "Small Text"),

        make_field("Line Status", "line_status_section", "Section Break"),
        make_field("Line Ready for Payment Entry Submission", "line_ready_for_payment_entry_submission", "Check", default=0, in_list_view=1),
        make_field("Payment Entry Submission Line Status", "payment_entry_submission_line_status", "Select", options="Draft\nReady\nApproved\nPayment Entry Submitted\nReturned\nCancelled", default="Draft", in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=PAYMENT_ENTRY_SUBMISSION_LINE,
        fields=fields,
        istable=1,
    )


def create_payment_entry_submission_run():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-PAY-ENTRY-SUB-.YYYY.-.#####", default="NDIS-PAY-ENTRY-SUB-.YYYY.-.#####", reqd=1),

        make_field("Status", "status_section", "Section Break"),
        make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Payment Entry Submission\nPayment Entry Submission Run Approved\nPayment Entries Submitted\nReturned to Payment Entry Draft Run\nCancelled", default="Draft", in_list_view=1),
        make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
        make_field("Payment Entry Submission Run Ready", "payment_entry_submission_run_ready", "Check", read_only=1, in_list_view=1),
        make_field("Payment Entry Submission Allowed", "payment_entry_submission_allowed", "Check", default=0),
        make_field("Journal Creation Allowed", "journal_creation_allowed", "Check", default=0, description="Blocked in Phase 29."),
        make_field("Write Off Creation Allowed", "write_off_creation_allowed", "Check", default=0, description="Blocked in Phase 29."),
        make_field("Recovery Creation Allowed", "recovery_creation_allowed", "Check", default=0, description="Blocked in Phase 29."),
        make_field("Bank Reconciliation Allowed", "bank_reconciliation_allowed", "Check", default=0, description="Blocked in Phase 29."),

        make_field("Summary", "summary_section", "Section Break"),
        make_field("Payment Entry Submission Line Count", "payment_entry_submission_line_count", "Int", read_only=1),
        make_field("Active Submission Line Count", "active_submission_line_count", "Int", read_only=1),
        make_field("Payment Entry Submission Amount Total", "payment_entry_submission_amount_total", "Currency", read_only=1),
        make_field("Draft Payment Entry Count", "draft_payment_entry_count", "Int", read_only=1),
        make_field("Submitted Payment Entry Count", "submitted_payment_entry_count", "Int", read_only=1),
        make_field("Payment Entry Submission Ready Count", "payment_entry_submission_ready_count", "Int", read_only=1),
        make_field("Submission Hold Count", "submission_hold_count", "Int", read_only=1),
        make_field("Blocked Submit Authorization Count", "blocked_submit_authorization_count", "Int", read_only=1),
        make_field("Blocked Journal Authorization Count", "blocked_journal_authorization_count", "Int", read_only=1),
        make_field("Blocked Write Off Authorization Count", "blocked_write_off_authorization_count", "Int", read_only=1),
        make_field("Blocked Recovery Authorization Count", "blocked_recovery_authorization_count", "Int", read_only=1),
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
        make_field("NDIS CRM Payment Entry Draft Run", "payment_entry_draft_run", "Link", options=PAYMENT_ENTRY_DRAFT_RUN, reqd=1, in_list_view=1),
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

        make_field("Owners", "owners_section", "Section Break"),
        make_field("Payment Entry Submission Owner", "payment_entry_submission_owner", "Link", options="User", in_list_view=1),
        make_field("Payment Entry Draft Owner", "payment_entry_draft_owner", "Link", options="User"),
        make_field("Payment Allocation Owner", "payment_allocation_owner", "Link", options="User"),
        make_field("Submitted By", "submitted_by", "Link", options="User", read_only=1),
        make_field("Submitted On", "submitted_on", "Datetime", read_only=1),

        make_field("Payment Entry Submission Lines", "payment_entry_submission_lines_section", "Section Break"),
        make_field("Payment Entry Submission Lines", "payment_entry_submission_lines", "Table", options=PAYMENT_ENTRY_SUBMISSION_LINE),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Payment Entry Submission Notes", "payment_entry_submission_notes", "Small Text"),
        make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=PAYMENT_ENTRY_SUBMISSION_RUN,
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
    )


def create_custom_fields_phase29():
    deal_fields = [
        {
            "fieldname": "payment_entry_submission_section",
            "label": "NDIS Payment Entry Submission Run",
            "fieldtype": "Section Break",
            "insert_after": "payment_entry_draft_ready",
        },
        {
            "fieldname": "ndis_payment_entry_submission_run_required",
            "label": "Payment Entry Submission Required Before Active Deal",
            "fieldtype": "Check",
            "default": "0",
            "insert_after": "payment_entry_submission_section",
            "description": "Optional guard only. Payment Entry submission normally happens after Payment Entry draft run.",
        },
        {
            "fieldname": "ndis_payment_entry_submission_run",
            "label": "NDIS CRM Payment Entry Submission Run",
            "fieldtype": "Link",
            "options": PAYMENT_ENTRY_SUBMISSION_RUN,
            "read_only": 1,
            "insert_after": "ndis_payment_entry_submission_run_required",
        },
        {
            "fieldname": "payment_entry_submission_status",
            "label": "Payment Entry Submission Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_payment_entry_submission_run",
        },
        {
            "fieldname": "payment_entry_submission_ready",
            "label": "Payment Entry Submission Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "payment_entry_submission_status",
        },
    ]

    shared_fields = [
        {
            "fieldname": "payment_entry_submission_section",
            "label": "NDIS Payment Entry Submission Run",
            "fieldtype": "Section Break",
            "insert_after": "payment_entry_draft_ready",
        },
        {
            "fieldname": "ndis_payment_entry_submission_run",
            "label": "NDIS CRM Payment Entry Submission Run",
            "fieldtype": "Link",
            "options": PAYMENT_ENTRY_SUBMISSION_RUN,
            "read_only": 1,
            "insert_after": "payment_entry_submission_section",
        },
        {
            "fieldname": "payment_entry_submission_status",
            "label": "Payment Entry Submission Status",
            "fieldtype": "Data",
            "read_only": 1,
            "insert_after": "ndis_payment_entry_submission_run",
        },
        {
            "fieldname": "payment_entry_submission_ready",
            "label": "Payment Entry Submission Ready",
            "fieldtype": "Check",
            "read_only": 1,
            "insert_after": "payment_entry_submission_status",
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
        INTAKE: shared_fields,
    }

    if doctype_exists(ATTENDANCE_DRAFT):
        custom_fields[ATTENDANCE_DRAFT] = shared_fields

    create_custom_fields(custom_fields, update=True)
    print("Created / updated Phase 29 Payment Entry submission chain custom fields.")


def create_payment_entry_submission_custom_fields():
    custom_fields = {
        "Payment Entry": [
            {
                "fieldname": "ndis_crm_payment_entry_submission_run",
                "label": "NDIS CRM Payment Entry Submission Run",
                "fieldtype": "Link",
                "options": PAYMENT_ENTRY_SUBMISSION_RUN,
                "read_only": 1,
                "insert_after": "ndis_crm_payment_entry_status",
            },
            {
                "fieldname": "ndis_crm_payment_entry_submission_status",
                "label": "NDIS CRM Payment Entry Submission Status",
                "fieldtype": "Data",
                "read_only": 1,
                "insert_after": "ndis_crm_payment_entry_submission_run",
            },
            {
                "fieldname": "ndis_crm_payment_entry_submission_approved",
                "label": "NDIS CRM Payment Entry Submission Approved",
                "fieldtype": "Check",
                "default": "0",
                "read_only": 1,
                "insert_after": "ndis_crm_payment_entry_submission_status",
            },
            {
                "fieldname": "ndis_crm_payment_entry_submitted_on",
                "label": "NDIS CRM Payment Entry Submitted On",
                "fieldtype": "Datetime",
                "read_only": 1,
                "insert_after": "ndis_crm_payment_entry_submission_approved",
            },
            {
                "fieldname": "ndis_crm_payment_entry_submitted_by",
                "label": "NDIS CRM Payment Entry Submitted By",
                "fieldtype": "Link",
                "options": "User",
                "read_only": 1,
                "insert_after": "ndis_crm_payment_entry_submitted_on",
            },
        ]
    }

    create_custom_fields(custom_fields, update=True)
    print("Created / updated Phase 29 Payment Entry submission custom fields.")


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
    if anchor not in script:
        frappe.throw(f"Could not append Phase 29 action script because the anchor was not found: {anchor}")
    before, after = script.rsplit(anchor, 1)
    return before + insert + anchor + after


def _deal_script():
    try:
        from ndis_crm.setup.phase28_payment_entry_draft import _deal_script as previous_script

        script = previous_script()
    except Exception:
        script = "function setupForm({ doc, call, createToast }) {\n  return { actions: [] }\n}"

    insert = r'''
,
      {
        label: "Create Payment Entry Submission Run",
        onClick: () => {
          call("ndis_crm.phase29_payment_entry_submission.create_payment_entry_submission_run_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Payment Entry Submission Run Created" : "Existing Payment Entry Submission Run Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-payment-entry-submission-run/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Payment Entry Submission Run",
        onClick: () => {
          if (doc.ndis_payment_entry_submission_run) {
            window.open(`/app/ndis-crm-payment-entry-submission-run/${doc.ndis_payment_entry_submission_run}`, "_blank")
          } else {
            createToast({ title: "No Payment Entry Submission Run linked yet", icon: "info" })
          }
        }
      }
'''.rstrip()
    return _append_before_last(script, "\n    ]", insert)


def create_form_scripts():
    upsert_doc(
        "CRM Form Script",
        "NDIS CRM Deal Actions",
        {
            "dt": CRM_DEAL,
            "view": "Form",
            "enabled": 1,
            "is_standard": 0,
            "script": _deal_script(),
        },
    )

    if frappe.db.exists("DocType", "Client Script"):
        upsert_doc(
            "Client Script",
            "NDIS CRM Payment Entry Draft Run Actions",
            {
                "dt": PAYMENT_ENTRY_DRAFT_RUN,
                "view": "Form",
                "enabled": 1,
                "script": _draft_run_script(),
            },
        )

        upsert_doc(
            "Client Script",
            "NDIS CRM Payment Entry Submission Run Actions",
            {
                "dt": PAYMENT_ENTRY_SUBMISSION_RUN,
                "view": "Form",
                "enabled": 1,
                "script": _submission_run_script(),
            },
        )


def _draft_run_script():
    try:
        from ndis_crm.setup.phase28_payment_entry_draft import _run_script as previous_script

        script = previous_script()
    except Exception:
        script = 'frappe.ui.form.on("NDIS CRM Payment Entry Draft Run", { refresh(frm) { if (frm.is_new()) { return; } } });'

    insert = r'''

        frm.add_custom_button(__("Create Payment Entry Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase29_payment_entry_submission.create_payment_entry_submission_run_from_payment_entry_draft_run",
                args: { payment_entry_draft_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating Payment Entry Submission Run...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Payment Entry Submission Run created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Payment Entry Submission Run", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_payment_entry_submission_run) {
            frm.add_custom_button(__("Open Payment Entry Submission Run"), function () {
                frappe.set_route("Form", "NDIS CRM Payment Entry Submission Run", frm.doc.ndis_payment_entry_submission_run);
            }, __("Open"));
        }
'''
    return _append_before_last(script, "\n    }\n});", insert)


def _submission_run_script():
    return r'''
frappe.ui.form.on("NDIS CRM Payment Entry Submission Run", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Payment Entry Submission Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase29_payment_entry_submission.generate_payment_entry_submission_lines",
                args: { payment_entry_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating Payment Entry submission lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Payment Entry submission lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Payment Entry Submission Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase29_payment_entry_submission.validate_payment_entry_submission_readiness",
                args: { payment_entry_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating Payment Entry submission readiness...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Payment Entry submission readiness validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Payment Entry Submission"), function () {
            frappe.call({
                method: "ndis_crm.phase29_payment_entry_submission.mark_ready_for_payment_entry_submission",
                args: { payment_entry_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for Payment Entry submission...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for Payment Entry submission"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Payment Entry Submission Run"), function () {
            frappe.call({
                method: "ndis_crm.phase29_payment_entry_submission.approve_payment_entry_submission_run",
                args: { payment_entry_submission_run: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving Payment Entry Submission Run...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Payment Entry Submission Run approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Submit Payment Entries"), function () {
            frappe.confirm(
                __("This will submit existing Phase 28 Draft Payment Entries. ERPNext may create standard GL Entries through Payment Entry submit. It will not create Journal Entry, manual GL Entry, write-off, recovery, or bank reconciliation."),
                function () {
                    frappe.call({
                        method: "ndis_crm.phase29_payment_entry_submission.submit_payment_entries",
                        args: { payment_entry_submission_run: frm.doc.name },
                        freeze: true,
                        freeze_message: __("Submitting Payment Entries...")
                    }).then((r) => {
                        if (r.message) {
                            frappe.show_alert({ message: r.message.message || __("Payment Entries submitted"), indicator: "green" });
                            frm.reload_doc();
                        }
                    });
                }
            );
        }, __("Actions"));

        if (frm.doc.payment_entry_draft_run) {
            frm.add_custom_button(__("Open Payment Entry Draft Run"), function () {
                frappe.set_route("Form", "NDIS CRM Payment Entry Draft Run", frm.doc.payment_entry_draft_run);
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
