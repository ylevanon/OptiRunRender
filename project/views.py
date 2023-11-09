import os
from flask import Blueprint, render_template, redirect, request, url_for
# from celery.result import AsyncResult
import boto3
from bs4 import BeautifulSoup
from rq import Queue
from .tasks import process_runner_input
from .models import Run, Graph, MapBuilder
from project.worker import conn
main = Blueprint('main', __name__)
q = Queue(connection=conn)

@main.route("/")
def index():
    return render_template("index.html")


@main.route("/about")
def about():
    return render_template("about.html")

# @main.route("/input", methods=["GET", "POST"])
# def input():
#     if request.method == "POST":
#         form_data = request.form
#         task = process_runner_input.delay(form_data)
#         return redirect(url_for("main.loading", task_id=task))
#     return render_template("input.html")

@main.route("/input", methods=["GET", "POST"])
def input():
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
        return redirect(url_for("main.customized_run"))
    else:
        print(status)
        return render_template("error.html")

@main.route("/customized_run")
def customized_run():
    s3 = boto3.client('s3')
    bucket_name = os.environ.get('S3_BUCKET_NAME')
    my_bucket = s3.Bucket(bucket_name)
    os.remove("/tmp/<file_name>.txt")
    # file_path = '/app/project/templates/customized_run.html'  # Replace with your desired file path
    # with open(file_path, 'wb') as f:
    my_bucket.download_file('customized_run.html', 'project/templates/customized_run.html')
    return render_template("customized_run.html")


# @main.route("/loading/<task_id>")
# def loading(task_id):
#     task = AsyncResult(task_id)
#     state = task.state
#     if state =="STARTED" or state=="PENDING":
#         return render_template("loading.html", result=state, refresh=True)
#     elif state == "SUCCESS":
#         print(task.status)
#         result = task.result
#         print(result)
#         print(len(result))
#         address = result[0]
#         distance = float(result[1])
#         tour = result[2]
#         route_length = result[3]
#         graph = Graph(distance=distance, address=address)
#         run = Run(distance=distance, address=address, graph=graph)
#         map_builder = MapBuilder()
#         map_builder.generate_run_map(run, graph, tour)
#         # generated_run_html, distance= result  # Extract distance and generated_run_html
#         # return render_template(
#         #     "customized_run.html", distance=distance)

#         return render_template(
#             "customized_run.html", distance=route_length)
#     else:
#         print(state)
#         return render_template("error.html")
    