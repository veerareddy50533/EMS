"""
NCL Industries Limited - Employee Management System (EMS)
High-performance REST API and Static File Server
Zero external dependencies (Python 3 standard library only)
"""

import http.server
import urllib.parse
import json
import os
import sqlite3
import secrets
import mimetypes
from datetime import datetime, timedelta
import database

PORT = 5050
HOST = "127.0.0.1"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# In-memory active sessions: token -> user dict
SESSIONS = {}

def get_db():
    return database.get_db()

class NCLRequestHandler(http.server.BaseHTTPRequestHandler):
    server_version = "NCL-EMS-Server/1.0"
    sys_version = ""

    def log_message(self, format, *args):
        # Clean custom logger
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {self.command} {self.path} - {args[0] if args else ''}")

    def send_json(self, data, status=200):
        body = json.dumps(data, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message, status=400):
        self.send_json({"success": False, "error": message}, status=status)

    def read_json_body(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            raw = self.rfile.read(content_length).decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            return None

    def get_auth_user(self):
        auth_header = self.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        else:
            # Check cookie
            cookies = self.headers.get("Cookie", "")
            for c in cookies.split(";"):
                if "ncl_token=" in c:
                    token = c.split("ncl_token=")[1].strip()
        
        if token and token in SESSIONS:
            return SESSIONS[token]
        return None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API Routes
        if path.startswith("/api/"):
            self.handle_api_get(path, query)
            return

        # Static file handling
        self.handle_static_file(path)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api_post(path, query)
            return

        self.send_error_json("Invalid POST endpoint", 404)

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api_put(path, query)
            return

        self.send_error_json("Invalid PUT endpoint", 404)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path.startswith("/api/"):
            self.handle_api_delete(path, query)
            return

        self.send_error_json("Invalid DELETE endpoint", 404)

    # ---------------- API GET ROUTES ----------------
    def handle_api_get(self, path, query):
        user = self.get_auth_user()

        # Public or auth check
        if path == "/api/auth/me":
            if user:
                self.send_json({"success": True, "user": user})
            else:
                self.send_error_json("Not authenticated", 401)
            return

        if not user:
            self.send_error_json("Authentication required for this resource", 401)
            return

        conn = get_db()
        cursor = conn.cursor()

        try:
            if path == "/api/stats":
                # Overview statistics
                cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'Active'")
                total_employees = cursor.fetchone()[0]

                today_str = datetime.now().strftime("%Y-%m-%d")
                cursor.execute("SELECT status, COUNT(*) FROM attendance WHERE date = ? GROUP BY status", (today_str,))
                att_stats = {row[0]: row[1] for row in cursor.fetchall()}

                cursor.execute("SELECT COUNT(*) FROM leaves WHERE status = 'Pending'")
                pending_leaves = cursor.fetchone()[0]

                cursor.execute("SELECT SUM(net_salary) FROM payroll WHERE month = 'October' AND year = 2026")
                monthly_payroll = cursor.fetchone()[0] or 0.0

                cursor.execute("SELECT AVG(rating), AVG(kpi_score) FROM performance")
                perf_row = cursor.fetchone()
                avg_rating = round(perf_row[0] or 0, 1)
                avg_kpi = round(perf_row[1] or 0, 1)

                # Division counts
                cursor.execute("SELECT division, COUNT(*) FROM users WHERE status = 'Active' GROUP BY division")
                divisions = [{"division": row[0], "count": row[1]} for row in cursor.fetchall()]

                # Department counts
                cursor.execute("SELECT department, COUNT(*) FROM users WHERE status = 'Active' GROUP BY department")
                departments = [{"department": row[0], "count": row[1]} for row in cursor.fetchall()]

                self.send_json({
                    "success": True,
                    "stats": {
                        "total_employees": total_employees,
                        "present_today": att_stats.get("Present", 0),
                        "late_today": att_stats.get("Late", 0),
                        "on_leave_today": att_stats.get("On Leave", 0),
                        "absent_today": att_stats.get("Absent", 0),
                        "half_day_today": att_stats.get("Half Day", 0),
                        "pending_leaves": pending_leaves,
                        "monthly_payroll": monthly_payroll,
                        "avg_rating": avg_rating,
                        "avg_kpi": avg_kpi,
                        "divisions": divisions,
                        "departments": departments
                    }
                })

            elif path == "/api/employees":
                # Filterable employee list
                dept_filter = query.get("department", [None])[0]
                div_filter = query.get("division", [None])[0]
                search = query.get("q", [None])[0]

                sql = "SELECT id, employee_id, username, role, full_name, email, phone, designation, department, division, location, joining_date, salary, status FROM users WHERE 1=1"
                params = []
                if dept_filter:
                    sql += " AND department = ?"
                    params.append(dept_filter)
                if div_filter:
                    sql += " AND division = ?"
                    params.append(div_filter)
                if search:
                    sql += " AND (full_name LIKE ? OR employee_id LIKE ? OR email LIKE ? OR designation LIKE ?)"
                    wildcard = f"%{search}%"
                    params.extend([wildcard, wildcard, wildcard, wildcard])

                sql += " ORDER BY employee_id ASC"
                cursor.execute(sql, params)
                employees = [dict(row) for row in cursor.fetchall()]
                self.send_json({"success": True, "employees": employees})

            elif path.startswith("/api/employees/"):
                emp_id = path.split("/")[-1]
                cursor.execute("SELECT * FROM users WHERE employee_id = ? OR id = ?", (emp_id, emp_id))
                emp = cursor.fetchone()
                if emp:
                    emp_dict = dict(emp)
                    del emp_dict["password_hash"]
                    self.send_json({"success": True, "employee": emp_dict})
                else:
                    self.send_error_json("Employee not found", 404)

            elif path == "/api/attendance":
                date_filter = query.get("date", [None])[0]
                emp_filter = query.get("employee_id", [None])[0]

                # Employees only see their own attendance unless manager/hr/admin
                if user["role"] == "employee":
                    emp_filter = user["employee_id"]

                sql = """
                SELECT a.*, u.full_name, u.designation, u.division, u.department 
                FROM attendance a
                JOIN users u ON a.employee_id = u.employee_id
                WHERE 1=1
                """
                params = []
                if date_filter:
                    sql += " AND a.date = ?"
                    params.append(date_filter)
                if emp_filter:
                    sql += " AND a.employee_id = ?"
                    params.append(emp_filter)

                sql += " ORDER BY a.date DESC, a.check_in ASC LIMIT 100"
                cursor.execute(sql, params)
                records = [dict(row) for row in cursor.fetchall()]
                self.send_json({"success": True, "attendance": records})

            elif path == "/api/leaves":
                emp_filter = query.get("employee_id", [None])[0]
                if user["role"] == "employee":
                    emp_filter = user["employee_id"]

                sql = """
                SELECT l.*, u.full_name, u.designation, u.department, u.division
                FROM leaves l
                JOIN users u ON l.employee_id = u.employee_id
                WHERE 1=1
                """
                params = []
                if emp_filter:
                    sql += " AND l.employee_id = ?"
                    params.append(emp_filter)

                sql += " ORDER BY l.created_at DESC"
                cursor.execute(sql, params)
                leaves = [dict(row) for row in cursor.fetchall()]
                self.send_json({"success": True, "leaves": leaves})

            elif path == "/api/payroll":
                emp_filter = query.get("employee_id", [None])[0]
                if user["role"] == "employee":
                    emp_filter = user["employee_id"]

                sql = """
                SELECT p.*, u.full_name, u.designation, u.department, u.division, u.location, u.pan_no, u.uan_no, u.bank_account
                FROM payroll p
                JOIN users u ON p.employee_id = u.employee_id
                WHERE 1=1
                """
                params = []
                if emp_filter:
                    sql += " AND p.employee_id = ?"
                    params.append(emp_filter)

                sql += " ORDER BY p.year DESC, p.id DESC"
                cursor.execute(sql, params)
                payroll = [dict(row) for row in cursor.fetchall()]
                self.send_json({"success": True, "payroll": payroll})

            elif path.startswith("/api/payroll/slip/"):
                slip_num = path.split("/")[-1]
                sql = """
                SELECT p.*, u.full_name, u.designation, u.department, u.division, u.location, u.pan_no, u.uan_no, u.bank_account, u.joining_date
                FROM payroll p
                JOIN users u ON p.employee_id = u.employee_id
                WHERE p.slip_number = ?
                """
                cursor.execute(sql, (slip_num,))
                row = cursor.fetchone()
                if row:
                    slip = dict(row)
                    self.send_json({"success": True, "slip": slip})
                else:
                    self.send_error_json("Salary slip not found", 404)

            elif path == "/api/performance":
                emp_filter = query.get("employee_id", [None])[0]
                if user["role"] == "employee":
                    emp_filter = user["employee_id"]

                sql = """
                SELECT p.*, u.full_name, u.designation, u.department, u.division,
                       r.full_name AS reviewer_name, r.designation AS reviewer_designation
                FROM performance p
                JOIN users u ON p.employee_id = u.employee_id
                LEFT JOIN users r ON p.reviewer_id = r.employee_id
                WHERE 1=1
                """
                params = []
                if emp_filter:
                    sql += " AND p.employee_id = ?"
                    params.append(emp_filter)

                sql += " ORDER BY p.created_at DESC"
                cursor.execute(sql, params)
                reviews = [dict(row) for row in cursor.fetchall()]
                self.send_json({"success": True, "performance": reviews})

            elif path == "/api/announcements":
                cursor.execute("SELECT * FROM announcements ORDER BY created_at DESC")
                announcements = [dict(row) for row in cursor.fetchall()]
                self.send_json({"success": True, "announcements": announcements})

            elif path == "/api/reports/export":
                # Export CSV format with official NCL Industries Limited Header
                rep_type = query.get("type", ["employees"])[0]
                self.handle_csv_export(cursor, rep_type)

            else:
                self.send_error_json(f"API endpoint '{path}' not found", 404)

        finally:
            conn.close()

    def handle_csv_export(self, cursor, rep_type):
        company_header = "NCL Industries Limited - Employee Management System (EMS)\nReport: "
        if rep_type == "employees":
            company_header += "Master Employee Register\nGenerated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
            cursor.execute("SELECT employee_id, full_name, email, phone, designation, department, division, location, joining_date, salary, status FROM users ORDER BY employee_id")
            rows = cursor.fetchall()
            csv_lines = [company_header, "Employee ID,Full Name,Email,Phone,Designation,Department,Division,Location,Joining Date,Salary (INR),Status\n"]
            for r in rows:
                csv_lines.append(f'"{r[0]}","{r[1]}","{r[2]}","{r[3]}","{r[4]}","{r[5]}","{r[6]}","{r[7]}","{r[8]}",{r[9]},"{r[10]}"\n')
            filename = "NCL_Employee_Master_Register.csv"

        elif rep_type == "attendance":
            company_header += "Attendance & Shift Register\nGenerated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
            cursor.execute("""
            SELECT a.date, a.employee_id, u.full_name, u.department, u.division, a.check_in, a.check_out, a.work_hours, a.status, a.remarks
            FROM attendance a JOIN users u ON a.employee_id = u.employee_id ORDER BY a.date DESC
            """)
            rows = cursor.fetchall()
            csv_lines = [company_header, "Date,Employee ID,Employee Name,Department,Division,Check In,Check Out,Work Hours,Status,Remarks\n"]
            for r in rows:
                c_in = r[5] if r[5] else "-"
                c_out = r[6] if r[6] else "-"
                rem = r[9] if r[9] else ""
                csv_lines.append(f'"{r[0]}","{r[1]}","{r[2]}","{r[3]}","{r[4]}","{c_in}","{c_out}",{r[7]},"{r[8]}","{rem}"\n')
            filename = "NCL_Attendance_Register.csv"

        else: # payroll
            company_header += "Payroll Disbursement Register\nGenerated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n"
            cursor.execute("""
            SELECT p.slip_number, p.employee_id, u.full_name, p.month, p.year, p.gross_salary, p.total_deductions, p.net_salary, p.payment_status, p.payment_date
            FROM payroll p JOIN users u ON p.employee_id = u.employee_id ORDER BY p.year DESC, p.id DESC
            """)
            rows = cursor.fetchall()
            csv_lines = [company_header, "Slip No,Employee ID,Employee Name,Month,Year,Gross Salary (INR),Deductions (INR),Net Salary (INR),Status,Payment Date\n"]
            for r in rows:
                p_date = r[9] if r[9] else ""
                csv_lines.append(f'"{r[0]}","{r[1]}","{r[2]}","{r[3]}",{r[4]},{r[5]},{r[6]},{r[7]},"{r[8]}","{p_date}"\n')
            filename = "NCL_Payroll_Register.csv"

        csv_content = "".join(csv_lines).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/csv; charset=utf-8")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(csv_content)))
        self.end_headers()
        self.wfile.write(csv_content)

    # ---------------- API POST ROUTES ----------------
    def handle_api_post(self, path, query):
        body = self.read_json_body()
        if body is None:
            self.send_error_json("Invalid JSON payload", 400)
            return

        # Auth Login (Public)
        if path == "/api/auth/login":
            username = body.get("username", "").strip()
            password = body.get("password", "").strip()

            if not username or not password:
                self.send_error_json("Username and password are required")
                return

            hashed = database.hash_password(password)
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE (username = ? OR employee_id = ? OR email = ?) AND password_hash = ?", 
                           (username, username, username, hashed))
            user_row = cursor.fetchone()
            
            if user_row:
                user = dict(user_row)
                del user["password_hash"]
                token = secrets.token_hex(24)
                SESSIONS[token] = user
                
                # Audit log
                cursor.execute("INSERT INTO audit_logs (actor, action, details) VALUES (?, ?, ?)",
                               (user["full_name"], "LOGIN_SUCCESS", f"User logged in with role {user['role']}"))
                conn.commit()
                conn.close()

                self.send_response(200)
                body_bytes = json.dumps({"success": True, "token": token, "user": user}).encode("utf-8")
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("Set-Cookie", f"ncl_token={token}; Path=/; HttpOnly; SameSite=Lax")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body_bytes)
            else:
                conn.close()
                self.send_error_json("Invalid credentials. Please verify your employee ID and password.", 401)
            return

        # Requires Auth for remaining POST endpoints
        user = self.get_auth_user()
        if not user:
            self.send_error_json("Authentication required", 401)
            return

        conn = get_db()
        cursor = conn.cursor()

        try:
            if path == "/api/auth/logout":
                # Clear session
                for tok, u in list(SESSIONS.items()):
                    if u["id"] == user["id"]:
                        del SESSIONS[tok]
                self.send_response(200)
                body_bytes = json.dumps({"success": True, "message": "Logged out successfully"}).encode("utf-8")
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body_bytes)))
                self.send_header("Set-Cookie", "ncl_token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT")
                self.end_headers()
                self.wfile.write(body_bytes)
                return

            elif path == "/api/employees":
                # Admin or HR only
                if user["role"] not in ["admin", "hr"]:
                    self.send_error_json("Permission denied: Admin or HR authorization required", 403)
                    return

                # Generate new NCL Employee ID
                cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1")
                last_id = cursor.fetchone()[0]
                emp_id = f"NCL-{1000 + last_id + 1}"

                username = body.get("username", "").strip() or emp_id.lower().replace("-", "")
                password = body.get("password", "ncl@123")
                pwd_hash = database.hash_password(password)

                cursor.execute("""
                INSERT INTO users (employee_id, username, password_hash, role, full_name, email, phone, designation, department, division, location, joining_date, salary, bank_account, pan_no, uan_no)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    emp_id, username, pwd_hash, body.get("role", "employee"),
                    body.get("full_name"), body.get("email"), body.get("phone", "+91 98490 00000"),
                    body.get("designation"), body.get("department"), body.get("division", "Corporate"),
                    body.get("location", "Hyderabad Corporate Office"),
                    body.get("joining_date", datetime.now().strftime("%Y-%m-%d")),
                    float(body.get("salary", 50000.0)),
                    body.get("bank_account", "HDFC0000000000"),
                    body.get("pan_no", "ABCDE1234F"),
                    body.get("uan_no", "100984900000")
                ))
                conn.commit()
                self.send_json({"success": True, "message": f"Employee {emp_id} enrolled successfully in NCL Industries Limited EMS", "employee_id": emp_id})

            elif path == "/api/attendance/clock":
                # Clock In / Clock Out
                action = body.get("action") # 'in' or 'out'
                emp_id = user["employee_id"]
                today_str = datetime.now().strftime("%Y-%m-%d")
                time_str = datetime.now().strftime("%H:%M")

                cursor.execute("SELECT * FROM attendance WHERE employee_id = ? AND date = ?", (emp_id, today_str))
                existing = cursor.fetchone()

                if action == "in":
                    if existing:
                        self.send_error_json("You have already checked in for today.")
                        return
                    
                    status = "Present"
                    # Mark Late if after 09:30 AM
                    hour, minute = datetime.now().hour, datetime.now().minute
                    if hour > 9 or (hour == 9 and minute > 30):
                        status = "Late"

                    cursor.execute("""
                    INSERT INTO attendance (employee_id, date, check_in, status, shift, remarks)
                    VALUES (?, ?, ?, ?, 'General (09:00 - 18:00)', 'Self Web Punch')
                    """, (emp_id, today_str, time_str, status))
                    conn.commit()
                    self.send_json({"success": True, "message": f"Checked in successfully at {time_str}", "status": status})

                elif action == "out":
                    if not existing:
                        self.send_error_json("No check-in record found for today. Please clock in first.")
                        return
                    if existing["check_out"]:
                        self.send_error_json(f"Already checked out today at {existing['check_out']}.")
                        return

                    # Calculate work hours
                    try:
                        ci_time = datetime.strptime(existing["check_in"], "%H:%M")
                        co_time = datetime.strptime(time_str, "%H:%M")
                        delta = (co_time - ci_time).total_seconds() / 3600.0
                        work_hours = round(max(0.1, delta), 2)
                    except Exception:
                        work_hours = 8.0

                    cursor.execute("""
                    UPDATE attendance SET check_out = ?, work_hours = ? WHERE id = ?
                    """, (time_str, work_hours, existing["id"]))
                    conn.commit()
                    self.send_json({"success": True, "message": f"Checked out successfully at {time_str}. Total hours: {work_hours} hrs."})
                else:
                    self.send_error_json("Invalid clock action. Use 'in' or 'out'.")

            elif path == "/api/leaves/apply":
                leave_type = body.get("leave_type")
                start_date = body.get("start_date")
                end_date = body.get("end_date")
                reason = body.get("reason")
                emp_id = user["employee_id"]

                if not all([leave_type, start_date, end_date, reason]):
                    self.send_error_json("All leave details (type, start date, end date, reason) are required.")
                    return

                # Calculate days
                d1 = datetime.strptime(start_date, "%Y-%m-%d")
                d2 = datetime.strptime(end_date, "%Y-%m-%d")
                total_days = max(1, (d2 - d1).days + 1)

                cursor.execute("""
                INSERT INTO leaves (employee_id, leave_type, start_date, end_date, total_days, reason, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Pending')
                """, (emp_id, leave_type, start_date, end_date, total_days, reason))
                conn.commit()
                self.send_json({"success": True, "message": f"Leave application for {total_days} day(s) submitted for approval."})

            elif path == "/api/leaves/review":
                # Manager, HR, Admin only
                if user["role"] not in ["admin", "hr", "manager"]:
                    self.send_error_json("Permission denied: Manager, HR or Admin required", 403)
                    return

                leave_id = body.get("leave_id")
                new_status = body.get("status") # 'Approved' or 'Rejected'

                if not leave_id or new_status not in ["Approved", "Rejected"]:
                    self.send_error_json("Valid leave_id and status (Approved/Rejected) required.")
                    return

                now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
                cursor.execute("""
                UPDATE leaves SET status = ?, reviewed_by = ?, reviewed_at = ? WHERE id = ?
                """, (new_status, user["full_name"], now_str, leave_id))
                conn.commit()
                self.send_json({"success": True, "message": f"Leave application #{leave_id} has been {new_status}."})

            elif path == "/api/payroll/generate":
                # Admin or HR only
                if user["role"] not in ["admin", "hr"]:
                    self.send_error_json("Permission denied: HR or Admin required", 403)
                    return

                month = body.get("month", datetime.now().strftime("%B"))
                year = int(body.get("year", datetime.now().year))

                # Fetch all active employees
                cursor.execute("SELECT employee_id, salary FROM users WHERE status = 'Active'")
                active_users = cursor.fetchall()
                generated_count = 0

                for emp in active_users:
                    eid = emp["employee_id"]
                    gross = float(emp["salary"])

                    # Check if slip already exists
                    cursor.execute("SELECT id FROM payroll WHERE employee_id = ? AND month = ? AND year = ?", (eid, month, year))
                    if cursor.fetchone():
                        continue

                    # Industrial Salary Structure Calculations
                    basic = round(gross * 0.50, 2)
                    hra = round(gross * 0.25, 2)
                    conveyance = round(min(gross * 0.08, 15000), 2)
                    special = round(gross - (basic + hra + conveyance), 2)

                    # Deductions
                    pf = round(min(basic * 0.12, 19200), 2)
                    esi = round(gross * 0.0075 if gross <= 21000 else 0.0, 2)
                    pt = 2500.0 if gross > 20000 else 1500.0
                    tds = round(gross * 0.15 if gross > 150000 else (gross * 0.08 if gross > 75000 else 0.0), 2)
                    total_ded = round(pf + esi + pt + tds, 2)
                    net_pay = round(gross - total_ded, 2)

                    slip_no = f"NCL-PAY-{year}{month[:3].upper()}-{eid.split('-')[-1]}"

                    cursor.execute("""
                    INSERT INTO payroll (slip_number, employee_id, month, year, basic_salary, hra, conveyance, special_allowance, gross_salary, pf_deduction, esi_deduction, professional_tax, tds_deduction, total_deductions, net_salary, payment_status, payment_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Paid', ?)
                    """, (slip_no, eid, month, year, basic, hra, conveyance, special, gross, pf, esi, pt, tds, total_ded, net_pay, datetime.now().strftime("%Y-%m-%d")))
                    generated_count += 1

                conn.commit()
                self.send_json({"success": True, "message": f"Successfully generated {generated_count} payroll record(s) for {month} {year}."})

            elif path == "/api/performance/review":
                if user["role"] not in ["admin", "hr", "manager"]:
                    self.send_error_json("Permission denied: Reviewer rights required", 403)
                    return

                emp_id = body.get("employee_id")
                period = body.get("review_period", "FY 2026-27 Q1")
                rating = float(body.get("rating", 4.0))
                kpi_score = int(body.get("kpi_score", 85))
                strengths = body.get("strengths", "")
                improvements = body.get("areas_for_improvement", "")
                goals = body.get("goals_achieved", "")
                feedback = body.get("feedback", "")

                cursor.execute("""
                INSERT INTO performance (employee_id, reviewer_id, review_period, rating, kpi_score, strengths, areas_for_improvement, goals_achieved, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (emp_id, user["employee_id"], period, rating, kpi_score, strengths, improvements, goals, feedback))
                conn.commit()
                self.send_json({"success": True, "message": "Performance evaluation submitted successfully."})

            elif path == "/api/announcements":
                if user["role"] not in ["admin", "hr"]:
                    self.send_error_json("Permission denied: Admin or HR required", 403)
                    return

                title = body.get("title")
                content = body.get("content")
                priority = body.get("priority", "Normal")
                target = body.get("target_role", "All")
                division = body.get("division", "Corporate")

                cursor.execute("""
                INSERT INTO announcements (title, content, target_role, priority, author_name, division)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (title, content, target, priority, f"{user['full_name']} ({user['designation']})", division))
                conn.commit()
                self.send_json({"success": True, "message": "Official announcement posted across NCL portal."})

            else:
                self.send_error_json(f"POST endpoint '{path}' not found", 404)

        finally:
            conn.close()

    # ---------------- API PUT ROUTES ----------------
    def handle_api_put(self, path, query):
        user = self.get_auth_user()
        if not user:
            self.send_error_json("Authentication required", 401)
            return

        body = self.read_json_body()
        if body is None:
            self.send_error_json("Invalid JSON payload", 400)
            return

        conn = get_db()
        cursor = conn.cursor()

        try:
            if path.startswith("/api/employees/"):
                emp_id = path.split("/")[-1]
                # Admin or HR can edit everything, employee can edit own phone/email
                if user["role"] not in ["admin", "hr"] and user["employee_id"] != emp_id:
                    self.send_error_json("Permission denied", 403)
                    return

                if user["role"] in ["admin", "hr"]:
                    cursor.execute("""
                    UPDATE users SET full_name = ?, email = ?, phone = ?, designation = ?, department = ?, division = ?, location = ?, salary = ?, status = ?
                    WHERE employee_id = ?
                    """, (
                        body.get("full_name"), body.get("email"), body.get("phone"),
                        body.get("designation"), body.get("department"), body.get("division"),
                        body.get("location"), float(body.get("salary", 50000.0)),
                        body.get("status", "Active"), emp_id
                    ))
                else:
                    cursor.execute("""
                    UPDATE users SET phone = ?, email = ? WHERE employee_id = ?
                    """, (body.get("phone"), body.get("email"), emp_id))

                conn.commit()
                self.send_json({"success": True, "message": f"Profile for employee {emp_id} updated successfully."})
            else:
                self.send_error_json(f"PUT endpoint '{path}' not found", 404)
        finally:
            conn.close()

    # ---------------- API DELETE ROUTES ----------------
    def handle_api_delete(self, path, query):
        user = self.get_auth_user()
        if not user or user["role"] not in ["admin", "hr"]:
            self.send_error_json("Admin or HR authorization required", 403)
            return

        conn = get_db()
        cursor = conn.cursor()
        try:
            if path.startswith("/api/announcements/"):
                ann_id = path.split("/")[-1]
                cursor.execute("DELETE FROM announcements WHERE id = ?", (ann_id,))
                conn.commit()
                self.send_json({"success": True, "message": "Announcement removed."})
            elif path.startswith("/api/employees/"):
                emp_id = path.split("/")[-1]
                # Soft delete status
                cursor.execute("UPDATE users SET status = 'Resigned' WHERE employee_id = ?", (emp_id,))
                conn.commit()
                self.send_json({"success": True, "message": f"Employee {emp_id} status updated to Resigned."})
            else:
                self.send_error_json(f"DELETE endpoint '{path}' not found", 404)
        finally:
            conn.close()

    # ---------------- STATIC FILE SERVING ----------------
    def handle_static_file(self, path):
        if path == "/" or path == "":
            path = "/index.html"

        # Sanitize path to prevent directory traversal
        rel_path = path.lstrip("/").replace("/", os.sep)
        full_path = os.path.abspath(os.path.join(PUBLIC_DIR, rel_path))

        if not full_path.startswith(PUBLIC_DIR):
            self.send_error(403, "Forbidden")
            return

        if not os.path.exists(full_path) or os.path.isdir(full_path):
            # Fallback to index.html for SPA routing
            full_path = os.path.join(PUBLIC_DIR, "index.html")

        mime_type, _ = mimetypes.guess_type(full_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        try:
            with open(full_path, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(len(content)))
            # Cache static assets slightly, but keep index.html fresh
            if full_path.endswith("index.html"):
                self.send_header("Cache-Control", "no-cache, must-revalidate")
            else:
                self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f"Error reading static file: {str(e)}")

def run_server():
    database.init_db()
    server_address = (HOST, PORT)
    httpd = http.server.ThreadingHTTPServer(server_address, NCLRequestHandler)
    print(f"======================================================================")
    print(f" NCL Industries Limited – Employee Management System (EMS)")
    print(f" Tagline: Empowering People. Enhancing Performance.")
    print(f" Server running at: http://{HOST}:{PORT}")
    print(f"======================================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down NCL EMS server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
