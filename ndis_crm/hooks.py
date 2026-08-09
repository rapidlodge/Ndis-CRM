app_name = "ndis_crm"
app_title = "NDIS CRM"
app_publisher = "Hex Flow"
app_description = "Custom NDIS CRM app for ERPNext"
app_email = "info@hexflow.com.au"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/ndis_crm/css/ndis_crm.css"
# app_include_js = "/assets/ndis_crm/js/ndis_crm.js"

# include js, css files in header of web template
# web_include_css = "/assets/ndis_crm/css/ndis_crm.css"
# web_include_js = "/assets/ndis_crm/js/ndis_crm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "ndis_crm/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "ndis_crm/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "ndis_crm.utils.jinja_methods",
# 	"filters": "ndis_crm.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "ndis_crm.install.before_install"
# after_install = "ndis_crm.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "ndis_crm.uninstall.before_uninstall"
# after_uninstall = "ndis_crm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "ndis_crm.utils.before_app_install"
# after_app_install = "ndis_crm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "ndis_crm.utils.before_app_uninstall"
# after_app_uninstall = "ndis_crm.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "ndis_crm.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "ndis_crm.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"ndis_crm.tasks.all"
# 	],
# 	"daily": [
# 		"ndis_crm.tasks.daily"
# 	],
# 	"hourly": [
# 		"ndis_crm.tasks.hourly"
# 	],
# 	"weekly": [
# 		"ndis_crm.tasks.weekly"
# 	],
# 	"monthly": [
# 		"ndis_crm.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "ndis_crm.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "ndis_crm.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "ndis_crm.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "ndis_crm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["ndis_crm.utils.before_request"]
# after_request = ["ndis_crm.utils.after_request"]

# Job Events
# ----------
# before_job = ["ndis_crm.utils.before_job"]
# after_job = ["ndis_crm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"ndis_crm.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


# -------------------------------
# NDIS CRM Foundation
# -------------------------------

after_install = "ndis_crm.setup.foundation.after_install"

# fixtures = [
#     {
#         "doctype": "Custom Field",
#         "filters": [
#             [
#                 "dt",
#                 "in",
#                 [
#                     "Lead",
#                     "Opportunity",
#                     "CRM Lead",
#                     "CRM Deal",
#                 ]
#             ]
#         ]
#     },
#     {
#         "doctype": "Role",
#         "filters": [
#             [
#                 "name",
#                 "in",
#                 [
#                     "NDIS CRM Manager",
#                     "NDIS Intake Officer",
#                     "NDIS Service Manager",
#                     "NDIS Plan Management Officer",
#                     "NDIS CRM Read Only"
#                 ]
#             ]
#         ]
#     }
    
# ]
fixtures = [
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "Lead",
                    "Opportunity",
                    "CRM Lead",
                    "CRM Deal"
                ]
            ]
        ]
    },
    {
        "doctype": "Role",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Manager",
                    "NDIS Intake Officer",
                    "NDIS Service Manager",
                    "NDIS Plan Management Officer",
                    "NDIS CRM Read Only"
                ]
            ]
        ]
    },
    {
        "doctype": "Workspace",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM"
                ]
            ]
        ]
    },
    {
        "doctype": "Desktop Icon",
        "filters": [
            [
                "app",
                "=",
                "ndis_crm"
            ]
        ]
    }
]
# -------------------------------
# NDIS CRM App Icon - Final
# -------------------------------

# -------------------------------
# NDIS CRM App Icon
# -------------------------------

add_to_apps_screen = [
    {
        "name": "ndis_crm",
        "logo": "/assets/ndis_crm/images/ndis_crm.svg",
        "title": "NDIS CRM",
        "route": "/ndis-crm",
        "has_permission": "ndis_crm.api.has_app_permission",
    }
]

