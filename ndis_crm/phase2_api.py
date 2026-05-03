import frappe
from frappe import _


CRM_LEAD = "CRM Lead"
CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"


ALLOWED_ROLES = {
    "System Manager",
    "Sales Manager",
    "Sales User",
    "NDIS CRM Manager",
    "NDIS Intake Officer",
    "NDIS Service Manager",
}


def _check_role():
    user_roles = set(frappe.get_roles())
    if not user_roles.intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this NDIS CRM action."))


def _field_exists(doctype, fieldname):
    return bool(
        frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
        or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
    )


def _get(doc, fieldname, default=None):
    if _field_exists(doc.doctype, fieldname):
        return doc.get(fieldname)
    return default


def _set_if_field(doc, fieldname, value):
    if value is not None and _field_exists(doc.doctype, fieldname):
        doc.set(fieldname, value)


def _full_name(doc):
    participant_name = _get(doc, "participant_name")
    if participant_name:
        return participant_name

    lead_name = _get(doc, "lead_name")
    if lead_name:
        return lead_name

    first = _get(doc, "first_name") or ""
    last = _get(doc, "last_name") or ""
    name = f"{first} {last}".strip()
    return name or doc.name


def _split_name(full_name):
    parts = (full_name or "").strip().split()
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _copy_service_interests(source_doc, source_field, target_doc, target_field):
    if not _field_exists(source_doc.doctype, source_field):
        return

    if not _field_exists(target_doc.doctype, target_field):
        return

    for row in source_doc.get(source_field) or []:
        target_doc.append(target_field, {
            "service_line": row.get("service_line"),
            "priority": row.get("priority"),
            "required_start_date": row.get("required_start_date"),
            "current_provider": row.get("current_provider"),
            "reason_for_change": row.get("reason_for_change"),
            "funding_available": row.get("funding_available"),
            "assessment_required": row.get("assessment_required"),
            "documents_required": row.get("documents_required"),
            "notes": row.get("notes"),
        })


def _get_existing_intake_for_lead(lead):
    if not frappe.db.exists("DocType", INTAKE):
        return None

    if not _field_exists(INTAKE, "participant_lead"):
        return None

    return frappe.db.get_value(INTAKE, {"participant_lead": lead}, "name")


def _get_existing_deal_for_lead(lead):
    if not frappe.db.exists("DocType", CRM_DEAL):
        return None

    return frappe.db.get_value(CRM_DEAL, {"lead": lead}, "name")


def _get_or_create_crm_organization(participant_name):
    """
    Frappe CRM Deal is designed around Organization.
    For NDIS participants, we create a simple CRM Organization record
    so the Deal page has a proper visible title and pipeline card.
    """
    if not participant_name:
        participant_name = "NDIS Participant"

    base_name = f"NDIS - {participant_name}".strip()
    base_name = base_name[:130]

    existing = frappe.db.get_value("CRM Organization", {"organization_name": base_name}, "name")
    if existing:
        return existing

    org = frappe.get_doc({
        "doctype": "CRM Organization",
        "organization_name": base_name,
    })
    org.insert(ignore_permissions=True)
    return org.name


