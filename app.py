# app.py
from flask import Flask, render_template_string, request, redirect, url_for, flash
from user_dao import UserDAO, User

app = Flask(__name__)
app.secret_key = "dev"  # replace in production
dao = UserDAO("users.db")
dao.create_table()  # safe if exists

TEMPLATE = """
<!doctype html>
<title>Users</title>
<link rel="stylesheet" href="https://unpkg.com/mVP.css">  <!-- tiny minimalist CSS -->
<div class="container">
  <h1>Users</h1>

  {% with messages = get_flashed_messages() %}
    {% if messages %}
      <ul class="messages">{% for m in messages %}<li>{{ m }}</li>{% endfor %}</ul>
    {% endif %}
  {% endwith %}

  <table>
    <thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Active</th><th>Actions</th></tr></thead>
    <tbody>
    {% for u in users %}
      <tr>
        <td>{{ u.id }}</td>
        <td>{{ u.name }}</td>
        <td>{{ u.email or "" }}</td>
        <td>{{ "✅" if u.active else "❌" }}</td>
        <td style="white-space:nowrap">
          <form action="{{ url_for('toggle_active', user_id=u.id) }}" method="post" style="display:inline">
            <button>Toggle Active</button>
          </form>
          <form action="{{ url_for('delete_user', user_id=u.id) }}" method="post" style="display:inline" onsubmit="return confirm('Delete this user?')">
            <button>Delete</button>
          </form>
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>

  <h2>Add User</h2>
  <form method="post" action="{{ url_for('create_user') }}">
    <label>Name <input name="name" required></label>
    <label>Email <input name="email" placeholder="optional"></label>
    <label><input type="checkbox" name="active" checked> Active</label>
    <button type="submit">Create</button>
  </form>
</div>
"""

@app.get("/")
def index():
    users = dao.get_all()
    return render_template_string(TEMPLATE, users=users)

@app.post("/users/create")
def create_user():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip() or None
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
