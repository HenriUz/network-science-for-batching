import numpy as np

from process.dataset import Problem
from process.graph import with_fast_builder
from scipy.sparse import csr_array

def _build_common_items(problem: Problem):
    # Number of items in each order to build the sparse matrix.
    lengths = [len(order) for order in problem.orders]

    # The rows of the matrix are the orders (with the ID repeated for each item they contain), and the columns are the items (repeated across different orders).
    rows = np.repeat(np.arange(problem.o), lengths)
    cols = np.fromiter(
        (item for order in problem.orders for item in order),
        dtype=np.int32,
        count=sum(lengths),
    )
    
    # Each non-zero entry in the matrix is equal to 1.
    data = np.ones(len(rows), dtype=np.int32)

    # Create a binary `order X item` matrix, indicating whether the item is included in the order.
    M = csr_array((data, (rows, cols)), shape=(problem.o, problem.i))

    # Multiplies the matrix by its transpose. The result is a matrix of the same dimensions as the original, `order X order`, where each entry indicates how many items they have in common.
    C = (M @ M.T).tocoo()

    mask = C.row < C.col
    return sorted(list(zip(C.row[mask].tolist(), C.col[mask].tolist(), C.data[mask].tolist())))

@with_fast_builder(_build_common_items)
def common_items(problem: Problem, origin: int, target: int) -> int:
    """
    Calculate the similarity between two orders by counting how many item IDs they have in common.

    This function has the "fast_builder" attribute, which is a function that takes a Problem instance and returns a list of edges based on item similarity. It is recommended to use fast_builder if the goal is to build the graph from scratch.

    Args:
        problem (Problem): Problem instance.
        origin (int): Origin order.
        target (int): Target order.
    
    Returns:
        similarity (int): Number of shared item IDs.
    """

    o_itens = problem.orders[origin].keys()
    t_itens = problem.orders[target].keys()
    return len(o_itens & t_itens)