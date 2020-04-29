from jax import grad, jit
import pytest


def f(x, y):
    return x * 2.0 + y * 3.0


def test_jax():
    gf = jit(grad(f, (0, 1)))
    grads = gf(1.0, 1.0)
    assert float(grads[0]) == pytest.approx(2.0)
    assert float(grads[1]) == pytest.approx(3.0)


test_jax()
