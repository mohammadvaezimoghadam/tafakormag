<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import PlatformHeader from './PlatformHeader.vue'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { 
  SendIcon, 
  MessageSquareIcon, 
  AlertCircleIcon, 
  SaveIcon, 
  RefreshCwIcon, 
  CheckCircle2Icon,
  ChevronRightIcon 
} from '@lucide/vue'
import * as api from '@/api'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = defineProps<{
  topic: {
    id: number
    title: string
    telegram_bot_active?: boolean
    bale_bot_active?: boolean
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
  }): void
}>()

// Active Toggles
const telegramActive = ref(props.topic.telegram_bot_active || false)
const baleActive = ref(props.topic.bale_bot_active || false)

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
  }
}

const toggleBaleChannel = (id: number) => {
  const idx = selectedBaleConnections.value.indexOf(id)
  if (idx > -1) {
    selectedBaleConnections.value.splice(idx, 1)
  } else {
    selectedBaleConnections.value.push(id)
  }
}

const handleSave = () => {
  isSaving.value = true
  setTimeout(() => {
    isSaving.value = false
    saveSuccess.value = true
    emit('save', {
      telegram_bot_active: telegramActive.value,
      bale_bot_active: baleActive.value,
      telegram_connections: selectedTgConnections.value,
      bale_connections: selectedBaleConnections.value
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

    <!-- Main Card wrapper -->
    <div class="w-full bg-card/25 dark:bg-card/15 border border-border/50 rounded-3xl p-5 shadow-xs flex flex-col gap-5">
      
      <div class="bg-indigo-50/50 dark:bg-indigo-950/20 rounded-2xl p-4 border border-indigo-50 dark:border-indigo-900/30 text-xs text-indigo-700 dark:text-indigo-400 leading-relaxed text-start">
        {{ languageStore.t('💡 با فعال‌سازی بازنشر، پست‌های ارسالی شما در این تاپیک به صورت خودکار از طریق ربات‌های اختصاصی در گروه‌ها و کانال‌های انتخاب شده منتشر خواهند شد.', '💡 By enabling auto-repost, your posts in this topic will be automatically published via dedicated bots in the selected groups and channels.') }}
      </div>

      <!-- Telegram Section -->
      <div class="flex flex-col gap-4">
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
                      <span class="text-[11px] font-bold text-foreground">{{ ch.label }}</span>
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
          </div>
        </transition>
      </div>

      <!-- Bale Section -->
      <div class="flex flex-col gap-4">
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
                      <span class="text-[11px] font-bold text-foreground">{{ ch.label }}</span>
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
          </div>
        </transition>
      </div>

      <div class="h-[1px] bg-border/40 my-1" />

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
