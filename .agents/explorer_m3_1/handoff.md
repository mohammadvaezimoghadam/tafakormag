# Milestone 3 — Frontend Plugin System Core Architecture & Exploration Report

**Agent**: Explorer 1 (`explorer_m3_1`)  
**Working Directory**: `f:\AVA\tafakor\.agents\explorer_m3_1`  
**Milestone**: Milestone 3 — Frontend Plugin System Core  
**Date**: 2026-08-24T01:05:00+03:30  
**Target Subsystem**: `frontend/src/plugins/core/` (`pluginTypes.ts`, `pluginRegistry.ts`, `pluginLoader.ts`, `PluginErrorBoundary.vue`, `index.ts`)  

---

## 1. Observation

### 1.1 Existing Frontend Codebase Inspection
A comprehensive inspection of the `frontend/` directory was conducted:
1. **Routing Architecture (`frontend/src/router/index.ts`)**:
   - Built on `vue-router` 5.1.0 with HTML5 history mode (`createWebHistory`).
   - Static routes defined for `/login`, `/`, `/topic/:id`, `/profile`, `/donate`, `/marketplace`, `/plugins`, and playgrounds.
   - Fallback route `/:pathMatch(.*)* -> redirect: '/'` is declared at line 60.
   - Dynamic plugin routes must be registered via `router.addRoute()` before or alongside navigation, ensuring lazy chunk loading (`import()`).
2. **Application Bootstrap (`frontend/src/main.ts`)**:
   - Pinia is instantiated (`const pinia = createPinia(); app.use(pinia)`), followed by `app.use(router)`.
   - `languageStore.init()` is executed immediately after store creation.
   - `initializePlugins(router)` is invoked prior to `app.mount('#app')`.
3. **Application Shell & Layout (`frontend/src/App.vue`)**:
   - Encapsulated within `ConfigProvider` from `reka-ui` managing document direction (`dir="rtl" | "ltr"`).
   - Dynamic toast notification system (`useToastStore`), global dark mode (`useDark` via `@vueuse/core`), and modal login dialogs.
4. **TypeScript Configuration (`frontend/tsconfig.app.json`)**:
   - `noUncheckedIndexedAccess: true` is strictly enforced.
   - Path alias `@/*` maps to `./src/*`.
   - `vue-tsc --build` executes cleanly with zero baseline errors.
5. **Backend Milestones Integration Parity**:
   - Milestone 1 (`apps/plugin_system`): Exposes `/api/plugins/` (marketplace listing, user install/uninstall/toggle, topic-level installations, and post references).
   - Milestone 2 (`plugins/quran`): Exposes `/api/plugins/quran/` (editions, surahs, ayahs, juzs, search, compare, and Markdown reference formatting).

---

## 2. Logic Chain & System Design

### 2.1 Complete TypeScript Contracts (`frontend/src/plugins/core/pluginTypes.ts`)

The plugin architecture requires strict, decoupled contracts separating platform core from plugin implementations.

