"""CDC drain and the incremental current-state models.

Runs at minute 15 of every hour, America/Sao_Paulo, or when the ``raw/app``
asset is updated. The drain task does not emit that asset: emitting it here
would schedule another run of this same DAG. Record the asset from outside
after a manual ``make apply``, or wait for the hour. The task outlets
``dbt://pix_data_platform/cur_app`` when freshness finishes.

Local only. The AWS sink is the SQS event source mapping on the CDC Lambda.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow.sdk import DAG, task
from airflow.sdk.definitions.callback import SyncCallback
from airflow.sdk.definitions.deadline import DeadlineAlert, DeadlineReference
from airflow.timetables.assets import AssetOrTimeSchedule
from airflow.timetables.trigger import CronTriggerTimetable
from orchestration.alerts import deadline_missed, on_failure
from orchestration.assets import CUR_APP, RAW_APP
from orchestration.cdc_flow import drain_cdc
from orchestration.cosmos_dbt import DUCKDB_POOL, cdc_dbt_group
from orchestration.dbt_cmd import CDC_FRESHNESS, run_source_freshness

BRAZIL = ZoneInfo("America/Sao_Paulo")

with DAG(
    dag_id="app_cdc_merge",
    description="Drain the local pgoutput slot and build incremental cur_* models.",
    schedule=AssetOrTimeSchedule(
        timetable=CronTriggerTimetable("15 * * * *", timezone=BRAZIL),
        assets=[RAW_APP],
    ),
    start_date=datetime(2020, 11, 1, tzinfo=BRAZIL),
    catchup=False,
    max_active_runs=1,
    tags=["pix", "cdc", "dbt"],
    default_args={
        "owner": "pix-data",
        "retries": 2,
        "retry_delay": timedelta(minutes=1),
        "on_failure_callback": on_failure,
    },
    on_failure_callback=on_failure,
    deadline=DeadlineAlert(
        reference=DeadlineReference.DAGRUN_QUEUED_AT,
        interval=timedelta(minutes=45),
        callback=SyncCallback(deadline_missed),
    ),
):

    @task(
        retries=3,
        retry_delay=timedelta(minutes=1),
        retry_exponential_backoff=True,
        max_retry_delay=timedelta(minutes=15),
    )
    def drain() -> dict[str, object]:
        return drain_cdc()

    @task(pool=DUCKDB_POOL, outlets=[CUR_APP])
    def source_freshness() -> None:
        run_source_freshness(CDC_FRESHNESS)

    drained = drain()
    drained >> cdc_dbt_group() >> source_freshness()
