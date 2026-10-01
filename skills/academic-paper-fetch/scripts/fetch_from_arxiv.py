#!/usr/bin/env python3
"""Fetch arXiv paper candidates by title or query and optionally download a PDF."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import requests

ARXIV_API = "https://export.arxiv.org/api/query"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch paper metadata from arXiv API.")
    parser.add_argument(
        "--title", default="", help="Paper title for title-first search"
    )
    parser.add_argument("--query", default="", help="Raw arXiv search query")
    parser.add_argument(
        "--title-candidates", type=int, default=10, help="Max candidates to return"
    )
    parser.add_argument("--output", default="", help="Optional output JSON file path")
    parser.add_argument(
        "--download-pdf", action="store_true", help="Download top-1 candidate PDF"
    )
    parser.add_argument(
        "--pdf-output", default="", help="PDF output path for --download-pdf"
    )
    return parser.parse_args()


def build_query(args: argparse.Namespace) -> str:
    if args.query.strip():
        return args.query.strip()
    if args.title.strip():
        safe_title = re.sub(r"\s+", " ", args.title.strip())
        return f'ti:"{safe_title}"'
    raise ValueError("Either --title or --query must be provided")


def parse_entry(entry: ET.Element, ns: dict[str, str]) -> dict[str, Any]:
    links = entry.findall("atom:link", ns)
    pdf_url = ""
    for link in links:
        if link.attrib.get("title") == "pdf":
            pdf_url = link.attrib.get("href", "")
            break

    authors = [
        a.findtext("atom:name", default="", namespaces=ns).strip()
        for a in entry.findall("atom:author", ns)
    ]
    category = [c.attrib.get("term", "") for c in entry.findall("atom:category", ns)]

    return {
        "id": entry.findtext("atom:id", default="", namespaces=ns).strip(),
        "title": entry.findtext("atom:title", default="", namespaces=ns)
        .strip()
        .replace("\n", " "),
        "summary": entry.findtext("atom:summary", default="", namespaces=ns)
        .strip()
        .replace("\n", " "),
        "published": entry.findtext(
            "atom:published", default="", namespaces=ns
        ).strip(),
        "updated": entry.findtext("atom:updated", default="", namespaces=ns).strip(),
        "authors": [a for a in authors if a],
        "categories": [c for c in category if c],
        "pdf_url": pdf_url,
    }


def fetch_candidates(query: str, max_results: int) -> list[dict[str, Any]]:
    params = f"search_query={quote_plus(query)}&start=0&max_results={max_results}"
    url = f"{ARXIV_API}?{params}"
    response = requests.get(url, timeout=60)
    response.raise_for_status()

    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)
    return [parse_entry(entry, ns) for entry in entries]


def download_pdf(pdf_url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(pdf_url, timeout=120)
    response.raise_for_status()
    output_path.write_bytes(response.content)


def main() -> int:
    args = parse_args()
    query = build_query(args)
    candidates = fetch_candidates(query, args.title_candidates)

    payload: dict[str, Any] = {
        "source": "arxiv",
        "query": query,
        "count": len(candidates),
        "candidates": candidates,
    }

    if args.download_pdf and candidates:
        top_pdf_url = candidates[0].get("pdf_url", "")
        if top_pdf_url:
            pdf_output = Path(args.pdf_output) if args.pdf_output else Path("paper.pdf")
            download_pdf(top_pdf_url, pdf_output)
            payload["downloaded_pdf"] = str(pdf_output)

    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.output:
        output_file = Path(args.output)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(text + "\n", encoding="utf-8")

    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
