import os

import boto3
import httpx
import pytest
from botocore.client import Config
from botocore.exceptions import ClientError
from ingestion.bcb.entities import CHAVES
from ingestion.bcb.store import ObjectStore, partition_key
from tests.samples import chaves_row

pytestmark = pytest.mark.integration


def _endpoint() -> str:
    return os.environ.get("AWS_ENDPOINT_URL", "http://localhost:4566")


def test_localstack_partition_overwrite() -> None:
    endpoint = _endpoint()
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
    bucket = "pix-itest"
    try:
        client.create_bucket(Bucket=bucket)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code not in {"BucketAlreadyOwnedByYou", "BucketAlreadyExists"}:
            raise

    store = ObjectStore(client, bucket)
    prefix = "raw/bcb/ChavesPix/ano_mes=202610/"
    client.put_object(Bucket=bucket, Key=prefix + "stale.parquet", Body=b"old")
    first = CHAVES.model.model_validate(chaves_row(qtdChaves=1))
    replacement = CHAVES.model.model_validate(chaves_row(qtdChaves=917))
    store.write_partition(CHAVES, 202610, [first])
    store.write_partition(CHAVES, 202610, [replacement])

    table = store.read_partition("ChavesPix", 202610)
    assert table.column("qtdChaves").to_pylist() == [917]
    assert table.column("ISPB").to_pylist() == ["05938780"]
    assert store.list_keys(prefix) == [partition_key("ChavesPix", 202610)]
    for key in store.list_keys(prefix):
        client.delete_object(Bucket=bucket, Key=key)
