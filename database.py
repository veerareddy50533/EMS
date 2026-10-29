"""
NCL Industries Limited - Employee Management System (EMS)
Database module and initial seed data
"""

import sqlite3
import hashlib
import os
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "database.sqlite")

def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Users / Employees table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT UNIQUE NOT NULL,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL, -- admin, hr, manager, employee
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        phone TEXT NOT NULL,
        designation TEXT NOT NULL,
        department TEXT NOT NULL,
        division TEXT NOT NULL, -- Cement, Bison Panel, Prefab, Corporate, Energy, Doors & Windows
        location TEXT NOT NULL, -- Hyderabad Corporate Office, Mattampally Plant, Kondapalli Plant, Tirupati Plant
        joining_date TEXT NOT NULL,
        salary REAL NOT NULL,
        bank_account TEXT NOT NULL,
        pan_no TEXT NOT NULL,
        uan_no TEXT NOT NULL,
        status TEXT DEFAULT 'Active', -- Active, On Leave, Resigned, Retired
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Attendance table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        date TEXT NOT NULL,
        check_in TEXT,
        check_out TEXT,
        work_hours REAL DEFAULT 0,
        status TEXT NOT NULL, -- Present, Late, Half Day, Absent, On Leave
        shift TEXT DEFAULT 'General (09:00 - 18:00)',
        remarks TEXT,
        FOREIGN KEY (employee_id) REFERENCES users(employee_id)
    );
    """)

    # Leaves table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS leaves (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        leave_type TEXT NOT NULL, -- Casual Leave, Sick Leave, Earned Leave, Maternity/Paternity
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        total_days INTEGER NOT NULL,
        reason TEXT NOT NULL,
        status TEXT DEFAULT 'Pending', -- Pending, Approved, Rejected
        reviewed_by TEXT,
        reviewed_at TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES users(employee_id)
    );
    """)

    # Payroll table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS payroll (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slip_number TEXT UNIQUE NOT NULL,
        employee_id TEXT NOT NULL,
        month TEXT NOT NULL,
        year INTEGER NOT NULL,
        basic_salary REAL NOT NULL,
        hra REAL NOT NULL,
        conveyance REAL NOT NULL,
        special_allowance REAL NOT NULL,
        gross_salary REAL NOT NULL,
        pf_deduction REAL NOT NULL,
        esi_deduction REAL NOT NULL,
        professional_tax REAL NOT NULL,
        tds_deduction REAL NOT NULL,
        total_deductions REAL NOT NULL,
        net_salary REAL NOT NULL,
        payment_status TEXT DEFAULT 'Paid', -- Paid, Processing, Pending
        payment_date TEXT,
        payment_method TEXT DEFAULT 'Direct Bank Transfer',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES users(employee_id)
    );
    """)

    # Performance reviews table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS performance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id TEXT NOT NULL,
        reviewer_id TEXT NOT NULL,
        review_period TEXT NOT NULL, -- e.g. FY 2025-26 Q3
        rating REAL NOT NULL, -- 1.0 to 5.0
        kpi_score INTEGER NOT NULL, -- percentage 0-100
        strengths TEXT,
        areas_for_improvement TEXT,
        goals_achieved TEXT,
        feedback TEXT,
        status TEXT DEFAULT 'Completed',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES users(employee_id)
    );
    """)

    # Announcements table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS announcements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        target_role TEXT DEFAULT 'All', -- All, Admin, HR, Manager, Employee
        priority TEXT DEFAULT 'Normal', -- Normal, High, Urgent
        author_name TEXT NOT NULL,
        division TEXT DEFAULT 'Corporate',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Audit logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        actor TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        ip_address TEXT DEFAULT '127.0.0.1',
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    conn.commit()

    # Seed initial data if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_data(cursor)
        conn.commit()

    conn.close()

