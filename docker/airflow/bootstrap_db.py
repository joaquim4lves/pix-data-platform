"""Create the Airflow role and database on the compose Postgres.

The official image only creates ``POSTGRES_DB``. Airflow metadata lives in its
own database so it is not part of the ``pix_app`` publication. Identifiers are
restricted to a short alphabet and the password is a parameter, not a literal.
"""

from __future__ import annotations

import os
import re

import psycopg

_IDENT = re.compile(r"[a-z_][a-z0-9_]{0,62}")


def _ident(value: str, label: str) -> str:
    if not _IDENT.fullmatch(value):
        raise SystemExit(f"{label} must match {_IDENT.pattern}, got {value!r}")
    return value


def main() -> None:
    host = os.environ.get("POSTGRES_HOST", "postgres")
    port = os.environ.get("POSTGRES_PORT", "5432")
    admin_user = os.environ.get("POSTGRES_USER", "pix")
    admin_password = os.environ.get("POSTGRES_PASSWORD", "pix")
    admin_db = os.environ.get("POSTGRES_DB", "pix")
    airflow_user = _ident(os.environ.get("AIRFLOW_DB_USER", "airflow"), "AIRFLOW_DB_USER")
    airflow_db = _ident(os.environ.get("AIRFLOW_DB_NAME", "airflow"), "AIRFLOW_DB_NAME")
    airflow_password = os.environ.get("AIRFLOW_DB_PASSWORD", "airflow")
    if airflow_password == "":
        raise SystemExit("AIRFLOW_DB_PASSWORD is empty")

    conn = psycopg.connect(
        host=host,
        port=port,
        user=admin_user,
        password=admin_password,
        dbname=admin_db,
        autocommit=True,
    )
    with conn.cursor() as cur:
        cur.execute("SELECT 1 FROM pg_roles WHERE rolname = %s", (airflow_user,))
        if cur.fetchone() is None:
            cur.execute(
                f'CREATE ROLE "{airflow_user}" LOGIN PASSWORD %s',
                (airflow_password,),
            )
        else:
            cur.execute(
                f'ALTER ROLE "{airflow_user}" WITH LOGIN PASSWORD %s',
                (airflow_password,),
            )
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (airflow_db,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{airflow_db}" OWNER "{airflow_user}"')
    conn.close()


if __name__ == "__main__":
    main()
