"""Load bundled fuel retail prices from CSV (no DB import)."""
from __future__ import annotations

import csv
from pathlib import Path

from django.conf import settings


def _default_csv_path() -> Path:
    return Path(settings.BASE_DIR) / "fuel_opt" / "scripts" / "fuel-prices-for-be-assessment.csv"


def load_fuel_rows(csv_path: Path | None = None) -> list[dict]:
    path = csv_path or _default_csv_path()
    if not path.exists():
        return []

    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                price = float(row.get("Retail Price", "").strip())
            except (TypeError, ValueError):
                continue
            rows.append(
                {
                    "name": (row.get("Truckstop Name") or "").strip(),
                    "address": (row.get("Address") or "").strip(),
                    "city": (row.get("City") or "").strip(),
                    "state": (row.get("State") or "").strip().upper(),
                    "price": price,
                }
            )
    return rows


def dedupe_min_price(rows: list[dict]) -> list[dict]:
    """One row per truck stop location; keep lowest retail price."""
    best: dict[tuple[str, str, str, str], dict] = {}
    for r in rows:
        key = (r["name"], r["address"], r["city"], r["state"])
        if key not in best or r["price"] < best[key]["price"]:
            best[key] = r
    return list(best.values())


def index_by_state(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        st = r["state"]
        if not st:
            continue
        out.setdefault(st, []).append(r)
    return out


_rows_cache: list[dict] | None = None
_by_state_cache: dict[str, list[dict]] | None = None


def format_station_address(row: dict) -> str:
    """Single-line US address for display and geocoding."""
    parts = [row.get("address", ""), row.get("city", ""), row.get("state", "")]
    body = ", ".join(p for p in parts if p)
    return f"{body}, USA" if body else ""


def get_fuel_data() -> tuple[list[dict], dict[str, list[dict]]]:
    global _rows_cache, _by_state_cache
    if _rows_cache is None:
        raw = load_fuel_rows()
        _rows_cache = dedupe_min_price(raw)
        _by_state_cache = index_by_state(_rows_cache)
    return _rows_cache, _by_state_cache  # type: ignore[return-value]
