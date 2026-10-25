# Employee Management System

A small full-stack web application for managing **employees** and **departments**
(Create, Read, Update, Delete) with a REST API and a relational database.

## Technologies
| Layer | Technology |
|-------|------------|
| Frontend | HTML5, CSS3, JavaScript (ES6+, `fetch` API) – no framework |
| Backend | Python 3 + Flask (REST API, validation, business rules) |
| Database | SQLite (file `data/ems.db`, created automatically on first run) |
| Tools | VS Code, terminal, curl, browser developer tools, Git |

## Prerequisites
* Python 3.10 or newer
* A modern web browser

## Installation
```bash
cd employee-management/backend
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
```

## Run
1. **Backend** (terminal 1)
   ```bash
   cd backend
   python app.py              # API at http://localhost:5000/api
   ```
2. **Frontend** (terminal 2)
   ```bash
   cd frontend
   python -m http.server 5500 # open http://localhost:5500
   ```
   (or open `frontend/index.html` with the VS Code *Live Server* extension)

The API base URL is set at the top of `frontend/app.js` (`const API = ...`).

## Tests
```bash
python -m unittest tests.test_api -v
```

## REST endpoints
| Method | URL | Purpose |
|--------|-----|---------|
| GET | `/api/employees?q=&department_id=` | list / search / filter employees |
| GET | `/api/employees/{id}` | one employee |
| POST | `/api/employees` | create employee |
| PUT | `/api/employees/{id}` | update employee |
| DELETE | `/api/employees/{id}` | delete employee |
| GET/POST | `/api/departments` | list / create departments |
| GET/PUT/DELETE | `/api/departments/{id}` | read / update / delete department |
| GET | `/api/stats` | dashboard numbers |
| GET | `/api/health` | connectivity check |

## Known limitations
* No login / authentication – intended as a lab project.
* A department that still has employees cannot be deleted (HTTP 409).
* SQLite is used for simplicity; the SQL is standard and can be moved to MySQL/PostgreSQL.
