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
DOWNSTREAM_PREPARATION_LINE = "NDIS CRM Downstream Preparation Line"

FINANCE_PROFILE = "NDIS Participant Financial Profile"
PLAN_BUDGET = "NDIS Plan Budget"
SERVICE_BOOKING = "NDIS Service Booking"
NDIS_SERVICE_TYPE = "NDIS Service Type"
NDIS_SUPPORT_ITEM = "NDIS Support Item"
NDIS_HOUSE = "NDIS House"


def install():
	ensure_required_doctypes()
	create_downstream_preparation_doctypes()
	create_custom_fields_phase13()
	create_form_scripts()
	frappe.clear_cache()
	frappe.db.commit()
	print("NDIS CRM Phase 13 downstream preparation bridge installed successfully.")


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
		"NDIS Service Line",
		"CRM Form Script",
	]
	missing = [dt for dt in required if not doctype_exists(dt)]
	if missing:
		frappe.throw("Missing required Phase 13 DocTypes: " + ", ".join(missing))
	print("Required Phase 13 DocTypes found.")


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


def create_downstream_preparation_doctypes():
	create_downstream_preparation_line()
	create_downstream_preparation()


def create_downstream_preparation_line():
	fields = [
		make_field("Source", "source_section", "Section Break"),
		make_field("Evidence Source Key", "evidence_source_key", "Data", read_only=1),
		make_field("Service Line", "service_line", "Link", options="NDIS Service Line", reqd=1, in_list_view=1),
		make_field("Service Code", "service_code", "Data", read_only=1),
		make_field("Service Model", "service_model", "Data"),
		make_field("Actual Delivery", "actual_delivery_section", "Section Break"),
		make_field("Session Date", "session_date", "Date", reqd=1, in_list_view=1),
		make_field("Actual Start Time", "actual_start_time", "Time", in_list_view=1),
		make_field("Actual End Time", "actual_end_time", "Time", in_list_view=1),
		make_field("Delivered Hours", "delivered_hours", "Float", in_list_view=1),
		make_field("Workers Required", "workers_required", "Int", default=1),
		make_field("Estimated Worker Hours", "estimated_worker_hours", "Float"),
		make_field("Worker / Attendance Source", "worker_attendance_section", "Section Break"),
		make_field("Support Worker User", "support_worker_user", "Link", options="User"),
	]
	if doctype_exists("Employee"):
		fields.append(make_field("Support Worker Employee", "support_worker_employee", "Link", options="Employee"))
	else:
		fields.append(make_field("Support Worker Employee", "support_worker_employee", "Data"))
	fields += [
		make_field("Support Worker Name", "support_worker_name", "Data"),
		make_field("Participant Attended", "participant_attended", "Check", default=1),
		make_field("Non Attendance Reason", "non_attendance_reason", "Small Text"),
		make_field("Service Delivered", "service_delivered", "Check", default=1),
		make_field("Progress Note", "progress_note", "Text Editor"),
		make_field("Incident Flag", "incident_flag", "Check", default=0),
		make_field("Incident Notes", "incident_notes", "Small Text"),
		make_field("Finance Source", "finance_source_section", "Section Break"),
	]
	if doctype_exists(NDIS_SERVICE_TYPE):
		fields.append(make_field("Finance Service Type", "finance_service_type", "Link", options=NDIS_SERVICE_TYPE))
	else:
		fields.append(make_field("Finance Service Type", "finance_service_type", "Data"))
	if doctype_exists(NDIS_SUPPORT_ITEM):
		fields.append(make_field("Support Item", "support_item", "Link", options=NDIS_SUPPORT_ITEM, in_list_view=1))
	else:
		fields.append(make_field("Support Item", "support_item", "Data", in_list_view=1))
	if doctype_exists(PLAN_BUDGET):
		fields.append(make_field("NDIS Plan Budget", "plan_budget", "Link", options=PLAN_BUDGET))
	if doctype_exists(SERVICE_BOOKING):
		fields.append(make_field("NDIS Service Booking", "service_booking", "Link", options=SERVICE_BOOKING, in_list_view=1))

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
		make_field("Billing Precheck Ready", "billing_precheck_ready", "Check", default=0),
		make_field("Evidence Status", "evidence_status", "Data"),
		make_field("Preparation Required", "preparation_required_section", "Section Break"),
		make_field("Attendance Preparation Required", "attendance_preparation_required", "Check", default=1),
		make_field("Billing Preparation Required", "billing_preparation_required", "Check", default=1),
		make_field("Payroll Preparation Required", "payroll_preparation_required", "Check", default=1),
		make_field("Claim Preparation Required", "claim_preparation_required", "Check", default=1),
		make_field("Preparation Ready Flags", "preparation_ready_section", "Section Break"),
		make_field("Attendance Preparation Ready", "attendance_preparation_ready", "Check", default=0, in_list_view=1),
		make_field("Billing Preparation Ready", "billing_preparation_ready", "Check", default=0, in_list_view=1),
		make_field("Payroll Preparation Ready", "payroll_preparation_ready", "Check", default=0, in_list_view=1),
		make_field("Claim Preparation Ready", "claim_preparation_ready", "Check", default=0, in_list_view=1),
		make_field("Preparation Holds", "preparation_holds_section", "Section Break"),
		make_field("Attendance Hold", "attendance_hold", "Check", default=0),
		make_field("Billing Hold", "billing_hold", "Check", default=0),
		make_field("Payroll Hold", "payroll_hold", "Check", default=0),
		make_field("Claim Hold", "claim_hold", "Check", default=0),
		make_field("Review Status", "review_status_section", "Section Break"),
		make_field("Line Ready for Downstream Creation", "line_ready_for_downstream_creation", "Check", default=0, in_list_view=1),
		make_field("Preparation Status", "preparation_status", "Select", options="Draft\nReady\nApproved\nReturned\nCancelled", default="Draft", in_list_view=1),
		make_field("Notes", "notes", "Small Text"),
	]
	create_doctype_if_missing(name=DOWNSTREAM_PREPARATION_LINE, fields=fields, istable=1)


