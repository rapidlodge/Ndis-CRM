import frappe
from frappe import _
from frappe.utils import now


CRM_DEAL = "CRM Deal"

POST_CLOSURE_ROUTING_PREPARATION_RUN = "NDIS CRM Post Closure Routing Preparation Run"
POST_CLOSURE_ROUTING_PREPARATION_LINE = "NDIS CRM Post Closure Routing Preparation Line"

POST_CLOSURE_ROUTING_FINALISATION_RUN = "NDIS CRM Post Closure Routing Finalisation Run"
POST_CLOSURE_ROUTING_FINALISATION_LINE = "NDIS CRM Post Closure Routing Finalisation Line"

RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN = "NDIS CRM Recovery Outcome Closure Finalisation Run"
RECOVERY_OUTCOME_CLOSURE_DRAFT_RUN = "NDIS CRM Recovery Outcome Closure Draft Run"
RECOVERY_OUTCOME_CLOSURE_PREPARATION_RUN = "NDIS CRM Recovery Outcome Closure Preparation Run"
RECOVERY_OUTCOME_ACTION_COMPLETION_RUN = "NDIS CRM Recovery Outcome Action Completion Run"

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
    "Ready for Routing Finalisation",
    "Routing Finalisation Approved",
    "Post Closure Routing Finalised",
]

APPROVED_STATUSES = [
    "Routing Finalisation Approved",
    "Post Closure Routing Finalised",
]

ALLOWED_ROLES = {
    "Administrator",
    "System Manager",
    "Accounts Manager",
    "Accounts User",
    "NDIS CRM Manager",
    "NDIS Plan Management Officer",
}


def _check_role():
    if not set(frappe.get_roles()).intersection(ALLOWED_ROLES):
        frappe.throw(_("You do not have permission to perform this post-closure routing finalisation action."))


def _doctype_exists(doctype):
    return bool(frappe.db.exists("DocType", doctype))


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
            if value:
                return value

    return None


def _to_float(value):
    if value in [None, ""]:
        return 0

    try:
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").strip()
        return float(value)
    except Exception:
        return 0


def _blocked_line(row):
    return any([
        row.get("actual_recovery_case_closure_authorized"),
        row.get("communication_creation_authorized"),
        row.get("email_send_authorized"),
        row.get("event_creation_authorized"),
        row.get("todo_creation_authorized"),
        row.get("task_creation_authorized"),
        row.get("recovery_case_creation_authorized"),
        row.get("journal_entry_authorized"),
        row.get("manual_gl_authorized"),
        row.get("payment_entry_authorized"),
        row.get("sales_invoice_authorized"),
        row.get("adjustment_authorized"),
        row.get("bank_reconciliation_authorized"),
        row.get("claim_batch_authorized"),
        row.get("claim_line_authorized"),
        row.get("remittance_import_authorized"),
    ])


def _existing_run_for_preparation_run(post_closure_routing_preparation_run):
    if not _doctype_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN):
        return None

    existing = _get_first_existing_value(
        POST_CLOSURE_ROUTING_PREPARATION_RUN,
        post_closure_routing_preparation_run,
        [
            "ndis_post_closure_routing_final_run",
            "ndis_recovery_outcome_post_closure_routing_finalisation_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        {"post_closure_routing_preparation_run": post_closure_routing_preparation_run},
        "name",
    )


def _existing_run_for_deal(deal):
    if not _doctype_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN):
        return None

    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_post_closure_routing_final_run",
            "ndis_recovery_outcome_post_closure_routing_finalisation_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(POST_CLOSURE_ROUTING_FINALISATION_RUN, {"crm_deal": deal}, "name")


def _get_preparation_run_for_deal(deal):
    existing = _get_first_existing_value(
        CRM_DEAL,
        deal,
        [
            "ndis_post_closure_routing_prep_run",
            "ndis_recovery_outcome_post_closure_routing_preparation_run",
        ],
    )
    if existing:
        return existing

    return frappe.db.get_value(POST_CLOSURE_ROUTING_PREPARATION_RUN, {"crm_deal": deal}, "name")


def _is_preparation_completed(run):
    if not run or not frappe.db.exists(POST_CLOSURE_ROUTING_PREPARATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        POST_CLOSURE_ROUTING_PREPARATION_RUN,
        run,
        ["status", "post_closure_routing_preparation_run_ready"],
    )

    return status == "Post Closure Routing Prepared" and bool(ready)


def _is_finalisation_approved(run):
    if not run or not frappe.db.exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, run):
        return False

    status, ready = frappe.db.get_value(
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        run,
        ["status", "post_closure_routing_finalisation_run_ready"],
    )

    return status in APPROVED_STATUSES and bool(ready)


def _append_line_if_missing(doc, row_data):
    existing = {
        row.post_closure_routing_finalisation_source_key
        for row in doc.get("post_closure_routing_finalisation_lines") or []
        if row.get("post_closure_routing_finalisation_source_key")
    }

    key = row_data.get("post_closure_routing_finalisation_source_key")

    if key and key in existing:
        return False

    doc.append("post_closure_routing_finalisation_lines", row_data)
    return True


