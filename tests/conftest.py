import pytest


@pytest.fixture(autouse=True)
def no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep retry/backoff tests fast."""
    monkeypatch.setattr("app.ingestion.api_client.time.sleep", lambda _s: None)
