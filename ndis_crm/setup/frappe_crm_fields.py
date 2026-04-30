import frappe


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


PLAN_MANAGEMENT_OPTIONS = """
NDIA Managed
Plan Managed
Self Managed
Mixed
Unknown
""".strip()


def install():
    """
    Adds NDIS CRM fields to Frappe CRM frontend doctypes.

    Safe behaviour:
    - Does not edit Frappe CRM core files.
    - Does not overwrite standard Frappe CRM fields.
    - Updates existing NDIS custom fields if already created.
    - Skips a field if the same fieldname already exists as a standard field.
    """

    doctypes = {
        "CRM Lead": get_crm_lead_fields(),
        "CRM Deal": get_crm_deal_fields(),
    }

    created = []
    updated = []
    skipped = []

    for dt, fields in doctypes.items():
        if not frappe.db.exists("DocType", dt):
            skipped.append(f"{dt}: DocType not found")
            continue

        known_fields = get_existing_fieldnames(dt)

        for df in fields:
            upsert_custom_field(
                dt=dt,
                df=df,
                known_fields=known_fields,
                created=created,
                updated=updated,
                skipped=skipped,
            )

        frappe.clear_cache(doctype=dt)

    frappe.db.commit()

    print("---- Frappe CRM NDIS Field Install Result ----")

    if created:
        print("Created:")
        for row in created:
            print(f"  - {row}")

    if updated:
        print("Updated:")
        for row in updated:
            print(f"  - {row}")

    if skipped:
        print("Skipped safely:")
        for row in skipped:
            print(f"  - {row}")

    print("---- Done ----")


def get_existing_fieldnames(dt):
    meta = frappe.get_meta(dt, cached=False)
    return {df.fieldname for df in meta.fields if df.fieldname}


def existing_custom_field_name(dt, fieldname):
    return frappe.db.exists(
        "Custom Field",
        {
            "dt": dt,
            "fieldname": fieldname,
        },
    )


def upsert_custom_field(dt, df, known_fields, created, updated, skipped):
    fieldname = df.get("fieldname")

    if not fieldname:
        skipped.append(f"{dt}: missing fieldname")
        return

    custom_field_name = existing_custom_field_name(dt, fieldname)

    # If this custom field already exists, update it safely.
    if custom_field_name:
        custom_field = frappe.get_doc("Custom Field", custom_field_name)

        for key, value in df.items():
            setattr(custom_field, key, value)

        custom_field.save(ignore_permissions=True)
        updated.append(f"{dt}.{fieldname}")
        known_fields.add(fieldname)
        return

    # If the field exists in the DocType but is NOT a Custom Field,
    # it is a standard/core field. Do not touch it.
    if fieldname in known_fields:
        skipped.append(
            f"{dt}.{fieldname} already exists as a standard/core field. Not touched."
        )
        return

    # If insert_after points to a field that does not exist, remove insert_after.
    # This prevents layout errors if Frappe CRM changes its internal fields later.
    df = df.copy()
    insert_after = df.get("insert_after")

    if insert_after and insert_after not in known_fields:
        df.pop("insert_after", None)
        skipped.append(
            f"{dt}.{fieldname}: insert_after '{insert_after}' not found, field added without insert_after."
        )

    custom_field = frappe.get_doc(
        {
            "doctype": "Custom Field",
            "dt": dt,
            **df,
        }
    )

    custom_field.insert(ignore_permissions=True)
    created.append(f"{dt}.{fieldname}")
    known_fields.add(fieldname)


