import sys

from methods.similarity import common_aisles, common_items
from process.dataset import Problem
from process.metrics import Metrics
from process.graph import Graph
from random import seed

def main(instance_path: str, use: int) -> Problem:
    problem = Problem(instance_path)
    graph = Graph(problem, common_aisles)

    match use:
        case 0:
            print("Calculando métricas da rede...")
            Metrics(graph).save_metrics_csv("../results/metrics.csv")
            print("Métricas calculadas!")
        case 1:
            print(graph.g.get_adjacency_sparse(attribute="weight"))

    return problem

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Incorrect number of arguments.")
        print("Use: python main.py <instance_path> <use (0: metrics, 1: solver)>")
        exit(1)
    
    main(sys.argv[1], int(sys.argv[2]))