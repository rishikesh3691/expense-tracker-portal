import frappe
from frappe import _
from frappe.utils import add_days, today, getdate, formatdate
import json
import random

# Helper methods to verify roles
def is_admin(user=None):
	if not user:
		user = frappe.session.user
	if user == "Administrator":
		return True
	roles = frappe.get_roles(user)
	return "Expense Admin" in roles or "System Manager" in roles

def is_employee(user=None):
	if not user:
		user = frappe.session.user
	roles = frappe.get_roles(user)
	return "Expense Employee" in roles

def check_auth():
	if frappe.session.user == "Guest":
		frappe.throw(_("Please log in to access this resource"), frappe.PermissionError)

# --- PORTAL API METHODS ---

@frappe.whitelist()
@frappe.whitelist()
def get_dashboard_stats(status=None, category=None, employee=None, date=None):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access denied. Only Expense Admins can view admin dashboard stats."), frappe.PermissionError)

	conditions = ["1=1"]
	params = []

	if category and category != "All":
		conditions.append("category = %s")
		params.append(category)

	if employee:
		conditions.append("submitted_by = %s")
		params.append(employee)

	if date:
		conditions.append("bill_date = %s")
		params.append(date)

	where_clause = " AND ".join(conditions)

	conditions_gross = list(conditions)
	params_gross = list(params)
	if status and status != "All":
		conditions_gross.append("status = %s")
		params_gross.append(status)
	where_clause_gross = " AND ".join(conditions_gross)

	# Total Submitted Amount (Approved + Pending + Rejected)
	total_submitted = frappe.db.sql(f"""
		SELECT SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_gross}
	""", tuple(params_gross))[0][0] or 0.0

	# Pending Stats
	conditions_pending = list(conditions)
	params_pending = list(params)
	conditions_pending.append("status = 'Pending'")
	where_clause_pending = " AND ".join(conditions_pending)
	pending_stats = frappe.db.sql(f"""
		SELECT COUNT(name), SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_pending}
	""", tuple(params_pending))[0]
	pending_count = pending_stats[0] or 0
	pending_amount = pending_stats[1] or 0.0

	# Approved Stats
	conditions_approved = list(conditions)
	params_approved = list(params)
	conditions_approved.append("status = 'Approved'")
	where_clause_approved = " AND ".join(conditions_approved)
	approved_stats = frappe.db.sql(f"""
		SELECT COUNT(name), SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_approved}
	""", tuple(params_approved))[0]
	approved_count = approved_stats[0] or 0
	approved_amount = approved_stats[1] or 0.0

	# Rejected Stats
	conditions_rejected = list(conditions)
	params_rejected = list(params)
	conditions_rejected.append("status = 'Rejected'")
	where_clause_rejected = " AND ".join(conditions_rejected)
	rejected_stats = frappe.db.sql(f"""
		SELECT COUNT(name), SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_rejected}
	""", tuple(params_rejected))[0]
	rejected_count = rejected_stats[0] or 0
	rejected_amount = rejected_stats[1] or 0.0

	# Total Employees Count
	employee_count = frappe.db.count("Expense Employee", filters={"status": "Active"})

	# Recent Bills (last 5)
	recent_bills = frappe.db.sql(f"""
		SELECT name, bill_title, amount, category, bill_date, submitted_by, status
		FROM `tabExpense Bill`
		WHERE {where_clause_gross}
		ORDER BY creation desc
		LIMIT 5
	""", tuple(params_gross), as_dict=True)
	
	# Fetch Full Name for each submitted_by
	for bill in recent_bills:
		bill["submitter_name"] = frappe.db.get_value("User", bill.submitted_by, "full_name") or bill.submitted_by

	# Approved Category Breakdown
	conditions_cat = list(conditions)
	params_cat = list(params)
	conditions_cat.append("status = 'Approved'")
	where_clause_cat = " AND ".join(conditions_cat)
	category_breakdown = frappe.db.sql(f"""
		SELECT category, SUM(amount) as total 
		FROM `tabExpense Bill` 
		WHERE {where_clause_cat}
		GROUP BY category
	""", tuple(params_cat), as_dict=True)

	# Monthly Trend (last 6 months)
	monthly_trend = frappe.db.sql(f"""
		SELECT 
			DATE_FORMAT(bill_date, '%%Y-%%m') as month,
			SUM(CASE WHEN status = 'Approved' THEN amount ELSE 0 END) as approved,
			SUM(amount) as total
		FROM `tabExpense Bill`
		WHERE {where_clause}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 6
	""", tuple(params), as_dict=True)

	# Recent Activity (last 10 modified bills across the system)
	recent_activity = frappe.db.sql(f"""
		SELECT name, bill_title, amount, status, creation, modified, modified_by, submitted_by, remarks
		FROM `tabExpense Bill`
		WHERE {where_clause_gross}
		ORDER BY modified DESC
		LIMIT 10
	""", tuple(params_gross), as_dict=True)

	for act in recent_activity:
		act["submitter_name"] = frappe.db.get_value("User", act.submitted_by, "full_name") or act.submitted_by
		act["modifier_name"] = frappe.db.get_value("User", act.modified_by, "full_name") or act.modified_by

	return {
		"total_submitted": total_submitted,
		"pending_count": pending_count,
		"pending_amount": pending_amount,
		"approved_count": approved_count,
		"approved_amount": approved_amount,
		"rejected_count": rejected_count,
		"rejected_amount": rejected_amount,
		"employee_count": employee_count,
		"recent_bills": recent_bills,
		"category_breakdown": category_breakdown,
		"monthly_trend": monthly_trend,
		"recent_activity": recent_activity
	}

