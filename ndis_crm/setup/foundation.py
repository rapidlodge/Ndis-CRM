import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


APP_NAME = "ndis_crm"
MODULE_NAME = "Ndis Crm"


SERVICE_CATEGORY_OPTIONS = """
Assistance with Daily Life
Supported Independent Living
Social & Community Participation
Improved Daily Living
Support Coordination
Improved Relationships
Transport
Assistive Technology
Improved Life Choices
Other
""".strip()


PLAN_MANAGEMENT_OPTIONS = """
NDIA Managed
Plan Managed
Self Managed
Mixed
Unknown
""".strip()


URGENCY_OPTIONS = """
Low
Medium
High
Critical
""".strip()


CURRENT_LIVING_OPTIONS = """
Own Home
Family Home
Hospital
SIL
SDA
Temporary Accommodation
Aged Care
Homeless / At Risk
Other
""".strip()


def install():
    """
    Main installer for NDIS CRM foundation.
    Safe to run more than once.
    """
    ensure_module()
    ensure_roles()
    create_standard_doctypes()
    create_crm_custom_fields()
    seed_service_lines()
    frappe.db.commit()
    print("NDIS CRM foundation installed successfully.")


def after_install():
    install()


def ensure_module():
    if not frappe.db.exists("Module Def", MODULE_NAME):
        module = frappe.get_doc({
            "doctype": "Module Def",
            "module_name": MODULE_NAME,
            "app_name": APP_NAME,
            "custom": 0
        })
        module.insert(ignore_permissions=True)
        print(f"Created Module Def: {MODULE_NAME}")
    else:
        print(f"Module Def already exists: {MODULE_NAME}")


def ensure_roles():
    roles = [
        "NDIS CRM Manager",
        "NDIS Intake Officer",
        "NDIS Service Manager",
        "NDIS Plan Management Officer",
        "NDIS CRM Read Only"
    ]

    for role_name in roles:
        if not frappe.db.exists("Role", role_name):
            role = frappe.get_doc({
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1
            })
            role.insert(ignore_permissions=True)
            print(f"Created Role: {role_name}")
        else:
            print(f"Role already exists: {role_name}")


def make_field(label, fieldname, fieldtype, **kwargs):
    field = {
        "label": label,
        "fieldname": fieldname,
        "fieldtype": fieldtype
    }
    field.update(kwargs)
    return field


def standard_permissions():
    return [
        {
            "role": "System Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "email": 1,
            "export": 1,
            "print": 1,
            "report": 1,
            "share": 1
        },
        {
            "role": "NDIS CRM Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "delete": 1,
            "email": 1,
            "export": 1,
            "print": 1,
            "report": 1,
            "share": 1
        },
        {
            "role": "NDIS Intake Officer",
            "read": 1,
            "write": 1,
            "create": 1,
            "email": 1,
            "print": 1,
            "report": 1
        },
        {
            "role": "NDIS Service Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "email": 1,
            "print": 1,
            "report": 1
        },
        {
            "role": "NDIS CRM Read Only",
            "read": 1,
            "export": 1,
            "print": 1,
            "report": 1
        }
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
        "title_field": title_field
    })

    for field in fields:
        doc.append("fields", field)

    if not istable:
        for perm in standard_permissions():
            doc.append("permissions", perm)

    doc.insert(ignore_permissions=True)
    print(f"Created DocType: {name}")


def create_standard_doctypes():
    create_ndis_service_line()
    create_ndis_service_interest()
    create_ndis_participant_intake()


