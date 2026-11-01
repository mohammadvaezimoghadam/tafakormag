# Orchestration Plan: Generic Plugin System & Quran Plugin

## Objective
Implement and verify a robust, zero-breaking-change Generic Plugin System and official Quran Plugin for the Tafakor Monorepo, including frontend/backend integration, opaque-box testing, and non-regression verification.

## Phase 0: Survey & Architecture Discovery (Current)
- Dispatch 3 parallel Explorers:
  - **Explorer 1 (Backend Core & Plugin Architecture)**: Map existing Django apps, settings, models, DRF API structure, authentication/permissions, existing test suite (35 tests), and plugin_system requirements.
  - **Explorer 2 (Quran Plugin & Importer Architecture)**: Map quran data sources, model specifications, JSON importer design, SQLite/PostgreSQL search optimization, APIs, Juz/Surah metadata.
  - **Explorer 3 (Frontend Plugin System & Composer)**: Map Vue 3 / Vite architecture, router, Pinia store, `TopicMessageInput.vue`, dynamic imports, plugin error boundaries, build and type-check setup.
- Aggregate Explorer reports into `PROJECT.md` with full Feature Inventory, Architecture, Interface Contracts, and Milestones.

## Phase 1: Dual Track Execution
### Track 1: Implementation Track
- **Milestone 1 (M1)**: Core Plugin System (`apps/plugin_system`)
  - Models (`Plugin`, `PluginInstallation`, `PluginTopicInstallation`, `PostPluginReference`)
  - Manifest validation (`manifest_version: 1`), Plugin registry (`registry.py`)
  - Settings integration (`INSTALLED_TAFAKOR_PLUGINS`), graceful zero-plugin fallback
  - Marketplace & topic integration APIs (`/api/plugins/`)
- **Milestone 2 (M2)**: Official Quran Plugin (`backend/plugins/quran` / `plugins/quran`)
  - Multi-edition models (`QuranEdition`, `QuranSurah`, `QuranAyah`, `QuranJuz`)
  - Source-driven atomic JSON importer management command (`import_quran`)
  - Search endpoint with normalized-text vs authentic display text
  - Navigation APIs (`/api/plugins/quran/*`)
- **Milestone 3 (M3)**: Frontend Plugin System & Quran Mini-App (`src/plugins`)
  - Frontend registry & dynamic loader (`pluginRegistry.ts`, `pluginLoader.ts`, `pluginTypes.ts`)
  - Marketplace UI (`/plugins`), Quran reader mini-app (`/apps/quran/*`)
  - Error boundary isolation
  - Non-invasive Composer action in `TopicMessageInput.vue` (Markdown insertion)

### Track 2: E2E Testing Track (Parallel)
- E2E Testing Orchestrator designs opaque-box test infrastructure and comprehensive 4-Tier test suite:
  - Tier 1: Feature Coverage (>=5 per feature)
  - Tier 2: Boundary & Corner Cases (>=5 per feature)
  - Tier 3: Cross-Feature Interactions
  - Tier 4: Real-World Workload Scenarios
- Publishes `TEST_INFRA.md` and `TEST_READY.md`.

## Phase 2: Final Milestone & Verification
- **Phase 1**: Pass 100% of E2E test suite (Tiers 1-4) + 35 pre-existing core tests.
- **Phase 2**: Adversarial Coverage Hardening (Tier 5) with Challengers and Forensic Auditor.
- Frontend clean build (`npm run build`) and type check (`npm run type-check`).

## Phase 3: Final Synthesis & Victory Report
- Write handoff.md and report completion to the Sentinel.
