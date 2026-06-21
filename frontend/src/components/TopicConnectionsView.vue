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
  telegramConnected: boolean
  baleConnected: boolean
  onSave?: (data: { 
    telegram_bot_active: boolean
    bale_bot_active: boolean
    telegram_connections: number[]
    bale_connections: number[] 
  }) => Promise<any> | any
}>()

const emit = defineEmits<{
  (e: 'back'): void
  (e: 'save', data: { 
    telegram_bot_active: boolean
    bale_bot_active: boolean
    telegram_connections: number[]
    bale_connections: number[] 
  }): void
  (e: 'goToConnections'): void
}>()

const getIds = (connections?: any[]) => {
  if (!connections) return []
  return connections.map(c => typeof c === 'object' && c !== null ? c.id : c)
}

const telegramActive = ref(props.topic.telegram_bot_active ?? false)
const baleActive = ref(props.topic.bale_bot_active ?? false)

const selectedTgConnections = ref<number[]>(getIds(props.topic.telegram_connections))
const selectedBaleConnections = ref<number[]>(getIds(props.topic.bale_connections))

interface Destination {
  id: number
  label: string
  chat_id: string
}

const tgDestinations = ref<Destination[]>([])
const baleDestinations = ref<Destination[]>([])

const loadingTg = ref(false)
const loadingBale = ref(false)
const isSaving = ref(false)
const saveSuccess = ref(false)

const loadTgDestinations = async () => {
  if (!props.telegramConnected) return
  loadingTg.value = true
  try {
    const res = await api.fetchDestinations('telegram')
    tgDestinations.value = res.data ?? []
  } catch (err) {
    console.error('Error fetching tg destinations:', err)
  } finally {
    loadingTg.value = false
  }
}

const loadBaleDestinations = async () => {
  if (!props.baleConnected) return
  loadingBale.value = true
  try {
    const res = await api.fetchDestinations('bale')
    baleDestinations.value = res.data ?? []
  } catch (err) {
    console.error('Error fetching bale destinations:', err)
  } finally {
    loadingBale.value = false
  }
}

watch(telegramActive, (active) => {
  if (active) {
    loadTgDestinations()
  }
})

watch(baleActive, (active) => {
  if (active) {
    loadBaleDestinations()
  }
})

const toggleTgChannel = (destId: number) => {
  const index = selectedTgConnections.value.indexOf(destId)
  if (index === -1) {
    selectedTgConnections.value.push(destId)
  } else {
    selectedTgConnections.value.splice(index, 1)
  }
}

const toggleBaleChannel = (destId: number) => {
  const index = selectedBaleConnections.value.indexOf(destId)
  if (index === -1) {
    selectedBaleConnections.value.push(destId)
  } else {
    selectedBaleConnections.value.splice(index, 1)
  }
}

const handleSave = async () => {
  isSaving.value = true
  try {
    const payload = {
      telegram_bot_active: telegramActive.value,
      bale_bot_active: baleActive.value,
      telegram_connections: selectedTgConnections.value,
      bale_connections: selectedBaleConnections.value
    }
    
    if (props.onSave) {
      await props.onSave(payload)
    } else {
      emit('save', payload)
    }
    
    saveSuccess.value = true
    
    setTimeout(() => {
      saveSuccess.value = false
      emit('back')
    }, 1000)
  } catch (err) {
    console.error('Error saving connections:', err)
  } finally {
    isSaving.value = false
  }
}

onMounted(() => {
  if (telegramActive.value) {
    loadTgDestinations()
  }
  if (baleActive.value) {
    loadBaleDestinations()
  }
})
</script>

