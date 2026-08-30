"""Cálculo e exportação de métricas para a rede de pedidos."""

import csv
import json
from pathlib import Path
from typing import Any

import numpy as np

from process.graph import Graph


class Metrics():
    """Calcula métricas estruturais e ponderadas de uma instância de ``Graph``."""

    def __init__(self, graph: Graph) -> None:
        self.graph = graph

    @staticmethod
    def _distribution_metrics(values: list[float]) -> dict[str, float | None]:
        """Resume uma distribuição; valores ausentes são representados por ``None``."""
        if not values:
            return {
                "min": None,
                "mean": None,
                "max": None,
                "median": None,
                "std": None,
            }

        array = np.asarray(values, dtype=float)
        return {
            "min": float(np.min(array)),
            "mean": float(np.mean(array)),
            "max": float(np.max(array)),
            "median": float(np.median(array)),
            "std": float(np.std(array)),
        }

    def compute_metrics(self) -> dict[str, Any]:
        """Calcula e retorna as métricas da rede em um dicionário.

        A distância média e o diâmetro são calculados no maior componente, pois
        não há caminho entre vértices de componentes distintos. O valor da rede
        pela lei de Metcalfe é representado por ``n²``.
        """
        network = self.graph.g
        num_nodes = network.vcount()
        num_edges = network.ecount()
        degrees = [float(value) for value in network.degree()]
        components = network.connected_components()
        largest_component = components.giant() if num_nodes else network
        largest_component_size = largest_component.vcount()

        if largest_component_size > 1:
            average_distance = float(largest_component.average_path_length())
            diameter = int(largest_component.diameter())
        else:
            average_distance = 0.0
            diameter = 0

        local_clustering = [
            float(value)
            for value in network.transitivity_local_undirected(mode="zero")
        ]
        articulation_points = list(network.articulation_points())
        bridges = [
            tuple(network.es[edge_id].tuple)
            for edge_id in network.bridges()
        ]
        isolated_nodes = [
            vertex.index
            for vertex in network.vs
            if vertex.degree() == 0
        ]

        weights = (
            [float(value) for value in network.es["weight"]]
            if num_edges and "weight" in network.es.attributes()
            else []
        )
        strengths = (
            [float(value) for value in network.strength(weights="weight")]
            if "weight" in network.es.attributes()
            else [0.0] * num_nodes
        )

        return {
            "num_nodes": num_nodes,
            "num_edges": num_edges,
            "density": float(network.density(loops=False)),
            "average_degree": float(np.mean(degrees)) if degrees else 0.0,
            "average_distance": average_distance,
            "diameter": diameter,
            "metcalfe_value": num_nodes**2,
            "num_components": len(components),
            "articulation_points": articulation_points,
            "num_articulation_points": len(articulation_points),
            "bridges": bridges,
            "num_bridges": len(bridges),
            "local_clustering": local_clustering,
            "average_clustering": float(
                network.transitivity_avglocal_undirected(mode="zero")
            ) if num_nodes else 0.0,
            "global_clustering": float(
                network.transitivity_undirected(mode="zero")
            ) if num_nodes else 0.0,
            "largest_component_size": largest_component_size,
            "isolated_nodes": isolated_nodes,
            "num_isolated_nodes": len(isolated_nodes),
            "weight": self._distribution_metrics(weights),
            "strength": self._distribution_metrics(strengths),
        }

    def save_metrics_csv(self, output_path: str | Path) -> dict[str, Any]:
        """Calcula as métricas e grava uma linha em CSV no caminho informado."""
        metrics = self.compute_metrics()
        csv_path = Path(output_path)
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        row = {
            key: json.dumps(value) if isinstance(value, (dict, list, tuple)) else value
            for key, value in metrics.items()
        }
        with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=row.keys())
            writer.writeheader()
            writer.writerow(row)

        return metrics
