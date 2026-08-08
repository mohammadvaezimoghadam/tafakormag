<script setup lang="ts">
import { ref } from 'vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Checkbox } from '@/components/ui/checkbox'
import { HeartIcon, SparklesIcon } from '@lucide/vue'

const props = defineProps<{
  open: boolean
  campaignTitle?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'submit-donation', amount: number, isAnonymous: boolean): void
}>()

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
    <DialogContent class="sm:max-w-md dir-rtl text-right rounded-2xl p-4 sm:p-6 border-border bg-card text-card-foreground">
      <DialogHeader class="space-y-1.5 pr-0 text-right">
        <DialogTitle class="text-base font-bold flex items-center gap-2 text-foreground">
          <HeartIcon class="size-4.5 text-primary fill-primary/20 shrink-0" />
          <span>مشارکت در پویش مهربانی</span>
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground leading-relaxed line-clamp-2">
          {{ campaignTitle || 'با کمک شما گامی در جهت حل این نیاز برداشته می‌شود.' }}
        </DialogDescription>
      </DialogHeader>

      <div class="space-y-3.5 py-1">
        <!-- Preset Amounts -->
        <div class="space-y-1.5">
          <Label class="text-xs font-semibold text-foreground block">مبلغ پیشنهادی (تومان):</Label>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            <Button
              v-for="amt in presetAmounts"
              :key="amt"
              type="button"
              variant="outline"
              size="sm"
              class="text-xs rounded-lg font-medium transition-colors"
              :class="customAmount === amt ? 'border-primary bg-primary/10 text-primary font-bold' : ''"
              @click="handlePresetSelect(amt)"
            >
              {{ formatCurrency(amt) }}
            </Button>
          </div>
        </div>

        <!-- Custom Input -->
        <div class="space-y-1.5">
          <Label for="amount" class="text-xs font-semibold text-foreground block">مبلغ دلخواه (تومان):</Label>
          <Input
            id="amount"
            type="number"
            v-model.number="customAmount"
            placeholder="مثلا ۵۰,۰۰۰"
            class="text-left dir-ltr font-semibold text-xs sm:text-sm rounded-lg"
          />
        </div>

        <!-- Anonymous Checkbox -->
        <div class="flex items-start gap-2 pt-1">
          <Checkbox id="anonymous" v-model:checked="isAnonymous" class="mt-0.5" />
          <Label for="anonymous" class="text-[11px] sm:text-xs font-medium text-muted-foreground cursor-pointer leading-normal">
            حمایت به صورت کاربر ناشناس (عدم نمایش نام در لیست حامیان)
          </Label>
        </div>
      </div>

      <DialogFooter class="flex flex-col-reverse sm:flex-row gap-2 sm:justify-start pt-2">
        <Button
          type="button"
          class="w-full sm:w-auto font-bold text-xs sm:text-sm gap-1.5 rounded-xl h-9 sm:h-10"
          :disabled="!customAmount || customAmount <= 0"
          @click="handleSubmit"
        >
          <SparklesIcon class="size-3.5" />
          <span>پرداخت و ثبت حمایت</span>
        </Button>
        <DialogClose as-child>
          <Button type="button" variant="ghost" class="w-full sm:w-auto text-xs h-9 sm:h-10 rounded-xl">
            انصراف
          </Button>
        </DialogClose>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
