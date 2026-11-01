# Frontend Plugin System & Quran Mini-App (R3) Survey & Design Report

**Explorer**: Explorer 3 (Frontend Plugin System & Composer Specialist)  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_survey_3`  
**Target Milestone**: R3 (Frontend Plugin Registry, Dynamic Loader, Error Boundary, Marketplace UI, Quran Reader Mini-App, Composer Action)

---

## 1. Observation

Direct observations and evidence from the codebase:

### 1.1 Frontend Tech Stack & Build Toolchain
* **Framework**: Vue 3.5.32 (`<script setup lang="ts">`, Composition API) (`frontend/package.json:28`).
* **Bundler**: Vite 8.0.8 with `@tailwindcss/vite` 4.3.1 and `vite-plugin-vue-devtools` 8.1.1 (`frontend/package.json:33,42`).
* **Router**: Vue Router 5.1.0 (`frontend/package.json:30`).
* **State Management**: Pinia 3.0.4 (`frontend/package.json:23`).
* **UI Components**: Shadcn-Vue 2.7.4 with Reka UI 2.10.1 (`frontend/package.json:24-25`).
* **Icons**: `@lucide/vue` 1.26.0 (`frontend/package.json:17`).
* **Utilities**: DOMPurify 3.4.14 (`frontend/package.json:22`), `@vueuse/core` 14.3.0 (`frontend/package.json:18`), `tailwind-merge` 3.6.0 (`frontend/package.json:26`), `clsx` 2.1.1 (`frontend/package.json:21`).
* **TypeScript & Type Check**: TypeScript ~6.0.0 with `vue-tsc` 3.2.6 (`frontend/package.json:41,44`).
* **Verification Commands Executed**:
  - `npm run type-check` (`vue-tsc --build`): Exited with code `0`.
  - `npm run build` (`run-p type-check "build-only {@}" --`): Exited with code `0` (Rolldown / Vite build cleanly produced client chunks in 3.23s).

### 1.2 Router & View Architecture
* In `frontend/src/router/index.ts`:
  - Current routes: `/login`, `/`, `/topic/:id`, `/profile`, `/donate`, `/marketplace`, `/playground/*`, `/:pathMatch(.*)* -> /`.
  - Route navigation guards (`router.beforeEach`, lines 56-72) handle `meta.requiresAuth` and `meta.requiresGuest` via `userStore.isLoginModalOpen`.
  - `FeedView.vue` is currently the multi-tab container for `home`, `donate`, `marketplace`, and `profile` (lines 50-145).
* In `frontend/src/views/FeedView.vue`:
  - Line 97-99: Route `/marketplace` maps to `currentTab.value = 'marketplace'`.
  - Line 1279-1296: Currently renders `UnderDevelopmentCard` for the marketplace placeholder.
  - Line 1188-1209: Renders sticky bottom bar containing `TopicMessageInput.vue`.

### 1.3 TopicMessageInput & Post Publishing Flow
* In `frontend/src/components/TopicMessageInput.vue`:
  - Text input state: `text = ref(props.initialText)` (line 77).
  - Plus Action button triggers `handlePlusClick` (lines 544-548), opening `isActionSheetOpen = ref(false)` Dialog (lines 1021-1090).
  - Plus modal currently displays 3 action cards: Donation Campaign (`create-donation`), Poll (coming soon), and Event (coming soon).
  - Formatted text uses standard Markdown formatting tags via `utils/textFormatter.ts` (`wrapSelection`, `parseMarkdownToHtml` with DOMPurify).
  - Submission (`handleSend`, lines 232-257): Emits `@send="{ text: text.value.trim(), attachments: completedAttachments }"`.
* In `frontend/src/views/FeedView.vue`:
  - `handleSendPost` (lines 927-973): Receives `{ text: string }`, checks duplicates, creates `FormData` with `topic`, `content: message.text`, `media_file`, `media_type`, and calls `postStore.createPost(formData)`.
  - The post content is rendered in `PostCard.vue` via `FormattedText.vue` using `parseMarkdownToHtml()`. Blockquotes (`> quote`), bold (`**bold**`), italics (`*italic*` / `_italic_`), inline code (`` `code` ``), and line breaks are natively supported.

### 1.4 Existing Marketplace Prototypes
* In `frontend/src/components/marketplace/MarketplaceAppIcon.vue`:
  - Implements standard squircle icon with sizes (`sm`, `md`, `lg`, `responsive`), ratings, badges, and Coming Soon overlay.
* In `frontend/src/views/playground/MarketplaceIconPlayground.vue`:
  - Implements interactive 3-column marketplace grid simulation with live app detail dialogs, screenshot galleries, and installation toggles.

---

## 2. Logic Chain

From the observed system architecture to the zero-breaking-change Plugin System design:

```
[Observation 1.1 & 1.2: Vue Router & Dynamic Import Capability]
       │
       ▼
[Logic Step 1: Dynamic Route & Component Registration]
Vite supports native `import()`. Plugins should register routes lazily via `router.addRoute()`
or dedicated sub-router namespaces (`/apps/:pluginId/*`), ensuring zero upfront bundle cost.
       │
       ▼
[Observation 1.3: Post Publishing Takes Plain Markdown Strings]
       │
       ▼
[Logic Step 2: Non-Invasive Composer Action Injection]
Plugins providing composer actions (like Quran Verse Picker) only need to inject formatted Markdown
into `TopicMessageInput.vue`'s text model. The core publishing pipeline remains 100% untouched.
       │
       ▼
[Observation 1.1: Component Isolation & Resilience]
       │
       ▼
[Logic Step 3: Plugin Error Boundary Wrapper]
Using Vue 3 `onErrorCaptured`, any plugin-level component runtime crash is caught and
isolated in a styled fallback alert, preventing the main feed, chat, or app shell from breaking.
       │
       ▼
[Observation 1.4: Existing Marketplace UI Patterns]
       │
       ▼
[Logic Step 4: Marketplace & Quran Mini-App Integration]
Replace `UnderDevelopmentCard` with a full Marketplace view connected to `/api/plugins/`
and provide `/apps/quran/*` mini-app views for Surahs, Ayahs, Recitation Audio, and Search.
```

---

## 3. Caveats

1. **Vite Dynamic Route HMR**: In dev mode, dynamically adding routes via `router.addRoute()` must ensure no route duplication occurs on Vite hot reload. Routes should be registered idempotently using unique route names.
2. **Audio Streaming & Media Context**: Quran recitations use external CDN audio streams (e.g. `everyayah.com` / `qurancdn.com`). Cross-Origin Resource Sharing (CORS) and standard `<audio>` elements should be wrapped in a shared audio composable with pause-on-unmount.
3. **Persian & Arabic Typography**: Quranic Arabic verses require proper RTL rendering, font family fallbacks (e.g. `Amiri`, `Scheherazade New`, `IRANYekanXVF`), and bracket ornaments (`﴿` and `﴾`).
4. **Auth State in Plugins**: Some marketplace operations (installing for a topic) require topic admin/creator privileges, while reading the Quran in `/apps/quran` is accessible to all users (guest & authenticated).

---

## 4. Conclusion & Architectural Design

### 4.1 Directory Structure (`frontend/src/plugins`)

```
frontend/src/
├── plugins/
│   ├── core/
│   │   ├── pluginTypes.ts            # Interfaces: PluginManifest, ComposerAction, PluginRoute
│   │   ├── pluginRegistry.ts         # Pinia Store: State, installation, topic enablement
│   │   ├── pluginLoader.ts           # Dynamic module loader & lifecycle executor
│   │   ├── PluginErrorBoundary.vue   # Vue 3 onErrorCaptured isolation wrapper
│   │   └── index.ts                  # Public core exports
│   ├── quran/                        # Official Quran Plugin Mini-App
│   │   ├── manifest.ts               # Quran plugin manifest & capability declarations
│   │   ├── api.ts                    # Client for /api/plugins/quran/*
│   │   ├── types.ts                  # Quran Surah, Ayah, Edition, Juz, Search types
│   │   ├── composables/
│   │   │   ├── useQuranAudio.ts      # Audio player with verse synchronization
│   │   │   └── useQuranReader.ts     # Navigation, font sizing, translation state
│   │   ├── components/
│   │   │   ├── AyahCard.vue          # Authentic Arabic text + translation + play/copy
│   │   │   ├── SurahHeader.vue       # Surah meta (revelation, total verses, bismillah)
│   │   │   ├── EditionSwitcher.vue   # Selector for translations (Fooladvand, Makarem, etc.)
│   │   │   ├── QuranAudioBar.vue     # Sticky bottom audio player with speed & reciter controls
│   │   │   └── QuranVersePickerModal.vue # Composer Action Modal: Surah/Ayah selection -> Markdown
│   │   └── views/
│   │       ├── QuranHomeView.vue     # Surah & Juz catalog view (/apps/quran)
│   │       ├── SurahReaderView.vue   # Verse-by-verse reader (/apps/quran/surah/:id)
│   │       ├── JuzReaderView.vue     # Juz reader (/apps/quran/juz/:id)
│   │       └── QuranSearchView.vue   # Full-text / normalized search (/apps/quran/search)
│   └── index.ts                      # Root plugin system initializer
```

---

### 4.2 Concrete Implementation Specifications

#### A. `src/plugins/core/pluginTypes.ts`

```typescript
import type { Component } from 'vue'
import type { RouteRecordRaw } from 'vue-router'

export type PluginCapability = 
  | 'routes' 
  | 'composer_actions' 
  | 'topic_tabs' 
  | 'settings' 
  | 'card_renderer'

export interface PluginComposerActionContext {
  topicId?: number | string
  currentText: string
  insertText: (markdown: string, replace?: boolean) => void
  closeModal: () => void
}

export interface PluginComposerAction {
  id: string
  title: string
  icon: any // Lucide component
  badge?: string
  description?: string
  component?: () => Promise<Component> // Lazy modal component
  execute?: (ctx: PluginComposerActionContext) => Promise<void> | void
}

export interface PluginTopicTab {
  id: string
  title: string
  icon: any
  component: () => Promise<Component>
}

export interface PluginRouteConfig {
  path: string
  name: string
  component: () => Promise<Component>
  meta?: {
    title?: string
    requiresAuth?: boolean
    hideNavigation?: boolean
    [key: string]: any
  }
  children?: PluginRouteConfig[]
}

export interface PluginManifest {
  id: string
  name: string
  nameFa: string
  version: string
  description: string
  descriptionFa: string
  author: string
  iconUrl?: string
  icon?: any
  category: 'religious' | 'tools' | 'ai' | 'analytics' | 'utility'
  capabilities: PluginCapability[]
  isOfficial?: boolean
  isComingSoon?: boolean
  rating?: number
  downloadsCount?: number
  routes?: PluginRouteConfig[]
  composerActions?: PluginComposerAction[]
  topicTabs?: PluginTopicTab[]
  onLoad?: () => Promise<void> | void
  onEnable?: (topicId?: number | string) => Promise<void> | void
  onDisable?: (topicId?: number | string) => Promise<void> | void
}
```

---

#### B. `src/plugins/core/pluginRegistry.ts` (Pinia Store)

```typescript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { PluginManifest, PluginComposerAction } from './pluginTypes'
import api from '@/api'

export const usePluginRegistryStore = defineStore('pluginRegistry', () => {
  // All manifests registered on client
  const registeredPlugins = ref<Map<string, PluginManifest>>(new Map())
  
  // User installed plugins (from /api/plugins/installations/)
  const installedPluginIds = ref<Set<string>>(new Set())
  
  // Topic enabled plugins mapping: topicId -> Set<pluginId>
  const topicEnabledPlugins = ref<Map<number | string, Set<string>>>(new Map())
  
  const loading = ref(false)

  const registerPlugin = (manifest: PluginManifest) => {
    registeredPlugins.value.set(manifest.id, manifest)
  }

  const unregisterPlugin = (pluginId: string) => {
    registeredPlugins.value.delete(pluginId)
  }

  const isPluginInstalled = (pluginId: string) => {
    return installedPluginIds.value.has(pluginId)
  }

  const isPluginEnabledForTopic = (pluginId: string, topicId?: number | string) => {
    if (!topicId) return isPluginInstalled(pluginId)
    const topicSet = topicEnabledPlugins.value.get(topicId)
    return topicSet ? topicSet.has(pluginId) : false
  }

  const getAvailableComposerActions = (topicId?: number | string): PluginComposerAction[] => {
    const actions: PluginComposerAction[] = []
    registeredPlugins.value.forEach((manifest) => {
      // Check if installed and enabled for this topic
      if (manifest.composerActions && isPluginEnabledForTopic(manifest.id, topicId)) {
        actions.push(...manifest.composerActions)
      }
    })
    return actions
  }

  const fetchPluginState = async () => {
    loading.value = true
    try {
      const res = await api.get('/api/plugins/')
      if (res.data?.results) {
        installedPluginIds.value.clear()
        res.data.results.forEach((p: any) => {
          if (p.is_installed) installedPluginIds.value.add(p.id)
        })
      }
    } catch (err) {
      console.warn('Failed to sync plugin state:', err)
    } finally {
      loading.value = false
    }
  }

  const installPlugin = async (pluginId: string) => {
    await api.post(`/api/plugins/${pluginId}/install/`)
    installedPluginIds.value.add(pluginId)
  }

  const uninstallPlugin = async (pluginId: string) => {
    await api.post(`/api/plugins/${pluginId}/uninstall/`)
    installedPluginIds.value.delete(pluginId)
  }

  const toggleTopicPlugin = async (pluginId: string, topicId: number | string, enabled: boolean) => {
    await api.post(`/api/plugins/${pluginId}/topic-toggle/`, { topic_id: topicId, enabled })
    if (!topicEnabledPlugins.value.has(topicId)) {
      topicEnabledPlugins.value.set(topicId, new Set())
    }
    const set = topicEnabledPlugins.value.get(topicId)!
    if (enabled) set.add(pluginId)
    else set.delete(pluginId)
  }

  return {
    registeredPlugins,
    installedPluginIds,
    topicEnabledPlugins,
    loading,
    registerPlugin,
    unregisterPlugin,
    isPluginInstalled,
    isPluginEnabledForTopic,
    getAvailableComposerActions,
    fetchPluginState,
    installPlugin,
    uninstallPlugin,
    toggleTopicPlugin
  }
})
```

---

#### C. `src/plugins/core/pluginLoader.ts` (Dynamic Router & Loader)

```typescript
import type { Router } from 'vue-router'
import { h } from 'vue'
import type { PluginManifest, PluginRouteConfig } from './pluginTypes'
import { usePluginRegistryStore } from './pluginRegistry'
import PluginErrorBoundary from './PluginErrorBoundary.vue'

// Manifest imports map
const pluginManifestModules = import.meta.glob('../**/manifest.ts')

