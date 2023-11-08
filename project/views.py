from flask import Blueprint, render_template, redirect, request, url_for
from celery.result import AsyncResult
from .tasks import process_runner_input
from .models import MapBuilder

main = Blueprint('main', __name__)

@main.route("/")
def index():
    return render_template("index.html")


@main.route("/about")
def about():
    return render_template("about.html")

@main.route("/input", methods=["GET", "POST"])
def input():
    if request.method == "POST":
        form_data = request.form
        task = process_runner_input.delay(form_data)
        return redirect(url_for("main.loading", task_id=task))
    return render_template("input.html")


@main.route("/loading/<task_id>")
def loading(task_id):
    task = AsyncResult(task_id)
    state = task.state
    if state =="STARTED" or state=="PENDING":
        return render_template("loading.html", result=state, refresh=True)
    elif state == "SUCCESS":
        print(task.status)
        result = task.result
        route_info = result  # Extract distance and generated_run_html
        print(len(route_info))
        print(route_info)
        distance = 2
        return render_template(
            "customized_run.html", distance=distance)
    else:
        print(state)
        return render_template("error.html")
    