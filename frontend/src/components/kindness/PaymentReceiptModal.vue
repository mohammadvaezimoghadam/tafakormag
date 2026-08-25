<script setup lang="ts">
import { computed } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { useLanguageStore } from '@/stores/languageStore'
import { CheckCircle2Icon } from '@lucide/vue'

const props = withDefaults(defineProps<{
  open?: boolean
  amount?: number
  refId?: string
  authority?: string
  campaignTitle?: string
}>(), {
  open: false,
  amount: undefined,
  refId: '',
  authority: '',
  campaignTitle: ''
})

const emit = defineEmits<{
  'update:open': [val: boolean]
  'close': []
  'view-campaign': []
}>()

const languageStore = useLanguageStore()

const formattedAmount = computed(() => {
  if (!props.amount) return '۰'
  return new Intl.NumberFormat('fa-IR').format(props.amount)
})

const handleClose = () => {
  emit('update:open', false)
  emit('close')
}

const handleViewCampaign = () => {
  emit('update:open', false)
  emit('view-campaign')
}
</script>

<template>
  <Dialog :open="open" @update:open="(val: boolean) => emit('update:open', val)">
    <DialogContent 
      class="max-w-[calc(100%-2rem)] sm:max-w-md rounded-2xl sm:rounded-3xl p-4 sm:p-5 font-sans text-start border border-border/70 bg-card text-card-foreground shadow-2xl"
      :dir="languageStore.dir"
      :show-close-button="false"
    >
      <DialogHeader class="flex flex-col items-center text-center gap-1.5 pb-0.5">
        <div class="size-10 sm:size-11 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/20 shadow-xs">
          <CheckCircle2Icon class="size-5 sm:size-5.5 stroke-[2.5]" />
        </div>
        <DialogTitle class="text-xs sm:text-[13px] font-bold text-foreground">
          {{ languageStore.t('پرداخت با موفقیت انجام شد', 'Payment Successful') }}
        </DialogTitle>
        <DialogDescription class="text-[10.5px] sm:text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
          {{ languageStore.t('مشارکت شما در پویش مهربانی با موفقیت از طریق درگاه زرین‌پال ثبت و تسویه گردید.', 'Your donation was successfully verified and settled via ZarinPal.') }}
        </DialogDescription>
      </DialogHeader>

      <!-- Receipt Details Box -->
      <div class="flex flex-col gap-1 p-2.5 sm:p-3 rounded-xl bg-muted/30 border border-border/40 text-[11px] sm:text-xs my-1">
        <!-- Campaign Title if provided -->
        <div v-if="campaignTitle" class="flex items-center justify-between py-1 border-b border-border/30">
          <span class="text-[10.5px] sm:text-[11px] text-muted-foreground font-medium">{{ languageStore.t('پویش مهربانی:', 'Campaign:') }}</span>
          <span class="font-bold text-foreground text-[11px] sm:text-xs truncate max-w-[180px] sm:max-w-[210px]">{{ campaignTitle }}</span>
        </div>

        <!-- Amount -->
        <div v-if="amount" class="flex items-center justify-between py-1 border-b border-border/30">
          <span class="text-[10.5px] sm:text-[11px] text-muted-foreground font-medium">{{ languageStore.t('مبلغ اهدایی:', 'Donation Amount:') }}</span>
          <span class="font-black text-emerald-600 dark:text-emerald-400 text-xs sm:text-sm">{{ formattedAmount }} {{ languageStore.t('تومان', 'Tomans') }}</span>
        </div>

        <!-- Ref ID -->
        <div v-if="refId" class="flex items-center justify-between py-1 border-b border-border/30">
          <span class="text-[10.5px] sm:text-[11px] text-muted-foreground font-medium">{{ languageStore.t('شماره پیگیری (Ref ID):', 'Reference ID:') }}</span>
          <span class="font-mono font-bold text-foreground text-[10.5px] sm:text-xs dir-ltr select-all">{{ refId }}</span>
        </div>

        <!-- Authority -->
        <div v-if="authority" class="flex items-center justify-between py-1">
          <span class="text-[10.5px] sm:text-[11px] text-muted-foreground font-medium">{{ languageStore.t('شناسه زرین‌پال:', 'ZarinPal Authority:') }}</span>
          <span class="font-mono text-[9.5px] sm:text-[10px] text-muted-foreground truncate max-w-[150px] sm:max-w-[180px] dir-ltr select-all">{{ authority }}</span>
        </div>
      </div>

      <DialogFooter class="flex flex-col sm:flex-row gap-2 sm:justify-end pt-1">
        <Button
          type="button"
          class="w-full font-bold text-xs gap-1.5 rounded-xl h-8 sm:h-8.5 shadow-sm active:scale-95 transition-all cursor-pointer bg-emerald-600 hover:bg-emerald-700 text-white"
          @click="handleViewCampaign"
        >
          <CheckCircle2Icon class="size-3.5" />
          <span>{{ languageStore.t('مشاهده پویش و بستن', 'View Campaign & Close') }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
