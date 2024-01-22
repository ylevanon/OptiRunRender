import os
import uuid
import boto3
from bs4 import BeautifulSoup
import gurobipy as gp
from gurobipy import GRB
import folium
import networkx as nx
import osmnx as ox
import pandas as pd
import networkx as nx
import warnings
from collections import deque
from shapely.errors import ShapelyDeprecationWarning
from scipy.spatial.distance import cdist
from geopy.geocoders import Nominatim


warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning)

google_elevation_key = "AIzaSyBH6B7cw1HhLc62MLwhtgJevj4Lyty6ns8"

# Consider building a class called ModelConsumable that you can pass to build model.


class Model:
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Model, cls).__new__(cls)
        return cls._instance

    def build_model(self, dist, elevation, nodes, start, distance, max_elevation):
        # Variables: vars is the set of edges in the graph, seq is the set of nodes in the graph
        distance = distance * 1609.34
        m = gp.Model()
        vars = m.addVars(dist.keys(), obj=dist, vtype=GRB.BINARY, name="x")
        seq = m.addVars(nodes, obj=nodes, vtype=GRB.INTEGER, name="u")
        root = start

        # Constraints: At most, two edges incident to each city
        for i0 in nodes:
            m.addConstr(
                gp.quicksum([vars[i, j] for i, j in dist.keys() if i == i0])
                == gp.quicksum([vars[j, i] for j, i in dist.keys() if i == i0])
            )

        m.addConstr(gp.quicksum([vars[j, i] for j, i in dist.keys() if i == root]) == 1)

        m.addConstr(
            gp.quicksum([vars[i, j] * dist[i, j] for i, j in vars.keys()]) >= distance
        )

        m.addConstr(
            gp.quicksum(
                [
                    vars[i, j] * elevation[i, j]
                    for i, j in vars.keys()
                    if elevation[i, j] > 0
                ]
            )
            <= max_elevation
        )

        for i, j in dist.keys():
            if i != root and j != root:
                m.addConstr(seq[i] - seq[j] + len(nodes) * vars[i, j] <= len(nodes) - 1)

        m.addConstr(seq[root] == 1)
        m.addConstrs(seq[i] >= 2 for i in nodes if i != root)
        m.addConstrs(seq[i] <= len(nodes) for i in nodes if i != root)

        m._vars = vars
        m.setObjective(
            gp.quicksum([vars[i, j] * dist[i, j] for i, j in vars.keys()]), GRB.MINIMIZE
        )
        m.setParam("MIPGap", 0.15)
        m.optimize()

        # Retrieve solution
        vals = m.getAttr("x", vars)
        selected = gp.tuplelist((i, j) for i, j in vals.keys() if vals[i, j] > 0.5)
        return selected


