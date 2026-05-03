import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


CRM_LEAD = "CRM Lead"
CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"


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
    ensure_required_doctypes()
    update_intake_links_to_frappe_crm()
    create_crm_custom_fields()
    ensure_crm_statuses()
    create_crm_form_scripts()
    create_intake_client_script()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 2 for Frappe CRM installed successfully.")


def ensure_required_doctypes():
    required = [
        CRM_LEAD,
        CRM_DEAL,
        "CRM Lead Status",
        "CRM Deal Status",
        "CRM Form Script",
        "CRM Organization",
        INTAKE,
        "NDIS Service Interest",
        "NDIS Service Line",
    ]

    missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]

    if missing:
        frappe.throw("Missing required DocTypes: " + ", ".join(missing))

    print("Required Frappe CRM and NDIS CRM DocTypes found.")


def update_docfield(parent, fieldname, **updates):
    field_id = frappe.db.get_value(
        "DocField",
        {
            "parent": parent,
            "fieldname": fieldname,
        },
        "name"
    )

    if not field_id:
        print(f"DocField not found: {parent}.{fieldname}")
        return

    for key, value in updates.items():
        frappe.db.set_value("DocField", field_id, key, value)

    print(f"Updated DocField: {parent}.{fieldname}")


def update_intake_links_to_frappe_crm():
    update_docfield(
        INTAKE,
        "participant_lead",
        options=CRM_LEAD,
        label="CRM Lead"
    )

    update_docfield(
        INTAKE,
        "opportunity",
        options=CRM_DEAL,
        label="CRM Deal"
    )

    frappe.clear_cache(doctype=INTAKE)


def create_crm_custom_fields():
    lead_fields = [
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
            "fieldname": "primary_disability",
            "label": "Primary Disability",
            "fieldtype": "Data",
            "insert_after": "participant_dob",
        },
        {
            "fieldname": "enquiry_urgency",
            "label": "Enquiry Urgency",
            "fieldtype": "Select",
            "options": URGENCY_OPTIONS,
            "insert_after": "primary_disability",
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
            "fieldname": "support_coordinator_name",
            "label": "Support Coordinator Name",
            "fieldtype": "Data",
            "insert_after": "plan_management_type",
        },
        {
            "fieldname": "support_coordinator_email",
            "label": "Support Coordinator Email",
            "fieldtype": "Data",
            "options": "Email",
            "insert_after": "support_coordinator_name",
        },
        {
            "fieldname": "plan_manager_name",
            "label": "Plan Manager Name",
            "fieldtype": "Data",
            "insert_after": "support_coordinator_email",
        },
        {
            "fieldname": "preferred_contact_method",
            "label": "Preferred Contact Method",
            "fieldtype": "Select",
            "options": "Phone\nEmail\nSMS\nIn Person\nSupport Coordinator\nFamily / Nominee",
            "insert_after": "plan_manager_name",
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
        {
            "fieldname": "ndis_service_interests",
            "label": "NDIS Service Interests",
            "fieldtype": "Table",
            "options": "NDIS Service Interest",
            "insert_after": "risk_notes",
        },
    ]

    deal_fields = [
        {
            "fieldname": "ndis_section",
            "label": "NDIS CRM",
            "fieldtype": "Section Break",
            "insert_after": "status",
        },
        {
            "fieldname": "opportunity_type_ndis",
            "label": "NDIS Deal Type",
            "fieldtype": "Select",
            "options": "Daily Life\nSIL\nSocial & Community Participation\nTherapy\nSupport Coordination\nBehaviour Support\nTransport\nAssistive Technology\nPlan Management\nMixed Service",
            "insert_after": "ndis_section",
        },
        {
            "fieldname": "participant_customer",
            "label": "Participant Customer",
            "fieldtype": "Link",
            "options": "Customer",
            "insert_after": "opportunity_type_ndis",
        },
        {
            "fieldname": "pipeline_type",
            "label": "Pipeline Type",
            "fieldtype": "Select",
            "options": "General Intake\nSIL Placement\nDaily Life Support\nTherapy\nSupport Coordination\nBehaviour Support\nTransport\nAssistive Technology\nPlan Management",
            "insert_after": "participant_customer",
        },
        {
            "fieldname": "pipeline_stage",
            "label": "Pipeline Stage",
            "fieldtype": "Select",
            "options": "New Opportunity\nService Need Confirmed\nDocuments Requested\nDocuments Collected\nFunding Verified\nService Agreement Sent\nService Agreement Signed\nHandover to Operations\nWon\nLost",
            "insert_after": "pipeline_type",
        },
        {
            "fieldname": "participant_name",
            "label": "Participant Name",
            "fieldtype": "Data",
            "insert_after": "pipeline_stage",
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
            "fieldname": "plan_start_date",
            "label": "Plan Start Date",
            "fieldtype": "Date",
            "insert_after": "participant_dob",
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
            "fieldname": "estimated_weekly_revenue",
            "label": "Estimated Weekly Revenue",
            "fieldtype": "Currency",
            "insert_after": "plan_management_type",
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
            "default": "1",
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
            "fieldname": "required_documents_collected",
            "label": "Required Documents Collected",
            "fieldtype": "Check",
            "insert_after": "service_agreement_status",
        },
        {
            "fieldname": "roster_required",
            "label": "Roster Required",
            "fieldtype": "Check",
            "insert_after": "required_documents_collected",
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
            "default": "1",
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
            "fieldname": "next_action",
            "label": "Next Action",
            "fieldtype": "Small Text",
            "insert_after": "handover_status",
        },
        {
            "fieldname": "ndis_service_interests",
            "label": "NDIS Service Interests",
            "fieldtype": "Table",
            "options": "NDIS Service Interest",
            "insert_after": "next_action",
        },
    ]

    create_custom_fields(
        {
            CRM_LEAD: lead_fields,
            CRM_DEAL: deal_fields,
        },
        update=True,
    )

    print("Created / updated NDIS custom fields on CRM Lead and CRM Deal.")


