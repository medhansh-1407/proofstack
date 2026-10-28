from calculator import calculate_total


def test_no_discount():
    assert calculate_total(100, 0) == 100


def test_twenty_percent_discount():
    assert calculate_total(100, 0.2) == 80


def test_full_discount():
    assert calculate_total(100, 1) == 0
