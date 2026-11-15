# Tafakor Project Engineering Rules & Architecture Guidelines

> **Repository:** Tafakor Platform (`tafakormag_avapardaz`)  
> **Tech Stack:** Django REST Framework (Backend), Vue 3 (Web Frontend), PostgreSQL, Redis, Docker, Nginx  
> **Target Audience:** All AI Coding Agents & Human Developers

---

## 1. Architectural Principles & Service Layer Pattern (MANDATORY)

- **Thin Views, Fat Services / Models:**
  - ViewSets and Views must ONLY handle: HTTP input parsing, authentication/permission verification, calling the appropriate service function, and returning a DRF `Response`.
  - **No business logic in Views:** Never write complex database operations, third-party API calls, or multi-step mutations directly inside `views.py` action methods.
  - Any View or Action method exceeding ~30 lines is an architectural smell and MUST be refactored into `services.py`.
- **App Modularity:**
  - `accounts`: User authentication, OTP via Kavenegar, phone-based identity, and bot connection status.
  - `notes`: Topics, Posts, Tags, Badges, BotTask queue, and Persian text normalization.
  - `donations`: Financial campaigns and payment tracking.
  - `plugin_system`: Dynamic plugin hooks and extensibility.
  - `subscriptions`: In-app purchases, Cafe Bazaar billing, VIP entitlements, and verification logs.
  - `ota`: Flutter Patcher over-the-air updates and channel management.

---

## 2. Django ORM, Database Indexing & N+1 Prevention

- **Zero N+1 Queries Policy:**
  - Any QuerySet traversing a `ForeignKey` or `OneToOneField` MUST explicitly use `.select_related(...)`.
  - Any QuerySet traversing a `ManyToManyField` or reverse relationship (e.g. `Topic` -> `telegram_connections`, `bale_connections`; `Post` -> `reactions`, `comments`, `plugin_references`) MUST explicitly use `.prefetch_related(...)`.
  - Always check list endpoints and nested serializers to ensure the number of SQL queries does not scale with the number of rows returned.
- **Relationships & Indexes:**
  - Always specify an explicit `related_name` on ForeignKeys and ManyToManyFields.
  - Always add `db_index=True` or `models.Index` on fields used in `filter()`, `exclude()`, or `order_by()`.

---

## 3. Persian Text Normalization & Hash Consistency

- **Canonical Normalization Function:**
  - Always use `normalize_persian_text()` from `backend.apps.notes.models` for any Arabic/Persian character normalization (converting 'ي' to 'ی', 'ك' to 'ک', stripping zero-width spaces).
  - NEVER write ad-hoc regex or reimplement character replacement.
- **Deduplication via `content_hash`:**
  - Maintain and respect `content_hash` for duplicate post detection. Recomputing hashes with any non-standard normalizer will corrupt deduplication across existing historical posts.

---

## 4. Asynchronous Bot Task Architecture (`BotTask`)

- **Non-blocking Request Cycles:**
  - NEVER make direct external HTTP calls to Telegram or Bale Bot APIs inside a web request cycle.
  - To send, edit, or delete messages on external platforms, ALWAYS create a `BotTask` record with the appropriate `platform`, `chat_id`, `message_id`, and `bot_token`.
  - Background workers/bots are responsible for consuming and executing `BotTask` records asynchronously.

---

## 5. Security & Settings Management

- **Zero Hardcoded Secrets:**
  - API keys (Kavenegar, Bazaar, Telegram/Bale tokens, DB passwords) must NEVER be hardcoded in Python code or committed to Git.
  - Read all secrets from environment variables (`os.environ` or `python-decouple`).
- **Reverse Proxy & SSL:**
  - Maintain `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`.
  - Ensure all active domains and subdomains (`https://tafakormag.ir`, `https://*.tafakormag.ir`) are present in `CSRF_TRUSTED_ORIGINS`.

---

## 6. Git & Deployment Golden Rule

- **Strict No-Edit on Server Policy:**
  - NEVER edit code directly on remote servers (`~/tafakor` or `~/tafakor_dev`).
  - All code must be authored and verified locally, committed, pushed to GitLab (`develop` or `main`), and updated on the server via `git pull origin <branch>` followed by container restart.

