# NCL Industries Limited – Employee Management System (EMS)

> **“Empowering People. Enhancing Performance.”**

---

## 🏢 About NCL Industries Limited EMS
Official comprehensive Employee Management System engineered for **NCL Industries Limited** (Estd. 1979) to govern workforce operations across industrial divisions:
- **Cement Works** (Nagarjuna Cement)
- **Boards Division** (Bison Panel - Cement Bonded Particle Boards)
- **Prefab Structural Systems**
- **Doors & Windows**
- **Corporate Headquarters & Energy**

---

## 🎨 Corporate Theme & Branding Guidelines
- **Corporate Theme**: Premium Industrial Palette
  - **Industrial Red**: `#C8102E` (Primary brand accent and highlights)
  - **Charcoal Black**: `#181C20`, `#111418` (Sidebar, headers, and navigation)
  - **Neutral Gray**: `#374151`, `#4B5563`, `#6B7280`, `#E5E7EB` (Subtext, borders, cards)
  - **Crisp White**: `#FFFFFF`, `#F8FAFC` (Card backgrounds and print surfaces)
- **Branding Badge**: Clean architectural industrial badge with `NCL INDUSTRIES LIMITED` typography and `ESTD. 1979`. Complies with standard guidelines avoiding misrepresentation.
- **Tagline**: *“Empowering People. Enhancing Performance.”*

---

## 🚀 Key Modules & Capabilities

1. **Authentication & Role-Based Access Control**:
   - Multi-role authorization: **Admin**, **HR**, **Manager**, **Employee**.
   - Secure token session authentication and audit logging.

2. **Executive & Plant Dashboards**:
   - Real-time headcount across industrial facilities (Mattampally Plant, Kondapalli Plant, Tirupati, Hyderabad HQ).
   - Biometric/web shift attendance status, pending leave queue, and monthly wage disbursement summary.

3. **Employee Directory**:
   - Master staff records with employee IDs (`NCL-1001` onwards), division, plant site, designations, and contact details.
   - Dynamic search, department filter, and 1-click new employee enrollment.

4. **Biometric & Shift Attendance**:
   - Self Web Clock In / Clock Out with real-time shift verification.
   - Historical shift register, late punch detection, and automated work hour calculations.

5. **Leave Management Workflow**:
   - Leave applications for Casual Leave (CL), Sick Leave (SL), Earned Leave (EL), and Paternity/Maternity.
   - Multi-tier manager and HR review workflow with instant approval/rejection.

6. **Payroll & Official Payslips**:
   - Automated Indian industrial salary structure (Basic 50%, HRA 25%, Conveyance, Special Allowance, EPF 12%, ESI, Professional Tax, TDS).
   - Printable official **NCL Industries Limited Payslips** with Corporate CIN (`L33130TG1979PLC002521`), registered office details, earnings vs. deductions table, and authorized signatory blocks.

7. **Printable Corporate ID Badges**:
   - Industrial standard employee ID cards with lanyard slot, security clearance levels, plant site, blood group, barcode, and division branding.

8. **Performance Appraisals & KPIs**:
   - Periodic review tracking (e.g., FY 2025-26 Q3 / FY 2026-27 Q1) with 5-star rating, percentage KPI scores, strengths, and mentorship remarks.

9. **Corporate Announcements & Safety Circulars**:
   - Plant alerts, ISO 45001 compliance notifications, safety milestones, and company circulars.

10. **Compliance Export Center**:
    - 1-click export of Master Employee Register, Attendance Register, and Payroll Register in official CSV formats.

---

## 🔐 Default Demo Accounts

| Role | Username / ID | Password | Department / Responsibility |
|---|---|---|---|
| **Executive Admin** | `admin` | `admin123` | Executive Management, Corporate Operations |
| **HR Head** | `hr` | `hr123` | Head - Human Capital & Industrial Relations |
| **Plant Manager** | `manager` | `manager123` | General Manager - Mattampally Plant Operations |
| **Employee** | `employee` | `emp123` | Senior Process Control Engineer, Kiln Operations |

*(1-click quick-fill buttons are conveniently available on the login portal).*

---

## 🛠️ How to Run the Application

1. Open PowerShell / Command Prompt in this directory:
   ```cmd
   python server.py
   ```
   *(or double-click `start.bat`)*

2. Open any browser at:
   ```
   http://127.0.0.1:5050
   ```
