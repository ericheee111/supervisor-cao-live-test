from scao_live.paths import safe_join

def test_basic_join():
    assert safe_join('/base', 'a', 'b') == '/base/a/b'

def test_single_part():
    assert safe_join('/base', 'x') == '/base/x'
