<script setup lang="ts">
import { ref } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import { HeartIcon, CreditCardIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const props = defineProps<{
  open: boolean
  campaignTitle?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'submit-donation', amount: number, isAnonymous: boolean): void
}>()

const languageStore = useLanguageStore()
const customAmount = ref<number | undefined>(50000)
const presetAmounts = [20000, 50000, 100000, 500000]
const isAnonymous = ref(false)

const formatCurrency = (val: number): string => {
  return new Intl.NumberFormat('fa-IR').format(val)
}

const handlePresetSelect = (amt: number) => {
  customAmount.value = amt
}

const handleSubmit = () => {
  if (customAmount.value && customAmount.value > 0) {
    emit('submit-donation', customAmount.value, isAnonymous.value)
    emit('update:open', false)
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent 
      class="max-w-[calc(100%-2rem)] sm:max-w-md rounded-2xl sm:rounded-3xl p-4 sm:p-5 font-sans text-start border border-border/70 bg-card text-card-foreground shadow-2xl"
      :dir="languageStore.dir"
    >
      <DialogHeader class="flex flex-col gap-1 text-start">
        <DialogTitle class="text-xs sm:text-[13px] font-bold flex items-center gap-2 text-foreground">
          <div class="size-7 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
            <HeartIcon class="size-3.5 fill-primary/20" />
          </div>
          <span>{{ languageStore.t('مشارکت در پویش مهربانی', 'Support Kindness Campaign') }}</span>
        </DialogTitle>
        <DialogDescription class="text-[11px] text-muted-foreground leading-relaxed line-clamp-2">
          {{ campaignTitle || languageStore.t('با کمک شما گامی در جهت حل این نیاز برداشته می‌شود.', 'Your contribution helps fulfill this urgent community need.') }}
        </DialogDescription>
      </DialogHeader>

      <div class="flex flex-col gap-3 py-1">
        <!-- Preset Amounts using ToggleGroup -->
        <div class="flex flex-col gap-1.5">
          <Label class="text-[11px] font-bold text-foreground">
            {{ languageStore.t('مبالغ پیشنهادی سریع (تومان)', 'Suggested preset amounts (Tomans)') }}
          </Label>
          <ToggleGroup 
            type="single" 
            :spacing="2"
            :model-value="customAmount ? String(customAmount) : ''"
            @update:model-value="(val) => handlePresetSelect(val ? Number(val) : 0)"
            class="grid grid-cols-2 sm:grid-cols-4 gap-1.5"
          >
            <ToggleGroupItem
              v-for="amt in presetAmounts"
              :key="amt"
              :value="String(amt)"
              size="sm"
              class="text-[11px] !rounded-full rounded-full font-medium border border-border/60 transition-all cursor-pointer data-[state=on]:border-primary data-[state=on]:bg-primary/10 data-[state=on]:text-primary data-[state=on]:font-bold data-[state=on]:shadow-xs hover:border-primary/40 h-7.5 px-2"
            >
              {{ formatCurrency(amt) }}
            </ToggleGroupItem>
          </ToggleGroup>
        </div>

        <!-- Custom Input -->
        <div class="flex flex-col gap-1.5">
          <Label for="donation-custom-amount" class="text-[11px] font-bold text-foreground">
            {{ languageStore.t('مبلغ دلخواه پرداختی', 'Custom Donation Amount') }}
          </Label>
          <div class="relative">
            <Input
              id="donation-custom-amount"
              type="number"
              v-model.number="customAmount"
              :placeholder="languageStore.t('مثلا ۵۰,۰۰۰', 'e.g. 50,000')"
              class="h-8.5 text-xs font-bold border-border/70 pr-3 pl-12 text-start placeholder:text-start tracking-normal focus-visible:ring-primary/20 rounded-xl"
            />
            <span class="absolute left-2.5 top-1/2 -translate-y-1/2 text-[10.5px] font-bold text-muted-foreground select-none pointer-events-none">
              تومان
            </span>
          </div>
        </div>

        <!-- Anonymous Checkbox -->
        <div class="flex items-center gap-2 p-2.5 rounded-xl bg-muted/30 border border-border/40 cursor-pointer" @click="isAnonymous = !isAnonymous">
          <Checkbox 
            id="anonymous" 
            :checked="isAnonymous"
            @update:checked="(val) => isAnonymous = !!val"
            class="size-3.5"
            @click.stop
          />
          <Label for="anonymous" class="text-[10.5px] font-medium text-muted-foreground cursor-pointer select-none leading-normal">
            {{ languageStore.t('حمایت به صورت کاربر ناشناس (عدم نمایش نام در لیست حامیان)', 'Donate anonymously (hide identity in donor list)') }}
          </Label>
        </div>
      </div>

      <DialogFooter class="flex flex-col sm:flex-row gap-2 sm:justify-end pt-1">
        <Button
          type="button"
          class="w-full font-bold text-xs gap-1.5 rounded-xl h-8.5 shadow-sm active:scale-95 transition-all cursor-pointer"
          :disabled="!customAmount || customAmount <= 0"
          @click="handleSubmit"
        >
          <CreditCardIcon class="size-3.5" />
          <span>{{ languageStore.t('پرداخت و ثبت حمایت', 'Proceed to Payment') }}</span>
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
