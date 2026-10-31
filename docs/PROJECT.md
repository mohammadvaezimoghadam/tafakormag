# Project: Tafakor Monorepo Generic Plugin System & Quran Plugin

## Architecture
The Tafakor Plugin Architecture enables generic, decoupled extensibility with zero breaking changes to existing core platform features (Topics, Posts, Bot Tasks, Auth, Donations).

```
+----------------------------------------------------------------------------------------------------+
|                                      FRONTEND (Vue 3 / Vite)                                       |
|                                                                                                    |
|  +---------------------------+    +----------------------------+    +---------------------------+  |
|  |     Marketplace UI        |    |   Quran Mini-App Views     |    |   TopicMessageInput.vue   |  |
|  |      (/plugins)           |    |     (/apps/quran/*)        |    |   (Composer Action Modal) |  |
|  +-------------+-------------+    +-------------+--------------+    +-------------+-------------+  |
|                |                                |                                 |                |
|                v                                v                                 v (Markdown)     |
|  +----------------------------------------------------------------------------------------------+  |
|  |  src/plugins/core (PluginRegistry, PluginLoader, PluginErrorBoundary, PluginTypes)          |  |
|  +----------------------------------------------------------------------------------------------+  |
+-------------------------------------------------|--------------------------------------------------+
                                                  | REST API calls
                                                  v
+----------------------------------------------------------------------------------------------------+
|                                      BACKEND (Django / DRF)                                        |
|                                                                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  |  apps/plugin_system (GENERIC CORE)                                                           |  |
|  |  - Models: Plugin, PluginInstallation, PluginTopicInstallation, PostPluginReference          |  |
|  |  - ManifestValidator (manifest_version: 1), PluginRegistry, INSTALLED_TAFAKOR_PLUGINS        |  |
|  |  - REST Endpoints: /api/plugins/ (marketplace, user & topic installations)                   |  |
|  +----------------------------------------------------------------------------------------------+  |
|                                                 | (Loose coupling via external_id)                 |
|                                                 v                                                  |
|  +----------------------------------------------------------------------------------------------+  |
|  |  plugins/quran (OFFICIAL QURAN PLUGIN)                                                       |  |
|  |  - Models: QuranEdition, QuranSurah, QuranAyah, QuranJuz                                     |  |
|  |  - Services: Unicode Normalizer, Search Service, Markdown Formatter                          |  |
|  |  - Management Command: python manage.py import_quran (atomic, source-driven)                  |  |
|  |  - REST Endpoints: /api/plugins/quran/ (editions, surahs, ayahs, juzs, search, compare)       |  |
|  +----------------------------------------------------------------------------------------------+  |
|                                                                                                    |
|  +----------------------------------------------------------------------------------------------+  |
|  |  CORE APPS (Untouched & Zero Regressions: apps.accounts, apps.notes, apps.donations)         |  |
|  +----------------------------------------------------------------------------------------------+  |
+----------------------------------------------------------------------------------------------------+
```

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---|---|---|---|
| 1 | Core Plugin Models | `Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference` | M1 | ORIGINAL_REQUEST §R1 |
| 2 | Manifest Validator | Schema validation for `manifest_version: 1`, scopes, capabilities, and settings schema | M1 | ORIGINAL_REQUEST §R1 |
| 3 | Dynamic Plugin Registry | `registry.py` autodiscovering and managing installed plugins lifecycle | M1 | ORIGINAL_REQUEST §R1 |
| 4 | Settings Isolation | `INSTALLED_TAFAKOR_PLUGINS` setting with safe empty fallback | M1 | ORIGINAL_REQUEST §R1 |
| 5 | Plugin Management APIs | REST endpoints `/api/plugins/` for marketplace listing, user & topic install/toggle | M1 | ORIGINAL_REQUEST §R1 |
| 6 | Multi-Edition Quran Models | `QuranEdition`, `QuranSurah`, `QuranAyah`, `QuranJuz` with decoupled relationships | M2 | ORIGINAL_REQUEST §R2 |
| 7 | Unicode Normalizer Engine | Comprehensive Arabic/Persian diacritics stripping & character standardization | M2 | ORIGINAL_REQUEST §R2 |
| 8 | Atomic JSON Importer | `python manage.py import_quran` supporting dynamic datasets without hardcoded counts | M2 | ORIGINAL_REQUEST §R2 |
| 9 | Cross-DB Search Engine | Substring & token search over `normalized_text` for SQLite and PostgreSQL parity | M2 | ORIGINAL_REQUEST §R2 |
| 10 | Quran Navigation APIs | REST endpoints `/api/plugins/quran/` (surahs, ayahs, juzs, editions, search, compare) | M2 | ORIGINAL_REQUEST §R2 |
| 11 | Frontend Plugin Core | `pluginTypes.ts`, `pluginRegistry.ts` (Pinia), `pluginLoader.ts`, `PluginErrorBoundary.vue` | M3 | ORIGINAL_REQUEST §R3 |
| 12 | Dynamic Lazy-Loading | Dynamic module `import()` and lazy route injection via `router.addRoute()` | M3 | ORIGINAL_REQUEST §R3 |
| 13 | Marketplace UI | Full marketplace view `/plugins` and `FeedView.vue` tab replacing placeholder | M3 | ORIGINAL_REQUEST §R3 |
| 14 | Quran Mini-App Views | Routes `/apps/quran/*` for Surahs catalog, Ayah reader, Juz reader, search, audio stream | M3 | ORIGINAL_REQUEST §R3 |
| 15 | Composer Action Integration | Verse Picker Dialog inserting formatted Markdown into `TopicMessageInput.vue` | M3 | ORIGINAL_REQUEST §R3 |
| 16 | Opaque-Box E2E Test Suite | 4-tier comprehensive test suite covering all features with >=5 cases per feature | M4 | ORIGINAL_REQUEST §R4 |
| 17 | Core Non-Regression | Verification that all 35 pre-existing core tests pass with 100% success rate | M4 | ORIGINAL_REQUEST §R4 |
| 18 | Adversarial Coverage Hardening | Tier 5 white-box stress testing and forensic audit for zero integrity violations | M4 | ORIGINAL_REQUEST §R4 |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|---|---|---|---|
| M1 | Generic Plugin System Core | Backend `apps/plugin_system` models, manifest validator, registry, settings, APIs & tests | none | DONE |
| M2 | Official Quran Plugin | Backend `backend/plugins/quran` models, normalizer, importer, search, APIs & tests | M1 | DONE |
| M3 | Frontend Plugin System & Mini-App | Frontend `src/plugins` core, registry, lazy loader, marketplace UI, Quran reader, composer action | M1, M2 | PLANNED |
| M4 | E2E Testing & Final Verification | Opaque-box E2E test harness & suite (Tiers 1-4), Non-regression check, Tier 5 Adversarial hardening, Audit | M1, M2, M3 | PLANNED |

