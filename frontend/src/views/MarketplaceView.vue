<template>
  <div class="max-w-5xl mx-auto px-4 py-8 space-y-8">
    
    <!-- Hero Banner -->
    <div class="p-8 bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 rounded-3xl text-white shadow-2xl space-y-3">
      <div class="inline-flex items-center gap-2 px-3 py-1 bg-white/20 backdrop-blur-md rounded-full text-xs font-semibold">
        <span>🧩</span>
        <span>مرکز افزونه‌ها و مینی‌اپ‌ها (Tafakor Marketplace)</span>
      </div>
      <h1 class="text-3xl sm:text-4xl font-black">مارکت‌پلیس افزونه‌های تفکر</h1>
      <p class="text-sm sm:text-base text-purple-100 max-w-2xl leading-relaxed">
        امکانات پلتفرم تفکر را با افزونه‌های رسمی و کاربردی گسترش دهید؛ بدون تغییر در هسته و با حفظ کامل حریم خصوصی.
      </p>
    </div>

    <!-- Plugins Section -->
    <div class="space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-lg font-bold text-zinc-900 dark:text-zinc-100">افزونه‌های موجود</h2>
        <span class="text-xs text-zinc-500">{{ plugins.length }} افزونه ثبت شده</span>
      </div>

      <div v-if="loading" class="text-center py-16 text-zinc-400 text-sm">
        در حال دریافت اطلاعات افزونه‌ها...
      </div>

      <div v-else-if="plugins.length === 0" class="text-center py-16 text-zinc-400 text-sm">
        در حال حاضر افزونه‌ای ثبت نشده است.
      </div>

      <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div
          v-for="p in plugins"
          :key="p.identifier"
          class="p-6 bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-3xl space-y-5 shadow-sm hover:shadow-lg transition-all flex flex-col justify-between"
        >
          <div class="space-y-3">
            <div class="flex items-start justify-between gap-3">
              <div class="flex items-center gap-3">
                <div class="w-12 h-12 rounded-2xl bg-emerald-50 dark:bg-emerald-950/40 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-2xl font-bold">
                  {{ p.identifier === 'quran' ? '📖' : '🧩' }}
                </div>
                <div>
                  <h3 class="font-bold text-zinc-900 dark:text-zinc-100 text-base flex items-center gap-2">
                    {{ p.name }}
                    <span v-if="p.is_core" class="px-2 py-0.5 bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 rounded-full text-[10px] font-semibold">
                      رسمی
                    </span>
                  </h3>
                  <p class="text-xs text-zinc-400">نسخه {{ p.version }} • توسعه‌دهنده: {{ p.author || 'تیم تفکر' }}</p>
                </div>
              </div>

              <!-- Status badge -->
              <span
                :class="[
                  'px-2.5 py-1 rounded-full text-xs font-semibold',
                  p.is_installed && p.is_enabled
                    ? 'bg-emerald-100 dark:bg-emerald-950/60 text-emerald-700 dark:text-emerald-300'
                    : p.is_installed
                    ? 'bg-amber-100 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300'
                    : 'bg-zinc-100 dark:bg-zinc-800 text-zinc-500'
                ]"
              >
                {{ p.is_installed && p.is_enabled ? 'فعال' : p.is_installed ? 'غیرفعال' : 'نصب نشده' }}
              </span>
            </div>

            <p class="text-xs sm:text-sm text-zinc-600 dark:text-zinc-400 leading-relaxed">
              {{ p.description }}
            </p>

            <!-- Capabilities pills -->
            <div class="flex flex-wrap gap-1.5 pt-1">
              <span
                v-for="cap in p.capabilities"
                :key="cap"
                class="px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded-lg text-[11px]"
              >
                {{ getCapabilityLabel(cap) }}
              </span>
            </div>
          </div>

          <!-- Actions -->
          <div class="pt-4 border-t border-zinc-100 dark:border-zinc-800/80 flex items-center justify-between gap-3">
            <div>
              <router-link
                v-if="p.identifier === 'quran'"
                to="/apps/quran"
                class="px-3 py-2 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/60 rounded-xl text-xs font-bold transition-colors inline-flex items-center gap-1"
              >
                <span>باز کردن مینی‌اپ</span>
                <span>↗</span>
              </router-link>
            </div>

            <div class="flex items-center gap-2">
              <template v-if="p.is_installed">
                <button
                  @click="togglePlugin(p.identifier)"
                  class="px-3.5 py-2 bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-200 rounded-xl text-xs font-semibold transition-colors"
                >
                  {{ p.is_enabled ? 'غیرفعال‌سازی' : 'فعال‌سازی' }}
                </button>
                <button
                  @click="uninstallPlugin(p.identifier)"
                  class="px-3.5 py-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-xl text-xs font-semibold transition-colors"
                >
                  حذف
                </button>
              </template>
              <template v-else>
                <button
                  @click="installPlugin(p.identifier)"
                  class="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold shadow-md shadow-indigo-600/20 transition-all"
                >
                  نصب و فعال‌سازی
                </button>
              </template>
            </div>
          </div>

        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePluginRegistryStore } from '../plugins/core/pluginRegistry'

const registry = usePluginRegistryStore()

onMounted(async () => {
  await registry.fetchMarketplacePlugins()
})

const loading = computed(() => registry.loading)
const plugins = computed(() => registry.marketplacePlugins)

const installPlugin = async (identifier: string) => {
  await registry.installPlugin(identifier)
}

const uninstallPlugin = async (identifier: string) => {
  await registry.uninstallPlugin(identifier)
}

const togglePlugin = async (identifier: string) => {
  await registry.togglePlugin(identifier)
}

const getCapabilityLabel = (cap: string) => {
  const map: Record<string, string> = {
    composer_action: 'دکمه در ویرایشگر',
    mini_app: 'مینی‌اپلیکیشن اختصاصی',
    search_provider: 'موتور جستجو',
    topic_action: 'عملیات تاپیک',
  }
  return map[cap] || cap
}
</script>
