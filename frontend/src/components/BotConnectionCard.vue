<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { 
  SendIcon, 
  Trash2Icon, 
  Edit2Icon, 
  HelpCircleIcon, 
  ChevronDownIcon, 
  ChevronUpIcon, 
  AlertTriangleIcon, 
  CheckCircle2Icon, 
  XCircleIcon,
  RefreshCwIcon
} from '@lucide/vue'

const props = withDefaults(defineProps<{
  platform: 'telegram' | 'bale'
  initialStatus?: 'disconnected' | 'connecting' | 'connected' | 'conflict'
  initialToken?: string
}>(), {
  initialStatus: 'disconnected',
  initialToken: ''
})

const emit = defineEmits<{
  (e: 'connect', token: string): void
  (e: 'disconnect'): void
  (e: 'edit', token: string): void
  (e: 'update:status', status: 'disconnected' | 'connecting' | 'connected' | 'conflict'): void
}>()

// Local interactive states
const status = ref<'disconnected' | 'connecting' | 'connected' | 'conflict'>(props.initialStatus)
const token = ref(props.initialToken)
const showGuide = ref(false)
const errorMsg = ref('')

// Sync states with props
watch(() => props.initialStatus, (newVal) => {
  status.value = newVal
})

watch(() => props.initialToken, (newVal) => {
  token.value = newVal
})

const platformName = computed(() => props.platform === 'telegram' ? 'تلگرام' : 'بله')

const isConnected = computed(() => status.value === 'connected')
const isConnecting = computed(() => status.value === 'connecting')
const isConflict = computed(() => status.value === 'conflict')
const isDisconnected = computed(() => status.value === 'disconnected')

// Create masked token representation
const maskedToken = computed(() => {
  if (!token.value) return ''
  const t = token.value.trim()
  if (t.length <= 12) return '••••••••••••'
  return `${t.substring(0, 6)}••••••••${t.substring(t.length - 6)}`
})

const handleConnect = () => {
  errorMsg.value = ''
  const cleanToken = token.value.trim()
  
  if (!cleanToken) {
    errorMsg.value = `لطفاً توکن ربات ${platformName.value} خود را وارد کنید.`
    return
  }
  
  // Format check: Bot tokens normally look like 123456789:ABCdefGhIJKlmNo...
  const tokenRegex = /^\d+:[A-Za-z0-9_-]+$/
  if (!tokenRegex.test(cleanToken)) {
    errorMsg.value = 'فرمت توکن نامعتبر است. توکن معتبر شامل شناسه عددی و کلید رمزنگاری است (مثال: 123456:ABC-DEF...).'
    return
  }

  status.value = 'connecting'
  emit('update:status', 'connecting')
  emit('connect', cleanToken)
}

const handleDisconnect = () => {
  status.value = 'disconnected'
  token.value = ''
  errorMsg.value = ''
  emit('update:status', 'disconnected')
  emit('disconnect')
}

const handleEdit = () => {
  status.value = 'disconnected'
  emit('update:status', 'disconnected')
  emit('edit', token.value)
}

const toggleGuide = () => {
  showGuide.value = !showGuide.value
}
</script>

