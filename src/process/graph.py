from collections.abc import Callable
from process.dataset import Problem
from typing import Optional

def with_fast_builder(fast_builder: Callable[[Problem], list[tuple[int, int, int]]]):
    """
    Attach an optimized builder to a similarity function. 
    
    Args:
        fast_builder (Callable[[Problem], list[tuple[int, int, int]]]): an optimized function that takes `Problem` as a parameter and returns the list of edges in the graph.
    """
    
    def decorator(func):
        func.fast_builder = fast_builder
        return func
    return decorator

class Graph():
    def __init__(self, problem: Problem, similarity: Callable[[Problem, int, int], any]) -> None:
        fast_builder = getattr(similarity, "fast_builder", None)

        if fast_builder is not None:
            self.edges = fast_builder(problem)
        else:
            n = problem.o
            self.edges = [
                (o, d, sim)
                for o in range(n)
                for d in range(o + 1, n)
                if (sim := similarity(problem, o, d)) != 0
            ]