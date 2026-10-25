"""API tests - run from project root:  python -m unittest tests.test_api -v"""
import os
import sys
import tempfile
import unittest

_tmp = tempfile.mkdtemp()
os.environ["EMS_DB"] = os.path.join(_tmp, "test.db")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import app as ems  # noqa: E402

VALID = dict(full_name="Test User", email="test.user@example.com", phone="9876543210",
             designation="Tester", salary=50000, join_date="2024-01-15",
             status="Active", department_id=1)


class EmployeeApiTests(unittest.TestCase):
    def setUp(self):
        self.c = ems.app.test_client()

    def test_01_health(self):
        self.assertEqual(self.c.get("/api/health").json["status"], "UP")

    def test_02_list_seeded_employees(self):
        r = self.c.get("/api/employees")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r.json), 6)

    def test_03_create_employee(self):
        r = self.c.post("/api/employees", json=VALID)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.json["department_name"], "Engineering")
        self.__class__.new_id = r.json["id"]

    def test_04_read_one(self):
        r = self.c.get(f"/api/employees/{self.__class__.new_id}")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["email"], VALID["email"])

    def test_05_update_employee(self):
        r = self.c.put(f"/api/employees/{self.__class__.new_id}", json={**VALID, "salary": 61000})
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json["salary"], 61000)

    def test_06_search_filter(self):
        self.assertEqual(len(self.c.get("/api/employees?q=kavya").json), 1)
        self.assertEqual(len(self.c.get("/api/employees?department_id=3").json), 2)

    def test_07_invalid_input_rejected(self):
        r = self.c.post("/api/employees", json={**VALID, "email": "bad", "salary": -5, "full_name": ""})
        self.assertEqual(r.status_code, 400)
        self.assertEqual(set(r.json["errors"]), {"full_name", "email", "salary"})

    def test_08_duplicate_email_conflict(self):
        r = self.c.post("/api/employees", json=VALID)
        self.assertEqual(r.status_code, 409)

    def test_09_delete_employee(self):
        r = self.c.delete(f"/api/employees/{self.__class__.new_id}")
        self.assertEqual(r.status_code, 204)
        self.assertEqual(self.c.get(f"/api/employees/{self.__class__.new_id}").status_code, 404)

    def test_10_department_crud(self):
        r = self.c.post("/api/departments", json={"name": "Legal", "location": "HQ"})
        self.assertEqual(r.status_code, 201)
        did = r.json["id"]
        self.assertEqual(self.c.put(f"/api/departments/{did}", json={"name": "Legal Affairs"}).json["name"],
                         "Legal Affairs")
        self.assertEqual(self.c.delete(f"/api/departments/{did}").status_code, 204)

    def test_11_department_with_employees_cannot_be_deleted(self):
        self.assertEqual(self.c.delete("/api/departments/1").status_code, 409)

    def test_12_stats(self):
        s = self.c.get("/api/stats").json
        self.assertEqual(s["total_employees"], 6)
        self.assertEqual(s["monthly_payroll"], 125000 + 98000 + 56000 + 72000 + 64000 + 83000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