export async function initializePluginSystem(router: Router) {
  const registryStore = usePluginRegistryStore()

  for (const path in pluginManifestModules) {
    try {
      const module: any = await pluginManifestModules[path]()
      const manifest: PluginManifest = module.default || module.manifest
      if (manifest && manifest.id) {
        registryStore.registerPlugin(manifest)

        // Register routes with Error Boundary wrapping
        if (manifest.routes && manifest.routes.length > 0) {
          registerPluginRoutes(router, manifest.routes, manifest.id)
        }

        if (manifest.onLoad) {
          await manifest.onLoad()
        }
      }
    } catch (err) {
      console.error(`[PluginLoader] Failed to load plugin at ${path}:`, err)
    }
  }

  // Sync state from server
  await registryStore.fetchPluginState()
}

function registerPluginRoutes(router: Router, routes: PluginRouteConfig[], pluginId: string) {
  routes.forEach((routeConfig) => {
    if (!router.hasRoute(routeConfig.name)) {
      router.addRoute({
        path: routeConfig.path,
        name: routeConfig.name,
        component: () => routeConfig.component().then((comp) => {
          // Wrap dynamically imported component in PluginErrorBoundary
          return {
            render() {
              return h(PluginErrorBoundary, { pluginId }, {
                default: () => h(comp.default || comp)
              })
            }
          }
        }),
        meta: routeConfig.meta || {}
      })
    }
  })
}
```

---

#### D. `src/plugins/core/PluginErrorBoundary.vue`

```vue
<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { AlertCircleIcon, RotateCcwIcon, LayersIcon } from '@lucide/vue'
import { Button } from '@/components/ui/button'
import { useLanguageStore } from '@/stores/languageStore'

