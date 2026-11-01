# Scope: Milestone 3 — Frontend Plugin System & Quran Mini-App

## Architecture
Milestone 3 implements the entire client-side plugin ecosystem and the first-party Quran Mini-App inside `frontend/`:
1. **Frontend Plugin Core** (`frontend/src/plugins/core/`):
   - `pluginTypes.ts`: Manifest interfaces (`PluginManifest`, `PluginCapability`, `PluginComposerAction`, `PluginRouteConfig`, `PluginPermission`), activation lifecycles, and registry types.
   - `pluginRegistry.ts`: Pinia store managing registered manifests, installed plugins (user & topic levels), and enabling/disabling states.
   - `pluginLoader.ts`: Dynamic plugin loader utilizing `import.meta.glob('../**/manifest.ts')`, lazy `import()` loading, and dynamic route registration with `router.addRoute()`.
   - `PluginErrorBoundary.vue`: Resilient Vue 3 error boundary using `onErrorCaptured` to catch and isolate runtime errors inside plugin views/components without crashing parent application.
2. **Official Quran Plugin** (`frontend/src/plugins/quran/`):
   - `manifest.ts`: Quran plugin manifest conforming to core plugin interfaces.
   - `api.ts`: Typed API client for backend `/api/plugins/quran/` endpoints (surahs, ayahs, editions, juzs, search).
   - `types.ts`: Comprehensive interfaces for Surah, Ayah, Edition, AudioStream, Juz, Search Results.
   - `composables/useQuranAudio.ts`: Recitation audio streaming player with auto-advance to next ayah, speed controls, play/pause state management.
   - `composables/useQuranReader.ts`: Reader state, translation toggles, font size controls, bookmarking, and navigation.
   - `components/AyahCard.vue`: Renders Arabic text with Uthmani font styling, Persian/English translation, audio play trigger, copy and share actions.
   - `components/SurahHeader.vue`: Header displaying Surah name (Arabic, transliteration, English), revelation type, total ayahs.
   - `components/EditionSwitcher.vue`: Selector for reciters and translation editions.
   - `components/QuranAudioBar.vue`: Floating sticky bottom audio player bar for continuous playback across pages.
   - `components/QuranVersePickerModal.vue`: Modal allowing search/browse and selecting verses for composer injection.
   - `views/QuranHomeView.vue`: Quran landing page with Surah/Juz tabs, recent bookmarks, quick search.
   - `views/SurahReaderView.vue`: Full reading view for specific Surah with scrolling, audio sync, and edition toggles.
   - `views/JuzReaderView.vue`: Reading view segmented by Juz.
   - `views/QuranSearchView.vue`: Full-text Quran search interface with highlighted matching terms.
3. **Marketplace UI Integration**:
   - `frontend/src/views/FeedView.vue`: Replace Tab 3 placeholder (`UnderDevelopmentCard`) with rich Plugin Marketplace listing, search, category filters, details modal, and install/uninstall toggle buttons.
   - Support `/marketplace` or `/plugins` routing.
4. **Non-Invasive Composer Action Integration**:
   - `frontend/src/components/TopicMessageInput.vue`: Plus action sheet dynamically querying active plugins for composer actions, launching `QuranVersePickerModal`, and inserting formatted Markdown:
     ```markdown
     > ﴿...﴾
     > translation
     > — Surah Name (Ayah Number)
     ```
   - Core message publishing pipeline remains strictly untouched and standard.
5. **Root Setup**:
   - `frontend/src/plugins/index.ts`: Initialization module setting up plugin registry and auto-loading manifests.
   - `frontend/src/main.ts`: Calls plugin initialization during app bootstrap.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Plugin Types & Interfaces | `pluginTypes.ts` with strict TypeScript contracts | M3 | R3 |
| 2 | Plugin Registry Store | `pluginRegistry.ts` Pinia store with persistence & toggle | M3 | R3 |
| 3 | Dynamic Plugin Loader | `pluginLoader.ts` with `import.meta.glob` & dynamic routing | M3 | R3 |
| 4 | Plugin Error Boundary | `PluginErrorBoundary.vue` with `onErrorCaptured` | M3 | R3 |
| 5 | Quran Plugin Manifest | `manifest.ts` declaring routes, composer actions, metadata | M3 | R3 |
| 6 | Quran API Client & Types | `api.ts` & `types.ts` connecting to backend Quran endpoints | M3 | R3 |
| 7 | Quran Composables | `useQuranAudio.ts` & `useQuranReader.ts` | M3 | R3 |
| 8 | Quran UI Components | AyahCard, SurahHeader, EditionSwitcher, QuranAudioBar, QuranVersePickerModal | M3 | R3 |
| 9 | Quran Views | QuranHomeView, SurahReaderView, JuzReaderView, QuranSearchView | M3 | R3 |
| 10 | Marketplace View & Tab 3 | FeedView Tab 3 replacement & `/marketplace` route | M3 | R3 |
| 11 | Composer Action Sheet | `TopicMessageInput.vue` dynamic plugin action injection | M3 | R3 |
| 12 | Root Bootstrap | `plugins/index.ts` & `main.ts` integration | M3 | R3 |

## Verification Criteria
1. `npm run type-check` (`vue-tsc --build`) passes with 0 errors.
2. `npm run build` succeeds with 0 errors and generates production bundles.
3. Zero regressions in existing feed, chat, donations, or profile views.
4. Clean Forensic Integrity Audit.
