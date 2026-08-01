from scao_live.int_utils import parse_int

import pytest

def test_basic():
    assert parse_int('42') == 42

def test_zero():
    assert parse_int('0') == 0

def test_negative():
    assert parse_int('-1') == -1

def test_empty_raises():
    with pytest.raises(ValueError):
        parse_int('')
