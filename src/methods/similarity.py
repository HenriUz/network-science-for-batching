import numpy as np

from process.dataset import Problem
from process.graph import with_fast_builder
from scipy.sparse import csr_array

def _build_common_items(problem: Problem) -> list[tuple[int, int, int]]:
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

def _build_common_aisles(problem: Problem) -> list[tuple[int, int, float]]:
    # --- Order x Item matrix (binary: does order o contain item i?) ---
    order_lengths = [len(order) for order in problem.orders]
    rows_o = np.repeat(np.arange(problem.o), order_lengths)
    cols_o = np.fromiter(
        (item for order in problem.orders for item in order),
        dtype=np.int32,
        count=sum(order_lengths),
    )
    data_o = np.ones(len(rows_o), dtype=np.int32)
    M_o = csr_array((data_o, (rows_o, cols_o)), shape=(problem.o, problem.i))

    # --- Aisle x Item matrix (binary: does aisle a contain item i?) ---
    aisle_lengths = [len(aisle) for aisle in problem.aisles]
    rows_a = np.repeat(np.arange(problem.a), aisle_lengths)
    cols_a = np.fromiter(
        (item for aisle in problem.aisles for item in aisle),
        dtype=np.int32,
        count=sum(aisle_lengths),
    )
    data_a = np.ones(len(rows_a), dtype=np.int32)
    M_a = csr_array((data_a, (rows_a, cols_a)), shape=(problem.a, problem.i))

    # --- Order x Aisle matrix ---
    # M_o @ M_a.T gives, for each (order, aisle) pair, how many items the order has that belong to that aisle. We only care about presence, so binarize it: 1 if the order has at least one item from the aisle, 0 otherwise.
    M_oa = (M_o @ M_a.T).tocsr()
    M_oa.eliminate_zeros()
    M_oa.data[:] = 1

    # How many distinct aisles each order touches (row sums of the binary matrix).
    degree = np.asarray(M_oa.sum(axis=1)).flatten()

    # --- Order x Order intersection matrix ---
    # C[o, d] = number of aisles orders o and d have in common.
    C = (M_oa @ M_oa.T).tocoo()

    mask = C.row < C.col
    o, d, intersection = C.row[mask], C.col[mask], C.data[mask]

    # Jaccard: |A ∩ B| / |A ∪ B|, with |A ∪ B| = |A| + |B| - |A ∩ B|.
    union = degree[o] + degree[d] - intersection
    jaccard = intersection / union

    return sorted(zip(o.tolist(), d.tolist(), jaccard.tolist()))

@with_fast_builder(_build_common_aisles)
def common_aisles(problem: Problem, origin: int, target: int) -> float:
    """
    Calculate the similarity between two orders based on the number of aisles they have in common, weighted by the Jaccard (|A ∩ B| / |A ∪ B|).

    This function has the "fast_builder" attribute, which is a function that takes a Problem instance and returns a list of edges based on item similarity. It is recommended to use fast_builder if the goal is to build the graph from scratch.

    Args:
        problem (Problem): Problem instance.
        origin (int): Origin order.
        target (int): Target order.
    
    Returns:
        similarity (float): Jaccard similarity between the two orders.
    """

    o_aisles = set()
    t_aisles = set()

    for aisle_idx, aisle in enumerate(problem.aisles):
        for item in problem.orders[origin]:
            if item in aisle:
                o_aisles.add(aisle_idx)
                break

        for item in problem.orders[target]:
            if item in aisle:
                t_aisles.add(aisle_idx)
                break

    union = len(o_aisles | t_aisles)
    if union == 0:
        return 0.0

    return len(o_aisles & t_aisles) / union