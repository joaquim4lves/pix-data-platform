import json
from datetime import UTC, datetime

import boto3
import httpx
import pytest
from ingestion.bcb.client import OlindaClient, Page
from ingestion.bcb.entities import TRANSACOES
from ingestion.bcb.pipeline import run
from ingestion.bcb.settings import Settings
from ingestion.bcb.store import ObjectStore
from moto import mock_aws
from tests.samples import chaves_row, municipio_row, tx_row

NOW = datetime(2026, 11, 24, 15, tzinfo=UTC)


def _settings() -> Settings:
    return Settings(
        base_url="https://olinda.example",
        bucket="pix-test",
        region="us-east-1",
        access_key_id="testing",
        secret_access_key="testing",
        endpoint_url=None,
        lookback_months=3,
        page_size=100,
        timeout_seconds=120,
        max_retries=2,
        backoff_seconds=0,
    )


class FakeClient:
    def __init__(self, rows: dict[tuple[str, int], list[dict[str, object]]]) -> None:
        self.rows = rows
        self.calls: list[tuple[str, int]] = []

    def fetch_month(self, spec, month: int) -> list[Page]:
        self.calls.append((spec.name, month))
        found = self.rows.get((spec.name, month), [])
        body = json.dumps({"value": found}).encode()
        return [Page(body=body, rows=found, skip=0)]

    def close(self) -> None:
        return None


@pytest.fixture
def store():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="pix-test")
        yield ObjectStore(client, "pix-test")


def test_running_twice_yields_the_same_partitions(store: ObjectStore) -> None:
    rows = {
        ("EstatisticasTransacoesPix", 202609): [tx_row(AnoMes=202609, VALOR="1.00")],
        ("EstatisticasTransacoesPix", 202610): [
            tx_row(AnoMes=202610, VALOR="2.00", NATUREZA="P2P"),
            tx_row(AnoMes=202610, VALOR="4.00", NATUREZA="B2B", FORMAINICIACAO="DICT"),
        ],
    }
    client = FakeClient(rows)
    kwargs = {
        "settings": _settings(),
        "mode": "ingest",
        "entities": ["EstatisticasTransacoesPix"],
        "now": NOW,
        "client": client,
        "store": store,
    }
    first = run(**kwargs)
    table_a = store.read_partition("EstatisticasTransacoesPix", 202610)
    keys_a = store.list_keys("raw/bcb/EstatisticasTransacoesPix/")
    second = run(**kwargs)
    table_b = store.read_partition("EstatisticasTransacoesPix", 202610)
    keys_b = store.list_keys("raw/bcb/EstatisticasTransacoesPix/")

    assert first.ok and second.ok
    assert table_a.equals(table_b)
    assert keys_a == keys_b
    assert keys_a == [
        "raw/bcb/EstatisticasTransacoesPix/ano_mes=202609/part.parquet",
        "raw/bcb/EstatisticasTransacoesPix/ano_mes=202610/part.parquet",
    ]
    assert store.load_watermarks()["EstatisticasTransacoesPix"] == 202610
    assert table_b.column("FORMAINICIACAO").to_pylist() == ["DICT", "Nao disponivel"]


def test_open_month_is_stored_and_left_out_of_the_watermark(store: ObjectStore) -> None:
    rows = {
        ("TransacoesPixPorMunicipio", month): [municipio_row(AnoMes=month)]
        for month in (202609, 202610, 202611)
    }
    result = run(
        _settings(),
        mode="ingest",
        entities=["TransacoesPixPorMunicipio"],
        now=NOW,
        client=FakeClient(rows),
        store=store,
    )
    entity = result.entities[0]
    assert entity.ok
    assert entity.rows_by_month[202611] == 1
    assert entity.watermark == 202610
    assert store.load_watermarks()["TransacoesPixPorMunicipio"] == 202610
    table = store.read_partition("TransacoesPixPorMunicipio", 202611)
    assert table.column("Estado").to_pylist() == ["MARANHÃO"]


def test_bad_payload_is_quarantined_and_the_next_entity_still_runs(store: ObjectStore) -> None:
    rows = {
        ("EstatisticasTransacoesPix", 202610): [tx_row(VALOR="nope")],
        ("ChavesPix", 202610): [chaves_row()],
    }
    result = run(
        _settings(),
        mode="ingest",
        entities=["EstatisticasTransacoesPix", "ChavesPix"],
        now=NOW,
        client=FakeClient(rows),
        store=store,
    )
    failed, loaded = result.entities
    assert not failed.ok
    assert failed.watermark is None
    assert failed.quarantined_keys
    assert store.list_keys("raw/bcb/EstatisticasTransacoesPix/") == []
    saved = store._s3.get_object(Bucket="pix-test", Key=failed.quarantined_keys[0])
    assert b"nope" in saved["Body"].read()
    assert loaded.ok
    assert loaded.watermark == 202610
    ispb = store.read_partition("ChavesPix", 202610).column("ISPB").to_pylist()
    assert ispb == ["05938780"]


def test_empty_month_does_not_delete_an_existing_partition(store: ObjectStore) -> None:
    row = TRANSACOES.model.model_validate(tx_row())
    store.write_partition(TRANSACOES, 202610, [row])
    store.save_watermark("EstatisticasTransacoesPix", 202610, NOW)
    result = run(
        _settings(),
        mode="ingest",
        entities=["EstatisticasTransacoesPix"],
        now=NOW,
        client=FakeClient({}),
        store=store,
    )
    assert result.ok
    assert store.read_partition("EstatisticasTransacoesPix", 202610).num_rows == 1
    assert store.load_watermarks()["EstatisticasTransacoesPix"] == 202610


def test_stale_watermark_fetches_the_gap(store: ObjectStore) -> None:
    store.save_watermark("EstatisticasTransacoesPix", 202601, NOW)
    client = FakeClient({})
    run(
        _settings(),
        mode="ingest",
        entities=["EstatisticasTransacoesPix"],
        now=NOW,
        client=client,
        store=store,
    )
    months = [month for _name, month in client.calls]
    assert months[0] == 202511
    assert months[-1] == 202611
    assert 202602 in months


def test_mixed_month_response_is_quarantined(store: ObjectStore) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        rows = [tx_row(AnoMes=202610), tx_row(AnoMes=202609)]
        return httpx.Response(200, json={"value": rows})

    client = OlindaClient(
        transport=httpx.MockTransport(handler),
        page_size=10,
        max_retries=1,
        backoff_seconds=0,
        sleeper=lambda _delay: None,
    )
    result = run(
        _settings(),
        mode="ingest",
        entities=["EstatisticasTransacoesPix"],
        now=NOW,
        client=client,
        store=store,
    )
    assert not result.ok
    assert result.entities[0].quarantined_keys
    assert store.list_keys("raw/bcb/EstatisticasTransacoesPix/") == []