def _source_key(row):
    return row.get("post_closure_routing_preparation_source_key") or "|".join([
        str(row.get("post_closure_route") or ""),
        str(row.get("target_routing_name") or ""),
        str(row.get("target_case_name") or ""),
        str(row.get("service_line") or ""),
    ])


def _route_final_result(route):
    mapping = {
        "Exit Recovery Cycle": "Recovery Cycle Closed in CRM",
        "Repeat Follow-Up Cycle": "Repeat Follow-Up Route Finalised",
        "Payment Promise Monitoring": "Payment Promise Monitoring Route Finalised",
        "Evidence Follow-Up Review": "Evidence Follow-Up Route Finalised",
        "Dispute Review": "Dispute Review Route Finalised",
        "Contact Correction Review": "Contact Correction Route Finalised",
        "Escalation Review": "Escalation Route Finalised",
        "Manual Review": "Manual Review Route Finalised",
    }
    return mapping.get(route or "", "Manual Review Route Finalised")


def _is_preparation_line_done(row):
    return row.get("post_closure_routing_preparation_line_status") == "Route Prepared"


def _build_finalisation_line(row, source_doc):
    source_ready = bool(
        source_doc.get("status") == "Post Closure Routing Prepared"
        and _is_preparation_line_done(row)
        and row.get("post_closure_routing_source_ready")
        and row.get("routing_review_complete")
        and row.get("routing_decision_recorded")
        and row.get("routing_authorized")
        and row.get("line_ready_for_post_closure_routing_preparation")
        and not row.get("post_closure_routing_preparation_hold")
        and not _blocked_line(row)
        and _to_float(row.get("proposed_recovery_amount")) > 0
    )

    route = row.get("post_closure_route")
    final_result = _route_final_result(route)

    return {
        "post_closure_routing_finalisation_source_key": _source_key(row),

        "source_routing_doctype": row.get("target_routing_doctype"),
        "source_routing_name": row.get("target_routing_name"),
        "source_routing_status": row.get("target_routing_status"),

        "target_final_routing_doctype": None,
        "target_final_routing_name": None,
        "target_final_routing_status": None,

        "target_case_doctype": row.get("target_case_doctype"),
        "target_case_name": row.get("target_case_name"),
        "target_case_docstatus": row.get("target_case_docstatus"),
        "target_case_status": row.get("target_case_status"),

        "service_line": row.get("service_line"),
        "service_code": row.get("service_code"),
        "service_date": row.get("service_date"),
        "sales_invoice": row.get("sales_invoice"),
        "payment_entry": row.get("payment_entry"),
        "journal_entry": row.get("journal_entry"),
        "ndis_remittance_import": row.get("ndis_remittance_import"),
        "ndis_claim_batch": row.get("ndis_claim_batch"),
        "ndis_claim_line": row.get("ndis_claim_line"),

        "proposed_recovery_amount": row.get("proposed_recovery_amount"),
        "recovery_type": row.get("recovery_type"),
        "recovery_route": row.get("recovery_route"),
        "recovery_reason": row.get("recovery_reason"),
        "recovery_party_type": row.get("recovery_party_type") or "Customer",
        "recovery_party": row.get("recovery_party") or source_doc.get("participant_customer"),
        "recovery_contact_name": row.get("recovery_contact_name"),
        "recovery_contact_email": row.get("recovery_contact_email"),
        "recovery_due_date": row.get("recovery_due_date"),

        "recipient_name": row.get("recipient_name"),
        "recipient_email": row.get("recipient_email"),
        "recipient_phone": row.get("recipient_phone"),

        "outcome_status_snapshot": row.get("outcome_status_snapshot"),
        "outcome_summary": row.get("outcome_summary"),
        "response_reference": row.get("response_reference"),
        "promised_payment_date": row.get("promised_payment_date"),
        "promised_payment_amount": row.get("promised_payment_amount"),
        "evidence_requested": row.get("evidence_requested"),
        "dispute_reason": row.get("dispute_reason"),
        "correct_contact_name": row.get("correct_contact_name"),
        "correct_contact_email": row.get("correct_contact_email"),
        "correct_contact_phone": row.get("correct_contact_phone"),

        "closure_decision": row.get("closure_decision"),
        "closure_route": row.get("closure_route"),
        "closure_priority": row.get("closure_priority"),
        "closure_owner": row.get("closure_owner"),
        "closure_due_date": row.get("closure_due_date"),
        "final_closure_outcome": row.get("final_closure_outcome"),
        "final_closure_summary": row.get("final_closure_summary"),

        "post_closure_routing_finalisation_source_ready": 1 if source_ready else 0,
        "post_closure_route": route,
        "post_closure_route_priority": row.get("post_closure_route_priority") or "Normal",
        "post_closure_route_owner": row.get("post_closure_route_owner") or source_doc.get("post_closure_routing_preparation_owner") or frappe.session.user,
        "post_closure_route_due_date": row.get("post_closure_route_due_date"),
        "post_closure_route_instruction": row.get("post_closure_route_instruction"),
        "post_closure_route_decision_summary": row.get("post_closure_route_decision_summary"),

        "final_routing_result": final_result,
        "final_routing_summary": row.get("post_closure_route_decision_summary") or row.get("post_closure_route_instruction") or final_result,
        "routing_finalisation_review_complete": 0,
        "routing_finalisation_authorized": 0,
        "routing_finalisation_recorded": 0,

        "actual_recovery_case_closure_authorized": 0,
        "communication_creation_authorized": 0,
        "email_send_authorized": 0,
        "event_creation_authorized": 0,
        "todo_creation_authorized": 0,
        "task_creation_authorized": 0,
        "recovery_case_creation_authorized": 0,
        "journal_entry_authorized": 0,
        "manual_gl_authorized": 0,
        "payment_entry_authorized": 0,
        "sales_invoice_authorized": 0,
        "adjustment_authorized": 0,
        "bank_reconciliation_authorized": 0,
        "claim_batch_authorized": 0,
        "claim_line_authorized": 0,
        "remittance_import_authorized": 0,

        "post_closure_routing_finalisation_hold": 0 if source_ready else 1,
        "post_closure_routing_finalisation_hold_reason": None if source_ready else "Phase 54 post-closure routing preparation source is not ready for finalisation.",
        "line_ready_for_post_closure_routing_finalisation": 0,
        "post_closure_routing_finalisation_line_status": "Draft",
        "notes": row.get("notes"),
    }


