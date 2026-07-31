from scao_live.math_utils import add_one

def test_add_one():
    assert add_one(5) == 6

def test_add_one_zero():
    assert add_one(0) == 1
