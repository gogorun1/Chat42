from app.services.rate_limiter import RateLimiter


def test_rate_limiter_blocks_after_limit() -> None:
    now = [100.0]
    limiter = RateLimiter(limit=2, window_seconds=60, clock=lambda: now[0])

    assert limiter.allow(42)
    assert limiter.allow(42)
    assert not limiter.allow(42)


def test_rate_limiter_resets_after_window() -> None:
    now = [100.0]
    limiter = RateLimiter(limit=1, window_seconds=60, clock=lambda: now[0])

    assert limiter.allow(42)
    now[0] = 160.0

    assert limiter.allow(42)


def test_rate_limiter_tracks_users_separately() -> None:
    limiter = RateLimiter(limit=1, window_seconds=60, clock=lambda: 100.0)

    assert limiter.allow(42)
    assert limiter.allow(43)