const props = defineProps<{
  pluginId?: string
  fallbackTitle?: string
}>()

const languageStore = useLanguageStore()
const hasError = ref(false)
const errorMessage = ref('')

onErrorCaptured((err, instance, info) => {
  console.error(`[PluginErrorBoundary] Plugin error caught (${props.pluginId}):`, err, info)
  hasError.value = true
  errorMessage.value = err?.message || 'Unknown plugin execution error'
  // Stop propagation to prevent app crash
  return false
})

const handleRetry = () => {
  hasError.value = false
  errorMessage.value = ''
}
</script>

<template>
  <div v-if="hasError" class="w-full p-4 rounded-2xl border border-destructive/30 bg-destructive/5 text-start flex flex-col gap-3 font-sans">
    <div class="flex items-center gap-2.5 text-destructive">
      <AlertCircleIcon class="size-5 shrink-0" />
      <span class="text-xs font-bold">
        {{ props.fallbackTitle || languageStore.t('خطا در اجرای افزونه', 'Plugin Execution Error') }}
      </span>
    </div>
    <p class="text-[11px] text-muted-foreground leading-relaxed">
      {{ errorMessage }}
    </p>
    <div class="flex items-center gap-2 pt-1">
      <Button size="sm" variant="outline" class="text-xs font-bold h-7 rounded-lg gap-1" @click="handleRetry">
        <RotateCcwIcon class="size-3" />
        <span>{{ languageStore.t('تلاش مجدد', 'Retry') }}</span>
      </Button>
    </div>
  </div>
  <slot v-else />
