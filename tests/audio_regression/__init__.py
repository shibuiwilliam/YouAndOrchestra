"""Audio regression tests.

These tests render representative pieces, extract acoustic features,
and compare to stored baselines. They detect unintended acoustic drift
when code changes occur.

Marked with ``@pytest.mark.audio_regression`` and run weekly in CI
(too slow for every PR).
"""
