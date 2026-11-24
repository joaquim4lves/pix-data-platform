"""Read a LocalStack partition through DuckDB httpfs.

Skips when LocalStack is down, same as the ingestion integration test.
The first run installs the httpfs extension, which needs network access
to DuckDB's extension repository.
"""

import os

import boto3
import duckdb
import httpx
import pytest
from botocore.client import Config
from botocore.exceptions import ClientError
from ingestion.bcb.entities import CHAVES
from ingestion.bcb.store import ObjectStore
from tests.samples import chaves_row
from transform.build import build_warehouse
from transform.sources import S3Raw

pytestmark = pytest.mark.integration


def test_model_reads_localstack_parquet_via_httpfs(tmp_path) -> None:
    endpoint = os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")
    try:
        health = httpx.get(f"{endpoint}/_localstack/health", timeout=2.0)
        health.raise_for_status()
    except httpx.HTTPError as exc:
        pytest.skip(f"LocalStack is not available: {exc}")

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        config=Config(s3={"addressing_style": "path"}),
    )
    bucket = "pix-duckdb-itest"
    try:
        client.create_bucket(Bucket=bucket)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            raise

    store = ObjectStore(client, bucket)
    store.write_partition(CHAVES, 202610, [CHAVES.model.model_validate(chaves_row(qtdChaves=917))])
    database = tmp_path / "pix.duckdb"
    build_warehouse(
        database,
        S3Raw(
            bucket=bucket,
            prefix="raw",
            region="us-east-1",
            access_key_id="test",
            secret_access_key="test",
            endpoint_url=endpoint,
        ),
    )

    con = duckdb.connect(str(database))
    try:
        row = con.execute(
            """
            select ispb, quantidade_chaves
            from marts.fct_chaves_pix
            where ano_mes = 202610
            """
        ).fetchone()
    finally:
        con.close()
    assert row == ("05938780", 917)
    for key in store.list_keys("raw/bcb/ChavesPix/"):
        client.delete_object(Bucket=bucket, Key=key)