# -------------------------------
# NDIS CRM Phase 2 - Frappe CRM Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.update({
    "CRM Lead": {
        "validate": "ndis_crm.phase2_api.validate_crm_lead"
    },
    "CRM Deal": {
        "validate": "ndis_crm.phase2_api.validate_crm_deal"
    },
    "NDIS Participant Intake": {
        "validate": "ndis_crm.phase2_api.validate_intake"
    }
})

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "CRM Lead Status",
        "filters": [
            [
                "name",
                "in",
                [
                    "New Enquiry",
                    "Contact Attempted",
                    "Contacted",
                    "Intake Started",
                    "Waiting Documents",
                    "Funding / Suitability Review",
                    "Qualified",
                    "Converted",
                    "Not Suitable",
                    "No Response",
                    "Duplicate",
                    "Declined by Participant",
                    "No Funding",
                    "Provider Capacity Issue"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Deal Status",
        "filters": [
            [
                "name",
                "in",
                [
                    "New Opportunity",
                    "Service Need Confirmed",
                    "Documents Requested",
                    "Documents Collected",
                    "Funding Verified",
                    "Service Agreement Sent",
                    "Service Agreement Signed",
                    "Handover to Operations",
                    "Won / Active Client",
                    "Lost"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Lead Actions",
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 3 - Document Collection Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase3_documents.validate_crm_deal_combined"

doc_events.setdefault("NDIS Document Request", {})
doc_events["NDIS Document Request"]["after_insert"] = "ndis_crm.phase3_documents.on_document_request_update"
doc_events["NDIS Document Request"]["on_update"] = "ndis_crm.phase3_documents.on_document_request_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "NDIS Document Type"
    },
    {
        "doctype": "NDIS Service Document Rule"
    }
])

# -------------------------------
# NDIS CRM Phase 4 - Handover Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase4_handover.validate_crm_deal_phase4_combined"

doc_events.setdefault("NDIS CRM Handover", {})
doc_events["NDIS CRM Handover"]["validate"] = "ndis_crm.phase4_handover.validate_handover"
doc_events["NDIS CRM Handover"]["on_update"] = "ndis_crm.phase4_handover.on_handover_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 5 - Finance Onboarding Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase5_finance_onboarding.validate_crm_deal_phase5_combined"

doc_events.setdefault("NDIS CRM Finance Onboarding", {})
doc_events["NDIS CRM Finance Onboarding"]["validate"] = "ndis_crm.phase5_finance_onboarding.validate_finance_onboarding"
doc_events["NDIS CRM Finance Onboarding"]["on_update"] = "ndis_crm.phase5_finance_onboarding.on_finance_onboarding_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "NDIS Service Line",
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 6 - Finance Budget and Service Booking Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("NDIS CRM Finance Onboarding", {})
doc_events["NDIS CRM Finance Onboarding"]["validate"] = "ndis_crm.phase6_finance_drafts.validate_finance_onboarding_phase6_combined"
doc_events["NDIS CRM Finance Onboarding"]["on_update"] = "ndis_crm.phase6_finance_drafts.on_finance_onboarding_phase6_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Finance Onboarding Service",
                    "NDIS Plan Budget",
                    "NDIS Service Booking",
                    "CRM Deal",
                    "NDIS CRM Handover"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 7 - Operations Setup Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase7_operations_setup.validate_crm_deal_phase7_combined"

doc_events.setdefault("NDIS CRM Operations Setup", {})
doc_events["NDIS CRM Operations Setup"]["validate"] = "ndis_crm.phase7_operations_setup.validate_operations_setup"
doc_events["NDIS CRM Operations Setup"]["on_update"] = "ndis_crm.phase7_operations_setup.on_operations_setup_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 8 - Service Schedule Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase8_service_schedule.validate_crm_deal_phase8_combined"

doc_events.setdefault("NDIS CRM Service Schedule Draft", {})
doc_events["NDIS CRM Service Schedule Draft"]["validate"] = "ndis_crm.phase8_service_schedule.validate_schedule_draft"
doc_events["NDIS CRM Service Schedule Draft"]["on_update"] = "ndis_crm.phase8_service_schedule.on_schedule_draft_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Operations Setup",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 9 - Roster Build Request Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase9_roster_build_request.validate_crm_deal_phase9_combined"

doc_events.setdefault("NDIS CRM Roster Build Request", {})
doc_events["NDIS CRM Roster Build Request"]["validate"] = "ndis_crm.phase9_roster_build_request.validate_roster_build_request"
doc_events["NDIS CRM Roster Build Request"]["on_update"] = "ndis_crm.phase9_roster_build_request.on_roster_build_request_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Operations Setup",
                    "NDIS CRM Service Schedule Draft",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 10 - Active Participant Service File Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase10_service_file.validate_crm_deal_phase10_combined"

doc_events.setdefault("NDIS Participant Service File", {})
doc_events["NDIS Participant Service File"]["validate"] = "ndis_crm.phase10_service_file.validate_service_file"
doc_events["NDIS Participant Service File"]["on_update"] = "ndis_crm.phase10_service_file.on_service_file_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Operations Setup",
                    "NDIS CRM Service Schedule Draft",
                    "NDIS CRM Roster Build Request",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 11 - Service Delivery Session Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase11_service_sessions.validate_crm_deal_phase11_combined"

doc_events.setdefault("NDIS CRM Service Session Draft", {})
doc_events["NDIS CRM Service Session Draft"]["validate"] = "ndis_crm.phase11_service_sessions.validate_session_draft"
doc_events["NDIS CRM Service Session Draft"]["on_update"] = "ndis_crm.phase11_service_sessions.on_session_draft_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Operations Setup",
                    "NDIS CRM Service Schedule Draft",
                    "NDIS CRM Roster Build Request",
                    "NDIS Participant Service File",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 12 - Service Delivery Evidence Review Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase12_delivery_evidence.validate_crm_deal_phase12_combined"

doc_events.setdefault("NDIS CRM Service Delivery Evidence Review", {})
doc_events["NDIS CRM Service Delivery Evidence Review"]["validate"] = "ndis_crm.phase12_delivery_evidence.validate_evidence_review"
doc_events["NDIS CRM Service Delivery Evidence Review"]["on_update"] = "ndis_crm.phase12_delivery_evidence.on_evidence_review_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Operations Setup",
                    "NDIS CRM Service Schedule Draft",
                    "NDIS CRM Roster Build Request",
                    "NDIS Participant Service File",
                    "NDIS CRM Service Session Draft",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 13 - Attendance/Billing/Payroll/Claim Preparation Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase13_downstream_preparation.validate_crm_deal_phase13_combined"

doc_events.setdefault("NDIS CRM Downstream Preparation", {})
doc_events["NDIS CRM Downstream Preparation"]["validate"] = "ndis_crm.phase13_downstream_preparation.validate_downstream_preparation"
doc_events["NDIS CRM Downstream Preparation"]["on_update"] = "ndis_crm.phase13_downstream_preparation.on_downstream_preparation_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Operations Setup",
                    "NDIS CRM Service Schedule Draft",
                    "NDIS CRM Roster Build Request",
                    "NDIS Participant Service File",
                    "NDIS CRM Service Session Draft",
                    "NDIS CRM Service Delivery Evidence Review",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 14 - Controlled Attendance Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase14_attendance_draft.validate_crm_deal_phase14_combined"

doc_events.setdefault("NDIS CRM Attendance Draft", {})
doc_events["NDIS CRM Attendance Draft"]["validate"] = "ndis_crm.phase14_attendance_draft.validate_attendance_draft"
doc_events["NDIS CRM Attendance Draft"]["on_update"] = "ndis_crm.phase14_attendance_draft.on_attendance_draft_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "NDIS CRM Handover",
                    "NDIS CRM Finance Onboarding",
                    "NDIS CRM Operations Setup",
                    "NDIS CRM Service Schedule Draft",
                    "NDIS CRM Roster Build Request",
                    "NDIS Participant Service File",
                    "NDIS CRM Service Session Draft",
                    "NDIS CRM Service Delivery Evidence Review",
                    "NDIS CRM Downstream Preparation",
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 15 - Controlled Billing Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase15_billing_draft.validate_crm_deal_phase15_combined"

doc_events.setdefault("NDIS CRM Billing Draft", {})
doc_events["NDIS CRM Billing Draft"]["validate"] = "ndis_crm.phase15_billing_draft.validate_billing_draft"
doc_events["NDIS CRM Billing Draft"]["on_update"] = "ndis_crm.phase15_billing_draft.on_billing_draft_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 16 - Controlled Claim Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase16_claim_draft.validate_crm_deal_phase16_combined"

doc_events.setdefault("NDIS CRM Claim Draft", {})
doc_events["NDIS CRM Claim Draft"]["validate"] = "ndis_crm.phase16_claim_draft.validate_claim_draft"
doc_events["NDIS CRM Claim Draft"]["on_update"] = "ndis_crm.phase16_claim_draft.on_claim_draft_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 17 - Controlled Invoice Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase17_invoice_draft.validate_crm_deal_phase17_combined"

doc_events.setdefault("NDIS CRM Invoice Draft", {})
doc_events["NDIS CRM Invoice Draft"]["validate"] = "ndis_crm.phase17_invoice_draft.validate_invoice_draft"
doc_events["NDIS CRM Invoice Draft"]["on_update"] = "ndis_crm.phase17_invoice_draft.on_invoice_draft_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 18 - Controlled Sales Invoice Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase18_sales_invoice_draft.validate_crm_deal_phase18_combined"

doc_events.setdefault("NDIS CRM Sales Invoice Draft Run", {})
doc_events["NDIS CRM Sales Invoice Draft Run"]["validate"] = "ndis_crm.phase18_sales_invoice_draft.validate_sales_invoice_draft_run"
doc_events["NDIS CRM Sales Invoice Draft Run"]["on_update"] = "ndis_crm.phase18_sales_invoice_draft.on_sales_invoice_draft_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 19 - Controlled Sales Invoice Submission Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase19_sales_invoice_submission.validate_crm_deal_phase19_combined"

doc_events.setdefault("NDIS CRM Sales Invoice Submission Run", {})
doc_events["NDIS CRM Sales Invoice Submission Run"]["validate"] = "ndis_crm.phase19_sales_invoice_submission.validate_sales_invoice_submission_run"
doc_events["NDIS CRM Sales Invoice Submission Run"]["on_update"] = "ndis_crm.phase19_sales_invoice_submission.on_sales_invoice_submission_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 20 - Controlled NDIS Claim Batch Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase20_claim_batch_draft.validate_crm_deal_phase20_combined"

doc_events.setdefault("NDIS CRM Claim Batch Draft Run", {})
doc_events["NDIS CRM Claim Batch Draft Run"]["validate"] = "ndis_crm.phase20_claim_batch_draft.validate_claim_batch_draft_run"
doc_events["NDIS CRM Claim Batch Draft Run"]["on_update"] = "ndis_crm.phase20_claim_batch_draft.on_claim_batch_draft_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 21 - Controlled NDIS Claim Batch Submission / Export Gate Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase21_claim_batch_submission.validate_crm_deal_phase21_combined"

doc_events.setdefault("NDIS CRM Claim Batch Submission Run", {})
doc_events["NDIS CRM Claim Batch Submission Run"]["validate"] = "ndis_crm.phase21_claim_batch_submission.validate_claim_batch_submission_run"
doc_events["NDIS CRM Claim Batch Submission Run"]["on_update"] = "ndis_crm.phase21_claim_batch_submission.on_claim_batch_submission_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 22 - Controlled Claim Export File Preparation Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase22_claim_export_preparation.validate_crm_deal_phase22_combined"

doc_events.setdefault("NDIS CRM Claim Export Preparation Run", {})
doc_events["NDIS CRM Claim Export Preparation Run"]["validate"] = "ndis_crm.phase22_claim_export_preparation.validate_claim_export_preparation_run"
doc_events["NDIS CRM Claim Export Preparation Run"]["on_update"] = "ndis_crm.phase22_claim_export_preparation.on_claim_export_preparation_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 23 - Controlled Claim Lodgement Confirmation Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase23_claim_lodgement_confirmation.validate_crm_deal_phase23_combined"

doc_events.setdefault("NDIS CRM Claim Lodgement Confirmation Run", {})
doc_events["NDIS CRM Claim Lodgement Confirmation Run"]["validate"] = "ndis_crm.phase23_claim_lodgement_confirmation.validate_claim_lodgement_confirmation_run"
doc_events["NDIS CRM Claim Lodgement Confirmation Run"]["on_update"] = "ndis_crm.phase23_claim_lodgement_confirmation.on_claim_lodgement_confirmation_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 24 - Controlled Remittance Import Preparation Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase24_remittance_import_preparation.validate_crm_deal_phase24_combined"

doc_events.setdefault("NDIS CRM Remittance Import Preparation Run", {})
doc_events["NDIS CRM Remittance Import Preparation Run"]["validate"] = "ndis_crm.phase24_remittance_import_preparation.validate_remittance_import_preparation_run"
doc_events["NDIS CRM Remittance Import Preparation Run"]["on_update"] = "ndis_crm.phase24_remittance_import_preparation.on_remittance_import_preparation_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 25 - Controlled Actual Remittance Import Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase25_actual_remittance_import.validate_crm_deal_phase25_combined"

doc_events.setdefault("NDIS CRM Actual Remittance Import Run", {})
doc_events["NDIS CRM Actual Remittance Import Run"]["validate"] = "ndis_crm.phase25_actual_remittance_import.validate_actual_remittance_import_run"
doc_events["NDIS CRM Actual Remittance Import Run"]["on_update"] = "ndis_crm.phase25_actual_remittance_import.on_actual_remittance_import_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 26 - Controlled Remittance Matching Review Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase26_remittance_matching_review.validate_crm_deal_phase26_combined"

doc_events.setdefault("NDIS CRM Remittance Matching Review Run", {})
doc_events["NDIS CRM Remittance Matching Review Run"]["validate"] = "ndis_crm.phase26_remittance_matching_review.validate_remittance_matching_review_run"
doc_events["NDIS CRM Remittance Matching Review Run"]["on_update"] = "ndis_crm.phase26_remittance_matching_review.on_remittance_matching_review_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 27 - Controlled Payment Allocation Preparation Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase27_payment_allocation_preparation.validate_crm_deal_phase27_combined"

doc_events.setdefault("NDIS CRM Payment Allocation Preparation Run", {})
doc_events["NDIS CRM Payment Allocation Preparation Run"]["validate"] = "ndis_crm.phase27_payment_allocation_preparation.validate_payment_allocation_preparation_run"
doc_events["NDIS CRM Payment Allocation Preparation Run"]["on_update"] = "ndis_crm.phase27_payment_allocation_preparation.on_payment_allocation_preparation_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions",
                    "NDIS CRM Payment Allocation Preparation Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 28 - Controlled Payment Entry Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase28_payment_entry_draft.validate_crm_deal_phase28_combined"

doc_events.setdefault("NDIS CRM Payment Entry Draft Run", {})
doc_events["NDIS CRM Payment Entry Draft Run"]["validate"] = "ndis_crm.phase28_payment_entry_draft.validate_payment_entry_draft_run"
doc_events["NDIS CRM Payment Entry Draft Run"]["on_update"] = "ndis_crm.phase28_payment_entry_draft.on_payment_entry_draft_run_update"

doc_events.setdefault("Payment Entry", {})
doc_events["Payment Entry"]["before_submit"] = "ndis_crm.phase28_payment_entry_draft.validate_payment_entry_phase28_submit_guard"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "Payment Entry",
                    "Payment Entry Reference",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions",
                    "NDIS CRM Payment Allocation Preparation Run Actions",
                    "NDIS CRM Payment Entry Draft Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 29 - Controlled Payment Entry Submission Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase29_payment_entry_submission.validate_crm_deal_phase29_combined"

doc_events.setdefault("NDIS CRM Payment Entry Submission Run", {})
doc_events["NDIS CRM Payment Entry Submission Run"]["validate"] = "ndis_crm.phase29_payment_entry_submission.validate_payment_entry_submission_run"
doc_events["NDIS CRM Payment Entry Submission Run"]["on_update"] = "ndis_crm.phase29_payment_entry_submission.on_payment_entry_submission_run_update"

doc_events.setdefault("Payment Entry", {})
doc_events["Payment Entry"]["before_submit"] = "ndis_crm.phase29_payment_entry_submission.validate_payment_entry_phase29_submit_guard"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "Payment Entry",
                    "Payment Entry Reference",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions",
                    "NDIS CRM Payment Allocation Preparation Run Actions",
                    "NDIS CRM Payment Entry Draft Run Actions",
                    "NDIS CRM Payment Entry Submission Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 30 - Controlled Remittance Import Finalisation Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase30_remittance_import_finalisation.validate_crm_deal_phase30_combined"

doc_events.setdefault("NDIS CRM Remittance Import Finalisation Run", {})
doc_events["NDIS CRM Remittance Import Finalisation Run"]["validate"] = "ndis_crm.phase30_remittance_import_finalisation.validate_remittance_import_finalisation_run"
doc_events["NDIS CRM Remittance Import Finalisation Run"]["on_update"] = "ndis_crm.phase30_remittance_import_finalisation.on_remittance_import_finalisation_run_update"

doc_events.setdefault("NDIS Remittance Import", {})
doc_events["NDIS Remittance Import"]["before_submit"] = "ndis_crm.phase30_remittance_import_finalisation.validate_remittance_import_phase30_submit_guard"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "Payment Entry",
                    "Payment Entry Reference",
                    "NDIS Remittance Import",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions",
                    "NDIS CRM Payment Allocation Preparation Run Actions",
                    "NDIS CRM Payment Entry Draft Run Actions",
                    "NDIS CRM Payment Entry Submission Run Actions",
                    "NDIS CRM Remittance Import Finalisation Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 31 - Controlled Variance/Rejection Review Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase31_variance_rejection_review.validate_crm_deal_phase31_combined"

doc_events.setdefault("NDIS CRM Variance Rejection Review Run", {})
doc_events["NDIS CRM Variance Rejection Review Run"]["validate"] = "ndis_crm.phase31_variance_rejection_review.validate_variance_rejection_review_run"
doc_events["NDIS CRM Variance Rejection Review Run"]["on_update"] = "ndis_crm.phase31_variance_rejection_review.on_variance_rejection_review_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "Payment Entry",
                    "Payment Entry Reference",
                    "NDIS Remittance Import",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions",
                    "NDIS CRM Payment Allocation Preparation Run Actions",
                    "NDIS CRM Payment Entry Draft Run Actions",
                    "NDIS CRM Payment Entry Submission Run Actions",
                    "NDIS CRM Remittance Import Finalisation Run Actions",
                    "NDIS CRM Variance Rejection Review Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 32 - Controlled Write Off Preparation Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase32_write_off_preparation.validate_crm_deal_phase32_combined"

doc_events.setdefault("NDIS CRM Write Off Preparation Run", {})
doc_events["NDIS CRM Write Off Preparation Run"]["validate"] = "ndis_crm.phase32_write_off_preparation.validate_write_off_preparation_run"
doc_events["NDIS CRM Write Off Preparation Run"]["on_update"] = "ndis_crm.phase32_write_off_preparation.on_write_off_preparation_run_update"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "Payment Entry",
                    "Payment Entry Reference",
                    "NDIS Remittance Import",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions",
                    "NDIS CRM Payment Allocation Preparation Run Actions",
                    "NDIS CRM Payment Entry Draft Run Actions",
                    "NDIS CRM Payment Entry Submission Run Actions",
                    "NDIS CRM Remittance Import Finalisation Run Actions",
                    "NDIS CRM Variance Rejection Review Run Actions",
                    "NDIS CRM Variance Review Phase32 Actions",
                    "NDIS CRM Write Off Preparation Run Actions"
                ]
            ]
        ]
    }
])

