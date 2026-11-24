"""Daily slot-lag and quarantine report. Local Postgres and the raw bucket.

A missing replication slot is an alert in the log, not a failure. Lag over
the configured byte limit fails the task. Any object under ``quarantine/``
fails the task. Both use the same log or Slack callback as the other DAGs.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from airflow.sdk import DAG, task
from airflow.sdk.definitions.callback import SyncCallback
from airflow.sdk.definitions.deadline import DeadlineAlert, DeadlineReference
from airflow.timetables.trigger import CronTriggerTimetable
from orchestration.alerts import deadline_missed, on_failure
from orchestration.maintenance import report_quarantine, report_slot_lag

BRAZIL = ZoneInfo("America/Sao_Paulo")

with DAG(
    dag_id="maintenance",
    description="Replication slot lag and the BCB quarantine prefix.",
    schedule=CronTriggerTimetable("0 8 * * *", timezone=BRAZIL),
    start_date=datetime(2020, 11, 1, tzinfo=BRAZIL),
    catchup=False,
    max_active_runs=1,
    tags=["pix", "maintenance"],
    default_args={
        "owner": "pix-data",
        "retries": 1,
        "retry_delay": timedelta(minutes=5),
        "on_failure_callback": on_failure,
    },
    on_failure_callback=on_failure,
    deadline=DeadlineAlert(
        reference=DeadlineReference.DAGRUN_QUEUED_AT,
        interval=timedelta(minutes=30),
        callback=SyncCallback(deadline_missed),
    ),
):

    @task
    def slot_lag() -> dict[str, object]:
        return report_slot_lag()

    @task
    def quarantine() -> dict[str, object]:
        return report_quarantine()

    slot_lag()
    quarantine()
