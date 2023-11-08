from celery import shared_task
from celery.contrib.abortable import AbortableTask
from .models import Model, Run, Graph, RouteParser, MapBuilder

@shared_task(bind=True, base=AbortableTask, task_track_started=True)
def process_runner_input(self, form_data):
    distance = float(form_data["distance"])
    graph = Graph(distance=distance, address=form_data["address"])
    run = Run(distance=form_data["distance"], address=form_data["address"], graph=graph)
    route_parser = RouteParser()
    start_of_path = route_parser.path_to_start(
        run.starting_node, run.model_root_node, graph.graph
    )
    model = Model()
    dist_mtrx = graph.get_distance_matrix()
    selected = model.build_model(
        graph.get_distance_matrix(), graph.get_nodes(), run.model_root_node, distance
    )

    route_length = route_parser.find_route_length(selected, dist_mtrx)
    tour_pairs = route_parser.create_ordered_tour_from_edges(selected)
    final_tour = route_parser.inject_intro_path(
        tour_pairs, start_of_path, run.model_root_node
    )

    map_builder = MapBuilder()
    map_builder.generate_run_map(run, graph, final_tour)
    # return "customized_run.html", round(route_length / 1609.34, 2)
    return [run.address, run.route_length, final_tour, round(route_length / 1609.34, 2)]
