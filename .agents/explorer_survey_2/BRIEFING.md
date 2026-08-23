# BRIEFING — 2026-08-23T20:30:00Z

## Mission
Survey, investigate, and comprehensively design R2 (Official Quran Plugin): architecture, models, data importer, search/normalization algorithms, and API contracts.

## 🔒 My Identity
- Archetype: Explorer / Specialist
- Roles: Quran Plugin & Data Importer Specialist
- Working directory: f:\AVA\tafakor\.agents\explorer_survey_2
- Original parent: 0d56fb76-8ec2-441c-9c61-1a89e98c70fb
- Milestone: Survey & Architectural Design (R2)

## 🔒 Key Constraints
- Read-only investigation — do NOT modify application source code (reports/analyses in own folder only).
- Deliver 5-component handoff report in handoff.md.
- Thorough investigation of current codebase structure, plugins integration, models, data sources, normalization, and API routes.

## Current Parent
- Conversation ID: 0d56fb76-8ec2-441c-9c61-1a89e98c70fb
- Updated: 2026-08-23T20:30:00Z

## Investigation State
- **Explored paths**:
  - `backend/note_platform/settings.py` & `urls.py` (App registration, dynamic sys.path, INSTALLED_APPS)
  - `backend/apps/notes/models.py` (Topic, Post, BotTask, normalize_persian_text)
  - `backend/apps/accounts/models.py` (User, MessagingTarget)
  - `backend/apps/donations/models.py` (DonationCampaign, DonationTransaction)
  - `frontend/src/components/TopicMessageInput.vue` (Composer action integration point)
  - `frontend/src/api/index.ts` (API client and error handling)
  - `pytest.ini` & `tests/integration/` (Test runner conventions)
- **Key findings**:
  - `backend` is added to `sys.path`, allowing `plugins.quran` to be loaded directly.
  - Core models in `apps/notes` have zero knowledge of plugins; `PostPluginReference` in `apps.plugin_system` (R1) links via `external_id` (e.g. `"surah:1,ayah:1-7"`).
  - Multi-edition architecture must decouple `QuranEdition` from `QuranSurah`, allowing N translations/recitations per Surah/Ayah.
  - Unicode text normalizer must strip diacritics (`\u064B-\u065F`, `\u0670`, etc.) and standardize Alef/Yeh/Kaf/Waw/Teh Marbuta to enable uniform SQLite (`icontains`) and PostgreSQL search without full-text extension dependencies.
  - Importer `import_quran` must be source-driven, transactional (`transaction.atomic`), validation-first, and support local JSON files, directory scans, bundled seed fallback, and remote downloads.
- **Unexplored areas**: None. Ready for complete handoff report synthesis.

## Key Decisions Made
- Multi-edition schema designed with 4 models: `QuranEdition`, `QuranSurah`, `QuranJuz`, `QuranAyah`.
- Search architecture uses dual fields: authentic `text` (for presentation and Markdown export) and indexable `normalized_text` (for ultra-fast substring and token search on both SQLite and PostgreSQL).
- Importer command designed with robust schema validation, atomic transactions, batch insertions (batch_size=1000), and bundled sample/seed fallbacks.
- Composer reference formatting designed for non-invasive Markdown insertion into `TopicMessageInput.vue`.

## Artifact Index
- DISPATCH.md — Initial dispatch message
- BRIEFING.md — Persistent working memory
- progress.md — Liveness heartbeat
- handoff.md — Final comprehensive design and synthesis report