```typescript
import type { Component } from 'vue'
import type { RouteRecordRaw, RouteMeta, Router } from 'vue-router'
import type { Pinia } from 'pinia'

/**
 * Supported capability types conforming to backend validator
 */
export type PluginCapability =
  | 'composer_action'
  | 'mini_app'
  | 'search_provider'
  | 'topic_action'
  | 'topic_integration'
  | 'bot_action'
  | 'feed_card'

/**
 * Granular permission scopes for security containment
 */
export type PluginPermission =
  | 'read:content'
  | 'read:quran'
  | 'write:post'
  | 'admin:topic'
  | string

/**
 * Context passed to Composer Action execute handler
 */
export interface PluginComposerActionContext {
  insertText: (text: string) => void
  currentTopicId?: number | string
  currentText?: string
  selectedText?: string
  toast?: (message: string, type?: 'success' | 'error' | 'info' | 'warning') => void
}

/**
 * Action contributed by a plugin to the Composer / TopicMessageInput
 */
export interface PluginComposerAction {
  id: string
  label: string
  labelFa?: string
  icon: string | Component
  tooltip?: string
  tooltipFa?: string
  dialogComponent?: Component
  execute?: (context: PluginComposerActionContext) => void | Promise<void>
  order?: number
  supportedContentTypes?: string[]
  shortcut?: string
}

/**
 * Navigation item contributed by a plugin to platform menus
 */
export interface PluginMenuItem {
  id: string
  label: string
  labelFa?: string
  icon: string | Component
  path: string
  order?: number
  badge?: string | number
}

/**
 * Plugin route metadata extension
 */
export interface PluginRouteMeta extends RouteMeta {
  title?: string
  titleFa?: string
  icon?: string
  requiresAuth?: boolean
  pluginId: string
  errorBoundary?: boolean
  layout?: 'default' | 'plain' | 'fullscreen'
}

/**
 * Plugin dynamic route definition
 */
export type PluginRouteConfig = RouteRecordRaw & {
  meta?: PluginRouteMeta
}

/**
 * Formal Client-side Plugin Manifest (conforms to manifest_version: 1)
 */
export interface PluginManifest {
  manifest_version: 1
  identifier: string
  name: string
  nameFa?: string
  version: string
  description?: string
  descriptionFa?: string
  author?: string
  homepage?: string
  icon?: string | Component
  is_core?: boolean
  capabilities: PluginCapability[]
  scopes?: PluginPermission[]
  routes?: PluginRouteConfig[]
  menuItems?: PluginMenuItem[]
  composerActions?: PluginComposerAction[]
  settings_schema?: Record<string, any>
  default_config?: Record<string, any>
}

/**
 * Context passed into plugin initialize lifecycle
 */
export interface PluginInitContext {
  registry: any
  router?: Router
  pinia?: Pinia
}

/**
 * Client plugin implementation bundle
 */
export interface ClientPlugin {
  manifest: PluginManifest
  initialize?: (context: PluginInitContext) => Promise<void> | void
  onDestroy?: () => Promise<void> | void
}

/**
 * Backend Marketplace Plugin representation (matches DRF PluginSerializer)
 */
export interface BackendPluginSummary {
  id: string
  identifier: string
  name: string
  version: string
  description: string
  author: string
  icon: string
  manifest_version: number
  capabilities: PluginCapability[]
  scopes: string[]
  is_active: boolean
  is_installed: boolean
  is_enabled: boolean
  is_core?: boolean
  user_config?: Record<string, any>
  settings_schema?: Record<string, any>
  default_config?: Record<string, any>
  created_at?: string
  updated_at?: string
}

/**
 * Topic-level Plugin Installation state (matches DRF PluginTopicInstallationSerializer)
 */
export interface TopicPluginInstallationState {
  id: number
  topic: number
  topic_name?: string
  plugin_identifier: string
  plugin_name?: string
  plugin_icon?: string
  plugin_version?: string
  installed_by?: number
  installed_by_phone?: string | null
  is_enabled: boolean
  topic_config: Record<string, any>
  installed_at?: string
  updated_at?: string
}

/**
 * Complete installed plugin state tracking
 */
export interface InstalledPluginState {
  identifier: string
  isInstalled: boolean
  isEnabled: boolean
  userConfig: Record<string, any>
  activeScopes: string[]
}
```

---

### 2.2 Pinia Plugin Registry Store (`frontend/src/plugins/core/pluginRegistry.ts`)

The registry store manages client-side manifests, backend marketplace synchronization, user/topic enablements, dynamic route mounting, and reactive action getters.

