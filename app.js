/* Employee Management System - client controller (vanilla JavaScript, fetch API) */
const API = "http://localhost:5000/api";

const state = { employees: [], departments: [] };
const $ = (id) => document.getElementById(id);
const inrFormat = new Intl.NumberFormat("en-IN");
const money = (n) => "₹ " + inrFormat.format(n);

/* ---------- small helpers ---------- */
function esc(text) {
  const d = document.createElement("div");
  d.textContent = text == null ? "" : String(text);
  return d.innerHTML;                       // XSS-safe output
}

function fmtDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

function toast(message, type = "ok") {
  const el = document.createElement("div");
  el.className = "toast " + type;
  el.textContent = message;
  $("toasts").appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

async function api(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(API + path, opts);
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = new Error(data.message || "Request failed");
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

function confirmDialog(title, text, okLabel = "Yes, delete") {
  return new Promise((resolve) => {
    $("modal-title").textContent = title;
    $("modal-text").textContent = text;
    $("modal-ok").textContent = okLabel;
    $("modal").hidden = false;
    const done = (v) => { $("modal").hidden = true; $("modal-ok").onclick = $("modal-cancel").onclick = null; resolve(v); };
    $("modal-ok").onclick = () => done(true);
    $("modal-cancel").onclick = () => done(false);
  });
}

/* ---------- form error helpers ---------- */
function clearErrors(form) {
  form.querySelectorAll(".err").forEach((e) => (e.textContent = ""));
  form.querySelectorAll(".invalid").forEach((e) => e.classList.remove("invalid"));
}
function showErrors(form, errors) {
  Object.entries(errors).forEach(([field, msg]) => {
    const key = form.id === "dept-form" ? "dept-" + field : field;
    const small = form.querySelector(`.err[data-for="${key}"]`);
    const input = $(key);
    if (small) small.textContent = msg;
    if (input) input.classList.add("invalid");
  });
}

/* ---------- connection + KPIs ---------- */
async function checkHealth() {
  try {
    await api("GET", "/health");
    $("conn").className = "conn up";
    $("conn").querySelector("b").textContent = "API Connected";
    return true;
  } catch {
    $("conn").className = "conn down";
    $("conn").querySelector("b").textContent = "API Offline";
    return false;
  }
}

async function loadStats() {
  const s = await api("GET", "/stats");
  $("kpi-total").textContent = s.total_employees;
  $("kpi-active").textContent = s.active_employees;
  $("kpi-depts").textContent = s.total_departments;
  $("kpi-payroll").textContent = money(s.monthly_payroll);
}

/* ---------- departments ---------- */
async function loadDepartments() {
  state.departments = await api("GET", "/departments");
  renderDepartments();
  fillDepartmentSelects();
}

function fillDepartmentSelects() {
  const formSel = $("department_id");
  const keep = formSel.value;
  formSel.innerHTML = '<option value="">Select department</option>' +
    state.departments.map((d) => `<option value="${d.id}">${esc(d.name)}</option>`).join("");
  formSel.value = keep;

  const filter = $("filter-dept");
  const keepF = filter.value;
  filter.innerHTML = '<option value="">All departments</option>' +
    state.departments.map((d) => `<option value="${d.id}">${esc(d.name)}</option>`).join("");
  filter.value = keepF;
}

function renderDepartments() {
  const body = $("dept-body");
  if (!state.departments.length) {
    body.innerHTML = '<tr><td colspan="5" class="empty">No departments yet.</td></tr>';
    return;
  }
  body.innerHTML = state.departments.map((d) => `
    <tr>
      <td>#${d.id}</td>
      <td class="name">${esc(d.name)}</td>
      <td>${esc(d.location || "—")}</td>
      <td class="num">${d.employee_count}</td>
      <td><div class="row-actions">
        <button class="btn small edit" data-act="dept-edit" data-id="${d.id}" type="button">Edit</button>
        <button class="btn small del" data-act="dept-del" data-id="${d.id}" type="button">Delete</button>
      </div></td>
    </tr>`).join("");
}

function resetDeptForm() {
  $("dept-form").reset();
  $("dept-id").value = "";
  $("dept-form-title").textContent = "Add New Department";
  $("dept-cancel").hidden = true;
  clearErrors($("dept-form"));
}

$("dept-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  clearErrors(form);
  const payload = { name: $("dept-name").value.trim(), location: $("dept-location").value.trim() };
  if (payload.name.length < 2) {
    showErrors(form, { name: "Department name is required (minimum 2 characters)." });
    return;
  }
  const id = $("dept-id").value;
  try {
    if (id) await api("PUT", `/departments/${id}`, payload);
    else await api("POST", "/departments", payload);
    toast(id ? "Department updated successfully" : "Department created successfully");
    resetDeptForm();
    await refreshAll();
  } catch (err) {
    if (err.data && err.data.errors) showErrors(form, err.data.errors);
    toast(err.message, "error");
  }
});
$("dept-cancel").addEventListener("click", resetDeptForm);

$("dept-body").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const dept = state.departments.find((d) => d.id === Number(btn.dataset.id));
  if (btn.dataset.act === "dept-edit") {
    $("dept-id").value = dept.id;
    $("dept-name").value = dept.name;
    $("dept-location").value = dept.location || "";
    $("dept-form-title").textContent = `Edit Department #${dept.id}`;
    $("dept-cancel").hidden = false;
  } else {
    const ok = await confirmDialog("Delete department?", `“${dept.name}” will be permanently removed.`);
    if (!ok) return;
    try {
      await api("DELETE", `/departments/${dept.id}`);
      toast("Department deleted");
      await refreshAll();
    } catch (err) {
      toast(err.message, "error");
    }
  }
});

