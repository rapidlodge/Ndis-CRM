import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_LEAD = "CRM Lead"
CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"

DOCUMENT_TYPE = "NDIS Document Type"
DOCUMENT_RULE = "NDIS Service Document Rule"
DOCUMENT_REQUEST = "NDIS Document Request"


def install():
    ensure_required_doctypes()
    create_document_doctypes()
    create_document_custom_fields()
    seed_document_types()
    seed_service_document_rules()
    create_form_scripts()
    frappe.clear_cache()
    frappe.db.commit()
    print("NDIS CRM Phase 3 document collection installed successfully.")


def ensure_required_doctypes():
    required = [
        CRM_LEAD,
        CRM_DEAL,
        INTAKE,
        "NDIS Service Line",
        "NDIS Service Interest",
        "CRM Form Script",
    ]

    missing = [dt for dt in required if not frappe.db.exists("DocType", dt)]

    if missing:
        frappe.throw("Missing required DocTypes: " + ", ".join(missing))

    print("Required Phase 3 DocTypes found.")


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
            "share": 1,
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
            "share": 1,
        },
        {
            "role": "NDIS Intake Officer",
            "read": 1,
            "write": 1,
            "create": 1,
            "email": 1,
            "print": 1,
            "report": 1,
        },
        {
            "role": "NDIS Service Manager",
            "read": 1,
            "write": 1,
            "create": 1,
            "email": 1,
            "print": 1,
            "report": 1,
        },
        {
            "role": "NDIS Plan Management Officer",
            "read": 1,
            "write": 1,
            "create": 1,
            "email": 1,
            "print": 1,
            "report": 1,
        },
        {
            "role": "NDIS CRM Read Only",
            "read": 1,
            "export": 1,
            "print": 1,
            "report": 1,
        },
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


def create_document_doctypes():
    create_ndis_document_type()
    create_ndis_service_document_rule()
    create_ndis_document_request()


def create_ndis_document_type():
    fields = [
        make_field("Document Type Details", "document_type_details_section", "Section Break"),
        make_field("Document Type Name", "document_type_name", "Data", reqd=1, unique=1, in_list_view=1),
        make_field("Document Code", "document_code", "Data", unique=1, in_list_view=1),
        make_field("Document Category", "document_category", "Select", options="Identity\nNDIS Plan\nConsent\nClinical\nRisk\nService Agreement\nFinance\nSIL\nTransport\nAssistive Technology\nOther", in_list_view=1),
        make_field("Active", "active", "Check", default=1, in_list_view=1),

        make_field("Control Rules", "control_rules_column", "Column Break"),
        make_field("Requires Review", "requires_review", "Check", default=1),
        make_field("Requires Expiry Date", "requires_expiry_date", "Check", default=0),
        make_field("Default Mandatory", "default_mandatory", "Check", default=1),

        make_field("Description", "description_section", "Section Break"),
        make_field("Description", "description", "Small Text"),
    ]

    create_doctype_if_missing(
        name=DOCUMENT_TYPE,
        fields=fields,
        autoname="field:document_type_name",
        title_field="document_type_name",
    )


def create_ndis_service_document_rule():
    fields = [
        make_field("Rule Details", "rule_details_section", "Section Break"),
        make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
        make_field("Document Type", "document_type", "Link", options=DOCUMENT_TYPE, reqd=1, in_list_view=1),
        make_field("Mandatory", "mandatory", "Check", default=1, in_list_view=1),
        make_field("Required Before", "required_before", "Select", options="Intake Qualification\nFunding Verification\nService Agreement Sent\nOperations Handover", default="Service Agreement Sent", in_list_view=1),
        make_field("Auto Request", "auto_request", "Check", default=1),
        make_field("Active", "active", "Check", default=1, in_list_view=1),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=DOCUMENT_RULE,
        fields=fields,
        autoname="hash",
        title_field="document_type",
    )


