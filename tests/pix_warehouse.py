"""A tiny multi-entity raw zone and the warehouse built from it."""

from __future__ import annotations

from pathlib import Path

from ingestion.bcb.entities import CHAVES, MUNICIPIO, TRANSACOES
from tests.raw_files import write_partition
from tests.samples import chaves_row, municipio_row, tx_row
from transform.build import build_warehouse
from transform.sources import LocalRaw


def _municipio(**overrides: object) -> dict[str, object]:
    measures = {
        "VL_PagadorPF": "0",
        "QT_PagadorPF": 0,
        "VL_PagadorPJ": "0",
        "QT_PagadorPJ": 0,
        "VL_RecebedorPF": "0",
        "QT_RecebedorPF": 0,
        "VL_RecebedorPJ": "0",
        "QT_RecebedorPJ": 0,
        "QT_PES_PagadorPF": 0,
        "QT_PES_PagadorPJ": 0,
        "QT_PES_RecebedorPF": 0,
        "QT_PES_RecebedorPJ": 0,
    }
    measures.update(overrides)
    return municipio_row(**measures)


def write_sample_raw(root: Path) -> None:
    write_partition(
        root,
        TRANSACOES,
        202402,
        [tx_row(AnoMes=202402, VALOR="4.00", QUANTIDADE=1, NATUREZA="P2P")],
    )
    write_partition(
        root,
        TRANSACOES,
        202609,
        [tx_row(AnoMes=202609, VALOR="9.00", QUANTIDADE=2, NATUREZA="P2B")],
    )
    write_partition(
        root,
        TRANSACOES,
        202610,
        [
            tx_row(AnoMes=202610, VALOR="10.00", QUANTIDADE=3, NATUREZA="P2P"),
            tx_row(
                AnoMes=202610,
                VALOR="7.00",
                QUANTIDADE=1,
                NATUREZA="B2B",
                FORMAINICIACAO="DICT",
                FINALIDADE="Pix Saque",
            ),
            tx_row(AnoMes=202610, VALOR="1.00", QUANTIDADE=1, NATUREZA="X2Z"),
        ],
    )
    write_partition(
        root,
        MUNICIPIO,
        202610,
        [
            _municipio(
                Municipio_Ibge=3550308,
                Municipio="SAO PAULO",
                Estado_Ibge=35,
                Estado="SAO PAULO",
                Sigla_Regiao="SE",
                Regiao="SUDESTE",
                VL_RecebedorPF="1000.00",
                VL_RecebedorPJ="500.00",
                QT_RecebedorPF=10,
                QT_RecebedorPJ=4,
            ),
            _municipio(VL_RecebedorPF="100.00", QT_RecebedorPF=3),
            _municipio(
                Municipio_Ibge=None,
                Municipio="N/D",
                Estado_Ibge=None,
                Estado="NAO INFORMADO",
                Sigla_Regiao=None,
                Regiao="Nao informado",
                VL_RecebedorPF="9999.00",
                QT_RecebedorPF=1,
            ),
        ],
    )
    write_partition(
        root,
        CHAVES,
        202402,
        [chaves_row(Data="2024-02-29", qtdChaves=5, Nome="OLD", Segmento="Cooperativa de Crédito")],
    )
    write_partition(
        root,
        CHAVES,
        202609,
        [
            chaves_row(
                Data="2026-09-30",
                qtdChaves=8,
                Nome="OLDER",
                Segmento="Instituição de Pagamento",
            )
        ],
    )
    write_partition(
        root,
        CHAVES,
        202610,
        [
            chaves_row(Data="2026-10-31", qtdChaves=10, TipoChave="CPF"),
            chaves_row(Data="2026-10-31", qtdChaves=4, TipoChave="Celular"),
            chaves_row(
                Data="2026-10-31",
                ISPB="00000000",
                Nome="OUTRO",
                NaturezaUsuario="PJ",
                TipoChave="e-mail",
                qtdChaves=2,
                Segmento="Banco Múltiplo",
            ),
        ],
    )


def build_sample(directory: Path) -> Path:
    raw = directory / "raw"
    database = directory / "pix.duckdb"
    write_sample_raw(raw)
    build_warehouse(database, LocalRaw(raw))
    return database