<template>
  <div 
    class="w-full bg-card/45 backdrop-blur-md border border-border/40 rounded-3xl p-5 md:p-6 flex flex-col gap-5 select-none shadow-xs transition-all duration-300 relative overflow-hidden"
    dir="rtl"
  >
    <!-- Background subtle tint decoration -->
    <div 
      :class="[
        'absolute -top-12 -left-12 size-32 rounded-full blur-3xl pointer-events-none transition-all duration-500',
        props.platform === 'telegram' ? 'bg-sky-500/10' : 'bg-emerald-500/10'
      ]" 
    />

    <!-- Header Section (Title & Status Badge) -->
    <div class="flex items-center justify-between border-b border-border/45 pb-4 z-10">
      <div class="flex items-center gap-2.5">
        <!-- Logo Indicator -->
        <div 
          :class="[
            'size-9 rounded-xl flex items-center justify-center text-white font-black text-xs shadow-xs',
            props.platform === 'telegram' ? 'bg-sky-500' : 'bg-emerald-500'
          ]"
        >
          <span class="font-sans text-[10px] tracking-tighter">{{ props.platform === 'telegram' ? 'TG' : 'BL' }}</span>
        </div>
        <div class="flex flex-col text-right">
          <h3 class="text-xs font-black text-foreground">اتصال به {{ platformName }}</h3>
          <span class="text-[9px] text-muted-foreground mt-0.5">اتصال ربات و دریافت نوتیفیکیشن‌ها</span>
        </div>
      </div>

      <!-- Status Badge -->
      <transition name="badge-fade" mode="out-in">
        <Badge 
          v-if="isConnected" 
          variant="secondary" 
          class="bg-emerald-500/10 border-emerald-500/20 text-emerald-650 dark:text-emerald-400 text-[9px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1.5 animate-pulse"
        >
          <span class="size-1.5 rounded-full bg-emerald-500" />
          متصل (Live)
        </Badge>
        <Badge 
          v-else-if="isConnecting" 
          variant="secondary" 
          class="bg-amber-500/10 border-amber-500/20 text-amber-500 text-[9px] font-extrabold px-2 py-0.5 rounded-full flex items-center gap-1.5"
        >
          <RefreshCwIcon class="animate-spin" data-icon="inline-start" />
          در حال اتصال...
        </Badge>
      </transition>
    </div>

    <!-- Active State Alert Banners -->
    <div class="flex flex-col gap-3 z-10">
      <!-- Error Alert -->
      <transition name="alert-slide">
        <div 
          v-if="errorMsg" 
          class="flex items-start gap-2 p-3 bg-destructive/10 text-destructive rounded-xl border border-destructive/20 text-[10.5px] font-bold text-right"
        >
          <AlertTriangleIcon class="size-4 shrink-0 mt-0.5" />
          <p class="leading-relaxed">{{ errorMsg }}</p>
        </div>
      </transition>

      <!-- Conflict/Disconnect Warning Alert -->
      <transition name="alert-slide">
        <div 
          v-if="isConflict" 
          class="flex flex-col gap-2 p-3.5 bg-amber-500/10 text-amber-650 dark:text-amber-400 rounded-xl border border-amber-500/20 text-[10.5px] font-bold text-right"
        >
          <div class="flex items-start gap-2">
            <AlertTriangleIcon class="size-4 shrink-0 mt-0.5 text-amber-500" />
            <p class="leading-relaxed">
              این توکن به دلیل اتصال به حساب یا پلتفرم دیگر قطع شده است. ربات‌ها در هر زمان فقط می‌توانند به یک سیستم متصل باشند.
            </p>
          </div>
          <span class="text-[9.5px] text-muted-foreground/90 font-medium mr-6">
            برای برقراری مجدد ارتباط، از متصل نبودن ربات به پروژه‌های دیگر اطمینان حاصل کرده و دوباره تلاش کنید.
          </span>
        </div>
      </transition>
    </div>

    <!-- Form Section -->
    <div class="form-group-layout z-10">
      <!-- Connected State view -->
      <div v-if="isConnected" class="flex flex-col gap-3 bg-background/30 border border-border/40 p-4 rounded-2xl">
        <div class="flex flex-col gap-1 text-right">
          <Label class="text-[10px] text-muted-foreground font-semibold">توکن ربات فعال:</Label>
          <code class="text-xs font-mono font-bold tracking-wider text-foreground/80 break-all select-all mt-1 select-none">
            {{ maskedToken }}
          </code>
        </div>

        <div class="flex items-center justify-end gap-2 mt-2">
          <Button 
            variant="outline" 
            size="sm" 
            @click="handleEdit" 
            class="h-8.5 text-[11px] font-bold cursor-pointer"
          >
            <Edit2Icon data-icon="inline-start" />
            ویرایش توکن
          </Button>
          <Button 
            variant="outline" 
            size="sm" 
            @click="handleDisconnect" 
            class="h-8.5 text-[11px] font-bold text-destructive hover:bg-destructive/5 hover:text-destructive border-destructive/20 hover:border-destructive/30 cursor-pointer"
          >
            <Trash2Icon data-icon="inline-start" />
            قطع اتصال
          </Button>
        </div>
      </div>

      <!-- Connecting, Disconnected or Conflict State View -->
      <div v-else class="flex flex-col gap-4">
        <div class="flex flex-col gap-1.5">
          <Label for="bot-token-input" class="text-[10.5px] text-muted-foreground font-extrabold">توکن ربات {{ platformName }}:</Label>
          <Input 
            id="bot-token-input" 
            type="text" 
            v-model="token" 
            :disabled="isConnecting"
            placeholder="مثال: 123456789:ABCdefGh..." 
            class="h-10 text-xs font-mono font-bold focus-visible:ring-primary/20 bg-background/25 border-border/60"
            @keyup.enter="handleConnect"
          />
        </div>

        <!-- Action Buttons -->
        <div class="flex items-center justify-between gap-3">
          <!-- Guide Trigger Link -->
          <button 
            @click="toggleGuide"
            class="flex items-center gap-1 text-[10px] font-extrabold text-primary/80 hover:text-primary transition-colors cursor-pointer outline-none select-none border border-transparent"
          >
            <HelpCircleIcon class="size-3.5" />
            <span>نیاز به راهنمایی دارید؟</span>
            <ChevronDownIcon v-if="!showGuide" class="size-3" />
            <ChevronUpIcon v-else class="size-3" />
          </button>

          <Button 
            size="sm" 
            @click="handleConnect" 
            :disabled="isConnecting"
            class="h-9.5 text-xs font-bold px-4 cursor-pointer"
          >
            <RefreshCwIcon v-if="isConnecting" class="animate-spin" data-icon="inline-start" />
            <SendIcon v-else data-icon="inline-start" />
            <span>{{ isConnecting ? 'در حال اتصال...' : (isConflict ? 'اتصال مجدد' : 'بررسی و اتصال') }}</span>
          </Button>
        </div>

        <!-- Interactive Help Guide (Collapsible) -->
        <transition name="guide-slide">
          <div 
            v-if="showGuide" 
            class="bg-muted/40 border border-border/40 rounded-2xl p-4 text-[10.5px] text-muted-foreground leading-relaxed flex flex-col gap-2.5 text-right"
          >
            <h4 class="font-extrabold text-foreground text-[11px] border-r-2 border-primary pr-1.5 leading-none mb-1">
              مراحل دریافت توکن در {{ platformName }}
            </h4>
            
            <ol v-if="props.platform === 'telegram'" class="list-decimal list-inside flex flex-col gap-1.5 pr-1 font-semibold">
              <li>به ربات رسمی <a href="https://t.me/BotFather" target="_blank" class="text-sky-500 hover:underline font-bold">@BotFather</a> در تلگرام پیام دهید.</li>
              <li>دستور <code class="bg-muted px-1 py-0.5 rounded font-mono font-black text-foreground">/newbot</code> را تایپ و ارسال کنید.</li>
              <li>یک نام کاربری مناسب برای ربات خود تعیین کنید (باید با کلمه bot تمام شود).</li>
              <li>توکن ارسالی از طرف BotFather (به شکل <code class="bg-muted px-1.5 py-0.5 rounded font-mono text-[9.5px]">123456:ABC...</code>) را کپی کرده و در کادر بالا وارد کنید.</li>
            </ol>
            
            <ol v-else class="list-decimal list-inside flex flex-col gap-1.5 pr-1 font-semibold">
              <li>به ربات رسمی <code class="bg-muted px-1 py-0.5 rounded font-mono font-black text-foreground">@BotFather</code> در پیام‌رسان بله پیام دهید.</li>
              <li>با استفاده از دکمه‌ها یا دستورات، درخواست ساخت ربات جدید را ارسال کنید.</li>
              <li>نام و شناسه ربات خود را انتخاب و ثبت نمایید.</li>
              <li>توکن رمزنگاری ارائه شده را کپی کرده و در فیلد بالا جایگذاری نمایید.</li>
            </ol>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Trans-fade for status badge */
.badge-fade-enter-active,
.badge-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.badge-fade-enter-from {
  opacity: 0;
  transform: scale(0.95);
}
.badge-fade-leave-to {
  opacity: 0;
  transform: scale(1.05);
}

/* Trans-slide for collapsible user guides */
.guide-slide-enter-active,
.guide-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  max-height: 200px;
}
.guide-slide-enter-from,
.guide-slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  border-color: transparent;
  transform: translateY(-8px);
}

/* Trans-slide for alert banners */
.alert-slide-enter-active,
.alert-slide-leave-active {
  transition: all 0.25s ease;
}
.alert-slide-enter-from,
.alert-slide-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
