# Star Citizen Heads API Integration

SCCharacters (BioMetrics) fetches character data from the **star-citizen-heads** project API (star-citizen-characters.com). This document describes the API contract and how we use it so we can avoid pulling all heads when not needed.

## API endpoint

- **Base URL:** `https://www.star-citizen-characters.com`
- **Characters list:** `GET /api/heads`

### Query parameters

| Parameter   | Type   | Description |
|------------|--------|-------------|
| `page`     | number | Required. Page number (1-based). |
| `search`   | string | Optional. Text search (min 3 chars). |
| `tags`     | string | Optional. Comma-separated tag IDs. |
| `orderBy`  | string | Optional. Sort order: `latest` (default), `oldest`, `like`, or `download`. |

### Paginated response (GET /api/heads)

```json
{
  "body": {
    "hasPrevPage": true,
    "hasNextPage": true,
    "rows": [ /* character objects */ ]
  }
}
```

### Random characters (GET /api/heads/random)

- **URL:** `GET /api/heads/random?count=N`
- **Auth:** None (public).
- **Parameters:** `count` (optional, default 10) — number of random characters (clamped to 2–50).
- **Response:** JSON array of character objects (same shape as `rows` items). Used by the roulette.

- **rows:** Array of character objects (each includes `id`, `title`, `dnaUrl`, `previewUrl`, `user`, `tags`, `createdAt`, `_count`, etc.).
- **hasNextPage / hasPrevPage:** Indicate whether more pages exist; useful for "Load more" without fetching until an empty page.

## Ordering (orderBy)

The API supports server-side ordering so clients do not need to fetch every page to get "most liked" or "most downloaded" first:

- **`latest`** – Newest first (default). Used for "Date (New–Old)".
- **`oldest`** – Oldest first. Used for "Date (Old–New)".
- **`like`** – Most liked first.
- **`download`** – Most downloaded first.
- Name (A–Z) has no server option; the app uses `latest` then sorts by name client-side.

SCCharacters uses these in:

- **Scraper:** Only `get_character_list(page, search_query, order_by)` is used. It passes `orderBy` to the API. There is no "get all" method; the app never fetches the full list (500k+ heads).
- **Online tab:** Sort combo index maps to `orderBy` (1=latest, 2=download, 3=like). Initial load and "Load more" both send the current `orderBy`, so pagination stays consistent. Browsing is pagination-only.

- **Pagination:** The scraper returns `(rows, has_next_page)` from the API’s `body.hasNextPage` so "Load more" is shown or disabled correctly.
- **Roulette:** Fetches 5 random from `/api/heads/random?count=5`. Each "GIRAR DE NUEVO" (Spin again) fetches 5 new random characters from the API.

## Possible future improvements

- **More orderBy options (star-citizen-heads):** e.g. `title` or `name` for A–Z so SCCharacters could avoid client-side name sort when the list is large.