@frappe.whitelist()
def create_intake_from_crm_lead(lead):
    """
    Create NDIS Participant Intake from CRM Lead.
    Safe to run multiple times. If intake already exists, returns it.
    """
    _check_role()

    if not lead:
        frappe.throw(_("CRM Lead is required."))

    if not frappe.db.exists(CRM_LEAD, lead):
        frappe.throw(_("CRM Lead {0} was not found.").format(lead))

    existing = _get_existing_intake_for_lead(lead)
    if existing:
        return {
            "doctype": INTAKE,
            "name": existing,
            "created": False,
            "message": "Existing NDIS Participant Intake returned.",
        }

    lead_doc = frappe.get_doc(CRM_LEAD, lead)
    participant_name = _full_name(lead_doc)

    intake = frappe.new_doc(INTAKE)

    _set_if_field(intake, "participant_lead", lead_doc.name)
    _set_if_field(intake, "status", "Intake Started")
    _set_if_field(intake, "intake_officer", frappe.session.user)
    _set_if_field(intake, "participant_name", participant_name)
    _set_if_field(intake, "ndis_number", _get(lead_doc, "ndis_number"))
    _set_if_field(intake, "date_of_birth", _get(lead_doc, "participant_dob"))
    _set_if_field(intake, "primary_disability", _get(lead_doc, "primary_disability"))
    _set_if_field(intake, "preferred_contact_method", _get(lead_doc, "preferred_contact_method"))
    _set_if_field(intake, "consent_to_contact", _get(lead_doc, "consent_to_contact"))
    _set_if_field(intake, "consent_notes", _get(lead_doc, "consent_notes"))
    _set_if_field(intake, "has_current_ndis_plan", _get(lead_doc, "has_ndis_plan"))
    _set_if_field(intake, "plan_start_date", _get(lead_doc, "plan_start_date"))
    _set_if_field(intake, "plan_end_date", _get(lead_doc, "plan_end_date"))
    _set_if_field(intake, "plan_management_type", _get(lead_doc, "plan_management_type"))
    _set_if_field(intake, "support_coordinator_name", _get(lead_doc, "support_coordinator_name"))
    _set_if_field(intake, "support_coordinator_email", _get(lead_doc, "support_coordinator_email"))
    _set_if_field(intake, "plan_manager_name", _get(lead_doc, "plan_manager_name"))
    _set_if_field(intake, "current_living_situation", _get(lead_doc, "current_living_situation"))
    _set_if_field(intake, "enquiry_urgency", _get(lead_doc, "enquiry_urgency"))
    _set_if_field(intake, "risk_level", _get(lead_doc, "risk_flag"))
    _set_if_field(intake, "intake_notes", f"Created from CRM Lead: {lead_doc.name}")

    _copy_service_interests(
        source_doc=lead_doc,
        source_field="ndis_service_interests",
        target_doc=intake,
        target_field="service_interests",
    )

    intake.insert(ignore_permissions=False)

    if _field_exists(CRM_LEAD, "status"):
        lead_doc.status = "Intake Started"
        lead_doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": INTAKE,
        "name": intake.name,
        "created": True,
        "message": "NDIS Participant Intake created successfully.",
    }


@frappe.whitelist()
def create_crm_deal_from_lead(lead):
    """
    Create CRM Deal from a qualified CRM Lead.
    This first creates/gets NDIS Participant Intake, then creates CRM Deal.
    """
    _check_role()

    if not lead:
        frappe.throw(_("CRM Lead is required."))

    lead_doc = frappe.get_doc(CRM_LEAD, lead)

    if lead_doc.status != "Qualified":
        frappe.throw(_("CRM Lead must be marked as Qualified before creating a CRM Deal."))

    intake_result = create_intake_from_crm_lead(lead)
    intake_name = intake_result.get("name")

    intake_doc = frappe.get_doc(INTAKE, intake_name)

    if _field_exists(INTAKE, "status") and intake_doc.status != "Qualified":
        intake_doc.status = "Qualified"
        intake_doc.save(ignore_permissions=True)

    return create_crm_deal_from_intake(intake_name)


