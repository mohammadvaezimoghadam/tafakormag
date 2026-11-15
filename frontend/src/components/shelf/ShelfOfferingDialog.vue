<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import {
  extractApiErrorMessage,
  listMarketplaceCategories,
  publishShelfBookListing,
} from '@/api/shelf'
import type { DonationMethod, MarketplaceCategory, ShelfBook, ShippingPayer } from '@/types/shelf'
import DonationOptionsSelector from './DonationOptionsSelector.vue'
import QuantityStepper from './QuantityStepper.vue'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { HandHeartIcon, Loader2Icon, TagIcon } from '@lucide/vue'

type OfferingMode = 'donation' | 'sale'

const props = defineProps<{
  open: boolean
  book: ShelfBook | null
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'updated', book: ShelfBook): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()

const CATEGORY_AUTO = '__auto__'
const STATION_NONE = '__none__'

const mode = ref<OfferingMode>('donation')
const form = reactive({
  donation_methods: ['in_person'] as DonationMethod[],
  station_id: STATION_NONE,
  deposit_now: false,
  shipping_payer: 'recipient' as ShippingPayer,
  price: '',
  stock: 1,
  category_id: CATEGORY_AUTO,
  description: '',
})

const maxBookQuantity = computed(() => Math.max(1, props.book?.quantity ?? 1))

const categories = ref<MarketplaceCategory[]>([])
const isSubmitting = ref(false)
const formError = ref('')

const flatCategories = computed(() => {
  const result: { id: number; label: string }[] = []
  for (const cat of categories.value) {
    result.push({ id: cat.id, label: cat.name })
    if (cat.children?.length) {
      for (const child of cat.children) {
        result.push({ id: child.id, label: `${cat.name} / ${child.name}` })
      }
    }
  }
  return result
})

const isDigital = computed(() => props.book?.book_format === 'digital')

onMounted(async () => {
  try {
    categories.value = await listMarketplaceCategories()
  } catch {
    categories.value = []
  }
})

watch(
  () => [props.open, props.book] as const,
  ([open, book]) => {
    if (!open || !book) return
    formError.value = ''
    mode.value = book.disposition === 'for_sale' ? 'sale' : 'donation'
    const existingMethods = book.donation_methods?.length
      ? book.donation_methods
      : book.book_format === 'digital'
        ? (['digital'] as DonationMethod[])
        : (['in_person'] as DonationMethod[])
    form.donation_methods = [...existingMethods]
    const stationId = book.marketplace_item_summary?.book_station_id ?? book.preferred_station_summary?.id
    form.station_id = stationId ? String(stationId) : STATION_NONE
    form.deposit_now = book.physical_copy_summary?.status === 'in_station'
    form.shipping_payer = book.shipping_payer || 'recipient'
    form.price = book.marketplace_item_summary?.deal_type === 'sale'
      ? String(book.marketplace_item_summary.price || '')
      : ''
    const qtyLimit = Math.max(1, book.quantity ?? 1)
    form.stock = Math.min(qtyLimit, Math.max(1, book.marketplace_item_summary?.stock ?? 1))
    form.category_id = book.marketplace_item_summary?.category
      ? String(book.marketplace_item_summary.category)
      : CATEGORY_AUTO
    form.description = book.book_title.description || ''
  },
  { immediate: true }
)