def get_crm_lead_fields():
    return [
        {
            "fieldname": "ndis_section",
            "label": "NDIS CRM",
            "fieldtype": "Section Break",
            "insert_after": "status",
        },
        {
            "fieldname": "is_ndis_participant",
            "label": "Is NDIS Participant?",
            "fieldtype": "Check",
            "insert_after": "ndis_section",
        },
        {
            "fieldname": "lead_category",
            "label": "Lead Category",
            "fieldtype": "Select",
            "options": "Participant\nFamily / Nominee\nSupport Coordinator\nPlan Manager\nProvider\nHospital\nLAC\nOther",
            "insert_after": "is_ndis_participant",
        },
        {
            "fieldname": "participant_name",
            "label": "Participant Name",
            "fieldtype": "Data",
            "insert_after": "lead_category",
        },
        {
            "fieldname": "ndis_number",
            "label": "NDIS Number",
            "fieldtype": "Data",
            "insert_after": "participant_name",
        },
        {
            "fieldname": "participant_dob",
            "label": "Participant Date of Birth",
            "fieldtype": "Date",
            "insert_after": "ndis_number",
        },
        {
            "fieldname": "enquiry_urgency",
            "label": "Enquiry Urgency",
            "fieldtype": "Select",
            "options": URGENCY_OPTIONS,
            "insert_after": "participant_dob",
        },
        {
            "fieldname": "current_living_situation",
            "label": "Current Living Situation",
            "fieldtype": "Select",
            "options": CURRENT_LIVING_OPTIONS,
            "insert_after": "enquiry_urgency",
        },
        {
            "fieldname": "has_ndis_plan",
            "label": "Has Current NDIS Plan",
            "fieldtype": "Check",
            "insert_after": "current_living_situation",
        },
        {
            "fieldname": "plan_start_date",
            "label": "Plan Start Date",
            "fieldtype": "Date",
            "insert_after": "has_ndis_plan",
        },
        {
            "fieldname": "plan_end_date",
            "label": "Plan End Date",
            "fieldtype": "Date",
            "insert_after": "plan_start_date",
        },
        {
            "fieldname": "plan_management_type",
            "label": "Plan Management Type",
            "fieldtype": "Select",
            "options": PLAN_MANAGEMENT_OPTIONS,
            "insert_after": "plan_end_date",
        },
        {
            "fieldname": "preferred_contact_method",
            "label": "Preferred Contact Method",
            "fieldtype": "Select",
            "options": "Phone\nEmail\nSMS\nIn Person\nSupport Coordinator\nFamily / Nominee",
            "insert_after": "plan_management_type",
        },
        {
            "fieldname": "consent_to_contact",
            "label": "Consent to Contact",
            "fieldtype": "Check",
            "insert_after": "preferred_contact_method",
        },
        {
            "fieldname": "consent_notes",
            "label": "Consent Notes",
            "fieldtype": "Small Text",
            "insert_after": "consent_to_contact",
        },
        {
            "fieldname": "next_follow_up_date",
            "label": "Next Follow-up Date",
            "fieldtype": "Date",
            "insert_after": "consent_notes",
        },
        {
            "fieldname": "assigned_intake_officer",
            "label": "Assigned Intake Officer",
            "fieldtype": "Link",
            "options": "User",
            "insert_after": "next_follow_up_date",
        },
        {
            "fieldname": "risk_flag",
            "label": "Risk Flag",
            "fieldtype": "Select",
            "options": "None\nLow\nMedium\nHigh\nCritical",
            "insert_after": "assigned_intake_officer",
        },
        {
            "fieldname": "risk_notes",
            "label": "Risk Notes",
            "fieldtype": "Small Text",
            "insert_after": "risk_flag",
        },
    ]


