import frappe
from frappe import _
from frappe.utils import nowdate, now_datetime


CRM_LEAD = "CRM Lead"
CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"

DOCUMENT_TYPE = "NDIS Document Type"
DOCUMENT_RULE = "NDIS Service Document Rule"
DOCUMENT_REQUEST = "NDIS Document Request"

COMPLETE_STATUSES = ["Received", "Reviewed", "Accepted", "Not Required"]

REQUIRED_BEFORE_PRIORITY = {
    "Intake Qualification": 1,
    "Funding Verification": 2,
    "Service Agreement Sent": 3,
    "Operations Handover": 4,
}


ALLOWED_ROLES = {
    "System Manager",
    "Sales Manager",
    "Sales User",
    "NDIS CRM Manager",
    "NDIS Intake Officer",
    "NDIS Service Manager",
    "NDIS Plan Management Officer",
}


def _check_role():
    user_roles = set(frappe.get_roles())
    if not user_roles.intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this NDIS CRM document action."))


def _field_exists(doctype, fieldname):
    return bool(
        frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
        or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
    )


def _get_service_interest_field(source_doctype):
    if source_doctype in [CRM_LEAD, CRM_DEAL]:
        return "ndis_service_interests"

    if source_doctype == INTAKE:
        return "service_interests"

    return None


def _get_source_doc(source_doctype, source_name):
    if not frappe.db.exists(source_doctype, source_name):
        frappe.throw(_("{0} {1} was not found.").format(source_doctype, source_name))

    return frappe.get_doc(source_doctype, source_name)


def _get_service_lines_from_source(source_doc):
    service_field = _get_service_interest_field(source_doc.doctype)

    if not service_field or not _field_exists(source_doc.doctype, service_field):
        return []

    service_lines = []

    for row in source_doc.get(service_field) or []:
        if row.get("service_line") and row.get("service_line") not in service_lines:
            service_lines.append(row.get("service_line"))

    return service_lines


def _get_source_link_context(source_doctype, source_name):
    """
    Build link context so Document Requests can be connected across:
    CRM Lead -> NDIS Intake -> CRM Deal
    """
    context = {
        "crm_lead": None,
        "participant_intake": None,
        "crm_deal": None,
        "participant_customer": None,
    }

    if source_doctype == CRM_LEAD:
        context["crm_lead"] = source_name

        intake = frappe.db.get_value(INTAKE, {"participant_lead": source_name}, "name")
        if intake:
            context["participant_intake"] = intake

        deal = frappe.db.get_value(CRM_DEAL, {"lead": source_name}, "name")
        if deal:
            context["crm_deal"] = deal

    elif source_doctype == INTAKE:
        context["participant_intake"] = source_name

        intake_doc = frappe.get_doc(INTAKE, source_name)

        if _field_exists(INTAKE, "participant_lead"):
            context["crm_lead"] = intake_doc.get("participant_lead")

        if _field_exists(INTAKE, "opportunity"):
            context["crm_deal"] = intake_doc.get("opportunity")

    elif source_doctype == CRM_DEAL:
        context["crm_deal"] = source_name

        deal_doc = frappe.get_doc(CRM_DEAL, source_name)

        if deal_doc.get("lead"):
            context["crm_lead"] = deal_doc.get("lead")

        if _field_exists(CRM_DEAL, "participant_customer"):
            context["participant_customer"] = deal_doc.get("participant_customer")

        if context["crm_lead"]:
            intake = frappe.db.get_value(INTAKE, {"participant_lead": context["crm_lead"]}, "name")
            if intake:
                context["participant_intake"] = intake

        if not context["participant_intake"]:
            intake = frappe.db.get_value(INTAKE, {"opportunity": source_name}, "name")
            if intake:
                context["participant_intake"] = intake

    return context


def _get_duplicate_filters(source_doctype, source_name, document_type):
    filters = {
        "document_type": document_type,
    }

    if source_doctype == CRM_LEAD:
        filters["crm_lead"] = source_name

    elif source_doctype == INTAKE:
        filters["participant_intake"] = source_name

    elif source_doctype == CRM_DEAL:
        filters["crm_deal"] = source_name

    return filters


def _max_required_before(current_value, new_value):
    current_priority = REQUIRED_BEFORE_PRIORITY.get(current_value or "Intake Qualification", 1)
    new_priority = REQUIRED_BEFORE_PRIORITY.get(new_value or "Intake Qualification", 1)

    if new_priority > current_priority:
        return new_value

    return current_value


def _get_required_document_rules(service_lines):
    if not service_lines:
        return {}

    rules = frappe.get_all(
        DOCUMENT_RULE,
        filters={
            "service_line": ["in", service_lines],
            "active": 1,
            "auto_request": 1,
        },
        fields=[
            "name",
            "service_line",
            "document_type",
            "mandatory",
            "required_before",
            "notes",
        ],
    )

    grouped = {}

    for rule in rules:
        document_type = rule.document_type

        if document_type not in grouped:
            grouped[document_type] = {
                "document_type": document_type,
                "mandatory": 0,
                "required_before": rule.required_before or "Intake Qualification",
                "required_for_services": [],
                "notes": [],
            }

        if rule.mandatory:
            grouped[document_type]["mandatory"] = 1

        grouped[document_type]["required_before"] = _max_required_before(
            grouped[document_type]["required_before"],
            rule.required_before,
        )

        if rule.service_line not in grouped[document_type]["required_for_services"]:
            grouped[document_type]["required_for_services"].append(rule.service_line)

        if rule.notes:
            grouped[document_type]["notes"].append(rule.notes)

    return grouped


