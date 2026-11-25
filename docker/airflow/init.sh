#!/usr/bin/env bash
# Metadata database, then pools. Run once from the airflow-init service.
set -euo pipefail

python /opt/airflow/project/docker/airflow/bootstrap_db.py
airflow db migrate
airflow pools set olinda "${OLINDA_POOL_SLOTS:-1}" "One in-flight call to the BCB Olinda API"
airflow pools set duckdb "${DUCKDB_POOL_SLOTS:-1}" "One writer for the local DuckDB file"
