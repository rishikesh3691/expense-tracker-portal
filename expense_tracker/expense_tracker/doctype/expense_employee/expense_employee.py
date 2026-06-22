import frappe
from frappe.model.document import Document

class ExpenseEmployee(Document):
	def validate(self):
		if self.user:
			# Auto fill email and full name from user record if missing
			user_doc = frappe.get_doc("User", self.user)
			if not self.email:
				self.email = user_doc.email
			if not self.employee_name:
				self.employee_name = user_doc.full_name or user_doc.name
