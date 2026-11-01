# Milestone 3 Exploration Report: Official Quran Plugin & Mini-App Architecture

**Agent**: Explorer 2 Milestone 3 (`explorer_m3_2`)  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_m3_2`  
**Target Module**: Frontend Quran Plugin (`frontend/src/plugins/quran/`) & Mini-App  
**Parent Agent ID**: `cd5a00b8-885e-4201-9b0b-5b392a950dea`  
**Date**: 2026-08-24T01:02:45Z  

---

## 1. Observation

### 1.1 Backend Quran Endpoints & Exact Schemas (`backend/plugins/quran/`)
Investigation of `backend/plugins/quran/urls.py`, `views.py`, `serializers.py`, and `models.py` confirms the following DRF endpoints:

| Endpoint | Method | Params / Payload | Response Structure | Purpose |
|---|---|---|---|---|
| `/api/plugins/quran/` | `GET` | None | `PluginDetail` (identifier, name, version, capabilities, scopes) | Plugin metadata lookup |
| `/api/plugins/quran/editions/` | `GET` | `language`, `type` (`quran`, `translation`, `transliteration`, `tafsir`, `audio`), `format` (`text`, `audio`), `is_default`, `q` | `QuranEdition[]`: `[{ identifier, name, english_name, language, type, format, direction, author, is_default, total_ayahs, metadata }]` | List available Quran editions & translations |
| `/api/plugins/quran/surahs/` | `GET` | `revelation_type` (`Meccan`/`Medinan`), `juz` | `QuranSurah[]`: `[{ number, name, english_name, english_name_translation, revelation_type, ayah_count, order_of_revelation, page_start, page_end, juz_start, bismillah_pre }]` | Canonical list of 114 Surahs |
| `/api/plugins/quran/surahs/<int:num>/` | `GET` | None | `QuranSurahDetail`: `QuranSurah + { prev_surah: { number }, next_surah: { number } }` | Surah metadata & adjacent navigation links |
| `/api/plugins/quran/surahs/<int:num>/ayahs/` | `GET` | `edition`, `with_translation`, `from_ayah`, `to_ayah`, `page`, `page_size`, `all` | If full: `{ surah, edition, with_translation, count, ayahs: [QuranAyah] }`<br>If paginated: `{ count, next, previous, results: [QuranAyah] }` | Retrieve Surah Ayahs with optional paired translation |
| `/api/plugins/quran/juzs/` (alias `/juz/`) | `GET` | None | `QuranJuz[]`: `[{ number, name, start_surah, start_surah_name, start_ayah, end_surah, end_surah_name, end_ayah, surah_mapping }]` | List 30 Quran Juzs with boundary mappings |
| `/api/plugins/quran/juzs/<int:num>/ayahs/` | `GET` | `edition`, `with_translation`, `page`, `page_size` | Paginated `QuranAyah[]` across all Surahs in that Juz | Paginated reading by Juz |
| `/api/plugins/quran/ayahs/<int:number>/` | `GET` | `edition`, `with_translation` | `QuranAyahDetail`: `QuranAyah + { surah: QuranSurah, edition: QuranEdition, normalized_text, highlighted_text }` | Global Ayah lookup (1–6236) |
| `/api/plugins/quran/ayahs/<int:surah>/<int:ayah>/` | `GET` | `edition`, `with_translation` | `QuranAyahDetail` | Surah:Ayah coordinate lookup |
| `/api/plugins/quran/search/` | `GET` | `q` (min 2 chars), `edition`, `language`, `surah`, `juz`, `exact`, `page`, `page_size`, `with_translation` | `QuranSearchResponse`: `{ query, normalized_query, edition, count, total_matches, page, page_size, total_pages, results: [QuranSearchResult] }` | Normalized search with `<mark>` diacritic-preserving highlighted authentic text |
| `/api/plugins/quran/compare/` | `GET` | `surah`, `ayah`, `editions` (comma-separated IDs) | `QuranCompareResponse`: `{ surah, ayah_number, global_number, juz, page, editions: [{ edition, text, audio_url }] }` | Multi-edition parallel verse comparison |
| `/api/plugins/quran/format-reference/` | `POST` | `{ surah, ayah_from, ayah_to, edition, translation_edition, include_citation, lang }` | `QuranFormatReferenceResponse`: `{ markdown, surah, surah_number, surah_name, surah_english_name, ayah_from, ayah_to, ayah_number, arabic_text, translation_text, translation_author, external_id, metadata }` | Formatted Markdown quote & metadata for Composer insertion |

### 1.2 Frontend Styling & Foundations (`frontend/src/`)
- **CSS Engine**: Tailwind CSS v4 with `@theme inline` mapping to CSS variables.
- **Color Palette & Theme**:
  - Light mode: Emerald accent `emerald-600` (`#059669`), `emerald-500/10` subtle backgrounds.
  - Dark mode: `dark:bg-zinc-900`, `dark:border-zinc-800`, `dark:text-zinc-100`, `dark:bg-emerald-950/20`.