def _generate_lines_from_preparation_run(doc, source):
    created = 0

    for row in source.get("post_closure_routing_preparation_lines") or []:
        if not _is_preparation_line_done(row):
            continue

        if _to_float(row.get("proposed_recovery_amount")) <= 0:
            continue

        if _append_line_if_missing(doc, _build_finalisation_line(row, source)):
            created += 1

    return created


def _active_lines(doc):
    return [
        row for row in doc.get("post_closure_routing_finalisation_lines") or []
        if _to_float(row.get("proposed_recovery_amount")) > 0
    ]


def _calculate_totals(doc):
    totals = {
        "post_closure_routing_finalisation_line_count": 0,
        "post_closure_routing_finalisation_amount_total": 0,
        "post_closure_routing_finalisation_ready_count": 0,
        "post_closure_routing_finalisation_hold_count": 0,
        "routing_finalised_count": 0,
        "recovery_cycle_closed_count": 0,
        "repeat_follow_up_route_finalised_count": 0,
        "payment_promise_monitoring_route_finalised_count": 0,
        "evidence_follow_up_route_finalised_count": 0,
        "dispute_review_route_finalised_count": 0,
        "contact_correction_route_finalised_count": 0,
        "escalation_route_finalised_count": 0,
        "manual_review_route_finalised_count": 0,
        "blocked_actual_recovery_case_closure_count": 0,
        "blocked_communication_count": 0,
        "blocked_email_send_count": 0,
        "blocked_event_count": 0,
        "blocked_todo_count": 0,
        "blocked_task_count": 0,
        "blocked_recovery_case_creation_count": 0,
        "blocked_journal_entry_count": 0,
        "blocked_manual_gl_count": 0,
        "blocked_payment_entry_count": 0,
        "blocked_sales_invoice_count": 0,
        "blocked_adjustment_count": 0,
        "blocked_bank_reconciliation_count": 0,
        "blocked_claim_batch_count": 0,
        "blocked_claim_line_count": 0,
        "blocked_remittance_import_count": 0,
    }

    result_counters = {
        "Recovery Cycle Closed in CRM": "recovery_cycle_closed_count",
        "Repeat Follow-Up Route Finalised": "repeat_follow_up_route_finalised_count",
        "Payment Promise Monitoring Route Finalised": "payment_promise_monitoring_route_finalised_count",
        "Evidence Follow-Up Route Finalised": "evidence_follow_up_route_finalised_count",
        "Dispute Review Route Finalised": "dispute_review_route_finalised_count",
        "Contact Correction Route Finalised": "contact_correction_route_finalised_count",
        "Escalation Route Finalised": "escalation_route_finalised_count",
        "Manual Review Route Finalised": "manual_review_route_finalised_count",
    }

    blocked_fields = [
        ("blocked_actual_recovery_case_closure_count", "actual_recovery_case_closure_authorized"),
        ("blocked_communication_count", "communication_creation_authorized"),
        ("blocked_email_send_count", "email_send_authorized"),
        ("blocked_event_count", "event_creation_authorized"),
        ("blocked_todo_count", "todo_creation_authorized"),
        ("blocked_task_count", "task_creation_authorized"),
        ("blocked_recovery_case_creation_count", "recovery_case_creation_authorized"),
        ("blocked_journal_entry_count", "journal_entry_authorized"),
        ("blocked_manual_gl_count", "manual_gl_authorized"),
        ("blocked_payment_entry_count", "payment_entry_authorized"),
        ("blocked_sales_invoice_count", "sales_invoice_authorized"),
        ("blocked_adjustment_count", "adjustment_authorized"),
        ("blocked_bank_reconciliation_count", "bank_reconciliation_authorized"),
        ("blocked_claim_batch_count", "claim_batch_authorized"),
        ("blocked_claim_line_count", "claim_line_authorized"),
        ("blocked_remittance_import_count", "remittance_import_authorized"),
    ]

    for row in doc.get("post_closure_routing_finalisation_lines") or []:
        totals["post_closure_routing_finalisation_line_count"] += 1
        totals["post_closure_routing_finalisation_amount_total"] += _to_float(row.get("proposed_recovery_amount"))

        if row.get("line_ready_for_post_closure_routing_finalisation"):
            totals["post_closure_routing_finalisation_ready_count"] += 1

        if row.get("post_closure_routing_finalisation_hold"):
            totals["post_closure_routing_finalisation_hold_count"] += 1

        if row.get("post_closure_routing_finalisation_line_status") == "Route Finalised":
            totals["routing_finalised_count"] += 1

        counter = result_counters.get(row.get("final_routing_result"), "manual_review_route_finalised_count")
        totals[counter] += 1

        for counter, fieldname in blocked_fields:
            if row.get(fieldname):
                totals[counter] += 1

    totals["post_closure_routing_finalisation_amount_total"] = round(
        totals["post_closure_routing_finalisation_amount_total"],
        2,
    )

    return totals


