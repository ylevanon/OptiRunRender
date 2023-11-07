from bs4 import BeautifulSoup
from flask import Blueprint, render_template, redirect, request, url_for
from celery.result import AsyncResult
from .tasks import process_runner_input

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
        test_map, distance= result  # Extract distance and test_map
        # Read the HTML file
        soupy_map = BeautifulSoup(test_map.get_root().render(), "html.parser")

        with open('/app/project/templates/customized_run.html', 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()

        # Parse the HTML content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find the element with the specified id
        custom_run_div = soup.find('div', {'id': 'custom-run'})

        # Check if the element was found
        if custom_run_div:
            # Extract the element's contents or attributes
             # Print the element's HTML
             # Convert the Folium map to an HTML string
            # folium_map_html = test_map.get_root().render()
            # for i in range(10):
            #     print("*")
            # Set the innerHTML of the custom_run_div to the Folium map HTML
            custom_run_div.clear()
            custom_run_div.append(soupy_map)
            # for i in range(10):
            #     print("*")
            print(custom_run_div.contents)
            #print(custom_run_div.prettify())  # Print the element's HTML
            # Save the modified HTML back to a file
            with open('/app/project/templates/customized_run.html', 'w', encoding='utf-8') as modified_file:
                modified_file.write(str(soup))
                html_file.close()
                modified_file.close()

        else:
            print("Element with id 'custom-run' not found.")
        return render_template(
            "customized_run.html", distance=distance)
    else:
        print(state)
        return render_template("error.html")
    