def exponential_backoff(attempt: int, base: float = 0.2, cap: float = 5.0) -> float:
    if attempt < 0:
        raise ValueError("attempt must be non-negative")
    return min(cap, base * (2 ** attempt))
