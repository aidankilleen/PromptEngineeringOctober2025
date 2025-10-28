# app_bootstrap.py
from flask import Flask, render_template_string, request, redirect, url_for, flash
from user_dao import UserDAO, User

app = Flask(__name__)
app.secret_key = "dev"  # replace in production
dao = UserDAO("users.db")
dao.create_table()  # safe if already exists

TEMPLATE = """
<!doctype html>
<html lang="en" data-bs-theme="light">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Users</title>

  <!-- Bootstrap 5 CSS -->
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet">

  <!-- DataTables (Bootstrap 5) CSS -->
  <link href="https://cdn.datatables.net/1.13.8/css/dataTables.bootstrap5.min.css" rel="stylesheet">

  <style>
    body { padding-top: 2rem; }
    .form-inline label { margin-right: .5rem; }
    .messages { list-style: none; padding-left: 0; }
  </style>
</head>
<body>
<div class="container">
  <div class="d-flex align-items-center justify-content-between mb-4">
    <h1 class="h3 mb-0">Users</h1>
    <form class="d-flex" method="post" action="{{ url_for('create_user') }}">
      <div class="input-group">
        <input class="form-control" name="name" placeholder="Name" required>
        <input class="form-control" name="email" placeholder="Email (optional)">
        <button class="btn btn-primary" type="submit">Add</button>
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
              <th style="width: 220px;">Actions</th>
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
                  <form method="post" action="{{ url_for('toggle_active', user_id=u.id) }}">
                    <button class="btn btn-sm btn-outline-primary" type="submit">Toggle Active</button>
                  </form>
                  <form method="post" action="{{ url_for('delete_user', user_id=u.id) }}"
                        onsubmit="return confirm('Delete this user?')">
                    <button class="btn btn-sm btn-outline-danger" type="submit">Delete</button>
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

<!-- jQuery (required by DataTables) -->
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<!-- Bootstrap 5 JS -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
<!-- DataTables + Bootstrap 5 integration -->
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/dataTables.bootstrap5.min.js"></script>

<script>
  $(function () {
    $('#usersTable').DataTable({
      pageLength: 10,
      lengthMenu: [5, 10, 25, 50, 100],
      order: [[0, 'asc']],
      columnDefs: [
        { orderable: false, targets: 4 } // Actions column not sortable
      ]
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

@app.post("/users/<int:user_id>/toggle")
def toggle_active(user_id: int):
    u = dao.get_by_id(user_id)
    if not u:
        flash("User not found.")
        return redirect(url_for("index"))
    u.active = not u.active
    dao.update(u)
    flash("User updated.")
    return redirect(url_for("index"))

@app.post("/users/<int:user_id>/delete")
def delete_user(user_id: int):
    if dao.delete(user_id):
        flash("User deleted.")
    else:
        flash("User not found.")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