class Run:
    def __init__(self, distance, address, graph: "Graph"):
        self.id = str(uuid.uuid4())  # Generate a unique ID
        self.distance = distance
        self.address = address
        self.coords = graph.coords
        self.starting_node = self.get_starting_node(graph.get_node_dataframe())
        self.model_root_node = self.get_model_root_node(
            graph.get_street_count_matrix(), graph.get_adjacency_matrix()
        )
        self.route = None

    def get_closest_coordinates_to_user(self, point, points):
        """
        Find the closest point from a list of points to a given point.

        Parameters:
        - point (tuple): The coordinates (x, y) of the target point.
        - points (list): List of points to search for the closest one.

        Returns:
        - get_closest_coordinates (tuple): The coordinates of the closest point.
        """
        return points[cdist([point], points).argmin()]

    def match_value(self, df, col1, x, col2):
        """
        Match a value x from col1 row to the corresponding value in col2.

        Parameters:
        - df (pd.DataFrame): The DataFrame containing the data.
        - col1 (str): The column name from which to match the value.
        - x: The value to match.
        - col2 (str): The column name to retrieve the matched value.

        Returns:
        - matched_value: The matched value from col2.
        """
        return df[df[col1] == x][col2].values[0]

    def split(a, n):
        """
        Split a list into n sublists.

        Parameters:
        - a (list): The list to be split.
        - n (int): The number of sublists.

        Returns:
        - generator: Generator of n sublists.
        """
        k, m = divmod(len(a), n)
        return (a[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)] for i in range(n))

    def get_lat_long(self):
        """
        Get latitude and longitude coordinates for a given address using Geopy.

        Parameters:
        - address (str): The address to geocode.

        Returns:
        - tuple: The (latitude, longitude) coordinates.
        """
        geolocator = Nominatim(user_agent="my_geocoder")
        location = geolocator.geocode(self.address)

        if location:
            lat, lon = location.latitude, location.longitude
            return lat, lon
        else:
            print(f"Could not find coordinates for address: {self.address}")
            return None

    def get_starting_node(self, node_df):
        """
        Find the closest node in the network to a given address.

        Parameters:
        - node_df (pd.DataFrame): DataFrame containing node information.
        - address (str): The target address.

        Returns:
        - start_node: The closest node to the given address.
        """
        coordinates = self.coords
        lat, lng = coordinates[0], coordinates[1]
        lat_lng_df = pd.DataFrame(
            {
                "x": [lat],
                "y": [lng],
            }
        )
        node_df["point"] = [(x, y) for x, y in zip(node_df["x"], node_df["y"])]
        lat_lng_df["point"] = [(x, y) for x, y in zip(lat_lng_df["x"], lat_lng_df["y"])]
        lat_lng_df["closest"] = [
            self.get_closest_coordinates_to_user(x, list(node_df["point"]))
            for x in lat_lng_df["point"]
        ]
        lat_lng_df["node from"] = [
            self.match_value(node_df, "point", x, "node from")
            for x in lat_lng_df["closest"]
        ]
        start_node = lat_lng_df["node from"].values.tolist()
        return start_node[0]

    def get_model_root_node(self, street_adj, node_adj):
        """
        Perform Breadth-First Search to find a suitable starting node.

        Parameters:
        - street_adj (dict): Dictionary representing the street count matrix.
        - node_adj (dict): Dictionary representing the adjacency matrix.
        - start_node: The initial node to start the search.

        Returns:
        - suitable_start_node: A suitable starting node for the route.
        """
        if street_adj[self.starting_node] >= 4.0:
            return self.starting_node

        queue = deque([self.starting_node])
        visited = set([self.starting_node])

        while queue:
            current_node = queue.popleft()

            if street_adj[current_node] >= 4.0:
                return current_node

            for neighbor in node_adj[current_node]:
                if neighbor not in visited:
                    queue.append(neighbor)
                    visited.add(neighbor)

        # If no suitable starting node is found, return None or handle accordingly
        return None