def create_ndis_document_request():
    fields = [
        make_field("Series", "naming_series", "Select", options="NDIS-DOC-.YYYY.-.#####", default="NDIS-DOC-.YYYY.-.#####", reqd=1),

        make_field("Source Links", "source_links_section", "Section Break"),
        make_field("CRM Lead", "crm_lead", "Link", options=CRM_LEAD, in_list_view=1),
        make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE, in_list_view=1),
        make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
        make_field("Participant Customer", "participant_customer", "Link", options="Customer"),

        make_field("Source Reference", "source_reference_column", "Column Break"),
        make_field("Source DocType", "source_doctype", "Data", read_only=1),
        make_field("Source Name", "source_name", "Data", read_only=1),

        make_field("Document Details", "document_details_section", "Section Break"),
        make_field("Document Type", "document_type", "Link", options=DOCUMENT_TYPE, reqd=1, in_list_view=1),
        make_field("Document Type Name", "document_type_name", "Data", fetch_from="document_type.document_type_name", read_only=1, in_list_view=1),
        make_field("Required?", "is_required", "Check", default=1, in_list_view=1),
        make_field("Required Before", "required_before", "Select", options="Intake Qualification\nFunding Verification\nService Agreement Sent\nOperations Handover", in_list_view=1),
        make_field("Required For Services", "required_for_services", "Small Text"),

        make_field("Status Details", "status_details_section", "Section Break"),
        make_field("Status", "status", "Select", options="Requested\nReceived\nReviewed\nAccepted\nRejected\nExpired\nNot Required", default="Requested", in_list_view=1),
        make_field("Requested Date", "requested_date", "Date", default="Today"),
        make_field("Due Date", "due_date", "Date"),
        make_field("Received Date", "received_date", "Date"),
        make_field("Expiry Date", "expiry_date", "Date"),

        make_field("File and Review", "file_review_section", "Section Break"),
        make_field("Uploaded File", "uploaded_file", "Attach", in_list_view=1),
        make_field("Reviewed By", "reviewed_by", "Link", options="User"),
        make_field("Reviewed On", "reviewed_on", "Datetime"),
        make_field("Review Notes", "review_notes", "Small Text"),
        make_field("Missing / Rejection Reason", "missing_reason", "Small Text"),

        make_field("Notes", "notes_section", "Section Break"),
        make_field("Notes", "notes", "Small Text"),
    ]

    create_doctype_if_missing(
        name=DOCUMENT_REQUEST,
        fields=fields,
        autoname="naming_series:",
        title_field="document_type_name",
    )


def create_document_custom_fields():
    shared_fields = [
        {
            "fieldname": "document_control_section",
            "label": "NDIS Document Control",
            "fieldtype": "Section Break",
            "insert_after": "ndis_service_interests",
        },
        {
            "fieldname": "required_documents_generated",
            "label": "Required Documents Generated",
            "fieldtype": "Check",
            "insert_after": "document_control_section",
        },
        {
            "fieldname": "document_completion_percent",
            "label": "Document Completion %",
            "fieldtype": "Percent",
            "read_only": 1,
            "insert_after": "required_documents_generated",
        },
        {
            "fieldname": "document_summary",
            "label": "Document Summary",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "document_completion_percent",
        },
    ]

    intake_fields = [
        {
            "fieldname": "document_control_section",
            "label": "NDIS Document Control",
            "fieldtype": "Section Break",
            "insert_after": "service_interests",
        },
        {
            "fieldname": "required_documents_generated",
            "label": "Required Documents Generated",
            "fieldtype": "Check",
            "insert_after": "document_control_section",
        },
        {
            "fieldname": "document_completion_percent",
            "label": "Document Completion %",
            "fieldtype": "Percent",
            "read_only": 1,
            "insert_after": "required_documents_generated",
        },
        {
            "fieldname": "document_summary",
            "label": "Document Summary",
            "fieldtype": "Small Text",
            "read_only": 1,
            "insert_after": "document_completion_percent",
        },
    ]

    create_custom_fields(
        {
            CRM_LEAD: shared_fields,
            CRM_DEAL: shared_fields,
            INTAKE: intake_fields,
        },
        update=True,
    )

    print("Created / updated document control custom fields.")