def create_ndis_service_line():
    fields = [
        make_field("Service Details", "service_details_section", "Section Break"),
        make_field("Service Line Name", "service_line_name", "Data", reqd=1, unique=1, in_list_view=1),
        make_field("Service Code", "service_code", "Data", in_list_view=1),
        make_field("Demand Level", "demand_level", "Select", options="Very High\nHigh\nMedium-High\nMedium\nLow", in_list_view=1),
        make_field("NDIS Support Category", "ndis_support_category", "Select", options=SERVICE_CATEGORY_OPTIONS, in_list_view=1),
        make_field("Budget Type", "budget_type", "Select", options="Core\nCapacity Building\nCapital\nRecurring\nUnknown", in_list_view=1),

        make_field("Rules", "rules_column_break", "Column Break"),
        make_field("Requires Intake Assessment", "requires_intake_assessment", "Check", default=1),
        make_field("Requires Document Checklist", "requires_document_checklist", "Check", default=1),
        make_field("Requires Risk Screening", "requires_risk_screening", "Check", default=0),
        make_field("Requires Clinical Review", "requires_clinical_review", "Check", default=0),
        make_field("Requires Service Agreement", "requires_service_agreement", "Check", default=1),
        make_field("Requires Roster Handover", "requires_roster_handover", "Check", default=0),
        make_field("Requires Billing Setup", "requires_billing_setup", "Check", default=1),
        make_field("Active", "active", "Check", default=1),

        make_field("Description", "description_section", "Section Break"),
        make_field("Description", "description", "Small Text")
    ]

    create_doctype_if_missing(
        name="NDIS Service Line",
        fields=fields,
        autoname="field:service_line_name",
        title_field="service_line_name",
        istable=0
    )


def create_ndis_service_interest():
    fields = [
        make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
        make_field("Support Category", "support_category", "Data", fetch_from="service_line.ndis_support_category", read_only=1, in_list_view=1),
        make_field("Budget Type", "budget_type", "Data", fetch_from="service_line.budget_type", read_only=1),
        make_field("Priority", "priority", "Select", options="Low\nMedium\nHigh\nUrgent", in_list_view=1),
        make_field("Required Start Date", "required_start_date", "Date", in_list_view=1),

        make_field("More Details", "more_details_section", "Section Break"),
        make_field("Current Provider", "current_provider", "Data"),
        make_field("Reason for Change", "reason_for_change", "Small Text"),
        make_field("Funding Available?", "funding_available", "Select", options="Yes\nNo\nUnknown"),
        make_field("Assessment Required?", "assessment_required", "Check"),
        make_field("Documents Required?", "documents_required", "Check"),
        make_field("Notes", "notes", "Small Text")
    ]

    create_doctype_if_missing(
        name="NDIS Service Interest",
        fields=fields,
        istable=1
    )


