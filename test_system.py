"""
Automated End-to-End Verification Suite for NCL Industries Limited EMS
Spins up the HTTP server in a daemon thread and validates all REST endpoints and branding.
"""

import threading
import http.server
import urllib.request
import urllib.parse
import json
import sqlite3
import os
import sys
import time

import database
import server

BASE_URL = "http://127.0.0.1:5050"

def run_e2e_tests():
    print("------------------------------------------------------------")
    print(" Starting NCL Industries Limited EMS E2E Verification Suite")
    print("------------------------------------------------------------")

    # 1. Start Server in background thread
    server_thread = threading.Thread(target=server.run_server, daemon=True)
    server_thread.start()
    time.sleep(1.0) # allow socket bind

    # 2. Test GET / (HTML Page & Branding)
    print("\n1. Testing Frontend HTML and Corporate Branding:")
    req = urllib.request.urlopen(f"{BASE_URL}/")
    assert req.status == 200, f"Root returned {req.status}"
    html = req.read().decode("utf-8")
    assert "NCL Industries Limited" in html, "Branding 'NCL Industries Limited' missing from HTML"
    assert "Employee Management System (EMS)" in html, "Title 'Employee Management System (EMS)' missing"
    assert "Empowering People. Enhancing Performance." in html, "Tagline missing from HTML"
    assert "/assets/favicon.svg" in html, "Favicon link missing"
    assert "/css/style.css" in html, "CSS stylesheet link missing"
    assert "/js/app.js" in html, "JavaScript application link missing"
    print("   [PASS] HTML rendered with correct NCL branding, title, and tagline.")

    # 3. Test Static Assets
    print("\n2. Testing Static Assets:")
    for path in ["/css/style.css", "/js/app.js", "/assets/logo.svg", "/assets/logo-white.svg", "/assets/favicon.svg"]:
        r = urllib.request.urlopen(f"{BASE_URL}{path}")
        assert r.status == 200, f"Asset {path} failed with {r.status}"
        print(f"   [PASS] {path} served successfully ({len(r.read())} bytes)")

    # 4. Test Authentication (Admin Login)
    print("\n3. Testing Corporate Authentication API:")
    login_data = json.dumps({"username": "admin", "password": "admin123"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    assert res.status == 200
    login_json = json.loads(res.read().decode("utf-8"))
    assert login_json.get("success") is True, "Login failed"
    token = login_json["token"]
    user = login_json["user"]
    assert user["role"] == "admin"
    assert user["full_name"] == "Rajendra Prasad Varma"
    assert user["employee_id"] == "NCL-1001"
    print(f"   [PASS] Admin authenticated. Token received for {user['full_name']} (NCL-1001)")

    auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 5. Test Current User Check /api/auth/me
    req = urllib.request.Request(f"{BASE_URL}/api/auth/me", headers=auth_headers)
    res = urllib.request.urlopen(req)
    me_json = json.loads(res.read().decode("utf-8"))
    assert me_json["user"]["username"] == "admin"
    print("   [PASS] /api/auth/me verified successfully")

    # 6. Test Stats Endpoint
    print("\n4. Testing Dashboard Statistics API:")
    req = urllib.request.Request(f"{BASE_URL}/api/stats", headers=auth_headers)
    res = urllib.request.urlopen(req)
    stats = json.loads(res.read().decode("utf-8"))["stats"]
    print(f"   [PASS] Total Employees: {stats['total_employees']}")
    print(f"   [PASS] Present Today: {stats['present_today']}, Pending Leaves: {stats['pending_leaves']}")
    print(f"   [PASS] Monthly Payroll: Rs. {stats['monthly_payroll']}")
    assert stats['total_employees'] >= 9

    # 7. Test Employee Directory
    print("\n5. Testing Employee Directory API:")
    req = urllib.request.Request(f"{BASE_URL}/api/employees", headers=auth_headers)
    employees = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))["employees"]
    assert len(employees) >= 9
    print(f"   [PASS] Fetched {len(employees)} active NCL personnel records")

    # 8. Test Attendance Register
    print("\n6. Testing Attendance Register API:")
    req = urllib.request.Request(f"{BASE_URL}/api/attendance", headers=auth_headers)
    attendance = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))["attendance"]
    assert len(attendance) > 0
    print(f"   [PASS] Retrieved {len(attendance)} historical attendance records")

    # 9. Test Leave Application & Review
    print("\n7. Testing Leave Management Workflow API:")
    # Employee login
    emp_login = json.dumps({"username": "employee", "password": "emp123"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/auth/login", data=emp_login, headers={"Content-Type": "application/json"})
    emp_token = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))["token"]
    emp_headers = {"Authorization": f"Bearer {emp_token}", "Content-Type": "application/json"}

    # Apply leave
    leave_payload = json.dumps({
        "leave_type": "Casual Leave",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "reason": "Plant Engineering Conference"
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/leaves/apply", data=leave_payload, headers=emp_headers)
    leave_res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    assert leave_res.get("success") is True
    print("   [PASS] Leave application submitted by employee")

    # Admin reviews and approves
    req = urllib.request.Request(f"{BASE_URL}/api/leaves", headers=auth_headers)
    leaves_list = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))["leaves"]
    target_leave = [l for l in leaves_list if l["reason"] == "Plant Engineering Conference"][0]
    
    review_payload = json.dumps({"leave_id": target_leave["id"], "status": "Approved"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/leaves/review", data=review_payload, headers=auth_headers)
    rev_res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
    assert rev_res.get("success") is True
    print(f"   [PASS] Leave #{target_leave['id']} approved by Admin")

    # 10. Test Payroll and Salary Slip
    print("\n8. Testing Payroll & Payslip Verification API:")
    req = urllib.request.Request(f"{BASE_URL}/api/payroll", headers=auth_headers)
    payroll_list = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))["payroll"]
    assert len(payroll_list) >= 9
    first_slip = payroll_list[0]
    slip_no = first_slip["slip_number"]
    
    # Fetch detailed payslip
    req = urllib.request.Request(f"{BASE_URL}/api/payroll/slip/{slip_no}", headers=auth_headers)
    slip_data = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))["slip"]
    assert slip_data["slip_number"] == slip_no
    assert slip_data["gross_salary"] > 0
    assert slip_data["net_salary"] > 0
    print(f"   [PASS] Verified Payslip {slip_no} for {slip_data['full_name']}: Gross=Rs.{slip_data['gross_salary']}, Net=Rs.{slip_data['net_salary']}")

    # 11. Test Reports CSV Export
    print("\n9. Testing Compliance CSV Export API:")
    for rep_type in ["employees", "attendance", "payroll"]:
        req = urllib.request.Request(f"{BASE_URL}/api/reports/export?type={rep_type}", headers=auth_headers)
        res = urllib.request.urlopen(req)
        assert res.status == 200
        csv_text = res.read().decode("utf-8")
        assert "NCL Industries Limited" in csv_text, f"NCL header missing from {rep_type} CSV export"
        print(f"   [PASS] CSV export for '{rep_type}' generated with official NCL Industries Limited header")

    # 12. Test Announcements
    print("\n10. Testing Announcements API:")
    req = urllib.request.Request(f"{BASE_URL}/api/announcements", headers=auth_headers)
    announcements = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))["announcements"]
    assert len(announcements) >= 4
    print(f"   [PASS] Verified {len(announcements)} corporate announcements")

    print("\n============================================================")
    print(" ALL 10 TEST SUITES PASSED PERFECTLY WITH ZERO ERRORS!")
    print(" NCL Industries Limited EMS is fully verified and operational.")
    print("============================================================\n")

if __name__ == "__main__":
    run_e2e_tests()