def upsert_document_type(row):
    existing = frappe.db.get_value(DOCUMENT_TYPE, {"document_code": row["document_code"]}, "name")

    if existing:
        doc = frappe.get_doc(DOCUMENT_TYPE, existing)
        for key, value in row.items():
            doc.set(key, value)
        doc.save(ignore_permissions=True)
        print(f"Updated document type: {row['document_type_name']}")
    else:
        doc = frappe.get_doc({
            "doctype": DOCUMENT_TYPE,
            **row,
        })
        doc.insert(ignore_permissions=True)
        print(f"Inserted document type: {row['document_type_name']}")


def seed_document_types():
    rows = [
        {"document_type_name": "NDIS Plan", "document_code": "NDIS_PLAN", "document_category": "NDIS Plan", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Consent to Contact / Information Sharing", "document_code": "CONSENT_CONTACT", "document_category": "Consent", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Service Agreement", "document_code": "SERVICE_AGREEMENT", "document_category": "Service Agreement", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Photo ID / Identity Evidence", "document_code": "PHOTO_ID", "document_category": "Identity", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Participant Goals / About Me", "document_code": "PARTICIPANT_GOALS", "document_category": "NDIS Plan", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Support Coordinator Authority", "document_code": "SC_AUTHORITY", "document_category": "Consent", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Plan Manager Details", "document_code": "PLAN_MANAGER_DETAILS", "document_category": "Finance", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Risk Assessment", "document_code": "RISK_ASSESSMENT", "document_category": "Risk", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Behaviour Support Plan", "document_code": "BSP", "document_category": "Clinical", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Restrictive Practice Authorisation", "document_code": "RP_AUTHORISATION", "document_category": "Risk", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Medication Chart", "document_code": "MEDICATION_CHART", "document_category": "Clinical", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Manual Handling Plan", "document_code": "MANUAL_HANDLING_PLAN", "document_category": "Clinical", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Functional Capacity Assessment", "document_code": "FCA", "document_category": "Clinical", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Therapy Referral", "document_code": "THERAPY_REFERRAL", "document_category": "Clinical", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 1, "active": 1},
        {"document_type_name": "OT Report", "document_code": "OT_REPORT", "document_category": "Clinical", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Transport Schedule", "document_code": "TRANSPORT_SCHEDULE", "document_category": "Transport", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Assistive Technology Assessment", "document_code": "AT_ASSESSMENT", "document_category": "Assistive Technology", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Assistive Technology Quote", "document_code": "AT_QUOTE", "document_category": "Assistive Technology", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 1, "active": 1},
        {"document_type_name": "SIL Roster / Support Model", "document_code": "SIL_ROSTER_MODEL", "document_category": "SIL", "requires_review": 1, "requires_expiry_date": 1, "default_mandatory": 1, "active": 1},
        {"document_type_name": "Hospital Discharge Summary", "document_code": "HOSPITAL_DISCHARGE", "document_category": "Clinical", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 0, "active": 1},
        {"document_type_name": "Incident History", "document_code": "INCIDENT_HISTORY", "document_category": "Risk", "requires_review": 1, "requires_expiry_date": 0, "default_mandatory": 0, "active": 1},
    ]

    for row in rows:
        upsert_document_type(row)


def get_service_line_by_code(service_code):
    return frappe.db.get_value("NDIS Service Line", {"service_code": service_code}, "name")


def get_document_type_by_code(document_code):
    return frappe.db.get_value(DOCUMENT_TYPE, {"document_code": document_code}, "name")


def upsert_rule(service_code, document_code, mandatory=1, required_before="Service Agreement Sent", auto_request=1, active=1, notes=None):
    service_line = get_service_line_by_code(service_code)
    document_type = get_document_type_by_code(document_code)

    if not service_line:
        print(f"Skipped rule. Service code missing: {service_code}")
        return

    if not document_type:
        print(f"Skipped rule. Document code missing: {document_code}")
        return

    existing = frappe.db.get_value(
        DOCUMENT_RULE,
        {
            "service_line": service_line,
            "document_type": document_type,
        },
        "name",
    )

    data = {
        "service_line": service_line,
        "document_type": document_type,
        "mandatory": mandatory,
        "required_before": required_before,
        "auto_request": auto_request,
        "active": active,
        "notes": notes,
    }

    if existing:
        doc = frappe.get_doc(DOCUMENT_RULE, existing)
        for key, value in data.items():
            doc.set(key, value)
        doc.save(ignore_permissions=True)
        print(f"Updated rule: {service_code} -> {document_code}")
    else:
        doc = frappe.get_doc({
            "doctype": DOCUMENT_RULE,
            **data,
        })
        doc.insert(ignore_permissions=True)
        print(f"Inserted rule: {service_code} -> {document_code}")


def add_common_rules(service_code):
    upsert_rule(service_code, "NDIS_PLAN", mandatory=1, required_before="Funding Verification")
    upsert_rule(service_code, "CONSENT_CONTACT", mandatory=1, required_before="Intake Qualification")
    upsert_rule(service_code, "SERVICE_AGREEMENT", mandatory=1, required_before="Service Agreement Sent")


def seed_service_document_rules():
    service_codes = [
        "DAILY_LIFE",
        "SIL",
        "COMMUNITY_PARTICIPATION",
        "THERAPY",
        "SUPPORT_COORDINATION",
        "BEHAVIOUR_SUPPORT",
        "TRANSPORT",
        "ASSISTIVE_TECHNOLOGY",
        "PLAN_MANAGEMENT",
    ]

    for service_code in service_codes:
        add_common_rules(service_code)

    # Assistance with Daily Life
    upsert_rule("DAILY_LIFE", "RISK_ASSESSMENT", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("DAILY_LIFE", "MEDICATION_CHART", mandatory=0, required_before="Operations Handover")
    upsert_rule("DAILY_LIFE", "MANUAL_HANDLING_PLAN", mandatory=0, required_before="Operations Handover")

    # SIL
    upsert_rule("SIL", "RISK_ASSESSMENT", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("SIL", "BSP", mandatory=0, required_before="Service Agreement Sent")
    upsert_rule("SIL", "RP_AUTHORISATION", mandatory=0, required_before="Service Agreement Sent")
    upsert_rule("SIL", "MEDICATION_CHART", mandatory=0, required_before="Operations Handover")
    upsert_rule("SIL", "MANUAL_HANDLING_PLAN", mandatory=0, required_before="Operations Handover")
    upsert_rule("SIL", "SIL_ROSTER_MODEL", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("SIL", "HOSPITAL_DISCHARGE", mandatory=0, required_before="Operations Handover")

    # Community Participation
    upsert_rule("COMMUNITY_PARTICIPATION", "RISK_ASSESSMENT", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("COMMUNITY_PARTICIPATION", "TRANSPORT_SCHEDULE", mandatory=0, required_before="Operations Handover")

    # Therapy
    upsert_rule("THERAPY", "THERAPY_REFERRAL", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("THERAPY", "FCA", mandatory=0, required_before="Operations Handover")
    upsert_rule("THERAPY", "OT_REPORT", mandatory=0, required_before="Operations Handover")

    # Support Coordination
    upsert_rule("SUPPORT_COORDINATION", "SC_AUTHORITY", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("SUPPORT_COORDINATION", "PARTICIPANT_GOALS", mandatory=0, required_before="Operations Handover")

    # Behaviour Support
    upsert_rule("BEHAVIOUR_SUPPORT", "RISK_ASSESSMENT", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("BEHAVIOUR_SUPPORT", "BSP", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("BEHAVIOUR_SUPPORT", "RP_AUTHORISATION", mandatory=0, required_before="Service Agreement Sent")
    upsert_rule("BEHAVIOUR_SUPPORT", "INCIDENT_HISTORY", mandatory=0, required_before="Operations Handover")

    # Transport
    upsert_rule("TRANSPORT", "TRANSPORT_SCHEDULE", mandatory=1, required_before="Service Agreement Sent")

    # Assistive Technology
    upsert_rule("ASSISTIVE_TECHNOLOGY", "AT_ASSESSMENT", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("ASSISTIVE_TECHNOLOGY", "AT_QUOTE", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("ASSISTIVE_TECHNOLOGY", "OT_REPORT", mandatory=0, required_before="Operations Handover")

    # Plan Management
    upsert_rule("PLAN_MANAGEMENT", "PLAN_MANAGER_DETAILS", mandatory=1, required_before="Service Agreement Sent")
    upsert_rule("PLAN_MANAGEMENT", "SC_AUTHORITY", mandatory=0, required_before="Operations Handover")


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


def create_form_scripts():
    lead_script = r'''
function setupForm({ doc, call, createToast }) {
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
            }
          })
        }
      },
      {
        label: "Generate Document Requests",
        onClick: () => {
          call("ndis_crm.phase3_documents.generate_document_requests_for_crm_lead", {
            lead: doc.name
          }).then((data) => {
            createToast({
              title: data && data.message ? data.message : "Document requests generated",
              icon: "check",
              iconClasses: "text-green-600",
            })
            window.open(`/app/ndis-document-request?crm_lead=${encodeURIComponent(doc.name)}`, "_blank")
          })
        }
      },
      {
        label: "Open Document Requests",
        onClick: () => {
          window.open(`/app/ndis-document-request?crm_lead=${encodeURIComponent(doc.name)}`, "_blank")
        }
      }
    ]
  }
}
'''.strip()

    deal_script = r'''
function setupForm({ doc, call, createToast }) {
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
      },
      {
        label: "Generate Document Requests",
        onClick: () => {
          call("ndis_crm.phase3_documents.generate_document_requests_for_crm_deal", {
            deal: doc.name
          }).then((data) => {
            createToast({
              title: data && data.message ? data.message : "Document requests generated",
              icon: "check",
              iconClasses: "text-green-600",
            })
            window.open(`/app/ndis-document-request?crm_deal=${encodeURIComponent(doc.name)}`, "_blank")
          })
        }
      },
      {
        label: "Open Document Requests",
        onClick: () => {
          window.open(`/app/ndis-document-request?crm_deal=${encodeURIComponent(doc.name)}`, "_blank")
        }
      }
    ]
  }
}
'''.strip()

    intake_script = r'''
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

            frm.add_custom_button(__("Generate Document Requests"), function () {
                frappe.call({
                    method: "ndis_crm.phase3_documents.generate_document_requests_for_intake",
                    args: {
                        intake: frm.doc.name
                    },
                    freeze: true,
                    freeze_message: __("Generating document requests...")
                }).then((r) => {
                    if (r.message) {
                        frappe.show_alert({
                            message: r.message.message || __("Document requests generated"),
                            indicator: "green"
                        });

                        frm.reload_doc();

                        frappe.route_options = {
                            participant_intake: frm.doc.name
                        };
                        frappe.set_route("List", "NDIS Document Request");
                    }
                });
            }, __("Actions"));

            frm.add_custom_button(__("Open Document Requests"), function () {
                frappe.route_options = {
                    participant_intake: frm.doc.name
                };
                frappe.set_route("List", "NDIS Document Request");
            }, __("Actions"));
        }
    }
});
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

    if frappe.db.exists("DocType", "Client Script"):
        upsert_doc(
            "Client Script",
            "NDIS Participant Intake Actions",
            {
                "dt": "NDIS Participant Intake",
                "view": "Form",
                "enabled": 1,
                "script": intake_script,
            },
        )
