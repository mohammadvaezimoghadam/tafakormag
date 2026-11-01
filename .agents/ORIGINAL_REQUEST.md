# Original User Request

## Initial Request — 2026-08-23T20:24:19Z

Implement a Generic Plugin System and the first official Quran Plugin for the Tafakor Monorepo, strictly following the zero-breaking-change architecture.

Working directory: f:\AVA\tafakor
Integrity mode: development

## Requirements

### R1. Generic Plugin System Core (apps/plugin_system)
Implement the core Django plugin app with `Plugin`, `PluginInstallation`, `PluginTopicInstallation`, and `PostPluginReference` models. Include manifest validation (`manifest_version: 1`), plugin registry (`registry.py`), and marketplace access management APIs (`/api/plugins/` endpoints for listing, installing, enabling, disabling, and topic plugin integration).

### R2. Quran Plugin (plugins/quran)
Implement the official Quran plugin under `backend/plugins/quran` with multi-edition models (`QuranEdition`, `QuranSurah`, `QuranAyah`, `QuranJuz`), a source-driven atomic JSON importer (`import_quran`), PostgreSQL/SQLite normalized-text search API, and Quran content navigation APIs (`/api/plugins/quran/surahs/`, `ayahs/`, `search/`, etc.).

### R3. Frontend Plugin System & Quran Mini-App (src/plugins)
Implement the frontend plugin registry (`pluginRegistry.ts`, `pluginLoader.ts`, `pluginTypes.ts`) with lazy-loaded dynamic imports (`import()`), marketplace UI (`/plugins`), Quran reader mini-app (`/apps/quran/*`), error boundary isolation, and a non-invasive Composer action that inserts formatted Markdown into `TopicMessageInput.vue` without altering the core publishing pipeline.

### R4. Automated Verification & Non-Regression Suite
Implement backend and frontend test suites covering plugin registry, manifest validation, lifecycle APIs, Quran importer, Quran search, and composer markdown injection. Verify that all 35 existing core tests continue to pass with zero regressions.

## Acceptance Criteria

### Core Non-Regression & Isolation
- [ ] Core platform features (Topics, Posts, Bot Tasks, SMS/Bale OTP, Donations) operate with zero breaking changes.
- [ ] An empty or disabled `INSTALLED_TAFAKOR_PLUGINS = []` causes no startup crashes or runtime errors in core features.
- [ ] `PostPluginReference` links to the core `Plugin` model and stores `external_id` without direct foreign keys to plugin-specific tables.

### Plugin Management & APIs
- [ ] `/api/plugins/` endpoints allow listing, installing, enabling, and disabling plugins at user and topic levels.
- [ ] Marketplace acts as a feature access manager without runtime code execution or package installation.

### Quran Functionality & Importer
- [ ] `python manage.py import_quran` validates and atomically loads Quran editions, surahs, and ayahs without hardcoded count assumptions.
- [ ] Search endpoint `/api/plugins/quran/search/?q=` searches over `normalized_text` while returning authentic `text` for display and export.
- [ ] Juz metadata is exposed if provided by the source dataset.

### Frontend & Composer Integration
- [ ] Quran routes (`/apps/quran/*`) and components are lazy-loaded on demand.
- [ ] Quran composer action inserts standard Markdown text directly into the existing composer without modifying the `Post` publishing pipeline.
- [ ] Plugin-level errors are isolated and do not crash the feed or navigation.

### Verification Suite
- [ ] All new unit and integration tests for `plugin_system` and `quran` pass.
- [ ] All pre-existing test suites (`pytest`, Playwright E2E, DRF API tests) pass with 100% success rate.
- [ ] Frontend builds cleanly with `npm run build` and `npm run type-check`.
