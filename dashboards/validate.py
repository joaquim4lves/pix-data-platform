"""Check the versioned Metabase definitions without starting Metabase."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "metabase"
FORBIDDEN = ("vlcompra", "vldinespec", "mesmatit", "fraud cases")
FORBIDDEN_SUMS = (
    "valor_pagador + valor_recebedor",
    "valor_recebedor + valor_pagador",
    "quantidade_pagador + quantidade_recebedor",
)
REQUIRED = {
    "q1_tx_count",
    "q1_tx_value",
    "q1_ticket",
    "q1_dict_users",
    "q2_trend",
    "q3_natureza",
    "q3_matrix",
    "q4_iniciacao",
    "q4_finalidade",
    "q5_users",
    "q5_keys",
    "q5_participants",
    "q6_kpi_value",
    "q6_kpi_payments",
    "q6_kpi_people",
    "q6_region",
    "q6_state",
    "q6_table",
    "q9_section",
    "q9_ticket_section",
    "q10a",
    "q_ratio",
    "q10b",
    "q8_age",
    "q7_flow",
}
FOOTER = "Source: Banco Central do Brasil, Estatísticas do Pix."
RATIO = "Approximate ratio computed by this portfolio"


def load() -> dict:
    return json.loads((ROOT / "collection.json").read_text(encoding="utf-8"))


def problems(spec: dict | None = None) -> list[str]:
    spec = spec if spec is not None else load()
    found: list[str] = []
    if spec.get("collection") != "PIX Open Data":
        found.append("collection must be named PIX Open Data")
    if spec.get("questions_collection") != "source questions":
        found.append("question library must be named source questions")
    if spec.get("empty_state") != "No data for this period.":
        found.append("empty state text is missing")
    questions = {item["key"]: item for item in spec["questions"]}
    missing = REQUIRED - set(questions)
    if missing:
        found.append(f"missing questions: {sorted(missing)}")
    names = [item["name"] for item in spec["dashboards"]]
    for expected in ("PIX at a glance", "Where it moves", "Receivers and MED"):
        if expected not in names:
            found.append(f"missing dashboard {expected}")
    for dashboard in spec["dashboards"]:
        texts = " ".join(block["text"] for block in dashboard["texts"])
        if FOOTER not in texts:
            found.append(f"{dashboard['name']} is missing the SPI footer")
        for card in dashboard["cards"]:
            if card["col"] + card["size_x"] > 24:
                found.append(f"{card['question']} extends past the 24-column grid")
    if RATIO not in json.dumps(spec):
        found.append("the SPI ratio caption is missing")
    for item in spec["questions"]:
        path = ROOT / "sql" / item["sql"]
        if not path.is_file():
            found.append(f"missing SQL file {item['sql']}")
            continue
        sql = path.read_text(encoding="utf-8").lower()
        for token in FORBIDDEN:
            if token in sql:
                found.append(f"{item['key']} contains {token}")
        for token in FORBIDDEN_SUMS:
            if token in sql:
                found.append(f"{item['key']} adds payer and receiver")
        for tag in item.get("tags", []):
            if "{{" + tag["name"] + "}}" not in path.read_text(encoding="utf-8"):
                found.append(f"{item['key']} declares unused tag {tag['name']}")
    return found


def main() -> int:
    found = problems()
    if found:
        print("\n".join(found), file=sys.stderr)
        return 1
    print(f"dashboard definitions ok ({len(load()['questions'])} questions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