</template>
```

---

#### E. Non-Invasive Composer Action Integration (`TopicMessageInput.vue`)

In `TopicMessageInput.vue`, the Plus Action Modal dynamically renders enabled plugin composer actions alongside standard actions:

```vue
<!-- TopicMessageInput.vue Plus Action Modal Section -->
<div class="grid grid-cols-3 gap-2.5 pt-1">
  <!-- 1. Native Donation Action -->
  <button
    type="button"
    class="group aspect-square rounded-2xl border border-primary/30 bg-primary/5 hover:bg-primary/10 flex flex-col items-center justify-center gap-2 p-2 transition-all cursor-pointer shadow-xs active:scale-95 text-center"
    @click="handleSelectDonation"
  >
    <div class="size-10 rounded-xl bg-primary/15 text-primary flex items-center justify-center group-hover:scale-110 transition-transform">
      <HeartIcon class="size-5 fill-primary/20" />
    </div>
    <span class="text-xs font-bold text-foreground group-hover:text-primary">
      {{ languageStore.t('ایجاد اهدا', 'Donation') }}
    </span>
  </button>

  <!-- 2. Dynamic Plugin Actions (e.g. Quran Verse Picker) -->
  <button
    v-for="action in availablePluginActions"
    :key="action.id"
    type="button"
    class="group aspect-square rounded-2xl border border-emerald-500/30 bg-emerald-500/5 hover:bg-emerald-500/10 flex flex-col items-center justify-center gap-2 p-2 transition-all cursor-pointer shadow-xs active:scale-95 text-center"
    @click="handleTriggerPluginAction(action)"
  >
    <div class="size-10 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center group-hover:scale-110 transition-transform">
      <component :is="action.icon || BookOpenIcon" class="size-5" />
    </div>
    <span class="text-xs font-bold text-foreground group-hover:text-emerald-600">
      {{ action.title }}
    </span>
  </button>
