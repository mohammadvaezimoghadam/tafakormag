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
 * Backward compatibility alias for ComposerActionContext
 */
export type ComposerActionContext = PluginComposerActionContext

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
 * Backward compatibility alias for ComposerAction
 */
export type ComposerAction = PluginComposerAction

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
  pluginId?: string
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
  manifest_version: 1 | number
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
  routes?: PluginRouteConfig[] | RouteRecordRaw[]
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
  manifest_version?: number
  capabilities: (PluginCapability | string)[]
  scopes?: string[]
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