const handleSubmit = async () => {
  if (!props.book) return
  formError.value = ''

  if (mode.value === 'sale') {
    const parsedPrice = Number(form.price)
    if (!Number.isFinite(parsedPrice) || parsedPrice <= 0) {
      formError.value = languageStore.t(
        'برای عرضه به صورت فروش، لطفاً مبلغ معتبر (بیشتر از صفر) وارد کنید.',
        'Please enter a valid positive price for a sale listing.'
      )
      return
    }
  }

  isSubmitting.value = true
  try {
    const resolvedDonationMethods: DonationMethod[] = isDigital.value
      ? ['digital']
      : form.donation_methods.filter((m) => m !== 'digital')

    const updated = await publishShelfBookListing(props.book.id, {
      deal_type: mode.value,
      price: mode.value === 'sale' ? Number(form.price) : 0,
      stock: Math.min(maxBookQuantity.value, Math.max(1, Math.floor(form.stock || 1))),
      donation_methods:
        mode.value === 'donation'
          ? (resolvedDonationMethods.length ? resolvedDonationMethods : ['in_person'])
          : [],
      station_id:
        mode.value === 'donation' && !isDigital.value && form.station_id !== STATION_NONE
          ? Number(form.station_id)
          : null,
      deposit_now:
        mode.value === 'donation' &&
        !isDigital.value &&
        resolvedDonationMethods.includes('station') &&
        form.station_id !== STATION_NONE &&
        form.deposit_now,
      shipping_payer: form.shipping_payer,
      category_id: form.category_id === CATEGORY_AUTO ? null : Number(form.category_id),
      description: form.description.trim(),
      digital_file_key: isDigital.value ? props.book.digital_reference || '' : '',
    })

    const shortCode = updated.physical_copy_summary?.short_code
    toastStore.triggerToast(
      mode.value === 'donation'
        ? shortCode && updated.donation_methods.includes('in_person')
          ? languageStore.t(
              `کتاب با کد گردش ${shortCode} در لیست اهدای کتاب منتشر شد`,
              `Published for donation (QR: ${shortCode})`
            )
          : languageStore.t('شرایط اهدای کتاب با موفقیت ذخیره و منتشر شد', 'Book published for donation')
        : languageStore.t('آگهی فروش کتاب در بازارچه منتشر شد', 'Book published for sale'),
      'success'
    )
    emit('updated', updated)
    emit('update:open', false)
  } catch (err) {
    const msg = extractApiErrorMessage(
      err,
      languageStore.t('تغییر وضعیت عرضه با خطا مواجه شد', 'Failed to update offering status')
    )
    formError.value = msg
    toastStore.triggerToast(msg, 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="emit('update:open', $event)">
    <DialogContent class="sm:max-w-[520px] max-h-[90vh] overflow-y-auto bg-card border-border/60 rounded-3xl">
      <DialogHeader class="text-start">
        <DialogTitle class="text-base font-extrabold text-foreground">
          {{ languageStore.t('اهدا یا فروش کتاب', 'Donate or Sell Book') }}
        </DialogTitle>
        <DialogDescription v-if="book" class="text-xs text-muted-foreground">
          {{ book.book_title.title }} — {{ book.book_title.author }}
        </DialogDescription>
      </DialogHeader>

      <div class="flex flex-col gap-4 py-1">
        <!-- Mode selector (Donation vs Sale) -->
        <div class="grid grid-cols-2 gap-2">
          <Button
            type="button"
            :variant="mode === 'donation' ? 'default' : 'outline'"
            class="justify-center rounded-2xl text-xs h-10"
            @click="mode = 'donation'"
          >
            <HandHeartIcon data-icon="inline-start" />
            <span>{{ languageStore.t('اهدای رایگان (تعیین نوع اهدا)', 'Donate (Choose Method)') }}</span>
          </Button>
          <Button
            type="button"
            :variant="mode === 'sale' ? 'default' : 'outline'"
            class="justify-center rounded-2xl text-xs h-10"
            @click="mode = 'sale'"
          >
            <TagIcon data-icon="inline-start" />
            <span>{{ languageStore.t('فروش در بازارچه', 'Sell in Marketplace') }}</span>
          </Button>
        </div>

        <!-- Donation Mode (Handover Types, Station, Postal Payer) -->
        <div v-if="mode === 'donation'" class="rounded-2xl border border-border/50 bg-muted/20 p-3 flex flex-col gap-3">
          <QuantityStepper
            v-model="form.stock"
            :min="1"
            :max="maxBookQuantity"
            :label="languageStore.t('تعداد جلد برای اهدا', 'Copies to Donate')"
            :hint="languageStore.t(`از ${languageStore.n(maxBookQuantity)} جلد در قفسه`, `of ${maxBookQuantity} in shelf`)"
            compact
          />

          <DonationOptionsSelector
            :book-format="isDigital ? 'digital' : 'physical'"
            :categories="flatCategories"
            :textarea-mode="true"
            v-model:donation-methods="form.donation_methods"
            v-model:station-id="form.station_id"
            v-model:deposit-now="form.deposit_now"
            v-model:shipping-payer="form.shipping_payer"
            v-model:category-id="form.category_id"
            v-model:description="form.description"
          />
        </div>

        <!-- Sale Options -->
        <div v-else class="flex flex-col gap-3 rounded-2xl border border-border/50 bg-muted/20 p-3">
          <QuantityStepper
            v-model="form.stock"
            :min="1"
            :max="maxBookQuantity"
            :label="languageStore.t('تعداد جلد برای فروش', 'Copies for Sale')"
            :hint="languageStore.t(`از ${languageStore.n(maxBookQuantity)} جلد در قفسه`, `of ${maxBookQuantity} in shelf`)"
            compact
          />
          <div class="flex flex-col gap-1.5">
            <Label for="offering-price" class="text-xs font-bold">
              {{ languageStore.t('قیمت فروش (تومان)', 'Price (Toman)') }} <span class="text-destructive">*</span>
            </Label>
            <Input
              id="offering-price"
              v-model="form.price"
              type="number"
              min="1"
              dir="ltr"
              :placeholder="languageStore.t('مثلاً: 150000', 'e.g. 150000')"
            />
          </div>

          <div v-if="flatCategories.length > 0" class="flex flex-col gap-1.5">
            <Label class="text-xs font-bold">
              {{ languageStore.t('دسته‌بندی بازارچه (اختیاری)', 'Category (Optional)') }}
            </Label>
            <Select v-model="form.category_id">
              <SelectTrigger class="rounded-2xl bg-input/50 border-transparent text-xs font-semibold">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  <SelectItem :value="CATEGORY_AUTO">
                    {{ languageStore.t('انتخاب خودکار دسته کتاب', 'Auto-select default') }}
                  </SelectItem>
                  <SelectItem
                    v-for="cat in flatCategories"
                    :key="cat.id"
                    :value="String(cat.id)"
                  >
                    {{ cat.label }}
                  </SelectItem>
                </SelectGroup>
              </SelectContent>
            </Select>
          </div>

          <div class="flex flex-col gap-1.5">
            <Label for="offering-desc" class="text-xs font-bold">
              {{ languageStore.t('توضیحات آگهی (اختیاری)', 'Listing Description (Optional)') }}
            </Label>
            <Textarea
              id="offering-desc"
              v-model="form.description"
              rows="2"
              :placeholder="languageStore.t('توضیحات تکمیلی درباره وضعیت نسخه یا تحویل...', 'Condition notes or handover details...')"
            />
          </div>
        </div>

        <div
          v-if="formError"
          class="rounded-2xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive font-semibold"
        >
          {{ formError }}
        </div>
      </div>

      <DialogFooter class="gap-2 sm:justify-start">
        <Button type="button" :disabled="isSubmitting" @click="handleSubmit">
          <Loader2Icon v-if="isSubmitting" data-icon="inline-start" class="animate-spin" />
          <span>
            {{
              mode === 'donation'
                ? languageStore.t('ثبت و انتشار برای اهدا', 'Publish Donation')
                : languageStore.t('انتشار آگهی فروش', 'Publish Sale')
            }}
          </span>
        </Button>
        <Button type="button" variant="outline" :disabled="isSubmitting" @click="emit('update:open', false)">
          {{ languageStore.t('انصراف', 'Cancel') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

