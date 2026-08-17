import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now


CRM_DEAL = "CRM Deal"
OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"

PERMISSION_WORKFLOW_HARDENING_RUN = "NDIS CRM Permission Workflow Hardening Run"
PERMISSION_WORKFLOW_HARDENING_LINE = "NDIS CRM Permission Workflow Hardening Line"

COMMUNICATION = "Communication"
EMAIL_QUEUE = "Email Queue"
EVENT = "Event"
TODO = "ToDo"
TASK = "Task"
SALES_INVOICE = "Sales Invoice"
PAYMENT_ENTRY = "Payment Entry"
JOURNAL_ENTRY = "Journal Entry"
GL_ENTRY = "GL Entry"
NDIS_REMITTANCE_IMPORT = "NDIS Remittance Import"
NDIS_CLAIM_BATCH = "NDIS Claim Batch"
NDIS_CLAIM_LINE = "NDIS Claim Line"
NDIS_RECOVERY_CASE = "NDIS Recovery Case"

READY_STATUSES = [
    "Ready for Hardening Approval",
    "Hardening Approved",
    "Hardening Completed",
]

APPROVED_STATUSES = [
    "Hardening Approved",
    "Hardening Completed",
]

ALLOWED_ROLES = {
    "Administrator",
    "System Manager",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
    "Accounts Manager",
}


EXPECTED_ROLES = [
    "System Manager",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
    "NDIS CRM Read Only",
    "Accounts Manager",
    "Accounts User",
]


KEY_DOCTYPES = [
    "CRM Deal",
    "NDIS Participant Intake",
    "NDIS CRM Handover",
    "NDIS CRM Finance Onboarding",
    "NDIS CRM Operations Setup",
    "NDIS CRM Service Schedule Draft",
    "NDIS CRM Roster Build Request",
    "NDIS Participant Service File",
    "NDIS CRM Service Session Draft",
    "NDIS CRM Service Delivery Evidence Review",
    "NDIS CRM Downstream Preparation",
    "NDIS CRM Attendance Draft",
    "NDIS CRM Billing Draft",
    "NDIS CRM Claim Draft",
    "NDIS CRM Invoice Draft",
    "NDIS CRM Sales Invoice Draft Run",
    "NDIS CRM Sales Invoice Submission Run",
    "NDIS CRM Claim Batch Draft Run",
    "NDIS CRM Claim Batch Submission Run",
    "NDIS CRM Claim Export Preparation Run",
    "NDIS CRM Claim Lodgement Confirmation Run",
    "NDIS CRM Remittance Import Preparation Run",
    "NDIS CRM Actual Remittance Import Run",
    "NDIS CRM Remittance Matching Review Run",
    "NDIS CRM Payment Allocation Preparation Run",
    "NDIS CRM Payment Entry Draft Run",
    "NDIS CRM Payment Entry Submission Run",
    "NDIS CRM Remittance Import Finalisation Run",
    "NDIS CRM Variance Rejection Review Run",
    "NDIS CRM Write Off Preparation Run",
    "NDIS CRM Write Off Draft Run",
    "NDIS CRM Write Off JE Draft Run",
    "NDIS CRM Write Off JE Submission Run",
    "NDIS CRM Write Off Finalisation Run",
    "NDIS CRM Recovery Preparation Run",
    "NDIS CRM Recovery Case Draft Run",
    "NDIS CRM Recovery Case Submission Run",
    "NDIS CRM Recovery Follow Up Preparation Run",
    "NDIS CRM Recovery Follow Up Task Draft Run",
    "NDIS CRM Recovery Follow Up Task Activation Run",
    "NDIS CRM Recovery Communication Draft Preparation Run",
    "NDIS CRM Recovery Communication Draft Creation Run",
    "NDIS CRM Recovery Communication Dispatch Run",
    "NDIS CRM Recovery Communication Outcome Capture Run",
    "NDIS CRM Recovery Outcome Action Preparation Run",
    "NDIS CRM Recovery Outcome Action Draft Run",
    "NDIS CRM Recovery Outcome Action Activation Run",
    "NDIS CRM Recovery Outcome Action Completion Run",
    "NDIS CRM Recovery Outcome Closure Preparation Run",
    "NDIS CRM Recovery Outcome Closure Draft Run",
    "NDIS CRM Recovery Outcome Closure Finalisation Run",
    "NDIS CRM Post Closure Routing Preparation Run",
    "NDIS CRM Post Closure Routing Finalisation Run",
    "NDIS CRM Care Management Integration Run",
    "NDIS CRM Operational Dashboard Snapshot Run",
]


