# ARCHITECTURE — Asistente de Contrapunto

Strict, non-negotiable rules for this project. Read before adding code.

---

## 1. Backend

- **Framework:** FastAPI, served with `uvicorn main:app --reload`.
- **Entry point:** `main.py` — HTTP layer only (routing, validation, file I/O, CORS).
- **Core engine:** `cli_runner.py` — the decoupled analysis pipeline. All music
  logic lives here, never in the HTTP layer.
- **Rule:** `main.py` must stay a thin wrapper. Business logic belongs in
  `cli_runner.py` so it remains usable from the CLI and the API alike.

### API contract

`POST http://localhost:8000/analyze/`

- **Request:** `multipart/form-data`
  - `file` — the MusicXML upload (`.musicxml` / `.xml`).
  - `especie` — one of `primera`, `segunda`.
- **Response (200):**
  ```json
  {
    "status": "ok",
    "especie": "primera",
    "annotated_url": "http://localhost:8000/download/<token>",
    "report_url": "http://localhost:8000/download/<token> | null",
    "input_file": "<server path — debug only>",
    "annotated_pdf": "<server path — debug only>",
    "report_pdf": "<server path | null — debug only>"
  }
  ```
- **Errors:** `422` (unsupported especie / invalid input), `500` (pipeline failure).

`GET /download/{token}`

- Serves a generated PDF as `application/pdf` (`FileResponse`). Returns `404` if
  the token is unknown or the file no longer exists.
- Tokens map to server paths in an **in-memory registry** (`_PDF_REGISTRY`), so
  they are lost on process restart — fine for the local single-machine workflow.
  The `*_pdf` fields in the `/analyze/` response are kept only for local debugging;
  clients should use `annotated_url` / `report_url`.

---

## 2. Frontend

- **Stack:** Vanilla HTML + CSS + JavaScript. **No React, Vue, Svelte, build
  step, bundler, or npm dependency.** Zero framework weight by design.
- **Location:** everything lives in `frontend/`.
  - `index.html` — markup and structure (semantic, accessible).
  - `style.css` — all styling. No inline styles in HTML.
  - `app.js` — all behavior. No inline `onclick` handlers in HTML.
- **Communication:** the frontend talks to the backend **only** via `fetch()` to
  `http://localhost:8000/analyze/`. No other coupling.
- **Serving:** open `frontend/index.html` directly, or serve it with any static
  server (e.g. `python -m http.server` from `frontend/`).

---

## 3. Aesthetic — "Baroque / Encarta-era Academic"

The visual direction is deliberate and committed: **Baroque, 1990s academic
courseware (Encarta-style), lightly Gothic.** It should feel like prestige
educational software from old Harvard/Oxford — not a modern SaaS template.

**Design tokens (single source of truth — mirror in `style.css`):**

| Token            | Value     | Use                                   |
| ---------------- | --------- | ------------------------------------- |
| Parchment        | `#f3e9d2` | Page / surface background             |
| Aged parchment   | `#e8dcc0` | Recessed panels                       |
| Deep burgundy    | `#5a1a1a` | Primary / crimson structural color    |
| Crimson          | `#7c2128` | Accents, links, hover                 |
| Antique gold     | `#b08d3c` | Borders, rules, ornament, focus       |
| Ink              | `#2b1d12` | Body text                             |

**Typography (Google Fonts):**

- `Cinzel` — grand display titles (engraved Roman capitals).
- `Playfair Display` — section headings / subtitles.
- `EB Garamond` — body copy and controls (classic academic serif).

**Principles** — derived from the *$10K Checklist* (`auditoria_estetica.pdf`).
These are requirements, not suggestions:

1. **Point of view, not a template** — commit fully to the Baroque direction.
2. **Typography does the work** — paired display + body serif carry hierarchy.
3. **Restrained color** — the six tokens above only. No rainbow.
4. **Hierarchy that breathes** — whitespace and scale, clear primary CTA.
5. **Imagery with intent** — CSS-drawn ornament/frames, no stock clipart.
6. **Motion that whispers** — subtle micro-interactions; honor
   `prefers-reduced-motion`.
7. **Mobile designed, not shrunk** — purpose-built small-screen layout.
8. **The invisible expensive stuff** — semantic HTML, WCAG AA contrast,
   keyboard navigation, real `<meta>` tags, fast load.
