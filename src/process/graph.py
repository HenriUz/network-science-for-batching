import igraph as ig

from collections.abc import Callable
from process.dataset import Problem

def with_fast_builder(fast_builder: Callable[[Problem], list[tuple[int, int, int]]]):
    """
    Attach an optimized builder to a similarity function. 
    
    Args:
        fast_builder (Callable[[Problem], list[tuple[int, int, int]]]): An optimized function that takes "Problem" as a parameter and returns the list of edges in the graph.
    """
    
    def decorator(func):
        func.fast_builder = fast_builder
        return func
    return decorator

def build_edges(
    problem: Problem,
    similarity: Callable[[Problem, int, int], any]
) -> list[tuple[int, int, any]]:
    """
    Builds a list of edges in the format (origin, target, weight).
    
    The origin and target are the orders defined in "problem", and the weight is calculated according to the "similarity" function.

    If the "similarity" function has the “fast_builder” attribute, it will be taken into account

    Args:
        problem (Problem): Problem instance.
        similarity (Callable[[Problem], list[tuple[int, int, int]]]): A function that takes a "Problem" instance and two order IDs and returns the similarity between them.

    Returns:
        edges (list[tuple[int, int, any]]): List of edges.
    """

    fast_builder = getattr(similarity, "fast_builder", None)
    if fast_builder is not None:
        return fast_builder(problem)
    
    n = problem.o
    return [
        (o, t, sim)
        for o in range(n)
        for t in range(o + 1, n)
        if (sim := similarity(problem, o, t)) != 0.0
    ]

class Graph():
    def __init__(self, problem: Problem, similarity: Callable[[Problem, int, int], any]) -> None:
        self.problem = problem
        
        edges = build_edges(problem, similarity)
        self.g = ig.Graph(
            n = problem.o,
            edges = [(o, t) for o, t, _ in edges],
            edge_attrs = {"weight": [w for _, _, w in edges]}
        )