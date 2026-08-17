import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now


CRM_DEAL = "CRM Deal"

UAT_REGRESSION_EVIDENCE_PACK_RUN = "NDIS CRM UAT Regression Evidence Pack Run"
PERMISSION_WORKFLOW_HARDENING_RUN = "NDIS CRM Permission Workflow Hardening Run"
OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"
CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"

PRODUCTION_READINESS_FREEZE_RUN = "NDIS CRM Production Readiness Freeze Run"
PRODUCTION_READINESS_FREEZE_LINE = "NDIS CRM Production Readiness Freeze Line"

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
    "Ready for Production Freeze Approval",
    "Production Freeze Approved",
    "Production Readiness Frozen",
]

APPROVED_STATUSES = [
    "Production Freeze Approved",
    "Production Readiness Frozen",
]

ALLOWED_ROLES = {
    "Administrator",
    "System Manager",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
    "Accounts Manager",
}


FREEZE_CHECKS = [
    {
        "area": "Source Evidence",
        "item": "UAT Evidence Pack Completed",
        "expected": "Phase 59 UAT Regression Evidence Pack is completed and ready.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Regression",
        "item": "Full Phase 2-59 Health Sweep",
        "expected": "Full Phase 2-59 health sweep has passed.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Health",
        "item": "Phase 60 Health Check",
        "expected": "Phase 60 health check passes.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Backup",
        "item": "Production Freeze Backup",
        "expected": "Backup with files completed before Phase 60 changes.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Fixture Safety",
        "item": "Known Fixture Sync Stall Captured",
        "expected": "Known bench migrate fixture-sync stall is documented; direct export-fixtures --app ndis_crm is the accepted safe export path.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Fixtures",
        "item": "Client Script Fixture Count",
        "expected": "Client Script fixture has at least 85 NDIS CRM scripts before Phase 60 export and increases after Phase 60 export.",
        "manual": 0,
        "risk": "Medium",
    },
    {
        "area": "Hooks",
        "item": "Final CRM Deal Validator Chain",
        "expected": "CRM Deal validate hook points to Phase 60 combined validator after install.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Code Quality",
        "item": "Python Compile",
        "expected": "Phase 60 server/setup files compile successfully.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Code Quality",
        "item": "JSON Validation",
        "expected": "All ndis_crm JSON files validate successfully.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Code Quality",
        "item": "git diff --check",
        "expected": "No whitespace or patch formatting errors.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Boundary",
        "item": "Production Freeze Boundary",
        "expected": "Phase 60 creates only production readiness freeze run/line records.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "item": "No Production Activation",
        "expected": "Phase 60 does not enable production mode or toggle live transaction posting.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "item": "No Communication or Task Creation",
        "expected": "No Communication, Email Queue, Event, ToDo, or Task records are created.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "item": "No Finance or Accounting Creation",
        "expected": "No Sales Invoice, Payment Entry, Journal Entry, GL Entry, adjustment, or bank reconciliation record is created.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "item": "No Claim or Remittance Creation",
        "expected": "No Claim Batch, Claim Line, or Remittance Import record is created.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Care Management",
        "item": "Care Management Bridge Finalised",
        "expected": "Care Management integration remains reference-only and linked.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Operational Visibility",
        "item": "Operational Dashboard Snapshot Completed",
        "expected": "Operational Dashboard Snapshot is completed and ready.",
        "manual": 0,
        "risk": "Medium",
    },
    {
        "area": "Governance",
        "item": "Permission Workflow Hardening Completed",
        "expected": "Permission Workflow Hardening is completed and ready.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Repository",
        "item": "apps/ndis_crm Clean",
        "expected": "apps/ndis_crm is clean after Phase 60 commit.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Repository",
        "item": "Unrelated Dirty Apps Preserved",
        "expected": "Existing apps/ndis_finance and apps/au_payroll dirtiness remains untouched.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Final Decision",
        "item": "V1 Production Readiness Sign-Off",
        "expected": "Responsible owner confirms V1 readiness is frozen for controlled production use.",
        "manual": 1,
        "risk": "High",
    },
]


