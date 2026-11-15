<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useLanguageStore } from '@/stores/languageStore'
import { useToastStore } from '@/stores/toastStore'
import {
  createShelfBook,
  extractApiErrorMessage,
  searchCatalogBookTitles,
  updateShelfBook,
} from '@/api/shelf'
import type { ShelfBook, ShelfBookTitle } from '@/types/shelf'
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
import { Badge } from '@/components/ui/badge'
import {
  ImagePlusIcon,
  Loader2Icon,
  SearchIcon,
  XIcon,
} from '@lucide/vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    book?: ShelfBook | null
    defaultIntent?: 'keeping' | 'donation'
    shelfOnly?: boolean
    quickPhysical?: boolean
  }>(),
  {
    book: null,
    defaultIntent: 'keeping',
    shelfOnly: false,
    quickPhysical: false,
  }
)

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  (e: 'saved', book: ShelfBook): void
}>()

const languageStore = useLanguageStore()
const toastStore = useToastStore()

const isEditMode = computed(() => !!props.book)

const form = reactive({
  book_title_id: null as number | null,
  title: '',
  author: '',
  quantity: 1,
})

const coverImageFile = ref<File | null>(null)
const coverPreviewUrl = ref<string | null>(null)
const catalogQuery = ref('')
const catalogResults = ref<ShelfBookTitle[]>([])
const isSearchingCatalog = ref(false)
const selectedCatalogBook = ref<ShelfBookTitle | null>(null)
const isSubmitting = ref(false)
const formError = ref('')

let searchTimer: ReturnType<typeof setTimeout> | null = null

const revokeCoverObjectUrl = () => {
  if (coverPreviewUrl.value?.startsWith('blob:')) {
    URL.revokeObjectURL(coverPreviewUrl.value)
  }
}

const clearSelectedCover = () => {
  revokeCoverObjectUrl()
  coverImageFile.value = null
  coverPreviewUrl.value = props.book?.book_title.cover_image || null
}

const handleCoverFileChange = (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  revokeCoverObjectUrl()
  coverImageFile.value = file
  coverPreviewUrl.value = URL.createObjectURL(file)
  input.value = ''
}

onBeforeUnmount(() => {
  revokeCoverObjectUrl()
})

const resetForm = () => {
  revokeCoverObjectUrl()
  coverImageFile.value = null
  coverPreviewUrl.value = null
  form.book_title_id = null
  form.title = ''
  form.author = ''
  form.quantity = 1
  catalogQuery.value = ''
  catalogResults.value = []
  selectedCatalogBook.value = null
  formError.value = ''
}

watch(
  () => [props.open, props.book] as const,
  ([open, book]) => {
    if (!open) return
    formError.value = ''
    if (book) {
      revokeCoverObjectUrl()
      coverImageFile.value = null
      coverPreviewUrl.value = book.book_title.cover_image || null
      selectedCatalogBook.value = book.book_title
      form.book_title_id = book.book_title.id
      form.title = book.book_title.title
      form.author = book.book_title.author
      form.quantity = Math.max(1, book.quantity || 1)
      catalogQuery.value = ''
      catalogResults.value = []
    } else {
      resetForm()
    }
  },
  { immediate: true }
)

const handleCatalogSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  const q = catalogQuery.value.trim()
  if (q.length < 2) {
    catalogResults.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    isSearchingCatalog.value = true
    try {
      catalogResults.value = await searchCatalogBookTitles(q)
    } catch {
      catalogResults.value = []
    } finally {
      isSearchingCatalog.value = false
    }
  }, 300)
}

const pickCatalogBook = (item: ShelfBookTitle) => {
  selectedCatalogBook.value = item
  form.book_title_id = item.id
  form.title = item.title
  form.author = item.author
  if (item.cover_image && !coverImageFile.value) {
    coverPreviewUrl.value = item.cover_image
  }
  catalogResults.value = []
  catalogQuery.value = ''
}

const clearCatalogSelection = () => {
  selectedCatalogBook.value = null
  form.book_title_id = null
  if (!coverImageFile.value) {
    coverPreviewUrl.value = null
  }
}