@frappe.whitelist()
def get_my_dashboard_stats(status=None, category=None, date=None):
	check_auth()
	user = frappe.session.user

	conditions = ["submitted_by = %s"]
	params = [user]

	if category and category != "All":
		conditions.append("category = %s")
		params.append(category)

	if date:
		conditions.append("bill_date = %s")
		params.append(date)

	where_clause = " AND ".join(conditions)

	conditions_gross = list(conditions)
	params_gross = list(params)
	if status and status != "All":
		conditions_gross.append("status = %s")
		params_gross.append(status)
	where_clause_gross = " AND ".join(conditions_gross)

	# Total Submitted Amount (Approved + Pending + Rejected)
	total_submitted = frappe.db.sql(f"""
		SELECT SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_gross}
	""", tuple(params_gross))[0][0] or 0.0

	# Pending Stats
	conditions_pending = list(conditions)
	params_pending = list(params)
	conditions_pending.append("status = 'Pending'")
	where_clause_pending = " AND ".join(conditions_pending)
	pending_stats = frappe.db.sql(f"""
		SELECT COUNT(name), SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_pending}
	""", tuple(params_pending))[0]
	pending_count = pending_stats[0] or 0
	pending_amount = pending_stats[1] or 0.0

	# Approved Stats
	conditions_approved = list(conditions)
	params_approved = list(params)
	conditions_approved.append("status = 'Approved'")
	where_clause_approved = " AND ".join(conditions_approved)
	approved_stats = frappe.db.sql(f"""
		SELECT COUNT(name), SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_approved}
	""", tuple(params_approved))[0]
	approved_count = approved_stats[0] or 0
	approved_amount = approved_stats[1] or 0.0

	# Rejected Stats
	conditions_rejected = list(conditions)
	params_rejected = list(params)
	conditions_rejected.append("status = 'Rejected'")
	where_clause_rejected = " AND ".join(conditions_rejected)
	rejected_stats = frappe.db.sql(f"""
		SELECT COUNT(name), SUM(amount) FROM `tabExpense Bill` WHERE {where_clause_rejected}
	""", tuple(params_rejected))[0]
	rejected_count = rejected_stats[0] or 0
	rejected_amount = rejected_stats[1] or 0.0

	# Recent Bills (last 5)
	recent_bills = frappe.db.sql(f"""
		SELECT name, bill_title, amount, category, bill_date, submitted_by, status
		FROM `tabExpense Bill`
		WHERE {where_clause_gross}
		ORDER BY creation desc
		LIMIT 5
	""", tuple(params_gross), as_dict=True)
	
	for bill in recent_bills:
		bill["submitter_name"] = frappe.db.get_value("User", bill.submitted_by, "full_name") or bill.submitted_by

	# Approved Category Breakdown
	conditions_cat = list(conditions)
	params_cat = list(params)
	conditions_cat.append("status = 'Approved'")
	where_clause_cat = " AND ".join(conditions_cat)
	category_breakdown = frappe.db.sql(f"""
		SELECT category, SUM(amount) as total 
		FROM `tabExpense Bill` 
		WHERE {where_clause_cat}
		GROUP BY category
	""", tuple(params_cat), as_dict=True)

	# Monthly Trend (last 6 months) for this user
	monthly_trend = frappe.db.sql(f"""
		SELECT 
			DATE_FORMAT(bill_date, '%%Y-%%m') as month,
			SUM(CASE WHEN status = 'Approved' THEN amount ELSE 0 END) as approved,
			SUM(amount) as total
		FROM `tabExpense Bill`
		WHERE {where_clause}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 6
	""", tuple(params), as_dict=True)

	# Recent Activity (last 10 modified bills for this user)
	recent_activity = frappe.db.sql(f"""
		SELECT name, bill_title, amount, status, creation, modified, modified_by, submitted_by, remarks
		FROM `tabExpense Bill`
		WHERE {where_clause_gross}
		ORDER BY modified DESC
		LIMIT 10
	""", tuple(params_gross), as_dict=True)

	for act in recent_activity:
		act["submitter_name"] = frappe.db.get_value("User", act.submitted_by, "full_name") or act.submitted_by
		act["modifier_name"] = frappe.db.get_value("User", act.modified_by, "full_name") or act.modified_by

	return {
		"total_submitted": total_submitted,
		"pending_count": pending_count,
		"pending_amount": pending_amount,
		"approved_count": approved_count,
		"approved_amount": approved_amount,
		"rejected_count": rejected_count,
		"rejected_amount": rejected_amount,
		"recent_bills": recent_bills,
		"category_breakdown": category_breakdown,
		"monthly_trend": monthly_trend,
		"recent_activity": recent_activity
	}

