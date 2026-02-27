# Frontend Documentation


## TL;DR

This frontend is a lightweight, config-driven web client for the Custom-Nerd/Nerd-Engine family of "Nerd" apps. Users ask a question on `index.html`; `index.js` orchestrates validation and a multi-strategy search flow (PDF upload, ID list, Article), streams progress from the backend via SSE, and renders an answer with formatted references. `user_env.js` and `env.js` inject runtime configuration and endpoints. `config.html`/`config.js` provide an admin UI to edit frontend styling, user flow options, environment keys, and backend prompt settings via REST endpoints. `reference.html`/`reference.js` display details for a selected citation using data cached in `localStorage`. `about.html` and `contact.html` are supporting pages for presentation and feedback.

### What to read first
- Start with `index.html` + `index.js` to understand the core UI and flow.
- Review `user_env.js` and `env.js` to see how runtime config and API endpoints are injected.
- Explore `config.html` + `config.js` to understand how admins change the app’s behavior without code changes.
- Check `reference.html` + `reference.js` to see how references are rendered from cached artifacts.


## Frontend architecture at a glance

- **Pages (routing is static):**
  - `index.html`: Main question/answer experience and result rendering.
  - `config.html`: Admin/configuration console for frontend, backend prompts, environment, and user flow.
  - `about.html`: Product and team overview.
  - `contact.html`: Feedback form (EmailJS integration).
  - `reference.html`: Per-reference detail page, opened from references in the answer.

- **Runtime configuration:**
  - `user_env.js`: Primary, user-editable configuration for branding, UX, user flow toggles (search strategies), and feature flags.
  - `env.js`: Core environment values like API base URL and EmailJS keys for contact.

- **UI logic:**
  - `index.js`: Orchestrates question submission, search strategy selection, backend calls, SSE streaming updates, answer rendering, references extraction, PDF generation, and history UX.
  - `reference.js`: Reads cached citation data from `localStorage` and renders a single reference view (with branding from `user_env.js`).
  - `config.js`: Admin console logic to fetch/update configs and prompts via backend endpoints; also manages user flow labels/visibility, API keys, saved states, and code-gen helpers in the console.

- **Styling:** `index.css`, `config.css`, `about.css`, `contact.css` style each page.


## End-to-end flow (from question to answer)

1) Page load and configuration
   - `user_env.js` defines `window.env.FRONTEND_FLOW` and `window.env.USER_FLOW` (branding, styles, placeholders, search strategies, reference section visibility, chat history), plus `FRONTEND_FLOW.API_URL` used as the backend base URL by `index.js`.
   - `env.js` adds global values such as `API_URL` (used on `contact.html`) and EmailJS keys.
   - `index.html` loads CSS, then `user_env.js`, then page scripts like `index.js` and any user flow helpers.

2) User enters a question and submits
   - `index.js` binds the submit button and Enter key handlers. The submit button is enabled only when input is non-empty.
   - If `USER_FLOW.chat_history.visible` is true, `index.js` first suggests similar historical questions by calling `GET /similar_questions`. If the user chooses a suggestion, the corresponding cached answer is displayed.
   - Otherwise, `index.js` shows the Search Strategy selector (from user flow helpers) so the user can choose among: PDF upload, ID list, Article search (as configured in `user_env.js`).

3) Pre-checks and process start
   - `index.js` calls `GET /check_valid/{question}` to screen out unsupported question types (e.g., recipes or animal queries) using backend logic.
   - It collects the selected strategies and values (e.g., PMIDs, uploaded PDFs) and posts them to `POST /process_detailed_combined_query` (multipart form-data).

4) Streaming progress updates
   - After the POST returns a `session_id`, `index.js` opens an `EventSource` on `GET /sse?session_id={id}` to receive live pipeline updates (e.g., generating queries, collecting articles, processing/synthesizing).
   - When the backend signals completion (`end_output` is present), `index.js` caches the result in `localStorage` under `generatedAnswer`.

5) Answer and references rendering
   - `index.js/getAnswer` reads `generatedAnswer` (if present), separates the main content from a references section, and stores artifacts in `localStorage`:
     - `rawOutput` (full output), `referencesContent` (raw refs or “No references to be shown.”), and `referenceObject`/`citations` (array of citation objects) used by both the main page and `reference.html`.
   - `index.js/formatText` renders headings and bullets; the answer is injected into the `#output` container.
   - If `USER_FLOW.reference_section.visible` is true, `index.js/formatReferences` converts numbered references to clickable links pointing to `reference.html?ref=<index>`.