const handleSubmit = async () => {
  formError.value = ''
  if (!isEditMode.value && !form.book_title_id) {
    if (!form.title.trim() || !form.author.trim()) {
      formError.value = languageStore.t(
        'لطفاً عنوان کتاب و نام نویسنده را وارد کنید یا کتاب را از فهرست جستجو انتخاب نمایید.',
        'Please enter book title and author, or select from catalog.'
      )
      return
    }
  }

  isSubmitting.value = true
  try {
    let saved: ShelfBook
    if (isEditMode.value && props.book) {
      saved = await updateShelfBook(props.book.id, {
        book_format: 'physical',
        reading_status: 'in_shelf',
        quantity: Math.max(1, form.quantity),
        ...(coverImageFile.value ? { cover_image: coverImageFile.value } : {}),
      })
      toastStore.triggerToast(
        languageStore.t('اطلاعات کتاب در قفسه به‌روزرسانی شد', 'Bookshelf entry updated'),
        'success'
      )
    } else {
      saved = await createShelfBook({
        book_title_id: form.book_title_id,
        title: form.book_title_id ? undefined : form.title.trim(),
        author: form.book_title_id ? undefined : form.author.trim(),
        book_format: 'physical',
        reading_status: 'in_shelf',
        quantity: Math.max(1, form.quantity),
        ...(coverImageFile.value ? { cover_image: coverImageFile.value } : {}),
      })
      toastStore.triggerToast(
        languageStore.t('کتاب به قفسه شما اضافه شد', 'Book added to your shelf'),
        'success'
      )
    }
    emit('saved', saved)
    emit('update:open', false)
  } catch (err) {
    const msg = extractApiErrorMessage(
      err,
      languageStore.t('ثبت کتاب با خطا مواجه شد', 'Failed to save book')
    )
    formError.value = msg
    toastStore.triggerToast(msg, 'error')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent class="sm:max-w-md max-h-[90vh] overflow-y-auto rounded-3xl p-5">
      <DialogHeader class="gap-1 text-start">
        <DialogTitle class="text-base font-extrabold text-foreground">
          {{
            isEditMode
              ? languageStore.t('ویرایش کتاب در قفسه', 'Edit Shelf Book')
              : languageStore.t('ثبت کتاب در قفسه', 'Add Book to Shelf')
          }}
        </DialogTitle>
        <DialogDescription class="text-xs text-muted-foreground">
          {{
            isEditMode
              ? languageStore.t('تعداد و تصویر جلد این کتاب را ویرایش کنید.', 'Update copies and cover image.')
              : languageStore.t('مشخصات کتاب را وارد کنید تا به قفسه شما اضافه شود.', 'Enter book details to add to your shelf.')
          }}
        </DialogDescription>
      </DialogHeader>

      <div class="flex flex-col gap-4 py-2">
        <!-- Edit mode fixed BookTitle banner -->
        <div
          v-if="isEditMode && book"
          class="rounded-2xl border border-border/60 bg-muted/40 p-3 flex flex-col gap-1"
        >
          <div class="text-sm font-bold text-foreground">{{ book.book_title.title }}</div>
          <div class="text-xs text-muted-foreground">
            {{ book.book_title.author }}
          </div>
        </div>

        <!-- Create mode catalog search / manual entry -->
        <template v-else>
          <!-- Autocomplete search -->
          <div class="flex flex-col gap-2">
            <Label class="text-xs font-bold text-muted-foreground">
              {{ languageStore.t('جستجو در فهرست کتاب‌های تفکر (اختیاری)', 'Search Tafakor Catalog (Optional)') }}
            </Label>

            <!-- Selected catalog book badge -->
            <div
              v-if="selectedCatalogBook"
              class="rounded-2xl border border-primary/30 bg-primary/5 p-3 flex items-center justify-between gap-2"
            >
              <div class="flex flex-col gap-0.5 min-w-0">
                <div class="flex items-center gap-1.5">
                  <Badge variant="default" class="text-[10px]">
                    {{ languageStore.t('انتخاب از فهرست', 'Catalog Match') }}
                  </Badge>
                  <span class="text-xs font-bold text-foreground truncate">{{ selectedCatalogBook.title }}</span>
                </div>
                <span class="text-[11px] text-muted-foreground truncate">
                  {{ selectedCatalogBook.author }}
                </span>
              </div>
              <Button type="button" variant="ghost" size="icon-xs" @click="clearCatalogSelection">
                <XIcon class="size-3.5" />
              </Button>
            </div>

            <div v-else class="relative">
              <SearchIcon class="size-3.5 text-muted-foreground absolute top-1/2 -translate-y-1/2 start-3 pointer-events-none" />
              <Input
                v-model="catalogQuery"
                class="ps-8 rounded-2xl bg-muted/20"
                :placeholder="languageStore.t('نام کتاب یا نویسنده را جستجو کنید...', 'Search title or author...')"
                @input="handleCatalogSearchInput"
              />
              <Loader2Icon
                v-if="isSearchingCatalog"
                class="size-3.5 animate-spin text-muted-foreground absolute top-1/2 -translate-y-1/2 end-3"
              />
            </div>

            <!-- Autocomplete results dropdown -->
            <div
              v-if="catalogResults.length > 0 && !selectedCatalogBook"
              class="rounded-2xl border border-border bg-background max-h-40 overflow-y-auto divide-y divide-border/50 shadow-sm"
            >
              <button
                v-for="item in catalogResults"
                :key="item.id"
                type="button"
                class="w-full text-start px-3 py-2.5 hover:bg-muted/60 transition-colors flex flex-col gap-0.5"
                @click="pickCatalogBook(item)"
              >
                <span class="text-xs font-bold text-foreground">{{ item.title }}</span>
                <span class="text-[11px] text-muted-foreground">{{ item.author }}</span>
              </button>
            </div>
          </div>

          <!-- Manual Title & Author Inputs (when not selected from catalog) -->
          <div v-if="!selectedCatalogBook" class="flex flex-col gap-3 rounded-2xl border border-border/50 bg-muted/20 p-3.5">
            <div class="flex flex-col gap-1.5">
              <Label for="shelf-title" class="text-xs font-bold">
                {{ languageStore.t('عنوان کتاب', 'Book Title') }} <span class="text-destructive">*</span>
              </Label>
              <Input
                id="shelf-title"
                v-model="form.title"
                class="rounded-xl"
                :placeholder="languageStore.t('مثلاً: کیمیاگر', 'e.g. The Alchemist')"
              />
            </div>

            <div class="flex flex-col gap-1.5">
              <Label for="shelf-author" class="text-xs font-bold">
                {{ languageStore.t('نویسنده', 'Author') }} <span class="text-destructive">*</span>
              </Label>
              <Input
                id="shelf-author"
                v-model="form.author"
                class="rounded-xl"
                :placeholder="languageStore.t('مثلاً: پائولو کوئیلو', 'e.g. Paulo Coelho')"
              />
            </div>
          </div>
        </template>

        <!-- Shelf Quantity Stepper -->
        <QuantityStepper
          v-model="form.quantity"
          :min="1"
          :max="10000"
          :label="languageStore.t('تعداد موجودی (جلد)', 'Quantity (Copies)')"
          compact
        />

        <!-- Cover Image Uploader -->
        <div class="flex flex-col gap-1.5">
          <Label class="text-xs font-bold">
            {{ languageStore.t('تصویر جلد کتاب (اختیاری)', 'Book Cover Image (Optional)') }}
          </Label>
          <div class="rounded-2xl border border-border/60 bg-muted/25 p-2.5 flex items-center justify-between gap-3">
            <div class="flex items-center gap-2.5 min-w-0">
              <div class="w-11 h-14 rounded-xl overflow-hidden bg-muted/60 border border-border/50 flex items-center justify-center shrink-0">
                <img
                  v-if="coverPreviewUrl"
                  :src="coverPreviewUrl"
                  :alt="form.title || 'cover'"
                  class="size-full object-cover"
                />
                <ImagePlusIcon v-else class="size-4 text-muted-foreground" />
              </div>
              <div class="flex flex-col gap-0.5 min-w-0">
                <span class="text-xs font-semibold text-foreground truncate">
                  {{
                    coverImageFile?.name
                      || (coverPreviewUrl
                        ? languageStore.t('تصویر جلد انتخاب‌شده است', 'Cover image ready')
                        : languageStore.t('بدون تصویر جلد', 'No cover selected'))
                  }}
                </span>
                <span class="text-[10.5px] text-muted-foreground">
                  {{ languageStore.t('فرمت JPG، PNG یا WebP', 'JPG, PNG, or WebP') }}
                </span>
              </div>
            </div>

            <div class="flex items-center gap-1.5 shrink-0">
              <label class="cursor-pointer inline-flex items-center gap-1 px-3 py-1.5 rounded-xl bg-background border border-border/60 text-xs font-semibold hover:bg-muted transition-colors">
                <ImagePlusIcon class="size-3.5" />
                <span>{{ coverPreviewUrl ? languageStore.t('تغییر', 'Change') : languageStore.t('انتخاب تصویر', 'Upload') }}</span>
                <input
                  type="file"
                  accept="image/*"
                  class="sr-only"
                  @change="handleCoverFileChange"
                />
              </label>
              <Button
                v-if="coverImageFile || coverPreviewUrl"
                type="button"
                variant="ghost"
                size="icon-xs"
                @click="clearSelectedCover"
              >
                <XIcon class="size-3.5" />
              </Button>
            </div>
          </div>
        </div>

        <!-- Form Error -->
        <div
          v-if="formError"
          class="rounded-2xl border border-destructive/30 bg-destructive/10 px-3 py-2 text-xs text-destructive font-semibold"
        >
          {{ formError }}
        </div>
      </div>

      <DialogFooter class="gap-2 sm:justify-start">
        <Button type="button" class="rounded-2xl" :disabled="isSubmitting" @click="handleSubmit">
          <Loader2Icon v-if="isSubmitting" data-icon="inline-start" class="animate-spin" />
          <span>
            {{
              isEditMode
                ? languageStore.t('ذخیره تغییرات', 'Save Changes')
                : languageStore.t('افزودن به قفسه', 'Add to Shelf')
            }}
          </span>
        </Button>
        <Button type="button" variant="outline" class="rounded-2xl" :disabled="isSubmitting" @click="emit('update:open', false)">
          {{ languageStore.t('انصراف', 'Cancel') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
