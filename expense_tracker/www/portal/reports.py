import frappe
from expense_tracker.api import get_portal_context

def get_context(context):
	get_portal_context(context)
	if not context.is_admin:
		frappe.local.flags.redirect_location = "/portal/dashboard"
		raise frappe.Redirect
