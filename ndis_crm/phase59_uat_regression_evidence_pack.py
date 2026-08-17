import json
from pathlib import Path

import frappe
from frappe import _
from frappe.utils import now


CRM_DEAL = "CRM Deal"
PERMISSION_WORKFLOW_HARDENING_RUN = "NDIS CRM Permission Workflow Hardening Run"
OPERATIONAL_DASHBOARD_SNAPSHOT_RUN = "NDIS CRM Operational Dashboard Snapshot Run"
CARE_MANAGEMENT_INTEGRATION_RUN = "NDIS CRM Care Management Integration Run"

UAT_REGRESSION_EVIDENCE_PACK_RUN = "NDIS CRM UAT Regression Evidence Pack Run"
UAT_REGRESSION_EVIDENCE_PACK_LINE = "NDIS CRM UAT Regression Evidence Pack Line"

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
    "Ready for UAT Sign Off",
    "UAT Evidence Approved",
    "UAT Evidence Completed",
]

APPROVED_STATUSES = [
    "UAT Evidence Approved",
    "UAT Evidence Completed",
]

ALLOWED_ROLES = {
    "Administrator",
    "System Manager",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
    "Accounts Manager",
}


UAT_CHECKS = [
    {
        "area": "Environment",
        "scenario": "Backup Evidence",
        "expected": "Backup completed before Phase 59 changes.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Environment",
        "scenario": "Known Fixture Sync Handling",
        "expected": "bench migrate schema sync completed; known Syncing fixtures stall handled with direct export-fixtures --app ndis_crm.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Code Quality",
        "scenario": "Python Compile",
        "expected": "All ndis_crm Python files compile successfully.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Code Quality",
        "scenario": "JSON Validation",
        "expected": "All DocType and fixture JSON files validate successfully.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Code Quality",
        "scenario": "git diff --check",
        "expected": "No whitespace or patch formatting errors.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Fixtures",
        "scenario": "Client Script Fixture Count",
        "expected": "Client Script fixture contains at least 83 NDIS CRM scripts before Phase 59 and increases after export.",
        "manual": 0,
        "risk": "Medium",
    },
    {
        "area": "Hooks",
        "scenario": "CRM Deal Validator Chain",
        "expected": "CRM Deal validate hook points to Phase 58 combined validator before Phase 59 and Phase 59 combined validator after install.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Phase Health",
        "scenario": "Phase 2-58 Regression",
        "expected": "Full Phase 2-58 health sweep passes.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Phase Health",
        "scenario": "Phase 59 Health",
        "expected": "Phase 59 health check passes.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "scenario": "Business Record Boundary",
        "expected": "Phase 59 creates only UAT evidence run/line records.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "scenario": "Communication Boundary",
        "expected": "No Communication, Email Queue, Event, ToDo, or Task records are created by Phase 59.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "scenario": "Finance Boundary",
        "expected": "No Sales Invoice, Payment Entry, Journal Entry, GL Entry, adjustment, or bank reconciliation record is created by Phase 59.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Boundary",
        "scenario": "Claim / Remittance Boundary",
        "expected": "No Claim Batch, Claim Line, or Remittance Import record is created by Phase 59.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Care Management",
        "scenario": "Reference-Only Integration",
        "expected": "Care Management Integration remains reference-only and no Care Management records are created/updated/deleted by this chain.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "CRM",
        "scenario": "CRM Lead to Deal Flow",
        "expected": "CRM Lead / Participant Intake / CRM Deal flow remains linked and guarded.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Operations",
        "scenario": "Service File / Schedule / Roster Flow",
        "expected": "Operations setup, schedule draft, roster request, service file, session draft, evidence review, and downstream prep remain linked.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Billing",
        "scenario": "Billing to Invoice Flow",
        "expected": "Billing Draft, Claim Draft, Invoice Draft, Sales Invoice Draft Run, and Sales Invoice Submission Run remain linked and controlled.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Claims",
        "scenario": "Claim Export / Lodgement Flow",
        "expected": "Claim batch, export preparation, and lodgement confirmation remain controlled.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Payments",
        "scenario": "Remittance / Payment Flow",
        "expected": "Remittance preparation, actual remittance import, matching, allocation, payment draft, payment submission, and finalisation remain controlled.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Variance",
        "scenario": "Variance / Write-Off Flow",
        "expected": "Variance rejection review, write-off preparation, draft, JE draft, JE submission, and write-off finalisation remain controlled.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Recovery",
        "scenario": "Recovery Flow",
        "expected": "Recovery preparation, case draft/submission, follow-up, communication, outcome capture, action, closure, and post-closure routing remain controlled.",
        "manual": 1,
        "risk": "High",
    },
    {
        "area": "Dashboard",
        "scenario": "Operational Dashboard Snapshot",
        "expected": "Operational dashboard gives read-only snapshot across CRM, finance, recovery, and Care Management integration.",
        "manual": 1,
        "risk": "Medium",
    },
    {
        "area": "Hardening",
        "scenario": "Permission Workflow Hardening",
        "expected": "Permission Workflow Hardening is completed and ready before UAT pack sign-off.",
        "manual": 0,
        "risk": "High",
    },
    {
        "area": "Repository",
        "scenario": "Repository Hygiene",
        "expected": "apps/ndis_crm is clean after Phase 59 commit and unrelated dirty apps remain untouched.",
        "manual": 1,
        "risk": "Medium",
    },
]