@frappe.whitelist()
def get_bills(start=0, page_length=15, search=None, status=None, category=None, employee=None, date=None, **kwargs):
	check_auth()
	user = frappe.session.user
	admin_mode = is_admin(user)

	# Core filters
	filters = {}
	if not admin_mode:
		filters["submitted_by"] = user
	elif employee:
		filters["submitted_by"] = employee

	if status and status != "All":
		filters["status"] = status
	
	if category and category != "All":
		filters["category"] = category

	if date:
		filters["bill_date"] = date

	# Custom search queries
	or_filters = []
	if search:
		or_filters = [
			["bill_title", "like", f"%{search}%"],
			["category", "like", f"%{search}%"],
			["description", "like", f"%{search}%"]
		]
		if admin_mode:
			or_filters.append(["submitted_by", "like", f"%{search}%"])

	# Get matching bills count — frappe.db.count doesn't support or_filters,
	# so use get_all with a count trick when search is active
	if or_filters:
		all_ids = frappe.get_all("Expense Bill",
			fields=["name"],
			filters=filters,
			or_filters=or_filters
		)
		total_count = len(all_ids)
	else:
		total_count = frappe.db.count("Expense Bill", filters=filters)

	# Fetch bills
	bills = frappe.get_all("Expense Bill",
		fields=["name", "bill_title", "amount", "category", "bill_date", "submitted_by", "status", "receipt_image", "description", "remarks"],
		filters=filters,
		or_filters=or_filters,
		order_by="creation desc",
		start=int(start),
		page_length=int(page_length)
	)

	# Append submitter's name
	for bill in bills:
		bill["submitter_name"] = frappe.db.get_value("User", bill.submitted_by, "full_name") or bill.submitted_by

	return {
		"bills": bills,
		"total_count": total_count
	}

