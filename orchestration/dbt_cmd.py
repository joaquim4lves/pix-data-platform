"""dbt invocations shared by the freshness tasks.

Cosmos runs ``dbt build`` for the selected graph. Source freshness is not a
model, so it stays a normal task. Selectors are the dbt ``--select`` syntax.
"""

from __future__ import annotations

from orchestration.paths import dbt_project_dir

BCB_SELECT: tuple[str, ...] = (
    "+fct_transacoes_mensal",
    "+fct_transacoes_municipio",
    "+fct_chaves_pix",
)
CDC_SELECT: tuple[str, ...] = (
    "+cur_pix_key",
    "+cur_pix_transaction",
    "+cur_pix_dispute",
)
BCB_FRESHNESS = (
    "source:raw.estatisticas_transacoes_pix "
    "source:raw.transacoes_pix_municipio "
    "source:raw.chaves_pix"
)
CDC_FRESHNESS = (
    "source:raw.app_pix_keys source:raw.app_pix_transactions source:raw.app_pix_disputes"
)


def run_dbt(args: list[str]) -> None:
    from dbt.cli.main import dbtRunner

    project = dbt_project_dir()
    invocation = [
        "--project-dir",
        str(project),
        "--profiles-dir",
        str(project),
        *args,
    ]
    result = dbtRunner().invoke(invocation)
    if getattr(result, "exception", None):
        raise result.exception
    if not getattr(result, "success", False):
        rendered = " ".join(args)
        raise RuntimeError(f"dbt {rendered} failed")


def run_source_freshness(selector: str) -> None:
    """Fail when dbt reports a freshness error. A warning stays a success."""

    run_dbt(["source", "freshness", "--select", selector])
