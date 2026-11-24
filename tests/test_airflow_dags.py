"""DAG import and integrity checks. No scheduler, webserver, or database service.

Skipped when the ``airflow`` extra is not installed, so ``make test`` stays
usable without it. ``make airflow-test`` imports Airflow first and fails closed.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

_HOME = Path(tempfile.mkdtemp(prefix="pix-airflow-home-"))
(_HOME / "raw").mkdir()
os.environ["AIRFLOW_HOME"] = str(_HOME)
os.environ["AIRFLOW__CORE__LOAD_EXAMPLES"] = "False"
os.environ["AIRFLOW__CORE__UNIT_TEST_MODE"] = "True"
os.environ["AIRFLOW__CORE__EXECUTOR"] = "LocalExecutor"
os.environ["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"] = f"sqlite:///{_HOME}/airflow.db"
os.environ["AIRFLOW__CORE__AUTH_MANAGER"] = (
    "airflow.api_fastapi.auth.managers.simple.simple_auth_manager.SimpleAuthManager"
)
os.environ["AIRFLOW__API_AUTH__JWT_SECRET"] = "local-test-jwt"
os.environ["AIRFLOW__CORE__FERNET_KEY"] = "mDcm7GibWr4ykbfhwNaePHmLbvzEdj5E7lNAK-Hj6qQ="
os.environ["AIRFLOW__CORE__DAGS_ARE_PAUSED_AT_CREATION"] = "True"
os.environ["PIX_DUCKDB_PATH"] = str(_HOME / "pix.duckdb")
os.environ["PIX_RAW_SOURCE"] = "local"
os.environ["PIX_RAW_ROOT"] = str(_HOME / "raw")
os.environ["S3_BUCKET"] = "pix-data-local"
os.environ["AIRFLOW__COSMOS__ENABLE_CACHE"] = "False"

import pytest  # noqa: E402

pytest.importorskip("airflow")
pytest.importorskip("cosmos")

from airflow.dag_processing.dagbag import DagBag  # noqa: E402

DAG_DIR = Path(__file__).resolve().parents[1] / "orchestration" / "dags"
EXPECTED = {"bcb_pix_monthly", "app_cdc_merge", "maintenance"}


@pytest.fixture(scope="module")
def dagbag() -> DagBag:
    return DagBag(dag_folder=DAG_DIR)


def test_dags_import(dagbag: DagBag) -> None:
    assert dagbag.import_errors == {}
    assert EXPECTED <= set(dagbag.dags)


def test_no_cycles_tags_owners_and_retries(dagbag: DagBag) -> None:
    assert dagbag.import_errors == {}
    for dag_id, dag in dagbag.dags.items():
        if dag_id not in EXPECTED:
            continue
        dag.check_cycle()
        assert dag.tags
        assert dag.catchup is False
        assert dag.default_args.get("owner") == "pix-data"
        assert dag.default_args.get("on_failure_callback") is not None
        assert dag.deadline is not None
        assert dag.tasks
        for task in dag.tasks:
            assert task.owner == "pix-data", task.task_id
            assert task.retries >= 1, task.task_id


def test_bcb_dag_maps_entities_and_limits_olinda(dagbag: DagBag) -> None:
    dag = dagbag.dags["bcb_pix_monthly"]
    ingest = dag.get_task("ingest_one")
    assert ingest.pool == "olinda"
    assert ingest.retries == 3
    assert ingest.retry_exponential_backoff
    task_ids = {task.task_id for task in dag.tasks}
    assert "publish_raw_bcb" in task_ids
    assert "source_freshness" in task_ids
    assert any("fct_transacoes_mensal" in task_id for task_id in task_ids)
    freshness = dag.get_task("source_freshness")
    assert freshness.pool == "duckdb"
    assert freshness.outlets


def test_cdc_dag_is_asset_or_time(dagbag: DagBag) -> None:
    dag = dagbag.dags["app_cdc_merge"]
    assert type(dag.timetable).__name__ == "AssetOrTimeSchedule"
    rendered = f"{dag.timetable.summary} {dag.timetable.asset_condition}"
    assert "raw/app" in rendered
    drain = dag.get_task("drain")
    assert drain.retries == 3
    assert drain.retry_exponential_backoff
    task_ids = {task.task_id for task in dag.tasks}
    assert any("cur_pix_key" in task_id for task_id in task_ids)


def test_maintenance_has_both_checks(dagbag: DagBag) -> None:
    dag = dagbag.dags["maintenance"]
    task_ids = {task.task_id for task in dag.tasks}
    assert task_ids == {"slot_lag", "quarantine"}