def _check_role():
    if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform production readiness freeze actions."))


def _doctype_exists(doctype):
    return bool(doctype and frappe.db.exists("DocType", doctype))


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


def _phase60_text():
    path = Path(frappe.get_app_path("ndis_crm")) / "phase60_production_readiness_freeze.py"
    if not path.exists():
        return ""

    try:
        return path.read_text()
    except Exception:
        return ""


def _source_uat_completed(uat_run):
    if not uat_run or not frappe.db.exists(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_run):
        return False

    status, ready = frappe.db.get_value(
        UAT_REGRESSION_EVIDENCE_PACK_RUN,
        uat_run,
        ["status", "uat_regression_evidence_pack_run_ready"],
    )

    return status == "UAT Evidence Completed" and bool(ready)


def _is_freeze_approved(run):
    if not run or not frappe.db.exists(PRODUCTION_READINESS_FREEZE_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        PRODUCTION_READINESS_FREEZE_RUN,
        run,
        ["status", "production_readiness_freeze_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _existing_run_for_uat(uat_run):
    if not _doctype_exists(PRODUCTION_READINESS_FREEZE_RUN):
        return None

    existing = _get_first_existing_value(
        UAT_REGRESSION_EVIDENCE_PACK_RUN,
        uat_run,
        [
            "ndis_production_readiness_freeze_run",
            "production_readiness_freeze_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        PRODUCTION_READINESS_FREEZE_RUN,
        {"uat_regression_evidence_pack_run": uat_run},
        "name",
        order_by="creation desc",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(PRODUCTION_READINESS_FREEZE_RUN):
        return None

    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_production_readiness_freeze_run",
            "production_readiness_freeze_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        PRODUCTION_READINESS_FREEZE_RUN,
        {"crm_deal": deal},
        "name",
        order_by="creation desc",
    )


def _get_uat_for_deal(deal):
    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_uat_regression_evidence_pack_run",
            "uat_regression_evidence_pack_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(UAT_REGRESSION_EVIDENCE_PACK_RUN, {"crm_deal": deal}, "name", order_by="creation desc")


def _evaluate_uat_completed(doc):
    if _source_uat_completed(doc.get("uat_regression_evidence_pack_run")):
        return "Pass", "UAT Regression Evidence Pack is completed and ready."

    return "Needs Attention", "UAT Regression Evidence Pack is not completed or not linked."


def _evaluate_client_script_fixture():
    client_scripts = _read_json_fixture("client_script.json")
    ndis_scripts = [row for row in client_scripts if str(row.get("name", "")).startswith("NDIS CRM")]

    if len(client_scripts) >= 85 and len(ndis_scripts) >= 85:
        return "Pass", f"Client Script fixture present: total={len(client_scripts)}, ndis={len(ndis_scripts)}."

    return "Needs Attention", f"Client Script fixture below expected: total={len(client_scripts)}, ndis={len(ndis_scripts)}."


def _evaluate_validator_chain():
    hooks = _hooks_text()

    if "phase60_production_readiness_freeze.validate_crm_deal_phase60_combined" in hooks:
        return "Pass", "CRM Deal validate hook points to Phase 60 combined validator."

    if "phase59_uat_regression_evidence_pack.validate_crm_deal_phase59_combined" in hooks:
        return "Manual Review", "CRM Deal validate hook still points to Phase 59. This is acceptable before Phase 60 hooks are installed."

    return "Needs Attention", "CRM Deal validate hook does not show Phase 59 or Phase 60 combined validator."


def _evaluate_no_production_activation():
    text = _phase60_text()
    bad_patterns = [
        "production_mode_enabled = 1",
        "enable_" + "production",
        "activate_" + "production",
        "submit" + "(",
        "." + "submit" + "()",
        "frappe." + "send" + "mail",
    ]

    found = [pattern for pattern in bad_patterns if pattern in text]

    if found:
        return "Needs Attention", "Production/boundary-sensitive pattern found: " + ", ".join(found)

    return "Pass", "No production activation, submit, or email-send pattern found in Phase 60 source."


def _evaluate_boundary_source_only():
    text = _phase60_text()

    if (
        "frappe.new_doc(PRODUCTION_READINESS_FREEZE_RUN)" in text
        and "." + "submit" + "()" not in text
        and "frappe." + "send" + "mail" not in text
    ):
        return "Pass", "Phase 60 source creates only the Production Readiness Freeze Run."

    return "Needs Attention", "Review Phase 60 source boundary manually."


def _evaluate_operational_dashboard(doc):
    run = doc.get("operational_dashboard_snapshot_run")
    if not run or not frappe.db.exists(OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, run):
        return "Needs Attention", "Operational Dashboard Snapshot is not linked."

    status, ready = frappe.db.get_value(
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        run,
        ["status", "operational_dashboard_snapshot_run_ready"],
    )

    if status == "Dashboard Snapshot Completed" and ready:
        return "Pass", "Operational Dashboard Snapshot is completed and ready."

    return "Needs Attention", f"Operational Dashboard Snapshot status={status}, ready={ready}."


def _evaluate_hardening(doc):
    run = doc.get("permission_workflow_hardening_run")
    if not run or not frappe.db.exists(PERMISSION_WORKFLOW_HARDENING_RUN, run):
        return "Needs Attention", "Permission Workflow Hardening Run is not linked."

    status, ready = frappe.db.get_value(
        PERMISSION_WORKFLOW_HARDENING_RUN,
        run,
        ["status", "permission_workflow_hardening_run_ready"],
    )

    if status == "Hardening Completed" and ready:
        return "Pass", "Permission Workflow Hardening is completed and ready."

    return "Needs Attention", f"Permission Workflow Hardening status={status}, ready={ready}."


def _evaluate_default(check, doc):
    item = check.get("item")

    if item == "UAT Evidence Pack Completed":
        return _evaluate_uat_completed(doc)

    if item == "Client Script Fixture Count":
        return _evaluate_client_script_fixture()

    if item == "Final CRM Deal Validator Chain":
        return _evaluate_validator_chain()

    if item == "Production Freeze Boundary":
        return _evaluate_boundary_source_only()

    if item == "No Production Activation":
        return _evaluate_no_production_activation()

    if item in [
        "No Communication or Task Creation",
        "No Finance or Accounting Creation",
        "No Claim or Remittance Creation",
    ]:
        return _evaluate_no_production_activation()

    if item == "Operational Dashboard Snapshot Completed":
        return _evaluate_operational_dashboard(doc)

    if item == "Permission Workflow Hardening Completed":
        return _evaluate_hardening(doc)

    if check.get("manual"):
        return "Manual Review", "Manual production-readiness evidence required."

    return "Manual Review", "Review and record evidence."


def _append_line_if_missing(doc, check):
    existing = {
        row.freeze_item
        for row in doc.get("production_readiness_freeze_lines") or []
        if row.get("freeze_item")
    }

    if check["item"] in existing:
        return False

    observed_status, observed_result = _evaluate_default(check, doc)

    doc.append("production_readiness_freeze_lines", {
        "freeze_area": check.get("area"),
        "freeze_item": check.get("item"),
        "expected_condition": check.get("expected"),
        "observed_status": observed_status,
        "observed_result": observed_result,
        "risk_level": check.get("risk") or "Medium",
        "evidence_reference": None,
        "review_owner": frappe.session.user,
        "reviewed_on": None,
        "freeze_review_complete": 0,
        "condition_verified": 1 if observed_status == "Pass" else 0,
        "blocker_found": 1 if observed_status == "Needs Attention" else 0,
        "blocker_summary": observed_result if observed_status == "Needs Attention" else None,
        "blocker_resolved": 0 if observed_status == "Needs Attention" else 1,
        "line_ready_for_freeze": 0,
        "freeze_line_status": "Draft",
    })

    return True


def _generate_lines(doc, refresh=False):
    if refresh:
        doc.set("production_readiness_freeze_lines", [])

    created = 0

    for check in FREEZE_CHECKS:
        if _append_line_if_missing(doc, check):
            created += 1

    return created


def _active_lines(doc):
    return doc.get("production_readiness_freeze_lines") or []


def _calculate_totals(doc):
    totals = {
        "freeze_line_count": 0,
        "passed_condition_count": 0,
        "manual_review_count": 0,
        "attention_condition_count": 0,
        "ready_freeze_line_count": 0,
        "completed_freeze_line_count": 0,
        "blocker_found_count": 0,
        "blocker_resolved_count": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
    }

    for row in _active_lines(doc):
        totals["freeze_line_count"] += 1

        if row.get("observed_status") == "Pass":
            totals["passed_condition_count"] += 1
        elif row.get("observed_status") == "Needs Attention":
            totals["attention_condition_count"] += 1
        else:
            totals["manual_review_count"] += 1

        if row.get("line_ready_for_freeze"):
            totals["ready_freeze_line_count"] += 1

        if row.get("freeze_line_status") == "Freeze Completed":
            totals["completed_freeze_line_count"] += 1

        if row.get("blocker_found"):
            totals["blocker_found_count"] += 1

        if row.get("blocker_resolved"):
            totals["blocker_resolved_count"] += 1

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
        if _field_exists(PRODUCTION_READINESS_FREEZE_RUN, fieldname):
            doc.set(fieldname, value)

    if totals["freeze_line_count"]:
        doc.freeze_completion_percent = round(
            (totals["ready_freeze_line_count"] / totals["freeze_line_count"]) * 100,
            2,
        )
    else:
        doc.freeze_completion_percent = 0

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "UAT Regression Evidence Pack linked",
        "complete": bool(doc.get("uat_regression_evidence_pack_run")),
    })

    checks.append({
        "label": "UAT Regression Evidence Pack completed",
        "complete": _source_uat_completed(doc.get("uat_regression_evidence_pack_run")),
    })

    checks.append({
        "label": "CRM Deal linked",
        "complete": bool(doc.get("crm_deal")),
    })

    checks.append({
        "label": "Freeze owner assigned",
        "complete": bool(doc.get("freeze_owner")),
    })

    checks.append({
        "label": "Freeze mode is readiness freeze only",
        "complete": doc.get("freeze_mode") == "Readiness Freeze Only",
    })

    blocked_fields = [
        ("Production Activation Allowed remains blocked in Phase 60", "production_activation_allowed"),
        ("Business Record Creation Allowed remains blocked in Phase 60", "business_record_creation_allowed"),
        ("Care Management Mutation Allowed remains blocked in Phase 60", "care_management_mutation_allowed"),
        ("Communication Creation Allowed remains blocked in Phase 60", "communication_creation_allowed"),
        ("Email Send Allowed remains blocked in Phase 60", "email_send_allowed"),
        ("Event Creation Allowed remains blocked in Phase 60", "event_creation_allowed"),
        ("ToDo Creation Allowed remains blocked in Phase 60", "todo_creation_allowed"),
        ("Task Creation Allowed remains blocked in Phase 60", "task_creation_allowed"),
        ("Finance Document Creation Allowed remains blocked in Phase 60", "finance_document_creation_allowed"),
        ("Claim Document Creation Allowed remains blocked in Phase 60", "claim_document_creation_allowed"),
        ("Remittance Document Creation Allowed remains blocked in Phase 60", "remittance_document_creation_allowed"),
        ("Accounting Document Creation Allowed remains blocked in Phase 60", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_fields:
        checks.append({
            "label": label,
            "complete": not bool(doc.get(fieldname)),
        })

    lines = _active_lines(doc)

    checks.append({
        "label": "Production readiness freeze lines exist",
        "complete": bool(lines),
    })

    if lines:
        checks.extend([
            {
                "label": "All freeze lines reviewed",
                "complete": not [row.freeze_item for row in lines if not row.get("freeze_review_complete")],
            },
            {
                "label": "All freeze conditions verified",
                "complete": not [row.freeze_item for row in lines if not row.get("condition_verified")],
            },
            {
                "label": "All found blockers resolved",
                "complete": not [row.freeze_item for row in lines if row.get("blocker_found") and not row.get("blocker_resolved")],
            },
            {
                "label": "No unresolved high-risk condition remains",
                "complete": not [
                    row.freeze_item
                    for row in lines
                    if row.get("risk_level") == "High"
                    and row.get("blocker_found")
                    and not row.get("blocker_resolved")
                ],
            },
            {
                "label": "All lines ready for freeze",
                "complete": not [row.freeze_item for row in lines if not row.get("line_ready_for_freeze")],
            },
        ])

    checks.append({
        "label": "Final production readiness review complete",
        "complete": bool(doc.get("final_production_readiness_review_complete")),
    })

    checks.append({
        "label": "Boundary freeze review complete",
        "complete": bool(doc.get("boundary_freeze_review_complete")),
    })

    checks.append({
        "label": "Regression freeze review complete",
        "complete": bool(doc.get("regression_freeze_review_complete")),
    })

    checks.append({
        "label": "Fixture freeze review complete",
        "complete": bool(doc.get("fixture_freeze_review_complete")),
    })

    checks.append({
        "label": "Repository freeze review complete",
        "complete": bool(doc.get("repository_freeze_review_complete")),
    })

    checks.append({
        "label": "Production readiness sign-off confirmed",
        "complete": bool(doc.get("production_readiness_sign_off_confirmed")),
    })

    total = len(checks)
    complete = len([row for row in checks if row["complete"]])
    readiness_percent = round((complete / total) * 100, 2) if total else 0
    incomplete = [row["label"] for row in checks if not row["complete"]]

    return {
        "total_checks": total,
        "complete_checks": complete,
        "readiness_percent": readiness_percent,
        "production_readiness_freeze_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.production_readiness_freeze_run_ready = 1 if summary["production_readiness_freeze_run_ready"] else 0

    targets = [
        (CRM_DEAL, doc.get("crm_deal")),
        (UAT_REGRESSION_EVIDENCE_PACK_RUN, doc.get("uat_regression_evidence_pack_run")),
        (PERMISSION_WORKFLOW_HARDENING_RUN, doc.get("permission_workflow_hardening_run")),
        (OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, doc.get("operational_dashboard_snapshot_run")),
        (CARE_MANAGEMENT_INTEGRATION_RUN, doc.get("care_management_integration_run")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_production_readiness_freeze_run", doc.name)
        _db_set_if_field(doctype, name, "production_readiness_freeze_status", doc.status)
        _db_set_if_field(doctype, name, "production_readiness_freeze_ready", 1 if summary["production_readiness_freeze_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


def _copy_uat_values(doc, source):
    doc.uat_regression_evidence_pack_run = source.name
    doc.permission_workflow_hardening_run = source.get("permission_workflow_hardening_run")
    doc.operational_dashboard_snapshot_run = source.get("operational_dashboard_snapshot_run")
    doc.care_management_integration_run = source.get("care_management_integration_run")
    doc.crm_deal = source.get("crm_deal")
    doc.crm_lead = source.get("crm_lead")
    doc.participant_customer = source.get("participant_customer")
    doc.participant_service_file = source.get("participant_service_file")
    doc.participant_name = source.get("participant_name") or source.get("participant_customer") or source.name
    doc.ndis_number = source.get("ndis_number")
    doc.plan_start_date = source.get("plan_start_date")
    doc.plan_end_date = source.get("plan_end_date")
    doc.company = source.get("company")


@frappe.whitelist()
def create_production_readiness_freeze_from_uat(uat_regression_evidence_pack_run):
    _check_role()

    if not uat_regression_evidence_pack_run:
        frappe.throw(_("UAT Regression Evidence Pack Run is required."))

    if not frappe.db.exists(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_regression_evidence_pack_run):
        frappe.throw(_("UAT Regression Evidence Pack Run {0} was not found.").format(uat_regression_evidence_pack_run))

    existing = _existing_run_for_uat(uat_regression_evidence_pack_run)
    if existing:
        return {
            "doctype": PRODUCTION_READINESS_FREEZE_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Production Readiness Freeze Run returned.",
        }

    source = frappe.get_doc(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_regression_evidence_pack_run)

    doc = frappe.new_doc(PRODUCTION_READINESS_FREEZE_RUN)
    doc.status = "Draft"
    doc.freeze_mode = "Readiness Freeze Only"
    doc.freeze_owner = frappe.session.user

    doc.production_freeze_completion_allowed = 0
    doc.production_activation_allowed = 0
    doc.business_record_creation_allowed = 0
    doc.care_management_mutation_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.finance_document_creation_allowed = 0
    doc.claim_document_creation_allowed = 0
    doc.remittance_document_creation_allowed = 0
    doc.accounting_document_creation_allowed = 0

    _copy_uat_values(doc, source)
    created_count = _generate_lines(doc, refresh=False)

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.production_readiness_freeze_run_ready = 1 if summary["production_readiness_freeze_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PRODUCTION_READINESS_FREEZE_RUN,
        "name": doc.name,
        "created": True,
        "freeze_line_count": created_count,
        "message": "NDIS CRM Production Readiness Freeze Run created successfully.",
    }


@frappe.whitelist()
def create_production_readiness_freeze_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": PRODUCTION_READINESS_FREEZE_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Production Readiness Freeze Run returned.",
        }

    source_run = _get_uat_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM UAT Regression Evidence Pack Run before creating Production Readiness Freeze."))

    return create_production_readiness_freeze_from_uat(source_run)


@frappe.whitelist()
def refresh_production_readiness_freeze_lines(production_readiness_freeze_run):
    _check_role()

    doc = frappe.get_doc(PRODUCTION_READINESS_FREEZE_RUN, production_readiness_freeze_run)
    created_count = _generate_lines(doc, refresh=True)

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Production readiness freeze lines refreshed. Lines: {created_count}.",
    }


@frappe.whitelist()
def validate_production_readiness_freeze(production_readiness_freeze_run):
    _check_role()

    doc = frappe.get_doc(PRODUCTION_READINESS_FREEZE_RUN, production_readiness_freeze_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Production Readiness Freeze validated.",
    }


@frappe.whitelist()
def mark_ready_for_production_freeze(production_readiness_freeze_run):
    _check_role()

    doc = frappe.get_doc(PRODUCTION_READINESS_FREEZE_RUN, production_readiness_freeze_run)
    summary = _calculate_readiness(doc)

    if not summary["production_readiness_freeze_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Production Freeze Approval. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Production Freeze Approval"
    doc.readiness_percent = summary["readiness_percent"]
    doc.production_readiness_freeze_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PRODUCTION_READINESS_FREEZE_RUN,
        "name": doc.name,
        "message": "Production Readiness Freeze marked Ready for Approval.",
    }


@frappe.whitelist()
def approve_production_readiness_freeze(production_readiness_freeze_run):
    _check_role()

    doc = frappe.get_doc(PRODUCTION_READINESS_FREEZE_RUN, production_readiness_freeze_run)
    summary = _calculate_readiness(doc)

    if not summary["production_readiness_freeze_run_ready"]:
        frappe.throw(
            _("Cannot approve Production Readiness Freeze. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Production Freeze Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.production_readiness_freeze_run_ready = 1
    doc.production_freeze_completion_allowed = 0

    for row in doc.get("production_readiness_freeze_lines") or []:
        if row.get("freeze_line_status") in ["Draft", "Ready"]:
            row.freeze_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": PRODUCTION_READINESS_FREEZE_RUN,
        "name": doc.name,
        "message": "Production Readiness Freeze approved. Production mode was not enabled and no business record was mutated.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("freeze_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("freeze_review_complete"):
            continue

        if not row.get("condition_verified"):
            continue

        if row.get("blocker_found") and not row.get("blocker_resolved"):
            continue

        if not row.get("line_ready_for_freeze"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_production_readiness_freeze(production_readiness_freeze_run):
    _check_role()

    doc = frappe.get_doc(PRODUCTION_READINESS_FREEZE_RUN, production_readiness_freeze_run)

    if doc.status != "Production Freeze Approved":
        frappe.throw(_("Production Readiness Freeze must be approved before completion."))

    if not doc.get("production_freeze_completion_allowed"):
        frappe.throw(_("Tick Production Freeze Completion Allowed before completing the freeze."))

    if (doc.get("freeze_mode") or "Readiness Freeze Only") != "Readiness Freeze Only":
        frappe.throw(_("Phase 60 supports readiness-freeze mode only."))

    blocked_fields = [
        ("Production Activation Allowed", "production_activation_allowed"),
        ("Business Record Creation Allowed", "business_record_creation_allowed"),
        ("Care Management Mutation Allowed", "care_management_mutation_allowed"),
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
            frappe.throw(_("{0} must remain unticked in Phase 60.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["production_readiness_freeze_run_ready"]:
        frappe.throw(
            _("Cannot complete Production Readiness Freeze. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines:
        frappe.throw(_("No ready Production Readiness Freeze lines found."))

    for row in ready_lines:
        row.freeze_line_status = "Freeze Completed"
        if not row.get("reviewed_on"):
            row.reviewed_on = now()

    doc.status = "Production Readiness Frozen"
    doc.production_freeze_completion_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "completed_line_count": len(ready_lines),
        "message": "Production readiness frozen for V1. Production mode was not enabled. No business, Care Management, communication, email, event, task, finance, claim, remittance, payment, journal, GL, adjustment, or bank reconciliation records were created or updated.",
    }


def validate_production_readiness_freeze_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.production_readiness_freeze_run_ready = 1 if summary["production_readiness_freeze_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["production_readiness_freeze_run_ready"]:
        frappe.throw(
            _("Cannot set Production Readiness Freeze Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Production Freeze Approved" and doc.get("production_freeze_completion_allowed"):
        frappe.throw(_("Production Freeze Completion Allowed can only be ticked after the run is approved."))

    blocked_fields = [
        ("Production activation", "production_activation_allowed"),
        ("Business record creation", "business_record_creation_allowed"),
        ("Care Management mutation", "care_management_mutation_allowed"),
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
            frappe.throw(_("{0} is not allowed in Phase 60.").format(label))


def on_production_readiness_freeze_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Production Readiness Freeze Run Summary Sync Failed"
        )


def validate_crm_deal_phase60(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_production_readiness_freeze_required"):
        required = doc.get("ndis_production_readiness_freeze_required")

    if not required:
        return

    run = doc.get("ndis_production_readiness_freeze_run") if _field_exists(CRM_DEAL, "ndis_production_readiness_freeze_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Production Readiness Freeze Run must be created and approved/completed.")
        )

    if not _is_freeze_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Production Readiness Freeze Run must be approved/completed.")
        )


def validate_crm_deal_phase60_combined(doc, method=None):
    try:
        from ndis_crm.phase59_uat_regression_evidence_pack import validate_crm_deal_phase59_combined
        validate_crm_deal_phase59_combined(doc, method)
    except ImportError:
        pass

    validate_crm_deal_phase60(doc, method)


def phase60_health_check():
    print("---- NDIS CRM Phase 60 Health Check ----")

    for dt in [
        PRODUCTION_READINESS_FREEZE_LINE,
        PRODUCTION_READINESS_FREEZE_RUN,
        UAT_REGRESSION_EVIDENCE_PACK_RUN,
        PERMISSION_WORKFLOW_HARDENING_RUN,
        OPERATIONAL_DASHBOARD_SNAPSHOT_RUN,
        CARE_MANAGEMENT_INTEGRATION_RUN,
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

    for field in [
        "ndis_production_readiness_freeze_required",
        "ndis_production_readiness_freeze_run",
        "production_readiness_freeze_status",
        "production_readiness_freeze_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print(
        "NDIS CRM Production Readiness Freeze Run records:",
        frappe.db.count(PRODUCTION_READINESS_FREEZE_RUN) if _doctype_exists(PRODUCTION_READINESS_FREEZE_RUN) else 0
    )
    print("Phase 60 creates production readiness freeze run/line records only.")
    print("Phase 60 does not enable production mode.")
    print("Phase 60 does not create or update Care Management, communication, event, task, finance, claim, remittance, payment, journal, GL, accounting, adjustment, or bank reconciliation records.")
    print("---- End Phase 60 Health Check ----")