def _get_document_request_filters(source_doctype, source_name):
    if source_doctype == CRM_LEAD:
        return {"crm_lead": source_name}

    if source_doctype == INTAKE:
        return {"participant_intake": source_name}

    if source_doctype == CRM_DEAL:
        return {"crm_deal": source_name}

    frappe.throw(_("Unsupported source doctype: {0}").format(source_doctype))


def _get_document_requests(source_doctype, source_name):
    filters = _get_document_request_filters(source_doctype, source_name)

    return frappe.get_all(
        DOCUMENT_REQUEST,
        filters=filters,
        fields=[
            "name",
            "document_type",
            "document_type_name",
            "is_required",
            "status",
            "required_before",
            "uploaded_file",
        ],
        order_by="is_required desc, document_type_name asc",
    )


def _calculate_document_summary(source_doctype, source_name):
    requests = _get_document_requests(source_doctype, source_name)

    required = [r for r in requests if r.is_required]
    completed_required = [r for r in required if r.status in COMPLETE_STATUSES]

    total_required = len(required)
    completed_count = len(completed_required)

    if total_required == 0:
        completion_percent = 100 if requests else 0
    else:
        completion_percent = round((completed_count / total_required) * 100, 2)

    incomplete = [
        r.document_type_name or r.document_type
        for r in required
        if r.status not in COMPLETE_STATUSES
    ]

    return {
        "total_requests": len(requests),
        "total_required": total_required,
        "completed_required": completed_count,
        "completion_percent": completion_percent,
        "all_required_complete": total_required > 0 and completed_count == total_required,
        "incomplete_required": incomplete,
    }


def _set_source_summary(source_doctype, source_name):
    summary = _calculate_document_summary(source_doctype, source_name)

    if _field_exists(source_doctype, "document_completion_percent"):
        frappe.db.set_value(
            source_doctype,
            source_name,
            "document_completion_percent",
            summary["completion_percent"],
            update_modified=False,
        )

    if _field_exists(source_doctype, "document_summary"):
        text = (
            f"Required: {summary['completed_required']} / {summary['total_required']} complete. "
            f"Total requests: {summary['total_requests']}."
        )

        if summary["incomplete_required"]:
            text += " Missing: " + ", ".join(summary["incomplete_required"])

        frappe.db.set_value(
            source_doctype,
            source_name,
            "document_summary",
            text,
            update_modified=False,
        )

    if _field_exists(source_doctype, "required_documents_collected"):
        frappe.db.set_value(
            source_doctype,
            source_name,
            "required_documents_collected",
            1 if summary["all_required_complete"] else 0,
            update_modified=False,
        )

    return summary


def _create_document_request(source_doctype, source_name, document_type, rule_data):
    duplicate_filters = _get_duplicate_filters(source_doctype, source_name, document_type)

    existing = frappe.db.get_value(DOCUMENT_REQUEST, duplicate_filters, "name")
    if existing:
        return existing, False

    context = _get_source_link_context(source_doctype, source_name)

    document_type_name = frappe.db.get_value(DOCUMENT_TYPE, document_type, "document_type_name") or document_type

    doc = frappe.get_doc({
        "doctype": DOCUMENT_REQUEST,
        "document_type": document_type,
        "document_type_name": document_type_name,
        "is_required": 1 if rule_data.get("mandatory") else 0,
        "required_before": rule_data.get("required_before") or "Intake Qualification",
        "required_for_services": "\n".join(rule_data.get("required_for_services") or []),
        "status": "Requested",
        "requested_date": nowdate(),
        "crm_lead": context.get("crm_lead"),
        "participant_intake": context.get("participant_intake"),
        "crm_deal": context.get("crm_deal"),
        "participant_customer": context.get("participant_customer"),
        "source_doctype": source_doctype,
        "source_name": source_name,
        "notes": "\n".join(rule_data.get("notes") or []),
    })

    doc.insert(ignore_permissions=False)

    return doc.name, True


