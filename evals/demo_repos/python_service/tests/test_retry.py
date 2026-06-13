from app.utils.retry import exponential_backoff


def test_exponential_backoff_is_capped() -> None:
    assert exponential_backoff(10, base=1.0, cap=5.0) == 5.0