@frappe.whitelist()
def create_bill(bill_title, amount, category, bill_date, description=None, receipt_image=None):
	check_auth()
	doc = frappe.get_doc({
		"doctype": "Expense Bill",
		"bill_title": bill_title,
		"amount": float(amount),
		"category": category,
		"bill_date": bill_date,
		"description": description,
		"receipt_image": receipt_image,
		"submitted_by": frappe.session.user,
		"status": "Pending"
	})
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc.as_dict()

@frappe.whitelist()
def update_bill(name, bill_title=None, amount=None, category=None, bill_date=None, description=None, receipt_image=None, remarks=None):
	check_auth()
	doc = frappe.get_doc("Expense Bill", name)
	
	# Verify permission
	if not is_admin() and doc.submitted_by != frappe.session.user:
		frappe.throw(_("Access Denied. You cannot update someone else's bill."), frappe.PermissionError)
		
	if not is_admin() and doc.status != "Pending":
		frappe.throw(_("You can only edit pending bills."))

	# Apply updates
	if bill_title is not None: doc.bill_title = bill_title
	if amount is not None: doc.amount = float(amount)
	if category is not None: doc.category = category
	if bill_date is not None: doc.bill_date = bill_date
	if description is not None: doc.description = description
	if receipt_image is not None: doc.receipt_image = receipt_image
	if is_admin() and remarks is not None: doc.remarks = remarks

	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.as_dict()

@frappe.whitelist()
def delete_bill(name):
	check_auth()
	doc = frappe.get_doc("Expense Bill", name)
	
	if not is_admin() and doc.submitted_by != frappe.session.user:
		frappe.throw(_("Access Denied. You cannot delete someone else's bill."), frappe.PermissionError)
		
	if not is_admin() and doc.status != "Pending":
		frappe.throw(_("You can only delete pending bills."))

	frappe.delete_doc("Expense Bill", name, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}

@frappe.whitelist()
def approve_bill(name, remarks=None):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can approve bills."), frappe.PermissionError)
		
	doc = frappe.get_doc("Expense Bill", name)
	doc.status = "Approved"
	if remarks:
		doc.remarks = remarks
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.as_dict()

@frappe.whitelist()
def reject_bill(name, remarks=None):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can reject bills."), frappe.PermissionError)
		
	doc = frappe.get_doc("Expense Bill", name)
	doc.status = "Rejected"
	if remarks:
		doc.remarks = remarks
	doc.save(ignore_permissions=True)
	frappe.db.commit()
	return doc.as_dict()

@frappe.whitelist()
def get_employees():
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can view employee list."), frappe.PermissionError)
		
	employees = frappe.get_all("Expense Employee", 
		fields=["name", "employee_name", "user", "email", "department", "designation", "phone", "status"],
		order_by="employee_name asc"
	)
	return employees

@frappe.whitelist()
def create_employee(email, employee_name, department=None, designation=None, phone=None, status="Active"):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can create employees."), frappe.PermissionError)
		
	# Create User if it doesn't exist
	if not frappe.db.exists("User", email):
		user_doc = frappe.get_doc({
			"doctype": "User",
			"email": email,
			"first_name": employee_name,
			"enabled": 1 if status == "Active" else 0,
			"send_welcome_email": 0,
			"user_type": "System User"
		})
		user_doc.insert(ignore_permissions=True)
		# Set temporary password
		user_doc.new_password = "ExpenseTracker2026!"
		user_doc.save(ignore_permissions=True)
		user_doc.add_roles("Expense Employee")
	else:
		user_doc = frappe.get_doc("User", email)
		user_doc.enabled = 1 if status == "Active" else 0
		user_doc.save(ignore_permissions=True)
		user_doc.add_roles("Expense Employee")

	# Create Expense Employee
	if not frappe.db.exists("Expense Employee", email):
		emp = frappe.get_doc({
			"doctype": "Expense Employee",
			"user": email,
			"employee_name": employee_name,
			"email": email,
			"department": department,
			"designation": designation,
			"phone": phone,
			"status": status
		})
		emp.insert(ignore_permissions=True)
	else:
		emp = frappe.get_doc("Expense Employee", email)
		emp.employee_name = employee_name
		emp.department = department
		emp.designation = designation
		emp.phone = phone
		emp.status = status
		emp.save(ignore_permissions=True)

	frappe.db.commit()
	return emp.as_dict()