class Graph:
    def __init__(self, distance, address):
        multiplier = 1609.34 / 3
        self.graph, self.coords = ox.graph_from_address(
            address, distance * multiplier, network_type="walk", return_coords=True
        )
        self.graph = ox.add_node_elevations_google(
            self.graph, api_key=google_elevation_key
        )
        self.nodes = self.get_nodes()
        self.node_df = self.get_node_dataframe()
        self.edge_df = self.get_edge_dataframe()
        self.dist_mtrx = self.get_distance_matrix()
        self.adj_mtrx = self.get_adjacency_matrix()
        self.street_cnt_mtrx = self.get_street_count_matrix()
        self.elv_mtrx = self.get_elevation_matrix()

    def get_nodes(self):
        """
        Get a list of nodes in the OSMnx graph.

        Parameters:
        - G (networkx.Graph): The OSMnx graph.

        Returns:
        - nodes (list): List of nodes in the graph.
        """
        return list(self.graph.nodes(data=False))

    def get_node_dataframe(self):
        """
        Create a DataFrame representing the nodes in the OSMnx graph.

        Parameters:
        - G (networkx.Graph): The OSMnx graph.

        Returns:
        - node_df (pd.DataFrame): DataFrame containing node information.
        - nodes (list): List of nodes in the graph.
        """
        # Extract raw node data from the graph, create DataFrame, and expand 'codes' column

        node_df = pd.DataFrame(self.graph.nodes(data=True)).set_axis(
            ["node from", "codes"], axis=1
        )
        node_df = pd.concat([node_df, node_df["codes"].apply(pd.Series)], axis=1)
        node_df = node_df.drop(columns="codes").rename(columns={"x": "y", "y": "x"})
        return node_df

    def get_edge_dataframe(self):
        """
        Create a DataFrame representing the edges in the OSMnx graph.

        Parameters:
        - G (networkx.Graph): The OSMnx graph.

        Returns:
        - database (pd.DataFrame): DataFrame containing edge information.
        """
        edges = list(self.graph.edges(data=True))
        edge_df = pd.DataFrame(edges, columns=["node from", "node too", "codes"])
        edge_df = pd.concat([edge_df, edge_df["codes"].apply(pd.Series)], axis=1).drop(
            columns="codes"
        )
        return edge_df

    def get_distance_matrix(self):
        """
        Create a distance matrix based on the edge database.

        Parameters:
        - database (pd.DataFrame): DataFrame containing edge information.

        Returns:
        - dist (dict): Dictionary representing the distance matrix.
        """
        copy_edge_df = self.edge_df.copy(deep=True)
        copy_edge_df["from too"] = list(
            zip(copy_edge_df["node from"], copy_edge_df["node too"])
        )
        dist_mtrx = dict(zip(copy_edge_df["from too"], copy_edge_df["length"]))
        return dist_mtrx

    def get_adjacency_matrix(self):
        """
        Create an adjacency matrix based on the edge dataframe.

        Parameters:
        - database (pd.DataFrame): DataFrame containing edge information.

        Returns:
        - adj (dict): Dictionary representing the adjacency matrix.
        """
        Gz = nx.from_pandas_edgelist(
            self.edge_df, "node from", "node too", create_using=nx.DiGraph()
        )
        adj_mtrx = nx.adjacency_matrix(Gz)
        adj_mtrx = nx.convert.to_dict_of_lists(Gz)
        return adj_mtrx

    def get_street_count_matrix(self):
        """
        Create a street count matrix based on the adjacency matrix.

        Parameters:
        - adj_matrix (dict): Dictionary representing the adjacency matrix.

        Returns:
        - street_dict (dict): Dictionary representing the street count matrix.
        """
        street_mtrx = {x: len(self.adj_mtrx[x]) for x in self.adj_mtrx}
        return street_mtrx

    def get_elevation_matrix(self):
        """
        Create a dictionary with the elevation difference for each edge in the graph.

        Returns:
        - elevation_diff_dict (dict): Dictionary with edge tuples as keys and elevation differences as values.
        """
        # Extract elevation data from node DataFrame
        elevation_data = {
            row["node from"]: row["elevation"] for index, row in self.node_df.iterrows()
        }

        # Calculate elevation differences for each edge
        elevation_diff_dict = {}
        for index, row in self.edge_df.iterrows():
            from_node = row["node from"]
            to_node = row["node too"]
            elevation_diff = elevation_data[to_node] - elevation_data[from_node]
            elevation_diff_dict[(from_node, to_node)] = elevation_diff

        return elevation_diff_dict