- **RTL & Internationalization**: Native `dir="rtl"` with `languageStore.isFa` / `languageStore.dir`.
- **Typography**:
  - Persian/UI text: `IRANYekanX` variable font.
  - Arabic Quranic text: `font-serif` with font stack fallbacks (`'Scheherazade New', 'Amiri', 'Traditional Arabic', 'Uthmanic', serif`), `leading-loose`, `text-right`.
- **Icons**: `@lucide/vue` (`BookOpenIcon`, `SearchIcon`, `PlayIcon`, `PauseIcon`, `Volume2Icon`, `VolumeXIcon`, `BookmarkIcon`, `CopyIcon`, `Share2Icon`, `SkipForwardIcon`, `SkipBackIcon`, `RotateCcwIcon`, `Settings2Icon`, etc.).
- **UI Primitives**: `shadcn-vue` components (`Button`, `Badge`, `Dialog`, `Popover`, `Select`, `DropdownMenu`, `Tabs`, `ScrollArea`, `Switch`, `Slider`).
- **Build Status**: Verified that `npm run type-check` (`vue-tsc --build`) passes with **0 errors**.

### 1.3 Audio CDN Endpoints & Reciter Streaming Architecture
1. **Primary Source**: `QuranAyah.audio_url` from backend if populated.
2. **Dynamic CDN Providers**:
   - **EveryAyah CDN**: `https://everyayah.com/data/{reciter_id}/{surah_3digit}{ayah_3digit}.mp3`
     - Reciter IDs: `Alafasy_128kbps`, `Parhizgar_48kbps` (Persian standard tartil), `Abdul_Basit_Murattal_192kbps`, `Minshawy_Murattal_128kbps`, `Husary_128kbps`, `Ghamadi_40kbps`.
   - **Islamic Network CDN**: `https://cdn.islamic.network/quran/audio/128/{reciter_id}/{global_ayah_number}.mp3`
     - Reciter IDs: `ar.alafasy`, `ar.abdulbasitmurattal`, `ar.parhizgar`, `ar.minshawi`, `ar.husary`.
   - **Quran.com Audio CDN**: `https://verses.quran.com/{reciter_path}/{surah_3digit}{ayah_3digit}.mp3`.

---

## 2. Logic Chain & Architecture Design

### 2.1 File & Module Layout (`frontend/src/plugins/quran/`)