def _sync_totals(doc):
    totals = _calculate_totals(doc)

    for fieldname, value in totals.items():
        if _field_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, fieldname):
            doc.set(fieldname, value)

    return totals


def _calculate_readiness(doc):
    checks = []

    checks.append({
        "label": "Post Closure Routing Preparation Run linked",
        "complete": bool(doc.get("post_closure_routing_preparation_run")),
    })

    checks.append({
        "label": "Post Closure Routing Preparation completed",
        "complete": _is_preparation_completed(doc.get("post_closure_routing_preparation_run")),
    })

    checks.append({
        "label": "Participant Customer linked",
        "complete": bool(doc.get("participant_customer")),
    })

    checks.append({
        "label": "Company selected",
        "complete": bool(doc.get("company")),
    })

    checks.append({
        "label": "Post Closure Routing Finalisation Owner assigned",
        "complete": bool(doc.get("post_closure_routing_finalisation_owner")),
    })

    lines = _active_lines(doc)
    no_candidates = bool(doc.get("no_post_closure_routing_finalisation_candidate_found"))

    checks.append({
        "label": "Post-closure routing finalisation lines exist or no-candidate flag is set",
        "complete": bool(lines) or no_candidates,
    })

    if lines:
        checks.extend([
            {
                "label": "Routing finalisation source-ready flags are complete",
                "complete": not [row.service_line for row in lines if not row.get("post_closure_routing_finalisation_source_ready")],
            },
            {
                "label": "All lines have final routing result",
                "complete": not [row.service_line for row in lines if not row.get("final_routing_result")],
            },
            {
                "label": "All lines have route owner",
                "complete": not [row.service_line for row in lines if not row.get("post_closure_route_owner")],
            },
            {
                "label": "Routing finalisation review complete",
                "complete": not [row.service_line for row in lines if not row.get("routing_finalisation_review_complete")],
            },
            {
                "label": "Routing finalisation authorized",
                "complete": not [row.service_line for row in lines if not row.get("routing_finalisation_authorized")],
            },
            {
                "label": "Routing finalisation recorded",
                "complete": not [row.service_line for row in lines if not row.get("routing_finalisation_recorded")],
            },
        ])

        blocked_fields = [
            ("Actual recovery case closure remains blocked in Phase 55", "actual_recovery_case_closure_authorized"),
            ("Communication creation remains blocked in Phase 55", "communication_creation_authorized"),
            ("Email sending remains blocked in Phase 55", "email_send_authorized"),
            ("Event creation remains blocked in Phase 55", "event_creation_authorized"),
            ("ToDo creation remains blocked in Phase 55", "todo_creation_authorized"),
            ("Task creation remains blocked in Phase 55", "task_creation_authorized"),
            ("Recovery Case creation remains blocked in Phase 55", "recovery_case_creation_authorized"),
            ("Journal Entry authorization remains blocked in Phase 55", "journal_entry_authorized"),
            ("Manual GL authorization remains blocked in Phase 55", "manual_gl_authorized"),
            ("Payment Entry authorization remains blocked in Phase 55", "payment_entry_authorized"),
            ("Sales Invoice authorization remains blocked in Phase 55", "sales_invoice_authorized"),
            ("Adjustment authorization remains blocked in Phase 55", "adjustment_authorized"),
            ("Bank reconciliation authorization remains blocked in Phase 55", "bank_reconciliation_authorized"),
            ("Claim Batch authorization remains blocked in Phase 55", "claim_batch_authorized"),
            ("Claim Line authorization remains blocked in Phase 55", "claim_line_authorized"),
            ("Remittance Import authorization remains blocked in Phase 55", "remittance_import_authorized"),
        ]

        for label, fieldname in blocked_fields:
            checks.append({
                "label": label,
                "complete": not [row.service_line for row in lines if row.get(fieldname)],
            })

        checks.append({
            "label": "No active routing finalisation hold remains",
            "complete": not [row.service_line for row in lines if row.get("post_closure_routing_finalisation_hold")],
        })

        checks.append({
            "label": "All active lines marked ready for routing finalisation",
            "complete": not [row.service_line for row in lines if not row.get("line_ready_for_post_closure_routing_finalisation")],
        })

    total = len(checks)
    complete = len([row for row in checks if row["complete"]])
    readiness_percent = round((complete / total) * 100, 2) if total else 0
    incomplete = [row["label"] for row in checks if not row["complete"]]

    return {
        "total_checks": total,
        "complete_checks": complete,
        "readiness_percent": readiness_percent,
        "post_closure_routing_finalisation_run_ready": total > 0 and complete == total,
        "incomplete": incomplete,
    }