@frappe.whitelist()
def update_employee(email, employee_name, department=None, designation=None, phone=None, status="Active"):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can update employees."), frappe.PermissionError)
		
	emp = frappe.get_doc("Expense Employee", email)
	emp.employee_name = employee_name
	emp.department = department
	emp.designation = designation
	emp.phone = phone
	emp.status = status
	emp.save(ignore_permissions=True)

	# Sync status with User enabled field
	if frappe.db.exists("User", email):
		user_doc = frappe.get_doc("User", email)
		user_doc.first_name = employee_name
		user_doc.enabled = 1 if status == "Active" else 0
		user_doc.save(ignore_permissions=True)

	frappe.db.commit()
	return emp.as_dict()

@frappe.whitelist()
def delete_employee(email):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can delete employees."), frappe.PermissionError)
		
	if frappe.db.exists("User", email):
		user_doc = frappe.get_doc("User", email)
		user_doc.enabled = 0
		user_doc.save(ignore_permissions=True)

	frappe.delete_doc("Expense Employee", email, ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}

@frappe.whitelist()
def get_reports(status=None, category=None, employee=None, date=None):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can view analytics reports."), frappe.PermissionError)

	conditions = ["1=1"]
	params = []

	if category and category != "All":
		conditions.append("category = %s")
		params.append(category)

	if employee:
		conditions.append("submitted_by = %s")
		params.append(employee)

	if date:
		conditions.append("bill_date = %s")
		params.append(date)

	where_clause = " AND ".join(conditions)

	conditions_gross = list(conditions)
	params_gross = list(params)
	if status and status != "All":
		conditions_gross.append("status = %s")
		params_gross.append(status)
	where_clause_gross = " AND ".join(conditions_gross)

	# 1. Monthly Expense Trend (all status vs approved)
	monthly_trend = frappe.db.sql(f"""
		SELECT 
			DATE_FORMAT(bill_date, '%%Y-%%m') as month,
			SUM(CASE WHEN status = 'Approved' THEN amount ELSE 0 END) as approved,
			SUM(amount) as total
		FROM `tabExpense Bill`
		WHERE {where_clause_gross}
		GROUP BY month
		ORDER BY month DESC
		LIMIT 12
	""", tuple(params_gross), as_dict=True)

	# 2. Category Distribution
	category_dist = frappe.db.sql(f"""
		SELECT 
			category, 
			SUM(amount) as total,
			COUNT(name) as count
		FROM `tabExpense Bill`
		WHERE {where_clause_gross}
		GROUP BY category
	""", tuple(params_gross), as_dict=True)

	# 3. Employee Submissions
	employee_stats = frappe.db.sql(f"""
		SELECT 
			submitted_by,
			SUM(CASE WHEN status = 'Approved' THEN amount ELSE 0 END) as approved,
			SUM(amount) as total,
			COUNT(name) as count
		FROM `tabExpense Bill`
		WHERE {where_clause_gross}
		GROUP BY submitted_by
		ORDER BY total DESC
	""", tuple(params_gross), as_dict=True)

	for stat in employee_stats:
		stat["employee_name"] = frappe.db.get_value("User", stat.submitted_by, "full_name") or stat.submitted_by

	return {
		"monthly_trend": monthly_trend,
		"category_dist": category_dist,
		"employee_stats": employee_stats
	}

