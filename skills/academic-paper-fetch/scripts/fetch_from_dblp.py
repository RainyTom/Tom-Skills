#!/usr/bin/env python3
"""Fetch paper candidates from DBLP search API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import requests

DBLP_API = "https://dblp.org/search/publ/api"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch paper metadata from DBLP.")
    parser.add_argument("--title", default="", help="Paper title for search")
    parser.add_argument("--query", default="", help="Raw DBLP query")
    parser.add_argument(
        "--title-candidates", type=int, default=10, help="Max candidates"
    )
    parser.add_argument("--output", default="", help="Optional output JSON file")
    return parser.parse_args()


def normalize_authors(author_field: Any) -> list[str]:
    if isinstance(author_field, dict):
        name = author_field.get("text", "")
        return [name] if name else []
    if isinstance(author_field, list):
        out: list[str] = []
        for entry in author_field:
            if isinstance(entry, dict) and entry.get("text"):
                out.append(entry["text"])
        return out
    return []


def fetch_candidates(query: str, max_results: int) -> list[dict[str, Any]]:
    url = f"{DBLP_API}?q={quote_plus(query)}&h={max_results}&format=json"
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    data = response.json()

    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    if isinstance(hits, dict):
        hits = [hits]

    candidates: list[dict[str, Any]] = []
    for hit in hits:
        info = hit.get("info", {})
        ee = info.get("ee", "")
        if isinstance(ee, list):
            ee_links = ee
        elif isinstance(ee, str):
            ee_links = [ee]
        else:
            ee_links = []

        candidates.append(
            {
                "title": info.get("title", ""),
                "authors": normalize_authors(info.get("authors", {}).get("author", [])),
                "year": info.get("year", ""),
                "venue": info.get("venue", ""),
                "type": info.get("type", ""),
                "dblp_url": info.get("url", ""),
                "ee_links": ee_links,
            }
        )

    return candidates


def main() -> int:
    args = parse_args()
    query = args.query.strip() or args.title.strip()
    if not query:
        raise SystemExit("Either --title or --query must be provided")

    candidates = fetch_candidates(query, args.title_candidates)
    payload = {
        "source": "dblp",
        "query": query,
        "count": len(candidates),
        "candidates": candidates,
    }

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(text + "\n", encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
