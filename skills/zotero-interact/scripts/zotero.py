#!/usr/bin/env python3
"""
Zotero Local API Helper Script

Interact with Zotero's local REST API at http://127.0.0.1:23119/api/

Usage:
    python3 zotero.py list [--limit N]
    python3 zotero.py search <query>
    python3 zotero.py get <itemKey>
    python3 zotero.py add --type <itemType> --title "..." [--creators "A, B"] [--date "2024"] [--doi "..."]
    python3 zotero.py fetch-doi <DOI>
    python3 zotero.py collections
    python3 zotero.py collection-items <collectionKey>
    python3 zotero.py tags
    python3 zotero.py export-bibtex [--limit N]
    python3 zotero.py delete <itemKey>
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import urllib.parse

API_BASE = "http://127.0.0.1:23119"
HEADERS = {"Content-Type": "application/json", "Zotero-API-Version": "3"}
# Local user library path prefix (0 = local user shortcut)
USER_PREFIX = "/api/users/0"


def _request(method, path, data=None, params=None):
    """Make an HTTP request to the Zotero API."""
    url = f"{API_BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = urllib.request.Request(url, data=body, method=method, headers=HEADERS)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8")
            # Parse JSON if possible; some endpoints return text
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return content
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        print(f"HTTP {e.code}: {e.reason}", file=sys.stderr)
        if body:
            print(body, file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: Cannot connect to Zotero at {API_BASE}", file=sys.stderr)
        print(
            f"Make sure Zotero is running and the local API is enabled.",
            file=sys.stderr,
        )
        print(f"Details: {e.reason}", file=sys.stderr)
        sys.exit(1)


def cmd_list(args):
    """List recent items."""
    params = {"limit": args.limit, "sort": "dateAdded", "direction": "desc"}
    data = _request("GET", f"{USER_PREFIX}/items", params=params)
    _print_items(data)


def cmd_search(args):
    """Search items by query string."""
    params = {"q": args.query, "limit": args.limit, "qmode": "everything"}
    data = _request("GET", f"{USER_PREFIX}/items", params=params)
    _print_items(data)


def cmd_get(args):
    """Get a single item by its key."""
    item = _request("GET", f"{USER_PREFIX}/items/{args.item_key}")
    print(json.dumps(item, indent=2, ensure_ascii=False))


def cmd_add(args):
    """Add a new item to the library."""
    item_data = {"itemType": args.type}

    if args.title:
        item_data["title"] = args.title
    if args.date:
        item_data["date"] = args.date
    if args.doi:
        item_data["DOI"] = args.doi
    if args.creators:
        creators = []
        for c in args.creators:
            parts = c.split(",", 1)
            if len(parts) == 2:
                creators.append(
                    {
                        "firstName": parts[1].strip(),
                        "lastName": parts[0].strip(),
                        "creatorType": "author",
                    }
                )
            else:
                creators.append({"lastName": parts[0].strip(), "creatorType": "author"})
        item_data["creators"] = creators
    if args.extra:
        item_data["extra"] = args.extra

    payload = {"items": [item_data]}
    result = _request("POST", f"{USER_PREFIX}/items", data=payload)
    print("Item created successfully.")
    if isinstance(result, list) and len(result) > 0:
        print(f"  Key: {result[0].get('key', 'unknown')}")
        if result[0].get("uri"):
            print(f"  URI: {result[0]['uri']}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_fetch_doi(args):
    """Add an item by DOI (metadata fetched automatically by Zotero)."""
    payload = {"items": [{"DOI": args.doi}]}
    result = _request("POST", f"{USER_PREFIX}/items", data=payload)
    print(f"Item fetched from DOI '{args.doi}':")
    if isinstance(result, list) and len(result) > 0:
        print(f"  Key: {result[0].get('key', 'unknown')}")
        print(f"  Title: {result[0].get('data', {}).get('title', 'N/A')}")
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_collections(args):
    """List all collections."""
    data = _request("GET", f"{USER_PREFIX}/collections")
    if not data:
        print("No collections found.")
        return
    print(f"{'Collection Key':<20} {'Name':<40}")
    print("-" * 60)
    for col in data:
        key = col.get("key", "")
        name = col.get("data", {}).get("name", "")
        print(f"{key:<20} {name:<40}")


def cmd_collection_items(args):
    """List items in a collection."""
    params = {"limit": args.limit}
    data = _request(
        "GET", f"{USER_PREFIX}/collections/{args.collection_key}/items", params=params
    )
    _print_items(data)


def cmd_tags(args):
    """List all tags."""
    data = _request("GET", f"{USER_PREFIX}/tags")
    if not data:
        print("No tags found.")
        return
    for tag in data:
        tag_data = tag.get("data", tag)
        print(f"  {tag_data.get('tag', '')}")


def cmd_export_bibtex(args):
    """Export items in BibTeX format."""
    params = {"limit": args.limit, "format": "bibtex"}
    data = _request("GET", f"{USER_PREFIX}/items", params=params)
    if isinstance(data, str):
        print(data)
    else:
        print("Failed to export BibTeX. The response was not text.")


def cmd_delete(args):
    """Delete an item by its key (requires version)."""
    # First, fetch the item to get its current version
    item = _request("GET", f"{USER_PREFIX}/items/{args.item_key}")
    if isinstance(item, dict):
        version = item.get("version", 0)
        req = urllib.request.Request(
            f"{API_BASE}{USER_PREFIX}/items/{args.item_key}",
            method="DELETE",
            headers={**HEADERS, "If-Unmodified-Since-Version": str(version)},
        )
        try:
            with urllib.request.urlopen(req) as resp:
                print(f"Item {args.item_key} deleted successfully.")
        except urllib.error.HTTPError as e:
            print(f"Delete failed: HTTP {e.code} {e.reason}", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"Item {args.item_key} not found.", file=sys.stderr)
        sys.exit(1)


def _print_items(data):
    """Pretty-print a list of items."""
    items = (
        data
        if isinstance(data, list)
        else data.get("data", data)
        if isinstance(data, dict)
        else []
    )
    if isinstance(items, dict):
        items = [items]

    if not items:
        print("No items found.")
        return

    print(f"{'Item Key':<20} {'Title':<60} {'Date':<12} {'Item Type':<20}")
    print("-" * 112)
    for item in items:
        d = item.get("data", item)
        key = item.get("key", d.get("key", ""))
        title = (d.get("title", "") or "")[:57]
        date = (d.get("date", "") or "")[:10]
        itype = (d.get("itemType", "") or "")[:18]
        print(f"{key:<20} {title:<60} {date:<12} {itype:<20}")


def main():
    parser = argparse.ArgumentParser(
        description="Zotero Local API Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # list
    p_list = sub.add_parser("list", help="List recent items")
    p_list.add_argument("--limit", type=int, default=10)

    # search
    p_search = sub.add_parser("search", help="Search items")
    p_search.add_argument("query", help="Search query (title, author, year, etc.)")
    p_search.add_argument("--limit", type=int, default=20)

    # get
    p_get = sub.add_parser("get", help="Get item by key")
    p_get.add_argument("item_key", help="Zotero item key")

    # add
    p_add = sub.add_parser("add", help="Add a new item")
    p_add.add_argument(
        "--type",
        required=True,
        help="Item type (journalArticle, book, conferencePaper, etc.)",
    )
    p_add.add_argument("--title", help="Item title")
    p_add.add_argument(
        "--creators", nargs="*", help="Creators as 'LastName, FirstName'"
    )
    p_add.add_argument("--date", help="Publication date")
    p_add.add_argument("--doi", help="DOI")
    p_add.add_argument("--extra", help="Extra metadata")

    # fetch-doi
    p_fetch = sub.add_parser("fetch-doi", help="Add item by DOI (auto-fetched)")
    p_fetch.add_argument("doi", help="DOI to fetch")

    # collections
    sub.add_parser("collections", help="List all collections")

    # collection-items
    p_citems = sub.add_parser("collection-items", help="List items in a collection")
    p_citems.add_argument("collection_key", help="Collection key")
    p_citems.add_argument("--limit", type=int, default=50)

    # tags
    sub.add_parser("tags", help="List all tags")

    # export-bibtex
    p_export = sub.add_parser("export-bibtex", help="Export items in BibTeX format")
    p_export.add_argument("--limit", type=int, default=100)

    # delete
    p_del = sub.add_parser("delete", help="Delete an item")
    p_del.add_argument("item_key", help="Item key to delete")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "list": cmd_list,
        "search": cmd_search,
        "get": cmd_get,
        "add": cmd_add,
        "fetch-doi": cmd_fetch_doi,
        "collections": cmd_collections,
        "collection-items": cmd_collection_items,
        "tags": cmd_tags,
        "export-bibtex": cmd_export_bibtex,
        "delete": cmd_delete,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
