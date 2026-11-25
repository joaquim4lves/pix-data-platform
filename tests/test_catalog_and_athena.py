"""The Glue contract and the Athena view script stay aligned with the models."""

from __future__ import annotations

import json
from pathlib import Path

from transform.athena_sql import render
from transform.catalog_contract import catalog_document

ROOT = Path(__file__).resolve().parents[1]
COLUMNS = ROOT / "infra" / "terraform" / "modules" / "catalog" / "columns.json"
VIEWS = ROOT / "transform" / "athena" / "views.sql"
DIAGRAM = ROOT / "docs" / "architecture" / "infra-aws.mmd"
EMBEDDED = (
    ROOT / "README.md",
    ROOT / "docs" / "adr" / "ADR-004.md",
    ROOT / "docs" / "runbooks" / "aws-dev.md",
)


def test_columns_json_matches_the_parquet_writers() -> None:
    assert json.loads(COLUMNS.read_text(encoding="utf-8")) == catalog_document()


def test_athena_views_match_the_renderer_and_avoid_raw_paths() -> None:
    rendered = render("pix")
    assert VIEWS.read_text(encoding="utf-8") == rendered
    assert "CREATE OR REPLACE VIEW pix_marts.fct_transacoes_mensal AS" in rendered
    assert "CREATE OR REPLACE VIEW pix_marts.cur_pix_key AS" in rendered
    assert "read_parquet" not in rendered
    assert "from pix_raw.estatisticas_transacoes_pix" in rendered


def test_infra_diagram_is_embedded_with_the_athena_edge() -> None:
    diagram = DIAGRAM.read_text(encoding="utf-8")
    assert 'mb -.->|"Athena path, not applied"| ath' in diagram
    assert "Metabase — DuckDB marts, local only" in diagram
    fence = f"```mermaid\n{diagram}```"
    for path in EMBEDDED:
        text = path.read_text(encoding="utf-8")
        assert fence in text, f"{path.relative_to(ROOT)} is missing the infra diagram"
