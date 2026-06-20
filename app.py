

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from sqlalchemy import Table

app = Flask(__name__)

app.config["SECRET_KEY"] = "mysecretkey"
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "sqlite:///tasks.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# ======================
# Models
# ======================

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)

    completed = db.Column(db.Boolean, default=False)

    priority = db.Column(db.String(20), default="Medium")

    due_date = db.Column(db.String(20))
    category = db.Column(db.String(50), default="Personal")
    description = db.Column(db.Text)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ======================
# Routes
# ======================

@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        existing_user = User.query.filter_by(
            username=username
        ).first()

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("register"))

        user = User(
            username=username,
            password=password
        )

        db.session.add(user)
        db.session.commit()

        flash("Registration successful!")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid username or password")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():

    search = request.args.get("search", "")

    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.title.ilike(f"%{search}%")
    ).all()

    total = len(tasks)

    completed = len(
        [task for task in tasks if task.completed]
    )

    pending = total - completed

    return render_template(
        "dashboard.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending
    )


@app.route("/add", methods=["GET", "POST"])
@login_required
def add_task():

    if request.method == "POST":

        title = request.form["title"]
        priority = request.form["priority"]
        category = request.form["category"]
        due_date = request.form["due_date"]
        description = request.form["description"]

        task = Task(
            title=title,
            description=description,
            priority=priority,
            category=category,
            due_date=due_date,
            user_id=current_user.id
        )

        db.session.add(task)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("add_task.html")



@app.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        task.title = request.form["title"]
        task.priority = request.form.get("priority", "Low").lower()
        task.due_date = request.form["due_date"]
        task.category = request.form["category"]

        db.session.commit()
        flash("Task updated successfully!")

        return redirect(url_for("dashboard"))

    return render_template(
        "edit_task.html",
        task=task
    )



@app.route("/complete/<int:id>")
@login_required
def complete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        return redirect(url_for("dashboard"))

    task.completed = not task.completed

    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/delete/<int:id>")
@login_required
def delete_task(id):

    task = Task.query.get_or_404(id)

    if task.user_id != current_user.id:
        return redirect(url_for("dashboard"))

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("dashboard"))


@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))

@app.route("/users")
def users():

    all_users = User.query.all()

    return render_template(
        "users.html",
        users=all_users
    )

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)