def create_ndis_participant_intake():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-INTAKE-.YYYY.-.#####", default="NDIS-INTAKE-.YYYY.-.#####", reqd=1),
        make_field("CRM Links", "crm_links_section", "Section Break"),
        make_field("Participant Lead", "participant_lead", "Link", options="Lead", in_list_view=1),
        make_field("Opportunity", "opportunity", "Link", options="Opportunity"),
        make_field("Status", "status", "Select", options="Draft\nContacted\nIntake Started\nWaiting Documents\nFunding Review\nSuitability Review\nQualified\nNot Suitable\nConverted", default="Draft", in_list_view=1),
        make_field("Intake Officer", "intake_officer", "Link", options="User"),

        make_field("Participant Details", "participant_details_section", "Section Break"),
        make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
        make_field("NDIS Number", "ndis_number", "Data"),
        make_field("Date of Birth", "date_of_birth", "Date"),
        make_field("Primary Disability", "primary_disability", "Data"),
        make_field("Preferred Contact Method", "preferred_contact_method", "Select", options="Phone\nEmail\nSMS\nIn Person\nSupport Coordinator\nFamily / Nominee"),
        make_field("Consent to Contact", "consent_to_contact", "Check"),
        make_field("Consent Notes", "consent_notes", "Small Text"),

        make_field("Plan Details", "plan_details_section", "Section Break"),
        make_field("Has Current NDIS Plan", "has_current_ndis_plan", "Check"),
        make_field("Plan Start Date", "plan_start_date", "Date"),
        make_field("Plan End Date", "plan_end_date", "Date"),
        make_field("Plan Management Type", "plan_management_type", "Select", options=PLAN_MANAGEMENT_OPTIONS),
        make_field("Support Coordinator Name", "support_coordinator_name", "Data"),
        make_field("Support Coordinator Email", "support_coordinator_email", "Data"),
        make_field("Plan Manager Name", "plan_manager_name", "Data"),
        make_field("Plan Manager Email", "plan_manager_email", "Data"),

        make_field("Service Needs", "service_needs_section", "Section Break"),
        make_field("Current Living Situation", "current_living_situation", "Select", options=CURRENT_LIVING_OPTIONS),
        make_field("Enquiry Urgency", "enquiry_urgency", "Select", options=URGENCY_OPTIONS),
        make_field("Service Interests", "service_interests", "Table", options="NDIS Service Interest"),

        make_field("Risk Screening", "risk_screening_section", "Section Break"),
        make_field("Risk Level", "risk_level", "Select", options="None\nLow\nMedium\nHigh\nCritical"),
        make_field("Behaviour Support Plan Available", "behaviour_support_plan_available", "Check"),
        make_field("Restrictive Practice Flag", "restrictive_practice_flag", "Check"),
        make_field("Manual Handling Needs", "manual_handling_needs", "Check"),
        make_field("Medication Support Required", "medication_support_required", "Check"),
        make_field("Clinical Review Required", "clinical_review_required", "Check"),

        make_field("Internal Notes", "internal_notes_section", "Section Break"),
        make_field("Intake Notes", "intake_notes", "Small Text"),
        make_field("Decision Notes", "decision_notes", "Small Text")
    ]

    create_doctype_if_missing(
        name="NDIS Participant Intake",
        fields=fields,
        autoname="naming_series:",
        title_field="participant_name",
        istable=0
    )