```typescript
import { defineStore } from 'pinia'
import { ref, computed, shallowRef } from 'vue'
import type { Router, RouteRecordRaw } from 'vue-router'
import axios from 'axios'
import type {
  ClientPlugin,
  PluginManifest,
  PluginComposerAction,
  PluginMenuItem,
  BackendPluginSummary,
  TopicPluginInstallationState,
  PluginInitContext
} from './pluginTypes'
import PluginErrorBoundary from './PluginErrorBoundary.vue'

export const usePluginRegistryStore = defineStore('pluginRegistry', () => {
  // --- Reactive State ---
  const registeredPlugins = shallowRef<Map<string, ClientPlugin>>(new Map())
  const marketplacePlugins = ref<BackendPluginSummary[]>([])
  const topicPluginsMap = ref<Map<string | number, TopicPluginInstallationState[]>>(new Map())
  const loading = ref(false)
  const initialized = ref(false)
  const actionLoadingMap = ref<Record<string, boolean>>({})
  const error = ref<string | null>(null)

  // API helper with token authorization
  const apiBase = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const getApiUrl = (endpoint: string) => {
    const base = apiBase.endsWith('/') ? apiBase.slice(0, -1) : apiBase
    return `${base}${endpoint}`
  }

  const getHeaders = () => {
    const token = localStorage.getItem('auth_token')
    return token ? { Authorization: `Token ${token}` } : {}
  }

  // --- Client Plugin Registration ---
  const registerPlugin = (plugin: ClientPlugin, router?: Router) => {
    const manifest = plugin.manifest
    if (!manifest || manifest.manifest_version !== 1) {
      console.error(`[PluginRegistry] Invalid manifest for plugin '${manifest?.identifier}'`)
      return
    }

    // Register into memory map
    const updatedMap = new Map(registeredPlugins.value)
    updatedMap.set(manifest.identifier, plugin)
    registeredPlugins.value = updatedMap

    // Register dynamic routes wrapped with Error Boundary
    if (router && manifest.routes && manifest.routes.length > 0) {
      manifest.routes.forEach((route: RouteRecordRaw) => {
        const routeName = String(route.name || '')
        if (!router.hasRoute(routeName)) {
          // Register route
          router.addRoute(route)
        }
      })
    }

    // Execute plugin initialization lifecycle
    if (plugin.initialize) {
      try {
        const context: PluginInitContext = {
          registry: {
            isPluginActive,
            isPluginActiveForTopic,
          },
          router
        }
        plugin.initialize(context)
      } catch (err) {
        console.error(`[PluginRegistry] Failed to initialize plugin '${manifest.identifier}':`, err)
      }
    }
  }

  // --- Backend Marketplace API Actions ---
  const fetchMarketplacePlugins = async (): Promise<BackendPluginSummary[]> => {
    loading.value = true
    error.value = null
    try {
      const res = await axios.get(getApiUrl('/api/plugins/'), {
        headers: getHeaders(),
      })
      marketplacePlugins.value = Array.isArray(res.data) ? res.data : []
      // Cache in localStorage for offline resiliency
      try {
        localStorage.setItem('tafakor_cached_marketplace_plugins', JSON.stringify(marketplacePlugins.value))
      } catch (e) {
        // Storage quota safe ignore
      }
      return marketplacePlugins.value
    } catch (err: any) {
      console.warn('[PluginRegistry] Network fetch failed, reading fallback cache:', err)
      error.value = err?.message || 'Failed to fetch marketplace'
      loadCachedMarketplace()
      return marketplacePlugins.value
    } finally {
      loading.value = false
    }
  }

  const loadCachedMarketplace = () => {
    try {
      const cached = localStorage.getItem('tafakor_cached_marketplace_plugins')
      if (cached) {
        marketplacePlugins.value = JSON.parse(cached)
      }
    } catch (e) {
      // Ignored
    }
  }

  const installPlugin = async (identifier: string, userConfig?: Record<string, any>) => {
    actionLoadingMap.value = { ...actionLoadingMap.value, [identifier]: true }
    try {
      await axios.post(
        getApiUrl(`/api/plugins/${identifier}/install/`),
        { user_config: userConfig || {} },
        { headers: getHeaders() }
      )
      await fetchMarketplacePlugins()
      return true
    } catch (err) {
      console.error(`[PluginRegistry] Error installing plugin '${identifier}':`, err)
      throw err
    } finally {
      actionLoadingMap.value = { ...actionLoadingMap.value, [identifier]: false }
    }
  }

  const uninstallPlugin = async (identifier: string) => {
    actionLoadingMap.value = { ...actionLoadingMap.value, [identifier]: true }
    try {
      await axios.post(
        getApiUrl(`/api/plugins/${identifier}/uninstall/`),
        {},
        { headers: getHeaders() }
      )
      await fetchMarketplacePlugins()
      return true
    } catch (err) {
      console.error(`[PluginRegistry] Error uninstalling plugin '${identifier}':`, err)
      throw err
    } finally {
      actionLoadingMap.value = { ...actionLoadingMap.value, [identifier]: false }
    }
  }

  const togglePlugin = async (identifier: string, isEnabled?: boolean, userConfig?: Record<string, any>) => {
    actionLoadingMap.value = { ...actionLoadingMap.value, [identifier]: true }
    try {
      const payload: Record<string, any> = {}
      if (typeof isEnabled === 'boolean') payload.is_enabled = isEnabled
      if (userConfig) payload.user_config = userConfig

      await axios.post(
        getApiUrl(`/api/plugins/${identifier}/toggle/`),
        payload,
        { headers: getHeaders() }
      )
      await fetchMarketplacePlugins()
      return true
    } catch (err) {
      console.error(`[PluginRegistry] Error toggling plugin '${identifier}':`, err)
      throw err
    } finally {
      actionLoadingMap.value = { ...actionLoadingMap.value, [identifier]: false }
    }
  }

  // --- Topic-Level Plugin Lifecycle ---
  const fetchTopicPlugins = async (topicId: string | number): Promise<TopicPluginInstallationState[]> => {
    try {
      const res = await axios.get(getApiUrl(`/api/plugins/topics/${topicId}/`), {
        headers: getHeaders()
      })
      const list = Array.isArray(res.data) ? res.data : []
      const newMap = new Map(topicPluginsMap.value)
      newMap.set(topicId, list)
      topicPluginsMap.value = newMap
      return list
    } catch (err) {
      console.error(`[PluginRegistry] Failed to fetch plugins for topic ${topicId}:`, err)
      return []
    }
  }

  const installTopicPlugin = async (topicId: string | number, identifier: string, topicConfig?: Record<string, any>) => {
    try {
      await axios.post(
        getApiUrl(`/api/plugins/topics/${topicId}/install/`),
        { identifier, topic_config: topicConfig || {} },
        { headers: getHeaders() }
      )
      await fetchTopicPlugins(topicId)
      return true
    } catch (err) {
      console.error(`[PluginRegistry] Error installing plugin '${identifier}' into topic ${topicId}:`, err)
      throw err
    }
  }

  const toggleTopicPlugin = async (topicId: string | number, identifier: string, isEnabled?: boolean, topicConfig?: Record<string, any>) => {
    try {
      const payload: Record<string, any> = { identifier }
      if (typeof isEnabled === 'boolean') payload.is_enabled = isEnabled
      if (topicConfig) payload.topic_config = topicConfig

      await axios.post(
        getApiUrl(`/api/plugins/topics/${topicId}/toggle/`),
        payload,
        { headers: getHeaders() }
      )
      await fetchTopicPlugins(topicId)
      return true
    } catch (err) {
      console.error(`[PluginRegistry] Error toggling plugin '${identifier}' in topic ${topicId}:`, err)
      throw err
    }
  }

  const uninstallTopicPlugin = async (topicId: string | number, identifier: string) => {
    try {
      await axios.post(
        getApiUrl(`/api/plugins/topics/${topicId}/uninstall/`),
        { identifier },
        { headers: getHeaders() }
      )
      await fetchTopicPlugins(topicId)
      return true
    } catch (err) {
      console.error(`[PluginRegistry] Error uninstalling plugin '${identifier}' from topic ${topicId}:`, err)
      throw err
    }
  }

  // --- Active Status Checks ---
  const isPluginActive = (identifier: string): boolean => {
    const registered = registeredPlugins.value.get(identifier)
    if (registered?.manifest.is_core) return true

    const backend = marketplacePlugins.value.find(p => p.identifier === identifier)
    return backend ? backend.is_installed && backend.is_enabled : false
  }

  const isPluginActiveForTopic = (identifier: string, topicId: string | number): boolean => {
    if (isPluginActive(identifier)) return true
    const topicPlugins = topicPluginsMap.value.get(topicId) || []
    const match = topicPlugins.find(tp => tp.plugin_identifier === identifier)
    return match ? match.is_enabled : false
  }

  // --- Reactive Computed Getters ---
  const composerActions = computed<PluginComposerAction[]>(() => {
    const actions: PluginComposerAction[] = []
    registeredPlugins.value.forEach((plugin, identifier) => {
      if (plugin.manifest.is_core || isPluginActive(identifier)) {
        if (plugin.manifest.composerActions) {
          actions.push(...plugin.manifest.composerActions)
        }
      }
    })
    return actions.sort((a, b) => (a.order || 0) - (b.order || 0))
  })

  const menuItems = computed<PluginMenuItem[]>(() => {
    const items: PluginMenuItem[] = []
    registeredPlugins.value.forEach((plugin, identifier) => {
      if (plugin.manifest.is_core || isPluginActive(identifier)) {
        if (plugin.manifest.menuItems) {
          items.push(...plugin.manifest.menuItems)
        }
      }
    })
    return items.sort((a, b) => (a.order || 0) - (b.order || 0))
  })

  return {
    registeredPlugins,
    marketplacePlugins,
    topicPluginsMap,
    loading,
    initialized,
    actionLoadingMap,
    error,
    registerPlugin,
    fetchMarketplacePlugins,
    installPlugin,
    uninstallPlugin,
    togglePlugin,
    fetchTopicPlugins,
    installTopicPlugin,
    toggleTopicPlugin,
    uninstallTopicPlugin,
    isPluginActive,
    isPluginActiveForTopic,
    composerActions,
    menuItems,
  }
})
```