6) PDF export (optional)
   - The “Download PDF” button triggers `index.js/generatePDF`, which reads `rawOutput` and the entered question, and uses `jsPDF` to export a well-formatted PDF (site name, timestamp, question, and answer content).

7) Reuse, history, and similar questions
   - When chat history is enabled, `index.js` renders a “Recent Questions” row by calling `GET /history_recent`. Clicking a chip loads the cached answer into `localStorage` and displays it, avoiding a fresh generation.


## Reference page flow (`reference.html` + `reference.js`)

When a user clicks a reference link on the main results page:
- The link opens `reference.html?ref=<zeroBasedIndex>`.
- `reference.js` reads `referenceObject` from `localStorage` and uses the `ref` parameter to locate the corresponding citation object.
- It renders the citation’s title (hyperlinked if a URL is available), authors, DOI, journal, abstract, and summary (where available).
- It applies branding from `user_env.js` (logo, favicon using emoji, theme colors) so the reference page matches the main site.
- A “Read the full article” button is enabled when a valid `url` exists; otherwise it is disabled with an explanatory tooltip.


## Admin/configuration console (`config.html` + `config.js`)

The configuration console allows an admin to edit frontend appearance, user flow, backend prompts, environment/API keys, and saved “states” without code changes.

- Frontend section
  - `GET /fetch_frontend_config` loads current values into the form: site name/logo/icon, tagline, disclaimer, placeholders, and `STYLES` (background, font, submit button color), as well as `USER_FLOW` toggles.
  - `POST /update_frontend_config` saves updates. Logo upload is supported via `FormData`.

- Backend prompts section
  - `GET /fetch_prompts_config` loads backing prompt templates used by the backend (e.g., `DETERMINE_QUESTION_VALIDITY_PROMPT`, `GENERAL_QUERY_PROMPT`, `FINAL_RESPONSE_PROMPT`, etc.).
  - `POST /update_prompts_config` saves prompt changes. There is also a query-contention toggle.

- User Flow section (Backend files)
  - `GET /fetch_backend_config` loads code snippets for: normal search (`user_search_apis.py`), ID-based search (`user_list_search.py`), and query cleaning (`clean_query.py`).
  - UI labels/visibility for the three search strategies and for `reference_section` and `chat_history` are bound to `USER_FLOW` and later written back to the frontend config.
  - `POST /update_backend_config` persists code snippets; `POST /update_frontend_config` persists updated `USER_FLOW`.
  - `GET /fetch_clean_query` and `POST /save_clean_query` are used to view/edit `clean_query.py` content.