@frappe.whitelist()
def get_settings():
	check_auth()
	user = frappe.session.user
	
	# Fetch user record
	user_doc = frappe.get_doc("User", user)
	
	# Fetch employee record
	emp_details = {}
	if frappe.db.exists("Expense Employee", user):
		emp_doc = frappe.get_doc("Expense Employee", user)
		emp_details = {
			"department": emp_doc.department,
			"designation": emp_doc.designation,
			"phone": emp_doc.phone,
			"status": emp_doc.status
		}
	else:
		emp_details = {
			"department": "",
			"designation": "Administrator" if is_admin(user) else "Employee",
			"phone": "",
			"status": "Active"
		}

	# Load global portal settings for wizard
	global_settings = {
		"company_name": "BizAxl Inc.",
		"tax_id": "",
		"currency": "USD",
		"fiscal_year_start": today(),
		"billing_address": "",
		"city": "",
		"country": "",
		"postal_code": "",
		"theme_color": "Navy",
		"logo_url": "",
		"brand_tagline": "Modern Enterprise Solutions",
		"max_claim_amount": 1000,
		"require_receipt_limit": 50,
		"auto_approval": False,
		"multi_currency": False
	}

	if is_admin(user):
		global_settings_raw = frappe.db.get_default("expense_portal_settings")
		if global_settings_raw:
			try:
				loaded = json.loads(global_settings_raw)
				global_settings.update(loaded)
			except Exception:
				pass

	return {
		"email": user,
		"full_name": user_doc.full_name,
		"user_image": user_doc.user_image,
		"is_admin": is_admin(user),
		"employee_details": emp_details,
		"global_settings": global_settings
	}

@frappe.whitelist()
def save_settings(full_name=None, phone=None, department=None, designation=None, password=None, user_image=None, global_settings=None):
	check_auth()
	user = frappe.session.user
	
	# Update user info
	user_doc = frappe.get_doc("User", user)
	if full_name:
		user_doc.first_name = full_name
		user_doc.last_name = ""
	if user_image:
		user_doc.user_image = user_image
	if password:
		user_doc.new_password = password
	user_doc.save(ignore_permissions=True)

	# Update employee details if they exist
	if frappe.db.exists("Expense Employee", user):
		emp_doc = frappe.get_doc("Expense Employee", user)
		if full_name: emp_doc.employee_name = full_name
		if phone is not None: emp_doc.phone = phone
		if department is not None: emp_doc.department = department
		if designation is not None: emp_doc.designation = designation
		emp_doc.save(ignore_permissions=True)

	# Save global portal wizard settings if admin and provided
	if global_settings and is_admin(user):
		if isinstance(global_settings, str):
			try:
				global_settings = json.loads(global_settings)
			except Exception:
				pass
		frappe.db.set_default("expense_portal_settings", json.dumps(global_settings))

	frappe.db.commit()
	return {"status": "success"}

@frappe.whitelist()
def activate_employee(email):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can modify employee status."), frappe.PermissionError)
	if frappe.db.exists("Expense Employee", email):
		emp = frappe.get_doc("Expense Employee", email)
		emp.status = "Active"
		emp.save(ignore_permissions=True)
	if frappe.db.exists("User", email):
		user_doc = frappe.get_doc("User", email)
		user_doc.enabled = 1
		user_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}

@frappe.whitelist()
def deactivate_employee(email):
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can modify employee status."), frappe.PermissionError)
	if frappe.db.exists("Expense Employee", email):
		emp = frappe.get_doc("Expense Employee", email)
		emp.status = "Inactive"
		emp.save(ignore_permissions=True)
	if frappe.db.exists("User", email):
		user_doc = frappe.get_doc("User", email)
		user_doc.enabled = 0
		user_doc.save(ignore_permissions=True)
	frappe.db.commit()
	return {"status": "success"}

