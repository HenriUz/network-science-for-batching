import os

class Problem():
    """
    Reads and processes the data contained in a dataset file.

    Attributes:
        o (int): Total number of orders in the dataset.
        i (int): Total number of items.
        a (int): Total number of available aisles.
        orders (list[dict[int, int]]): List containing dictionaries that represent the orders. Each dictionary lists an item along with its quantity.
        sorted_orders (list[tuple[int, int]]): List sorted in descending order by the number of items in each order. Each element is a tuple in the format (index, number of items).
        aisles (list[dict[int, int]]): List containing dictionaries that represent the aisles. Each dictionary lists an item along with its quantity in the aisle.
        lb (int): Lower bound.
        ub (int): Upper bound.
    """
    
    def __init__(self, instance_path: str) -> None:
        """
        Args:
            instance_path (str): Path to the instance.
        """

        try:
            with open(instance_path, "rb") as data:
                lines = data.readlines()
        
                first_line = lines[0].strip().split()
                self.o, self.i, self.a = int(first_line[0]), int(first_line[1]), int(first_line[2])

                self.orders = []
                for i in range(self.o):
                    order_line = lines[i + 1].strip().split()
                    order = {int(order_line[1 + k * 2]): int(order_line[2 + k * 2]) for k in range(int(order_line[0]))}
                    self.orders.append(order)

                self.sorted_orders = [(x, sum(d.values())) for x, d in enumerate(self.orders)]
                self.sorted_orders.sort(key = lambda i: i[1], reverse = True)

                self.aisles = []
                for i in range(self.a):
                    aisle_line = lines[i + 1 + self.o].strip().split()
                    aisle = {int(aisle_line[1 + k * 2]): int(aisle_line[2 + k * 2]) for k in range(int(aisle_line[0]))}
                    self.aisles.append(aisle)
                
                last_line = lines[self.o + self.a + 1].strip().split()
                self.lb, self.ub = int(last_line[0]), int(last_line[1])

        except FileNotFoundError:
            print(f"Error: file '{instance_path}' not found.")
            exit(1)
        except OSError as e:
            print(f"Error opening the file: {e}")
            exit(1)

    def objective_function(
        self,
        number_items: int,
        number_aisles: int
    ) -> float:
        """
        Calculates the value of the objective function and returns it. If either the lower bound or upper bound constraint is violated, or if `number_aisles` is 0, the return value will be 0. 

        Args:
            number_items (int): Number of items in the orders.
            number_aisles (int): Number of selected aisles.
        
        Returns:
            Objective (float): Value of the objective function.
        """
        
        if number_items < self.lb or number_items > self.ub or number_aisles == 0:
            return 0.0

        return number_items / number_aisles