# -------------------------------
# NDIS CRM Phase 33 - Controlled Write Off Draft Hooks
# -------------------------------

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("CRM Deal", {})
doc_events["CRM Deal"]["validate"] = "ndis_crm.phase33_write_off_draft.validate_crm_deal_phase33_combined"

doc_events.setdefault("NDIS CRM Write Off Draft Run", {})
doc_events["NDIS CRM Write Off Draft Run"]["validate"] = "ndis_crm.phase33_write_off_draft.validate_write_off_draft_run"
doc_events["NDIS CRM Write Off Draft Run"]["on_update"] = "ndis_crm.phase33_write_off_draft.on_write_off_draft_run_update"

doc_events.setdefault("NDIS Write Off", {})
doc_events["NDIS Write Off"]["before_submit"] = "ndis_crm.phase33_write_off_draft.validate_optional_ndis_write_off_phase33_submit_guard"

try:
    fixtures
except NameError:
    fixtures = []

fixtures.extend([
    {
        "doctype": "Custom Field",
        "filters": [
            [
                "dt",
                "in",
                [
                    "CRM Deal",
                    "Payment Entry",
                    "Payment Entry Reference",
                    "NDIS Remittance Import",
                    "NDIS Write Off",
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
                    "NDIS Participant Intake"
                ]
            ]
        ]
    },
    {
        "doctype": "CRM Form Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS CRM Deal Actions"
                ]
            ]
        ]
    },
    {
        "doctype": "Client Script",
        "filters": [
            [
                "name",
                "in",
                [
                    "NDIS Participant Intake Actions",
                    "NDIS CRM Handover Actions",
                    "NDIS CRM Finance Onboarding Actions",
                    "NDIS CRM Operations Setup Actions",
                    "NDIS CRM Service Schedule Draft Actions",
                    "NDIS CRM Roster Build Request Actions",
                    "NDIS Participant Service File Actions",
                    "NDIS CRM Service Session Draft Actions",
                    "NDIS CRM Service Delivery Evidence Review Actions",
                    "NDIS CRM Downstream Preparation Actions",
                    "NDIS CRM Attendance Draft Actions",
                    "NDIS CRM Billing Draft Actions",
                    "NDIS CRM Claim Draft Actions",
                    "NDIS CRM Invoice Draft Actions",
                    "NDIS CRM Sales Invoice Draft Run Actions",
                    "NDIS CRM Sales Invoice Submission Run Actions",
                    "NDIS CRM Claim Batch Draft Run Actions",
                    "NDIS CRM Claim Batch Submission Run Actions",
                    "NDIS CRM Claim Export Preparation Run Actions",
                    "NDIS CRM Claim Lodgement Confirmation Run Actions",
                    "NDIS CRM Remittance Import Preparation Run Actions",
                    "NDIS CRM Actual Remittance Import Run Actions",
                    "NDIS CRM Remittance Matching Review Run Actions",
                    "NDIS CRM Payment Allocation Preparation Run Actions",
                    "NDIS CRM Payment Entry Draft Run Actions",
                    "NDIS CRM Payment Entry Submission Run Actions",
                    "NDIS CRM Remittance Import Finalisation Run Actions",
                    "NDIS CRM Variance Rejection Review Run Actions",
                    "NDIS CRM Variance Review Phase32 Actions",
                    "NDIS CRM Write Off Preparation Run Actions",
                    "NDIS CRM Write Off Preparation Phase33 Actions",
                    "NDIS CRM Write Off Draft Run Actions"
                ]
            ]
        ]
    }
])