def _sync_summary_to_links(doc):
    summary = _calculate_readiness(doc)
    totals = _sync_totals(doc)

    if _field_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, "post_closure_routing_finalisation_run_ready"):
        doc.post_closure_routing_finalisation_run_ready = 1 if summary["post_closure_routing_finalisation_run_ready"] else 0

    target_doctypes = [
        CRM_DEAL,
        POST_CLOSURE_ROUTING_PREPARATION_RUN,
        RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN,
        RECOVERY_OUTCOME_CLOSURE_DRAFT_RUN,
        RECOVERY_OUTCOME_CLOSURE_PREPARATION_RUN,
        RECOVERY_OUTCOME_ACTION_COMPLETION_RUN,
    ]

    linked_names = [
        doc.get("crm_deal"),
        doc.get("post_closure_routing_preparation_run"),
        doc.get("recovery_outcome_closure_finalisation_run"),
        doc.get("recovery_outcome_closure_draft_run"),
        doc.get("recovery_outcome_closure_preparation_run"),
        doc.get("recovery_outcome_action_completion_run"),
    ]

    for doctype, name in zip(target_doctypes, linked_names):
        if not name:
            continue

        _db_set_if_field(doctype, name, "ndis_post_closure_routing_final_run", doc.name)
        _db_set_if_field(doctype, name, "post_closure_routing_finalisation_status", doc.status)
        _db_set_if_field(doctype, name, "post_closure_routing_finalisation_ready", 1 if summary["post_closure_routing_finalisation_run_ready"] else 0)

    return {
        "readiness": summary,
        "totals": totals,
    }


@frappe.whitelist()
def create_post_closure_routing_finalisation_run_from_preparation_run(post_closure_routing_preparation_run):
    _check_role()

    if not post_closure_routing_preparation_run:
        frappe.throw(_("NDIS CRM Post Closure Routing Preparation Run is required."))

    if not frappe.db.exists(POST_CLOSURE_ROUTING_PREPARATION_RUN, post_closure_routing_preparation_run):
        frappe.throw(_("NDIS CRM Post Closure Routing Preparation Run {0} was not found.").format(post_closure_routing_preparation_run))

    existing = _existing_run_for_preparation_run(post_closure_routing_preparation_run)
    if existing:
        return {
            "doctype": POST_CLOSURE_ROUTING_FINALISATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Post Closure Routing Finalisation Run returned.",
        }

    source = frappe.get_doc(POST_CLOSURE_ROUTING_PREPARATION_RUN, post_closure_routing_preparation_run)

    doc = frappe.new_doc(POST_CLOSURE_ROUTING_FINALISATION_RUN)
    doc.status = "Draft"

    doc.post_closure_routing_preparation_run = source.name
    doc.recovery_outcome_closure_finalisation_run = source.get("recovery_outcome_closure_finalisation_run")
    doc.recovery_outcome_closure_draft_run = source.get("recovery_outcome_closure_draft_run")
    doc.recovery_outcome_closure_preparation_run = source.get("recovery_outcome_closure_preparation_run")
    doc.recovery_outcome_action_completion_run = source.get("recovery_outcome_action_completion_run")

    doc.crm_deal = source.get("crm_deal")
    doc.crm_lead = source.get("crm_lead")
    doc.participant_intake = source.get("participant_intake")
    doc.participant_customer = source.get("participant_customer")
    doc.ndis_financial_profile = source.get("ndis_financial_profile")
    doc.participant_name = source.get("participant_name") or source.get("participant_customer") or source.name
    doc.ndis_number = source.get("ndis_number")
    doc.plan_start_date = source.get("plan_start_date")
    doc.plan_end_date = source.get("plan_end_date")
    doc.claim_period_start = source.get("claim_period_start")
    doc.claim_period_end = source.get("claim_period_end")
    doc.company = source.get("company")
    doc.ndis_remittance_import = source.get("ndis_remittance_import")

    doc.post_closure_routing_finalisation_owner = frappe.session.user
    doc.post_closure_routing_preparation_owner = source.get("post_closure_routing_preparation_owner")

    doc.target_routing_finalisation_mode = "CRM Routing Finalisation Only"
    doc.routing_finalisation_allowed = 0

    doc.actual_recovery_case_closure_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.claim_batch_creation_allowed = 0
    doc.claim_line_creation_allowed = 0
    doc.remittance_import_creation_allowed = 0

    created_count = _generate_lines_from_preparation_run(doc, source)
    doc.no_post_closure_routing_finalisation_candidate_found = 1 if created_count == 0 else 0

    summary = _calculate_readiness(doc)
    doc.readiness_percent = summary["readiness_percent"]
    doc.post_closure_routing_finalisation_run_ready = 1 if summary["post_closure_routing_finalisation_run_ready"] else 0

    _sync_totals(doc)
    doc.insert(ignore_permissions=False)
    _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": POST_CLOSURE_ROUTING_FINALISATION_RUN,
        "name": doc.name,
        "created": True,
        "post_closure_routing_finalisation_line_count": created_count,
        "no_post_closure_routing_finalisation_candidate_found": bool(doc.no_post_closure_routing_finalisation_candidate_found),
        "message": "NDIS CRM Post Closure Routing Finalisation Run created successfully.",
    }


