"""Create the PIX Open Data collection from dashboards/metabase.

Idempotent: dashboards and questions in that collection are replaced.
The warehouse is built first, unless data/pix.duckdb already exists.
Set METABASE_REBUILD=1 to load the seeded extract again. Stop Metabase
before a rebuild, because the driver holds the DuckDB file.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx

from dashboards.sample import write_demo
from dashboards.validate import problems

ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = Path(__file__).resolve().parent / "metabase" / "collection.json"
NS = uuid.UUID("8f3c2a1e-6b7d-4e90-9c1a-2d4e5f607182")


def _uuid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def build_warehouse() -> Path:
    database = Path(_env("PIX_DUCKDB_PATH", str(ROOT / "data" / "pix.duckdb")))
    raw = Path(_env("PIX_DEMO_ROOT", str(ROOT / "data" / "demo-raw")))
    if database.exists() and os.environ.get("METABASE_REBUILD") != "1":
        print(f"reusing {database}")
        return database
    if database.exists():
        database.unlink()
    raw.mkdir(parents=True, exist_ok=True)
    print("writing seeded extract")
    write_demo(raw)
    env = os.environ.copy()
    env["PIX_RAW_SOURCE"] = "local"
    env["PIX_RAW_ROOT"] = str(raw)
    env["PIX_DUCKDB_PATH"] = str(database)
    env["PIX_AS_OF_DATE"] = _env("PIX_AS_OF_DATE", "2026-11-25")
    database.parent.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "transform.dbt_main",
        "build",
        "--project-dir",
        str(ROOT / "transform" / "dbt"),
        "--profiles-dir",
        str(ROOT / "transform" / "dbt"),
        "--vars",
        json.dumps({"pix_as_of_date": env["PIX_AS_OF_DATE"]}),
    ]
    completed = subprocess.run(command, cwd=ROOT, env=env, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    import duckdb

    connection = duckdb.connect(str(database))
    connection.execute("CHECKPOINT")
    connection.close()
    database.chmod(0o666)
    database.parent.chmod(0o777)
    return database


def _as_date(value: object) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise RuntimeError(f"unexpected month boundary {value!r}")


def _range(connection: object, sql: str) -> str:
    start, end = connection.execute(sql).fetchone()  # type: ignore[attr-defined]
    start_day = _as_date(start)
    end_day = _as_date(end)
    last = (end_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    return f"{start_day.isoformat()}~{last.isoformat()}"


def defaults(database: Path) -> dict[str, str]:
    import duckdb

    connection = duckdb.connect(str(database), read_only=True)
    try:
        transactions = _range(
            connection,
            """
            select min(month_start), max(month_start)
            from (
                select distinct month_start
                from marts.fct_pix_transactions
                where is_complete_month
                order by month_start desc
                limit 12
            ) as recent
            """,
        )
        med = _range(
            connection,
            """
            select min(month_start), max(month_start)
            from marts.fct_pix_med
            where is_complete_month and ano_mes >= 202201
            """,
        )
    finally:
        connection.close()
    return {"computed:transactions_last_12": transactions, "computed:med_full": med}


class Metabase:
    def __init__(self, base: str) -> None:
        self.base = base.rstrip("/")
        self.client = httpx.Client(base_url=self.base, timeout=60)
        self.token = ""

    def wait(self) -> None:
        deadline = time.time() + 240
        while time.time() < deadline:
            try:
                response = self.client.get("/api/health")
                if response.status_code == 200 and response.json().get("status") == "ok":
                    return
            except httpx.HTTPError:
                pass
            time.sleep(3)
        raise RuntimeError("Metabase did not become healthy")

    def login(self) -> None:
        email = _env("MB_EMAIL", "pix@example.com")
        password = _env("MB_PASSWORD", "PixLocal-1a")
        properties = self.client.get("/api/session/properties")
        properties.raise_for_status()
        setup = properties.json().get("setup-token")
        if setup:
            response = self.client.post(
                "/api/setup",
                json={
                    "token": setup,
                    "user": {
                        "email": email,
                        "first_name": "PIX",
                        "last_name": "Local",
                        "password": password,
                    },
                    "prefs": {
                        "site_name": "PIX Open Data",
                        "site_locale": "en",
                        "allow_tracking": False,
                    },
                },
            )
            _raise(response)
            self.token = response.json()["id"]
        else:
            response = self.client.post(
                "/api/session",
                json={"username": email, "password": password},
            )
            _raise(response)
            self.token = response.json()["id"]
        self.client.headers["X-Metabase-Session"] = self.token

    def database(self, name: str, path: str) -> int:
        existing = self.client.get("/api/database")
        _raise(existing)
        for item in existing.json().get("data", []):
            if item["name"] == name:
                return int(item["id"])
        payload = {
            "engine": "duckdb",
            "name": name,
            "auto_run_queries": True,
            "details": {"database_file": path, "read_only": True},
        }
        response = self.client.post("/api/database", json=payload)
        if response.status_code >= 400:
            payload["details"] = {"database_file": path}
            response = self.client.post("/api/database", json=payload)
        _raise(response)
        return int(response.json()["id"])

    def fields(self, database_id: int) -> dict[tuple[str, str], int]:
        deadline = time.time() + 180
        found: dict[tuple[str, str], int] = {}
        while time.time() < deadline:
            self.client.post(f"/api/database/{database_id}/sync_schema")
            response = self.client.get(f"/api/database/{database_id}/metadata")
            _raise(response)
            found = {}
            for table in response.json().get("tables", []):
                if table.get("schema") not in (None, "marts"):
                    continue
                for field in table.get("fields", []):
                    found[(table["name"], field["name"])] = int(field["id"])
            if ("fct_pix_transactions", "month_start") in found and (
                "fct_pix_med",
                "month_start",
            ) in found:
                return found
            time.sleep(3)
        raise RuntimeError("DuckDB metadata did not include the dashboard marts")

    def collection(self, name: str, parent: int | None) -> int:
        response = self.client.get("/api/collection")
        _raise(response)
        for item in response.json():
            if item.get("name") == name and item.get("personal_owner_id") is None:
                if parent is None or item.get("parent_id") == parent:
                    return int(item["id"])
        created = self.client.post(
            "/api/collection",
            json={"name": name, "parent_id": parent, "description": name},
        )
        _raise(created)
        return int(created.json()["id"])

    def clear(self, collection_id: int) -> None:
        response = self.client.get(f"/api/collection/{collection_id}/items", params={"limit": 200})
        _raise(response)
        items = response.json().get("data", [])
        for model in ("dashboard", "card"):
            for item in items:
                if item.get("model") == model:
                    deleted = self.client.delete(f"/api/{model}/{item['id']}")
                    if deleted.status_code not in (200, 204):
                        archived = self.client.put(
                            f"/api/{model}/{item['id']}",
                            json={"archived": True},
                        )
                        _raise(archived)


def _raise(response: httpx.Response) -> None:
    if response.status_code >= 400:
        detail = response.text[:500]
        raise RuntimeError(
            f"{response.request.method} {response.request.url} -> {response.status_code} {detail}"
        )


def _tags(question: dict, field_ids: dict[tuple[str, str], int]) -> dict:
    tags = {}
    for tag in question.get("tags", []):
        body: dict = {
            "id": _uuid(f"tag:{question['key']}:{tag['name']}"),
            "name": tag["name"],
            "display-name": tag["name"],
            "type": tag["type"],
        }
        if tag["type"] == "dimension":
            field_id = field_ids.get((tag["field"][0], tag["field"][1]))
            if field_id is None:
                raise RuntimeError(f"no field {tag['field']} for {question['key']}")
            body["dimension"] = ["field", field_id, None]
            body["widget-type"] = tag["widget"]
        else:
            body["required"] = bool(tag.get("required"))
            if "default" in tag:
                body["default"] = tag["default"]
        tags[tag["name"]] = body
    return tags


def _resolve_default(value: object, ranges: dict[str, str]) -> object:
    if isinstance(value, str) and value in ranges:
        return ranges[value]
    return value


def provision() -> None:
    spec = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
    found = problems(spec)
    if found:
        raise SystemExit("\n".join(found))
    database = build_warehouse()
    ranges = defaults(database)
    metabase = Metabase(_env("MB_URL", "http://localhost:3000"))
    print("waiting for Metabase")
    metabase.wait()
    metabase.login()
    database_id = metabase.database(spec["database_name"], spec["duckdb_path"])
    field_ids = metabase.fields(database_id)
    parent = metabase.collection(spec["collection"], None)
    library = metabase.collection(spec["questions_collection"], parent)
    metabase.clear(parent)
    metabase.clear(library)
    card_ids: dict[str, int] = {}
    for question in spec["questions"]:
        sql = (SPEC_PATH.parent / "sql" / question["sql"]).read_text(encoding="utf-8")
        viz = dict(question.get("viz") or {})
        viz.setdefault("empty.title", spec["empty_state"])
        response = metabase.client.post(
            "/api/card",
            json={
                "name": question["name"],
                "description": question.get("description") or spec["empty_state"],
                "collection_id": library,
                "display": question["display"],
                "visualization_settings": viz,
                "dataset_query": {
                    "type": "native",
                    "database": database_id,
                    "native": {"query": sql, "template-tags": _tags(question, field_ids)},
                },
            },
        )
        _raise(response)
        card_ids[question["key"]] = int(response.json()["id"])
    questions = {item["key"]: item for item in spec["questions"]}
    for dashboard in spec["dashboards"]:
        parameters = []
        for parameter in dashboard["parameters"]:
            body = dict(parameter)
            if "default" in body:
                body["default"] = _resolve_default(body["default"], ranges)
            parameters.append(body)
        created = metabase.client.post(
            "/api/dashboard",
            json={
                "name": dashboard["name"],
                "description": dashboard["description"],
                "collection_id": parent,
                "parameters": parameters,
                "width": dashboard.get("width", "fixed"),
            },
        )
        _raise(created)
        dashboard_id = int(created.json()["id"])
        dashcards = []
        for index, card in enumerate(dashboard["cards"]):
            question = questions[card["question"]]
            mappings = []
            for tag in question.get("tags", []):
                mappings.append(
                    {
                        "parameter_id": tag["name"],
                        "card_id": card_ids[card["question"]],
                        "target": [
                            "dimension" if tag["type"] == "dimension" else "variable",
                            ["template-tag", tag["name"]],
                        ],
                    }
                )
            viz: dict = {}
            click = card.get("click")
            if click:
                viz["click_behavior"] = {
                    "type": "crossfilter",
                    "parameterMapping": {
                        click["parameter"]: {
                            "id": click["parameter"],
                            "source": {
                                "type": "column",
                                "id": click["column"],
                                "name": click["column"],
                            },
                            "target": {"type": "parameter", "id": click["parameter"]},
                        }
                    },
                }
            dashcards.append(
                {
                    "id": -index - 1,
                    "card_id": card_ids[card["question"]],
                    "row": card["row"],
                    "col": card["col"],
                    "size_x": card["size_x"],
                    "size_y": card["size_y"],
                    "parameter_mappings": mappings,
                    "visualization_settings": viz,
                }
            )
        for index, block in enumerate(dashboard["texts"]):
            dashcards.append(
                {
                    "id": -(100 + index),
                    "card_id": None,
                    "row": block["row"],
                    "col": block["col"],
                    "size_x": block["size_x"],
                    "size_y": block["size_y"],
                    "parameter_mappings": [],
                    "visualization_settings": {
                        "text": block["text"],
                        "virtual_card": {
                            "name": None,
                            "display": "text",
                            "dataset_query": {},
                            "visualization_settings": {},
                            "archived": False,
                        },
                    },
                }
            )
        updated = metabase.client.put(
            f"/api/dashboard/{dashboard_id}",
            json={"dashcards": dashcards, "parameters": parameters},
        )
        _raise(updated)
        print(f"{dashboard['name']}: {metabase.base}/dashboard/{dashboard_id}")
    _smoke(metabase, database_id)


def _smoke(metabase: Metabase, database_id: int) -> None:
    response = metabase.client.post(
        "/api/dataset",
        json={
            "database": database_id,
            "type": "native",
            "native": {
                "query": "select banner, gap_note from marts.fct_pix_publication",
            },
        },
    )
    _raise(response)
    rows = response.json().get("data", {}).get("rows", [])
    if not rows or "September" not in str(rows[0][1]):
        raise RuntimeError(f"publication banner was not the seeded September gap: {rows}")
    print("provisioned", rows[0][0])


def main() -> int:
    provision()
    return 0


if __name__ == "__main__":
    sys.exit(main())
