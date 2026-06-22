import frappe
from expense_tracker.api import get_portal_context

def get_context(context):
	get_portal_context(context)