@frappe.whitelist()
def create_post_closure_routing_finalisation_run_from_crm_deal(deal):
    _check_role()

    if not deal:
        frappe.throw(_("CRM Deal is required."))

    if not frappe.db.exists(CRM_DEAL, deal):
        frappe.throw(_("CRM Deal {0} was not found.").format(deal))

    existing = _existing_run_for_deal(deal)
    if existing:
        return {
            "doctype": POST_CLOSURE_ROUTING_FINALISATION_RUN,
            "name": existing,
            "created": False,
            "message": "Existing NDIS CRM Post Closure Routing Finalisation Run returned.",
        }

    source_run = _get_preparation_run_for_deal(deal)

    if not source_run:
        frappe.throw(_("Please complete NDIS CRM Post Closure Routing Preparation Run before creating Post Closure Routing Finalisation Run."))

    return create_post_closure_routing_finalisation_run_from_preparation_run(source_run)


@frappe.whitelist()
def generate_post_closure_routing_finalisation_lines(post_closure_routing_finalisation_run):
    _check_role()

    doc = frappe.get_doc(POST_CLOSURE_ROUTING_FINALISATION_RUN, post_closure_routing_finalisation_run)

    if not doc.get("post_closure_routing_preparation_run"):
        frappe.throw(_("Post Closure Routing Preparation Run is required."))

    source = frappe.get_doc(POST_CLOSURE_ROUTING_PREPARATION_RUN, doc.post_closure_routing_preparation_run)
    created_count = _generate_lines_from_preparation_run(doc, source)

    if created_count == 0 and not doc.get("post_closure_routing_finalisation_lines"):
        doc.no_post_closure_routing_finalisation_candidate_found = 1
    else:
        doc.no_post_closure_routing_finalisation_candidate_found = 0

    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "created_count": created_count,
        "summary": summary,
        "message": f"Post-closure routing finalisation lines generated. Created: {created_count}.",
    }


@frappe.whitelist()
def validate_post_closure_routing_finalisation_readiness(post_closure_routing_finalisation_run):
    _check_role()

    doc = frappe.get_doc(POST_CLOSURE_ROUTING_FINALISATION_RUN, post_closure_routing_finalisation_run)
    summary = _sync_summary_to_links(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "summary": summary,
        "message": "Post Closure Routing Finalisation Run readiness validated.",
    }


@frappe.whitelist()
def mark_ready_for_post_closure_routing_finalisation(post_closure_routing_finalisation_run):
    _check_role()

    doc = frappe.get_doc(POST_CLOSURE_ROUTING_FINALISATION_RUN, post_closure_routing_finalisation_run)
    summary = _calculate_readiness(doc)

    if not summary["post_closure_routing_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot mark Ready for Routing Finalisation. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Ready for Routing Finalisation"
    doc.readiness_percent = summary["readiness_percent"]
    doc.post_closure_routing_finalisation_run_ready = 1
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": POST_CLOSURE_ROUTING_FINALISATION_RUN,
        "name": doc.name,
        "message": "Post Closure Routing Finalisation Run marked Ready.",
    }


@frappe.whitelist()
def approve_post_closure_routing_finalisation_run(post_closure_routing_finalisation_run):
    _check_role()

    doc = frappe.get_doc(POST_CLOSURE_ROUTING_FINALISATION_RUN, post_closure_routing_finalisation_run)
    summary = _calculate_readiness(doc)

    if not summary["post_closure_routing_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot approve Post Closure Routing Finalisation Run. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    doc.status = "Routing Finalisation Approved"
    doc.readiness_percent = summary["readiness_percent"]
    doc.post_closure_routing_finalisation_run_ready = 1

    doc.routing_finalisation_allowed = 0
    doc.actual_recovery_case_closure_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.claim_batch_creation_allowed = 0
    doc.claim_line_creation_allowed = 0
    doc.remittance_import_creation_allowed = 0

    for row in doc.get("post_closure_routing_finalisation_lines") or []:
        if row.get("post_closure_routing_finalisation_line_status") in ["Draft", "Ready"]:
            row.post_closure_routing_finalisation_line_status = "Approved"

    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "doctype": POST_CLOSURE_ROUTING_FINALISATION_RUN,
        "name": doc.name,
        "message": "Post Closure Routing Finalisation Run approved. No downstream document was created.",
    }


