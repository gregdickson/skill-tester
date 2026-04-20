from app.engine.value import Value


class SGD:
    """Stochastic Gradient Descent for Value parameters.

    Performs weight updates using gradients computed via finite differences
    (numerical gradient estimation from LLM-as-judge scores).
    """

    def __init__(self, parameters: list[Value], lr: float = 0.01):
        self.parameters = parameters
        self.lr = lr

    def step(self) -> dict[str, dict]:
        """Update all parameters. Returns dict of {label: {before, after, grad}}."""
        updates = {}
        for p in self.parameters:
            before = p.data
            p.data -= self.lr * p.grad
            p.clamp(0.0, 1.0)
            updates[p.label] = {
                "before": round(before, 4),
                "after": round(p.data, 4),
                "grad": round(p.grad, 4),
            }
        return updates

    def zero_grad(self) -> None:
        for p in self.parameters:
            p.grad = 0.0