def create_downstream_preparation():
	fields = [
		make_field("Series", "naming_series", "Select", options="NDIS-DOWNSTREAM-PREP-.YYYY.-.#####", default="NDIS-DOWNSTREAM-PREP-.YYYY.-.#####", reqd=1),
		make_field("Status", "status_section", "Section Break"),
		make_field("Status", "status", "Select", options="Draft\nIn Review\nReady for Downstream Processing\nDownstream Preparation Approved\nReturned to Evidence Review\nCancelled", default="Draft", in_list_view=1),
		make_field("Readiness %", "readiness_percent", "Percent", read_only=1, in_list_view=1),
		make_field("Downstream Ready", "downstream_ready", "Check", read_only=1, in_list_view=1),
		make_field("Preparation Line Count", "preparation_line_count", "Int", read_only=1),
		make_field("Preparation Summary", "preparation_summary_section", "Section Break"),
		make_field("Delivered Hours Total", "delivered_hours_total", "Float", read_only=1),
		make_field("Estimated Worker Hours Total", "estimated_worker_hours_total", "Float", read_only=1),
		make_field("Attendance Ready Count", "attendance_ready_count", "Int", read_only=1),
		make_field("Billing Ready Count", "billing_ready_count", "Int", read_only=1),
		make_field("Payroll Ready Count", "payroll_ready_count", "Int", read_only=1),
		make_field("Claim Ready Count", "claim_ready_count", "Int", read_only=1),
		make_field("Attendance Hold Count", "attendance_hold_count", "Int", read_only=1),
		make_field("Billing Hold Count", "billing_hold_count", "Int", read_only=1),
		make_field("Payroll Hold Count", "payroll_hold_count", "Int", read_only=1),
		make_field("Claim Hold Count", "claim_hold_count", "Int", read_only=1),
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
		make_field("NDIS CRM Delivery Evidence Review", "delivery_evidence_review", "Link", options=EVIDENCE_REVIEW, reqd=1, in_list_view=1),
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
		make_field("Preparation Window", "preparation_window_section", "Section Break"),
		make_field("Preparation Period Start", "preparation_period_start", "Date", in_list_view=1),
		make_field("Preparation Period End", "preparation_period_end", "Date", in_list_view=1),
		make_field("Owners", "owners_section", "Section Break"),
		make_field("Preparation Owner", "preparation_owner", "Link", options="User", in_list_view=1),
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
		make_field("Preparation Lines", "preparation_lines_section", "Section Break"),
		make_field("Preparation Lines", "preparation_lines", "Table", options=DOWNSTREAM_PREPARATION_LINE),
		make_field("Notes", "notes_section", "Section Break"),
		make_field("Downstream Preparation Notes", "downstream_preparation_notes", "Small Text"),
		make_field("Returned / Blocker Notes", "returned_notes", "Small Text"),
	]
	create_doctype_if_missing(name=DOWNSTREAM_PREPARATION, fields=fields, autoname="naming_series:", title_field="participant_name")


