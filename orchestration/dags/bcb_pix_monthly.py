"""Monthly BCB extract, then the dbt models that read it.

Schedule: 07:00 America/Sao_Paulo on the 2nd. ``catchup`` is off. A scheduled
run calls the incremental pipeline (watermark, last N months, partition
overwrite). History is a conf window or ``airflow dags backfill``. See the
local Airflow runbook.

The Olinda pool serializes entities. The client retries HTTP 500, and the
mapped task retries again with exponential backoff. AWS keeps EventBridge and
the ingest Lambda. This DAG is not deployed there.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow.sdk import DAG, task
from airflow.sdk.definitions.callback import SyncCallback
from airflow.sdk.definitions.deadline import DeadlineAlert, DeadlineReference
from airflow.timetables.trigger import CronTriggerTimetable
from orchestration.alerts import deadline_missed, on_failure
from orchestration.assets import BCB_MARTS, RAW_BCB
from orchestration.cosmos_dbt import DUCKDB_POOL, bcb_dbt_group
from orchestration.dbt_cmd import BCB_FRESHNESS, run_source_freshness
from orchestration.ingest import bcb_entity_names, ingest_entity
from orchestration.windows import IngestPlan, resolve_ingest_plan

BRAZIL = ZoneInfo("America/Sao_Paulo")
OWNER = "pix-data"
OLINDA_POOL = "olinda"

with DAG(
    dag_id="bcb_pix_monthly",
    description="Olinda entities, then dbt models and freshness for the BCB marts.",
    schedule=CronTriggerTimetable("0 7 2 * *", timezone=BRAZIL),
    start_date=datetime(2020, 11, 1, tzinfo=BRAZIL),
    catchup=False,
    max_active_runs=1,
    tags=["pix", "bcb", "ingestion", "dbt"],
    default_args={
        "owner": OWNER,
        "retries": 2,
        "retry_delay": timedelta(minutes=2),
        "on_failure_callback": on_failure,
    },
    on_failure_callback=on_failure,
    deadline=DeadlineAlert(
        reference=DeadlineReference.DAGRUN_QUEUED_AT,
        interval=timedelta(hours=6),
        callback=SyncCallback(deadline_missed),
    ),
):

    @task
    def plan_window(**context: object) -> dict[str, object]:
        dag_run = context["dag_run"]
        conf = getattr(dag_run, "conf", None)
        logical = context.get("logical_date")
        if logical is not None and not isinstance(logical, datetime):
            logical = None
        plan = resolve_ingest_plan(
            conf=conf if isinstance(conf, dict) else None,
            run_type=getattr(dag_run, "run_type", "manual"),
            logical_date=logical,
        )
        return {
            "mode": plan.mode,
            "start": plan.start,
            "end": plan.end,
            "lookback_months": plan.lookback_months,
        }

    @task
    def list_entities() -> list[str]:
        return bcb_entity_names()

    @task(
        pool=OLINDA_POOL,
        retries=3,
        retry_delay=timedelta(minutes=2),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=30),
    )
    def ingest_one(entity: str, plan: dict[str, object]) -> dict[str, object]:
        return ingest_entity(entity, IngestPlan(**plan))

    @task(outlets=[RAW_BCB])
    def publish_raw_bcb(results: list[dict[str, object]]) -> dict[str, int]:
        return {"entities": len(results)}

    @task(pool=DUCKDB_POOL, outlets=[BCB_MARTS])
    def source_freshness() -> None:
        run_source_freshness(BCB_FRESHNESS)

    window = plan_window()
    ingested = ingest_one.partial(plan=window).expand(entity=list_entities())
    published = publish_raw_bcb(ingested)
    published >> bcb_dbt_group() >> source_freshness()
