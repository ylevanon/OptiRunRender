import unittest
import osmnx as ox
import pandas as pd
import networkx as nx
from project.models import Graph  # Import your Graph class here


class TestGraph(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up a Graph instance to test
        cls.distance = 1  # Example distance
        cls.address = "1600 Amphitheatre Parkway, Mountain View, CA"
        cls.graph = Graph(cls.distance, cls.address)

    def test_get_nodes(self):
        nodes = self.graph.get_nodes()
        self.assertIsInstance(nodes, list)
        self.assertGreater(len(nodes), 0)

    def test_get_node_dataframe(self):
        node_df = self.graph.get_node_dataframe()
        self.assertIsInstance(node_df, pd.DataFrame)
        self.assertGreater(len(node_df), 0)

    def test_get_edge_dataframe(self):
        edge_df = self.graph.get_edge_dataframe()
        self.assertIsInstance(edge_df, pd.DataFrame)
        self.assertGreater(len(edge_df), 0)

    def test_get_distance_matrix(self):
        dist_mtrx = self.graph.get_distance_matrix()
        elv_mtrx = self.graph.get_elevation_matrix()
        self.assertIsInstance(dist_mtrx, dict)
        self.assertGreater(len(dist_mtrx), 0)
        print(len(dist_mtrx))
        print(len(elv_mtrx))
        print(dist_mtrx.keys())
        print(elv_mtrx.keys())

    def test_get_adjacency_matrix(self):
        adj_mtrx = self.graph.get_adjacency_matrix()
        self.assertIsInstance(adj_mtrx, dict)
        self.assertGreater(len(adj_mtrx), 0)

    def test_get_street_count_matrix(self):
        street_cnt_mtrx = self.graph.get_street_count_matrix()
        self.assertIsInstance(street_cnt_mtrx, dict)
        self.assertGreater(len(street_cnt_mtrx), 0)


if __name__ == "__main__":
    unittest.main()