def create_custom_fields_phase13():
	deal_fields = [
		{"fieldname": "downstream_preparation_section", "label": "NDIS Downstream Preparation", "fieldtype": "Section Break", "insert_after": "delivery_evidence_ready"},
		{"fieldname": "ndis_downstream_preparation_required", "label": "Downstream Preparation Required Before Active Deal", "fieldtype": "Check", "default": 0, "insert_after": "downstream_preparation_section", "description": "Optional guard only. Normally downstream preparation happens after a participant is active and evidence is approved."},
		{"fieldname": "ndis_downstream_preparation", "label": "NDIS CRM Downstream Preparation", "fieldtype": "Link", "options": DOWNSTREAM_PREPARATION, "read_only": 1, "insert_after": "ndis_downstream_preparation_required"},
		{"fieldname": "downstream_preparation_status", "label": "Downstream Preparation Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_downstream_preparation"},
		{"fieldname": "downstream_preparation_ready", "label": "Downstream Preparation Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "downstream_preparation_status"},
	]
	shared_fields = [
		{"fieldname": "downstream_preparation_section", "label": "NDIS Downstream Preparation", "fieldtype": "Section Break", "insert_after": "delivery_evidence_ready"},
		{"fieldname": "ndis_downstream_preparation", "label": "NDIS CRM Downstream Preparation", "fieldtype": "Link", "options": DOWNSTREAM_PREPARATION, "read_only": 1, "insert_after": "downstream_preparation_section"},
		{"fieldname": "downstream_preparation_status", "label": "Downstream Preparation Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_downstream_preparation"},
		{"fieldname": "downstream_preparation_ready", "label": "Downstream Preparation Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "downstream_preparation_status"},
	]
	evidence_fields = [
		{"fieldname": "downstream_preparation_section", "label": "NDIS Downstream Preparation", "fieldtype": "Section Break", "insert_after": "evidence_ready"},
		{"fieldname": "ndis_downstream_preparation", "label": "NDIS CRM Downstream Preparation", "fieldtype": "Link", "options": DOWNSTREAM_PREPARATION, "read_only": 1, "insert_after": "downstream_preparation_section"},
		{"fieldname": "downstream_preparation_status", "label": "Downstream Preparation Status", "fieldtype": "Data", "read_only": 1, "insert_after": "ndis_downstream_preparation"},
		{"fieldname": "downstream_preparation_ready", "label": "Downstream Preparation Ready", "fieldtype": "Check", "read_only": 1, "insert_after": "downstream_preparation_status"},
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
				EVIDENCE_REVIEW: evidence_fields,
				INTAKE: shared_fields,
			},
			update=True,
		)
	finally:
		frappe.flags.in_install = was_in_install
	print("Created / updated Phase 13 downstream preparation custom fields.")


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
			"NDIS CRM Service Delivery Evidence Review Actions",
			{"dt": EVIDENCE_REVIEW, "view": "Form", "enabled": 1, "script": _evidence_script()},
		)
		upsert_doc(
			"Client Script",
			"NDIS CRM Downstream Preparation Actions",
			{"dt": DOWNSTREAM_PREPARATION, "view": "Form", "enabled": 1, "script": _downstream_script()},
		)


