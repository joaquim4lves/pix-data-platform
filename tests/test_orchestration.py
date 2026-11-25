"""Unit tests for the orchestration callables. They do not import Airflow."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import boto3
import httpx
import pytest
from ingestion.bcb.errors import IngestionError
from ingestion.bcb.pipeline import EntityRun, RunResult
from ingestion.bcb.store import ObjectStore
from moto import mock_aws
from orchestration.alerts import deadline_missed, notify, on_failure
from orchestration.cdc_flow import drain_cdc
from orchestration.dbt_cmd import BCB_FRESHNESS, BCB_SELECT, CDC_FRESHNESS, CDC_SELECT
from orchestration.ingest import bcb_entity_names, ingest_entity
from orchestration.maintenance import (
    QuarantinePresentError,
    SlotLagError,
    enforce_quarantine,
    enforce_slot_lag,
    read_slot_lag,
    slot_lag_limit,
)
from orchestration.windows import IngestPlan, logical_ano_mes, resolve_ingest_plan

BRAZIL = ZoneInfo("America/Sao_Paulo")


def _ok() -> RunResult:
    return RunResult(
        entities=[
            EntityRun(
                entity="ChavesPix",
                ok=True,
                rows_written=2,
                rows_by_month={202610: 2},
                watermark=202610,
            )
        ]
    )


def _failed() -> RunResult:
    return RunResult(
        entities=[
            EntityRun(
                entity="ChavesPix",
                ok=False,
                rows_written=0,
                rows_by_month={},
                watermark=None,
                error="olinda 500",
            )
        ]
    )


class _Rows:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self._row = row

    def fetchone(self) -> tuple[object, ...] | None:
        return self._row


class _Conn:
    def __init__(self, row: tuple[object, ...] | None) -> None:
        self.row = row
        self.params: tuple[object, ...] | None = None

    def execute(self, _sql: str, params: tuple[object, ...]) -> _Rows:
        self.params = params
        return _Rows(self.row)


class _Response:
    def raise_for_status(self) -> None:
        return None


def test_scheduled_run_uses_the_watermark_window() -> None:
    plan = resolve_ingest_plan(
        conf={},
        run_type="scheduled",
        logical_date=datetime(2026, 11, 2, 10, 0, tzinfo=UTC),
    )
    assert plan == IngestPlan(mode="ingest")


def test_conf_range_is_a_backfill() -> None:
    plan = resolve_ingest_plan(
        conf={"start": "202011", "end": 202012, "lookback_months": 1},
        run_type="manual",
        logical_date=None,
    )
    assert plan == IngestPlan(mode="backfill", start=202011, end=202012)


def test_ano_mes_conf_is_one_month() -> None:
    plan = resolve_ingest_plan(
        conf={"ano_mes": "202401"},
        run_type="manual",
        logical_date=None,
    )
    assert plan == IngestPlan(mode="backfill", start=202401, end=202401)


def test_airflow_backfill_run_uses_the_sao_paulo_month() -> None:
    # 02:30 UTC on the 1st is still the previous evening in Sao Paulo.
    moment = datetime(2026, 3, 1, 2, 30, tzinfo=UTC)
    plan = resolve_ingest_plan(conf=None, run_type="backfill", logical_date=moment)
    assert plan.mode == "backfill"
    assert plan.start == plan.end == logical_ano_mes(moment)
    assert plan.start == 202602


def test_backfill_without_a_logical_date_fails() -> None:
    with pytest.raises(ValueError, match="logical date"):
        resolve_ingest_plan(conf={}, run_type="backfill", logical_date=None)


def test_half_open_conf_range_fails() -> None:
    with pytest.raises(ValueError, match="both start and end"):
        resolve_ingest_plan(conf={"start": "202011"}, run_type="manual", logical_date=None)


def test_entity_names_follow_the_ingestion_order() -> None:
    assert bcb_entity_names() == [
        "EstatisticasTransacoesPix",
        "TransacoesPixPorMunicipio",
        "ChavesPix",
    ]


def test_ingest_entity_passes_the_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(_settings: object, **kwargs: object) -> RunResult:
        captured.update(kwargs)
        return _ok()

    monkeypatch.setattr("orchestration.ingest.run", fake_run)
    body = ingest_entity("ChavesPix", IngestPlan(mode="ingest", lookback_months=3))
    assert body["ok"] is True
    assert captured["entities"] == ["ChavesPix"]
    assert captured["mode"] == "ingest"
    assert captured["lookback_months"] == 3


def test_ingest_entity_raises_when_the_pipeline_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("orchestration.ingest.run", lambda *_a, **_k: _failed())
    with pytest.raises(IngestionError):
        ingest_entity("ChavesPix", IngestPlan(mode="backfill", start=202011, end=202011))


def test_drain_returns_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Consumed:
        published = 4
        advanced_to = "0/1"

    class _Applied:
        deleted = 4
        failed = 0

    monkeypatch.setattr("orchestration.cdc_flow.consume", lambda *_a, **_k: _Consumed())
    monkeypatch.setattr("orchestration.cdc_flow.apply_queue", lambda *_a, **_k: _Applied())
    assert drain_cdc()["published"] == 4
    assert drain_cdc()["deleted"] == 4


def test_drain_fails_when_the_sink_leaves_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Consumed:
        published = 1
        advanced_to = None

    class _Applied:
        deleted = 0
        failed = 1

    monkeypatch.setattr("orchestration.cdc_flow.consume", lambda *_a, **_k: _Consumed())
    monkeypatch.setattr("orchestration.cdc_flow.apply_queue", lambda *_a, **_k: _Applied())
    with pytest.raises(RuntimeError, match="left 1"):
        drain_cdc()


def test_missing_slot_alerts_and_does_not_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr(
        "orchestration.maintenance.notify",
        lambda event, _msg: events.append(event),
    )
    conn = _Conn(None)
    report = read_slot_lag(conn, "pix_app_slot")
    assert conn.params == ("pix_app_slot",)
    payload = enforce_slot_lag(report)
    assert payload["exists"] is False
    assert events == ["slot_missing"]


def test_slot_lag_over_the_limit_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CDC_SLOT_LAG_BYTES", "100")
    monkeypatch.setattr("orchestration.maintenance.notify", lambda *_a, **_k: None)
    report = read_slot_lag(_Conn(("pix_app_slot", False, 250)), "pix_app_slot")
    assert report.lag_bytes == 250
    assert report.active is False
    with pytest.raises(SlotLagError):
        enforce_slot_lag(report)


def test_slot_lag_limit_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AIRFLOW_VAR_CDC_SLOT_LAG_BYTES", raising=False)
    monkeypatch.delenv("CDC_SLOT_LAG_BYTES", raising=False)
    assert slot_lag_limit() == 256 * 1024 * 1024


def test_empty_quarantine_is_success() -> None:
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="pix-test")
        store = ObjectStore(client, "pix-test")
        assert enforce_quarantine(store) == {"bucket": "pix-test", "keys": []}


def test_quarantine_objects_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("orchestration.maintenance.notify", lambda *_a, **_k: None)
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="pix-test")
        client.put_object(
            Bucket="pix-test",
            Key="quarantine/ChavesPix/ano_mes=202610/x.json",
            Body=b"{}",
        )
        store = ObjectStore(client, "pix-test")
        with pytest.raises(QuarantinePresentError):
            enforce_quarantine(store)


def test_notify_logs_without_a_webhook(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.delenv("AIRFLOW_ALERT_SLACK_WEBHOOK_URL", raising=False)
    with caplog.at_level("ERROR"):
        notify("task_failed", "bcb_pix_monthly.ingest_one failed")
    assert "task_failed" in caplog.text
    assert "webhook" not in caplog.text.lower()


def test_notify_posts_without_echoing_the_webhook(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(url: str, *, json: dict[str, str], timeout: float) -> _Response:
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout
        return _Response()

    monkeypatch.setenv("AIRFLOW_ALERT_SLACK_WEBHOOK_URL", "https://hooks.example/secret")
    monkeypatch.setattr(httpx, "post", fake_post)
    notify("slot_lag", "slot pix_app_slot lag_bytes=10")
    body = captured["json"]
    assert isinstance(body, dict)
    assert "secret" not in body["text"]
    assert captured["url"] == "https://hooks.example/secret"


def test_failure_and_deadline_callbacks_notify(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []
    monkeypatch.setattr("orchestration.alerts.notify", lambda event, _msg: events.append(event))

    class _Dag:
        dag_id = "maintenance"

    class _Ti:
        task_id = "slot_lag"

    on_failure({"dag": _Dag(), "task_instance": _Ti()})
    deadline_missed({"dag": _Dag()})
    assert events == ["task_failed", "deadline_missed"]


def test_selectors_name_the_marts_and_the_sources() -> None:
    assert "+fct_transacoes_mensal" in BCB_SELECT
    assert "+cur_pix_key" in CDC_SELECT
    assert "source:raw.chaves_pix" in BCB_FRESHNESS
    assert "source:raw.app_pix_disputes" in CDC_FRESHNESS
