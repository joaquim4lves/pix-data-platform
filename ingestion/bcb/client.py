"""Olinda client.

The function-import path argument is a lower bound, not an equality filter.
Every read adds ``$filter`` for the requested month. Spaces are encoded as
``%20``; a ``+`` is rejected by the service. ``$skip`` is part of the pager,
and a repeated HTTP 500 on ``$skip`` falls back to slicing by a low-cardinality
column so a truncated page is never written as a full month.
"""

from __future__ import annotations

import json
import logging
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from urllib.parse import quote

import httpx

from ingestion.bcb.calendar import month_start, next_month_start
from ingestion.bcb.entities import EntitySpec
from ingestion.bcb.errors import (
    OlindaError,
    PageSaturatedError,
    PayloadError,
    parse_olinda_error,
)

logger = logging.getLogger("ingestion.bcb.client")

RETRYABLE_STATUS = frozenset({429, 500, 502, 503, 504})
DEFAULT_BASE_URL = "https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata"


@dataclass(frozen=True)
class Page:
    body: bytes
    rows: list[dict[str, Any]]
    skip: int


class OlindaClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 120.0,
        max_retries: int = 5,
        backoff_seconds: float = 1.0,
        page_size: int = 50_000,
        transport: httpx.BaseTransport | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        rng: Callable[[], float] = random.random,
    ) -> None:
        if page_size < 1:
            raise ValueError("page_size must be >= 1")
        if max_retries < 1:
            raise ValueError("max_retries must be >= 1")
        self._base_url = base_url.rstrip("/")
        self._page_size = page_size
        self._max_retries = max_retries
        self._backoff = backoff_seconds
        self._sleeper = sleeper
        self._rng = rng
        self._http = httpx.Client(
            transport=transport,
            timeout=httpx.Timeout(timeout),
            headers={
                "Accept": "application/json",
                "User-Agent": "pix-data-platform/0.1",
            },
        )

    def __enter__(self) -> OlindaClient:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    @property
    def timeout(self) -> httpx.Timeout:
        return self._http.timeout

    def fetch_month(self, spec: EntitySpec, ano_mes: int) -> list[Page]:
        return self._collect(spec, ano_mes, extra=None, allow_split=True)

    def _collect(
        self,
        spec: EntitySpec,
        ano_mes: int,
        *,
        extra: str | None,
        allow_split: bool,
    ) -> list[Page]:
        pages: list[Page] = []
        skip = 0
        while True:
            try:
                page = self._get_page(spec, ano_mes, skip, extra)
            except OlindaError as exc:
                if skip > 0 and exc.status == 500:
                    if allow_split and spec.split_field:
                        logger.warning(
                            "skip failed, slicing the month",
                            extra={
                                "entity": spec.name,
                                "ano_mes": ano_mes,
                                "skip": skip,
                                "split_field": spec.split_field,
                            },
                        )
                        return self._fetch_split(spec, ano_mes)
                    raise PageSaturatedError(
                        f"{spec.name} {ano_mes} is larger than page_size and $skip failed",
                        status=exc.status,
                        body=exc.body,
                    ) from exc
                raise
            pages.append(page)
            if len(page.rows) < self._page_size:
                return pages
            skip += len(page.rows)

    def _fetch_split(self, spec: EntitySpec, ano_mes: int) -> list[Page]:
        if not spec.split_field or not spec.split_values:
            raise PageSaturatedError(
                f"{spec.name} has no split column for a saturated page",
                status=500,
                body=b"",
            )
        pages: list[Page] = []
        for value in spec.split_values:
            clause = f"{spec.split_field} eq '{_odata_quote(value)}'"
            pages.extend(self._collect(spec, ano_mes, extra=clause, allow_split=False))
        excluded = " or ".join(
            f"{spec.split_field} eq '{_odata_quote(value)}'" for value in spec.split_values
        )
        pages.extend(self._collect(spec, ano_mes, extra=f"not ({excluded})", allow_split=False))
        return pages

    def _get_page(
        self,
        spec: EntitySpec,
        ano_mes: int,
        skip: int,
        extra: str | None,
    ) -> Page:
        url = self._build_url(spec, ano_mes, skip, extra)
        started = time.perf_counter()
        response = self._request(url)
        rows = _decode_rows(response.content)
        _assert_period(spec, ano_mes, rows, response.content)
        logger.info(
            "fetched page",
            extra={
                "entity": spec.name,
                "ano_mes": ano_mes,
                "skip": skip,
                "rows": len(rows),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 1),
            },
        )
        return Page(body=response.content, rows=rows, skip=skip)

    def _build_url(self, spec: EntitySpec, ano_mes: int, skip: int, extra: str | None) -> str:
        path = f"{spec.resource}({spec.param_name}='{_param_value(spec, ano_mes)}')"
        pairs = [
            ("$filter", _filter(spec, ano_mes, extra)),
            ("$top", str(self._page_size)),
            ("$format", "json"),
        ]
        if skip:
            pairs.append(("$skip", str(skip)))
        query = "&".join(f"{quote(key, safe='$')}={quote(value, safe='')}" for key, value in pairs)
        return f"{self._base_url}/{path}?{query}"

    def _request(self, url: str) -> httpx.Response:
        last_body = b""
        last_status: int | None = None
        for attempt in range(self._max_retries):
            try:
                response = self._http.get(url)
            except httpx.TransportError as exc:
                if attempt == self._max_retries - 1:
                    raise OlindaError(
                        f"transport error after {self._max_retries} attempts: {exc}",
                        status=None,
                        body=last_body,
                    ) from exc
                delay = self._delay(attempt)
                logger.warning(
                    "retrying transport error",
                    extra={"attempt": attempt + 1, "delay_s": delay, "error": str(exc)},
                )
                self._sleeper(delay)
                continue
            if response.status_code in RETRYABLE_STATUS:
                last_body = response.content
                last_status = response.status_code
                parsed = parse_olinda_error(response.content)
                if attempt == self._max_retries - 1:
                    raise OlindaError(
                        _error_message(parsed, response.status_code),
                        status=response.status_code,
                        body=response.content,
                    )
                delay = self._delay(attempt)
                logger.warning(
                    "retrying olinda error",
                    extra={
                        "attempt": attempt + 1,
                        "status": response.status_code,
                        "mensagem": None if parsed is None else parsed.get("mensagem"),
                        "delay_s": delay,
                    },
                )
                self._sleeper(delay)
                continue
            if response.status_code >= 400:
                parsed = parse_olinda_error(response.content)
                raise OlindaError(
                    _error_message(parsed, response.status_code),
                    status=response.status_code,
                    body=response.content,
                )
            return response
        raise OlindaError("exhausted retries", status=last_status, body=last_body)

    def _delay(self, attempt: int) -> float:
        base = self._backoff * (2**attempt)
        return min(base + self._rng() * self._backoff, 30.0)