def seed_data(cursor):
    """Seed comprehensive initial data for NCL Industries Limited"""
    pwd_admin = hash_password("admin123")
    pwd_hr = hash_password("hr123")
    pwd_manager = hash_password("manager123")
    pwd_emp = hash_password("emp123")

    employees = [
        # (employee_id, username, password_hash, role, full_name, email, phone, designation, department, division, location, joining_date, salary, bank_account, pan_no, uan_no)
        ("NCL-1001", "admin", pwd_admin, "admin", "Rajendra Prasad Varma", "r.varma@nclind.com", "+91 98490 12001", "Chief Executive Officer & Administrator", "Executive Management", "Corporate", "Hyderabad Corporate Office", "2018-04-01", 320000.0, "HDFC00018429910", "ABCPV9012A", "100984920192"),
        ("NCL-1002", "hr", pwd_hr, "hr", "Sunita Chandrasekhar", "s.chandrasekhar@nclind.com", "+91 98490 12002", "Head - Human Capital & Industrial Relations", "Human Resources", "Corporate", "Hyderabad Corporate Office", "2019-06-15", 185000.0, "ICIC00029381920", "BCKPS4821B", "100984920193"),
        ("NCL-1003", "manager", pwd_manager, "manager", "K. Venkata Ramana", "kv.ramana@nclind.com", "+91 98490 12003", "General Manager - Plant Operations", "Plant Engineering", "Cement (Nagarjuna)", "Mattampally Plant, Nalgonda", "2017-02-10", 195000.0, "SBIN00049281729", "CLKPR3910C", "100984920194"),
        ("NCL-1004", "employee", pwd_emp, "employee", "Arun Kumar Sharma", "a.sharma@nclind.com", "+91 98490 12004", "Senior Process Control Engineer", "Production & Kiln Operations", "Cement (Nagarjuna)", "Mattampally Plant, Nalgonda", "2021-08-01", 95000.0, "AXIS00091823741", "DLKPS1982D", "100984920195"),
        ("NCL-1005", "priya_nair", pwd_emp, "employee", "Priya Nair", "p.nair@nclind.com", "+91 98490 12005", "Quality Assurance Lead - Bison Panels", "Quality Control", "Bison Panel (Particle Board)", "Kondapalli Plant, Vijayawada", "2022-01-17", 88000.0, "HDFC00091820491", "EMKPN2910E", "100984920196"),
        ("NCL-1006", "ramesh_patel", pwd_manager, "manager", "Ramesh Babu Patel", "rb.patel@nclind.com", "+91 98490 12006", "Operations Manager - Building Products", "Prefab & Ready-Mix", "Prefab Systems", "Tirupati Plant", "2018-11-20", 165000.0, "ICIC00038291029", "FPKPR8291F", "100984920197"),
        ("NCL-1007", "deepa_rao", pwd_emp, "employee", "Deepa Mohan Rao", "d.rao@nclind.com", "+91 98490 12007", "Supply Chain & Logistics Specialist", "Supply Chain", "Corporate", "Hyderabad Corporate Office", "2023-03-01", 78000.0, "SBIN00082739182", "GMKPS9281G", "100984920198"),
        ("NCL-1008", "vikram_reddy", pwd_emp, "employee", "Vikram Reddy", "v.reddy@nclind.com", "+91 98490 12008", "Industrial Safety & EHS Officer", "Health, Safety & Environment", "Cement (Nagarjuna)", "Mattampally Plant, Nalgonda", "2020-10-12", 82000.0, "KOTK00019283746", "HMKPV1928H", "100984920199"),
        ("NCL-1009", "anita_deshmukh", pwd_hr, "hr", "Anita Deshmukh", "a.deshmukh@nclind.com", "+91 98490 12009", "Senior HR Specialist - Talent Acquisition", "Human Resources", "Corporate", "Hyderabad Corporate Office", "2022-07-05", 85000.0, "HDFC00049281029", "IMKPD3928I", "100984920200")
    ]

    cursor.executemany("""
    INSERT INTO users (employee_id, username, password_hash, role, full_name, email, phone, designation, department, division, location, joining_date, salary, bank_account, pan_no, uan_no)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, employees)

    # Seed Announcements
    announcements = [
        ("NCL Industries Limited - FY 2026-27 Strategic Safety & Production Milestone", 
         "All division plant heads and personnel across Nagarjuna Cement and Bison Panel units are commended for achieving 1.2M Safe Man-Hours without LTI. Strict adherence to ISO 45001 safety protocols remains paramount.", 
         "All", "High", "Sunita Chandrasekhar (Head - HR)", "Corporate"),
        
        ("Bison Panel Division - Modernization & Capacity Expansion", 
         "Installation of high-speed cement bonded particle board pressing machinery at our Kondapalli plant is scheduled. Work crews will follow specialized shift schedules during commissioning.", 
         "Employee", "Normal", "K. Venkata Ramana (GM Plant)", "Bison Panel"),

        ("Annual Performance Appraisal & Increments Cycle FY 2025-26", 
         "The Annual Performance Appraisal window is now open in NCL EMS. All Reporting Managers are requested to finalize quarterly KPI scores and feedback before the 15th.", 
         "Manager", "Urgent", "Sunita Chandrasekhar (Head - HR)", "Corporate"),

        ("NCL Nagarjuna Cement - Quality Benchmarking Award 2026", 
         "NCL Industries Limited has been recognized with the National Industrial Excellence Award for OPC 53 Grade high-durability cement formulations.", 
         "All", "Normal", "Rajendra Prasad Varma (CEO)", "Cement (Nagarjuna)")
    ]

    cursor.executemany("""
    INSERT INTO announcements (title, content, target_role, priority, author_name, division)
    VALUES (?, ?, ?, ?, ?, ?)
    """, announcements)

    # Seed Attendance for past 7 days for employees
    today = datetime.now()
    emp_ids = ["NCL-1001", "NCL-1002", "NCL-1003", "NCL-1004", "NCL-1005", "NCL-1006", "NCL-1007", "NCL-1008", "NCL-1009"]
    
    attendance_records = []
    for days_back in range(7, -1, -1):
        target_date = today - timedelta(days=days_back)
        date_str = target_date.strftime("%Y-%m-%d")
        day_of_week = target_date.weekday()
        if day_of_week == 6:  # Skip Sunday as industrial weekly off
            continue
        
        for eid in emp_ids:
            if days_back == 0:
                # Today: partially checked in
                if eid in ["NCL-1001", "NCL-1002", "NCL-1003", "NCL-1004", "NCL-1005", "NCL-1008"]:
                    attendance_records.append((eid, date_str, "08:55", None, 5.5, "Present", "General (09:00 - 18:00)", "On-Duty Plant / Office"))
                elif eid == "NCL-1007":
                    attendance_records.append((eid, date_str, "09:35", None, 4.8, "Late", "General (09:00 - 18:00)", "Traffic Delay - Approved"))
                else:
                    attendance_records.append((eid, date_str, None, None, 0.0, "On Leave", "General (09:00 - 18:00)", "Approved Leave"))
            else:
                if eid == "NCL-1004" and days_back == 3:
                    attendance_records.append((eid, date_str, "09:02", "13:30", 4.5, "Half Day", "First Half (09:00 - 13:30)", "Doctor Appointment"))
                elif eid == "NCL-1009" and days_back == 2:
                    attendance_records.append((eid, date_str, None, None, 0.0, "Absent", "General (09:00 - 18:00)", "Casual Leave"))
                else:
                    attendance_records.append((eid, date_str, "08:52", "18:15", 9.2, "Present", "General (09:00 - 18:00)", "Regular Shift Completed"))

    cursor.executemany("""
    INSERT INTO attendance (employee_id, date, check_in, check_out, work_hours, status, shift, remarks)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, attendance_records)

    # Seed Leaves
    leaves = [
        ("NCL-1004", "Casual Leave", (today + timedelta(days=5)).strftime("%Y-%m-%d"), (today + timedelta(days=6)).strftime("%Y-%m-%d"), 2, "Family function in Vijayawada", "Pending", None, None),
        ("NCL-1005", "Earned Leave", (today - timedelta(days=12)).strftime("%Y-%m-%d"), (today - timedelta(days=8)).strftime("%Y-%m-%d"), 5, "Annual home leave", "Approved", "K. Venkata Ramana", (today - timedelta(days=14)).strftime("%Y-%m-%d")),
        ("NCL-1007", "Sick Leave", (today - timedelta(days=4)).strftime("%Y-%m-%d"), (today - timedelta(days=3)).strftime("%Y-%m-%d"), 2, "Viral fever and physician recommended rest", "Approved", "Sunita Chandrasekhar", (today - timedelta(days=4)).strftime("%Y-%m-%d")),
        ("NCL-1008", "Casual Leave", (today + timedelta(days=10)).strftime("%Y-%m-%d"), (today + timedelta(days=11)).strftime("%Y-%m-%d"), 2, "Personal domestic work", "Pending", None, None)
    ]
    cursor.executemany("""
    INSERT INTO leaves (employee_id, leave_type, start_date, end_date, total_days, reason, status, reviewed_by, reviewed_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, leaves)

    # Seed Payroll
    # Calculate realistic industrial Indian payslips with PF, ESI, Tax
    payroll_data = [
        ("NCL-1001", "October", 2026, 160000.0, 80000.0, 20000.0, 60000.0, 320000.0, 19200.0, 0.0, 2500.0, 48000.0, 69700.0, 250300.0, "NCL-PAY-202610-001"),
        ("NCL-1002", "October", 2026, 92500.0, 46250.0, 16000.0, 30250.0, 185000.0, 11100.0, 0.0, 2500.0, 24500.0, 38100.0, 146900.0, "NCL-PAY-202610-002"),
        ("NCL-1003", "October", 2026, 97500.0, 48750.0, 18000.0, 30750.0, 195000.0, 11700.0, 0.0, 2500.0, 26000.0, 40200.0, 154800.0, "NCL-PAY-202610-003"),
        ("NCL-1004", "October", 2026, 47500.0, 23750.0, 8000.0, 15750.0, 95000.0, 5700.0, 712.5, 2500.0, 7500.0, 16412.5, 78587.5, "NCL-PAY-202610-004"),
        ("NCL-1005", "October", 2026, 44000.0, 22000.0, 7500.0, 14500.0, 88000.0, 5280.0, 660.0, 2500.0, 6800.0, 15240.0, 72760.0, "NCL-PAY-202610-005"),
        ("NCL-1006", "October", 2026, 82500.0, 41250.0, 14000.0, 27250.0, 165000.0, 9900.0, 0.0, 2500.0, 21000.0, 33400.0, 131600.0, "NCL-PAY-202610-006"),
        ("NCL-1007", "October", 2026, 39000.0, 19500.0, 6500.0, 13000.0, 78000.0, 4680.0, 585.0, 2500.0, 5200.0, 12965.0, 65035.0, "NCL-PAY-202610-007"),
        ("NCL-1008", "October", 2026, 41000.0, 20500.0, 7000.0, 13500.0, 82000.0, 4920.0, 615.0, 2500.0, 5800.0, 13835.0, 68165.0, "NCL-PAY-202610-008"),
        ("NCL-1009", "October", 2026, 42500.0, 21250.0, 7000.0, 14250.0, 85000.0, 5100.0, 637.5, 2500.0, 6200.0, 14437.5, 70562.5, "NCL-PAY-202610-009")
    ]
    cursor.executemany("""
    INSERT INTO payroll (employee_id, month, year, basic_salary, hra, conveyance, special_allowance, gross_salary, pf_deduction, esi_deduction, professional_tax, tds_deduction, total_deductions, net_salary, slip_number, payment_date)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2026-10-31')
    """, payroll_data)

    # Seed Performance Reviews
    reviews = [
        ("NCL-1004", "NCL-1003", "FY 2025-26 Q3", 4.8, 96, "Exceptional process optimization at Kiln-3, reducing thermal energy consumption by 4.2%.", "Can mentor junior field apprentices in SCADA automated telemetry.", "Exceeded clinker production target with zero safety violations.", "Outstanding contributor to Nagarjuna Cement operations."),
        ("NCL-1005", "NCL-1006", "FY 2025-26 Q3", 4.6, 92, "High precision in Bison panel tensile strength and moisture-resistance testing.", "Lead time on certified test report approvals can be further accelerated.", "Maintained 99.8% compliance across ASTM & BIS standards for precast panels.", "Reliable quality gatekeeper for building products division."),
        ("NCL-1007", "NCL-1002", "FY 2025-26 Q3", 4.4, 88, "Streamlined outbound freight dispatch routes, optimizing fleet turnaround time by 14%.", "Enhance automated vendor dispatch tracking integration.", "Consistently met bulk cement delivery timelines across southern states.", "Valuable logistics coordinator at corporate HQ.")
    ]
    cursor.executemany("""
    INSERT INTO performance (employee_id, reviewer_id, review_period, rating, kpi_score, strengths, areas_for_improvement, goals_achieved, feedback)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, reviews)

    # Seed initial audit log
    cursor.execute("""
    INSERT INTO audit_logs (actor, action, details)
    VALUES ('System Initializer', 'DATABASE_INIT', 'NCL Industries Limited EMS initialized with standard corporate configuration and department matrices.')
    """)

if __name__ == "__main__":
    init_db()
    print("NCL Industries Limited EMS database successfully initialized and seeded.")
