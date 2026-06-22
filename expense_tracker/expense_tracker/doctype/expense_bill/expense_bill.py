import frappe
from frappe.model.document import Document
from frappe import _

class ExpenseBill(Document):
	def validate(self):
		if not self.submitted_by:
			self.submitted_by = frappe.session.user
		
		# If status is modified, ensure only Expense Admin or System Manager can approve/reject
		if self.has_value_changed("status") and self.status != "Pending":
			roles = frappe.get_roles(frappe.session.user)
			if "Expense Admin" not in roles and "System Manager" not in roles:
				frappe.throw(_("Only Expense Admin can approve or reject bills"))
