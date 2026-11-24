"""Errors raised while talking to Olinda or writing a partition."""

from __future__ import annotations

import json


class OlindaError(Exception):
    """The Olinda request failed after the retry policy was applied."""

    def __init__(self, message: str, *, status: int | None = None, body: bytes = b"") -> None:
        super().__init__(message)
        self.status = status
        self.body = body


class PageSaturatedError(OlindaError):
    """A page came back full and $skip could not advance it."""


class PayloadError(Exception):
    """A 200 response cannot be written for the month that was requested."""

    def __init__(self, message: str, body: bytes) -> None:
        super().__init__(message)
        self.body = body


class IngestionError(Exception):
    """One or more entities failed. The message is a JSON result payload."""


def parse_olinda_error(body: bytes) -> dict[str, object] | None:
    """Parse the comment-wrapped JSON Olinda returns on HTTP errors.

    A typical body is ``/*{ "codigo" : 500, "mensagem" : "Erro desconhecido" }*/``.
    Other gateways (the 403 from ``$count``) use a different shape and return None.
    """

    text = body.decode("utf-8", errors="replace").strip()
    if text.startswith("/*") and text.endswith("*/"):
        text = text[2:-2].strip()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict) and ("codigo" in payload or "mensagem" in payload):
        return payload
    return None