</div>

<!-- Dynamic Lazy-Loaded Plugin Modal Component -->
<component
  :is="activePluginModalComponent"
  v-if="activePluginModalComponent"
  :open="isPluginModalOpen"
  @update:open="(val: boolean) => isPluginModalOpen = val"
  @insert="handleInsertMarkdownFromPlugin"
/>
```

**Markdown Injection Handler**:
```typescript
const handleInsertMarkdownFromPlugin = (markdownText: string) => {
  if (!markdownText) return
  
  const el = textareaRef.value
  if (el) {
    const start = el.selectionStart ?? text.value.length
    const end = el.selectionEnd ?? text.value.length
    const before = text.value.substring(0, start)
    const after = text.value.substring(end)
    
    // Add clean newlines if inserting inside existing paragraph
    const prefix = (before.length > 0 && !before.endsWith('\n\n')) ? '\n\n' : ''
    const suffix = (after.length > 0 && !after.startsWith('\n\n')) ? '\n\n' : ''
    
    text.value = `${before}${prefix}${markdownText}${suffix}${after}`
  } else {
    text.value = text.value ? `${text.value}\n\n${markdownText}` : markdownText
  }
  
  isPluginModalOpen.value = false
  activePluginModalComponent.value = null
  isActionSheetOpen.value = false
  
  nextTick(() => {
    adjustHeight()
  })
}
```

---

#### F. Quran Mini-App Specifications (`src/plugins/quran`)

1. **Manifest (`src/plugins/quran/manifest.ts`)**:
   - `id`: `'quran'`
   - `name`: `'Holy Quran'` / `nameFa`: `'قرآن کریم'`
   - `version`: `'1.0.0'`
   - `icon`: `BookOpenIcon`
   - `category`: `'religious'`
   - `capabilities`: `['routes', 'composer_actions']`
   - `routes`:
     - `/apps/quran` -> `QuranHomeView.vue` (Surah & Juz list, Quick Search bar)
     - `/apps/quran/surah/:surahNumber` -> `SurahReaderView.vue` (Ayah reader, audio recitation, translation switcher)
     - `/apps/quran/juz/:juzNumber` -> `JuzReaderView.vue` (Juz navigation)
     - `/apps/quran/search` -> `QuranSearchView.vue` (Normalized search with match highlighting)
   - `composerActions`:
     - `id`: `'insert-verse'`
     - `title`: `'درج آیه قرآن'`
     - `icon`: `BookOpenIcon`
     - `component`: `() => import('./components/QuranVersePickerModal.vue')`

2. **API Client (`src/plugins/quran/api.ts`)**:
   - `fetchSurahs()`: `GET /api/plugins/quran/surahs/` -> Returns 114 Surahs with metadata.
   - `fetchSurahDetail(id, edition)`: `GET /api/plugins/quran/surahs/${id}/?edition=${edition}` -> Returns Surah with Ayahs.
   - `fetchAyahs(surahId, start, end, edition)`: `GET /api/plugins/quran/ayahs/?surah=${surahId}&start=${start}&end=${end}`.
   - `searchQuran(query, edition)`: `GET /api/plugins/quran/search/?q=${query}&edition=${edition}` -> Returns normalized text search results.
   - `fetchEditions()`: `GET /api/plugins/quran/editions/` -> Returns available text translations and reciters.

3. **Composer Markdown Output Example**:
   ```markdown
   > ﴿إِنَّ مَعَ الْعُسْرِ يُسْرًا﴾
   >
   > به یقین با هر سختی آسانی است.
   > — سوره الشرح (آیه ۶) [ترجمه انصاریان]
   ```

4. **Audio Engine (`useQuranAudio.ts`)**:
   - Audio recitations dynamically stream verse MP3s (e.g. `https://everyayah.com/data/Alafasy_128kbps/{surah_3_digits}{ayah_3_digits}.mp3`).
   - Supports: Play/Pause, Continuous Autoplay across consecutive Ayahs, Speed selector (0.75x, 1x, 1.25x), and Verse active highlight.

