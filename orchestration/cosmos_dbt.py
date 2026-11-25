"""Cosmos task groups for the dbt project.

Parse uses Cosmos's mock profile so importing the DAGs does not open DuckDB.
Execution uses ``transform/dbt/profiles.yml`` (the duckdb target). Model assets
from Cosmos stay off; ``orchestration.assets`` is the scheduling contract.

``dbt_deps`` is off. ``packages.yml`` is empty. The DuckDB file has one writer,
so every dbt task takes the ``duckdb`` pool.
"""

from __future__ import annotations

import shutil
import sys
from datetime import timedelta
from pathlib import Path

from cosmos import DbtTaskGroup, ExecutionConfig, ProfileConfig, ProjectConfig, RenderConfig
from cosmos.constants import ExecutionMode, LoadMode, TestBehavior

from orchestration.alerts import on_failure
from orchestration.dbt_cmd import BCB_SELECT, CDC_SELECT
from orchestration.paths import dbt_project_dir

DUCKDB_POOL = "duckdb"


def dbt_executable() -> str:
    """``dbt`` on ``PATH``, or the script next to the current interpreter.

    A venv ``python`` is a symlink to the system interpreter. Resolving it
    would look for ``dbt`` in ``/usr/bin`` and miss ``.venv/bin/dbt``.
    """

    found = shutil.which("dbt")
    if found:
        return found
    sibling = Path(sys.executable).parent / "dbt"
    if sibling.is_file():
        return str(sibling)
    raise FileNotFoundError("dbt is not installed. pip install -e '.[dev,airflow]'")


def dbt_group(*, group_id: str, select: tuple[str, ...]) -> DbtTaskGroup:
    project = dbt_project_dir()
    return DbtTaskGroup(
        group_id=group_id,
        project_config=ProjectConfig(
            dbt_project_path=project,
            install_dbt_deps=False,
        ),
        profile_config=ProfileConfig(
            profile_name="pix_data_platform",
            target_name="duckdb",
            profiles_yml_filepath=project / "profiles.yml",
        ),
        execution_config=ExecutionConfig(
            execution_mode=ExecutionMode.LOCAL,
            dbt_executable_path=dbt_executable(),
        ),
        render_config=RenderConfig(
            select=list(select),
            load_method=LoadMode.DBT_LS,
            test_behavior=TestBehavior.AFTER_ALL,
            emit_datasets=False,
            enable_mock_profile=True,
        ),
        operator_args={
            "pool": DUCKDB_POOL,
            "owner": "pix-data",
            "retries": 2,
            "retry_delay": timedelta(minutes=1),
            "on_failure_callback": on_failure,
        },
    )


def bcb_dbt_group() -> DbtTaskGroup:
    return dbt_group(group_id="dbt_bcb", select=BCB_SELECT)


def cdc_dbt_group() -> DbtTaskGroup:
    return dbt_group(group_id="dbt_cur", select=CDC_SELECT)
