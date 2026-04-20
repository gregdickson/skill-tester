class Value:
    """Scalar value with gradient storage.

    Adapted from Karpathy's micrograd. Used as a weight container for
    finite-difference gradient estimation with LLM-as-judge loss functions.
    """

    def __init__(self, data: float, label: str = ""):
        self.data = data
        self.grad = 0.0
        self.label = label

    def __repr__(self) -> str:
        return f"Value(data={self.data:.4f}, grad={self.grad:.4f}, label='{self.label}')"

    def __add__(self, other):
        other_val = other if isinstance(other, Value) else Value(other)
        return Value(self.data + other_val.data)

    def __mul__(self, other):
        other_val = other if isinstance(other, Value) else Value(other)
        return Value(self.data * other_val.data)

    def __sub__(self, other):
        other_val = other if isinstance(other, Value) else Value(other)
        return Value(self.data - other_val.data)

    def __truediv__(self, other):
        other_val = other if isinstance(other, Value) else Value(other)
        return Value(self.data / other_val.data)

    def __radd__(self, other):
        return self.__add__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def clamp(self, min_val: float = 0.0, max_val: float = 1.0) -> None:
        self.data = max(min_val, min(max_val, self.data))
