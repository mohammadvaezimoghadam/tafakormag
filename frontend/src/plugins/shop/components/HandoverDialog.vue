<script setup lang="ts">
import { ref, computed } from 'vue'
import { inspectCopy, claimCopy, confirmHandover } from '../api'
import type { PhysicalCopyItem, TransferItem } from '../types'
import { useToastStore } from '@/stores/toastStore'

const props = defineProps<{
  open: boolean
  initialCode?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'success', transfer: TransferItem): void
  (e: 'view-journey', code: string): void
}>()

const toastStore = useToastStore()
const shortCodeInput = ref(props.initialCode || '')
const inspectedCopy = ref<PhysicalCopyItem | null>(null)
const isLoading = ref(false)
const isSubmitting = ref(false)
const otpInput = ref('')
const recipientNote = ref('')

const handleInspect = async () => {
  if (!shortCodeInput.value.trim()) return
  isLoading.value = true
  try {
    const copy = await inspectCopy(shortCodeInput.value.trim())
    inspectedCopy.value = copy
  } catch (err: any) {
    const msg = err.response?.data?.detail || 'کتابی با این شناسه یافت نشد.'
    toastStore.showToast(msg, 'error')
    inspectedCopy.value = null
  } finally {
    isLoading.value = false
  }
}

const handleClaim = async () => {
  if (!inspectedCopy.value) return
  isSubmitting.value = true
  try {
    const transfer = await claimCopy({
      short_code: inspectedCopy.value.short_code,
      recipient_note: recipientNote.value,
    })
    toastStore.showToast('درخواست دریافت کتاب ثبت شد. در انتظار تایید اهداکننده.', 'success')
    emit('success', transfer)
    emit('update:open', false)
  } catch (err: any) {
    const msg = err.response?.data?.detail || 'خطا در ثبت درخواست دریافت کتاب.'
    toastStore.showToast(msg, 'error')
  } finally {
    isSubmitting.value = false
  }
}

const handleConfirm = async () => {
  if (!inspectedCopy.value?.active_transfer_id) return
  isSubmitting.value = true
  try {
    const transfer = await confirmHandover(inspectedCopy.value.active_transfer_id, {
      otp_code: otpInput.value || undefined,
    })
    toastStore.showToast('انتقال کتاب با موفقیت نهایی و تایید شد.', 'success')
    emit('success', transfer)
    emit('update:open', false)
  } catch (err: any) {
    const msg = err.response?.data?.detail || 'خطا در تایید انتقال کتاب.'
    toastStore.showToast(msg, 'error')
  } finally {
    isSubmitting.value = false
  }
}

const close = () => {
  inspectedCopy.value = null
  shortCodeInput.value = ''
  otpInput.value = ''
  recipientNote.value = ''
  emit('update:open', false)
}
</script>

<template>
  <div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs select-none">
    <div
      class="w-full max-w-md bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-5 shadow-2xl flex flex-col gap-4 text-zinc-900 dark:text-zinc-100"
      dir="rtl"
    >
      <!-- Dialog Header -->
      <div class="flex items-center justify-between pb-3 border-b border-zinc-100 dark:border-zinc-800">
        <div>
          <h3 class="text-sm font-bold">گردش و انتقال حضوری کتاب</h3>
          <p class="text-[11px] text-zinc-500 dark:text-zinc-400">شناسه کتاب را وارد کرده یا بارکد QR را اسکن فرمایید</p>
        </div>
        <button
          @click="close"
          type="button"
          class="w-7 h-7 rounded-lg flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-sm cursor-pointer"
        >
          ✕
        </button>
      </div>

      <!-- Step 1: Input Short Code -->
      <div class="flex gap-2">
        <input
          v-model="shortCodeInput"
          @keyup.enter="handleInspect"
          placeholder="مثال: TK-8492"
          class="flex-1 px-3 py-2 text-xs font-mono rounded-lg border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50 focus:outline-hidden focus:border-zinc-900 dark:focus:border-zinc-400 uppercase tracking-wider"
        />
        <button
          @click="handleInspect"
          :disabled="isLoading || !shortCodeInput.trim()"
          type="button"
          class="px-4 py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-xs font-semibold hover:bg-zinc-800 dark:hover:bg-zinc-200 disabled:opacity-50 transition-colors cursor-pointer"
        >
          {{ isLoading ? 'بررسی...' : 'استعلام' }}
        </button>
      </div>

      <!-- Step 2: Inspected Copy Card -->
      <div v-if="inspectedCopy" class="p-3.5 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-800/40 flex flex-col gap-3">
        <div class="flex items-start justify-between gap-2">
          <div>
            <span class="inline-block text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-200 dark:bg-zinc-700 text-zinc-700 dark:text-zinc-300 mb-1">
              {{ inspectedCopy.short_code }}
            </span>
            <h4 class="text-xs font-bold text-zinc-900 dark:text-zinc-100">
              {{ inspectedCopy.book_title.title }}
            </h4>
            <p class="text-[11px] text-zinc-500">
              اثر {{ inspectedCopy.book_title.author }}
            </p>
          </div>

          <button
            @click="emit('view-journey', inspectedCopy.short_code)"
            type="button"
            class="text-[10px] text-zinc-600 dark:text-zinc-400 hover:underline cursor-pointer"
          >
            مشاهده سفرنامه
          </button>
        </div>

        <!-- Action Branches -->
        <!-- Case A: Recipient scans and wants to claim -->
        <div v-if="inspectedCopy.can_claim" class="flex flex-col gap-2 pt-2 border-t border-zinc-200 dark:border-zinc-700/60">
          <input
            v-model="recipientNote"
            placeholder="یادداشت یا تشکر از اهداکننده (اختیاری)"
            class="w-full px-3 py-1.5 text-[11px] rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-zinc-800 dark:text-zinc-200"
          />
          <button
            @click="handleClaim"
            :disabled="isSubmitting"
            type="button"
            class="w-full py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
          >
            {{ isSubmitting ? 'در حال ثبت...' : 'تایید و دریافت کتاب' }}
          </button>
        </div>

        <!-- Case B: Donor confirming transfer with 1-tap -->
        <div v-else-if="inspectedCopy.is_holder && inspectedCopy.active_transfer_id" class="flex flex-col gap-2 pt-2 border-t border-zinc-200 dark:border-zinc-700/60">
          <p class="text-[11px] text-zinc-600 dark:text-zinc-400">
            درخواست دریافت این کتاب ثبت شده است. با تایید شما کتاب به خواننده بعدی واگذار می‌شود.
          </p>
          <button
            @click="handleConfirm"
            :disabled="isSubmitting"
            type="button"
            class="w-full py-2 rounded-lg bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 text-xs font-bold shadow-xs transition-colors cursor-pointer"
          >
            {{ isSubmitting ? 'در حال نهایی‌سازی...' : 'تایید نهایی انتقال (تک‌تپ)' }}
          </button>
        </div>

        <!-- Case C: Already holder with no active transfer -->
        <div v-else-if="inspectedCopy.is_holder" class="pt-2 text-[11px] text-zinc-500">
          این کتاب در حال حاضر در اختیار شماست.
        </div>
      </div>
    </div>
  </div>
</template>