## Interface Contracts

### 1. Backend Core Plugin System ↔ Plugins
- **Manifest**: Plugins must provide `manifest.json` or Python manifest with `manifest_version: 1`, `identifier`, `name`, `version`, `capabilities`, `scopes`.
- **Plugin Base Class**: Plugins extend `BasePlugin` (in `apps.plugin_system.base`).
- **Post Reference**: Content referencing uses `PostPluginReference` with `(post, plugin, resource_type, external_id, metadata)`. No direct foreign keys from core to plugin tables.

### 2. Frontend Plugin Core ↔ Mini-Apps
- **Manifest**: Mini-apps export a `PluginManifest` with `id`, `name`, `nameFa`, `version`, `capabilities`, `routes`, `composerActions`.
- **Composer Action Contract**: Composer actions provide a component/dialog that calls `context.insertText(markdownString)` on completion.
- **Route Injection**: Dynamic routes registered under `/apps/<pluginId>/*` wrapped in `PluginErrorBoundary`.

### 3. Backend Quran API ↔ Frontend Quran Mini-App
- `GET /api/plugins/quran/editions/`: Returns list of editions.
- `GET /api/plugins/quran/surahs/`: Returns 114 Surahs with metadata.
- `GET /api/plugins/quran/surahs/<id>/ayahs/?edition=<id>&with_translation=<id>`: Returns Surah text & translations.
- `GET /api/plugins/quran/search/?q=<query>&edition=<id>`: Returns matching ayahs with `highlighted_text`.
- `POST /api/plugins/quran/format-reference/`: Generates standard Markdown quote.

## Code Layout
```
f:\AVA\tafakor\
├── backend/
│   ├── note_platform/
│   │   ├── settings.py           # Includes INSTALLED_TAFAKOR_PLUGINS
│   │   └── urls.py               # Routes /api/plugins/
│   ├── apps/
│   │   └── plugin_system/        # M1: Generic Plugin System Core
│   │       ├── models.py
│   │       ├── manifest.py
│   │       ├── validator.py
│   │       ├── registry.py
│   │       ├── serializers.py
│   │       ├── views.py
│   │       ├── urls.py
│   │       └── tests/
│   └── plugins/
│       └── quran/                # M2: Official Quran Plugin
│           ├── apps.py
│           ├── manifest.json
│           ├── models.py
│           ├── services/
│           │   ├── normalizer.py
│           │   ├── search_service.py
│           │   └── formatter.py
│           ├── management/commands/import_quran.py
│           ├── data/
│           │   ├── surahs.json
│           │   ├── juzs.json
│           │   ├── editions.json
│           │   └── sample_quran.json
│           ├── serializers.py
│           ├── views.py
│           ├── urls.py
│           └── tests/
├── frontend/
│   └── src/
│       ├── plugins/              # M3: Frontend Plugin System & Mini-App
│       │   ├── core/
│       │   │   ├── pluginTypes.ts
│       │   │   ├── pluginRegistry.ts
│       │   │   ├── pluginLoader.ts
│       │   │   ├── PluginErrorBoundary.vue
│       │   │   └── index.ts
│       │   ├── quran/
│       │   │   ├── manifest.ts
│       │   │   ├── api.ts
│       │   │   ├── types.ts
│       │   │   ├── composables/
│       │   │   ├── components/
│       │   │   └── views/
│       │   └── index.ts
│       ├── components/
│       │   └── TopicMessageInput.vue  # Non-invasive Composer integration
│       └── views/
│           └── FeedView.vue           # Marketplace tab integration
└── tests/
    ├── e2e/                      # M4: E2E Testing Suite
    └── integration/
```
