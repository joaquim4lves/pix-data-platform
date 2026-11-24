"""Failure and deadline alerts. Slack is optional and comes from the environment.

``AIRFLOW_ALERT_SLACK_WEBHOOK_URL`` empty means log only. The value is never
written into the message body or the log line.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("orchestration.alerts")


def notify(event: str, message: str) -> None:
    logger.error("alert %s: %s", event, message)
    url = os.environ.get("AIRFLOW_ALERT_SLACK_WEBHOOK_URL", "").strip()
    if not url:
        return
    import httpx

    response = httpx.post(url, json={"text": f"[{event}] {message}"}, timeout=10.0)
    response.raise_for_status()


def on_failure(context: dict) -> None:
    """Task ``on_failure_callback``. Airflow passes the task context."""

    dag = context.get("dag")
    ti = context.get("task_instance") or context.get("ti")
    dag_id = getattr(dag, "dag_id", None) or context.get("dag_id") or "unknown"
    task_id = getattr(ti, "task_id", None) or context.get("task_id") or "unknown"
    notify("task_failed", f"{dag_id}.{task_id} failed")


def deadline_missed(context: dict | None = None, **_kwargs: object) -> None:
    """Synchronous deadline callback. Airflow 3 runs this in the executor."""

    dag_id = "unknown"
    if context:
        dag = context.get("dag")
        dag_id = getattr(dag, "dag_id", None) or str(context.get("dag_id") or dag_id)
    notify("deadline_missed", f"{dag_id} missed its deadline")
