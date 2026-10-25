INSERT INTO departments (name, location) VALUES
  ('Engineering',     'Bengaluru HQ - Block A'),
  ('Human Resources', 'Bengaluru HQ - Block B'),
  ('Finance',         'Bengaluru HQ - Block B'),
  ('Operations',      'Site Office - Whitefield');

INSERT INTO employees (full_name, email, phone, designation, salary, join_date, status, department_id) VALUES
  ('Rohan Mehta',    'rohan.mehta@example.com',    '9845012345', 'Senior Software Engineer', 125000, '2021-06-14', 'Active',   1),
  ('Priya Nair',     'priya.nair@example.com',     '9731098765', 'HR Manager',                98000, '2020-02-03', 'Active',   2),
  ('Arjun Reddy',    'arjun.reddy@example.com',    '9900112233', 'Accounts Executive',        56000, '2022-09-19', 'Active',   3),
  ('Kavya Iyer',     'kavya.iyer@example.com',     '9886543210', 'QA Engineer',               72000, '2023-01-09', 'Active',   1),
  ('Imran Sheikh',   'imran.sheikh@example.com',   '9448076543', 'Site Supervisor',           64000, '2019-11-25', 'On Leave', 4),
  ('Sneha Kulkarni', 'sneha.kulkarni@example.com', '9620054321', 'Finance Analyst',           83000, '2021-03-15', 'Active',   3);