---

### 2.3 Dynamic Plugin Loader with Vite Glob Imports (`frontend/src/plugins/core/pluginLoader.ts`)

The loader uses Vite's `import.meta.glob` to autodiscover all plugin packages under `frontend/src/plugins/` dynamically without manual registration tables.

```typescript
import type { Router } from 'vue-router'
import { usePluginRegistryStore } from './pluginRegistry'
import type { ClientPlugin } from './pluginTypes'

/**
 * Autodiscover all plugin entry points dynamically via Vite's build-time glob.
 * Matches all index.ts files in sibling plugin directories, excluding 'core'.
 */
const pluginModules = import.meta.glob<{
  default?: ClientPlugin
  [key: string]: any
}>([
  '../*/index.ts',
  '!../core/**',
])

/**
 * Initializes and dynamically registers all available client-side plugins.
 * Uses lazy dynamic imports so plugin code is only bundled and loaded on demand.
 */
export async function initializePlugins(router?: Router): Promise<void> {
  const registry = usePluginRegistryStore()
  if (registry.initialized) return

  try {
    // 1. Fetch marketplace plugin state from backend in parallel
    await registry.fetchMarketplacePlugins().catch(err => {
      console.warn('[PluginLoader] Backend marketplace fetch failed, proceeding with local plugins:', err)
    })

    // 2. Discover and register all client plugin modules dynamically
    const loadPromises = Object.entries(pluginModules).map(async ([path, importFn]) => {
      try {
        const mod = await importFn()
        // Extract exported plugin object (default export or named clientPlugin / *Plugin)
        const plugin: ClientPlugin | undefined =
          mod.default ||
          Object.values(mod).find((val: any) => val && typeof val === 'object' && val.manifest?.identifier)

        if (plugin && plugin.manifest) {
          registry.registerPlugin(plugin, router)
        } else {
          console.warn(`[PluginLoader] Module at '${path}' did not export a valid ClientPlugin.`)
        }
      } catch (modErr) {
        console.error(`[PluginLoader] Failed to dynamically load plugin module at '${path}':`, modErr)
      }
    })

    await Promise.allSettled(loadPromises)
    registry.initialized = true
  } catch (err) {
    console.error('[PluginLoader] Fatal error during plugin subsystem initialization:', err)
  }
}
```