@frappe.whitelist()
def generate_document_requests(source_doctype, source_name):
    """
    Main generator.
    Creates document requests from selected NDIS service interests.
    """
    _check_role()

    source_doc = _get_source_doc(source_doctype, source_name)
    service_lines = _get_service_lines_from_source(source_doc)

    if not service_lines:
        frappe.throw(_("No NDIS Service Interests found. Please add service interests first."))

    rules = _get_required_document_rules(service_lines)

    if not rules:
        frappe.throw(_("No active document rules found for the selected service interests."))

    created = []
    existing = []

    for document_type, rule_data in rules.items():
        name, was_created = _create_document_request(
            source_doctype=source_doctype,
            source_name=source_name,
            document_type=document_type,
            rule_data=rule_data,
        )

        if was_created:
            created.append(name)
        else:
            existing.append(name)

    if _field_exists(source_doctype, "required_documents_generated"):
        frappe.db.set_value(
            source_doctype,
            source_name,
            "required_documents_generated",
            1,
            update_modified=False,
        )

    summary = _set_source_summary(source_doctype, source_name)

    frappe.db.commit()

    return {
        "created_count": len(created),
        "existing_count": len(existing),
        "created": created,
        "existing": existing,
        "summary": summary,
        "message": f"Document requests generated. Created: {len(created)}, Existing: {len(existing)}.",
    }


@frappe.whitelist()
def generate_document_requests_for_crm_lead(lead):
    return generate_document_requests(CRM_LEAD, lead)


@frappe.whitelist()
def generate_document_requests_for_crm_deal(deal):
    return generate_document_requests(CRM_DEAL, deal)


@frappe.whitelist()
def generate_document_requests_for_intake(intake):
    return generate_document_requests(INTAKE, intake)


@frappe.whitelist()
def get_document_summary(source_doctype, source_name):
    _check_role()
    return _set_source_summary(source_doctype, source_name)


def get_incomplete_documents_for_deal(deal_name):
    requests = frappe.get_all(
        DOCUMENT_REQUEST,
        filters={
            "crm_deal": deal_name,
            "is_required": 1,
            "required_before": ["in", [
                "Intake Qualification",
                "Funding Verification",
                "Service Agreement Sent",
            ]],
        },
        fields=[
            "name",
            "document_type_name",
            "status",
        ],
        order_by="document_type_name asc",
    )

    incomplete = [
        r for r in requests
        if r.status not in COMPLETE_STATUSES
    ]

    return requests, incomplete


def validate_crm_deal_documents(doc, method=None):
    """
    Phase 3 validation:
    Cannot move CRM Deal to Service Agreement Sent unless required document requests are complete.
    """
    if doc.status != "Service Agreement Sent":
        return

    if not frappe.db.exists("DocType", DOCUMENT_REQUEST):
        frappe.throw(_("NDIS Document Request DocType is missing."))

    requests, incomplete = get_incomplete_documents_for_deal(doc.name)

    if not requests:
        frappe.throw(
            _("Cannot move CRM Deal to Service Agreement Sent. Generate document requests first.")
        )

    if incomplete:
        missing = ", ".join([
            f"{r.document_type_name} ({r.status})"
            for r in incomplete
        ])

        if _field_exists(CRM_DEAL, "required_documents_collected"):
            doc.set("required_documents_collected", 0)

        frappe.throw(
            _("Cannot move CRM Deal to Service Agreement Sent. Required documents are incomplete: {0}").format(missing)
        )

    if _field_exists(CRM_DEAL, "required_documents_collected"):
        doc.set("required_documents_collected", 1)


def validate_crm_deal_combined(doc, method=None):
    """
    Combined CRM Deal validator.
    Runs Phase 3 document validation first, then keeps Phase 2 funding validation alive.
    """
    validate_crm_deal_documents(doc, method)

    try:
        from ndis_crm.phase2_api import validate_crm_deal
        validate_crm_deal(doc, method)
    except ImportError:
        pass


def on_document_request_update(doc, method=None):
    """
    Update document completion summary on linked records whenever a document request changes.
    """
    try:
        if doc.get("crm_lead"):
            _set_source_summary(CRM_LEAD, doc.get("crm_lead"))

        if doc.get("participant_intake"):
            _set_source_summary(INTAKE, doc.get("participant_intake"))

        if doc.get("crm_deal"):
            _set_source_summary(CRM_DEAL, doc.get("crm_deal"))

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS Document Request Summary Update Failed"
        )


def phase3_health_check():
    print("---- NDIS CRM Phase 3 Health Check ----")

    for dt in [
        DOCUMENT_TYPE,
        DOCUMENT_RULE,
        DOCUMENT_REQUEST,
        CRM_LEAD,
        CRM_DEAL,
        INTAKE,
    ]:
        print(f"{dt}: {'OK' if frappe.db.exists('DocType', dt) else 'MISSING'}")

    print("NDIS Document Type count:", frappe.db.count(DOCUMENT_TYPE) if frappe.db.exists("DocType", DOCUMENT_TYPE) else 0)
    print("NDIS Service Document Rule count:", frappe.db.count(DOCUMENT_RULE) if frappe.db.exists("DocType", DOCUMENT_RULE) else 0)

    for field in [
        "required_documents_generated",
        "document_completion_percent",
        "document_summary",
    ]:
        print(f"CRM Lead field {field}: {'OK' if _field_exists(CRM_LEAD, field) else 'MISSING'}")
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")
        print(f"NDIS Intake field {field}: {'OK' if _field_exists(INTAKE, field) else 'MISSING'}")

    print("CRM Deal combined validator should be active through hooks.py.")
    print("---- End Phase 3 Health Check ----")
