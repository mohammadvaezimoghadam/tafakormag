import type { Router } from 'vue-router'
import { usePluginRegistryStore } from './pluginRegistry'
import type { ClientPlugin } from './pluginTypes'

/**
 * Autodiscover all plugin entry points dynamically via Vite's build-time glob.
 * Matches all index.ts files in sibling plugin directories, excluding 'core'.
 */
const pluginModules = import.meta.glob<{
  default?: ClientPlugin
  quranPlugin?: ClientPlugin
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
          mod.quranPlugin ||
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