def _ready_lines_for_finalisation(doc):
    ready = []

    for row in _active_lines(doc):
        if row.get("post_closure_routing_finalisation_line_status") not in ["Approved", "Ready"]:
            continue

        if not row.get("line_ready_for_post_closure_routing_finalisation"):
            continue

        if not row.get("post_closure_routing_finalisation_source_ready"):
            continue

        if not row.get("routing_finalisation_review_complete"):
            continue

        if not row.get("routing_finalisation_authorized"):
            continue

        if not row.get("routing_finalisation_recorded"):
            continue

        if row.get("post_closure_routing_finalisation_hold"):
            continue

        if _blocked_line(row):
            continue

        ready.append(row)

    return ready


@frappe.whitelist()
def finalise_post_closure_routing(post_closure_routing_finalisation_run):
    _check_role()

    doc = frappe.get_doc(POST_CLOSURE_ROUTING_FINALISATION_RUN, post_closure_routing_finalisation_run)

    if doc.status != "Routing Finalisation Approved":
        frappe.throw(_("Post Closure Routing Finalisation Run must be approved before finalisation."))

    if not doc.get("routing_finalisation_allowed"):
        frappe.throw(_("Tick Routing Finalisation Allowed before finalising post-closure routing."))

    if (doc.get("target_routing_finalisation_mode") or "CRM Routing Finalisation Only") != "CRM Routing Finalisation Only":
        frappe.throw(_("Phase 55 supports CRM Routing Finalisation Only."))

    blocked_run_fields = [
        ("Actual Recovery Case Closure Allowed", "actual_recovery_case_closure_allowed"),
        ("Communication Creation Allowed", "communication_creation_allowed"),
        ("Email Send Allowed", "email_send_allowed"),
        ("Event Creation Allowed", "event_creation_allowed"),
        ("ToDo Creation Allowed", "todo_creation_allowed"),
        ("Task Creation Allowed", "task_creation_allowed"),
        ("Recovery Case Creation Allowed", "recovery_case_creation_allowed"),
        ("Journal Entry Creation Allowed", "journal_entry_creation_allowed"),
        ("Manual GL Creation Allowed", "manual_gl_creation_allowed"),
        ("Payment Entry Creation Allowed", "payment_entry_creation_allowed"),
        ("Sales Invoice Creation Allowed", "sales_invoice_creation_allowed"),
        ("Adjustment Creation Allowed", "adjustment_creation_allowed"),
        ("Bank Reconciliation Allowed", "bank_reconciliation_allowed"),
        ("Claim Batch Creation Allowed", "claim_batch_creation_allowed"),
        ("Claim Line Creation Allowed", "claim_line_creation_allowed"),
        ("Remittance Import Creation Allowed", "remittance_import_creation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} must remain unticked in Phase 55.").format(label))

    summary = _calculate_readiness(doc)

    if not summary["post_closure_routing_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot finalise post-closure routing. Incomplete items: {0}").format(
                "; ".join(summary["incomplete"])
            )
        )

    ready_lines = _ready_lines_for_finalisation(doc)

    if not ready_lines and not doc.get("no_post_closure_routing_finalisation_candidate_found"):
        frappe.throw(_("No ready post-closure routing finalisation lines found."))

    for row in ready_lines:
        row.target_final_routing_doctype = POST_CLOSURE_ROUTING_FINALISATION_LINE
        row.target_final_routing_name = row.name
        row.target_final_routing_status = "Route Finalised"
        row.post_closure_routing_finalisation_line_status = "Route Finalised"

    doc.status = "Post Closure Routing Finalised"
    doc.routing_finalisation_allowed = 0
    doc.actual_recovery_case_closure_allowed = 0
    doc.communication_creation_allowed = 0
    doc.email_send_allowed = 0
    doc.event_creation_allowed = 0
    doc.todo_creation_allowed = 0
    doc.task_creation_allowed = 0
    doc.recovery_case_creation_allowed = 0
    doc.journal_entry_creation_allowed = 0
    doc.manual_gl_creation_allowed = 0
    doc.payment_entry_creation_allowed = 0
    doc.sales_invoice_creation_allowed = 0
    doc.adjustment_creation_allowed = 0
    doc.bank_reconciliation_allowed = 0
    doc.claim_batch_creation_allowed = 0
    doc.claim_line_creation_allowed = 0
    doc.remittance_import_creation_allowed = 0
    doc.finalised_by = frappe.session.user
    doc.finalised_on = now()

    _sync_totals(doc)
    doc.save(ignore_permissions=True)

    frappe.db.commit()

    return {
        "finalised_line_count": len(ready_lines),
        "message": "Post-closure routing finalised in CRM-only control layer. No Recovery Case was closed. No Communication, Email Queue, Event, ToDo, Task, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or Remittance Import was created.",
    }