def ensure_status(doctype, status_field, status_name, status_type, position, color="gray", probability=None):
    if frappe.db.exists(doctype, status_name):
        doc = frappe.get_doc(doctype, status_name)
        changed = False

        if doc.get("type") != status_type:
            doc.type = status_type
            changed = True

        if doc.get("position") != position:
            doc.position = position
            changed = True

        if doc.get("color") != color:
            doc.color = color
            changed = True

        if probability is not None and doc.get("probability") != probability:
            doc.probability = probability
            changed = True

        if changed:
            doc.save(ignore_permissions=True)
            print(f"Updated status: {doctype} - {status_name}")
        else:
            print(f"Status already exists: {doctype} - {status_name}")

        return

    data = {
        "doctype": doctype,
        status_field: status_name,
        "type": status_type,
        "position": position,
        "color": color,
    }

    if probability is not None:
        data["probability"] = probability

    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)

    print(f"Created status: {doctype} - {status_name}")


def ensure_crm_statuses():
    lead_statuses = [
        ("New Enquiry", "Open", 10, "blue"),
        ("Contact Attempted", "Ongoing", 20, "cyan"),
        ("Contacted", "Ongoing", 30, "teal"),
        ("Intake Started", "Ongoing", 40, "orange"),
        ("Waiting Documents", "On Hold", 50, "amber"),
        ("Funding / Suitability Review", "Ongoing", 60, "violet"),
        ("Qualified", "Won", 70, "green"),
        ("Converted", "Won", 80, "green"),
        ("Not Suitable", "Lost", 90, "red"),
        ("No Response", "Lost", 100, "gray"),
        ("Duplicate", "Lost", 110, "gray"),
        ("Declined by Participant", "Lost", 120, "red"),
        ("No Funding", "Lost", 130, "red"),
        ("Provider Capacity Issue", "On Hold", 140, "orange"),
    ]

    for status_name, status_type, position, color in lead_statuses:
        ensure_status(
            doctype="CRM Lead Status",
            status_field="lead_status",
            status_name=status_name,
            status_type=status_type,
            position=position,
            color=color,
        )

    deal_statuses = [
        ("New Opportunity", "Open", 10, "blue", 5),
        ("Service Need Confirmed", "Ongoing", 20, "cyan", 15),
        ("Documents Requested", "Ongoing", 30, "orange", 25),
        ("Documents Collected", "Ongoing", 40, "teal", 35),
        ("Funding Verified", "Ongoing", 50, "violet", 50),
        ("Service Agreement Sent", "Ongoing", 60, "amber", 65),
        ("Service Agreement Signed", "Ongoing", 70, "green", 80),
        ("Handover to Operations", "Ongoing", 80, "purple", 90),
        ("Won / Active Client", "Won", 90, "green", 100),
        ("Lost", "Lost", 100, "red", 0),
    ]

    for status_name, status_type, position, color, probability in deal_statuses:
        ensure_status(
            doctype="CRM Deal Status",
            status_field="deal_status",
            status_name=status_name,
            status_type=status_type,
            position=position,
            color=color,
            probability=probability,
        )


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


