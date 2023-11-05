# from __future__ import print_function  # In python 2.7
# import os
# import osmnx as ox
# from flask import Flask, render_template, request, redirect, url_for
# import folium
# from project.tasks import process_runner_input



# @app.route("/")
# def index():
#     return render_template("index.html")


# @app.route("/about")
# def about():
#     return render_template("about.html")


# @app.route("/route")
# def route():
#     return render_template("route.html")


# @app.route("/input", methods=["GET", "POST"])
# def input():
#     if request.method == "POST":
#         form_data = request.form
#         job = q.enqueue(process_runner_input, form_data)
#         return redirect(url_for("loading", task_id=job.id))
#     return render_template("input.html")


# @app.route("/loading/<task_id>")
# def loading(task_id):
#     job = q.fetch_job(task_id)
#     status = job.get_status()
#     if status in ["queued", "started", "deferred", "failed"]:
#         return render_template("loading_screen.html", result=status, refresh=True)
#     elif status == "finished":
#         print(job.get_status())
#         result = job.result
#         generated_run_html, distance = result  # Extract distance and generated_run_html
#         return render_template(
#             "route.html", distance=distance, generated_run_html=generated_run_html
#         )


# if __name__ == "__main__":
#     port = os.environ.get("PORT", 5000)
#     app.run(debug=False, host="0.0.0.0", port=port)