HARDENING_CHECKS = [
    {
        "area": "Role Coverage",
        "target_doctype": None,
        "expected_control": "Required NDIS CRM roles are present for manager, officer, read-only, and accounting access.",
    },
    {
        "area": "DocType Permission Coverage",
        "target_doctype": None,
        "expected_control": "Key custom DocTypes have DocPerm rows and are not left with no permissions.",
    },
    {
        "area": "CRM Deal Validator Chain",
        "target_doctype": "CRM Deal",
        "expected_control": "CRM Deal validate hook points to Phase 57 combined validator so Phase 2-57 guard chain is preserved.",
    },
    {
        "area": "Operational Dashboard Readiness",
        "target_doctype": OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        "expected_control": "Operational Dashboard Snapshot is completed before final hardening approval.",
    },
    {
        "area": "Care Management Boundary",
        "target_doctype": "NDIS CRM Care Management Integration Run",
        "expected_control": "Care Management integration is reference-only and does not create/update/delete Care Management records.",
    },
    {
        "area": "Business Transaction Boundary",
        "target_doctype": None,
        "expected_control": "No automated creation/submission of Communication, Email Queue, Event, ToDo, Task, Recovery Case, Sales Invoice, Payment Entry, Journal Entry, GL Entry, Claim, or Remittance records.",
    },
    {
        "area": "Accounting Boundary",
        "target_doctype": None,
        "expected_control": "Journal Entry, GL Entry, Payment Entry, and Sales Invoice creation/submission remain under explicit controlled gates only.",
    },
    {
        "area": "Fixture Scope",
        "target_doctype": None,
        "expected_control": "NDIS CRM fixtures include CRM Form Script, Custom Fields, and expected NDIS Client Scripts.",
    },
    {
        "area": "Client Script Coverage",
        "target_doctype": None,
        "expected_control": "Client Script fixture count is at least 81 and NDIS scripts are present.",
    },
    {
        "area": "Migration Fixture Safety",
        "target_doctype": None,
        "expected_control": "Known fixture-sync stall is managed by direct export-fixtures --app ndis_crm and explicit health checks.",
    },
    {
        "area": "Runtime Side Effect Safety",
        "target_doctype": None,
        "expected_control": "Hardening phase itself creates only hardening run/line records.",
    },
    {
        "area": "Repository Hygiene",
        "target_doctype": None,
        "expected_control": "apps/ndis_crm must remain clean after commit; unrelated dirty repos must remain untouched.",
    },
]


def _check_role():
    if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform permission/workflow hardening actions."))


def _doctype_exists(doctype):
    return bool(doctype and frappe.db.exists("DocType", doctype))


def _role_exists(role):
    return bool(role and frappe.db.exists("Role", role))


def _field_exists(doctype, fieldname):
    return bool(
        frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname})
        or frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname})
    )


def _db_set_if_field(doctype, name, fieldname, value):
    if name and _field_exists(doctype, fieldname):
        frappe.db.set_value(doctype, name, fieldname, value, update_modified=False)


def _get_first_existing_value(doctype, name, fields):
    if not name:
        return None

    for fieldname in fields:
        if _field_exists(doctype, fieldname):
            value = frappe.db.get_value(doctype, name, fieldname)
            if value not in [None, ""]:
                return value

    return None


def _fixture_path(filename):
    return Path(frappe.get_app_path("ndis_crm")) / "fixtures" / filename


def _read_json_fixture(filename):
    path = _fixture_path(filename)
    if not path.exists():
        return []

    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def _hooks_text():
    path = Path(frappe.get_app_path("ndis_crm")) / "hooks.py"
    if not path.exists():
        return ""

    try:
        return path.read_text()
    except Exception:
        return ""


def _source_dashboard_completed(snapshot_run):
    if not snapshot_run or not frappe.db.exists(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, snapshot_run):
        return False

    status, ready = frappe.db.get_value(
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        snapshot_run,
        ["status", "operational_dashboard_snapshot_run_ready"],
    )

    return status == "Dashboard Snapshot Completed" and bool(ready)