def create_crm_form_scripts():
    lead_script = r'''
function setupForm({ doc, call, router, createToast }) {
  return {
    actions: [
      {
        label: "Create NDIS Intake",
        onClick: () => {
          call("ndis_crm.phase2_api.create_intake_from_crm_lead", {
            lead: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "NDIS Intake Created" : "Existing NDIS Intake Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-participant-intake/${data.name}`, "_blank")
            } else {
              createToast({
                title: "Could not create NDIS Intake",
                icon: "x",
                iconClasses: "text-red-600",
              })
            }
          })
        }
      },
      {
        label: "Create CRM Deal",
        onClick: () => {
          call("ndis_crm.phase2_api.create_crm_deal_from_lead", {
            lead: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "CRM Deal Created" : "Existing CRM Deal Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/crm/deals/${data.name}`, "_blank")
            } else {
              createToast({
                title: "Could not create CRM Deal",
                icon: "x",
                iconClasses: "text-red-600",
              })
            }
          })
        }
      }
    ]
  }
}
'''.strip()

    deal_script = r'''
function setupForm({ doc, createToast }) {
  return {
    actions: [
      {
        label: "Open Linked CRM Lead",
        onClick: () => {
          if (doc.lead) {
            window.open(`/crm/leads/${doc.lead}`, "_blank")
          } else {
            createToast({
              title: "No CRM Lead linked to this Deal",
              icon: "info",
            })
          }
        }
      }
    ]
  }
}
'''.strip()

    upsert_doc(
        "CRM Form Script",
        "NDIS CRM Lead Actions",
        {
            "dt": "CRM Lead",
            "view": "Form",
            "enabled": 1,
            "is_standard": 0,
            "script": lead_script,
        },
    )

    upsert_doc(
        "CRM Form Script",
        "NDIS CRM Deal Actions",
        {
            "dt": "CRM Deal",
            "view": "Form",
            "enabled": 1,
            "is_standard": 0,
            "script": deal_script,
        },
    )


def create_intake_client_script():
    script = r'''
frappe.ui.form.on("NDIS Participant Intake", {
    refresh(frm) {
        if (!frm.is_new()) {
            frm.add_custom_button(__("Create CRM Deal"), function () {
                frappe.call({
                    method: "ndis_crm.phase2_api.create_crm_deal_from_intake",
                    args: {
                        intake: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Creating CRM Deal...")
                }).then((r) => {
                    if (r.message && r.message.name) {
                        frappe.show_alert({
                            message: r.message.created ? __("CRM Deal created") : __("Existing CRM Deal found"),
                            indicator: "green"
                        });

                        frm.reload_doc();

                        frappe.set_route("Form", "CRM Deal", r.message.name);
                    }
                });
            }, __("Actions"));
        }
    }
});
'''.strip()

    if frappe.db.exists("DocType", "Client Script"):
        upsert_doc(
            "Client Script",
            "NDIS Participant Intake Actions",
            {
                "dt": "NDIS Participant Intake",
                "view": "Form",
                "enabled": 1,
                "script": script,
            },
        )
    else:
        print("Client Script DocType not found. Skipped NDIS Participant Intake client script.")