- Environment section (LLM and API keys)
  - `GET /fetch_env_config` loads `LLM` provider selection (OpenAI/Gemini/Claude/**Ollama**), preserves all four provider keys, and renders optional publisher keys (e.g., NCBI/Elsevier/Springer/Wiley/Oxford) and custom keys.
  - `POST /update_env_config` saves environment updates, always preserving OpenAI, Gemini, Claude, and Ollama (`OLLAMA_MODEL`, `OLLAMA_BASE_URL`) keys and any custom keys.
  - **4-segment provider pill switch**: Clicking any of the four segments (OpenAI / Gemini / Claude / Ollama) directly activates that provider; no longer cycles. Fixed via CSS (`pointer-events: none` on the slider, `pointer-events: all` on labels) and explicit JS `click` listeners with `stopPropagation()` in `initModernToggle()`.
  - **API key "Test" buttons**: Each cloud provider row (OpenAI, Gemini, Claude) now has a "Test" button. Clicking it calls `POST /test_api_key` with the current key value and displays an inline result (✓ / ✗ + message).
  - **Ollama sub-section** (visible only when Ollama is selected):
    - Pre-check status badge — fetches `GET /ollama_status` on load to indicate whether Ollama is installed, the server is running, and which models are already pulled.
    - Model dropdown listing: `llama3.2`, `llama3.1:8b`, `phi3:mini`, `qwen3:8b`, `codellama:7b`, `kimi-k2.5:cloud`, plus a "Custom model name…" option.
    - Custom model text input — only rendered when "Custom model name…" is selected; hidden otherwise.
    - "Model Guide" (❓) button — opens the Ollama Model Guide modal (see below).
    - "Setup Ollama" button — calls `GET /ollama_setup?model=<selected_model>` and streams progress over SSE into a step-by-step progress UI (4 steps: install → start server → pull model → verify).
    - "Test Connection" button — calls `POST /test_api_key` with `provider: ollama` and shows inline connectivity result.

- **Ollama Model Guide modal**
  - Opened via `openOllamaGuide()` which also fetches `/ollama_status` to detect locally installed models.
  - Displays a wide (max 1060px), filterable table of curated Ollama models organized by category sections (Recommended, Fast & Lightweight, Best Quality, Coding, etc.).
  - Each row shows: model name, parameter size, disk footprint, minimum RAM, speed badge, quality badge, and a "Use" button that selects the model in the dropdown.
  - **Basic / Advanced toggle**: "Basic" mode hides technical columns and instead shows a plain-language "Works best on" compatibility description (e.g., "MacBook M1 or later · Windows/Linux PC with 8 GB RAM"). "Advanced" mode shows the full technical breakdown.
  - **Installed model detection**: Models already pulled locally receive an "Installed" chip next to their name. Models installed locally but not in the static table appear in a dynamically prepended "✅ Installed on your machine" section and are also added as options in the model dropdown under an "Installed" optgroup.
  - Filterable by search text across model name and use-case descriptions.

- Saved state management
  - `POST /save_state`, `GET /list_saved_states`, `POST /load_state`, and `POST /delete_state` support exporting/importing/deleting named configuration snapshots.

- Hard reset and utilities
  - `GET /fetch_hard_backup_config` resets configurations to a known good baseline.
  - `POST /clear_chat_history` clears stored history in the backend.
  - AI helpers in the console call `POST /generate_code_endpoint?type=...` and `POST /generate_prompt_endpoint` to prototype code and prompts (console-only workflow).


## File-by-file role guide (high level)

- `index.html` / `index.css` / `index.js`
  - Entry point for users. Contains the question input, submit button, results containers (`#output`, `#references`), and the “Download PDF” CTA. The JS module:
    - Reads runtime config (`window.env`), binds UI events, validates input (`check_valid`), orchestrates search strategy selection, posts the combined request, listens for SSE updates, and renders the final answer and references.
    - Extracts references and caches supporting objects in `localStorage` for reuse by `reference.html`.
    - Integrates optional features: recent questions, similar suggestions, and PDF export.

- `reference.html` / `reference.js`
  - Drill-down view for a single reference. Pulls from `localStorage.referenceObject` using `?ref=` to locate and display a citation with branding from `user_env.js`. Provides a direct link to the article if available.

- `config.html` / `config.css` / `config.js`
  - Admin console to manage:
    - Frontend branding, text, styles, and `USER_FLOW` options.
    - Backend prompt templates and query-contention toggle.
    - “Backend files” (code snippets for the two search entry points and the `clean_query.py` helper) and associated labels/visibility.
    - Environment keys, model provider toggle (OpenAI/Gemini/Claude/Ollama, 4-segment pill), plus optional publisher keys and custom keys.
    - Saved state operations and hard reset.
    - Ollama local setup flow with live SSE progress streaming, curated model dropdown, Ollama Model Guide modal (Basic/Advanced toggle, installed-model detection), and "Test Connection" button.
    - API key "Test" buttons for OpenAI, Gemini, and Claude to validate keys inline.

- `about.html` / `about.css`
  - Informational page describing the platform, key features, and team profiles. Loads `user_env.js` to set the logo with fallback to a default image.

- `contact.html` / `contact.css`
  - Feedback form that sends messages via EmailJS using keys from `env.js`. Also uses `user_env.js` for logo fallback and theming.

- `user_env.js`
  - Primary runtime configuration consumed by the frontend. Defines `FRONTEND_FLOW` (branding, `API_URL`, styling) and `USER_FLOW` (search strategy definitions and toggles, `chat_history.visible`, `reference_section.visible`, `query_cleaning.visible`). The main app reads these to render UI, choose behaviors, and set the backend base URL.

- `env.js`
  - Secondary environment settings used by specific pages. Defines `API_URL` for contact interactions and EmailJS credentials. Non-conflicting with `FRONTEND_FLOW.API_URL` used on the main app path.

- Backend-adjacent files referred to by the console (for context)
  - `openai_prompts.py`: Centralizes prompt templates used by backend orchestration. Edited through the console for experimentation and tuning.
  - `user_search_apis.py`: Backend integration point for “normal search” (API-driven article collection); visible/editable from the console.
  - `user_list_search.py`: Backend function for ID-based (ID) lookups; editable from the console.
  - `historical_answer.json`: Backend-side cache of past answers; surfaced to users via “Recent Questions” when `chat_history.visible` is enabled.


## Backend endpoints used by the frontend

Core question/answer workflow (from `index.js`):
- `GET /check_valid/{question}` — Validate input against platform policy.
- `POST /process_detailed_combined_query` — Start processing, returns `session_id`.
- `GET /sse?session_id={id}` — Stream real-time progress updates.
- `GET /history_recent?limit={n}&first={bool}` — Populate “Recent Questions”.
- `GET /similar_questions?query=...&threshold=...&limit=...` — Suggest similar past questions.

Admin/config (from `config.js`):
- `GET /fetch_frontend_config`, `POST /update_frontend_config`
- `GET /fetch_prompts_config`, `POST /update_prompts_config`
- `GET /fetch_backend_config`, `POST /update_backend_config`
- `GET /fetch_env_config`, `POST /update_env_config`
- `POST /save_state`, `GET /list_saved_states`, `POST /load_state`, `POST /delete_state`
- `GET /fetch_hard_backup_config`, `POST /clear_chat_history`
- `GET /fetch_clean_query`, `POST /save_clean_query`
- `POST /generate_code_endpoint?type=...`, `POST /generate_prompt_endpoint`
- `GET /ollama_status` — pre-check: installed, running, model list
- `GET /ollama_setup?model=...` — SSE stream for automated Ollama install/serve/pull/verify
- `POST /test_api_key` — inline API key validation (OpenAI, Gemini, Claude, Ollama)


## Data stored in localStorage (shared across pages)

- `generatedAnswer`: The completed backend response object (includes `end_output` and `citations_obj`).
- `rawOutput`: Full text of the final answer (for PDF export).
- `referencesContent`: Raw, rendered references content or a “No references to be shown.” sentinel.
- `referenceObject`: Array of citation objects aligned to reference indices.
- `citations`: A copy of the citation array for convenience.
- `allArticles`: Same array used by references viewing.
- `url`: The article URL of the currently open reference (used by `reference.js`).


## Frontend lifecycle summary (sequence)

1. Load `user_env.js` → hydrate branding, API base URL, search strategy availability.
2. User types a question → UI validates → submit enabled.
3. If chat history is enabled → try `GET /similar_questions` → show chips; else continue.
4. Show strategy selector; user chooses any mix of: upload PDFs, enter IDs, search Article.
5. `GET /check_valid` → if not good, display server message; else continue.
6. `POST /process_detailed_combined_query` with FormData (question, flags, PMIDs, files).
7. `GET /sse?session_id=...` → stream progress and status to the UI.
8. On completion → cache artifacts → render formatted answer → render references (if enabled).
9. Optional: “Download PDF” uses `jsPDF` and `rawOutput` to generate a PDF.
10. Optional: Clicking a reference opens `reference.html?ref=...` for deep-dive metadata.


## Extending the frontend

- **Add a new search strategy**
  - Extend `USER_FLOW.searchStrategies` in `user_env.js` with a new strategy `id`, `label`, `type`, and visibility. Ensure corresponding HTML controls and handlers exist in the user flow helper used by `index.js` (e.g., collection of selected values and validation). Update `config.js` if you want to expose labels/visibility in the admin console.

- **Customize branding and UX**
  - Edit `FRONTEND_FLOW` in `user_env.js` (site name/icon, colors, font, tagline, placeholders). Use `config.html` for non-code updates via admin endpoints.

- **Tweak backend prompts without redeploying**
  - Use `config.html` prompts section to tune prompt templates (`openai_prompts.py`), including enabling/disabling query contentions. Changes persist via `/update_prompts_config`.

- **Add or use publisher/custom API keys**
  - Use the Environment tab in `config.html` to add optional publisher keys or your own. These are preserved even when switching LLM providers and saved via `/update_env_config`.

- **Persist/share configurations**
  - Save/load/delete named configuration states from the console to move between environments or roll back changes quickly.


## Key takeaways for developers

- The main UI flow is contained in `index.js`; `user_env.js` drives what the UI shows and where it talks (API URL).
- The admin console in `config.html`/`config.js` centralizes almost all knobs (frontend branding, user flow, prompts, env), backed by explicit REST endpoints.
- References are rendered as links and opened in a dedicated page that reads citation artifacts from `localStorage`.
- Caching in `localStorage` enables quick re-display of previous answers and a simple “similar questions” experience when chat history is enabled.
- The system is intentionally “config-first”: prefer changing `user_env.js` or using `config.html` over code edits for routine adjustments.
- The 4-segment LLM provider pill (OpenAI / Gemini / Claude / Ollama) uses direct `onclick` handlers per segment and CSS `pointer-events` tuning to ensure every segment is reliably clickable regardless of the animated slider overlay.
- Ollama is the only provider that requires no cloud API key — the entire local setup (install, model pull, serve) is handled through the UI via the `/ollama_setup` SSE stream.
- The Ollama Model Guide modal is opened via `openOllamaGuide()` which also calls `/ollama_status` so installed model detection and the model dropdown always reflect the current local state.