# --- SYSTEM SETUP & SAMPLE DATA GENERATOR ---

@frappe.whitelist()
def setup_project():
	"""
	Automatically creates required Roles, assigns them, creates sample users, 
	generates Expense Employee records, and builds 20 realistic sample bills.
	"""
	# 1. Create Roles
	for role_name in ["Expense Admin", "Expense Employee"]:
		if not frappe.db.exists("Role", role_name):
			role = frappe.get_doc({
				"doctype": "Role",
				"role_name": role_name
			})
			role.insert(ignore_permissions=True)
			
	# 2. Assign Expense Admin to Administrator
	admin_user = frappe.get_doc("User", "Administrator")
	admin_user.add_roles("Expense Admin")
	
	# 3. Create Sample Employees
	sample_employees = [
		{"email": "john@company.com", "name": "John Doe", "dept": "Sales", "desig": "Sales Executive", "phone": "+1-555-0199"},
		{"email": "priya@company.com", "name": "Priya Sharma", "dept": "Engineering", "desig": "Senior Engineer", "phone": "+91-98765-43210"},
		{"email": "rahul@company.com", "name": "Rahul Verma", "dept": "Marketing", "desig": "Marketing Specialist", "phone": "+91-98100-12345"},
		{"email": "ananya@company.com", "name": "Ananya Sen", "dept": "Human Resources", "desig": "HR Manager", "phone": "+91-99999-88888"},
		{"email": "arjun@company.com", "name": "Arjun Nair", "dept": "Finance", "desig": "Financial Analyst", "phone": "+91-88888-77777"}
	]
	
	for emp in sample_employees:
		# Check if User exists
		if not frappe.db.exists("User", emp["email"]):
			user = frappe.get_doc({
				"doctype": "User",
				"email": emp["email"],
				"first_name": emp["name"],
				"send_welcome_email": 0,
				"enabled": 1,
				"user_type": "System User"
			})
			user.insert(ignore_permissions=True)
			user.new_password = "ExpenseTracker2026!"
			user.save(ignore_permissions=True)
		else:
			user = frappe.get_doc("User", emp["email"])
			user.enabled = 1
			user.save(ignore_permissions=True)
			
		user.add_roles("Expense Employee")
		
		# Create/Sync Expense Employee doc
		if not frappe.db.exists("Expense Employee", emp["email"]):
			emp_doc = frappe.get_doc({
				"doctype": "Expense Employee",
				"user": emp["email"],
				"employee_name": emp["name"],
				"email": emp["email"],
				"department": emp["dept"],
				"designation": emp["desig"],
				"phone": emp["phone"],
				"status": "Active"
			})
			emp_doc.insert(ignore_permissions=True)
		else:
			emp_doc = frappe.get_doc("Expense Employee", emp["email"])
			emp_doc.employee_name = emp["name"]
			emp_doc.department = emp["dept"]
			emp_doc.designation = emp["desig"]
			emp_doc.phone = emp["phone"]
			emp_doc.status = "Active"
			emp_doc.save(ignore_permissions=True)

	# 4. Generate 20 Sample Bills
	categories = ["Travel", "Food", "Office", "Medical", "Internet", "Training", "Other"]
	statuses = ["Pending", "Approved", "Rejected"]
	
	titles = {
		"Travel": ["Client Meeting Uber", "Flight to Chicago Conference", "Airport Taxi Fare", "Hotel Stay - Annual Summit"],
		"Food": ["Team Dinner - Project Kickoff", "Lunch with Client", "Coffee with Candidate", "Late Night Office Snacks"],
		"Office": ["Mechanical Keyboard", "Whiteboard Markers and Notepads", "Ergonomic Desk Chair", "Dual Monitor Stand"],
		"Medical": ["Annual Eye Checkup Reimbursement", "First Aid Kit Refills", "Prescription Medicine Cover", "Wellness Program Pass"],
		"Internet": ["Monthly Home Broadband WiFi", "Mobile Data Roaming Pack", "WiFi Router Upgrade", "Co-working Space Daypass"],
		"Training": ["Vue.js 3 Advanced Course", "AWS Certified Solutions Architect Exam", "Agile Product Management Book", "React Native Masterclass"],
		"Other": ["Software Subscription - Slack Pro", "Software Subscription - Github Copilot", "Courier Service Charges", "Business Cards Printing"]
	}

	descriptions = {
		"Travel": "Travel expenses incurred for official work, client visits, or conference attendance.",
		"Food": "Meals and catering for company events or client consultations.",
		"Office": "Consumables, devices, and office ergonomics related support.",
		"Medical": "Medical cover and wellness benefit program claims.",
		"Internet": "Remote worker internet connectivity and mobile allowances.",
		"Training": "Professional growth, certifications, online courses, and guides.",
		"Other": "Miscellaneous expenses like software tools, printing, shipping."
	}
	
	# Delete existing bills first to ensure a clean run of 20 bills
	frappe.db.delete("Expense Bill")
	
	emails = [emp["email"] for emp in sample_employees]
	
	for i in range(20):
		category = random.choice(categories)
		title = random.choice(titles[category])
		desc = descriptions[category]
		amount = round(random.uniform(15.0, 850.0), 2)
		submitted_by = random.choice(emails)
		status = random.choice(statuses)
		
		# Dates spread out over the last 60 days
		bill_date = add_days(today(), -random.randint(1, 60))
		
		remarks = ""
		if status == "Approved":
			remarks = "Verified and approved. Releasing payment."
		elif status == "Rejected":
			remarks = "Receipt not attached clearly or exceeds budget limits."
			
		bill = frappe.get_doc({
			"doctype": "Expense Bill",
			"bill_title": f"{title} #{i+1}",
			"amount": amount,
			"category": category,
			"bill_date": bill_date,
			"description": f"{desc} Bill submitted for review.",
			"submitted_by": submitted_by,
			"status": status,
			"remarks": remarks
		})
		bill.insert(ignore_permissions=True)
		
	frappe.db.commit()
	return {"status": "success", "message": "Successfully set up roles, users, and 20 sample bills."}