class RouteParser:
    def path_to_start(self, start_node, end_node, G):
        """
        Find the shortest path from start_node to end_node in the OSMnx graph.

        Parameters:
        - start_node: The starting node.
        - end_node: The destination node.
        - G (networkx.Graph): The OSMnx graph.

        Returns:
        - list: List representing the shortest path from start_node to end_node.
        """
        if start_node == end_node:
            return []
        else:
            return nx.shortest_path(G, start_node, end_node)

    def find_route_length(self, selected_edges, dist_dict):
        """
        Calculate the total length of a route based on selected edges.

        Parameters:
        - selected_edges (list): List of edges selected for the route.
        - dist_dict (dict): Dictionary representing the distance matrix.

        Returns:
        - float: Total length of the route.
        """
        route_length = 0
        for i in selected_edges:
            route_length += dist_dict[i[0], i[1]]
        return route_length

    def convert_node_ids_to_coordinates(self, G, tour):
        """
        Convert node IDs in a tour to latitude and longitude coordinates.

        Parameters:
        - G (networkx.Graph): The OSMnx graph.
        - tour (list): List of node IDs representing the tour.

        Returns:
        - list: List of (latitude, longitude) coordinates representing the tour.
        """
        tour_coordinates = [(G.nodes[node]["y"], G.nodes[node]["x"]) for node in tour]
        return tour_coordinates

    def create_ordered_tour_from_edges(self, selected_edges):
        """
        Create an ordered tour from a list of selected edges.

        Parameters:
        - G (networkx.Graph): The OSMnx graph.
        - selected_edges (list): List of edges selected for the route.

        Returns:
        - list: List of tuples representing the ordered tour.
        """
        edge_list = [(edge[0], edge[1]) for edge in selected_edges]
        input_dict = dict(edge_list)
        start_point = edge_list[0][0]

        tour_list = []
        for _ in range(len(edge_list)):
            tour_list.append((start_point, input_dict[start_point]))
            start_point = input_dict[start_point]

        return tour_list

    def inject_intro_path(self, ord_tour, intro, end):
        """
        Create the final tour by incorporating introduction and end nodes.

        Parameters:
        - ord_tour (list): List of tuples representing the ordered tour.
        - intro (list): List of introduction nodes.
        - end: End node.

        Returns:
        - list: List representing the final tour.
        """
        final_tour = [step[0] for step in ord_tour]
        final_tour.append(final_tour[0])

        if len(intro) > 0:
            final_tour = final_tour[1:]
            while final_tour[-1] != end:
                last_node = final_tour.pop(0)
                final_tour.append(last_node)
            final_tour.insert(0, end)

            for i in range(len(intro) - 2, -1, -1):
                final_tour.append(intro[i])

        return final_tour


class MapBuilder:
    def generate_run_map(self, run, graph, final_tour):
        test_map = folium.Map(
            location=run.coords,
            zoom_start=200,
            width="100%",
            height="100%",
        )
        iframe = folium.IFrame(run.address, width=50, height=50)

        popup = folium.Popup(iframe, max_width=350)

        folium.Marker(run.coords, popup=popup).add_to(test_map)
        test_map = self.plot_run_on_map(graph.graph, final_tour, test_map)
        test_map.save("/app/project/templates/generated_route.html")
        # Read the HTML file
        soupy_map = BeautifulSoup(test_map.get_root().render(), "html.parser")

        with open(
            "/app/project/templates/customized_run.html", "r", encoding="utf-8"
        ) as html_file:
            html_content = html_file.read()

        # Parse the HTML content
        soup = BeautifulSoup(html_content, "html.parser")

        # Find the element with the specified id
        custom_run_div = soup.find("div", {"id": "custom-run"})

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
            # print(custom_run_div.prettify())  # Print the element's HTML
            # Save the modified HTML back to a file
            with open(
                "/app/project/templates/customized_run.html", "w", encoding="utf-8"
            ) as modified_file:
                modified_file.write(str(soup))
                s3 = boto3.client("s3")
                bucket_name = os.environ.get("S3_BUCKET_NAME")
                with open("/app/project/templates/customized_run.html", "rb") as f:
                    s3.upload_fileobj(f, bucket_name, "customized_run.html")
                modified_file.close()
                html_file.close()

        else:
            print("Element with id 'custom-run' not found.")

    def plot_run_on_map(self, G, lst, fol_map):
        """
        Create a Folium map of the route.

        Parameters:
        - G (networkx.Graph): The OSMnx graph.
        - lst (list): List of node IDs representing the route.
        - fol_map: The Folium map to which the route will be added.

        Returns:
        - folium.Map: The Folium map with the added route.
        """
        return ox.plot_route_folium(
            G, lst, route_map=fol_map, color="blue", weight=5, opacity=0.7
        )
