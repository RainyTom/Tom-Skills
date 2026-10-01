#!/usr/bin/env python3
"""Fetch paper candidates for Google Scholar style retrieval.

Priority:
1) SerpAPI Google Scholar endpoint (requires SERPAPI_API_KEY)
2) Crossref bibliographic search fallback
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import requests

SERPAPI_URL = "https://serpapi.com/search.json"
CROSSREF_URL = "https://api.crossref.org/works"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch Google Scholar-like paper candidates."
    )
    parser.add_argument("--title", default="", help="Paper title for search")
    parser.add_argument("--query", default="", help="Raw query")
    parser.add_argument(
        "--title-candidates", type=int, default=10, help="Max candidates"
    )
    parser.add_argument("--output", default="", help="Optional output JSON file")
    parser.add_argument("--serpapi-key", default="", help="SerpAPI key (optional)")
    return parser.parse_args()


def fetch_with_serpapi(query: str, limit: int, api_key: str) -> list[dict[str, Any]]:
    params = {
        "engine": "google_scholar",
        "q": query,
        "num": limit,
        "hl": "en",
        "api_key": api_key,
    }
    response = requests.get(SERPAPI_URL, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    results = data.get("organic_results", [])

    out: list[dict[str, Any]] = []
    for item in results[:limit]:
        resources = item.get("resources", [])
        pdf_links = [
            r.get("link", "")
            for r in resources
            if "pdf" in (r.get("file_format", "") or "").lower()
        ]
        out.append(
            {
                "title": item.get("title", ""),
                "snippet": item.get("snippet", ""),
                "publication_info": item.get("publication_info", {}),
                "result_id": item.get("result_id", ""),
                "link": item.get("link", ""),
                "pdf_links": [u for u in pdf_links if u],
                "inline_cited_by_total": item.get("inline_links", {})
                .get("cited_by", {})
                .get("total", 0),
            }
        )
    return out


def fetch_with_crossref(query: str, limit: int) -> list[dict[str, Any]]:
    params = {
        "query.bibliographic": query,
        "rows": limit,
        "select": "DOI,title,author,published-print,published-online,container-title,URL,type,is-referenced-by-count,link",
    }
    response = requests.get(CROSSREF_URL, params=params, timeout=60)
    response.raise_for_status()
    items = response.json().get("message", {}).get("items", [])

    out: list[dict[str, Any]] = []
    for item in items[:limit]:
        title = item.get("title", [""])
        authors = []
        for author in item.get("author", []) or []:
            given = author.get("given", "")
            family = author.get("family", "")
            full = (given + " " + family).strip()
            if full:
                authors.append(full)

        links = item.get("link", []) or []
        pdf_links = [
            l.get("URL", "")
            for l in links
            if "application/pdf" in (l.get("content-type", "") or "")
        ]
        out.append(
            {
                "title": title[0] if title else "",
                "doi": item.get("DOI", ""),
                "authors": authors,
                "venue": (item.get("container-title") or [""])[0],
                "type": item.get("type", ""),
                "crossref_url": item.get("URL", ""),
                "cited_by": item.get("is-referenced-by-count", 0),
                "pdf_links": [u for u in pdf_links if u],
            }
        )
    return out


def main() -> int:
    args = parse_args()
    query = args.query.strip() or args.title.strip()
    if not query:
        raise SystemExit("Either --title or --query must be provided")

    api_key = args.serpapi_key.strip() or os.environ.get("SERPAPI_API_KEY", "").strip()
    source = "crossref-fallback"
    if api_key:
        try:
            candidates = fetch_with_serpapi(query, args.title_candidates, api_key)
            source = "google_scholar_serpapi"
        except Exception:
            candidates = fetch_with_crossref(query, args.title_candidates)
    else:
        candidates = fetch_with_crossref(query, args.title_candidates)

    payload = {
        "source": source,
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
