import pytest
from ingestion.bcb.cli import main
from ingestion.bcb.errors import IngestionError
from ingestion.bcb.handler import handler
from ingestion.bcb.pipeline import EntityRun, RunResult


def _failed() -> RunResult:
    return RunResult(
        entities=[
            EntityRun(
                entity="ChavesPix",
                ok=False,
                rows_written=0,
                rows_by_month={},
                watermark=None,
                error="boom",
            )
        ]
    )


def _ok() -> RunResult:
    return RunResult(
        entities=[
            EntityRun(
                entity="ChavesPix",
                ok=True,
                rows_written=4,
                rows_by_month={202610: 4},
                watermark=202610,
            )
        ]
    )


def test_ingest_returns_nonzero_when_an_entity_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingestion.bcb.cli.run", lambda *_args, **_kwargs: _failed())
    assert main(["ingest"]) == 1


def test_backfill_requires_a_range() -> None:
    with pytest.raises(SystemExit):
        main(["backfill"])


def test_handler_raises_with_the_result_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingestion.bcb.handler.run", lambda *_args, **_kwargs: _failed())
    with pytest.raises(IngestionError, match="ChavesPix"):
        handler({"mode": "ingest"}, None)


def test_handler_returns_row_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("ingestion.bcb.handler.run", lambda *_args, **_kwargs: _ok())
    body = handler({"mode": "backfill", "start": 202610, "end": 202610}, None)
    assert body["ok"] is True
    assert body["entities"][0]["rows_written"] == 4
    assert body["entities"][0]["watermark"] == 202610