@frappe.whitelist()
def create_crm_deal_from_intake(intake):
    """
    Create CRM Deal from NDIS Participant Intake.
    Safe to run multiple times. If deal already exists, returns it.
    """
    _check_role()

    if not intake:
        frappe.throw(_("NDIS Participant Intake is required."))

    if not frappe.db.exists(INTAKE, intake):
        frappe.throw(_("NDIS Participant Intake {0} was not found.").format(intake))

    intake_doc = frappe.get_doc(INTAKE, intake)

    if _field_exists(INTAKE, "opportunity") and intake_doc.get("opportunity"):
        return {
            "doctype": CRM_DEAL,
            "name": intake_doc.get("opportunity"),
            "created": False,
            "message": "Existing CRM Deal returned.",
        }

    participant_lead = _get(intake_doc, "participant_lead")

    if participant_lead:
        existing_deal = _get_existing_deal_for_lead(participant_lead)
        if existing_deal:
            _set_if_field(intake_doc, "opportunity", existing_deal)
            intake_doc.save(ignore_permissions=True)
            frappe.db.commit()

            return {
                "doctype": CRM_DEAL,
                "name": existing_deal,
                "created": False,
                "message": "Existing CRM Deal linked to intake.",
            }

    if _field_exists(INTAKE, "status") and intake_doc.status not in ["Qualified", "Converted"]:
        frappe.throw(_("NDIS Participant Intake must be Qualified before creating a CRM Deal."))

    participant_name = _get(intake_doc, "participant_name") or intake_doc.name
    first_name, last_name = _split_name(participant_name)

    organization = _get_or_create_crm_organization(participant_name)

    deal = frappe.new_doc(CRM_DEAL)
    deal.status = "New Opportunity"
    deal.organization = organization
    deal.organization_name = organization
    deal.lead = participant_lead
    deal.lead_name = participant_name
    deal.first_name = first_name
    deal.last_name = last_name

    if participant_lead and frappe.db.exists(CRM_LEAD, participant_lead):
        lead_doc = frappe.get_doc(CRM_LEAD, participant_lead)

        deal.email = _get(lead_doc, "email")
        deal.mobile_no = _get(lead_doc, "mobile_no")
        deal.phone = _get(lead_doc, "phone")
        deal.source = _get(lead_doc, "source")
        deal.industry = _get(lead_doc, "industry")
        deal.territory = _get(lead_doc, "territory")

        _set_if_field(deal, "participant_name", _get(lead_doc, "participant_name") or participant_name)
        _set_if_field(deal, "ndis_number", _get(lead_doc, "ndis_number"))
        _set_if_field(deal, "participant_dob", _get(lead_doc, "participant_dob"))
        _set_if_field(deal, "plan_start_date", _get(lead_doc, "plan_start_date"))
        _set_if_field(deal, "plan_end_date", _get(lead_doc, "plan_end_date"))
        _set_if_field(deal, "plan_management_type", _get(lead_doc, "plan_management_type"))
        _set_if_field(deal, "consent_to_contact", _get(lead_doc, "consent_to_contact"))

    _set_if_field(deal, "opportunity_type_ndis", "Mixed Service")
    _set_if_field(deal, "pipeline_type", "General Intake")
    _set_if_field(deal, "pipeline_stage", "New Deal")
    _set_if_field(deal, "funding_verified", 0)
    _set_if_field(deal, "service_agreement_required", 1)
    _set_if_field(deal, "service_agreement_status", "Not Started")
    _set_if_field(deal, "required_documents_collected", 0)
    _set_if_field(deal, "billing_setup_required", 1)
    _set_if_field(deal, "handover_status", "Not Ready")

    _set_if_field(deal, "plan_start_date", _get(intake_doc, "plan_start_date"))
    _set_if_field(deal, "plan_end_date", _get(intake_doc, "plan_end_date"))
    _set_if_field(deal, "plan_management_type", _get(intake_doc, "plan_management_type"))

    _copy_service_interests(
        source_doc=intake_doc,
        source_field="service_interests",
        target_doc=deal,
        target_field="ndis_service_interests",
    )

    deal.insert(ignore_permissions=False)

    _set_if_field(intake_doc, "opportunity", deal.name)
    _set_if_field(intake_doc, "status", "Converted")
    intake_doc.save(ignore_permissions=True)

    if participant_lead and frappe.db.exists(CRM_LEAD, participant_lead):
        lead_doc = frappe.get_doc(CRM_LEAD, participant_lead)
        if _field_exists(CRM_LEAD, "converted"):
            lead_doc.converted = 1
        if _field_exists(CRM_LEAD, "status"):
            lead_doc.status = "Converted"
        lead_doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": CRM_DEAL,
        "name": deal.name,
        "created": True,
        "message": "CRM Deal created successfully.",
    }