<template>
  <div class="w-full flex flex-col gap-5 text-right font-sans" dir="rtl">
    <!-- Header -->
    <PlatformHeader 
      is-inner-page
      inner-title="تنظیمات اتصالات"
      :show-options-button="false"
      @back="emit('back')"
    />

    <!-- Main Card wrapper -->
    <div class="w-full bg-card/25 dark:bg-card/15 border border-border/50 rounded-3xl p-5 shadow-xs flex flex-col gap-5">
      
      <div class="bg-indigo-50/50 dark:bg-indigo-950/20 rounded-2xl p-4 border border-indigo-50 dark:border-indigo-900/30 text-xs text-indigo-700 dark:text-indigo-400 leading-relaxed">
        💡 با فعال‌سازی بازنشر، پست‌های ارسالی شما در این تاپیک به صورت خودکار از طریق ربات‌های اختصاصی در گروه‌ها و کانال‌های انتخاب شده منتشر خواهند شد.
      </div>

      <!-- Telegram Section -->
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between p-4 bg-background/40 dark:bg-card/30 rounded-2xl border border-border/50 transition-all duration-300">
          <div class="flex flex-col text-right pl-4">
            <span class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
              <span class="size-2 rounded-full bg-sky-500 shrink-0" />
              بازنشر در تلگرام
            </span>
            <span class="text-[9.5px] text-muted-foreground mt-1 leading-normal">
              ارسال پیام‌های جدید این تاپیک به کانال‌ها و گروه‌های تلگرام
            </span>
          </div>
          <Switch v-model:checked="telegramActive" />
        </div>

        <transition name="expand-fade">
          <div v-if="telegramActive" class="flex flex-col gap-2.5 overflow-hidden">
            <!-- Telegram not connected -->
            <div 
              v-if="!telegramConnected" 
              class="flex flex-col gap-3 p-3.5 rounded-2xl bg-destructive/5 border border-destructive/15 text-right font-sans"
            >
              <div class="flex items-start gap-2.5">
                <AlertCircleIcon class="size-4.5 text-destructive shrink-0 mt-0.5" />
                <div class="flex flex-col gap-1">
                  <span class="text-[11px] font-bold text-destructive">ربات تلگرام متصل نیست</span>
                  <span class="text-[9.5px] text-muted-foreground leading-normal">
                    برای تعریف مقاصد بازنشر در تلگرام، ابتدا باید ربات تلگرام خود را در پروفایل متصل کنید.
                  </span>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="xs" 
                class="self-start text-[10px] h-7 rounded-lg border-destructive/20 text-destructive hover:bg-destructive/10 cursor-pointer pr-2.5 pl-2 gap-1"
                @click="emit('goToConnections')"
              >
                <span>اتصال ربات تلگرام</span>
                <ChevronRightIcon class="size-3.5 rotate-180" />
              </Button>
            </div>

            <!-- Telegram Channels list -->
            <div v-else class="flex flex-col gap-2 bg-background/30 rounded-2xl p-1.5 border border-border/40">
              <div v-if="loadingTg" class="text-center text-xs text-gray-400 py-4">در حال بارگذاری مقاصد تلگرام...</div>
              <div v-else-if="tgDestinations.length === 0" class="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/20 rounded-xl p-3 border border-amber-50 dark:border-amber-900/30">
                ⚠️ هیچ مقصد متصلی در تلگرام یافت نشد. ابتدا ربات خود را در تلگرام به گروه یا کانال عضو و مدیر کنید.
              </div>
              <div 
                v-else
                v-for="ch in tgDestinations" 
                :key="ch.id"
                @click="toggleTgChannel(ch.id)"
                class="flex items-center justify-between p-2.5 rounded-xl hover:bg-muted/40 cursor-pointer transition-colors"
              >
                <div class="flex items-center gap-3">
                  <div class="size-8 rounded-lg bg-sky-500/10 flex items-center justify-center text-sky-500 shrink-0">
                    <SendIcon class="size-4 rotate-45 -translate-x-0.5 translate-y-0.5" />
                  </div>
                  <div class="flex flex-col text-right">
                    <span class="text-[11px] font-bold text-foreground">{{ ch.label }}</span>
                    <span class="text-[9px] text-muted-foreground mt-0.5 dir-ltr text-right">{{ ch.chat_id }}</span>
                  </div>
                </div>
                <Checkbox :checked="selectedTgConnections.includes(ch.id)" @update:checked="toggleTgChannel(ch.id)" @click.stop class="shrink-0" />
              </div>
            </div>
          </div>
        </transition>
      </div>

      <!-- Bale Section -->
      <div class="flex flex-col gap-4">
        <div class="flex items-center justify-between p-4 bg-background/40 dark:bg-card/30 rounded-2xl border border-border/50 transition-all duration-300">
          <div class="flex flex-col text-right pl-4">
            <span class="text-xs font-extrabold text-foreground flex items-center gap-1.5">
              <span class="size-2 rounded-full bg-emerald-500 shrink-0" />
              بازنشر در بله
            </span>
            <span class="text-[9.5px] text-muted-foreground mt-1 leading-normal">
              ارسال پیام‌های جدید این تاپیک به کانال‌ها و گروه‌های بله
            </span>
          </div>
          <Switch v-model:checked="baleActive" />
        </div>

        <transition name="expand-fade">
          <div v-if="baleActive" class="flex flex-col gap-2.5 overflow-hidden">
            <!-- Bale not connected -->
            <div 
              v-if="!baleConnected" 
              class="flex flex-col gap-3 p-3.5 rounded-2xl bg-destructive/5 border border-destructive/15 text-right font-sans"
            >
              <div class="flex items-start gap-2.5">
                <AlertCircleIcon class="size-4.5 text-destructive shrink-0 mt-0.5" />
                <div class="flex flex-col gap-1">
                  <span class="text-[11px] font-bold text-destructive">ربات بله متصل نیست</span>
                  <span class="text-[9.5px] text-muted-foreground leading-normal">
                    برای تعریف مقاصد بازنشر در بله، ابتدا باید ربات بله خود را در پروفایل متصل کنید.
                  </span>
                </div>
              </div>
              <Button 
                variant="outline" 
                size="xs" 
                class="self-start text-[10px] h-7 rounded-lg border-destructive/20 text-destructive hover:bg-destructive/10 cursor-pointer pr-2.5 pl-2 gap-1"
                @click="emit('goToConnections')"
              >
                <span>اتصال ربات بله</span>
                <ChevronRightIcon class="size-3.5 rotate-180" />
              </Button>
            </div>

            <!-- Bale Channels list -->
            <div v-else class="flex flex-col gap-2 bg-background/30 rounded-2xl p-1.5 border border-border/40">
              <div v-if="loadingBale" class="text-center text-xs text-gray-400 py-4">در حال بارگذاری مقاصد بله...</div>
              <div v-else-if="baleDestinations.length === 0" class="text-xs text-amber-600 bg-amber-50 dark:bg-amber-950/20 rounded-xl p-3 border border-amber-50 dark:border-amber-900/30">
                ⚠️ هیچ مقصد متصلی در بله یافت نشد. ابتدا ربات خود را در بله به گروه یا کانال عضو و مدیر کنید.
              </div>
              <div 
                v-else
                v-for="ch in baleDestinations" 
                :key="ch.id"
                @click="toggleBaleChannel(ch.id)"
                class="flex items-center justify-between p-2.5 rounded-xl hover:bg-muted/40 cursor-pointer transition-colors"
              >
                <div class="flex items-center gap-3">
                  <div class="size-8 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500 shrink-0">
                    <SendIcon class="size-4 rotate-45 -translate-x-0.5 translate-y-0.5" />
                  </div>
                  <div class="flex flex-col text-right">
                    <span class="text-[11px] font-bold text-foreground">{{ ch.label }}</span>
                    <span class="text-[9px] text-muted-foreground mt-0.5 dir-ltr text-right">{{ ch.chat_id }}</span>
                  </div>
                </div>
                <Checkbox :checked="selectedBaleConnections.includes(ch.id)" @update:checked="toggleBaleChannel(ch.id)" @click.stop class="shrink-0" />
              </div>
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
            <span>در حال ذخیره‌سازی...</span>
          </div>
          <div v-else-if="saveSuccess" class="flex items-center gap-2 justify-center text-emerald-600 dark:text-emerald-400">
            <CheckCircle2Icon class="size-4" />
            <span>اتصالات با موفقیت به روز رسانی شد</span>
          </div>
          <div v-else class="flex items-center gap-2 justify-center">
            <SaveIcon class="size-4" />
            <span>ذخیره تنظیمات اتصالات</span>
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
