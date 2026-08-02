import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


MODULE_NAME = "Ndis Crm"

CRM_DEAL = "CRM Deal"
INTAKE = "NDIS Participant Intake"
HANDOVER = "NDIS CRM Handover"
FINANCE_ONBOARDING = "NDIS CRM Finance Onboarding"
OPERATIONS_SETUP = "NDIS CRM Operations Setup"
SCHEDULE_DRAFT = "NDIS CRM Service Schedule Draft"
ROSTER_REQUEST = "NDIS CRM Roster Build Request"
SERVICE_FILE = "NDIS Participant Service File"
SESSION_DRAFT = "NDIS CRM Service Session Draft"
EVIDENCE_REVIEW = "NDIS CRM Service Delivery Evidence Review"
DOWNSTREAM_PREPARATION = "NDIS CRM Downstream Preparation"

ATTENDANCE_DRAFT = "NDIS CRM Attendance Draft"
ATTENDANCE_DRAFT_LINE = "NDIS CRM Attendance Draft Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_attendance_draft_doctypes()
	create_custom_fields_phase14()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 14 attendance draft bridge installed successfully.")


def doctype_exists(doctype):
	return bool(frappe.db.exists("DocType", doctype))


def ensure_required_doctypes():
	required = [
		CRM_DEAL,
		INTAKE,
		HANDOVER,
		FINANCE_ONBOARDING,
		OPERATIONS_SETUP,
		SCHEDULE_DRAFT,
		ROSTER_REQUEST,
		SERVICE_FILE,
		SESSION_DRAFT,
		EVIDENCE_REVIEW,
		DOWNSTREAM_PREPARATION,
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 14 DocTypes: " + ", ".join(missing))
	print("Required Phase 14 DocTypes found.")


def make_field(label, fieldname, fieldtype, **kwargs):
	field = {"label": label, "fieldname": fieldname, "fieldtype": fieldtype}
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
		{"role": "NDIS Intake Officer", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
		{"role": "NDIS Service Manager", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
		{"role": "NDIS Plan Management Officer", "read": 1, "write": 1, "create": 1, "email": 1, "print": 1, "report": 1},
		{"role": "NDIS CRM Read Only", "read": 1, "export": 1, "print": 1, "report": 1},
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


def create_attendance_draft_doctypes():
	create_attendance_draft_line()
	create_attendance_draft()


def create_attendance_draft_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Preparation Source Key", "preparation_source_key", "Data", read_only=1),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Attendance Draft", "attendance_draft_section", "Section Break"),
		make_field("Session Date", "session_date", "Date", reqd=1, in_list_view=1),
		make_field("Attendance Date", "attendance_date", "Date", reqd=1, in_list_view=1),
		make_field("Actual Start Time", "actual_start_time", "Time", in_list_view=1),
		make_field("Actual End Time", "actual_end_time", "Time", in_list_view=1),
		make_field("Attendance Hours", "attendance_hours", "Float", in_list_view=1),
		make_field("Delivered Hours", "delivered_hours", "Float"),
		make_field("Workers Required", "workers_required", "Int", default=1),
		make_field("Estimated Worker Hours", "estimated_worker_hours", "Float"),
		make_field("Worker Mapping", "worker_mapping_section", "Section Break"),
		make_field("Support Worker User", "support_worker_user", "Link", options="User"),
	]
	if doctype_exists("Employee"):
		fields.append(make_field("Support Worker Employee", "support_worker_employee", "Link", options="Employee", in_list_view=1))
	else:
		fields.append(make_field("Support Worker Employee", "support_worker_employee", "Data", in_list_view=1))
	fields += [
		make_field("Support Worker Name", "support_worker_name", "Data"),
		make_field("Worker Reference Ready", "worker_reference_ready", "Check", default=0),
		make_field("Employee Mapping Ready", "employee_mapping_ready", "Check", default=0),
		make_field("Participant / Delivery", "participant_delivery_section", "Section Break"),
		make_field("Participant Attended", "participant_attended", "Check", default=1),
		make_field("Non Attendance Reason", "non_attendance_reason", "Small Text"),
		make_field("Service Delivered", "service_delivered", "Check", default=1),
		make_field("Proposed Attendance Status", "proposed_attendance_status", "Select", options="Present\nAbsent\nHalf Day\nOn Leave\nWork From Home", default="Present"),
		make_field("Progress Note", "progress_note", "Text Editor"),
		make_field("Incident Flag", "incident_flag", "Check", default=0),
		make_field("Incident Notes", "incident_notes", "Small Text"),
		make_field("Finance Snapshot", "finance_snapshot_section", "Section Break"),
	]
	if doctype_exists(NDIS_SERVICE_TYPE):
		fields.append(make_field("Finance Service Type", "finance_service_type", "Link", options=NDIS_SERVICE_TYPE))
	else:
		fields.append(make_field("Finance Service Type", "finance_service_type", "Data"))
	if doctype_exists(NDIS_SUPPORT_ITEM):
		fields.append(make_field("Support Item", "support_item", "Link", options=NDIS_SUPPORT_ITEM))
	else:
		fields.append(make_field("Support Item", "support_item", "Data"))
	if doctype_exists(PLAN_BUDGET):
		fields.append(make_field("NDIS Plan Budget", "plan_budget", "Link", options=PLAN_BUDGET))
	if doctype_exists(SERVICE_BOOKING):
		fields.append(make_field("NDIS Service Booking", "service_booking", "Link", options=SERVICE_BOOKING))

	fields.append(make_field("Location / Risk", "location_risk_section", "Section Break"))
	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))
	fields += [
		make_field("Delivery Location", "delivery_location", "Data"),
		make_field("Requires Roster", "requires_roster", "Check", default=1),
		make_field("Requires House", "requires_house", "Check", default=0),
		make_field("Requires Clinical Review", "requires_clinical_review", "Check", default=0),
		make_field("Clinical Review Complete", "clinical_review_complete", "Check", default=0),
		make_field("Transport Required", "transport_required", "Check", default=0),
		make_field("Worker Skill Requirements", "worker_skill_requirements", "Small Text"),
		make_field("Preparation Snapshot", "preparation_snapshot_section", "Section Break"),
		make_field("Attendance Preparation Ready", "attendance_preparation_ready", "Check", default=0),
		make_field("Attendance Hold", "attendance_hold", "Check", default=0),
		make_field("Billing Preparation Ready", "billing_preparation_ready", "Check", default=0),
		make_field("Payroll Preparation Ready", "payroll_preparation_ready", "Check", default=0),
		make_field("Claim Preparation Ready", "claim_preparation_ready", "Check", default=0),
		make_field("Review Status", "review_status_section", "Section Break"),
		make_field("Line Ready for Attendance Creation", "line_ready_for_attendance_creation", "Check", default=0, in_list_view=1),
		make_field("Attendance Draft Status", "attendance_draft_status", "Select", options="Draft\nReady\nApproved\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(name=ATTENDANCE_DRAFT_LINE, fields=fields, istable=1)


def create_attendance_draft():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-ATT-DRAFT-.YYYY.-.#####", default="NDIS-ATT-DRAFT-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Attendance Creation\nAttendance Draft Approved\nReturned to Downstream Preparation\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Attendance Draft Ready", "attendance_draft_ready", "Check", read_only=1, in_list_view=1),
		make_field("Employee Required for Attendance", "employee_required_for_attendance", "Check", default=1),
		make_field("Attendance Summary", "attendance_summary_section", "Section Break"),
		make_field("Attendance Line Count", "attendance_line_count", "Int", read_only=1),
		make_field("Attendance Hours Total", "attendance_hours_total", "Float", read_only=1),
		make_field("Estimated Worker Hours Total", "estimated_worker_hours_total", "Float", read_only=1),
		make_field("Attendance Ready Count", "attendance_ready_count", "Int", read_only=1),
		make_field("Attendance Approved Count", "attendance_approved_count", "Int", read_only=1),
		make_field("Attendance Hold Count", "attendance_hold_count", "Int", read_only=1),
		make_field("Employee Missing Count", "employee_missing_count", "Int", read_only=1),
		make_field("Source Links", "source_links_section", "Section Break"),
		make_field("CRM Lead", "crm_lead", "Link", options="CRM Lead"),
		make_field("CRM Deal", "crm_deal", "Link", options=CRM_DEAL, in_list_view=1),
		make_field("NDIS Participant Intake", "participant_intake", "Link", options=INTAKE),
		make_field("NDIS CRM Handover", "handover", "Link", options=HANDOVER),
		make_field("NDIS CRM Finance Onboarding", "finance_onboarding", "Link", options=FINANCE_ONBOARDING),
		make_field("NDIS CRM Operations Setup", "operations_setup", "Link", options=OPERATIONS_SETUP),
		make_field("NDIS CRM Service Schedule Draft", "service_schedule_draft", "Link", options=SCHEDULE_DRAFT),
		make_field("NDIS CRM Roster Build Request", "roster_build_request", "Link", options=ROSTER_REQUEST),
		make_field("NDIS Participant Service File", "participant_service_file", "Link", options=SERVICE_FILE),
		make_field("NDIS CRM Service Session Draft", "service_session_draft", "Link", options=SESSION_DRAFT),
		make_field("NDIS CRM Delivery Evidence Review", "delivery_evidence_review", "Link", options=EVIDENCE_REVIEW),
		make_field("NDIS CRM Downstream Preparation", "downstream_preparation", "Link", options=DOWNSTREAM_PREPARATION, reqd=1, in_list_view=1),
		make_field("Participant Customer", "participant_customer", "Link", options="Customer", in_list_view=1),
	]
	if doctype_exists(FINANCE_PROFILE):
		fields.append(make_field("NDIS Financial Profile", "ndis_financial_profile", "Link", options=FINANCE_PROFILE))
	else:
		fields.append(make_field("NDIS Financial Profile", "ndis_financial_profile", "Data"))
	fields += [
		make_field("Participant Details", "participant_details_section", "Section Break"),
		make_field("Participant Name", "participant_name", "Data", reqd=1, in_list_view=1),
		make_field("NDIS Number", "ndis_number", "Data"),
		make_field("Plan Start Date", "plan_start_date", "Date"),
		make_field("Plan End Date", "plan_end_date", "Date"),
		make_field("Attendance Window", "attendance_window_section", "Section Break"),
		make_field("Attendance Period Start", "attendance_period_start", "Date", in_list_view=1),
		make_field("Attendance Period End", "attendance_period_end", "Date", in_list_view=1),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Attendance Owner", "attendance_owner", "Link", options="User", in_list_view=1),
		make_field("Preparation Owner", "preparation_owner", "Link", options="User"),
		make_field("Operations Owner", "operations_owner", "Link", options="User"),
		make_field("Rostering Owner", "rostering_owner", "Link", options="User"),
		make_field("Service Manager", "service_manager", "Link", options="User"),
		make_field("Clinical Owner", "clinical_owner", "Link", options="User"),
		make_field("Default Cost Center", "default_cost_center", "Link", options="Cost Center"),
	]
	if doctype_exists(NDIS_HOUSE):
		fields.append(make_field("Default House", "default_house", "Link", options=NDIS_HOUSE))
	else:
		fields.append(make_field("Default House", "default_house", "Data"))
	fields += [
		make_field("Attendance Lines", "attendance_lines_section", "Section Break"),
		make_field("Attendance Lines", "attendance_lines", "Table", options=ATTENDANCE_DRAFT_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Attendance Draft Notes", "attendance_draft_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(name=ATTENDANCE_DRAFT, fields=fields, autoname="naming_series:", title_field="participant_name")


def create_custom_fields_phase14():
	deal_fields = [
		{"fieldname": "attendance_draft_section", "label": "NDIS Attendance Draft", "fieldtype": "Section Break", "insert_after": "downstream_preparation_ready"},
		{"fieldname": "ndis_attendance_draft_required", "label": "Attendance Draft Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "attendance_draft_section", "description": "Optional guard only. Normally attendance draft happens after participant activation and service delivery."},
		{"fieldname": "ndis_attendance_draft", "label": "NDIS CRM Attendance Draft", "fieldtype": "Link", "options": ATTENDANCE_DRAFT, "read_only": 1, "insert_after": "ndis_attendance_draft_required"},
		{"fieldname": "attendance_draft_status", "label": "Attendance Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_attendance_draft"},
		{"fieldname": "attendance_draft_ready", "label": "Attendance Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "attendance_draft_status"},
	]
	shared_fields = [
		{"fieldname": "attendance_draft_section", "label": "NDIS Attendance Draft", "fieldtype": "Section Break", "insert_after": "downstream_preparation_ready"},
		{"fieldname": "ndis_attendance_draft", "label": "NDIS CRM Attendance Draft", "fieldtype": "Link", "options": ATTENDANCE_DRAFT, "read_only": 1, "insert_after": "attendance_draft_section"},
		{"fieldname": "attendance_draft_status", "label": "Attendance Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_attendance_draft"},
		{"fieldname": "attendance_draft_ready", "label": "Attendance Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "attendance_draft_status"},
	]
	downstream_fields = [
		{"fieldname": "attendance_draft_section", "label": "NDIS Attendance Draft", "fieldtype": "Section Break", "insert_after": "downstream_ready"},
		{"fieldname": "ndis_attendance_draft", "label": "NDIS CRM Attendance Draft", "fieldtype": "Link", "options": ATTENDANCE_DRAFT, "read_only": 1, "insert_after": "attendance_draft_section"},
		{"fieldname": "attendance_draft_status", "label": "Attendance Draft Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_attendance_draft"},
		{"fieldname": "attendance_draft_ready", "label": "Attendance Draft Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "attendance_draft_status"},
	]
	was_in_install = frappe.flags.in_install
	frappe.flags.in_install = True
	try:
		create_custom_fields(
			{
				CRM_DEAL: deal_fields,
				HANDOVER: shared_fields,
				FINANCE_ONBOARDING: shared_fields,
				OPERATIONS_SETUP: shared_fields,
				SCHEDULE_DRAFT: shared_fields,
				ROSTER_REQUEST: shared_fields,
				SERVICE_FILE: shared_fields,
				SESSION_DRAFT: shared_fields,
				EVIDENCE_REVIEW: shared_fields,
				DOWNSTREAM_PREPARATION: downstream_fields,
				INTAKE: shared_fields,
			},
			update=True,
		)
	finally:
		frappe.flags.in_install = was_in_install
	print("Created / updated Phase 14 attendance draft custom fields.")


def upsert_doc(doctype, name, values):
	if frappe.db.exists(doctype, name):
		doc = frappe.get_doc(doctype, name)
		for key, value in values.items():
			doc.set(key, value)
		doc.save(ignore_permissions=True)
		print(f"Updated {doctype}: {name}")
	else:
		doc = frappe.get_doc({"doctype": doctype, "name": name, **values})
		doc.insert(ignore_permissions=True)
		print(f"Created {doctype}: {name}")


def create_form_scripts():
	upsert_doc(
		"CRM Form Script",
		"NDIS CRM Deal Actions",
		{"dt": CRM_DEAL, "view": "Form", "enabled": 1, "is_standard": 0, "script": _deal_script()},
	)
	if frappe.db.exists("DocType", "Client Script"):
		upsert_doc(
			"Client Script",
			"NDIS CRM Downstream Preparation Actions",
			{"dt": DOWNSTREAM_PREPARATION, "view": "Form", "enabled": 1, "script": _downstream_script()},
		)
		upsert_doc(
			"Client Script",
			"NDIS CRM Attendance Draft Actions",
			{"dt": ATTENDANCE_DRAFT, "view": "Form", "enabled": 1, "script": _attendance_script()},
		)


def _deal_script():
	from ndis_crm.setup.phase13_downstream_preparation import _deal_script as phase13_deal_script

	script = phase13_deal_script()
	insert = r''',
      {
        label: "Create Attendance Draft",
        onClick: () => {
          call("ndis_crm.phase14_attendance_draft.create_attendance_draft_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Attendance Draft Created" : "Existing Attendance Draft Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-attendance-draft/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Attendance Draft",
        onClick: () => {
          if (doc.ndis_attendance_draft) {
            window.open(`/app/ndis-crm-attendance-draft/${doc.ndis_attendance_draft}`, "_blank")
          } else {
            createToast({ title: "No Attendance Draft linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _downstream_script():
	from ndis_crm.setup.phase13_downstream_preparation import _downstream_script as phase13_downstream_script

	script = phase13_downstream_script()
	insert = r'''

        frm.add_custom_button(__("Create Attendance Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase14_attendance_draft.create_attendance_draft_from_downstream_preparation",
                args: { downstream_preparation: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating attendance draft...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Attendance Draft created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Attendance Draft", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_attendance_draft) {
            frm.add_custom_button(__("Open Attendance Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Attendance Draft", frm.doc.ndis_attendance_draft);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.delivery_evidence_review)", insert + "\n        if (frm.doc.delivery_evidence_review)")


def _attendance_script():
	return r'''
frappe.ui.form.on("NDIS CRM Attendance Draft", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Attendance Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase14_attendance_draft.generate_attendance_lines",
                args: { attendance_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating attendance lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Attendance lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Attendance Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase14_attendance_draft.validate_attendance_draft_readiness",
                args: { attendance_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating attendance draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Attendance draft validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Attendance Creation"), function () {
            frappe.call({
                method: "ndis_crm.phase14_attendance_draft.mark_ready_for_attendance_creation",
                args: { attendance_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for attendance creation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for attendance creation"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Attendance Draft"), function () {
            frappe.call({
                method: "ndis_crm.phase14_attendance_draft.approve_attendance_draft",
                args: { attendance_draft: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving attendance draft...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Attendance Draft approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.downstream_preparation) {
            frm.add_custom_button(__("Open Downstream Preparation"), function () {
                frappe.set_route("Form", "NDIS CRM Downstream Preparation", frm.doc.downstream_preparation);
            }, __("Open"));
        }

        if (frm.doc.delivery_evidence_review) {
            frm.add_custom_button(__("Open Delivery Evidence Review"), function () {
                frappe.set_route("Form", "NDIS CRM Service Delivery Evidence Review", frm.doc.delivery_evidence_review);
            }, __("Open"));
        }

        if (frm.doc.crm_deal) {
            frm.add_custom_button(__("Open CRM Deal"), function () {
                window.open(`/crm/deals/${frm.doc.crm_deal}`, "_blank");
            }, __("Open"));
        }
    }
});
'''.strip()
