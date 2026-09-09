<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import PlatformHeader from './PlatformHeader.vue'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { 
  SendIcon, 
  MessageSquareIcon, 
  AlertCircleIcon, 
  SaveIcon, 
  RefreshCwIcon, 
  CheckCircle2Icon,
  ChevronRightIcon,
  SparklesIcon,
  RotateCcwIcon,
  LinkIcon
} from '@lucide/vue'
import * as api from '@/api'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = defineProps<{
  topic: {
    id: number
    title: string
    telegram_bot_active?: boolean
    telegram_post_badge?: string
    telegram_post_link_mode?: 'auto_long' | 'always' | 'disabled'
    bale_bot_active?: boolean
    bale_post_badge?: string
    bale_post_link_mode?: 'auto_long' | 'always' | 'disabled'
    telegram_connections?: any[]
    bale_connections?: any[]
    [key: string]: any
  }
  telegramConnected?: boolean
  baleConnected?: boolean
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'goToConnections'): void
  (e: 'save', data: {
    telegram_bot_active: boolean
    bale_bot_active: boolean
    telegram_connections: number[]
    bale_connections: number[]
    telegram_post_badge: string
    bale_post_badge: string
    telegram_post_link_mode: 'auto_long' | 'always' | 'disabled'
    bale_post_link_mode: 'auto_long' | 'always' | 'disabled'
  }): void
}>()

// Active Toggles
const telegramActive = ref(props.topic.telegram_bot_active || false)
const baleActive = ref(props.topic.bale_bot_active || false)

// Platform Badge Refs
const telegramPostBadge = ref(props.topic.telegram_post_badge || '')
const balePostBadge = ref(props.topic.bale_post_badge || '')

// Platform Post Link Mode Refs
const telegramPostLinkMode = ref<'auto_long' | 'always' | 'disabled'>(props.topic.telegram_post_link_mode || 'auto_long')
const balePostLinkMode = ref<'auto_long' | 'always' | 'disabled'>(props.topic.bale_post_link_mode || 'auto_long')

// Flags to track whether the user has deliberately edited the badge manually
const tgBadgeManuallyEdited = ref(!!props.topic.telegram_post_badge)
const baleBadgeManuallyEdited = ref(!!props.topic.bale_post_badge)

// Verification Connection States (Retrieved from global or profiles)
const telegramConnected = ref(props.telegramConnected || false)
const baleConnected = ref(props.baleConnected || false)

watch(() => props.telegramConnected, (newVal) => {
  telegramConnected.value = newVal || false
})

watch(() => props.baleConnected, (newVal) => {
  baleConnected.value = newVal || false
})

// Mock/Fetched Destinations (Telegram Channels / Bale Groups)
const tgDestinations = ref<any[]>([])
const baleDestinations = ref<any[]>([])

const loadingTg = ref(false)
const loadingBale = ref(false)

// Selected list of connection IDs
const selectedTgConnections = ref<number[]>([])
const selectedBaleConnections = ref<number[]>([])

const isSaving = ref(false)
const saveSuccess = ref(false)

// Auto-badge resolution helpers from registered destinations
const getAutoBadgeForTelegram = () => {
  if (tgDestinations.value.length === 0) return ''
  const selected = tgDestinations.value.find(d => selectedTgConnections.value.includes(d.id))
  return selected?.auto_badge || tgDestinations.value[0]?.auto_badge || ''
}

const getAutoBadgeForBale = () => {
  if (baleDestinations.value.length === 0) return ''
  const selected = baleDestinations.value.find(d => selectedBaleConnections.value.includes(d.id))
  return selected?.auto_badge || baleDestinations.value[0]?.auto_badge || ''
}

const loadConnectionsData = async () => {
  try {
    // 1. Fetch current profile to verify bot connection statuses
    const profileRes = await api.fetchProfile()
    if (profileRes.data) {
      telegramConnected.value = !!(profileRes.data.is_telegram_bot_connected ?? (profileRes.data.telegram_bot_token || profileRes.data.telegram_token))
      baleConnected.value = !!(profileRes.data.is_bale_bot_connected ?? (profileRes.data.bale_bot_token || profileRes.data.bale_token))
    }
  } catch (err) {
    console.error('Failed to load connections configuration from API:', err)
    telegramConnected.value = props.telegramConnected || false
    baleConnected.value = props.baleConnected || false
  }

  try {
    // 2. Fetch all channels/destinations for both if connected
    if (telegramConnected.value) {
      loadingTg.value = true
      const tgRes = await api.fetchDestinations('telegram')
      if (tgRes.data) {
        tgDestinations.value = tgRes.data
      }
      loadingTg.value = false
    }

    if (baleConnected.value) {
      loadingBale.value = true
      const baleRes = await api.fetchDestinations('bale')
      if (baleRes.data) {
        baleDestinations.value = baleRes.data
      }
      loadingBale.value = false
    }

    // Initialize selections from props connections
    if (props.topic.telegram_connections) {
      selectedTgConnections.value = props.topic.telegram_connections.map(c => c.id || c)
    }
    if (props.topic.bale_connections) {
      selectedBaleConnections.value = props.topic.bale_connections.map(c => c.id || c)
    }

    // If badges are currently blank, auto-populate from destinations
    if (!telegramPostBadge.value.trim() && !tgBadgeManuallyEdited.value) {
      const autoTg = getAutoBadgeForTelegram()
      if (autoTg) telegramPostBadge.value = autoTg
    }
    if (!balePostBadge.value.trim() && !baleBadgeManuallyEdited.value) {
      const autoBale = getAutoBadgeForBale()
      if (autoBale) balePostBadge.value = autoBale
    }

  } catch (err) {
    console.error('Failed to load destinations channels:', err)
    loadingTg.value = false
    loadingBale.value = false
  }
}

