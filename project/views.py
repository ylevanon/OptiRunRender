from flask import Blueprint, render_template, redirect, request, url_for
from celery.result import AsyncResult
from .tasks import process_runner_input
from .models import Run, Graph, MapBuilder

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
        print(result)
        print(len(result))
        address = result[0]
        distance = result[1]
        tour = result[2]
        route_length = result[3]
        graph = Graph(distance=distance, address=address)
        run = Run(distance=distance, address=address, graph=graph)
        map_builder = MapBuilder()
        map_builder.generate_run_map(run, graph, tour)
        # generated_run_html, distance= result  # Extract distance and generated_run_html
        # return render_template(
        #     "customized_run.html", distance=distance)
        return render_template(
            "customized_run.html", distance=route_length)
    else:
        print(state)
        return render_template("error.html")
    