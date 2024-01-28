from flask import Blueprint, abort, render_template, redirect, request, url_for
from rq import Queue
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from .forms import LoginForm, RegistrationForm
from .models import User
from .models import Route
from project.worker import conn

main = Blueprint("main", __name__)
q = Queue(connection=conn)


@main.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid username or password")
            return redirect(url_for("main.login"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.index")
        return redirect(next_page)
    return render_template("login.html", title="Sign In", form=form)


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    from .extensions import db

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("main.login"))
    return render_template("register.html", title="Register", form=form)


@main.route("/")
def index():
    return render_template("index.html")


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/input", methods=["GET", "POST"])
def input():
    from .tasks import process_runner_input

    if request.method == "POST":
        form_data = request.form
        job = q.enqueue(process_runner_input, form_data)
        return redirect(url_for("main.loading", task_id=job.id))
    return render_template("input.html")


@main.route("/loading/<task_id>")
def loading(task_id):
    job = q.fetch_job(task_id)
    status = job.get_status()
    if status in ["queued", "started", "deferred", "failed"]:
        return render_template("loading.html", result=status, refresh=True)
    elif status == "finished":
        results = job.result
        print("the results are:")
        print(results)
        return redirect(url_for("main.customized_run", route_id=results))
    else:
        print(status)
        return render_template("error.html")


@main.route("/customized_run/<route_id>")
def customized_run(route_id):
    # Query the database for the Route with the provided ID
    route = Route.query.get(route_id)
    if route is None:
        abort(404, description="Route not found")
    print("This is route.coordinates!!!!")
    print(route.coordinates)
    # Pass the coordinates to the template, converting them to a JSON string if needed
    return render_template("customized_run.html", waypoints=route.coordinates)


@main.route("/leaflet")
def leaflet():
    waypoints = [
        {"lat": 47.6954566, "lng": -122.1266523},
        {"lat": 47.6951402, "lng": -122.1266353},
    ]
    return render_template("leaflet.html", waypoints=waypoints)