onMounted(() => {
  loadConnectionsData()
})

const toggleTgChannel = (id: number) => {
  const idx = selectedTgConnections.value.indexOf(id)
  if (idx > -1) {
    selectedTgConnections.value.splice(idx, 1)
  } else {
    selectedTgConnections.value.push(id)
    const ch = tgDestinations.value.find(d => d.id === id)
    // If badge is empty or unedited, automatically set to this channel's auto_badge
    if (ch?.auto_badge && (!telegramPostBadge.value.trim() || !tgBadgeManuallyEdited.value)) {
      telegramPostBadge.value = ch.auto_badge
    }
  }
}

const toggleBaleChannel = (id: number) => {
  const idx = selectedBaleConnections.value.indexOf(id)
  if (idx > -1) {
    selectedBaleConnections.value.splice(idx, 1)
  } else {
    selectedBaleConnections.value.push(id)
    const ch = baleDestinations.value.find(d => d.id === id)
    // If badge is empty or unedited, automatically set to this channel's auto_badge
    if (ch?.auto_badge && (!balePostBadge.value.trim() || !baleBadgeManuallyEdited.value)) {
      balePostBadge.value = ch.auto_badge
    }
  }
}

watch(() => props.topic, (newTopic) => {
  if (newTopic) {
    telegramActive.value = newTopic.telegram_bot_active || false
    baleActive.value = newTopic.bale_bot_active || false
    telegramPostBadge.value = newTopic.telegram_post_badge || ''
    balePostBadge.value = newTopic.bale_post_badge || ''
    telegramPostLinkMode.value = newTopic.telegram_post_link_mode || 'auto_long'
    balePostLinkMode.value = newTopic.bale_post_link_mode || 'auto_long'
    if (newTopic.telegram_connections) {
      selectedTgConnections.value = newTopic.telegram_connections.map((c: any) => c.id || c)
    }
    if (newTopic.bale_connections) {
      selectedBaleConnections.value = newTopic.bale_connections.map((c: any) => c.id || c)
    }
  }
}, { deep: true })

const handleSave = () => {
  isSaving.value = true
  setTimeout(() => {
    isSaving.value = false
    saveSuccess.value = true
    emit('save', {
      telegram_bot_active: telegramActive.value,
      bale_bot_active: baleActive.value,
      telegram_connections: selectedTgConnections.value,
      bale_connections: selectedBaleConnections.value,
      telegram_post_badge: telegramPostBadge.value.trim(),
      bale_post_badge: balePostBadge.value.trim(),
      telegram_post_link_mode: telegramPostLinkMode.value,
      bale_post_link_mode: balePostLinkMode.value
    })
    
    setTimeout(() => {
      saveSuccess.value = false
      emit('back')
    }, 1000)
  }, 1200)
}
</script>

