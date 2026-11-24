"""Raw-zone paths for the local filesystem and for S3 through httpfs."""

from pathlib import Path

from transform.sources import LocalRaw, S3Raw, parquet_glob, s3_statements


def test_local_glob_follows_the_ingestion_layout(tmp_path: Path) -> None:
    glob = parquet_glob(LocalRaw(tmp_path), "EstatisticasTransacoesPix")
    assert glob.endswith("bcb/EstatisticasTransacoesPix/ano_mes=*/part.parquet")


def test_localstack_s3_uses_path_style_http() -> None:
    location = S3Raw(
        bucket="pix-data-local",
        prefix="raw",
        region="us-east-1",
        access_key_id="test",
        secret_access_key="secret",
        endpoint_url="http://localhost:4566",
    )
    statements = "\n".join(s3_statements(location))
    assert "INSTALL httpfs" in statements
    assert "LOAD httpfs" in statements
    assert "s3_endpoint='localhost:4566'" in statements
    assert "s3_use_ssl=false" in statements
    assert "s3_url_style='path'" in statements
    assert "s3_access_key_id='test'" in statements
    assert (
        parquet_glob(location, "ChavesPix")
        == "s3://pix-data-local/raw/bcb/ChavesPix/ano_mes=*/part.parquet"
    )


def test_session_token_is_forwarded_when_present() -> None:
    location = S3Raw(
        bucket="pix-prod",
        prefix="raw",
        region="us-east-1",
        access_key_id="ASIA",
        secret_access_key="secret",
        endpoint_url=None,
        session_token="tok+en",
    )
    statements = "\n".join(s3_statements(location))
    assert "s3_session_token='tok+en'" in statements
    assert "s3_endpoint" not in statements


def test_empty_keys_leave_duckdb_on_its_credential_chain() -> None:
    location = S3Raw(
        bucket="pix-prod",
        prefix="raw",
        region="us-east-1",
        access_key_id="",
        secret_access_key="",
        endpoint_url=None,
    )
    statements = "\n".join(s3_statements(location))
    assert "s3_access_key_id" not in statements
    assert "s3_secret_access_key" not in statements
    assert "s3_region='us-east-1'" in statements


def test_real_s3_does_not_force_a_custom_endpoint() -> None:
    location = S3Raw(
        bucket="pix-prod",
        prefix="raw",
        region="us-east-1",
        access_key_id="AKIA",
        secret_access_key="secret",
        endpoint_url=None,
    )
    statements = "\n".join(s3_statements(location))
    assert "s3_endpoint" not in statements
    assert "s3_url_style" not in statements
    assert "s3_region='us-east-1'" in statements