/* ---------- employees ---------- */
async function loadEmployees() {
  const params = new URLSearchParams();
  const q = $("search").value.trim();
  if (q) params.set("q", q);
  if ($("filter-dept").value) params.set("department_id", $("filter-dept").value);
  const qs = params.toString();
  state.employees = await api("GET", "/employees" + (qs ? "?" + qs : ""));
  renderEmployees();
}

function statusBadge(s) {
  const cls = s === "Active" ? "active" : s === "On Leave" ? "leave" : "resigned";
  return `<span class="badge ${cls}">${esc(s)}</span>`;
}

function renderEmployees() {
  const body = $("emp-body");
  const editing = $("emp-id").value;
  if (!state.employees.length) {
    body.innerHTML = '<tr><td colspan="7" class="empty">No employees match your search.</td></tr>';
    return;
  }
  body.innerHTML = state.employees.map((e) => `
    <tr class="${String(e.id) === editing ? "editing" : ""}">
      <td>#${e.id}</td>
      <td><div class="name">${esc(e.full_name)}</div><div class="sub">${esc(e.email)}</div></td>
      <td>${esc(e.department_name)}</td>
      <td>${esc(e.designation)}<div class="sub">Joined ${fmtDate(e.join_date)}</div></td>
      <td class="num">${money(e.salary)}</td>
      <td>${statusBadge(e.status)}</td>
      <td><div class="row-actions">
        <button class="btn small edit" data-act="emp-edit" data-id="${e.id}" type="button">Edit</button>
        <button class="btn small del" data-act="emp-del" data-id="${e.id}" type="button">Delete</button>
      </div></td>
    </tr>`).join("");
}

const EMP_FIELDS = ["full_name", "email", "phone", "designation", "salary", "join_date", "status", "department_id"];

function resetEmpForm() {
  $("emp-form").reset();
  $("emp-id").value = "";
  $("emp-form-title").textContent = "Add New Employee";
  $("emp-save").textContent = "Save Employee";
  $("emp-cancel").hidden = true;
  clearErrors($("emp-form"));
  renderEmployees();
}

function clientValidate(p) {
  const errors = {};
  if (p.full_name.length < 2) errors.full_name = "Full name is required (minimum 2 characters).";
  if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(p.email)) errors.email = "Enter a valid email address.";
  if (p.phone && !/^\d{10}$/.test(p.phone)) errors.phone = "Phone must contain exactly 10 digits.";
  if (!p.designation) errors.designation = "Designation is required.";
  if (!/^\d+$/.test(p.salary) || Number(p.salary) <= 0) errors.salary = "Salary must be a positive whole number.";
  if (!p.join_date) errors.join_date = "Joining date is required.";
  if (!p.department_id) errors.department_id = "Select a department.";
  return errors;
}

$("emp-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  clearErrors(form);
  const payload = {};
  EMP_FIELDS.forEach((f) => (payload[f] = $(f).value.trim()));

  const errors = clientValidate(payload);
  if (Object.keys(errors).length) {
    showErrors(form, errors);
    return;                                   // nothing is sent to the server
  }
  payload.salary = Number(payload.salary);
  payload.department_id = Number(payload.department_id);

  const id = $("emp-id").value;
  try {
    if (id) await api("PUT", `/employees/${id}`, payload);
    else await api("POST", "/employees", payload);
    toast(id ? "Employee updated successfully" : "Employee created successfully");
    resetEmpForm();
    await refreshAll();
  } catch (err) {
    if (err.data && err.data.errors) showErrors(form, err.data.errors);
    toast(err.data && err.data.errors ? Object.values(err.data.errors)[0] : err.message, "error");
  }
});
$("emp-cancel").addEventListener("click", resetEmpForm);

$("emp-body").addEventListener("click", async (e) => {
  const btn = e.target.closest("button[data-act]");
  if (!btn) return;
  const emp = state.employees.find((x) => x.id === Number(btn.dataset.id));
  if (btn.dataset.act === "emp-edit") {
    clearErrors($("emp-form"));
    $("emp-id").value = emp.id;
    EMP_FIELDS.forEach((f) => ($(f).value = emp[f] == null ? "" : emp[f]));
    $("emp-form-title").textContent = `Edit Employee #${emp.id}`;
    $("emp-save").textContent = "Update Employee";
    $("emp-cancel").hidden = false;
    renderEmployees();
    window.scrollTo({ top: 0, behavior: "smooth" });
  } else {
    const ok = await confirmDialog("Delete employee?", `${emp.full_name} (${emp.designation}) will be permanently removed.`);
    if (!ok) return;
    try {
      await api("DELETE", `/employees/${emp.id}`);
      toast("Employee deleted successfully");
      if ($("emp-id").value === String(emp.id)) resetEmpForm();
      await refreshAll();
    } catch (err) {
      toast(err.message, "error");
    }
  }
});

/* debounced live search + department filter */
let timer;
$("search").addEventListener("input", () => { clearTimeout(timer); timer = setTimeout(loadEmployees, 300); });
$("filter-dept").addEventListener("change", loadEmployees);
$("refresh").addEventListener("click", () => refreshAll().then(() => toast("Data refreshed")));

/* ---------- tabs ---------- */
document.querySelectorAll(".tab").forEach((t) =>
  t.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((x) => x.classList.toggle("active", x === t));
    $("view-employees").hidden = t.dataset.tab !== "employees";
    $("view-departments").hidden = t.dataset.tab !== "departments";
  })
);

/* ---------- boot ---------- */
async function refreshAll() {
  await Promise.all([loadDepartments(), loadStats()]);
  await loadEmployees();
}

(async function init() {
  if (await checkHealth()) {
    try { await refreshAll(); } catch (err) { toast(err.message, "error"); }
  } else {
    toast("Cannot reach the API at " + API, "error");
  }
})();