---

### 4.3 Marketplace UI (`/plugins` and Tab 3 in `FeedView.vue`)

* In `FeedView.vue`, replacing `UnderDevelopmentCard` with `MarketplaceView.vue`:
  - **Featured Banner**: Highlights the official Quran Plugin.
  - **Category Pills**: "همه" (All), "قرآنی و معارف" (Quran & Religious), "ابزارها" (Tools), "هوش مصنوعی" (AI).
  - **Responsive 3-Column Grid**: Utilizing `MarketplaceAppIcon.vue` with `isInstalled` indicators.
  - **Plugin Details Modal**:
    - App icon, title, category, star rating, author.
    - Full Persian description.
    - Screenshots gallery preview.
    - Topic Activation Switches: Allows enabling/disabling the plugin specifically for the current user's topics.
    - Install / Uninstall action button connected to `/api/plugins/`.

---

## 5. Verification Method

To independently verify the frontend plugin system design:

1. **Static Type Checking**:
   ```bash
   npm run type-check
   ```
   *Expected*: `vue-tsc --build` passes with 0 errors across all `src/plugins/**/*.ts` and Vue components.

2. **Production Bundle Build**:
   ```bash
   npm run build
   ```
   *Expected*: Vite and Rolldown build produces clean code-split chunks for `plugin-quran` (`dist/assets/quran-*.js`) with zero build errors.

3. **Core Non-Regression**:
   * Verify that existing routes (`/`, `/topic/:id`, `/donate`, `/profile`) and composer operations operate identically when no plugins are installed.
   * Verify that `parseMarkdownToHtml` renders Quran blockquotes and quotes cleanly in `PostCard.vue`.

---
*End of Explorer 3 Report*
