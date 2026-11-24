"""Star schema built from fixture Parquet, with no network."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb
import pytest
from tests.pix_warehouse import build_sample, write_sample_raw
from transform.build import build_warehouse
from transform.cli import main
from transform.sources import LocalRaw


def _money(value: object) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"))


def test_models_keep_grain_labels_and_the_unknown_municipality(tmp_path: Path) -> None:
    database = build_sample(tmp_path)
    # A second build replaces the file in place and keeps the same grain.
    build_warehouse(database, LocalRaw(tmp_path / "raw"))
    con = duckdb.connect(str(database))

    nature = {
        row[0]: row
        for row in con.execute(
            "select codigo, rotulo, publicado from marts.dim_natureza"
        ).fetchall()
    }
    assert nature["P2P"][1] == "Pessoa física para pessoa física"
    assert nature["P2P"][2] is True
    assert nature["P2G"][1] == "Pessoa física para o governo"
    assert nature["P2G"][2] is True
    assert nature["G2G"][1] == "Governo para governo"
    assert nature["G2G"][2] is False
    assert nature["X2Z"][1] == "X2Z"
    assert nature["X2Z"][2] is False
    assert set(nature) >= {"B2B", "B2G", "B2P", "G2B", "G2G", "G2P", "P2B", "P2G", "P2P", "X2Z"}

    forma = dict(con.execute("select codigo, rotulo from marts.dim_forma_iniciacao").fetchall())
    assert forma["DICT"] == "Chave Pix"
    assert forma["Nao disponivel"] == "Não disponível"

    tempo = {
        row[0]: row
        for row in con.execute(
            """
            select ano_mes, ano, mes, trimestre, data_inicio, data_fim, nome_mes, rotulo
            from marts.dim_tempo
            """
        ).fetchall()
    }
    assert tempo[202402] == (
        202402,
        2024,
        2,
        1,
        date(2024, 2, 1),
        date(2024, 2, 29),
        "Fevereiro",
        "2024-02",
    )
    assert tempo[202609][5] == date(2026, 9, 30)
    assert tempo[202609][6] == "Setembro"
    assert tempo[202610][3] == 4
    assert tempo[202610][5] == date(2026, 10, 31)
    assert tempo[202610][6] == "Outubro"

    cities = {
        row[0]: row
        for row in con.execute(
            """
            select municipio_ibge, nome, nome_fonte, uf_ibge, uf_sigla, uf_nome,
                   sigla_regiao, regiao_nome
            from marts.dim_municipio
            """
        ).fetchall()
    }
    assert cities[0] == (
        0,
        "Não informado",
        "N/D",
        0,
        None,
        "Não informado",
        None,
        "Não informado",
    )
    assert cities[3550308][1] == "SAO PAULO"
    assert cities[3550308][4:] == ("SP", "São Paulo", "SE", "Sudeste")
    assert cities[2103406][1] == "COELHO NETO"
    assert cities[2103406][4:] == ("MA", "Maranhão", "NE", "Nordeste")

    received = {
        row[0]: _money(row[1])
        for row in con.execute(
            """
            select municipio_ibge, valor_recebido
            from marts.fct_transacoes_municipio
            where ano_mes = 202610
            """
        ).fetchall()
    }
    assert received == {
        3550308: Decimal("1500.00"),
        2103406: Decimal("100.00"),
        0: Decimal("9999.00"),
    }
    assert con.execute("select count(*) from marts.fct_transacoes_municipio").fetchone()[0] == 3

    monthly = con.execute(
        """
        select ano_mes, sum(valor), sum(quantidade), count(*)
        from marts.fct_transacoes_mensal
        group by ano_mes
        order by ano_mes
        """
    ).fetchall()
    assert [(row[0], _money(row[1]), _money(row[2]), row[3]) for row in monthly] == [
        (202402, Decimal("4.00"), Decimal("1.00"), 1),
        (202609, Decimal("9.00"), Decimal("2.00"), 1),
        (202610, Decimal("18.00"), Decimal("5.00"), 3),
    ]
    assert (
        con.execute(
            "select count(*) from marts.fct_transacoes_mensal where natureza = 'X2Z'"
        ).fetchone()[0]
        == 1
    )

    keys = con.execute(
        """
        select ano_mes, data_referencia, ispb, natureza_usuario, tipo_chave, quantidade_chaves
        from marts.fct_chaves_pix
        where ano_mes = 202610 and ispb = '05938780'
        order by tipo_chave
        """
    ).fetchall()
    assert keys == [
        (202610, date(2026, 10, 31), "05938780", "PF", "CPF", 10),
        (202610, date(2026, 10, 31), "05938780", "PF", "Celular", 4),
    ]
    institution = con.execute(
        """
        select nome, segmento, ano_mes_referencia
        from marts.dim_instituicao
        where ispb = '05938780'
        """
    ).fetchone()
    assert institution == ("COOPER CARD IP", "Instituição de Pagamento", 202610)
    con.close()


def test_cli_build_and_dq(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raw = tmp_path / "raw"
    write_sample_raw(raw)
    monkeypatch.setenv("PIX_RAW_SOURCE", "local")
    monkeypatch.setenv("PIX_RAW_ROOT", str(raw))
    monkeypatch.setenv("PIX_DUCKDB_PATH", str(tmp_path / "pix.duckdb"))
    assert main(["build"]) == 0
    assert main(["dq"]) == 0


def test_empty_raw_zone_builds_seeded_dimensions(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    database = tmp_path / "empty.duckdb"
    build_warehouse(database, LocalRaw(raw))
    con = duckdb.connect(str(database))
    assert con.execute("select count(*) from marts.dim_natureza").fetchone()[0] == 9
    assert con.execute("select count(*) from marts.fct_transacoes_mensal").fetchone()[0] == 0
    assert con.execute("select count(*) from marts.dim_municipio").fetchone()[0] == 0
    assert con.execute("select count(*) from marts.dim_tempo").fetchone()[0] == 0
    con.close()
