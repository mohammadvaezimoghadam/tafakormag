import { defineStore } from 'pinia'
import { ref, computed, shallowRef } from 'vue'
import type { Router, RouteRecordRaw } from 'vue-router'
import axios from 'axios'
import type {
  ClientPlugin,
  PluginComposerAction,
  PluginMenuItem,
  BackendPluginSummary,
  TopicPluginInstallationState,
  PluginInitContext
} from './pluginTypes'

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

    // Register dynamic routes
    if (router && manifest.routes && manifest.routes.length > 0) {
      manifest.routes.forEach((route: RouteRecordRaw) => {
        const routeName = String(route.name || '')
        if (!routeName || !router.hasRoute(routeName)) {
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