def validate_post_closure_routing_finalisation_run(doc, method=None):
    summary = _calculate_readiness(doc)
    _sync_totals(doc)

    if _field_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, "readiness_percent"):
        doc.readiness_percent = summary["readiness_percent"]

    if _field_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN, "post_closure_routing_finalisation_run_ready"):
        doc.post_closure_routing_finalisation_run_ready = 1 if summary["post_closure_routing_finalisation_run_ready"] else 0

    if doc.status in READY_STATUSES and not summary["post_closure_routing_finalisation_run_ready"]:
        frappe.throw(
            _("Cannot set Post Closure Routing Finalisation Run to {0}. Incomplete items: {1}").format(
                doc.status,
                "; ".join(summary["incomplete"])
            )
        )

    if doc.status != "Routing Finalisation Approved" and doc.get("routing_finalisation_allowed"):
        frappe.throw(_("Routing Finalisation Allowed can only be ticked after the run is approved."))

    blocked_run_fields = [
        ("Actual recovery case closure", "actual_recovery_case_closure_allowed"),
        ("Communication creation", "communication_creation_allowed"),
        ("Email send", "email_send_allowed"),
        ("Event creation", "event_creation_allowed"),
        ("ToDo creation", "todo_creation_allowed"),
        ("Task creation", "task_creation_allowed"),
        ("Recovery Case creation", "recovery_case_creation_allowed"),
        ("Journal Entry creation", "journal_entry_creation_allowed"),
        ("Manual GL creation", "manual_gl_creation_allowed"),
        ("Payment Entry creation", "payment_entry_creation_allowed"),
        ("Sales Invoice creation", "sales_invoice_creation_allowed"),
        ("Adjustment creation", "adjustment_creation_allowed"),
        ("Bank reconciliation", "bank_reconciliation_allowed"),
        ("Claim Batch creation", "claim_batch_creation_allowed"),
        ("Claim Line creation", "claim_line_creation_allowed"),
        ("Remittance Import creation", "remittance_import_creation_allowed"),
    ]

    for label, fieldname in blocked_run_fields:
        if doc.get(fieldname):
            frappe.throw(_("{0} is not allowed in Phase 55.").format(label))


def on_post_closure_routing_finalisation_run_update(doc, method=None):
    try:
        _sync_summary_to_links(doc)
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "NDIS CRM Post Closure Routing Finalisation Run Summary Sync Failed"
        )


def validate_crm_deal_phase55(doc, method=None):
    if doc.status != "Won / Active Client":
        return

    required = 0

    if _field_exists(CRM_DEAL, "ndis_post_closure_routing_final_run_required"):
        required = doc.get("ndis_post_closure_routing_final_run_required")

    if not required:
        return

    run = None

    if _field_exists(CRM_DEAL, "ndis_post_closure_routing_final_run"):
        run = doc.get("ndis_post_closure_routing_final_run")

    if not run:
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Post Closure Routing Finalisation Run must be created and approved/completed.")
        )

    if not _is_finalisation_approved(run):
        frappe.throw(
            _("Cannot mark CRM Deal as Won / Active Client. NDIS Post Closure Routing Finalisation Run must be approved/completed.")
        )


def validate_crm_deal_phase55_combined(doc, method=None):
    try:
        from ndis_crm.phase54_recovery_outcome_post_closure_routing_preparation import validate_crm_deal_phase54_combined
        validate_crm_deal_phase54_combined(doc, method)
    except ImportError:
        try:
            from ndis_crm.phase53_recovery_outcome_closure_finalisation import validate_crm_deal_phase53_combined
            validate_crm_deal_phase53_combined(doc, method)
        except ImportError:
            pass

    validate_crm_deal_phase55(doc, method)


def phase55_health_check():
    print("---- NDIS CRM Phase 55 Health Check ----")

    for dt in [
        POST_CLOSURE_ROUTING_FINALISATION_LINE,
        POST_CLOSURE_ROUTING_FINALISATION_RUN,
        POST_CLOSURE_ROUTING_PREPARATION_LINE,
        POST_CLOSURE_ROUTING_PREPARATION_RUN,
        RECOVERY_OUTCOME_CLOSURE_FINALISATION_RUN,
        RECOVERY_OUTCOME_CLOSURE_DRAFT_RUN,
        RECOVERY_OUTCOME_CLOSURE_PREPARATION_RUN,
        RECOVERY_OUTCOME_ACTION_COMPLETION_RUN,
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
        "ndis_post_closure_routing_final_run_required",
        "ndis_post_closure_routing_final_run",
        "post_closure_routing_finalisation_status",
        "post_closure_routing_finalisation_ready",
    ]:
        print(f"CRM Deal field {field}: {'OK' if _field_exists(CRM_DEAL, field) else 'MISSING'}")

    print(
        "NDIS CRM Post Closure Routing Finalisation Run records:",
        frappe.db.count(POST_CLOSURE_ROUTING_FINALISATION_RUN) if _doctype_exists(POST_CLOSURE_ROUTING_FINALISATION_RUN) else 0
    )
    print("Phase 55 creates CRM post-closure routing finalisation run/line records only.")
    print("Phase 55 finalises the CRM-only post-closure routing result.")
    print("Phase 55 does not create Communication, Email Queue, Event, ToDo, Task, Recovery Case, Journal Entry, GL Entry, Payment Entry, Sales Invoice, adjustment, bank reconciliation, Claim Batch, Claim Line, or NDIS Remittance Import.")
    print("---- End Phase 55 Health Check ----")