```
frontend/src/plugins/quran/
├── manifest.ts                     # PluginManifest definition (routes, composer actions, metadata)
├── api.ts                          # Fully typed API client for /api/plugins/quran/
├── types.ts                        # TypeScript interfaces for models & responses
├── index.ts                        # Entry point exporting ClientPlugin and public modules
├── composables/
│   ├── useQuranAudio.ts            # Global singleton audio player (streaming, auto-advance, speed)
│   └── useQuranReader.ts           # Reader state, font size, translation toggle, bookmarks
├── components/
│   ├── AyahCard.vue                # Verse card with Arabic Uthmani, translation, actions
│   ├── SurahHeader.vue             # Header banner with calligraphy & Bismillah
│   ├── EditionSwitcher.vue         # Reciter & translation switcher popover
│   ├── QuranAudioBar.vue           # Floating sticky bottom audio player
│   └── QuranVersePickerModal.vue   # Modal for Composer verse selection & search
└── views/
    ├── QuranHomeView.vue           # Quran landing page with Surah/Juz tabs & quick search
    ├── SurahReaderView.vue         # Full Surah reader with audio sync & auto-scroll
    ├── JuzReaderView.vue           # Juz-segmented reader
    └── QuranSearchView.vue         # Full-text Quran search with diacritic highlighting
```

---

### 2.2 Core Specification Details

#### A. `manifest.ts`
Conforms strictly to `PluginManifest` (`pluginTypes.ts`):
- `manifest_version: 1`
- `identifier: 'quran'`
- `name: 'Official Quran Plugin'`, `nameFa: 'افزونه رسمی قرآن کریم'`
- `version: '1.0.0'`
- `capabilities: ['composer_action', 'mini_app', 'search_provider']`
- `scopes: ['read:content', 'read:quran']`
- `routes`:
  - `/apps/quran` -> `QuranHomeView.vue` (Name: `quran-home`)
  - `/apps/quran/surahs/:number` -> `SurahReaderView.vue` (Name: `quran-surah-reader`)
  - `/apps/quran/juz/:number?` -> `JuzReaderView.vue` (Name: `quran-juz-reader`)
  - `/apps/quran/search` -> `QuranSearchView.vue` (Name: `quran-search`)
- `menuItems`: Route entry pointing to `/apps/quran` with icon `📖`
- `composerActions`: Action `'quran-insert-ayah'` with `QuranVersePickerModal` dialog component

#### B. `api.ts` & `types.ts`
Full TypeScript mapping of backend endpoints:
- `getEditions(params)` -> `QuranEdition[]`
- `getSurahs(params)` -> `QuranSurah[]`
- `getSurahDetail(number)` -> `QuranSurah` (with `prev_surah`, `next_surah`)
- `getSurahAyahs(number, options)` -> `{ surah, edition, with_translation, count, ayahs: QuranAyah[] }`
- `getJuzs()` -> `QuranJuz[]`
- `getJuzAyahs(number, options)` -> Paginated Ayahs for Juz
- `getAyah(surah, ayah, options)` -> `QuranAyah`
- `getAyahByGlobal(number, options)` -> `QuranAyah`
- `search(params)` -> `QuranSearchResponse` (with `results: QuranSearchResult[]`)
- `compare(params)` -> `QuranCompareResponse`
- `formatReference(payload)` -> `QuranFormatReferenceResponse`

#### C. `composables/useQuranAudio.ts`
Reactive singleton managing HTML5 `Audio`:
- **State**:
  - `isPlaying`: boolean
  - `isLoading`: boolean
  - `currentSurah`: `QuranSurah | null`
  - `currentAyahNumber`: number | null (1..N)
  - `currentGlobalNumber`: number | null (1..6236)
  - `currentReciterId`: string (default `'ar.alafasy'`)
  - `playbackRate`: number (0.75, 1.0, 1.25, 1.5, 2.0)
  - `currentTime`: number, `duration`: number, `progress`: number (0..100)
  - `repeatMode`: `'none' | 'ayah' | 'surah'`
  - `volume`: number (0..1), `isMuted`: boolean
- **Methods**:
  - `playAyah(surah: QuranSurah, ayahNumber: number, audioUrl?: string)`: Resolves CDN URL, initializes audio, begins playback.
  - `togglePlayPause()`: Toggles current playback.
  - `nextAyah()`: Automatically advances to next verse within Surah, or loops if `repeatMode === 'surah'`.
  - `prevAyah()`: Rewinds to previous verse.
  - `seek(progressPercent: number)`: Updates `audio.currentTime`.
  - `setPlaybackRate(rate: number)`: Adjusts `audio.playbackRate`.
  - `setReciter(reciterId: string)`: Switches reciter and persists choice.
  - `onAyahChanged(callback)`: Allows `SurahReaderView` to register a listener to smoothly scroll the active verse into view.

