from datetime import UTC, datetime
from decimal import Decimal

import boto3
import pytest
from ingestion.bcb.entities import MUNICIPIO, TRANSACOES
from ingestion.bcb.store import ObjectStore, partition_key
from moto import mock_aws
from tests.samples import municipio_row, tx_row


@pytest.fixture
def store():
    with mock_aws():
        client = boto3.client("s3", region_name="us-east-1")
        client.create_bucket(Bucket="pix-test")
        yield ObjectStore(client, "pix-test")


def test_partition_overwrite_removes_stale_objects(store: ObjectStore) -> None:
    prefix = "raw/bcb/EstatisticasTransacoesPix/ano_mes=202610/"
    store._s3.put_object(Bucket="pix-test", Key=prefix + "stale.parquet", Body=b"old")
    first = TRANSACOES.model.model_validate(tx_row(VALOR="1.00"))
    second_a = TRANSACOES.model.model_validate(tx_row(VALOR="9.50", NATUREZA="P2P"))
    second_b = TRANSACOES.model.model_validate(tx_row(VALOR="3.00", NATUREZA="P2B"))

    store.write_partition(TRANSACOES, 202610, [first])
    store.write_partition(TRANSACOES, 202610, [second_b, second_a])

    table = store.read_partition("EstatisticasTransacoesPix", 202610)
    assert table.num_rows == 2
    assert table.column("NATUREZA").to_pylist() == ["P2B", "P2P"]
    assert table.column("VALOR").to_pylist() == [Decimal("3.00"), Decimal("9.50")]
    assert store.list_keys(prefix) == [partition_key("EstatisticasTransacoesPix", 202610)]


def test_refuses_to_write_an_empty_partition(store: ObjectStore) -> None:
    with pytest.raises(ValueError, match="empty partition"):
        store.write_partition(TRANSACOES, 202610, [])


def test_unknown_municipality_keeps_null_codes(store: ObjectStore) -> None:
    unknown = MUNICIPIO.model.model_validate(
        municipio_row(
            Municipio_Ibge=None,
            Municipio="N/D",
            Estado_Ibge=None,
            Estado="NAO INFORMADO",
            Sigla_Regiao=None,
            Regiao="Nao informado",
        )
    )
    known = MUNICIPIO.model.model_validate(municipio_row())
    store.write_partition(MUNICIPIO, 202609, [unknown, known])
    table = store.read_partition("TransacoesPixPorMunicipio", 202609)
    assert table.column("Municipio").to_pylist() == ["COELHO NETO", "N/D"]
    assert table.column("Municipio_Ibge").to_pylist() == [2103406, None]
    assert table.column("Sigla_Regiao").to_pylist() == ["NE", None]


def test_watermark_round_trip(store: ObjectStore) -> None:
    assert store.load_watermarks() == {}
    moment = datetime(2026, 11, 24, 12, 0, tzinfo=UTC)
    store.save_watermark("ChavesPix", 202610, moment)
    assert store.load_watermarks() == {"ChavesPix": 202610}