def validate_crm_lead(doc, method=None):
    """
    Server-side validation for CRM Lead.
    """
    if doc.status == "Qualified":
        if _field_exists(CRM_LEAD, "consent_to_contact") and not doc.get("consent_to_contact"):
            frappe.throw(_("Cannot mark CRM Lead as Qualified unless Consent to Contact is ticked."))


def validate_crm_deal(doc, method=None):
    """
    Server-side validation for CRM Deal.
    """
    if doc.status == "Funding Verified":
        missing = []

        if _field_exists(CRM_DEAL, "plan_start_date") and not doc.get("plan_start_date"):
            missing.append("Plan Start Date")

        if _field_exists(CRM_DEAL, "plan_end_date") and not doc.get("plan_end_date"):
            missing.append("Plan End Date")

        if _field_exists(CRM_DEAL, "plan_management_type") and not doc.get("plan_management_type"):
            missing.append("Plan Management Type")

        if missing:
            frappe.throw(
                _("Cannot move CRM Deal to Funding Verified. Missing: {0}").format(", ".join(missing))
            )

    if doc.status == "Service Agreement Sent":
        if _field_exists(CRM_DEAL, "required_documents_collected") and not doc.get("required_documents_collected"):
            frappe.throw(
                _("Cannot move CRM Deal to Service Agreement Sent until Required Documents Collected is ticked.")
            )


def validate_intake(doc, method=None):
    """
    Server-side validation for NDIS Participant Intake.
    """
    if _field_exists(INTAKE, "status") and doc.status == "Qualified":
        if _field_exists(INTAKE, "consent_to_contact") and not doc.get("consent_to_contact"):
            frappe.throw(_("Cannot qualify NDIS Intake unless Consent to Contact is ticked."))


def phase2_health_check():
    print("---- NDIS CRM Phase 2 Health Check ----")

    for dt in [CRM_LEAD, CRM_DEAL, "CRM Lead Status", "CRM Deal Status", "CRM Form Script", INTAKE]:
        print(f"{dt}: {'OK' if frappe.db.exists('DocType', dt) else 'MISSING'}")

    lead_statuses = frappe.get_all("CRM Lead Status", pluck="name")
    deal_statuses = frappe.get_all("CRM Deal Status", pluck="name")

    print("CRM Lead Status count:", len(lead_statuses))
    print("CRM Deal Status count:", len(deal_statuses))

    lead_script = frappe.db.exists("CRM Form Script", "NDIS CRM Lead Actions")
    deal_script = frappe.db.exists("CRM Form Script", "NDIS CRM Deal Actions")
    intake_script = frappe.db.exists("Client Script", "NDIS Participant Intake Actions")

    print(f"CRM Lead Form Script: {'OK' if lead_script else 'MISSING'}")
    print(f"CRM Deal Form Script: {'OK' if deal_script else 'MISSING'}")
    print(f"NDIS Intake Client Script: {'OK' if intake_script else 'MISSING'}")

    print("CRM Lead consent field:", "OK" if _field_exists(CRM_LEAD, "consent_to_contact") else "MISSING")
    print("CRM Deal docs collected field:", "OK" if _field_exists(CRM_DEAL, "required_documents_collected") else "MISSING")

    participant_lead_options = frappe.db.get_value(
        "DocField",
        {"parent": INTAKE, "fieldname": "participant_lead"},
        "options"
    )

    opportunity_options = frappe.db.get_value(
        "DocField",
        {"parent": INTAKE, "fieldname": "opportunity"},
        "options"
    )

    print("NDIS Intake participant_lead options:", participant_lead_options)
    print("NDIS Intake opportunity options:", opportunity_options)

    print("---- End Phase 2 Health Check ----")
