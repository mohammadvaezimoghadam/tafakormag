<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  BookOpenIcon, 
  LayersIcon, 
  CheckIcon, 
  StarIcon, 
  ArrowUpRightIcon, 
  ShieldCheckIcon,
  BellIcon,
  DownloadIcon,
  RefreshCwIcon,
  Trash2Icon,
  XIcon
} from '@lucide/vue'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose
} from '@/components/ui/dialog'
import { useLanguageStore } from '@/stores/languageStore'
import type { MarketplaceApp } from '@/types/marketplace'

const languageStore = useLanguageStore()

export interface MarketplaceAppModalProps {
  open: boolean
  app: MarketplaceApp | null
  isInstalled?: boolean
  isInstalling?: boolean
}

const props = withDefaults(defineProps<MarketplaceAppModalProps>(), {
  open: false,
  app: null,
  isInstalled: false,
  isInstalling: false
})

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'open-app', app: MarketplaceApp): void
  (e: 'install', app: MarketplaceApp): void
  (e: 'uninstall', app: MarketplaceApp): void
  (e: 'notify', app: MarketplaceApp): void
}>()

const isNotificationSubscribed = ref(false)

const appTitle = computed(() => props.app?.title || '')
const appCategory = computed(() => props.app?.category || '')
const appDeveloper = computed(() => props.app?.developer || props.app?.author || languageStore.t('تیم نرم‌افزاری تفکر', 'Tafakor Team'))
const appIsComingSoon = computed(() => props.app?.isComingSoon ?? false)
const appIsInstalled = computed(() => props.isInstalled || props.app?.isInstalled || false)
const appVersion = computed(() => languageStore.n(props.app?.version || '1.0.0'))
const appRating = computed(() => props.app?.rating ? languageStore.n(props.app.rating.toFixed(1)) : languageStore.n('4.9'))
const appDownloadsCount = computed(() => {
  const count = props.app?.downloadsCount || 2450
  return languageStore.n(count.toLocaleString('fa-IR'))
})

const fallbackLetter = computed(() => {
  const t = appTitle.value.trim()
  return t ? t.charAt(0).toUpperCase() : 'A'
})

const handleOpenApp = () => {
  if (!props.app) return
  emit('open-app', props.app)
}

const handleInstall = () => {
  if (!props.app) return
  emit('install', props.app)
}

const handleToggleNotification = () => {
  if (!props.app) return
  isNotificationSubscribed.value = !isNotificationSubscribed.value
  emit('notify', props.app)
}
</script>

