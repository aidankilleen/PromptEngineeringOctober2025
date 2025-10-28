# app_bootstrap_edit.py
from flask import Flask, render_template_string, request, redirect, url_for, flash
from user_dao import UserDAO, User

app = Flask(__name__)
app.secret_key = "dev"
dao = UserDAO("users.db")
dao.create_table()

TEMPLATE = """
<!doctype html>
<html lang="en" data-bs-theme="light">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Users</title>

  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

  <!-- Bootstrap Icons -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css" rel="stylesheet">

  <!-- DataTables (Bootstrap 5) CSS -->
  <link href="https://cdn.datatables.net/1.13.8/css/dataTables.bootstrap5.min.css" rel="stylesheet">

  <style> body { padding-top: 2rem; } </style>
</head>
<body>
<div class="container">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0">Users</h1>
    <form class="d-flex" method="post" action="{{ url_for('create_user') }}">
      <div class="input-group">
        <input class="form-control" name="name" placeholder="Name" required>
        <input class="form-control" name="email" placeholder="Email (optional)">
        <button class="btn btn-primary" type="submit">
          <i class="bi bi-plus-lg"></i> Add
        </button>
      </div>
      <div class="form-check ms-2">
        <input class="form-check-input" type="checkbox" name="active" id="active" checked>
        <label class="form-check-label" for="active">Active</label>
      </div>
    </form>
  </div>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <div class="alert alert-info" role="alert">
        {% for m in messages %}{{ m }}<br>{% endfor %}
      </div>
    {% endif %}
  {% endwith %}

  <div class="card">
    <div class="card-body">
      <div class="table-responsive">
        <table id="usersTable" class="table table-striped table-hover table-bordered align-middle">
          <thead class="table-light">
            <tr>
              <th style="width: 80px;">ID</th>
              <th>Name</th>
              <th>Email</th>
              <th style="width: 100px;">Active</th>
              <th style="width: 140px;">Actions</th>
            </tr>
          </thead>
          <tbody>
            {% for u in users %}
            <tr>
              <td class="text-center">{{ u.id }}</td>
              <td>{{ u.name }}</td>
              <td>{{ u.email or "" }}</td>
              <td class="text-center">
                {% if u.active %}<span class="badge text-bg-success">True</span>
                {% else %}<span class="badge text-bg-secondary">False</span>{% endif %}
              </td>
              <td class="text-center">
                <div class="d-inline-flex gap-2">
                  <!-- Edit button (modal + JS-initialized tooltip) -->
                  <button
                    type="button"
                    class="btn btn-sm btn-outline-secondary btn-edit"
                    data-bs-toggle="modal"
                    data-bs-target="#editModal"
                    data-user-id="{{ u.id }}"
                    data-user-name="{{ u.name|e }}"
                    data-user-email="{{ (u.email or '')|e }}"
                    data-user-active="{{ 1 if u.active else 0 }}"
                    data-edit-url="{{ url_for('edit_user', user_id=u.id) }}"
                    data-bs-title="Edit User" data-bs-placement="top"
                  >
                    <i class="bi bi-pencil-square"></i>
                  </button>

                  <!-- Delete button (tooltip via data attribute) -->
                  <form method="post" action="{{ url_for('delete_user', user_id=u.id) }}"
                        onsubmit="return confirm('Delete this user?')" style="display:inline">
                    <button
                      class="btn btn-sm btn-outline-danger"
                      type="submit"
                      data-bs-toggle="tooltip" data-bs-placement="top" title="Delete User"
                    >
                      <i class="bi bi-trash"></i>
                    </button>
                  </form>
                </div>
              </td>
            </tr>
            {% endfor %}
          </tbody>
          <tfoot class="table-light">
            <tr>
              <th>ID</th><th>Name</th><th>Email</th><th>Active</th><th>Actions</th>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  </div>
</div>

<!-- Edit User Modal -->
<div class="modal fade" id="editModal" tabindex="-1" aria-labelledby="editModalLabel" aria-hidden="true">
  <div class="modal-dialog">
    <form method="post" id="editForm">
      <div class="modal-content">
        <div class="modal-header">
          <h1 class="modal-title fs-5" id="editModalLabel">Edit User</h1>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Cancel"></button>
        </div>
        <div class="modal-body">
          <input type="hidden" name="id" id="edit-id">
          <div class="mb-3">
            <label for="edit-name" class="form-label">Name</label>
            <input type="text" class="form-control" name="name" id="edit-name" required>
          </div>
          <div class="mb-3">
            <label for="edit-email" class="form-label">Email</label>
            <input type="email" class="form-control" name="email" id="edit-email" placeholder="optional">
          </div>
          <div class="form-check">
            <input class="form-check-input" type="checkbox" name="active" id="edit-active">
            <label class="form-check-label" for="edit-active">Active</label>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-outline-secondary" data-bs-dismiss="modal">Cancel</button>
          <button type="submit" class="btn btn-primary">Save</button>
        </div>
      </div>
    </form>
  </div>
</div>

<!-- Scripts -->
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/dataTables.bootstrap5.min.js"></script>

<script>
  $(function () {
    $('#usersTable').DataTable({
      pageLength: 10,
      lengthMenu: [5, 10, 25, 50, 100],
      order: [[0, 'asc']],
      columnDefs: [{ orderable: false, targets: 4 }]
    });

    // Enable tooltips for elements that use data-bs-toggle="tooltip" (e.g., Delete)
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(el => new bootstrap.Tooltip(el));

    // ALSO enable tooltips for Edit buttons (they use modal on data-bs-toggle)
    document.querySelectorAll('.btn-edit').forEach(btn => {
      new bootstrap.Tooltip(btn, {
        title: btn.getAttribute('data-bs-title') || 'Edit User',
        placement: btn.getAttribute('data-bs-placement') || 'top'
      });
    });

    // Fill modal from button's data-* and set the form action
    const editModal = document.getElementById('editModal');
    editModal.addEventListener('show.bs.modal', function (event) {
      const button = event.relatedTarget;
      const id = button.getAttribute('data-user-id');
      const name = button.getAttribute('data-user-name');
      const email = button.getAttribute('data-user-email');
      const active = button.getAttribute('data-user-active') === '1';
      const editUrl = button.getAttribute('data-edit-url');

      document.getElementById('edit-id').value = id;
      document.getElementById('edit-name').value = name || '';
      document.getElementById('edit-email').value = email || '';
      document.getElementById('edit-active').checked = active;

      document.getElementById('editForm').action = editUrl;
    });
  });
</script>
</body>
</html>
"""

@app.get("/")
def index():
    users = dao.get_all()
    return render_template_string(TEMPLATE, users=users)

@app.post("/users/create")
def create_user():
    name = request.form.get("name", "").strip()
    email = (request.form.get("email") or "").strip() or None
    active = request.form.get("active") == "on"
    if not name:
        flash("Name is required.")
        return redirect(url_for("index"))
    dao.create(User(id=None, name=name, email=email, active=active))
    flash("User created.")
    return redirect(url_for("index"))

@app.post("/users/<int:user_id>/delete")
def delete_user(user_id: int):
    if dao.delete(user_id):
        flash("User deleted.")
    else:
        flash("User not found.")
    return redirect(url_for("index"))

@app.post("/users/<int:user_id>/edit")
def edit_user(user_id: int):
    name = (request.form.get("name") or "").strip()
    email = (request.form.get("email") or "").strip() or None
    active = request.form.get("active") == "on"

    if not name:
        flash("Name is required.")
        return redirect(url_for("index"))

    user = dao.get_by_id(user_id)
    if not user:
        flash("User not found.")
        return redirect(url_for("index"))

    user.name = name
    user.email = email
    user.active = active
    dao.update(user)
    flash("User updated.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