def create_crm_custom_fields():
    lead_fields = [
        {
            "fieldname": "ndis_section",
            "label": "NDIS CRM",
            "fieldtype": "Section Break",
            "insert_after": "status"
        },
        {
            "fieldname": "is_ndis_participant",
            "label": "Is NDIS Participant?",
            "fieldtype": "Check",
            "insert_after": "ndis_section"
        },
        {
            "fieldname": "lead_category",
            "label": "Lead Category",
            "fieldtype": "Select",
            "options": "Participant\nFamily / Nominee\nSupport Coordinator\nPlan Manager\nProvider\nHospital\nLAC\nOther",
            "insert_after": "is_ndis_participant"
        },
        {
            "fieldname": "participant_name",
            "label": "Participant Name",
            "fieldtype": "Data",
            "insert_after": "lead_category"
        },
        {
            "fieldname": "ndis_number",
            "label": "NDIS Number",
            "fieldtype": "Data",
            "insert_after": "participant_name"
        },
        {
            "fieldname": "participant_dob",
            "label": "Participant Date of Birth",
            "fieldtype": "Date",
            "insert_after": "ndis_number"
        },
        {
            "fieldname": "enquiry_urgency",
            "label": "Enquiry Urgency",
            "fieldtype": "Select",
            "options": URGENCY_OPTIONS,
            "insert_after": "participant_dob"
        },
        {
            "fieldname": "current_living_situation",
            "label": "Current Living Situation",
            "fieldtype": "Select",
            "options": CURRENT_LIVING_OPTIONS,
            "insert_after": "enquiry_urgency"
        },
        {
            "fieldname": "has_ndis_plan",
            "label": "Has Current NDIS Plan",
            "fieldtype": "Check",
            "insert_after": "current_living_situation"
        },
        {
            "fieldname": "plan_start_date",
            "label": "Plan Start Date",
            "fieldtype": "Date",
            "insert_after": "has_ndis_plan"
        },
        {
            "fieldname": "plan_end_date",
            "label": "Plan End Date",
            "fieldtype": "Date",
            "insert_after": "plan_start_date"
        },
        {
            "fieldname": "plan_management_type",
            "label": "Plan Management Type",
            "fieldtype": "Select",
            "options": PLAN_MANAGEMENT_OPTIONS,
            "insert_after": "plan_end_date"
        },
        {
            "fieldname": "preferred_contact_method",
            "label": "Preferred Contact Method",
            "fieldtype": "Select",
            "options": "Phone\nEmail\nSMS\nIn Person\nSupport Coordinator\nFamily / Nominee",
            "insert_after": "plan_management_type"
        },
        {
            "fieldname": "consent_to_contact",
            "label": "Consent to Contact",
            "fieldtype": "Check",
            "insert_after": "preferred_contact_method"
        },
        {
            "fieldname": "consent_notes",
            "label": "Consent Notes",
            "fieldtype": "Small Text",
            "insert_after": "consent_to_contact"
        },
        {
            "fieldname": "next_follow_up_date",
            "label": "Next Follow-up Date",
            "fieldtype": "Date",
            "insert_after": "consent_notes"
        },
        {
            "fieldname": "assigned_intake_officer",
            "label": "Assigned Intake Officer",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "next_follow_up_date"
        },
        {
            "fieldname": "risk_flag",
            "label": "Risk Flag",
            "fieldtype": "Select",
            "options": "None\nLow\nMedium\nHigh\nCritical",
            "insert_after": "assigned_intake_officer"
        },
        {
            "fieldname": "risk_notes",
            "label": "Risk Notes",
            "fieldtype": "Small Text",
            "insert_after": "risk_flag"
        },
        {
            "fieldname": "ndis_service_interests",
            "label": "NDIS Service Interests",
            "fieldtype": "Table",
            "options": "NDIS Service Interest",
            "insert_after": "risk_notes"
        }
    ]

    opportunity_fields = [
        {
            "fieldname": "ndis_section",
            "label": "NDIS CRM",
            "fieldtype": "Section Break",
            "insert_after": "status"
        },
        {
            "fieldname": "opportunity_type_ndis",
            "label": "NDIS Opportunity Type",
            "fieldtype": "Select",
            "options": "Daily Life\nSIL\nSocial & Community Participation\nTherapy\nSupport Coordination\nBehaviour Support\nTransport\nAssistive Technology\nPlan Management\nMixed Service",
            "insert_after": "ndis_section"
        },
        {
            "fieldname": "participant_lead",
            "label": "Participant Lead",
            "fieldtype": "Link",
            "options": "Lead",
            "insert_after": "opportunity_type_ndis"
        },
        {
            "fieldname": "participant_customer",
            "label": "Participant Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "insert_after": "participant_lead"
        },
        {
            "fieldname": "pipeline_type",
            "label": "Pipeline Type",
            "fieldtype": "Select",
            "options": "General Intake\nSIL Placement\nDaily Life Support\nTherapy\nSupport Coordination\nBehaviour Support\nTransport\nAssistive Technology\nPlan Management",
            "insert_after": "participant_customer"
        },
        {
            "fieldname": "pipeline_stage",
            "label": "Pipeline Stage",
            "fieldtype": "Select",
            "options": "New Opportunity\nService Need Confirmed\nDocuments Requested\nDocuments Collected\nFunding Verified\nService Agreement Sent\nService Agreement Signed\nHandover to Operations\nWon\nLost",
            "insert_after": "pipeline_type"
        },
        {
            "fieldname": "estimated_weekly_revenue",
            "label": "Estimated Weekly Revenue",
            "fieldtype": "Currency",
            "insert_after": "pipeline_stage"
        },
        {
            "fieldname": "estimated_start_date",
            "label": "Estimated Start Date",
            "fieldtype": "Date",
            "insert_after": "estimated_weekly_revenue"
        },
        {
            "fieldname": "funding_verified",
            "label": "Funding Verified",
            "fieldtype": "Check",
            "insert_after": "estimated_start_date"
        },
        {
            "fieldname": "service_agreement_required",
            "label": "Service Agreement Required",
            "fieldtype": "Check",
            "default": 1,
            "insert_after": "funding_verified"
        },
        {
            "fieldname": "service_agreement_status",
            "label": "Service Agreement Status",
            "fieldtype": "Select",
            "options": "Not Started\nPrepared\nSent\nSigned\nDeclined\nNot Required",
            "insert_after": "service_agreement_required"
        },
        {
            "fieldname": "roster_required",
            "label": "Roster Required",
            "fieldtype": "Check",
            "insert_after": "service_agreement_status"
        },
        {
            "fieldname": "clinical_review_required",
            "label": "Clinical Review Required",
            "fieldtype": "Check",
            "insert_after": "roster_required"
        },
        {
            "fieldname": "billing_setup_required",
            "label": "Billing Setup Required",
            "fieldtype": "Check",
            "default": 1,
            "insert_after": "clinical_review_required"
        },
        {
            "fieldname": "handover_status",
            "label": "Handover Status",
            "fieldtype": "Select",
            "options": "Not Ready\nReady\nHanded Over\nAccepted\nRejected",
            "insert_after": "billing_setup_required"
        },
        {
            "fieldname": "lost_reason",
            "label": "Lost Reason",
            "fieldtype": "Select",
            "options": "\nNo Funding\nNo Capacity\nNot Suitable\nChose Other Provider\nNo Response\nParticipant Declined\nOther",
            "insert_after": "handover_status"
        },
        {
            "fieldname": "competitor_provider",
            "label": "Competitor Provider",
            "fieldtype": "Data",
            "insert_after": "lost_reason"
        },
        {
            "fieldname": "next_action",
            "label": "Next Action",
            "fieldtype": "Small Text",
            "insert_after": "competitor_provider"
        },
        {
            "fieldname": "ndis_service_interests",
            "label": "NDIS Service Interests",
            "fieldtype": "Table",
            "options": "NDIS Service Interest",
            "insert_after": "next_action"
        }
    ]

    custom_fields = {
        "Lead": lead_fields,
        "Opportunity": opportunity_fields
    }

    create_custom_fields(custom_fields, update=True)
    print("Created / updated custom fields for Lead and Opportunity.")


