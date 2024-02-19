from project import create_app
from flask_login import current_user  # Make sure to import current_user
from .models import Route, db
from .classes import Model, Run, Graph, RouteParser, MapBuilder

app = create_app()
app.app_context().push()


def process_runner_input(form_data, user_id=None):
    distance = float(form_data["distance"])
    gain = float(form_data["gain"])
    friendliness = float(form_data["friendliness"])
    graph = Graph(distance=distance, address=form_data["address"])
    run = Run(distance=form_data["distance"], address=form_data["address"], graph=graph)
    route_parser = RouteParser()
    start_of_path = route_parser.path_to_start(
        run.starting_node, run.model_root_node, graph.graph
    )
    model = Model()
    dist_mtrx = graph.get_distance_matrix()
    selected = model.build_model(
        dist_mtrx,
        graph.get_nodes(),
        run.model_root_node,
        distance,
        graph.get_elevation_matrix(),
        gain,
        graph.get_terrain_matrix(),
        friendliness,
    )

    route_length = route_parser.find_route_length(selected, dist_mtrx)
    tour_pairs = route_parser.create_ordered_tour_from_edges(selected)
    final_tour = route_parser.inject_intro_path(
        tour_pairs, start_of_path, run.model_root_node
    )

    map_builder = MapBuilder()
    coordinates = map_builder.generate_run_map(run, graph, final_tour)

    # Assuming user_id is passed as an argument; otherwise, you can obtain it from current_user.id if the user is logged in
    if user_id is None and current_user.is_authenticated:
        user_id = current_user.id

    route = Route(
        coordinates=coordinates,
        distance=round(route_length / 1609.34, 2),
        address=form_data["address"],
        user_id=user_id,  # Add the user_id here
    )
    db.session.add(route)
    db.session.commit()
    # return [run.address, run.distance, coordinates, round(route_length / 1609.34, 2)]
    return route.id