#### D. `composables/useQuranReader.ts`
User reading preferences & bookmarking persisted in `localStorage`:
- **State**:
  - `arabicEdition`: `'quran-simple'` | `'quran-uthmani'`
  - `translationEdition`: `'fa.ansarian'` | `'fa.makarem'` | `'en.sahih'` | `'none'`
  - `showTranslation`: boolean
  - `fontSize`: number (range 18–44px, default 24px)
  - `showBismillah`: boolean
  - `bookmarks`: `Array<{ id: string; surahNumber: number; surahName: string; ayahNumber: number; addedAt: string; textPreview: string }>`
  - `lastRead`: `{ surahNumber: number; surahName: string; ayahNumber: number; timestamp: string } | null`
- **Methods**:
  - `toggleBookmark(surah: QuranSurah, ayah: QuranAyah)`
  - `isBookmarked(surahNumber: number, ayahNumber: number): boolean`
  - `saveLastRead(surahNumber: number, surahName: string, ayahNumber: number)`
  - `setFontSize(size: number)`

#### E. Components Specification
1. **`AyahCard.vue`**:
   - **Props**: `ayah: QuranAyah`, `surah: QuranSurah`, `isPlaying?: boolean`, `isCurrentAudio?: boolean`, `isBookmarked?: boolean`, `fontSize?: number`, `showTranslation?: boolean`.
   - **Features**:
     - Arabic text rendered in Quranic calligraphy style (`font-serif`) with verse ornament number badge `۝{num}`.
     - Translation text displayed in italicized block below with subtle vertical accent border.
     - Action toolbar: Play verse audio, Copy Markdown citation, Copy Arabic only, Bookmark toggle, Compare editions button.
2. **`SurahHeader.vue`**:
   - **Props**: `surah: QuranSurah`, `showBismillah?: boolean`.
   - **Features**:
     - Gradient banner with Surah name in ornate Arabic typography.
     - Subtitle with English name and translation.
     - Badges: Revelation type (مکی / مدنی), Ayah count, Juz start index.
     - Calligraphic Bismillah rendering (`بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ`) with ornamental divider (suppressed for Surah 9 At-Tawbah).
3. **`EditionSwitcher.vue`**:
   - **Props / Emits**: Settings sync with `useQuranReader` and `useQuranAudio`.
   - **Features**:
     - Dropdowns for: Arabic Script (`quran-simple`, `quran-uthmani`), Translation (`fa.ansarian`, `fa.makarem`, `en.sahih`), Audio Reciter (`Mishary Alafasy`, `Shahriar Parhizgar`, `Abdul Basit`, `Al-Minshawi`, `Al-Husary`).
     - Font size slider with live preview.
     - Translation visibility toggle.
4. **`QuranAudioBar.vue`**:
   - Floating sticky bottom player bar (visible when audio is loaded/playing).
   - Shows current Surah & Ayah info, Reciter name, and duration counter (`mm:ss / mm:ss`).
   - Interactive progress bar for seeking.
   - Controls: Play/Pause, Next Ayah, Previous Ayah, Repeat Mode toggle (`none`, `ayah`, `surah`), Playback Speed menu (`0.75x`, `1x`, `1.25x`, `1.5x`, `2x`), Volume / Mute toggle, Close button.
5. **`QuranVersePickerModal.vue`**:
   - **Props**: `onInsert?: (markdown: string) => void`.
   - **Emits**: `(e: 'insert', markdown: string)`, `(e: 'close')`.
   - **Features**:
     - **Tab 1: Browse Mode**: Select Surah (1–114), select Ayah range (`from_ayah` to `to_ayah`), select translation edition. Real-time preview of formatted blockquote.
     - **Tab 2: Quick Search Mode**: Search input with instant keyword matching across Ayahs, click to preview and select.
     - Inserts formatted Markdown via `props.onInsert` or `emit('insert')`.

