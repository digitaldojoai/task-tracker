const API_BASE = "http://127.0.0.1:8000";
const STATUSES = ["ToDo", "InProgress", "Done"];

const els = {
  board: document.querySelector(".board"),
  addBtn: document.getElementById("add-task-btn"),
  priorityFilter: document.getElementById("priority-filter"),
  clearFiltersBtn: document.getElementById("clear-filters-btn"),
  errorBanner: document.getElementById("error-banner"),
  modalBackdrop: document.getElementById("modal-backdrop"),
  form: document.getElementById("task-form"),
  modalTitle: document.getElementById("modal-title"),
  taskId: document.getElementById("task-id"),
  fieldTitle: document.getElementById("field-title"),
  fieldDescription: document.getElementById("field-description"),
  fieldStatus: document.getElementById("field-status"),
  fieldPriority: document.getElementById("field-priority"),
  fieldAssignee: document.getElementById("field-assignee"),
  formError: document.getElementById("form-error"),
  deleteBtn: document.getElementById("delete-btn"),
  cancelBtn: document.getElementById("cancel-btn"),
};

function showError(message) {
  els.errorBanner.textContent = message;
  els.errorBanner.classList.remove("hidden");
}

function clearError() {
  els.errorBanner.classList.add("hidden");
  els.errorBanner.textContent = "";
}

function buildQuery() {
  const params = new URLSearchParams();
  if (els.priorityFilter.value) params.set("priority", els.priorityFilter.value);
  return params.toString();
}

async function fetchTasks() {
  const query = buildQuery();
  const response = await fetch(`${API_BASE}/tasks${query ? "?" + query : ""}`);
  if (!response.ok) throw new Error(`Failed to load tasks (${response.status})`);
  return response.json();
}

function renderCard(task) {
  const card = document.createElement("div");
  card.className = "card";
  card.dataset.id = task.id;

  const title = document.createElement("div");
  title.className = "card-title";
  title.textContent = task.title;
  card.appendChild(title);

  const meta = document.createElement("div");
  meta.className = "card-meta";

  const priorityPill = document.createElement("span");
  priorityPill.className = `pill pill-priority-${task.priority}`;
  priorityPill.textContent = task.priority;
  meta.appendChild(priorityPill);

  if (task.assignee) {
    const assigneePill = document.createElement("span");
    assigneePill.className = "pill";
    assigneePill.textContent = task.assignee;
    meta.appendChild(assigneePill);
  }

  card.appendChild(meta);
  card.addEventListener("click", () => openModal(task));
  return card;
}

async function renderBoard() {
  clearError();
  let tasks;
  try {
    tasks = await fetchTasks();
  } catch (err) {
    showError(err.message);
    return;
  }

  for (const status of STATUSES) {
    const list = document.getElementById(`list-${status}`);
    list.innerHTML = "";
    const tasksForStatus = tasks.filter((t) => t.status === status);
    document.getElementById(`count-${status}`).textContent = tasksForStatus.length;

    if (tasksForStatus.length === 0) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      empty.textContent = "No tasks";
      list.appendChild(empty);
      continue;
    }

    for (const task of tasksForStatus) {
      list.appendChild(renderCard(task));
    }
  }
}

function openModal(task) {
  els.form.reset();
  els.formError.classList.add("hidden");
  els.deleteBtn.dataset.confirming = "false";
  els.deleteBtn.textContent = "Delete";

  if (task) {
    els.modalTitle.textContent = "Edit task";
    els.taskId.value = task.id;
    els.fieldTitle.value = task.title;
    els.fieldDescription.value = task.description || "";
    els.fieldStatus.value = task.status;
    els.fieldPriority.value = task.priority;
    els.fieldAssignee.value = task.assignee || "";
    els.deleteBtn.classList.remove("hidden");
  } else {
    els.modalTitle.textContent = "Add task";
    els.taskId.value = "";
    els.fieldStatus.value = "ToDo";
    els.fieldPriority.value = "Medium";
    els.deleteBtn.classList.add("hidden");
  }

  els.modalBackdrop.classList.remove("hidden");
  els.fieldTitle.focus();
}

function closeModal() {
  els.modalBackdrop.classList.add("hidden");
}

function currentPayload() {
  return {
    title: els.fieldTitle.value,
    description: els.fieldDescription.value,
    status: els.fieldStatus.value,
    priority: els.fieldPriority.value,
    assignee: els.fieldAssignee.value || null,
  };
}

async function submitForm(event) {
  event.preventDefault();
  els.formError.classList.add("hidden");

  const id = els.taskId.value;
  const payload = currentPayload();
  const url = id ? `${API_BASE}/tasks/${id}` : `${API_BASE}/tasks`;
  const method = id ? "PATCH" : "POST";

  try {
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const body = await response.json().catch(() => ({}));
      throw new Error(body.detail ? JSON.stringify(body.detail) : `Save failed (${response.status})`);
    }

    closeModal();
    renderBoard();
  } catch (err) {
    els.formError.textContent = err.message;
    els.formError.classList.remove("hidden");
  }
}

async function deleteCurrentTask() {
  const id = els.taskId.value;
  if (!id) return;

  if (els.deleteBtn.dataset.confirming !== "true") {
    els.deleteBtn.dataset.confirming = "true";
    els.deleteBtn.textContent = "Confirm delete?";
    return;
  }

  try {
    const response = await fetch(`${API_BASE}/tasks/${id}`, { method: "DELETE" });
    if (!response.ok && response.status !== 204) {
      throw new Error(`Delete failed (${response.status})`);
    }
    closeModal();
    renderBoard();
  } catch (err) {
    els.formError.textContent = err.message;
    els.formError.classList.remove("hidden");
  }
}

els.addBtn.addEventListener("click", () => openModal(null));
els.cancelBtn.addEventListener("click", closeModal);
els.form.addEventListener("submit", submitForm);
els.deleteBtn.addEventListener("click", deleteCurrentTask);
els.priorityFilter.addEventListener("change", renderBoard);
els.clearFiltersBtn.addEventListener("click", () => {
  els.priorityFilter.value = "";
  renderBoard();
});
els.modalBackdrop.addEventListener("click", (event) => {
  if (event.target === els.modalBackdrop) closeModal();
});

renderBoard();
