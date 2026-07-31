from scao_live.math_utils import add_one


def test_add_one_integer():
    # Integer case: add_one(n) == n + 1
    assert add_one(1) == 2
    assert add_one(5) == 6
    assert add_one(-3) == -2


def test_add_one_zero():
    # Zero case: add_one(0) == 1
    assert add_one(0) == 1