def _odata_quote(value: str) -> str:
    return value.replace("'", "''")


def _param_value(spec: EntitySpec, ano_mes: int) -> str:
    if spec.period == "date":
        return month_start(ano_mes).isoformat()
    return str(ano_mes)


def _filter(spec: EntitySpec, ano_mes: int, extra: str | None) -> str:
    if spec.period == "ano_mes":
        clause = f"AnoMes eq {ano_mes}"
    else:
        start = month_start(ano_mes).isoformat()
        end = next_month_start(ano_mes).isoformat()
        clause = f"Data ge {start} and Data lt {end}"
    if extra:
        clause = f"{clause} and {extra}"
    return clause


def _error_message(parsed: dict[str, object] | None, status: int) -> str:
    if parsed and parsed.get("mensagem"):
        return str(parsed["mensagem"])
    return f"HTTP {status}"


def _decode_rows(body: bytes) -> list[dict[str, Any]]:
    try:
        payload = json.loads(body, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        raise PayloadError("response is not JSON", body) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("value"), list):
        raise PayloadError("response has no value list", body)
    rows = payload["value"]
    if not all(isinstance(row, dict) for row in rows):
        raise PayloadError("value items must be objects", body)
    return rows


def _assert_period(spec: EntitySpec, ano_mes: int, rows: list[dict[str, Any]], body: bytes) -> None:
    for index, row in enumerate(rows):
        try:
            observed = _row_ano_mes(spec, row)
        except (KeyError, TypeError, ValueError) as exc:
            raise PayloadError(f"row {index} has no usable period", body) from exc
        if observed != ano_mes:
            raise PayloadError(
                f"row {index} is month {observed}, requested {ano_mes}",
                body,
            )


def _row_ano_mes(spec: EntitySpec, row: dict[str, Any]) -> int:
    if spec.period == "ano_mes":
        return int(row["AnoMes"])
    year, month, _day = str(row["Data"]).split("-")
    return int(year) * 100 + int(month)