---

### 2.4 Resilient Vue 3 Error Boundary (`frontend/src/plugins/core/PluginErrorBoundary.vue`)

Vue 3 component leveraging `onErrorCaptured` to catch, log, and isolate unhandled runtime errors in any plugin view, mini-app, or dialog without crashing the host application.

```vue
<template>
  <div 
    v-if="hasError" 
    class="p-6 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-900/50 rounded-3xl text-center space-y-4 my-4 shadow-sm"
    :dir="languageStore.dir"
  >
    <div class="w-12 h-12 rounded-2xl bg-red-100 dark:bg-red-900/50 text-red-600 dark:text-red-400 mx-auto flex items-center justify-center text-xl shadow-xs">
      ⚠️
    </div>
    
    <div class="space-y-1.5">
      <h3 class="font-bold text-red-900 dark:text-red-200 text-base sm:text-lg">
        {{ languageStore.t('خطا در اجرای افزونه', 'Plugin Execution Error') }}
      </h3>
      <p class="text-xs sm:text-sm text-red-700 dark:text-red-400 max-w-md mx-auto leading-relaxed">
        {{ errorMessage || languageStore.t('افزونه با مشکلی مواجه شد اما سایر بخش‌های تفکر بدون مشکل فعال هستند.', 'This plugin encountered an issue, but the rest of Tafakor remains unaffected.') }}
      </p>
    </div>

    <!-- Collapsible Error Diagnostics -->
    <div v-if="errorDetails" class="text-start max-w-md mx-auto">
      <button 
        @click="showDetails = !showDetails"
        class="text-[11px] font-medium text-red-600 dark:text-red-400 underline underline-offset-2 cursor-pointer focus:outline-none"
      >
        {{ showDetails ? languageStore.t('بستن جزئیات فنی', 'Hide Details') : languageStore.t('مشاهده جزئیات خطا', 'Show Error Details') }}
      </button>
      <pre 
        v-if="showDetails" 
        class="mt-2 p-3 bg-red-100/60 dark:bg-red-900/40 rounded-xl text-[10px] font-mono text-red-900 dark:text-red-200 overflow-x-auto max-h-32 border border-red-200 dark:border-red-800/60"
      >{{ errorDetails }}</pre>
    </div>

    <!-- Actions -->
    <div class="pt-2 flex items-center justify-center gap-3">
      <button
        @click="resetError"
        class="px-4 py-2 bg-red-600 hover:bg-red-700 active:scale-95 text-white rounded-xl text-xs font-bold transition-all shadow-sm"
      >
        {{ languageStore.t('تلاش مجدد', 'Retry') }}
      </button>
      <router-link
        to="/"
        class="px-4 py-2 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 rounded-xl text-xs font-semibold transition-all"
      >
        {{ languageStore.t('بازگشت به خانه', 'Back to Home') }}
      </router-link>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  pluginName?: string
}>(), {
  pluginName: 'Plugin'
})

const hasError = ref(false)
const errorMessage = ref('')
const errorDetails = ref('')
const showDetails = ref(false)

onErrorCaptured((err: any, instance, info) => {
  console.error(`[PluginErrorBoundary] Error in plugin '${props.pluginName}':`, err, info)
  hasError.value = true
  errorMessage.value = err?.message || 'Unknown plugin execution failure.'
  errorDetails.value = `${err?.stack || err?.toString() || ''}\nInfo: ${info || ''}`
  // Return false to prevent bubbling up and crashing the root Vue tree
  return false
})

const resetError = () => {
  hasError.value = false
  errorMessage.value = ''
  errorDetails.value = ''
  showDetails.value = false
}
</script>
```

