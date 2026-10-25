"""Employee Management System - Flask REST API backed by SQLite.

Run:  python app.py          (serves http://localhost:5000)
"""
import os
import re
import sqlite3

from flask import Flask, g, jsonify, request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.environ.get("EMS_DB", os.path.join(BASE_DIR, "..", "data", "ems.db"))
SCHEMA_PATH = os.path.join(BASE_DIR, "..", "database", "schema.sql")
SEED_PATH = os.path.join(BASE_DIR, "..", "database", "seed.sql")

app = Flask(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PHONE_RE = re.compile(r"^\d{10}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
STATUSES = ("Active", "On Leave", "Resigned")


# --------------------------------------------------------------------------
# Database helpers
# --------------------------------------------------------------------------
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        conn.executescript(fh.read())
    empty = conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0] == 0
    if empty and os.environ.get("EMS_SEED", "1") == "1":
        with open(SEED_PATH, encoding="utf-8") as fh:
            conn.executescript(fh.read())
    conn.commit()
    conn.close()


# --------------------------------------------------------------------------
# CORS (frontend is served from a different port during development)
# --------------------------------------------------------------------------
@app.after_request
def add_cors_headers(resp):
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


# --------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------
def validate_employee(data):
    errors = {}
    name = (data.get("full_name") or "").strip()
    email = (data.get("email") or "").strip()
    phone = (data.get("phone") or "").strip()
    designation = (data.get("designation") or "").strip()
    join_date = (data.get("join_date") or "").strip()
    status = data.get("status") or "Active"

    if len(name) < 2:
        errors["full_name"] = "Full name is required (minimum 2 characters)."
    if not EMAIL_RE.match(email):
        errors["email"] = "Enter a valid email address."
    if phone and not PHONE_RE.match(phone):
        errors["phone"] = "Phone must contain exactly 10 digits."
    if not designation:
        errors["designation"] = "Designation is required."
    try:
        salary = int(data.get("salary"))
        if salary <= 0:
            raise ValueError
    except (TypeError, ValueError):
        salary = None
        errors["salary"] = "Salary must be a positive whole number."
    if not DATE_RE.match(join_date):
        errors["join_date"] = "Joining date is required."
    if status not in STATUSES:
        errors["status"] = "Status must be Active, On Leave or Resigned."
    try:
        dept_id = int(data.get("department_id"))
    except (TypeError, ValueError):
        dept_id = None
        errors["department_id"] = "Select a department."

    clean = dict(full_name=name, email=email, phone=phone or None,
                 designation=designation, salary=salary, join_date=join_date,
                 status=status, department_id=dept_id)
    return clean, errors


def validate_department(data):
    errors = {}
    name = (data.get("name") or "").strip()
    location = (data.get("location") or "").strip()
    if len(name) < 2:
        errors["name"] = "Department name is required (minimum 2 characters)."
    return dict(name=name, location=location or None), errors


def bad_request(errors, status=400):
    return jsonify({"message": "Validation failed", "errors": errors}), status


# --------------------------------------------------------------------------
# Health + statistics
# --------------------------------------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"status": "UP"})


@app.get("/api/stats")
def stats():
    db = get_db()
    row = db.execute(
        """SELECT COUNT(*)                                        AS total_employees,
                  COALESCE(SUM(salary), 0)                        AS monthly_payroll,
                  COALESCE(SUM(status = 'Active'), 0)             AS active_employees
           FROM employees"""
    ).fetchone()
    depts = db.execute("SELECT COUNT(*) FROM departments").fetchone()[0]
    return jsonify({**dict(row), "total_departments": depts})


# --------------------------------------------------------------------------
# Departments
# --------------------------------------------------------------------------
DEPT_SELECT = """
    SELECT d.id, d.name, d.location, d.created_at,
           (SELECT COUNT(*) FROM employees e WHERE e.department_id = d.id) AS employee_count
    FROM departments d
"""


@app.get("/api/departments")
def list_departments():
    rows = get_db().execute(DEPT_SELECT + " ORDER BY d.id").fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/departments/<int:dept_id>")
def get_department(dept_id):
    row = get_db().execute(DEPT_SELECT + " WHERE d.id = ?", (dept_id,)).fetchone()
    if row is None:
        return jsonify({"message": "Department not found"}), 404
    return jsonify(dict(row))


@app.post("/api/departments")
def create_department():
    clean, errors = validate_department(request.get_json(silent=True) or {})
    if errors:
        return bad_request(errors)
    db = get_db()
    try:
        cur = db.execute("INSERT INTO departments (name, location) VALUES (?, ?)",
                         (clean["name"], clean["location"]))
        db.commit()
    except sqlite3.IntegrityError:
        return bad_request({"name": "A department with this name already exists."}, 409)
    row = db.execute(DEPT_SELECT + " WHERE d.id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.put("/api/departments/<int:dept_id>")
def update_department(dept_id):
    clean, errors = validate_department(request.get_json(silent=True) or {})
    if errors:
        return bad_request(errors)
    db = get_db()
    if db.execute("SELECT 1 FROM departments WHERE id = ?", (dept_id,)).fetchone() is None:
        return jsonify({"message": "Department not found"}), 404
    try:
        db.execute("UPDATE departments SET name = ?, location = ? WHERE id = ?",
                   (clean["name"], clean["location"], dept_id))
        db.commit()
    except sqlite3.IntegrityError:
        return bad_request({"name": "A department with this name already exists."}, 409)
    row = db.execute(DEPT_SELECT + " WHERE d.id = ?", (dept_id,)).fetchone()
    return jsonify(dict(row))


@app.delete("/api/departments/<int:dept_id>")
def delete_department(dept_id):
    db = get_db()
    row = db.execute(DEPT_SELECT + " WHERE d.id = ?", (dept_id,)).fetchone()
    if row is None:
        return jsonify({"message": "Department not found"}), 404
    if row["employee_count"] > 0:
        return jsonify({"message": f"Cannot delete '{row['name']}': it still has "
                                   f"{row['employee_count']} employee(s). Reassign or remove them first."}), 409
    db.execute("DELETE FROM departments WHERE id = ?", (dept_id,))
    db.commit()
    return "", 204


# --------------------------------------------------------------------------
# Employees
# --------------------------------------------------------------------------
EMP_SELECT = """
    SELECT e.id, e.full_name, e.email, e.phone, e.designation, e.salary,
           e.join_date, e.status, e.department_id, d.name AS department_name,
           e.created_at
    FROM employees e JOIN departments d ON d.id = e.department_id
"""


@app.get("/api/employees")
def list_employees():
    q = (request.args.get("q") or "").strip()
    dept = request.args.get("department_id")
    sql, params, where = EMP_SELECT, [], []
    if q:
        where.append("(e.full_name LIKE ? OR e.email LIKE ? OR e.designation LIKE ?)")
        params += [f"%{q}%"] * 3
    if dept:
        where.append("e.department_id = ?")
        params.append(dept)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY e.id"
    rows = get_db().execute(sql, params).fetchall()
    return jsonify([dict(r) for r in rows])


@app.get("/api/employees/<int:emp_id>")
def get_employee(emp_id):
    row = get_db().execute(EMP_SELECT + " WHERE e.id = ?", (emp_id,)).fetchone()
    if row is None:
        return jsonify({"message": "Employee not found"}), 404
    return jsonify(dict(row))


def _department_exists(db, dept_id):
    return db.execute("SELECT 1 FROM departments WHERE id = ?", (dept_id,)).fetchone() is not None


@app.post("/api/employees")
def create_employee():
    clean, errors = validate_employee(request.get_json(silent=True) or {})
    if errors:
        return bad_request(errors)
    db = get_db()
    if not _department_exists(db, clean["department_id"]):
        return bad_request({"department_id": "Selected department does not exist."})
    try:
        cur = db.execute(
            """INSERT INTO employees (full_name, email, phone, designation, salary,
                                      join_date, status, department_id)
               VALUES (:full_name, :email, :phone, :designation, :salary,
                       :join_date, :status, :department_id)""", clean)
        db.commit()
    except sqlite3.IntegrityError:
        return bad_request({"email": "This email is already registered."}, 409)
    row = db.execute(EMP_SELECT + " WHERE e.id = ?", (cur.lastrowid,)).fetchone()
    return jsonify(dict(row)), 201


@app.put("/api/employees/<int:emp_id>")
def update_employee(emp_id):
    clean, errors = validate_employee(request.get_json(silent=True) or {})
    if errors:
        return bad_request(errors)
    db = get_db()
    if db.execute("SELECT 1 FROM employees WHERE id = ?", (emp_id,)).fetchone() is None:
        return jsonify({"message": "Employee not found"}), 404
    if not _department_exists(db, clean["department_id"]):
        return bad_request({"department_id": "Selected department does not exist."})
    try:
        db.execute(
            """UPDATE employees SET full_name = :full_name, email = :email, phone = :phone,
                      designation = :designation, salary = :salary, join_date = :join_date,
                      status = :status, department_id = :department_id
               WHERE id = :id""", {**clean, "id": emp_id})
        db.commit()
    except sqlite3.IntegrityError:
        return bad_request({"email": "This email is already registered."}, 409)
    row = db.execute(EMP_SELECT + " WHERE e.id = ?", (emp_id,)).fetchone()
    return jsonify(dict(row))


@app.delete("/api/employees/<int:emp_id>")
def delete_employee(emp_id):
    db = get_db()
    cur = db.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
    db.commit()
    if cur.rowcount == 0:
        return jsonify({"message": "Employee not found"}), 404
    return "", 204


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
