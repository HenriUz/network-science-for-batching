import numpy as np
import numpy.typing as npt

from collections.abc import Callable
from process.dataset import Problem

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
        self.problem = problem
        
        fast_builder = getattr(similarity, "fast_builder", None)
        if fast_builder is not None:
            self.edges = fast_builder(problem)
        else:
            n = problem.o
            self.edges = [
                (o, d, sim)
                for o in range(n)
                for d in range(o + 1, n)
                if (sim := similarity(problem, o, d)) != 0.0
            ]
    
    def adj_matrix(self) -> npt.NDArray[any]:
        """
        Construct the adjacency matrix for the graph.

        Returns:
            matrix (NDArray[any]): Adjacency matrix.
        """
        
        if self.edges != []:
            edges = np.array(self.edges)
            
            origins = edges[:,0]
            targets = edges[:,1]
            sim     = edges[:,2]

            matrix = np.zeros((self.problem.o, self.problem.o), dtype=sim.dtype)
            matrix[origins, targets] = sim
            matrix[targets, origins] = sim
        else:
            matrix = np.zeros((self.problem.o, self.problem.o), dtype=np.int32)

        return matrix