def _check_role():
    if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform UAT regression evidence actions."))


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


def _source_hardening_completed(hardening_run):
    if not hardening_run or not frappe.db.exists(PERMISSION_WORKFLOW_HARDENING_RUN, hardening_run):
        return False

    status, ready = frappe.db.get_value(
        PERMISSION_WORKFLOW_HARDENING_RUN,
        hardening_run,
        ["status", "permission_workflow_hardening_run_ready"],
    )

    return status == "Hardening Completed" and bool(ready)


def _is_uat_approved(run):
    if not run or not frappe.db.exists(UAT_REGRESSION_EVIDENCE_PACK_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        UAT_REGRESSION_EVIDENCE_PACK_RUN,
        run,
        ["status", "uat_regression_evidence_pack_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _existing_run_for_hardening(hardening_run):
    if not _doctype_exists(UAT_REGRESSION_EVIDENCE_PACK_RUN):
        return None

    existing = _get_first_existing_value(
        PERMISSION_WORKFLOW_HARDENING_RUN,
        hardening_run,
        [
            "ndis_uat_regression_evidence_pack_run",
            "uat_regression_evidence_pack_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        UAT_REGRESSION_EVIDENCE_PACK_RUN,
        {"permission_workflow_hardening_run": hardening_run},
        "name",
        order_by="creation desc",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(UAT_REGRESSION_EVIDENCE_PACK_RUN):
        return None

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

    return frappe.db.get_value(
        UAT_REGRESSION_EVIDENCE_PACK_RUN,
        {"crm_deal": deal},
        "name",
        order_by="creation desc",
    )


def _get_hardening_for_deal(deal):
    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_permission_workflow_hardening_run",
            "permission_workflow_hardening_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(PERMISSION_WORKFLOW_HARDENING_RUN, {"crm_deal": deal}, "name", order_by="creation desc")


def _evaluate_client_script_fixture():
    client_scripts = _read_json_fixture("client_script.json")
    ndis_scripts = [row for row in client_scripts if str(row.get("name", "")).startswith("NDIS CRM")]

    if len(client_scripts) >= 83 and len(ndis_scripts) >= 83:
        return "Pass", f"Client Script fixture present: total={len(client_scripts)}, ndis={len(ndis_scripts)}."

    return "Needs Attention", f"Client Script fixture below expected: total={len(client_scripts)}, ndis={len(ndis_scripts)}."


def _evaluate_crm_deal_validator_chain():
    hooks = _hooks_text()

    if "phase59_uat_regression_evidence_pack.validate_crm_deal_phase59_combined" in hooks:
        return "Pass", "CRM Deal validate hook points to Phase 59 combined validator."

    if "phase58_permission_workflow_hardening.validate_crm_deal_phase58_combined" in hooks:
        return "Manual Review", "CRM Deal validate hook still points to Phase 58. This is acceptable before Phase 59 hooks are installed."

    return "Needs Attention", "CRM Deal validate hook does not show Phase 58 or Phase 59 combined validator."


def _evaluate_hardening_completed(doc):
    if _source_hardening_completed(doc.get("permission_workflow_hardening_run")):
        return "Pass", "Permission Workflow Hardening Run is completed and ready."

    return "Needs Attention", "Permission Workflow Hardening Run is not completed or not linked."


def _evaluate_business_boundary():
    phase_file = Path(frappe.get_app_path("ndis_crm")) / "phase59_uat_regression_evidence_pack.py"

    if not phase_file.exists():
        return "Needs Attention", "Phase 59 file not found."

    text = phase_file.read_text()

    bad_patterns = [
        "frappe.sendmail",
        ".submit()",
        "make_communication",
        "frappe.get_doc({\"doctype\": \"Communication\"",
        "frappe.get_doc({'doctype': 'Communication'",
    ]

    found = [pattern for pattern in bad_patterns if pattern in text]

    if found:
        return "Needs Attention", "Boundary-sensitive pattern found: " + ", ".join(found)

    return "Pass", "No sendmail/submit/communication creation pattern found in Phase 59 source."


def _evaluate_default(check, doc):
    scenario = check.get("scenario")

    if scenario == "Client Script Fixture Count":
        return _evaluate_client_script_fixture()

    if scenario == "CRM Deal Validator Chain":
        return _evaluate_crm_deal_validator_chain()

    if scenario == "Permission Workflow Hardening":
        return _evaluate_hardening_completed(doc)

    if scenario in [
        "Business Record Boundary",
        "Communication Boundary",
        "Finance Boundary",
        "Claim / Remittance Boundary",
    ]:
        return _evaluate_business_boundary()

    if check.get("manual"):
        return "Manual Review", "Manual evidence required."

    return "Manual Review", "Review and attach/record evidence."


def _append_line_if_missing(doc, check):
    existing = {
        row.uat_scenario
        for row in doc.get("uat_regression_evidence_lines") or []
        if row.get("uat_scenario")
    }

    if check["scenario"] in existing:
        return False

    observed_status, observed_result = _evaluate_default(check, doc)

    doc.append("uat_regression_evidence_lines", {
        "uat_area": check.get("area"),
        "uat_scenario": check.get("scenario"),
        "expected_result": check.get("expected"),
        "observed_status": observed_status,
        "observed_result": observed_result,
        "risk_level": check.get("risk") or "Medium",
        "evidence_reference": None,
        "tester": frappe.session.user,
        "tested_on": None,
        "uat_review_complete": 0,
        "uat_evidence_recorded": 1 if observed_status == "Pass" else 0,
        "issue_found": 1 if observed_status == "Needs Attention" else 0,
        "issue_summary": observed_result if observed_status == "Needs Attention" else None,
        "issue_resolved": 0 if observed_status == "Needs Attention" else 1,
        "line_ready_for_uat_sign_off": 0,
        "uat_line_status": "Draft",
    })

    return True


def _generate_lines(doc, refresh=False):
    if refresh:
        doc.set("uat_regression_evidence_lines", [])

    created = 0

    for check in UAT_CHECKS:
        if _append_line_if_missing(doc, check):
            created += 1

    return created


def _active_lines(doc):
    return doc.get("uat_regression_evidence_lines") or []


def _calculate_totals(doc):
    totals = {
        "uat_line_count": 0,
        "passed_uat_count": 0,
        "manual_review_count": 0,
        "attention_uat_count": 0,
        "ready_uat_line_count": 0,
        "completed_uat_line_count": 0,
        "issue_found_count": 0,
        "issue_resolved_count": 0,
        "high_risk_count": 0,
        "medium_risk_count": 0,
        "low_risk_count": 0,
    }

    for row in _active_lines(doc):
        totals["uat_line_count"] += 1

        if row.get("observed_status") == "Pass":
            totals["passed_uat_count"] += 1
        elif row.get("observed_status") == "Needs Attention":
            totals["attention_uat_count"] += 1
        else:
            totals["manual_review_count"] += 1

        if row.get("line_ready_for_uat_sign_off"):
            totals["ready_uat_line_count"] += 1

        if row.get("uat_line_status") == "UAT Completed":
            totals["completed_uat_line_count"] += 1

        if row.get("issue_found"):
            totals["issue_found_count"] += 1

        if row.get("issue_resolved"):
            totals["issue_resolved_count"] += 1

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
        if _field_exists(UAT_REGRESSION_EVIDENCE_PACK_RUN, fieldname):
            doc.set(fieldname, value)

    if totals["uat_line_count"]:
        doc.uat_completion_percent = round(
            (totals["ready_uat_line_count"] / totals["uat_line_count"]) * 100,
            2,
        )
    else:
        doc.uat_completion_percent = 0

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Permission Workflow Hardening Run linked",
        "complete": bool(doc.get("permission_workflow_hardening_run")),
    })

    checks.append({
        "label": "Permission Workflow Hardening completed",
        "complete": _source_hardening_completed(doc.get("permission_workflow_hardening_run")),
    })

    checks.append({
        "label": "CRM Deal linked",
        "complete": bool(doc.get("crm_deal")),
    })

    checks.append({
        "label": "UAT owner assigned",
        "complete": bool(doc.get("uat_owner")),
    })

    checks.append({
        "label": "Evidence mode is controlled evidence only",
        "complete": doc.get("uat_mode") == "Controlled Evidence Pack Only",
    })

    blocked_fields = [
        ("Business Record Creation Allowed remains blocked in Phase 59", "business_record_creation_allowed"),
        ("Care Management Mutation Allowed remains blocked in Phase 59", "care_management_mutation_allowed"),
        ("Communication Creation Allowed remains blocked in Phase 59", "communication_creation_allowed"),
        ("Email Send Allowed remains blocked in Phase 59", "email_send_allowed"),
        ("Event Creation Allowed remains blocked in Phase 59", "event_creation_allowed"),
        ("ToDo Creation Allowed remains blocked in Phase 59", "todo_creation_allowed"),
        ("Task Creation Allowed remains blocked in Phase 59", "task_creation_allowed"),
        ("Finance Document Creation Allowed remains blocked in Phase 59", "finance_document_creation_allowed"),
        ("Claim Document Creation Allowed remains blocked in Phase 59", "claim_document_creation_allowed"),
        ("Remittance Document Creation Allowed remains blocked in Phase 59", "remittance_document_creation_allowed"),
        ("Accounting Document Creation Allowed remains blocked in Phase 59", "accounting_document_creation_allowed"),
    ]

    for label, fieldname in blocked_fields:
        checks.append({
            "label": label,
            "complete": not bool(doc.get(fieldname)),
        })

    lines = _active_lines(doc)

    checks.append({
        "label": "UAT evidence lines exist",
        "complete": bool(lines),
    })

    if lines:
        checks.extend([
            {
                "label": "All UAT lines reviewed",
                "complete": not [row.uat_scenario for row in lines if not row.get("uat_review_complete")],
            },
            {
                "label": "All UAT evidence recorded",
                "complete": not [row.uat_scenario for row in lines if not row.get("uat_evidence_recorded")],
            },
            {
                "label": "All found issues resolved",
                "complete": not [row.uat_scenario for row in lines if row.get("issue_found") and not row.get("issue_resolved")],
            },
            {
                "label": "No unhandled high-risk scenario remains",
                "complete": not [
                    row.uat_scenario
                    for row in lines
                    if row.get("risk_level") == "High"
                    and row.get("observed_status") == "Needs Attention"
                    and not row.get("issue_resolved")
                ],
            },
            {
                "label": "All lines ready for UAT sign-off",
                "complete": not [row.uat_scenario for row in lines if not row.get("line_ready_for_uat_sign_off")],
            },
        ])

    checks.append({
        "label": "Final UAT review complete",
        "complete": bool(doc.get("final_uat_review_complete")),
    })

    checks.append({
        "label": "Boundary evidence review complete",
        "complete": bool(doc.get("boundary_evidence_review_complete")),
    })

    checks.append({
        "label": "Regression evidence review complete",
        "complete": bool(doc.get("regression_evidence_review_complete")),
    })

    checks.append({
        "label": "Fixture evidence review complete",
        "complete": bool(doc.get("fixture_evidence_review_complete")),
    })

    checks.append({
        "label": "Repository evidence review complete",
        "complete": bool(doc.get("repository_evidence_review_complete")),
    })

    total = len(checks)
    complete = len([row for row in checks if row["complete"]])
    readiness_percent = round((complete / total) * 100, 2) if total else 0
    incomplete = [row["label"] for row in checks if not row["complete"]]

    return {
        "total_checks": total,
        "complete_checks": complete,
        "readiness_percent": readiness_percent,
        "uat_regression_evidence_pack_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.uat_regression_evidence_pack_run_ready = 1 if summary["uat_regression_evidence_pack_run_ready"] else 0

    targets = [
        (CRM_DEAL, doc.get("crm_deal")),
        (PERMISSION_WORKFLOW_HARDENING_RUN, doc.get("permission_workflow_hardening_run")),
        (OPERATIONAL_DASHBOARD_SNAPSHOT_RUN, doc.get("operational_dashboard_snapshot_run")),
        (CARE_MANAGEMENT_INTEGRATION_RUN, doc.get("care_management_integration_run")),
    ]

    for doctype, name in targets:
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_uat_regression_evidence_pack_run", doc.name)
        _db_set_if_field(doctype, name, "uat_regression_evidence_pack_status", doc.status)
        _db_set_if_field(doctype, name, "uat_regression_evidence_pack_ready", 1 if summary["uat_regression_evidence_pack_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


def _copy_hardening_values(doc, source):
    doc.permission_workflow_hardening_run = source.name
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
def create_uat_regression_evidence_pack_from_hardening(permission_workflow_hardening_run):
    _check_role()

    if not permission_workflow_hardening_run:
        frappe.throw(_("Permission Workflow Hardening Run is required."))

    if not frappe.db.exists(PERMISSION_WORKFLOW_HARDENING_RUN, permission_workflow_hardening_run):
        frappe.throw(_("Permission Workflow Hardening Run {0} was not found.").format(permission_workflow_hardening_run))

    existing = _existing_run_for_hardening(permission_workflow_hardening_run)
    if existing:
        return {
            "doctype": UAT_REGRESSION_EVIDENCE_PACK_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM UAT Regression Evidence Pack Run returned.",
        }

    source = frappe.get_doc(PERMISSION_WORKFLOW_HARDENING_RUN, permission_workflow_hardening_run)

    doc = frappe.new_doc(UAT_REGRESSION_EVIDENCE_PACK_RUN)
    doc.status = "Draft"
    doc.uat_mode = "Controlled Evidence Pack Only"
    doc.uat_owner = frappe.session.user

    doc.uat_completion_allowed = 0
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

    _copy_hardening_values(doc, source)
    created_count = _generate_lines(doc, refresh=False)

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.uat_regression_evidence_pack_run_ready = 1 if summary["uat_regression_evidence_pack_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": UAT_REGRESSION_EVIDENCE_PACK_RUN,
        "name": doc.name,
        "created": True,
        "uat_line_count": created_count,
        "message": "NDIS CRM UAT Regression Evidence Pack Run created successfully.",
    }


@frappe.whitelist()
def create_uat_regression_evidence_pack_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": UAT_REGRESSION_EVIDENCE_PACK_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM UAT Regression Evidence Pack Run returned.",
        }

    source_run = _get_hardening_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Permission Workflow Hardening Run before creating UAT Regression Evidence Pack."))

    return create_uat_regression_evidence_pack_from_hardening(source_run)


@frappe.whitelist()
def refresh_uat_regression_evidence_lines(uat_regression_evidence_pack_run):
    _check_role()

    doc = frappe.get_doc(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_regression_evidence_pack_run)
    created_count = _generate_lines(doc, refresh=True)

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"UAT regression evidence lines refreshed. Lines: {created_count}.",
    }


@frappe.whitelist()
def validate_uat_regression_evidence_readiness(uat_regression_evidence_pack_run):
    _check_role()

    doc = frappe.get_doc(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_regression_evidence_pack_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "UAT Regression Evidence Pack readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_uat_sign_off(uat_regression_evidence_pack_run):
    _check_role()

    doc = frappe.get_doc(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_regression_evidence_pack_run)
    summary = _calculate_readiness(doc)

    if not summary["uat_regression_evidence_pack_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for UAT Sign Off. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for UAT Sign Off"
    doc.readiness_percent = summary["readiness_percent"]
    doc.uat_regression_evidence_pack_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": UAT_REGRESSION_EVIDENCE_PACK_RUN,
        "name": doc.name,
        "message": "UAT Regression Evidence Pack marked Ready for Sign Off.",
    }


@frappe.whitelist()
def approve_uat_regression_evidence_pack(uat_regression_evidence_pack_run):
    _check_role()

    doc = frappe.get_doc(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_regression_evidence_pack_run)
    summary = _calculate_readiness(doc)

    if not summary["uat_regression_evidence_pack_run_ready"]:
        frappe.throw(
            _("Cannot approve UAT Regression Evidence Pack. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "UAT Evidence Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.uat_regression_evidence_pack_run_ready = 1
    doc.uat_completion_allowed = 0

    for row in doc.get("uat_regression_evidence_lines") or []:
        if row.get("uat_line_status") in ["Draft", "Ready"]:
            row.uat_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": UAT_REGRESSION_EVIDENCE_PACK_RUN,
        "name": doc.name,
        "message": "UAT Regression Evidence Pack approved. No business record was created or updated.",
    }


def _ready_lines_for_completion(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("uat_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("uat_review_complete"):
            continue

        if not row.get("uat_evidence_recorded"):
            continue

        if row.get("issue_found") and not row.get("issue_resolved"):
            continue

        if not row.get("line_ready_for_uat_sign_off"):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def complete_uat_regression_evidence_pack(uat_regression_evidence_pack_run):
    _check_role()

    doc = frappe.get_doc(UAT_REGRESSION_EVIDENCE_PACK_RUN, uat_regression_evidence_pack_run)

    if doc.status != "UAT Evidence Approved":
        frappe.throw(_("UAT Regression Evidence Pack must be approved before completion."))

    if not doc.get("uat_completion_allowed"):
        frappe.throw(_("Tick UAT Completion Allowed before completing UAT evidence pack."))

    if (doc.get("uat_mode") or "Controlled Evidence Pack Only") != "Controlled Evidence Pack Only":
        frappe.throw(_("Phase 59 supports controlled evidence pack mode only."))

    blocked_fields = [
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
            frappe.throw(_("{0} must remain unticked in Phase 59.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["uat_regression_evidence_pack_run_ready"]:
        frappe.throw(
            _("Cannot complete UAT Regression Evidence Pack. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_completion(doc)

    if not ready_lines:
        frappe.throw(_("No ready UAT Regression Evidence lines found."))

    for row in ready_lines:
        row.uat_line_status = "UAT Completed"
        if not row.get("tested_on"):
            row.tested_on = now()

    doc.status = "UAT Evidence Completed"
    doc.uat_completion_allowed = 0
    doc.completed_by = frappe.session.user
    doc.completed_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "completed_line_count": len(ready_lines),
        "message": "UAT regression evidence pack completed. No business, Care Management, communication, email, event, task, finance, claim, remittance, payment, journal, GL, adjustment, or bank reconciliation records were created or updated.",
    }


def validate_uat_regression_evidence_pack_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    doc.readiness_percent = summary["readiness_percent"]
    doc.uat_regression_evidence_pack_run_ready = 1 if summary["uat_regression_evidence_pack_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["uat_regression_evidence_pack_run_ready"]:
        frappe.throw(
            _("Cannot set UAT Regression Evidence Pack Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "UAT Evidence Approved" and doc.get("uat_completion_allowed"):
        frappe.throw(_("UAT Completion Allowed can only be ticked after the run is approved."))

    blocked_fields = [
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
            frappe.throw(_("{0} is not allowed in Phase 59.").format(label))


def on_uat_regression_evidence_pack_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM UAT Regression Evidence Pack Run Summary Sync Failed"
        )


def validate_crm_deal_phase59(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_uat_regression_evidence_pack_required"):
        required = doc.get("ndis_uat_regression_evidence_pack_required")

    if not required:
        return

    run = doc.get("ndis_uat_regression_evidence_pack_run") if _field_exists(CRM_DEAL, "ndis_uat_regression_evidence_pack_run") else None

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS UAT Regression Evidence Pack Run must be created and approved/completed.")
        )

    if not _is_uat_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS UAT Regression Evidence Pack Run must be approved/completed.")
        )


def validate_crm_deal_phase59_combined(doc, method=None):
    try:
        from ndis_crm.phase58_permission_workflow_hardening import validate_crm_deal_phase58_combined
        validate_crm_deal_phase58_combined(doc, method)
    except ImportError:
        pass

    validate_crm_deal_phase59(doc, method)


def phase59_health_check():
    print("---- NDIS CRM Phase 59 Health Check ----")

    for dt in [
        UAT_REGRESSION_EVIDENCE_PACK_LINE,
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
        "ndis_uat_regression_evidence_pack_required",
        "ndis_uat_regression_evidence_pack_run",
        "uat_regression_evidence_pack_status",
        "uat_regression_evidence_pack_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print(
        "NDIS CRM UAT Regression Evidence Pack Run records:",
        frappe.db.count(UAT_REGRESSION_EVIDENCE_PACK_RUN) if _doctype_exists(UAT_REGRESSION_EVIDENCE_PACK_RUN) else 0
    )
    print("Phase 59 creates UAT regression evidence pack run/line records only.")
    print("Phase 59 does not create or update Care Management, communication, event, task, finance, claim, remittance, payment, journal, GL, accounting, adjustment, or bank reconciliation records.")
    print("---- End Phase 59 Health Check ----")
