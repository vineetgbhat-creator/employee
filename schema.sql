-- Employee Management System : relational schema (SQLite)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    location    TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS employees (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    phone         TEXT,
    designation   TEXT    NOT NULL,
    salary        INTEGER NOT NULL CHECK (salary > 0),
    join_date     TEXT    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'Active'
                          CHECK (status IN ('Active', 'On Leave', 'Resigned')),
    department_id INTEGER NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (department_id) REFERENCES departments(id) ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department_id);
