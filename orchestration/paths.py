"""Repository paths that stay valid when the DAG folder is bind-mounted."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Directory that contains ``ingestion``, ``transform``, and ``orchestration``.

    Resolved from this module, which is imported via ``PYTHONPATH``, not from
    the DAG file. In Compose the DAG folder is ``/opt/airflow/dags`` while the
    repository is ``/opt/airflow/project``.
    """

    return Path(__file__).resolve().parents[1]


def dbt_project_dir() -> Path:
    return repo_root() / "transform" / "dbt"
