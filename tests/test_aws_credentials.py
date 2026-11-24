"""Real AWS uses the default credential chain. LocalStack keeps the dummy keys."""

from __future__ import annotations

import pytest
from cdc.aws import client as cdc_client
from cdc.settings import CdcSettings
from ingestion.bcb.settings import Settings, endpoint_from_env, region_from_env, static_credentials
from ingestion.bcb.store import ObjectStore


def test_unset_endpoint_stays_on_localstack(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AWS_ENDPOINT_URL", raising=False)
    assert endpoint_from_env() == "http://localhost:4566"


@pytest.mark.parametrize("value", ["", "   ", "aws", "AWS", "none", "off"])
def test_blank_and_sentinels_mean_real_aws(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("AWS_ENDPOINT_URL", value)
    assert endpoint_from_env() is None


def test_lambda_region_wins_over_the_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_REGION", "sa-east-1")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
    assert region_from_env() == "sa-east-1"


def test_custom_endpoint_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    assert endpoint_from_env() == "http://localhost:4566"


def test_localstack_without_keys_uses_the_dummy_pair(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    assert static_credentials() == ("test", "test", None)


def test_real_aws_without_keys_leaves_the_chain_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_ENDPOINT_URL", "aws")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)
    assert static_credentials() == ("", "", None)


def test_lambda_temporary_credentials_keep_the_session_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AWS_ENDPOINT_URL", "aws")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "ASIAEXAMPLE")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "session-token")
    settings = Settings.from_env()
    cdc = CdcSettings.from_env()
    assert settings.endpoint_url is None
    assert settings.session_token == "session-token"
    assert cdc.endpoint_url is None
    assert cdc.access_key_id == "ASIAEXAMPLE"
    assert cdc.session_token == "session-token"


def _settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "base_url": "https://olinda.example",
        "bucket": "pix-test",
        "region": "us-east-1",
        "access_key_id": "testing",
        "secret_access_key": "secret",
        "endpoint_url": None,
        "lookback_months": 3,
        "page_size": 10,
        "timeout_seconds": 1,
        "max_retries": 1,
        "backoff_seconds": 0,
        "session_token": "session-token",
    }
    values.update(overrides)
    return Settings(**values)  # type: ignore[arg-type]


def test_store_forwards_the_session_token(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_client(service: str, **kwargs: object) -> object:
        captured["service"] = service
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("ingestion.bcb.store.boto3.client", fake_client)
    ObjectStore.from_settings(_settings())
    kwargs = captured["kwargs"]
    assert captured["service"] == "s3"
    assert isinstance(kwargs, dict)
    assert kwargs["aws_session_token"] == "session-token"
    assert kwargs["aws_access_key_id"] == "testing"
    assert "endpoint_url" not in kwargs


def test_store_omits_static_keys_for_the_default_chain(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_client(service: str, **kwargs: object) -> object:
        del service
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("ingestion.bcb.store.boto3.client", fake_client)
    ObjectStore.from_settings(_settings(access_key_id="", secret_access_key="", session_token=None))
    kwargs = captured["kwargs"]
    assert isinstance(kwargs, dict)
    assert "aws_access_key_id" not in kwargs
    assert "aws_secret_access_key" not in kwargs
    assert "aws_session_token" not in kwargs


def test_cdc_client_forwards_the_session_token(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    def fake_client(service: str, **kwargs: object) -> object:
        captured["service"] = service
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr("cdc.aws.boto3.client", fake_client)
    settings = CdcSettings(
        database_url="postgresql://pix:pix@localhost/pix",
        publication="pix_app",
        slot="pix_app_slot",
        queue_name="pix-cdc",
        bucket="pix-test",
        region="us-east-1",
        access_key_id="ASIAEXAMPLE",
        secret_access_key="secret",
        endpoint_url=None,
        session_token="session-token",
    )
    cdc_client("sqs", settings)
    kwargs = captured["kwargs"]
    assert captured["service"] == "sqs"
    assert isinstance(kwargs, dict)
    assert kwargs["aws_session_token"] == "session-token"
    assert "endpoint_url" not in kwargs
