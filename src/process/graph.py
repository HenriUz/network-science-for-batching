from collections.abc import Callable
from typing import Any

import igraph as ig

from process.dataset import Problem


class Graph:
    def __init__(
        self,
        problem: Problem,
        similarity: Callable[[Problem], list[tuple[int, int, Any]]],
    ) -> None:
        self.problem = problem

        edges = similarity(problem)
        self.g = ig.Graph(
            n=problem.o,
            edges=[(o, t) for o, t, _ in edges],
            edge_attrs={"weight": [w for _, _, w in edges]},
        )