def seed_service_lines():
    service_lines = [
        {
            "service_line_name": "Assistance with Daily Life / Core Daily Activities",
            "service_code": "DAILY_LIFE",
            "demand_level": "Very High",
            "ndis_support_category": "Assistance with Daily Life",
            "budget_type": "Core",
            "requires_risk_screening": 1,
            "requires_roster_handover": 1,
            "requires_billing_setup": 1,
            "description": "Personal care, domestic assistance, meal preparation, showering, medication prompts, daily living support, overnight support."
        },
        {
            "service_line_name": "Supported Independent Living — SIL",
            "service_code": "SIL",
            "demand_level": "Very High",
            "ndis_support_category": "Supported Independent Living",
            "budget_type": "Core",
            "requires_risk_screening": 1,
            "requires_clinical_review": 1,
            "requires_roster_handover": 1,
            "requires_billing_setup": 1,
            "description": "24/7 or shared living support in SIL homes, active overnight, sleepover, daily routines, behaviour support implementation."
        },
        {
            "service_line_name": "Social & Community Participation",
            "service_code": "COMMUNITY_PARTICIPATION",
            "demand_level": "Very High",
            "ndis_support_category": "Social & Community Participation",
            "budget_type": "Core",
            "requires_risk_screening": 1,
            "requires_roster_handover": 1,
            "requires_billing_setup": 1,
            "description": "Community access, outings, shopping, appointments, group activities, recreational participation and community support shifts."
        },
        {
            "service_line_name": "Therapy / Improved Daily Living",
            "service_code": "THERAPY",
            "demand_level": "High",
            "ndis_support_category": "Improved Daily Living",
            "budget_type": "Capacity Building",
            "requires_clinical_review": 1,
            "requires_billing_setup": 1,
            "description": "OT, speech therapy, psychology, physiotherapy, functional capacity assessments, therapy assistants and skill-building therapy."
        },
        {
            "service_line_name": "Support Coordination",
            "service_code": "SUPPORT_COORDINATION",
            "demand_level": "High",
            "ndis_support_category": "Support Coordination",
            "budget_type": "Capacity Building",
            "requires_risk_screening": 1,
            "requires_billing_setup": 1,
            "description": "Connecting participants with providers, plan implementation, budget monitoring, crisis support and specialist support coordination."
        },
        {
            "service_line_name": "Behaviour Support / Improved Relationships",
            "service_code": "BEHAVIOUR_SUPPORT",
            "demand_level": "High",
            "ndis_support_category": "Improved Relationships",
            "budget_type": "Capacity Building",
            "requires_risk_screening": 1,
            "requires_clinical_review": 1,
            "requires_billing_setup": 1,
            "description": "Positive behaviour support plans, behaviour assessments, restrictive practice support and behaviour strategies."
        },
        {
            "service_line_name": "Transport Support",
            "service_code": "TRANSPORT",
            "demand_level": "Medium-High",
            "ndis_support_category": "Transport",
            "budget_type": "Core",
            "requires_roster_handover": 1,
            "requires_billing_setup": 1,
            "description": "Participant transport, community access transport, travel to appointments, work, therapy and activities."
        },
        {
            "service_line_name": "Assistive Technology",
            "service_code": "ASSISTIVE_TECHNOLOGY",
            "demand_level": "Medium-High",
            "ndis_support_category": "Assistive Technology",
            "budget_type": "Capital",
            "requires_document_checklist": 1,
            "requires_clinical_review": 1,
            "requires_billing_setup": 1,
            "description": "Mobility aids, wheelchairs, hoists, communication devices, low-cost and high-cost equipment."
        },
        {
            "service_line_name": "Plan Management / Choice and Control",
            "service_code": "PLAN_MANAGEMENT",
            "demand_level": "Medium-High",
            "ndis_support_category": "Improved Life Choices",
            "budget_type": "Capacity Building",
            "requires_document_checklist": 1,
            "requires_billing_setup": 1,
            "description": "Invoice processing, provider payments, participant budget tracking, monthly statements and claim reconciliation."
        }
    ]

    for row in service_lines:
        if not frappe.db.exists("NDIS Service Line", row["service_line_name"]):
            doc = frappe.get_doc({
                "doctype": "NDIS Service Line",
                **row
            })
            doc.insert(ignore_permissions=True)
            print(f"Inserted service line: {row['service_line_name']}")
        else:
            print(f"Service line already exists: {row['service_line_name']}")


def health_check():
    doctypes = [
        "NDIS Service Line",
        "NDIS Service Interest",
        "NDIS Participant Intake"
    ]

    roles = [
        "NDIS CRM Manager",
        "NDIS Intake Officer",
        "NDIS Service Manager",
        "NDIS Plan Management Officer",
        "NDIS CRM Read Only"
    ]

    print("---- NDIS CRM Health Check ----")

    for dt in doctypes:
        print(f"DocType {dt}: {'OK' if frappe.db.exists('DocType', dt) else 'MISSING'}")

    for role in roles:
        print(f"Role {role}: {'OK' if frappe.db.exists('Role', role) else 'MISSING'}")

    service_line_count = frappe.db.count("NDIS Service Line")
    print(f"NDIS Service Line records: {service_line_count}")

    lead_field = frappe.db.exists("Custom Field", "Lead-ndis_section")
    opp_field = frappe.db.exists("Custom Field", "Opportunity-ndis_section")

    print(f"Lead custom fields: {'OK' if lead_field else 'MISSING'}")
    print(f"Opportunity custom fields: {'OK' if opp_field else 'MISSING'}")

    print("---- End Health Check ----")