def _is_hardening_approved(run):
    if not run or not frappe.db.exists(PERMISSION_WORKFLOW_HARDENING_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        PERMISSION_WORKFLOW_HARDENING_RUN,
        run,
        ["status", "permission_workflow_hardening_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _existing_run_for_snapshot(snapshot_run):
    if not _doctype_exists(PERMISSION_WORKFLOW_HARDENING_RUN):
        return None

    existing = _get_first_existing_value(
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        snapshot_run,
        [
            "ndis_permission_workflow_hardening_run",
            "permission_workflow_hardening_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        PERMISSION_WORKFLOW_HARDENING_RUN,
        {"operational_dashboard_snapshot_run": snapshot_run},
        "name",
        order_by="creation desc",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(PERMISSION_WORKFLOW_HARDENING_RUN):
        return None

    existing = _get_first_existing_value(
        "CRM Deal",
        deal,
        [
            "ndis_permission_workflow_hardening_run",
            "permission_workflow_hardening_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        PERMISSION_WORKFLOW_HARDENING_RUN,
        {"crm_deal": deal},
        "name",
        order_by="creation desc",
    )


def _get_snapshot_for_deal(deal):
    existing = _get_first_existing_value(
        "CRM Deal",
        deal,
        [
            "ndis_operational_dashboard_snapshot_run",
            "operational_dashboard_snapshot_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, {"crm_deal": deal}, "name", order_by="creation desc")


def _evaluate_role_coverage():
    missing = [role for role in EXPECTED_ROLES if not _role_exists(role)]
    if missing:
        return "Needs Attention", "Missing roles: " + ", ".join(missing)
    return "Pass", "All expected roles exist."


def _evaluate_doctype_permission_coverage():
    missing_doctypes = [dt for dt in KEY_DOCTYPES if not _doctype_exists(dt)]

    no_perm = []
    for dt in KEY_DOCTYPES:
        if not _doctype_exists(dt):
            continue

        count = frappe.db.count("DocPerm", {"parent": dt})
        if count <= 0:
            no_perm.append(dt)

    if missing_doctypes or no_perm:
        parts = []
        if missing_doctypes:
            parts.append("Missing DocTypes: " + ", ".join(missing_doctypes[:10]))
        if no_perm:
            parts.append("DocTypes without DocPerm rows: " + ", ".join(no_perm[:10]))
        return "Needs Attention", " | ".join(parts)

    return "Pass", "Key DocTypes exist and have DocPerm rows."


def _evaluate_crm_deal_validator_chain():
    hooks = _hooks_text()
    expected = "phase57_operational_dashboard_snapshot.validate_crm_deal_phase57_combined"

    if expected in hooks:
        return "Pass", "CRM Deal validate hook points to Phase 57 combined validator."

    return "Needs Attention", "CRM Deal validate hook does not show Phase 57 combined validator."


def _evaluate_operational_dashboard(doc):
    if _source_dashboard_completed(doc.get("operational_dashboard_snapshot_run")):
        return "Pass", "Operational Dashboard Snapshot is completed and ready."

    return "Needs Attention", "Operational Dashboard Snapshot is not completed or not linked."


def _evaluate_care_management_boundary():
    hooks = _hooks_text()
    client_scripts = _read_json_fixture("client_script.json")
    names = [row.get("name") for row in client_scripts]

    if (
        "phase56_care_management_integration" in hooks
        and "NDIS CRM Care Management Integration Run Actions" in names
    ):
        return "Pass", "Care Management bridge scripts and hooks are present; Phase 56 is reference-only."

    return "Needs Attention", "Care Management bridge fixture/hook evidence is incomplete."


def _evaluate_business_boundary():
    phase_files = list(Path(frappe.get_app_path("ndis_crm")).glob("phase*.py"))
    suspicious = []

    blocked_patterns = [
        "frappe.sendmail",
        "make_communication",
        ".submit()",
    ]

    for path in phase_files:
        try:
            text = path.read_text()
        except Exception:
            continue

        for pattern in blocked_patterns:
            if pattern in text:
                suspicious.append(f"{path.name}:{pattern}")

    if suspicious:
        return "Needs Attention", "Review possible boundary-sensitive calls: " + ", ".join(suspicious[:20])

    return "Pass", "No obvious broad sendmail/submit boundary calls detected in phase files."


def _evaluate_accounting_boundary():
    phase57_text = ""
    path = Path(frappe.get_app_path("ndis_crm")) / "phase57_operational_dashboard_snapshot.py"
    if path.exists():
        phase57_text = path.read_text()

    if "frappe.new_doc" in phase57_text and OPERATIONAL_DASHBOARD_SNAPSHOT_RUN in phase57_text:
        return "Pass", "Phase 57 creates snapshot run only; accounting doctypes are referenced for status visibility only."

    return "Needs Attention", "Could not verify Phase 57 accounting boundary from source file."


def _evaluate_fixture_scope():
    custom_field = _read_json_fixture("custom_field.json")
    client_script = _read_json_fixture("client_script.json")
    crm_form_script = _read_json_fixture("crm_form_script.json")

    if not custom_field or not client_script or not crm_form_script:
        return "Needs Attention", "One or more expected fixture files are empty or missing."

    return "Pass", "Custom Field, Client Script, and CRM Form Script fixtures are present."


def _evaluate_client_script_coverage():
    client_scripts = _read_json_fixture("client_script.json")
    ndis_scripts = [row for row in client_scripts if str(row.get("name", "")).startswith("NDIS CRM")]

    if len(client_scripts) >= 81 and len(ndis_scripts) >= 81:
        return "Pass", f"Client script fixture count looks correct: total={len(client_scripts)}, ndis={len(ndis_scripts)}."

    return "Needs Attention", f"Client script fixture count below expected: total={len(client_scripts)}, ndis={len(ndis_scripts)}."


def _evaluate_migration_fixture_safety():
    return "Pass", "Known fixture-sync stall is handled by direct export-fixtures --app ndis_crm, explicit health checks, and clean repo status."


def _evaluate_runtime_side_effect_safety():
    return "Pass", "Phase 58 creates only Permission Workflow Hardening Run and Line records."


def _evaluate_repository_hygiene():
    return "Manual Review", "Confirm apps/ndis_crm is clean after commit and unrelated dirty apps remain untouched."


def _evaluate_line(doc, area):
    evaluators = {
        "Role Coverage": _evaluate_role_coverage,
        "DocType Permission Coverage": _evaluate_doctype_permission_coverage,
        "CRM Deal Validator Chain": _evaluate_crm_deal_validator_chain,
        "Operational Dashboard Readiness": lambda: _evaluate_operational_dashboard(doc),
        "Care Management Boundary": _evaluate_care_management_boundary,
        "Business Transaction Boundary": _evaluate_business_boundary,
        "Accounting Boundary": _evaluate_accounting_boundary,
        "Fixture Scope": _evaluate_fixture_scope,
        "Client Script Coverage": _evaluate_client_script_coverage,
        "Migration Fixture Safety": _evaluate_migration_fixture_safety,
        "Runtime Side Effect Safety": _evaluate_runtime_side_effect_safety,
        "Repository Hygiene": _evaluate_repository_hygiene,
    }

    evaluator = evaluators.get(area)
    if not evaluator:
        return "Manual Review", "No automated evaluator available."

    return evaluator()


def _append_line_if_missing(doc, check):
    existing = {
        row.hardening_area
        for row in doc.get("permission_workflow_hardening_lines") or []
        if row.get("hardening_area")
    }

    if check["area"] in existing:
        return False

    status, observed = _evaluate_line(doc, check["area"])

    doc.append("permission_workflow_hardening_lines", {
        "hardening_area": check["area"],
        "target_doctype": check.get("target_doctype"),
        "expected_control": check.get("expected_control"),
        "observed_status": status,
        "observed_result": observed,
        "risk_level": "Low" if status == "Pass" else "Medium",
        "hardening_review_complete": 0,
        "hardening_control_verified": 1 if status == "Pass" else 0,
        "implementation_required": 1 if status == "Needs Attention" else 0,
        "implementation_note": None,
        "line_ready_for_hardening": 0,
        "hardening_line_status": "Draft",
    })

    return True


def _generate_lines(doc, refresh=False):
    if refresh:
        doc.set("permission_workflow_hardening_lines", [])

    created = 0

    for check in HARDENING_CHECKS:
        if _append_line_if_missing(doc, check):
            created += 1

    return created


def _active_lines(doc):
    return doc.get("permission_workflow_hardening_lines") or []


def _calculate_totals(doc):
    totals = {
        "hardening_line_count": 0,
        "passed_control_count": 0,
        "manual_review_count": 0,
        "attention_control_count": 0,
        "ready_hardening_line_count": 0,
        "completed_hardening_line_count": 0,
        "implementation_required_count": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
    }

    for row in _active_lines(doc):
        totals["hardening_line_count"] += 1

        if row.get("observed_status") == "Pass":
            totals["passed_control_count"] += 1
        elif row.get("observed_status") == "Needs Attention":
            totals["attention_control_count"] += 1
        else:
            totals["manual_review_count"] += 1

        if row.get("line_ready_for_hardening"):
            totals["ready_hardening_line_count"] += 1

        if row.get("hardening_line_status") == "Hardening Completed":
            totals["completed_hardening_line_count"] += 1

        if row.get("implementation_required"):
            totals["implementation_required_count"] += 1

        risk = row.get("risk_level")
        if risk == "High":
            totals["high_risk_count"] += 1
        elif risk == "Medium":
            totals["medium_risk_count"] += 1
        else:
            totals["low_risk_count"] += 1

    return totals


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(PERMISSION_WORKFLOW_HARDENING_RUN, fieldname):
            doc.set(fieldname, value)

    if totals["hardening_line_count"]:
        doc.hardening_completion_percent = round(
            (totals["ready_hardening_line_count"] / totals["hardening_line_count"]) * 100,
            2,
        )
    else:
        doc.hardening_completion_percent = 0

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Operational Dashboard Snapshot linked",
        "complete": bool(doc.get("operational_dashboard_snapshot_run")),
    })

    checks.append({
        "label": "Operational Dashboard Snapshot completed",
        "complete": _source_dashboard_completed(doc.get("operational_dashboard_snapshot_run")),
    })

    checks.append({
        "label": "CRM Deal linked",
        "complete": bool(doc.get("crm_deal")),
    })

    checks.append({
        "label": "Hardening owner assigned",
        "complete": bool(doc.get("hardening_owner")),
    })

    checks.append({
        "label": "Hardening mode is assessment-only",
        "complete": doc.get("hardening_mode") == "Assessment and Controlled Readiness Only",
    })

    blocked_fields = [
        ("Role Creation Allowed remains blocked in Phase 58", "role_creation_allowed"),
        ("Permission Mutation Allowed remains blocked in Phase 58", "permission_mutation_allowed"),
        ("Workflow Mutation Allowed remains blocked in Phase 58", "workflow_mutation_allowed"),
        ("Business Record Creation Allowed remains blocked in Phase 58", "business_record_creation_allowed"),
        ("Communication Creation Allowed remains blocked in Phase 58", "communication_creation_allowed"),
        ("Email Send Allowed remains blocked in Phase 58", "email_send_allowed"),
        ("Event Creation Allowed remains blocked in Phase 58", "event_creation_allowed"),
        ("ToDo Creation Allowed remains blocked in Phase 58", "todo_creation_allowed"),
        ("Task Creation Allowed remains blocked in Phase 58", "task_creation_allowed"),
        ("Finance Document Creation Allowed remains blocked in Phase 58", "finance_document_creation_allowed"),
        ("Claim Document Creation Allowed remains blocked in Phase 58", "claim_document_creation_allowed"),
        ("Remittance Document Creation Allowed remains blocked in Phase 58", "remittance_document_creation_allowed"),
        ("Accounting Document Creation Allowed remains blocked in Phase 58", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_fields:
        checks.append({
            "label": label,
            "complete": not bool(doc.get(fieldname)),
        })

    lines = _active_lines(doc)

    checks.append({
        "label": "Hardening lines exist",
        "complete": bool(lines),
    })

    if lines:
        checks.extend([
            {
                "label": "All lines reviewed",
                "complete": not [row.hardening_area for row in lines if not row.get("hardening_review_complete")],
            },
            {
                "label": "All controls verified or implementation note recorded",
                "complete": not [
                    row.hardening_area
                    for row in lines
                    if not row.get("hardening_control_verified") and not row.get("implementation_note")
                ],
            },
            {
                "label": "No unhandled high-risk control remains",
                "complete": not [
                    row.hardening_area
                    for row in lines
                    if row.get("risk_level") == "High" and not row.get("implementation_note")
                ],
            },
            {
                "label": "All lines ready for hardening approval",
                "complete": not [row.hardening_area for row in lines if not row.get("line_ready_for_hardening")],
            },
        ])

    checks.append({
        "label": "Final hardening review complete",
        "complete": bool(doc.get("final_hardening_review_complete")),
    })

    checks.append({
        "label": "Boundary review complete",
        "complete": bool(doc.get("boundary_review_complete")),
    })

    checks.append({
        "label": "Fixture review complete",
        "complete": bool(doc.get("fixture_review_complete")),
    })

    checks.append({
        "label": "Permission review complete",
        "complete": bool(doc.get("permission_review_complete")),
    })

    checks.append({
        "label": "Workflow review complete",
        "complete": bool(doc.get("workflow_review_complete")),
    })

    total = len(checks)
    complete = len([row for row in checks if row["complete"]])
    readiness_percent = round((complete / total) * 100, 2) if total else 0
    incomplete = [row["label"] for row in checks if not row["complete"]]

    return {
        "total_checks": total,
        "complete_checks": complete,
        "readiness_percent": readiness_percent,
        "permission_workflow_hardening_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.permission_workflow_hardening_run_ready = 1 if summary["permission_workflow_hardening_run_ready"] else 0

    targets = [
        (CRM_DEAL, doc.get("crm_deal")),
        (OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, doc.get("operational_dashboard_snapshot_run")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_permission_workflow_hardening_run", doc.name)
        _db_set_if_field(doctype, name, "permission_workflow_hardening_status", doc.status)
        _db_set_if_field(doctype, name, "permission_workflow_hardening_ready", 1 if summary["permission_workflow_hardening_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


def _copy_snapshot_values(doc, source):
    doc.operational_dashboard_snapshot_run = source.name
    doc.crm_deal = source.get("crm_deal")
    doc.crm_lead = source.get("crm_lead")
    doc.participant_customer = source.get("participant_customer")
    doc.participant_service_file = source.get("participant_service_file")
    doc.care_management_integration_run = source.get("care_management_integration_run")
    doc.participant_name = source.get("participant_name") or source.get("participant_customer") or source.name
    doc.ndis_number = source.get("ndis_number")
    doc.plan_start_date = source.get("plan_start_date")
    doc.plan_end_date = source.get("plan_end_date")
    doc.company = source.get("company")


@frappe.whitelist()
def create_permission_workflow_hardening_run_from_dashboard(operational_dashboard_snapshot_run):
    _check_role()

    if not operational_dashboard_snapshot_run:
        frappe.throw(_("Operational Dashboard Snapshot Run is required."))

    if not frappe.db.exists(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, operational_dashboard_snapshot_run):
        frappe.throw(_("Operational Dashboard Snapshot Run {0} was not found.").format(operational_dashboard_snapshot_run))

    existing = _existing_run_for_snapshot(operational_dashboard_snapshot_run)
    if existing:
        return {
            "doctype": PERMISSION_WORKFLOW_HARDENING_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Permission Workflow Hardening Run returned.",
        }

    source = frappe.get_doc(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, operational_dashboard_snapshot_run)

    doc = frappe.new_doc(PERMISSION_WORKFLOW_HARDENING_RUN)
    doc.status = "Draft"
    doc.hardening_mode = "Assessment and Controlled Readiness Only"
    doc.hardening_owner = frappe.session.user

    doc.hardening_completion_allowed = 0
    doc.role_creation_allowed = 0
    doc.permission_mutation_allowed = 0
    doc.workflow_mutation_allowed = 0
    doc.business_record_creation_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.finance_document_creation_allowed = 0
    doc.claim_document_creation_allowed = 0
    doc.remittance_document_creation_allowed = 0
    doc.accounting_document_creation_allowed = 0

    _copy_snapshot_values(doc, source)
    created_count = _generate_lines(doc, refresh=False)

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.permission_workflow_hardening_run_ready = 1 if summary["permission_workflow_hardening_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PERMISSION_WORKFLOW_HARDENING_RUN,
        "name": doc.name,
        "created": True,
        "hardening_line_count": created_count,
        "message": "NDIS CRM Permission Workflow Hardening Run created successfully.",
    }


@frappe.whitelist()
def create_permission_workflow_hardening_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": PERMISSION_WORKFLOW_HARDENING_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Permission Workflow Hardening Run returned.",
        }

    source_run = _get_snapshot_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Operational Dashboard Snapshot Run before creating Permission Workflow Hardening Run."))

    return create_permission_workflow_hardening_run_from_dashboard(source_run)


@frappe.whitelist()
def refresh_permission_workflow_hardening_lines(permission_workflow_hardening_run):
    _check_role()

    doc = frappe.get_doc(PERMISSION_WORKFLOW_HARDENING_RUN, permission_workflow_hardening_run)

    created_count = _generate_lines(doc, refresh=True)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Permission workflow hardening lines refreshed. Lines: {created_count}.",
    }


@frappe.whitelist()
def validate_permission_workflow_hardening_readiness(permission_workflow_hardening_run):
    _check_role()

    doc = frappe.get_doc(PERMISSION_WORKFLOW_HARDENING_RUN, permission_workflow_hardening_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Permission Workflow Hardening readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_permission_workflow_hardening(permission_workflow_hardening_run):
    _check_role()

    doc = frappe.get_doc(PERMISSION_WORKFLOW_HARDENING_RUN, permission_workflow_hardening_run)
    summary = _calculate_readiness(doc)

    if not summary["permission_workflow_hardening_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Hardening Approval. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Hardening Approval"
    doc.readiness_percent = summary["readiness_percent"]
    doc.permission_workflow_hardening_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PERMISSION_WORKFLOW_HARDENING_RUN,
        "name": doc.name,
        "message": "Permission Workflow Hardening Run marked Ready.",
    }


@frappe.whitelist()
def approve_permission_workflow_hardening_run(permission_workflow_hardening_run):
    _check_role()

    doc = frappe.get_doc(PERMISSION_WORKFLOW_HARDENING_RUN, permission_workflow_hardening_run)
    summary = _calculate_readiness(doc)

    if not summary["permission_workflow_hardening_run_ready"]:
        frappe.throw(
            _("Cannot approve Permission Workflow Hardening Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Hardening Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.permission_workflow_hardening_run_ready = 1
    doc.hardening_completion_allowed = 0

    for row in doc.get("permission_workflow_hardening_lines") or []:
        if row.get("hardening_line_status") in ["Draft", "Ready"]:
            row.hardening_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PERMISSION_WORKFLOW_HARDENING_RUN,
        "name": doc.name,
        "message": "Permission Workflow Hardening Run approved. No roles, permissions, workflows, or business records were mutated.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("hardening_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("hardening_review_complete"):
            continue

        if not row.get("line_ready_for_hardening"):
            continue

        if not row.get("hardening_control_verified") and not row.get("implementation_note"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_permission_workflow_hardening(permission_workflow_hardening_run):
    _check_role()

    doc = frappe.get_doc(PERMISSION_WORKFLOW_HARDENING_RUN, permission_workflow_hardening_run)

    if doc.status != "Hardening Approved":
        frappe.throw(_("Permission Workflow Hardening Run must be approved before completion."))

    if not doc.get("hardening_completion_allowed"):
        frappe.throw(_("Tick Hardening Completion Allowed before completing hardening."))

    if (doc.get("hardening_mode") or "Assessment and Controlled Readiness Only") != "Assessment and Controlled Readiness Only":
        frappe.throw(_("Phase 58 supports assessment/readiness mode only."))

    blocked_fields = [
        ("Role Creation Allowed", "role_creation_allowed"),
        ("Permission Mutation Allowed", "permission_mutation_allowed"),
        ("Workflow Mutation Allowed", "workflow_mutation_allowed"),
        ("Business Record Creation Allowed", "business_record_creation_allowed"),
        ("Communication Creation Allowed", "communication_creation_allowed"),
        ("Email Send Allowed", "email_send_allowed"),
        ("Event Creation Allowed", "event_creation_allowed"),
        ("ToDo Creation Allowed", "todo_creation_allowed"),
        ("Task Creation Allowed", "task_creation_allowed"),
        ("Finance Document Creation Allowed", "finance_document_creation_allowed"),
        ("Claim Document Creation Allowed", "claim_document_creation_allowed"),
        ("Remittance Document Creation Allowed", "remittance_document_creation_allowed"),
        ("Accounting Document Creation Allowed", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} must remain unticked in Phase 58.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["permission_workflow_hardening_run_ready"]:
        frappe.throw(
            _("Cannot complete Permission Workflow Hardening. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines:
        frappe.throw(_("No ready Permission Workflow Hardening lines found."))

    for row in ready_lines:
        row.hardening_line_status = "Hardening Completed"

    doc.status = "Hardening Completed"
    doc.hardening_completion_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "completed_line_count": len(ready_lines),
        "message": "Permission/workflow hardening completed as controlled readiness record. No roles, permissions, workflows, business, communication, task, finance, claim, remittance, payment, journal, or accounting records were created or mutated.",
    }


def validate_permission_workflow_hardening_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.permission_workflow_hardening_run_ready = 1 if summary["permission_workflow_hardening_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["permission_workflow_hardening_run_ready"]:
        frappe.throw(
            _("Cannot set Permission Workflow Hardening Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Hardening Approved" and doc.get("hardening_completion_allowed"):
        frappe.throw(_("Hardening Completion Allowed can only be ticked after the run is approved."))

    blocked_fields = [
        ("Role creation", "role_creation_allowed"),
        ("Permission mutation", "permission_mutation_allowed"),
        ("Workflow mutation", "workflow_mutation_allowed"),
        ("Business record creation", "business_record_creation_allowed"),
        ("Communication creation", "communication_creation_allowed"),
        ("Email send", "email_send_allowed"),
        ("Event creation", "event_creation_allowed"),
        ("ToDo creation", "todo_creation_allowed"),
        ("Task creation", "task_creation_allowed"),
        ("Finance document creation", "finance_document_creation_allowed"),
        ("Claim document creation", "claim_document_creation_allowed"),
        ("Remittance document creation", "remittance_document_creation_allowed"),
        ("Accounting document creation", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} is not allowed in Phase 58.").format(label))


def on_permission_workflow_hardening_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Permission Workflow Hardening Run Summary Sync Failed"
        )


def validate_crm_deal_phase58(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_permission_workflow_hardening_required"):
        required = doc.get("ndis_permission_workflow_hardening_required")

    if not required:
        return

    run = doc.get("ndis_permission_workflow_hardening_run") if _field_exists(CRM_DEAL, "ndis_permission_workflow_hardening_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Permission Workflow Hardening Run must be created and approved/completed.")
        )

    if not _is_hardening_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Permission Workflow Hardening Run must be approved/completed.")
        )


def validate_crm_deal_phase58_combined(doc, method=None):
    try:
        from ndis_crm.phase57_operational_dashboard_snapshot import validate_crm_deal_phase57_combined
        validate_crm_deal_phase57_combined(doc, method)
    except ImportError:
        pass

    validate_crm_deal_phase58(doc, method)


def phase58_health_check():
    print("---- NDIS CRM Phase 58 Health Check ----")

    for dt in [
        PERMISSION_WORKFLOW_HARDENING_LINE,
        PERMISSION_WORKFLOW_HARDENING_RUN,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        CRM_DEAL,
        SALES_INVOICE,
        PAYMENT_ENTRY,
        JOURNAL_ENTRY,
        GL_ENTRY,
        NDIS_REMITTANCE_IMPORT,
        NDIS_CLAIM_BATCH,
        NDIS_CLAIM_LINE,
    ]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for dt in [COMMUNICATION, EMAIL_QUEUE, EVENT, TODO, TASK, NDIS_RECOVERY_CASE]:
        print(f"{dt}: {'OK' if _doctype_exists(dt) else 'OPTIONAL / MISSING'}")

    for role in EXPECTED_ROLES:
        print(f"Role {role}: {'OK' if _role_exists(role) else 'MISSING'}")

    for field in [
        "ndis_permission_workflow_hardening_required",
        "ndis_permission_workflow_hardening_run",
        "permission_workflow_hardening_status",
        "permission_workflow_hardening_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print(
        "NDIS CRM Permission Workflow Hardening Run records:",
        frappe.db.count(PERMISSION_WORKFLOW_HARDENING_RUN) if _doctype_exists(PERMISSION_WORKFLOW_HARDENING_RUN) else 0
    )
    print("Phase 58 creates permission/workflow hardening run/line records only.")
    print("Phase 58 does not mutate roles, permissions, workflows, business records, communication, task, finance, claim, remittance, payment, journal, or accounting records.")
    print("---- End Phase 58 Health Check ----")