def _deal_script():
	from ndis_crm.setup.phase12_delivery_evidence import _deal_script as phase12_deal_script

	script = phase12_deal_script()
	insert = r''',
      {
        label: "Create Downstream Preparation",
        onClick: () => {
          call("ndis_crm.phase13_downstream_preparation.create_downstream_preparation_from_crm_deal", {
            deal: doc.name
          }).then((data) => {
            if (data && data.name) {
              createToast({
                title: data.created ? "Downstream Preparation Created" : "Existing Downstream Preparation Found",
                icon: "check",
                iconClasses: "text-green-600",
              })
              window.open(`/app/ndis-crm-downstream-preparation/${data.name}`, "_blank")
            }
          })
        }
      },
      {
        label: "Open Downstream Preparation",
        onClick: () => {
          if (doc.ndis_downstream_preparation) {
            window.open(`/app/ndis-crm-downstream-preparation/${doc.ndis_downstream_preparation}`, "_blank")
          } else {
            createToast({ title: "No Downstream Preparation linked yet", icon: "info" })
          }
        }
      }'''
	return script.replace("\n    ]", insert + "\n    ]")


def _evidence_script():
	from ndis_crm.setup.phase12_delivery_evidence import _evidence_review_script

	script = _evidence_review_script()
	insert = r'''

        frm.add_custom_button(__("Create Downstream Preparation"), function () {
            frappe.call({
                method: "ndis_crm.phase13_downstream_preparation.create_downstream_preparation_from_evidence_review",
                args: { evidence_review: frm.doc.name },
                freeze: true,
                freeze_message: __("Creating downstream preparation...")
            }).then((r) => {
                if (r.message && r.message.name) {
                    frappe.show_alert({ message: r.message.message || __("Downstream Preparation created"), indicator: "green" });
                    frm.reload_doc();
                    frappe.set_route("Form", "NDIS CRM Downstream Preparation", r.message.name);
                }
            });
        }, __("Actions"));

        if (frm.doc.ndis_downstream_preparation) {
            frm.add_custom_button(__("Open Downstream Preparation"), function () {
                frappe.set_route("Form", "NDIS CRM Downstream Preparation", frm.doc.ndis_downstream_preparation);
            }, __("Open"));
        }
'''
	return script.replace("\n        if (frm.doc.service_session_draft)", insert + "\n        if (frm.doc.service_session_draft)")


def _downstream_script():
	return r'''
frappe.ui.form.on("NDIS CRM Downstream Preparation", {
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }

        frm.add_custom_button(__("Generate Preparation Lines"), function () {
            frappe.call({
                method: "ndis_crm.phase13_downstream_preparation.generate_preparation_lines",
                args: { downstream_preparation: frm.doc.name },
                freeze: true,
                freeze_message: __("Generating preparation lines...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Preparation lines generated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Validate Preparation Readiness"), function () {
            frappe.call({
                method: "ndis_crm.phase13_downstream_preparation.validate_downstream_preparation_readiness",
                args: { downstream_preparation: frm.doc.name },
                freeze: true,
                freeze_message: __("Validating downstream preparation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Downstream preparation validated"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Mark Ready for Downstream Processing"), function () {
            frappe.call({
                method: "ndis_crm.phase13_downstream_preparation.mark_ready_for_downstream_processing",
                args: { downstream_preparation: frm.doc.name },
                freeze: true,
                freeze_message: __("Marking ready for downstream processing...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Ready for downstream processing"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        frm.add_custom_button(__("Approve Downstream Preparation"), function () {
            frappe.call({
                method: "ndis_crm.phase13_downstream_preparation.approve_downstream_preparation",
                args: { downstream_preparation: frm.doc.name },
                freeze: true,
                freeze_message: __("Approving downstream preparation...")
            }).then((r) => {
                if (r.message) {
                    frappe.show_alert({ message: r.message.message || __("Downstream Preparation approved"), indicator: "green" });
                    frm.reload_doc();
                }
            });
        }, __("Actions"));

        if (frm.doc.delivery_evidence_review) {
            frm.add_custom_button(__("Open Delivery Evidence Review"), function () {
                frappe.set_route("Form", "NDIS CRM Service Delivery Evidence Review", frm.doc.delivery_evidence_review);
            }, __("Open"));
        }

        if (frm.doc.service_session_draft) {
            frm.add_custom_button(__("Open Service Session Draft"), function () {
                frappe.set_route("Form", "NDIS CRM Service Session Draft", frm.doc.service_session_draft);
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