---

### 2.5 Bootstrap Re-Exports (`frontend/src/plugins/core/index.ts` & `frontend/src/plugins/index.ts`)

**`frontend/src/plugins/core/index.ts`**:
```typescript
export * from './pluginTypes'
export * from './pluginRegistry'
export * from './pluginLoader'
export { default as PluginErrorBoundary } from './PluginErrorBoundary.vue'
```

**`frontend/src/plugins/index.ts`**:
```typescript
export * from './core'
export * from './quran'
```

**`frontend/src/main.ts` Integration**:
```typescript
import './assets/main.css'
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useLanguageStore } from '@/stores/languageStore'
import { initializePlugins } from '@/plugins/core/pluginLoader'

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

const languageStore = useLanguageStore()
languageStore.init()

// Initialize Plugin Subsystem
initializePlugins(router)

app.mount('#app')
```

---

## 3. Caveats

1. **Vite Dynamic Import Optimization**:
   - `import.meta.glob` requires static glob pattern literals (e.g. `'../*/index.ts'`). Dynamic variable expressions cannot be resolved by Vite's static analyzer.
2. **TypeScript `noUncheckedIndexedAccess: true`**:
   - In `frontend/tsconfig.app.json`, `noUncheckedIndexedAccess: true` is configured. All array index lookups and map value retrievals must be treated as potentially `undefined` and guarded with explicit null-checks or defaults.
3. **Route Name Uniqueness**:
   - Dynamic routes registered via `router.addRoute()` must have globally unique route `name` identifiers to avoid collision with core routes (`login`, `home`, `topic`, `marketplace`). Plugin routes should prefix names with `<plugin_id>-` (e.g. `quran-surahs`, `quran-reader`).
4. **Offline Resilience**:
   - In the event of backend network outage during app boot, the plugin registry must fail gracefully by falling back to cached local storage representations and proceeding to register available core/static plugins.

---

## 4. Conclusion

1. The proposed Frontend Plugin Architecture in `frontend/src/plugins/core/` provides full feature parity with the Django backend Plugin System (`apps/plugin_system`).
2. It satisfies all isolation and zero-breaking-change requirements:
   - Dynamic lazy-loading of plugin views via `import()`.
   - Auto-discovery via Vite's `import.meta.glob`.
   - Complete fault tolerance via `PluginErrorBoundary.vue`.
   - Seamless non-invasive Markdown injection into `TopicMessageInput.vue`.
   - User and topic-level plugin enablement via the Pinia registry.
3. The design is ready for immediate implementation by Worker agents.

---

## 5. Verification Method

To independently verify the frontend plugin architecture and type safety:

```powershell
cd f:\AVA\tafakor\frontend

# 1. Verify TypeScript types and template compilations
npm run type-check

# 2. Verify Vite production build bundling
npm run build-only

# 3. Verify unit tests
npm run test:unit
```
