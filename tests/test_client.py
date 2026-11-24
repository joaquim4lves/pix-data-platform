import httpx
import pytest
from ingestion.bcb.client import OlindaClient
from ingestion.bcb.entities import CHAVES, MUNICIPIO, NATUREZA_CODES, TRANSACOES
from ingestion.bcb.errors import OlindaError, PayloadError, parse_olinda_error
from tests.samples import tx_row

_ENVELOPE = b'/*{ "codigo" : 500, "mensagem" : "Erro desconhecido" }*/'


def _client(handler, **kwargs) -> OlindaClient:
    defaults = {
        "transport": httpx.MockTransport(handler),
        "timeout": 120.0,
        "max_retries": 3,
        "backoff_seconds": 0.5,
        "page_size": 2,
        "sleeper": lambda _delay: None,
        "rng": lambda: 0.0,
    }
    defaults.update(kwargs)
    return OlindaClient(**defaults)


def test_parse_comment_wrapped_error_body() -> None:
    parsed = parse_olinda_error(_ENVELOPE)
    assert parsed is not None
    assert parsed["codigo"] == 500
    assert parsed["mensagem"] == "Erro desconhecido"
    assert parse_olinda_error(b'{"status": 403, "message": "Access Denied"}') is None


def test_transaction_request_filters_the_exact_month() -> None:
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, json={"value": [tx_row()]})

    with _client(handler, page_size=100) as client:
        pages = client.fetch_month(TRANSACOES, 202610)

    url = str(seen[0])
    assert "EstatisticasTransacoesPix(Database='202610')" in url
    assert seen[0].params["$filter"] == "AnoMes eq 202610"
    assert "$skip" not in seen[0].params
    assert "+" not in url
    assert pages[0].rows[0]["NATUREZA"] == "B2P"


def test_municipio_uses_database_parameter_with_capital_b() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return httpx.Response(200, json={"value": []})

    with _client(handler) as client:
        client.fetch_month(MUNICIPIO, 202610)

    assert "TransacoesPixPorMunicipio(DataBase='202610')" in seen[0]
    assert "Database=" not in seen[0]


def test_chaves_filters_a_date_range_for_the_month() -> None:
    seen: list[httpx.URL] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.url)
        return httpx.Response(200, json={"value": []})

    with _client(handler) as client:
        client.fetch_month(CHAVES, 202610)

    assert "ChavesPix(Data='2026-10-01')" in str(seen[0])
    assert seen[0].params["$filter"] == "Data ge 2026-10-01 and Data lt 2026-11-01"


def test_default_timeout_covers_a_slow_month() -> None:
    transport = httpx.MockTransport(lambda _request: httpx.Response(200, json={"value": []}))
    with OlindaClient(transport=transport) as client:
        assert client.timeout.read is not None
        assert float(client.timeout.read) >= 60


def test_retries_http_500_with_backoff_then_returns_rows() -> None:
    calls = {"n": 0}
    slept: list[float] = []

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(500, content=_ENVELOPE)
        return httpx.Response(200, json={"value": [tx_row()]})

    with _client(handler, sleeper=slept.append) as client:
        pages = client.fetch_month(TRANSACOES, 202610)

    assert calls["n"] == 3
    assert slept == [0.5, 1.0]
    assert pages[0].rows[0]["AnoMes"] == 202610


def test_does_not_retry_http_400() -> None:
    calls = {"n": 0}

    def handler(_request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        body = b'/*{"codigo":400,"mensagem":"bad parameter"}*/'
        return httpx.Response(400, content=body)

    with _client(handler) as client:
        with pytest.raises(OlindaError, match="bad parameter"):
            client.fetch_month(TRANSACOES, 202610)
    assert calls["n"] == 1


def test_paginates_with_top_and_skip() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["$top"] == "2"
        assert "+" not in str(request.url)
        skip = int(request.url.params.get("$skip", "0"))
        if skip == 0:
            rows = [tx_row(FINALIDADE="Pix"), tx_row(FINALIDADE="Pix Saque")]
        elif skip == 2:
            rows = [tx_row(FINALIDADE="Pix Troco")]
        else:
            raise AssertionError(skip)
        return httpx.Response(200, json={"value": rows})

    with _client(handler) as client:
        pages = client.fetch_month(TRANSACOES, 202610)

    finalidades = [row["FINALIDADE"] for page in pages for row in page.rows]
    assert finalidades == ["Pix", "Pix Saque", "Pix Troco"]


def test_rejects_a_page_that_mixes_months() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        rows = [tx_row(AnoMes=202610), tx_row(AnoMes=202609)]
        return httpx.Response(200, json={"value": rows})

    with _client(handler, page_size=10) as client:
        with pytest.raises(PayloadError, match="202609"):
            client.fetch_month(TRANSACOES, 202610)


def test_splits_by_natureza_when_skip_keeps_failing() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        filt = request.url.params["$filter"]
        if request.url.params.get("$skip"):
            return httpx.Response(500, content=_ENVELOPE)
        if "not (" in filt:
            return httpx.Response(200, json={"value": []})
        marker = "NATUREZA eq '"
        if marker in filt:
            code = filt.split(marker, 1)[1].split("'", 1)[0]
            return httpx.Response(200, json={"value": [tx_row(NATUREZA=code)]})
        rows = [tx_row(), tx_row(NATUREZA="P2P")]
        return httpx.Response(200, json={"value": rows})

    with _client(handler, max_retries=2) as client:
        pages = client.fetch_month(TRANSACOES, 202610)

    natures = [row["NATUREZA"] for page in pages for row in page.rows]
    assert natures == list(NATUREZA_CODES)
