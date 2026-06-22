# Expense Tracker Portal

A modern, dynamic, and premium-designed **Expense Tracker Portal** built on the Frappe framework. The application provides a sleek light-theme interface for both administrators and employees to manage claims, visualize trends, register active personnel, and track spending categories.

---

## 🚀 Key Features

### 1. Dynamic Dashboard
* **KPI Metrics Grid**: Gross Submitted, Pending Bills, Approved Bills, and Avoided (Rejected) Bills with real-time indicators.
* **Claim History Overview**: An interactive line chart tracking Gross Submitted vs Approved amounts month-over-month.
* **Category Breakdown**: A modern doughnut chart showing category distribution for approved expenses.
* **Live Recent Activity Log**: A dynamic, chronological vertical timeline logging bill submissions, edits, approvals, and rejections in real time.

### 2. Multi-Filter Reports & Analytics
* **Interactive Filtering**: Filter all analytics and data matrices instantly by Category, Status, Employee, or Date.
* **Advanced Chart.js Visualizations**:
  * **Monthly Expense Trend**: Comparative trend lines with smooth curve fills.
  * **Top Categories Contribution**: Doughnut breakdown showing category percentages.
  * **Expense By Category**: Dual-axis bar and line chart mapping category expenses vs claim counts.
  * **Expense By Employee**: Side-by-side grouped bar chart comparing Gross vs Approved amounts per user.
* **Data Export**: Direct CSV downloads for the Employee Expense Contribution table.

### 3. Comprehensive Bills Management
* **Seamless Creation & Updates**: Avoid database rollbacks with whitelisted transaction handling.
* **Drag-and-Drop File Uploads**: Robust attachment handling supporting instant PNG, JPG, and document receipts uploads.
* **Status Updates**: Simple Approve/Reject modal operations for administrators.

### 4. Employee Registry
* **Status Toggles**: Instantly activate or deactivate personnel.
* **Interactive Modals**: Seamlessly create or update employee records directly from the UI.

### 5. Settings & Profile Security
* **Direct Access**: Clean, modern card interface for managing profile details and security credentials.
* **Avatar Upload**: Support for custom user avatars.

---

## 🛠️ Technology Stack
* **Backend**: Frappe (Python)
* **Frontend Logic**: Vue 3 (Reactive CDN setup)
* **Styling**: Tailwind CSS & Custom Modern CSS (vibrant colors, glassmorphism, responsive grids)
* **Charts**: Chart.js (Responsive, interactive tooltip configurations)
* **Icons**: Lucide Icons

---

## ⚙️ Installation & Setup

### 1. Get the App
Add the repository to your local bench workspace:
```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/rishikesh3691/expense-tracker-portal.git --branch develop
bench install-app expense_tracker
```

### 2. Run Database Migration
Sync the custom Doctypes (`Expense Bill` and `Expense Employee`):
```bash
bench migrate
bench clear-cache
```

### 3. Generate Initial Roles & Sample Data
Initialize the system with administrative roles, active users, and realistic sample data by calling the whitelisted setup script:
```bash
bench --site [your-site-name] execute expense_tracker.api.setup_project
```

This creates:
* **Roles**: `Expense Admin` and `Expense Employee`.
* **Roles Assignment**: Grants `Expense Admin` permissions to the `Administrator` user.
* **Sample Employees**: Generates John, Priya, Rahul, Ananya, and Arjun with password `ExpenseTracker2026!`.
* **Sample Bills**: Seeds 20 realistic expense bills across different categories and statuses.

---

## 🔒 Custom Doctypes Included

### 1. Expense Employee
Tracks personnel information:
* `user`: Link to User email
* `employee_name`: Full Name
* `department`: Sales, Engineering, Marketing, HR, Finance, etc.
* `designation`: Corporate title
* `phone`: Contact number
* `status`: Active / Inactive

### 2. Expense Bill
Tracks individual expense claims:
* `bill_title`: Name of the expense
* `amount`: Currency value
* `category`: Travel, Food, Office, Medical, Internet, Training, or Other
* `bill_date`: Posting date
* `submitted_by`: Submitting user email
* `status`: Pending, Approved, or Rejected
* `receipt_image`: URL link to the uploaded receipt attachment
* `remarks`: Additional notes or reason for rejection

---

## 📄 License
This project is licensed under the MIT License.