<template>
  <Dialog :open="open" @update:open="(val: boolean) => emit('update:open', val)">
    <DialogContent 
      :show-close-button="false"
      class="w-[94vw] max-w-[420px] max-h-[90dvh] overflow-hidden rounded-3xl p-0 border border-border/80 bg-card text-card-foreground shadow-2xl flex flex-col text-start font-sans select-none" 
      :dir="languageStore.dir"
    >
      <!-- Minimalist Dialog Header (Aligned with CreateDonationDialog) -->
      <DialogHeader v-if="app" class="px-4 py-3.5 border-b border-border/40 shrink-0 bg-muted/20 flex flex-col gap-0">
        <div class="flex items-center justify-between gap-2.5">
          <!-- Icon & App Details Column -->
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            <!-- App Squircle Icon -->
            <div 
              :class="[
                'size-10 sm:size-11 rounded-xl flex items-center justify-center shadow-xs border shrink-0 overflow-hidden',
                !appIsComingSoon 
                  ? 'bg-primary/10 border-primary/20 text-primary'
                  : 'bg-muted/40 border-border/70 text-muted-foreground'
              ]"
            >
              <!-- Image Icon -->
              <Avatar v-if="app.iconUrl" class="size-full rounded-xl">
                <AvatarImage :src="app.iconUrl" :alt="appTitle" class="size-full object-cover" />
                <AvatarFallback class="size-full bg-primary/10 text-primary font-bold text-xs">
                  {{ fallbackLetter }}
                </AvatarFallback>
              </Avatar>

              <!-- Vector Icon -->
              <component 
                v-else 
                :is="app.icon || (app.id === 'quran' ? BookOpenIcon : LayersIcon)" 
                class="size-5 shrink-0" 
              />
            </div>

            <!-- Title & Category Info -->
            <div class="flex flex-col min-w-0 text-start">
              <DialogTitle class="text-sm font-bold text-foreground flex items-center gap-1 truncate">
                <span class="truncate">{{ appTitle }}</span>
                <ShieldCheckIcon v-if="!appIsComingSoon" class="size-3.5 text-primary shrink-0" />
              </DialogTitle>

              <DialogDescription class="text-xs text-muted-foreground truncate">
                {{ appCategory }} • {{ appDeveloper }}
              </DialogDescription>
            </div>
          </div>

          <!-- Header Actions: Badge & Close Button -->
          <div class="flex items-center gap-1.5 shrink-0">
            <Badge 
              variant="outline" 
              :class="[
                'text-[10px] font-bold px-2 py-0.5 rounded-full border shadow-2xs leading-tight',
                appIsComingSoon 
                  ? 'border-border/80 bg-background/80 text-muted-foreground'
                  : 'border-emerald-500/40 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
              ]"
            >
              <CheckIcon v-if="appIsInstalled && !appIsComingSoon" class="size-2.5 me-0.5 shrink-0 inline-block text-emerald-500" />
              <span>{{ appIsComingSoon ? languageStore.t('به‌زودی', 'Coming Soon') : (appIsInstalled ? languageStore.t('نصب‌شده', 'Installed') : languageStore.t('رسمی', 'Official')) }}</span>
            </Badge>

            <DialogClose as-child>
              <Button 
                variant="ghost" 
                size="icon" 
                class="size-8 rounded-full text-muted-foreground hover:text-foreground hover:bg-muted/80 cursor-pointer"
                :title="languageStore.t('بستن', 'Close')"
              >
                <XIcon class="size-4" />
              </Button>
            </DialogClose>
          </div>
        </div>
      </DialogHeader>

      <!-- Scrollable Body (Mobile Optimized Spacing) -->
      <div v-if="app" class="p-4 flex-1 overflow-y-auto max-h-[calc(90dvh-130px)] flex flex-col gap-4 text-start">
        
        <!-- Metrics / Stats Bar (For Active / Released Apps) -->
        <div 
          v-if="!appIsComingSoon" 
          class="grid grid-cols-3 gap-2 p-2.5 rounded-2xl bg-muted/20 border border-border/50 text-center"
        >
          <!-- Metric 1: Rating -->
          <div class="flex flex-col items-center justify-center gap-0.5 border-e border-border/40 px-1">
            <div class="flex items-center gap-1 text-xs font-bold text-foreground">
              <StarIcon class="size-3.5 text-amber-500 fill-amber-500 shrink-0" />
              <span>{{ appRating }}</span>
            </div>
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('امتیاز کاربران', 'Rating') }}</span>
          </div>

          <!-- Metric 2: Installs -->
          <div class="flex flex-col items-center justify-center gap-0.5 border-e border-border/40 px-1">
            <span class="text-xs font-bold text-foreground font-sans">{{ appDownloadsCount }}</span>
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('نصب فعال', 'Installs') }}</span>
          </div>

          <!-- Metric 3: Version -->
          <div class="flex flex-col items-center justify-center gap-0.5 px-1">
            <span class="text-xs font-bold text-foreground font-sans">{{ appVersion }}</span>
            <span class="text-[10px] text-muted-foreground">{{ languageStore.t('نسخه', 'Version') }}</span>
          </div>
        </div>

        <!-- Section 1: About Extension -->
        <div class="flex flex-col gap-1.5">
          <span class="text-xs font-bold text-foreground block">
            {{ languageStore.t('درباره افزونه', 'About Extension') }}
          </span>
          <p class="text-xs text-muted-foreground leading-relaxed text-start">
            {{ app.description }}
          </p>
        </div>

        <!-- Section 2: Key Capabilities & Features -->
        <div class="flex flex-col gap-2">
          <span class="text-xs font-bold text-foreground block">
            {{ languageStore.t('قابلیت‌ها و دسترسی‌ها', 'Capabilities & Features') }}
          </span>

          <div class="flex flex-wrap gap-1.5">
            <template v-if="app.id === 'quran'">
              <span class="px-2.5 py-1.5 bg-muted/30 border border-border/60 rounded-xl text-xs text-foreground font-medium flex items-center gap-1.5 shadow-2xs">
                <span>📖</span>
                <span>درج آیه با دستور <code class="font-mono text-primary font-bold">/quran</code></span>
              </span>
              <span class="px-2.5 py-1.5 bg-muted/30 border border-border/60 rounded-xl text-xs text-foreground font-medium flex items-center gap-1.5 shadow-2xs">
                <span>🔊</span>
                <span>پخش صوتی با صدای قاریان</span>
              </span>
              <span class="px-2.5 py-1.5 bg-muted/30 border border-border/60 rounded-xl text-xs text-foreground font-medium flex items-center gap-1.5 shadow-2xs">
                <span>🔍</span>
                <span>جستجوی دقیق بدون اعراب</span>
              </span>
              <span class="px-2.5 py-1.5 bg-muted/30 border border-border/60 rounded-xl text-xs text-foreground font-medium flex items-center gap-1.5 shadow-2xs">
                <span>🇮🇷</span>
                <span>ترجمه انصاریان و مکارم</span>
              </span>
            </template>
            <template v-else>
              <span class="px-2.5 py-1.5 bg-muted/20 border border-border/40 rounded-xl text-xs text-muted-foreground flex items-center gap-1.5">
                <span>✨</span>
                <span>ادغام با ویرایشگر پیام</span>
              </span>
              <span class="px-2.5 py-1.5 bg-muted/20 border border-border/40 rounded-xl text-xs text-muted-foreground flex items-center gap-1.5">
                <span>🔒</span>
                <span>حفظ کامل حریم خصوصی</span>
              </span>
            </template>
          </div>
        </div>

      </div>

      <!-- Footer Actions (Aligned with CreateDonationDialog) -->
      <DialogFooter class="p-4 border-t border-border/40 shrink-0 bg-muted/20 flex flex-row items-center gap-2" :dir="languageStore.dir">
        <!-- A) Active & Installed Plugin Actions -->
        <template v-if="!appIsComingSoon">
          <!-- Primary: Install / Uninstall Button -->
          <Button
            type="button"
            @click="handleInstall"
            :disabled="isInstalling"
            :variant="appIsInstalled ? 'outline' : 'default'"
            :class="[
              'flex-1 rounded-xl text-xs font-bold h-9 shadow-xs active:scale-95 transition-all cursor-pointer gap-1.5 justify-center',
              appIsInstalled ? 'border border-destructive/30 text-destructive hover:bg-destructive/10 dark:hover:bg-destructive/20' : ''
            ]"
          >
            <RefreshCwIcon v-if="isInstalling" class="size-3.5 animate-spin shrink-0" />
            <Trash2Icon v-else-if="appIsInstalled" class="size-3.5 shrink-0" />
            <DownloadIcon v-else class="size-3.5 shrink-0" />
            <span>{{ isInstalling ? languageStore.t('در حال نصب...', 'Installing...') : (appIsInstalled ? languageStore.t('پاک کردن', 'Uninstall') : languageStore.t('نصب افزونه', 'Install Plugin')) }}</span>
          </Button>

          <!-- Bordered Button: Open Mini-App with Soon Badge -->
          <Button
            type="button"
            @click="handleOpenApp"
            variant="outline"
            class="flex-1 rounded-xl text-xs font-bold h-9 border border-border/80 hover:bg-muted text-foreground shadow-xs active:scale-95 transition-all cursor-pointer gap-1.5 justify-center"
          >
            <ArrowUpRightIcon class="size-3.5 text-primary shrink-0" />
            <span>{{ languageStore.t('باز کردن مینی‌اپ', 'Open Mini-App') }}</span>
            <span class="text-[9px] font-bold px-1.5 py-0.5 bg-muted/60 dark:bg-muted/40 text-muted-foreground border border-border/60 rounded-md ms-0.5">
              {{ languageStore.t('به‌زودی', 'Soon') }}
            </span>
          </Button>
        </template>

        <!-- B) Coming Soon Action -->
        <template v-else>
          <Button
            type="button"
            @click="handleToggleNotification"
            :variant="isNotificationSubscribed ? 'secondary' : 'default'"
            class="w-full rounded-xl text-xs font-bold h-9 shadow-xs active:scale-95 transition-all cursor-pointer gap-1.5"
          >
            <CheckIcon v-if="isNotificationSubscribed" class="size-3.5 text-emerald-500 shrink-0" />
            <BellIcon v-else class="size-3.5 shrink-0" />
            <span>{{ isNotificationSubscribed ? languageStore.t('اطلاع‌رسانی برای شما فعال شد', 'Subscribed to Release Alerts') : languageStore.t('اطلاع‌رسانی هنگام انتشار', 'Notify Me on Release') }}</span>
          </Button>
        </template>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
