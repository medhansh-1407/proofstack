def calculate_total(price: float, discount: float) -> float:
    """Calculate the final price after a fractional discount."""
    return price * (1 - discount)
