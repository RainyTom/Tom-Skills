---
name: zotero-interact
description: "Interact with Zotero reference manager via its local API (http://127.0.0.1:23119/api/). Use for: searching/retrieving items, managing collections, adding/updating/deleting references, exporting citations, querying tags, syncing libraries, and automating bibliography workflows. Trigger keywords: citation, reference, bibliography, zotero, paper, article, PDF, collection, tag, library, DOI, ISBN, PubMed."
---

# Zotero Interaction Skill

Interact with a local Zotero instance through its REST API. Zotero's local API runs at `http://127.0.0.1:23119/api/` and requires Zotero to be running on the same machine.

## When to Use

- Search and retrieve Zotero library items (articles, books, papers, etc.)
- Add, update, or delete references in Zotero
- Manage collections and tags
- Export citations in various formats (BibTeX, RIS, CSL JSON, etc.)
- Query items by DOI, ISBN, PMID, or arXiv ID
- Batch-process library metadata
- Generate bibliographies programmatically

## Zotero Local API Basics

| Endpoint                                | Method | Description                |
| --------------------------------------- | ------ | -------------------------- |
| `/api/items`                            | GET    | List all items (paginated) |
| `/api/items/:itemKey`                   | GET    | Get single item            |
| `/api/items`                            | POST   | Create item(s)             |
| `/api/items/:itemKey`                   | PUT    | Update item                |
| `/api/items/:itemKey`                   | DELETE | Delete item                |
| `/api/collections`                      | GET    | List collections           |
| `/api/collections/:collectionKey/items` | GET    | Items in a collection      |
| `/api/tags`                             | GET    | List all tags              |
| `/api/groups`                           | GET    | List groups                |
| `/api/items/search`                     | POST   | Search items               |
| `/api/items`                            | DELETE | Delete multiple items      |

**Base URL**: `http://127.0.0.1:23119`
**Headers**: `Content-Type: application/json`, `Zotero-API-Version: 3`

> **Note**: Items in the response include an `itemKey` and `version` field. The `version` is required for updates (PUT) and deletions (DELETE) to prevent conflicts.

## Procedure

### 1. Prerequisites Check

Verify Zotero is running and the API is accessible:

```bash
curl -s http://127.0.0.1:23119/api/items?limit=1 | head -c 200
```

If this fails, remind the user to start Zotero and ensure "Enable Local API" is checked in Zotero preferences (Advanced → Settings).

### 2. Choose an Operation

Use the helper script for common operations:

```bash
# Search items by title, author, year, etc.
python ./scripts/zotero.py search "deep learning"

# List recent items (default 10)
python ./scripts/zotero.py list --limit 20

# Get item details by itemKey
python ./scripts/zotero.py get ITEMKEY123

# Add a new item (journal article)
python ./scripts/zotero.py add --type journalArticle --title "..." --creators "Author, First" --date "2024" --doi "10.1234/..."

# Add item by DOI (auto-fetches metadata)
python ./scripts/zotero.py fetch-doi "10.1000/xyz123"

# List collections
python ./scripts/zotero.py collections

# List items in a collection
python ./scripts/zotero.py collection-items COLLECTIONKEY

# List all tags
python ./scripts/zotero.py tags

# Export items as BibTeX
python ./scripts/zotero.py export-bibtex > references.bib

# Delete an item (use with caution)
python ./scripts/zotero.py delete ITEMKEY123
```

### 3. Direct API Calls (Advanced)

For operations not covered by the helper script, use `curl` directly:

```bash
# Search items with full-text
curl -s "http://127.0.0.1:23119/api/items?q=quantum&limit=5" | python -m json.tool

# Create a collection
curl -s -X POST "http://127.0.0.1:23119/api/collections" \
  -H "Content-Type: application/json" \
  -d '{"name":"My New Collection"}'

# Get item count
curl -s "http://127.0.0.1:23119/api/items?limit=1" | grep -o '"totalResults":[0-9]*'
```

### 4. Error Handling

- **Connection refused**: Zotero is not running. Ask user to launch Zotero.
- **404 Not Found**: Invalid item key or endpoint.
- **409 Conflict**: Version mismatch. Re-fetch the item to get the latest version before updating.
- **Empty results**: The search query returned no matches. Try different keywords.
