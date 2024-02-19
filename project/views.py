from flask import Blueprint, abort, render_template, redirect, request, url_for
from rq import Queue
from flask import render_template, flash, redirect, url_for
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlparse
from .forms import LoginForm, RegistrationForm
from .models import User
from .models import Route
from project.worker import conn
from .extensions import db

main = Blueprint("main", __name__)
q = Queue(connection=conn)


@main.route("/landing")
@login_required
def landing():
    # This is your current index route, now serving as the landing page
    return render_template("landing.html", current_user=current_user)


@main.route("/", methods=["GET", "POST"])
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.landing"))

    login_form = LoginForm(prefix="login")
    print("Request form contents:")
    print(request.form)
    if "login-submit" in request.form and login_form.validate_on_submit():
        user = User.query.filter_by(email=login_form.email.data).first()
        print("user logging in:")
        print(user)
        print(
            "check password is a " + str(user.check_password(login_form.password.data))
        )
        if user and user.check_password(login_form.password.data):
            login_user(user, remember=login_form.remember_me.data)
            next_page = request.args.get("next")
            if not next_page or urlparse(next_page).netloc != "":
                next_page = url_for("main.landing")
            return redirect(next_page)
        elif "login-submit" in request.form:
            flash("Invalid email or password")

    return render_template("login.html", login_form=login_form)


@main.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegistrationForm(prefix="register")
    print("Request form contents:")
    print(request.form)
    if "register-submit" in request.form and register_form.validate_on_submit():
        print("creating a user!")
        user = User(
            first_name=register_form.first_name.data,
            last_name=register_form.last_name.data,
            email=register_form.email.data,
        )
        user.set_password(register_form.password.data)
        print("about to add user to the database")
        db.session.add(user)
        db.session.commit()
        print("successfully added user!")
        flash("Congratulations, you are now a registered user!")
        return redirect(url_for("main.landing"))

    return render_template("register.html", register_form=register_form)


@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@main.route("/about")
def about():
    return render_template("about.html")


@main.route("/input", methods=["GET", "POST"])
def input():
    from .tasks import process_runner_input

    if request.method == "POST":
        form_data = request.form
        # Check if the user is authenticated to get the user ID
        user_id = current_user.id if current_user.is_authenticated else None

        job = q.enqueue(process_runner_input, form_data, user_id)
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


@login_required
@main.route("/customized_run/<route_id>")
def customized_run(route_id):
    # Query the database for the Route with the provided ID
    route = Route.query.get(route_id)
    if route is None:
        abort(404, description="Route not found")
        # Check if the current user is the owner of the route
    if route.user_id != current_user.id:
        abort(403)  # Forbidden access if the user does not own the route

    # Pass the coordinates to the template, converting them to a JSON string if needed
    return render_template("customized_run.html", waypoints=route.coordinates)


@main.route("/leaflet")
def leaflet():
    waypoints = [
        {"lat": 47.6954566, "lng": -122.1266523},
        {"lat": 47.6951402, "lng": -122.1266353},
    ]
    return render_template("leaflet.html", waypoints=waypoints)
