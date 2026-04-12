from __future__ import annotations

from pathlib import Path
import re

import pandas as pd

from app.models import TaxonomyEntry


def normalize_text(s: str) -> str:
    s = "" if s is None else str(s)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def build_path_string(row: pd.Series) -> str:
    levels = [
        row.get("tier1", ""),
        row.get("tier2", ""),
        row.get("tier3", ""),
        row.get("tier4", ""),
    ]
    return " > ".join([normalize_text(value) for value in levels if normalize_text(value)])


def load_taxonomy(path: str | Path) -> list[TaxonomyEntry]:
    taxonomy_path = Path(path)
    if not taxonomy_path.exists():
        raise FileNotFoundError(f"Taxonomy TSV not found: {taxonomy_path}")

    df = pd.read_csv(taxonomy_path, sep="\t", dtype=str).fillna("")

    normalized_cols = {}
    for column in df.columns:
        key = column.strip().lower()
        key = re.sub(r"\s+", " ", key)
        normalized_cols[column] = key
    df = df.rename(columns=normalized_cols)

    rename_map = {
        "unique id": "unique_id",
        "parent": "parent_id",
        "tier 1": "tier1",
        "tier 2": "tier2",
        "tier 3": "tier3",
        "tier 4": "tier4",
        "description": "description",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    required = ["unique_id", "parent_id", "tier1", "tier2", "description"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing expected columns in TSV: {missing}")

    if "tier3" not in df.columns:
        df["tier3"] = ""
    if "tier4" not in df.columns:
        df["tier4"] = ""

    for column in ("tier1", "tier2", "tier3", "tier4", "description"):
        df[column] = df[column].map(normalize_text)

    df["unique_id"] = pd.to_numeric(df["unique_id"], errors="coerce")
    df["parent_id"] = pd.to_numeric(df["parent_id"], errors="coerce")
    df = df[df["unique_id"].notna()].copy()
    df["unique_id"] = df["unique_id"].astype(int)
    df["path"] = df.apply(build_path_string, axis=1)

    entries = [
        TaxonomyEntry(
            unique_id=int(row["unique_id"]),
            parent_id=None if pd.isna(row["parent_id"]) else int(row["parent_id"]),
            tier1=row["tier1"],
            tier2=row["tier2"],
            tier3=row["tier3"],
            tier4=row["tier4"],
            path=row["path"],
            description=row["description"],
        )
        for _, row in df.iterrows()
    ]

    if not entries:
        raise ValueError(f"No taxonomy entries found in {taxonomy_path}")
    return entries