@frappe.whitelist()
def clear_sample_data():
	"""
	Deletes all sample/fake bills generated by setup_project (those with '#' in their title).
	Keeps all real user-created bills.
	"""
	check_auth()
	if not is_admin():
		frappe.throw(_("Access Denied. Only Admins can clear sample data."), frappe.PermissionError)

	# Sample bills have "#<number>" appended to title by setup_project
	sample_bills = frappe.db.sql("""
		SELECT name FROM `tabExpense Bill`
		WHERE bill_title REGEXP ' #[0-9]+$'
	""", as_dict=True)

	count = 0
	for b in sample_bills:
		frappe.delete_doc("Expense Bill", b.name, ignore_permissions=True)
		count += 1

	frappe.db.commit()
	return {"status": "success", "message": f"Deleted {count} sample bills. Real bills are preserved."}

def get_portal_context(context):
	# If not logged in, redirect to login page
	if frappe.session.user == "Guest":
		redirect_url = "/login"
		if hasattr(frappe.local, "request") and frappe.local.request:
			redirect_url += f"?redirect-to={frappe.local.request.path}"
		frappe.local.flags.redirect_location = redirect_url
		raise frappe.Redirect
		
	roles = frappe.get_roles(frappe.session.user)
	is_admin_user = "Expense Admin" in roles or "System Manager" in roles or frappe.session.user == "Administrator"
	is_employee_user = "Expense Employee" in roles

	# Check if user has unauthorized roles
	if not is_admin_user and not is_employee_user:
		context.unauthorized = True
	else:
		context.unauthorized = False

	# Basic user context to boot the Vue app
	context.user_email = frappe.session.user
	context.user_full_name = frappe.db.get_value("User", frappe.session.user, "full_name") or frappe.session.user
	context.is_admin = is_admin_user
	context.is_employee = is_employee_user