def get_crm_deal_fields():
    return [
        {
            "fieldname": "ndis_section",
            "label": "NDIS CRM",
            "fieldtype": "Section Break",
            "insert_after": "status",
        },
        {
            "fieldname": "ndis_deal_type",
            "label": "NDIS Deal Type",
            "fieldtype": "Select",
            "options": "Daily Life\nSIL\nSocial & Community Participation\nTherapy\nSupport Coordination\nBehaviour Support\nTransport\nAssistive Technology\nPlan Management\nMixed Service",
            "insert_after": "ndis_section",
        },
        {
            "fieldname": "participant_crm_lead",
            "label": "Participant CRM Lead",
            "fieldtype": "Link",
            "options": "CRM Lead",
            "insert_after": "ndis_deal_type",
        },
        {
            "fieldname": "pipeline_type",
            "label": "Pipeline Type",
            "fieldtype": "Select",
            "options": "General Intake\nSIL Placement\nDaily Life Support\nTherapy\nSupport Coordination\nBehaviour Support\nTransport\nAssistive Technology\nPlan Management",
            "insert_after": "participant_crm_lead",
        },
        {
            "fieldname": "pipeline_stage",
            "label": "Pipeline Stage",
            "fieldtype": "Select",
            "options": "New Deal\nService Need Confirmed\nDocuments Requested\nDocuments Collected\nFunding Verified\nService Agreement Sent\nService Agreement Signed\nHandover to Operations\nWon\nLost",
            "insert_after": "pipeline_type",
        },
        {
            "fieldname": "estimated_weekly_revenue",
            "label": "Estimated Weekly Revenue",
            "fieldtype": "Currency",
            "insert_after": "pipeline_stage",
        },
        {
            "fieldname": "estimated_start_date",
            "label": "Estimated Start Date",
            "fieldtype": "Date",
            "insert_after": "estimated_weekly_revenue",
        },
        {
            "fieldname": "funding_verified",
            "label": "Funding Verified",
            "fieldtype": "Check",
            "insert_after": "estimated_start_date",
        },
        {
            "fieldname": "service_agreement_required",
            "label": "Service Agreement Required",
            "fieldtype": "Check",
            "default": 1,
            "insert_after": "funding_verified",
        },
        {
            "fieldname": "service_agreement_status",
            "label": "Service Agreement Status",
            "fieldtype": "Select",
            "options": "Not Started\nPrepared\nSent\nSigned\nDeclined\nNot Required",
            "insert_after": "service_agreement_required",
        },
        {
            "fieldname": "roster_required",
            "label": "Roster Required",
            "fieldtype": "Check",
            "insert_after": "service_agreement_status",
        },
        {
            "fieldname": "clinical_review_required",
            "label": "Clinical Review Required",
            "fieldtype": "Check",
            "insert_after": "roster_required",
        },
        {
            "fieldname": "billing_setup_required",
            "label": "Billing Setup Required",
            "fieldtype": "Check",
            "default": 1,
            "insert_after": "clinical_review_required",
        },
        {
            "fieldname": "handover_status",
            "label": "Handover Status",
            "fieldtype": "Select",
            "options": "Not Ready\nReady\nHanded Over\nAccepted\nRejected",
            "insert_after": "billing_setup_required",
        },
        {
            "fieldname": "ndis_lost_reason",
            "label": "NDIS Lost Reason",
            "fieldtype": "Select",
            "options": "\nNo Funding\nNo Capacity\nNot Suitable\nChose Other Provider\nNo Response\nParticipant Declined\nOther",
            "insert_after": "handover_status",
        },
        {
            "fieldname": "competitor_provider",
            "label": "Competitor Provider",
            "fieldtype": "Data",
            "insert_after": "ndis_lost_reason",
        },
        {
            "fieldname": "next_action",
            "label": "Next Action",
            "fieldtype": "Small Text",
            "insert_after": "competitor_provider",
        },
    ]


def health_check():
    print("---- Frappe CRM NDIS Fields Health Check ----")

    for dt in ["CRM Lead", "CRM Deal"]:
        if not frappe.db.exists("DocType", dt):
            print(f"{dt}: MISSING")
            continue

        print(f"{dt}: OK")

        fields = frappe.get_all(
            "Custom Field",
            filters={"dt": dt},
            fields=["fieldname", "label", "fieldtype"],
            order_by="idx asc",
        )

        for row in fields:
            if (
                row.fieldname.startswith("ndis")
                or row.fieldname in [
                    "is_ndis_participant",
                    "lead_category",
                    "participant_name",
                    "ndis_number",
                    "participant_dob",
                    "enquiry_urgency",
                    "current_living_situation",
                    "has_ndis_plan",
                    "plan_management_type",
                    "preferred_contact_method",
                    "consent_to_contact",
                    "risk_flag",
                    "pipeline_type",
                    "pipeline_stage",
                    "estimated_weekly_revenue",
                    "estimated_start_date",
                    "funding_verified",
                    "service_agreement_status",
                    "handover_status",
                    "ndis_lost_reason",
                ]
            ):
                print(f"  - {row.fieldname} | {row.label} | {row.fieldtype}")

    print("---- End Health Check ----")