<template>
  <div 
    class="w-full flex flex-col gap-5 text-start font-sans" 
    :dir="languageStore.dir"
  >
    <!-- Header -->
    <PlatformHeader 
      is-inner-page
      :inner-title="languageStore.t('تنظیمات اتصالات', 'Connections Settings')"
      :show-options-button="false"
      @back="emit('back')"
    />

    <!-- Notice Banner -->
    <div class="bg-indigo-50/50 dark:bg-indigo-950/20 rounded-2xl p-4 border border-indigo-50 dark:border-indigo-900/30 text-xs text-indigo-700 dark:text-indigo-400 leading-relaxed text-start">
      {{ languageStore.t('💡 با فعال‌سازی بازنشر، پست‌های ارسالی شما در این تاپیک به صورت خودکار از طریق ربات‌های اختصاصی در گروه‌ها و کانال‌های انتخاب شده منتشر خواهند شد.', '💡 By enabling auto-repost, your posts in this topic will be automatically published via dedicated bots in the selected groups and channels.') }}
    </div>

    <!-- Telegram Card: In a dedicated card with slightly lighter background -->
    <div class="w-full bg-card/65 dark:bg-card/40 border border-border/60 rounded-3xl p-5 shadow-xs flex flex-col gap-4">
        <div class="flex items-center justify-between p-4 bg-background/40 dark:bg-card/30 rounded-2xl border border-border/50 transition-all duration-300">
          <div class="flex flex-col text-start pe-4">
            <span class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
              <span class="size-2 rounded-full bg-sky-500 shrink-0" />
              {{ languageStore.t('بازنشر در تلگرام', 'Repost in Telegram') }}
            </span>
            <span class="text-[9.5px] text-muted-foreground mt-1 leading-normal">
              {{ languageStore.t('ارسال پیام‌های جدید این تاپیک به کانال‌ها و گروه‌های تلگرام', 'Send new messages of this topic to Telegram channels and groups') }}
            </span>
          </div>
          <Switch v-model:checked="telegramActive" />
        </div>

        <transition name="expand-fade">
          <div v-if="telegramActive" class="flex flex-col gap-2.5 overflow-hidden">
            <!-- Telegram not connected -->
            <div 
              v-if="!telegramConnected" 
              class="flex flex-col gap-3 p-3.5 rounded-2xl bg-destructive/5 border border-destructive/15 text-start font-sans"
            >
              <div class="flex items-start gap-2.5">
                <AlertCircleIcon class="size-4.5 text-destructive shrink-0 mt-0.5" />
                <div class="flex flex-col gap-1">
                  <span class="text-[11px] font-bold text-destructive">{{ languageStore.t('ربات تلگرام متصل نیست', 'Telegram bot is not connected') }}</span>
                  <span class="text-[9.5px] text-muted-foreground leading-normal">
                    {{ languageStore.t('برای تعریف مقاصد بازنشر در تلگرام، ابتدا باید ربات تلگرام خود را در پروفایل متصل کنید.', 'To define repost destinations in Telegram, you must first connect your Telegram bot in your profile.') }}
                  </span>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="xs" 
                class="self-start text-[10px] h-7 rounded-lg border-destructive/20 text-destructive hover:bg-destructive/10 cursor-pointer gap-1 ps-2.5 pe-2"
                @click="emit('goToConnections')"
              >
                <span>{{ languageStore.t('اتصال ربات تلگرام', 'Connect Telegram Bot') }}</span>
                <ChevronRightIcon class="size-3.5" :class="[languageStore.isFa ? 'rotate-180' : '']" />
              </Button>
            </div>

            <!-- Telegram Channels list -->
            <div v-else class="flex flex-col gap-2 bg-background/30 rounded-2xl p-1.5 border border-border/40">
              <div v-if="loadingTg" class="text-center text-xs text-gray-400 py-4">{{ languageStore.t('در حال بارگذاری مقاصد تلگرام......', 'Loading Telegram destinations...') }}</div>
              <div v-else-if="tgDestinations.length === 0" class="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/20 rounded-xl p-3 border border-amber-50 dark:border-amber-900/30 text-start">
                {{ languageStore.t('⚠️ هیچ مقصد متصلی در تلگرام یافت نشد. ابتدا ربات خود را در تلگرام به گروه یا کانال عضو و مدیر کنید.', '⚠️ No connected destination found in Telegram. First add your bot to a group or channel and make it an admin.') }}
              </div>
              <template v-else>
                <div 
                  v-for="ch in tgDestinations" 
                  :key="ch.id"
                  @click="toggleTgChannel(ch.id)"
                  class="flex items-center justify-between p-2.5 rounded-xl hover:bg-muted/40 cursor-pointer transition-colors"
                >
                  <div class="flex items-center gap-3">
                    <div class="size-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-500 shrink-0">
                      <SendIcon class="size-4 rotate-45 -translate-x-0.5 translate-y-0.5" />
                    </div>
                    <div class="flex flex-col text-start">
                      <div class="flex items-center gap-1.5">
                        <span class="text-[11px] font-bold text-foreground">{{ ch.label }}</span>
                        <span v-if="ch.auto_badge" class="text-[9px] font-medium text-sky-600 dark:text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded-md dir-ltr font-mono">{{ ch.auto_badge }}</span>
                      </div>
                      <span class="text-[9px] text-muted-foreground mt-0.5 dir-ltr text-start">{{ ch.chat_id }}</span>
                    </div>
                  </div>
                  <Checkbox :checked="selectedTgConnections.includes(ch.id)" @update:checked="toggleTgChannel(ch.id)" @click.stop class="shrink-0" />
                </div>
                <!-- Disconnect Guide -->
                <div class="m-1.5 p-3 bg-muted/20 border border-border/40 rounded-xl leading-relaxed text-start">
                  <span class="text-[10px] font-bold text-muted-foreground block">{{ languageStore.t('💡 راهنمای حذف مقصد:', '💡 Destination Removal Guide:') }}</span>
                  <span class="text-[9px] text-muted-foreground/80 mt-1 block">{{ languageStore.t('برای حذف دائمی هر یک از مقاصد فوق، کافیست ربات تفکر را از کانال یا گروه مربوطه در تلگرام ریمو (حذف) کنید. سیستم به صورت خودکار تغییرات را اعمال خواهد کرد.', 'To permanently remove any of the above destinations, simply remove the Tafakor bot from the corresponding channel or group in Telegram. The system will apply the changes automatically.') }}</span>
                </div>
              </template>
            </div>

            <!-- Telegram Post Badge / Signature -->
            <div class="flex flex-col gap-2 p-3.5 bg-background/30 rounded-2xl border border-border/40 text-start">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <Label for="tg-post-badge" class="text-[11px] font-bold text-foreground/85">
                    {{ languageStore.t('امضای پست‌ها در تلگرام (بج منبع)', 'Telegram Post Signature (Source Badge)') }}
                  </Label>
                  <span 
                    v-if="telegramPostBadge && telegramPostBadge === getAutoBadgeForTelegram()"
                    class="text-[8.5px] font-semibold text-sky-600 dark:text-sky-400 bg-sky-500/10 px-1.5 py-0.5 rounded-md"
                  >
                    {{ languageStore.t('تگ خودکار', 'Auto Tag') }}
                  </span>
                  <span 
                    v-else-if="telegramPostBadge"
                    class="text-[8.5px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded-md"
                  >
                    {{ languageStore.t('تگ سفارشی', 'Custom Tag') }}
                  </span>
                </div>
                <span class="text-[9.5px] text-muted-foreground">{{ languageStore.t('اختیاری', 'Optional') }}</span>
              </div>
              <Input 
                id="tg-post-badge" 
                v-model="telegramPostBadge" 
                @input="tgBadgeManuallyEdited = true"
                :placeholder="languageStore.t('مثال: @my_channel یا 📌 منبع: کانال تلگرام تفکر', 'e.g., @my_channel or 📌 Source: Tafakor Telegram')" 
                class="h-9.5 rounded-xl border-border/60 focus-visible:ring-primary/20 bg-background/50 text-xs font-medium text-start"
                dir="auto"
                maxlength="100"
              />

              <!-- Auto-tag recommendation & reset pill -->
              <div 
                v-if="getAutoBadgeForTelegram()" 
                class="flex items-center justify-between text-[10px] bg-sky-50/60 dark:bg-sky-950/20 border border-sky-200/40 dark:border-sky-800/40 px-2.5 py-1.5 rounded-xl"
              >
                <div class="flex items-center gap-1.5 text-sky-700 dark:text-sky-300">
                  <SparklesIcon class="size-3.5 shrink-0 text-sky-500" />
                  <span class="text-[10px]">{{ languageStore.t('تگ خودکار کانال:', 'Auto channel tag:') }}</span>
                  <code class="font-mono font-bold dir-ltr bg-sky-100 dark:bg-sky-900/50 px-1.5 py-0.5 rounded text-[9.5px] text-sky-800 dark:text-sky-200">{{ getAutoBadgeForTelegram() }}</code>
                </div>
                <button 
                  type="button" 
                  @click="telegramPostBadge = getAutoBadgeForTelegram(); tgBadgeManuallyEdited = false"
                  class="text-[9.5px] font-bold text-sky-600 dark:text-sky-400 hover:underline cursor-pointer flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-sky-100/50 dark:hover:bg-sky-900/30 transition-colors"
                >
                  <RotateCcwIcon class="size-3" />
                  <span>{{ languageStore.t('اعمال مجدد تگ خودکار', 'Reset to Auto Tag') }}</span>
                </button>
              </div>

              <span class="text-[9.5px] text-muted-foreground leading-normal">
                {{ languageStore.t('این متن کوتاه به صورت خودکار به انتهای پیام‌های ارسالی به تلگرام اضافه خواهد شد.', 'This text will be automatically appended to posts sent to Telegram.') }}
              </span>
            </div>

            <!-- Telegram Post Link Mode -->
            <div class="flex flex-col gap-2.5 p-3.5 bg-background/30 rounded-2xl border border-border/40 text-start">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <LinkIcon class="size-3.5 text-sky-500 shrink-0" />
                  <Label class="text-[11px] font-bold text-foreground/85">
                    {{ languageStore.t('لینک مشاهده و ثبت نظر در تلگرام', 'Preview & Comment Link in Telegram') }}
                  </Label>
                </div>
                <span 
                  class="text-[8.5px] px-2 py-0.5 rounded-md font-semibold"
                  :class="[
                    telegramPostLinkMode === 'auto_long' ? 'bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20' :
                    telegramPostLinkMode === 'always' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' :
                    'bg-muted/50 text-muted-foreground border border-border/40'
                  ]"
                >
                  {{ 
                    telegramPostLinkMode === 'auto_long' ? languageStore.t('خودکار (متن‌های طولانی)', 'Auto (Long Posts)') :
                    telegramPostLinkMode === 'always' ? languageStore.t('همیشه فعال', 'Always Active') :
                    languageStore.t('غیرفعال', 'Disabled')
                  }}
                </span>
              </div>

              <span class="text-[9.5px] text-muted-foreground leading-normal">
                {{ languageStore.t('تنظیم نحوه درج لینک وب‌اپلیکیشن تفکر در انتهای پیام‌های بازنشر جهت مطالعه کامل پست و ثبت نظر ناشناس:', 'Choose how to attach the Tafakor preview link at the end of reposted messages for full reading and anonymous comments:') }}
              </span>

              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-0.5">
                <!-- Auto Long Option -->
                <button
                  type="button"
                  @click="telegramPostLinkMode = 'auto_long'"
                  class="flex flex-col items-start p-2.5 rounded-xl border text-start transition-all cursor-pointer relative"
                  :class="[
                    telegramPostLinkMode === 'auto_long'
                      ? 'border-sky-500 bg-sky-500/10 text-foreground ring-1 ring-sky-500/30'
                      : 'border-border/50 bg-background/50 hover:bg-muted/40 text-muted-foreground'
                  ]"
                >
                  <div class="flex items-center justify-between w-full">
                    <span class="text-[10.5px] font-bold" :class="[telegramPostLinkMode === 'auto_long' ? 'text-sky-600 dark:text-sky-400' : 'text-foreground']">
                      {{ languageStore.t('خودکار', 'Automatic') }}
                    </span>
                    <span class="text-[8px] font-semibold bg-sky-500/15 text-sky-600 dark:text-sky-400 px-1.5 py-0.2 rounded-full">
                      {{ languageStore.t('پیش‌فرض', 'Default') }}
                    </span>
                  </div>
                  <span class="text-[9px] mt-1 leading-snug" :class="[telegramPostLinkMode === 'auto_long' ? 'text-sky-800/80 dark:text-sky-200/80' : 'text-muted-foreground']">
                    {{ languageStore.t('فقط برای پیام‌های طولانی که کوتاه می‌شوند', 'Only for long posts exceeding limits') }}
                  </span>
                </button>

                <!-- Always Option -->
                <button
                  type="button"
                  @click="telegramPostLinkMode = 'always'"
                  class="flex flex-col items-start p-2.5 rounded-xl border text-start transition-all cursor-pointer relative"
                  :class="[
                    telegramPostLinkMode === 'always'
                      ? 'border-sky-500 bg-sky-500/10 text-foreground ring-1 ring-sky-500/30'
                      : 'border-border/50 bg-background/50 hover:bg-muted/40 text-muted-foreground'
                  ]"
                >
                  <div class="flex items-center justify-between w-full">
                    <span class="text-[10.5px] font-bold" :class="[telegramPostLinkMode === 'always' ? 'text-sky-600 dark:text-sky-400' : 'text-foreground']">
                      {{ languageStore.t('همیشه فعال', 'Always') }}
                    </span>
                  </div>
                  <span class="text-[9px] mt-1 leading-snug" :class="[telegramPostLinkMode === 'always' ? 'text-sky-800/80 dark:text-sky-200/80' : 'text-muted-foreground']">
                    {{ languageStore.t('برای تمامی پست‌ها حتی پست‌های کوتاه', 'Attach link to all posts even short ones') }}
                  </span>
                </button>

                <!-- Disabled Option -->
                <button
                  type="button"
                  @click="telegramPostLinkMode = 'disabled'"
                  class="flex flex-col items-start p-2.5 rounded-xl border text-start transition-all cursor-pointer relative"
                  :class="[
                    telegramPostLinkMode === 'disabled'
                      ? 'border-destructive/60 bg-destructive/10 text-destructive ring-1 ring-destructive/20'
                      : 'border-border/50 bg-background/50 hover:bg-muted/40 text-muted-foreground'
                  ]"
                >
                  <div class="flex items-center justify-between w-full">
                    <span class="text-[10.5px] font-bold" :class="[telegramPostLinkMode === 'disabled' ? 'text-destructive' : 'text-foreground']">
                      {{ languageStore.t('غیرفعال', 'Disabled') }}
                    </span>
                  </div>
                  <span class="text-[9px] mt-1 leading-snug" :class="[telegramPostLinkMode === 'disabled' ? 'text-destructive/80' : 'text-muted-foreground']">
                    {{ languageStore.t('عدم درج هیچ لینکی در انتهای پیام‌ها', 'Do not attach any preview link') }}
                  </span>
                </button>
              </div>

              <!-- Preview snippet of bottom guide text -->
              <div v-if="telegramPostLinkMode !== 'disabled'" class="mt-1 p-2 rounded-xl bg-sky-50/50 dark:bg-sky-950/20 border border-sky-100 dark:border-sky-900/30 flex flex-col gap-1 text-[9px]">
                <div class="flex items-center gap-1 font-bold text-sky-800 dark:text-sky-300">
                  <SparklesIcon class="size-3 text-sky-500" />
                  <span>{{ languageStore.t('نمونه متن راهنما و لینک در پایین پست:', 'Preview of guide text & link at post bottom:') }}</span>
                </div>
                <div class="text-[9px] text-muted-foreground bg-background/70 p-1.5 rounded-lg border border-border/40 dir-auto font-sans">
                  🔗 {{ languageStore.t('مشاهده و ثبت نظر در تفکر:', 'View and comment on Tafakor:') }}<br />
                  <span class="dir-ltr inline-block font-mono text-[8.5px] text-sky-600 dark:text-sky-400 mt-0.5">https://.../p/123</span>
                </div>
              </div>
            </div>
          </div>
        </transition>
    </div>

    <!-- Bale Card: Separated in its own card with slightly lighter background -->
    <div class="w-full bg-card/65 dark:bg-card/40 border border-border/60 rounded-3xl p-5 shadow-xs flex flex-col gap-4">
        <div class="flex items-center justify-between p-4 bg-background/40 dark:bg-card/30 rounded-2xl border border-border/50 transition-all duration-300">
          <div class="flex flex-col text-start pe-4">
            <span class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
              <span class="size-2 rounded-full bg-emerald-500 shrink-0" />
              {{ languageStore.t('بازنشر در بله', 'Repost in Bale') }}
            </span>
            <span class="text-[9.5px] text-muted-foreground mt-1 leading-normal">
              {{ languageStore.t('ارسال پیام‌های جدید این تاپیک به کانال‌ها و گروه‌های بله', 'Send new messages of this topic to Bale channels and groups') }}
            </span>
          </div>
          <Switch v-model:checked="baleActive" />
        </div>

        <transition name="expand-fade">
          <div v-if="baleActive" class="flex flex-col gap-2.5 overflow-hidden">
            <!-- Bale not connected -->
            <div 
              v-if="!baleConnected" 
              class="flex flex-col gap-3 p-3.5 rounded-2xl bg-destructive/5 border border-destructive/15 text-start font-sans"
            >
              <div class="flex items-start gap-2.5">
                <AlertCircleIcon class="size-4.5 text-destructive shrink-0 mt-0.5" />
                <div class="flex flex-col gap-1">
                  <span class="text-[11px] font-bold text-destructive">{{ languageStore.t('ربات بله متصل نیست', 'Bale bot is not connected') }}</span>
                  <span class="text-[9.5px] text-muted-foreground leading-normal">
                    {{ languageStore.t('برای تعریف مقاصد بازنشر در بله، ابتدا باید ربات بله خود را در پروفایل متصل کنید.', 'To define repost destinations in Bale, you must first connect your Bale bot in your profile.') }}
                  </span>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="xs" 
                class="self-start text-[10px] h-7 rounded-lg border-destructive/20 text-destructive hover:bg-destructive/10 cursor-pointer gap-1 ps-2.5 pe-2"
                @click="emit('goToConnections')"
              >
                <span>{{ languageStore.t('اتصال ربات بله', 'Connect Bale Bot') }}</span>
                <ChevronRightIcon class="size-3.5" :class="[languageStore.isFa ? 'rotate-180' : '']" />
              </Button>
            </div>

            <!-- Bale Channels list -->
            <div v-else class="flex flex-col gap-2 bg-background/30 rounded-2xl p-1.5 border border-border/40">
              <div v-if="loadingBale" class="text-center text-xs text-gray-400 py-4">{{ languageStore.t('در حال بارگذاری مقاصد بله......', 'Loading Bale destinations...') }}</div>
              <div v-else-if="baleDestinations.length === 0" class="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/20 rounded-xl p-3 border border-amber-50 dark:border-amber-900/30 text-start">
                {{ languageStore.t('⚠️ هیچ مقصد متصلی در بله یافت نشد. ابتدا ربات خود را در بله به گروه یا کانال عضو و مدیر کنید.', '⚠️ No connected destination found in Bale. First add your bot to a group or channel and make it an admin.') }}
              </div>
              <template v-else>
                <div 
                  v-for="ch in baleDestinations" 
                  :key="ch.id"
                  @click="toggleBaleChannel(ch.id)"
                  class="flex items-center justify-between p-2.5 rounded-xl hover:bg-muted/40 cursor-pointer transition-colors"
                >
                  <div class="flex items-center gap-3">
                    <div class="size-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500 shrink-0">
                      <SendIcon class="size-4 rotate-45 -translate-x-0.5 translate-y-0.5" />
                    </div>
                    <div class="flex flex-col text-start">
                      <div class="flex items-center gap-1.5">
                        <span class="text-[11px] font-bold text-foreground">{{ ch.label }}</span>
                        <span v-if="ch.auto_badge" class="text-[9px] font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-md dir-ltr font-mono">{{ ch.auto_badge }}</span>
                      </div>
                      <span class="text-[9px] text-muted-foreground mt-0.5 dir-ltr text-start">{{ ch.chat_id }}</span>
                    </div>
                  </div>
                  <Checkbox :checked="selectedBaleConnections.includes(ch.id)" @update:checked="toggleBaleChannel(ch.id)" @click.stop class="shrink-0" />
                </div>
                <!-- Disconnect Guide -->
                <div class="m-1.5 p-3 bg-muted/20 border border-border/40 rounded-xl leading-relaxed text-start">
                  <span class="text-[10px] font-bold text-muted-foreground block">{{ languageStore.t('💡 راهنمای حذف مقصد:', '💡 Destination Removal Guide:') }}</span>
                  <span class="text-[9px] text-muted-foreground/80 mt-1 block">{{ languageStore.t('برای حذف دائمی هر یک از مقاصد فوق، کافیست ربات تفکر را از کانال یا گروه مربوطه در بله ریمو (حذف) کنید. سیستم به صورت خودکار تغییرات را اعمال خواهد کرد.', 'To permanently remove any of the above destinations, simply remove the Tafakor bot from the corresponding channel or group in Bale. The system will apply the changes automatically.') }}</span>
                </div>
              </template>
            </div>

            <!-- Bale Post Badge / Signature -->
            <div class="flex flex-col gap-2 p-3.5 bg-background/30 rounded-2xl border border-border/40 text-start">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <Label for="bale-post-badge" class="text-[11px] font-bold text-foreground/85">
                    {{ languageStore.t('امضای پست‌ها در بله (بج منبع)', 'Bale Post Signature (Source Badge)') }}
                  </Label>
                  <span 
                    v-if="balePostBadge && balePostBadge === getAutoBadgeForBale()"
                    class="text-[8.5px] font-semibold text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-md"
                  >
                    {{ languageStore.t('تگ خودکار', 'Auto Tag') }}
                  </span>
                  <span 
                    v-else-if="balePostBadge"
                    class="text-[8.5px] font-semibold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded-md"
                  >
                    {{ languageStore.t('تگ سفارشی', 'Custom Tag') }}
                  </span>
                </div>
                <span class="text-[9.5px] text-muted-foreground">{{ languageStore.t('اختیاری', 'Optional') }}</span>
              </div>
              <Input 
                id="bale-post-badge" 
                v-model="balePostBadge" 
                @input="baleBadgeManuallyEdited = true"
                :placeholder="languageStore.t('مثال: ble.ir/my_channel یا 📌 منبع: کانال بله تفکر', 'e.g., ble.ir/my_channel or 📌 Source: Tafakor Bale')" 
                class="h-9.5 rounded-xl border-border/60 focus-visible:ring-primary/20 bg-background/50 text-xs font-medium text-start"
                dir="auto"
                maxlength="100"
              />

              <!-- Auto-tag recommendation & reset pill -->
              <div 
                v-if="getAutoBadgeForBale()" 
                class="flex items-center justify-between text-[10px] bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-200/40 dark:border-emerald-800/40 px-2.5 py-1.5 rounded-xl"
              >
                <div class="flex items-center gap-1.5 text-emerald-700 dark:text-emerald-300">
                  <SparklesIcon class="size-3.5 shrink-0 text-emerald-500" />
                  <span class="text-[10px]">{{ languageStore.t('تگ خودکار کانال:', 'Auto channel tag:') }}</span>
                  <code class="font-mono font-bold dir-ltr bg-emerald-100 dark:bg-emerald-900/50 px-1.5 py-0.5 rounded text-[9.5px] text-emerald-800 dark:text-emerald-200">{{ getAutoBadgeForBale() }}</code>
                </div>
                <button 
                  type="button" 
                  @click="balePostBadge = getAutoBadgeForBale(); baleBadgeManuallyEdited = false"
                  class="text-[9.5px] font-bold text-emerald-600 dark:text-emerald-400 hover:underline cursor-pointer flex items-center gap-1 px-1.5 py-0.5 rounded hover:bg-emerald-100/50 dark:hover:bg-emerald-900/30 transition-colors"
                >
                  <RotateCcwIcon class="size-3" />
                  <span>{{ languageStore.t('اعمال مجدد تگ خودکار', 'Reset to Auto Tag') }}</span>
                </button>
              </div>

              <span class="text-[9.5px] text-muted-foreground leading-normal">
                {{ languageStore.t('این متن کوتاه به صورت خودکار به انتهای پیام‌های ارسالی به بله اضافه خواهد شد.', 'This text will be automatically appended to posts sent to Bale.') }}
              </span>
            </div>

            <!-- Bale Post Link Mode -->
            <div class="flex flex-col gap-2.5 p-3.5 bg-background/30 rounded-2xl border border-border/40 text-start">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-1.5">
                  <LinkIcon class="size-3.5 text-emerald-500 shrink-0" />
                  <Label class="text-[11px] font-bold text-foreground/85">
                    {{ languageStore.t('لینک مشاهده و ثبت نظر در بله', 'Preview & Comment Link in Bale') }}
                  </Label>
                </div>
                <span 
                  class="text-[8.5px] px-2 py-0.5 rounded-md font-semibold"
                  :class="[
                    balePostLinkMode === 'auto_long' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' :
                    balePostLinkMode === 'always' ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20' :
                    'bg-muted/50 text-muted-foreground border border-border/40'
                  ]"
                >
                  {{ 
                    balePostLinkMode === 'auto_long' ? languageStore.t('خودکار (متن‌های طولانی)', 'Auto (Long Posts)') :
                    balePostLinkMode === 'always' ? languageStore.t('همیشه فعال', 'Always Active') :
                    languageStore.t('غیرفعال', 'Disabled')
                  }}
                </span>
              </div>

              <span class="text-[9.5px] text-muted-foreground leading-normal">
                {{ languageStore.t('تنظیم نحوه درج لینک وب‌اپلیکیشن تفکر در انتهای پیام‌های بازنشر جهت مطالعه کامل پست و ثبت نظر ناشناس:', 'Choose how to attach the Tafakor preview link at the end of reposted messages for full reading and anonymous comments:') }}
              </span>

              <div class="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-0.5">
                <!-- Auto Long Option -->
                <button
                  type="button"
                  @click="balePostLinkMode = 'auto_long'"
                  class="flex flex-col items-start p-2.5 rounded-xl border text-start transition-all cursor-pointer relative"
                  :class="[
                    balePostLinkMode === 'auto_long'
                      ? 'border-emerald-500 bg-emerald-500/10 text-foreground ring-1 ring-emerald-500/30'
                      : 'border-border/50 bg-background/50 hover:bg-muted/40 text-muted-foreground'
                  ]"
                >
                  <div class="flex items-center justify-between w-full">
                    <span class="text-[10.5px] font-bold" :class="[balePostLinkMode === 'auto_long' ? 'text-emerald-600 dark:text-emerald-400' : 'text-foreground']">
                      {{ languageStore.t('خودکار', 'Automatic') }}
                    </span>
                    <span class="text-[8px] font-semibold bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 px-1.5 py-0.2 rounded-full">
                      {{ languageStore.t('پیش‌فرض', 'Default') }}
                    </span>
                  </div>
                  <span class="text-[9px] mt-1 leading-snug" :class="[balePostLinkMode === 'auto_long' ? 'text-emerald-800/80 dark:text-emerald-200/80' : 'text-muted-foreground']">
                    {{ languageStore.t('فقط برای پیام‌های طولانی که کوتاه می‌شوند', 'Only for long posts exceeding limits') }}
                  </span>
                </button>

                <!-- Always Option -->
                <button
                  type="button"
                  @click="balePostLinkMode = 'always'"
                  class="flex flex-col items-start p-2.5 rounded-xl border text-start transition-all cursor-pointer relative"
                  :class="[
                    balePostLinkMode === 'always'
                      ? 'border-emerald-500 bg-emerald-500/10 text-foreground ring-1 ring-emerald-500/30'
                      : 'border-border/50 bg-background/50 hover:bg-muted/40 text-muted-foreground'
                  ]"
                >
                  <div class="flex items-center justify-between w-full">
                    <span class="text-[10.5px] font-bold" :class="[balePostLinkMode === 'always' ? 'text-emerald-600 dark:text-emerald-400' : 'text-foreground']">
                      {{ languageStore.t('همیشه فعال', 'Always') }}
                    </span>
                  </div>
                  <span class="text-[9px] mt-1 leading-snug" :class="[balePostLinkMode === 'always' ? 'text-emerald-800/80 dark:text-emerald-200/80' : 'text-muted-foreground']">
                    {{ languageStore.t('برای تمامی پست‌ها حتی پست‌های کوتاه', 'Attach link to all posts even short ones') }}
                  </span>
                </button>

                <!-- Disabled Option -->
                <button
                  type="button"
                  @click="balePostLinkMode = 'disabled'"
                  class="flex flex-col items-start p-2.5 rounded-xl border text-start transition-all cursor-pointer relative"
                  :class="[
                    balePostLinkMode === 'disabled'
                      ? 'border-destructive/60 bg-destructive/10 text-destructive ring-1 ring-destructive/20'
                      : 'border-border/50 bg-background/50 hover:bg-muted/40 text-muted-foreground'
                  ]"
                >
                  <div class="flex items-center justify-between w-full">
                    <span class="text-[10.5px] font-bold" :class="[balePostLinkMode === 'disabled' ? 'text-destructive' : 'text-foreground']">
                      {{ languageStore.t('غیرفعال', 'Disabled') }}
                    </span>
                  </div>
                  <span class="text-[9px] mt-1 leading-snug" :class="[balePostLinkMode === 'disabled' ? 'text-destructive/80' : 'text-muted-foreground']">
                    {{ languageStore.t('عدم درج هیچ لینکی در انتهای پیام‌ها', 'Do not attach any preview link') }}
                  </span>
                </button>
              </div>

              <!-- Preview snippet of bottom guide text -->
              <div v-if="balePostLinkMode !== 'disabled'" class="mt-1 p-2 rounded-xl bg-emerald-50/50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 flex flex-col gap-1 text-[9px]">
                <div class="flex items-center gap-1 font-bold text-emerald-800 dark:text-emerald-300">
                  <SparklesIcon class="size-3 text-emerald-500" />
                  <span>{{ languageStore.t('نمونه متن راهنما و لینک در پایین پست:', 'Preview of guide text & link at post bottom:') }}</span>
                </div>
                <div class="text-[9px] text-muted-foreground bg-background/70 p-1.5 rounded-lg border border-border/40 dir-auto font-sans">
                  🔗 {{ languageStore.t('مشاهده و ثبت نظر در تفکر:', 'View and comment on Tafakor:') }}<br />
                  <span class="dir-ltr inline-block font-mono text-[8.5px] text-emerald-600 dark:text-emerald-400 mt-0.5">https://.../p/123</span>
                </div>
              </div>
            </div>
          </div>
        </transition>
    </div>

    <!-- Save Button -->
    <Button 
      @click="handleSave"
      :disabled="isSaving || saveSuccess"
      class="w-full h-11 rounded-xl font-bold transition-all relative overflow-hidden active:scale-[0.98] cursor-pointer"
      :variant="saveSuccess ? 'secondary' : 'default'"
    >
      <transition name="btn-content" mode="out-in">
        <div v-if="isSaving" class="flex items-center gap-2 justify-center">
          <RefreshCwIcon class="size-4 animate-spin" />
          <span>{{ languageStore.t('در حال ذخیره‌سازی...', 'Saving...') }}</span>
        </div>
        <div v-else-if="saveSuccess" class="flex items-center gap-2 justify-center text-emerald-650 dark:text-emerald-400">
          <CheckCircle2Icon class="size-4" />
          <span>{{ languageStore.t('اتصالات با موفقیت به روز رسانی شد', 'Connections updated successfully') }}</span>
        </div>
        <div v-else class="flex items-center gap-2 justify-center">
          <SaveIcon class="size-4" />
          <span>{{ languageStore.t('ذخیره تنظیمات اتصالات', 'Save Connections Settings') }}</span>
        </div>
      </transition>
    </Button>
  </div>
</template>

<style scoped>
.btn-content-enter-active,
.btn-content-leave-active {
  transition: all 0.2s ease-out;
}
.btn-content-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.btn-content-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Slide expand transition for auto-repost list */
.expand-fade-enter-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 500px;
  opacity: 1;
}
.expand-fade-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 500px;
  opacity: 1;
}
.expand-fade-enter-from,
.expand-fade-leave-to {
  max-height: 0;
  opacity: 0;
  margin-top: 0;
  padding-top: 0;
  padding-bottom: 0;
}
</style>
