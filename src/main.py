import sys

from methods.similarity import common_items
from process.dataset import Problem
from process.graph import Graph
from random import seed

def main(instance_path: str) -> Problem:
    problem = Problem(instance_path)
    graph = Graph(problem, common_items)

    print(graph.g.get_adjacency_sparse(attribute="weight"))

    return problem

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Incorrect number of arguments.")
        print("Use: python main.py <instance_path>")
        exit(1)
    
    main(sys.argv[1])