#### F. Views Specification
1. **`QuranHomeView.vue`**:
   - Top Header with Quran icon, search shortcut, and "Continue Reading" banner (resuming `lastRead`).
   - Tabs:
     - **Surahs Tab**: Grid of 114 Surah cards with search filter, showing Surah name, number, revelation type, ayah count, juz index.
     - **Juzs Tab**: Grid of 30 Juz cards showing start/end surah ranges and ayah boundaries.
     - **Bookmarks Tab**: List of saved verses with instant navigation to Surah reader and delete action.
2. **`SurahReaderView.vue`**:
   - Displays `SurahHeader`, top navigation bar (Prev Surah, Next Surah, Surah selector, Edition switcher popover, Search button).
   - Full vertical list of `AyahCard` components.
   - Synced with `useQuranAudio`: highlights active playing verse with emerald border/glow and automatically scrolls it to center of viewport.
   - Bottom `QuranAudioBar` sticky player.
3. **`JuzReaderView.vue`**:
   - Juz selector (1–30) with prev/next buttons.
   - Displays Ayahs grouped under chapter banners as the Juz spans multiple Surahs.
   - Continuous audio streaming across Surah boundaries within the Juz.
4. **`QuranSearchView.vue`**:
   - Advanced search bar with debounced input and filter dropdowns (Surah filter, Juz filter, Translation filter, Exact match toggle).
   - Renders search result list with diacritic-preserving highlighted authentic text via safe `<mark>` tags.
   - Actions per result: "Open in Reader", "Play Audio", "Copy Markdown Quote".

---

## 3. Caveats

1. **Browser Audio Autoplay Policy**: Browsers may restrict automatic playback until the user initiates a first interaction (e.g. clicking "Play" or selecting an Ayah). `useQuranAudio` must handle `play()` Promise rejections gracefully.
2. **Audio CDN Availability**: Third-party CDNs (EveryAyah, Islamic Network) require internet connectivity. If an audio stream fails to load, `useQuranAudio` should emit a user-friendly toast/alert rather than breaking the reader.
3. **Diacritic Highlighting in Search**: The backend `/api/plugins/quran/search/` endpoint returns `highlighted_text` containing `<mark>` tags around matched tokens in authentic Uthmani script. Frontend views must render this safely using `v-html` with sanitized input.
4. **Zero-Breaking-Change Guarantee**: The Quran plugin components must remain completely self-contained in `frontend/src/plugins/quran/` without mutating core store schemas or breaking existing chat/topic feeds.

---

## 4. Conclusion

The architecture for the Official Quran Plugin (`frontend/src/plugins/quran/`) is comprehensively designed, fully compatible with existing backend APIs (`/api/plugins/quran/`), and ready for implementation.

### Implementation Blueprint Summary
- **Manifest & API**: `manifest.ts`, `api.ts`, `types.ts`, `index.ts`.
- **Composables**: `useQuranAudio.ts` (audio streaming engine with auto-advance & speed control), `useQuranReader.ts` (reader preferences & bookmarks).
- **Components**: `AyahCard.vue`, `SurahHeader.vue`, `EditionSwitcher.vue`, `QuranAudioBar.vue`, `QuranVersePickerModal.vue`.
- **Views**: `QuranHomeView.vue`, `SurahReaderView.vue`, `JuzReaderView.vue`, `QuranSearchView.vue`.
- **Composer Action**: Seamless insertion of standard Quran blockquote Markdown into `TopicMessageInput.vue` via `QuranVersePickerModal.vue`.

---

## 5. Verification Method

To verify the frontend Quran plugin architecture:

```powershell
cd f:\AVA\tafakor\frontend

# 1. Verify TypeScript types and template compilation
npm run type-check

# 2. Verify production bundling
npm run build-only

# 3. Backend Quran API test suite verification
cd f:\AVA\tafakor\backend
python manage.py test plugins.quran.tests
```
