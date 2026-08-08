<script setup lang="ts">
import { 
  PencilIcon, 
  LinkIcon, 
  Trash2Icon,
  UploadCloudIcon,
  ShieldCheckIcon
} from '@lucide/vue'
import {
  DropdownMenuRoot,
  DropdownMenuPortal,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
} from 'reka-ui'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

const props = withDefaults(defineProps<{
  isOpen: boolean
  triggerRect?: DOMRect | null
  isOwner?: boolean
}>(), {
  isOpen: false,
  triggerRect: null,
  isOwner: false,
})

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'edit'): void
  (e: 'connections'): void
  (e: 'import'): void
  (e: 'admins'): void
  (e: 'delete'): void
}>()

const handleAction = (action: 'edit' | 'connections' | 'delete' | 'import' | 'admins') => {
  if (action === 'edit') {
    emit('edit')
  } else if (action === 'connections') {
    emit('connections')
  } else if (action === 'import') {
    emit('import')
  } else if (action === 'admins') {
    emit('admins')
  } else if (action === 'delete') {
    emit('delete')
  }
  emit('close')
}
</script>

<template>
  <DropdownMenuRoot :open="isOpen" @update:open="(val: boolean) => { if (!val) emit('close') }">
    <DropdownMenuPortal>
      <DropdownMenuContent
        :dir="languageStore.dir"
        :side-offset="8"
        align="end"
        class="bg-popover/90 backdrop-blur-xl border border-border/60 rounded-2xl p-1.5 shadow-xl flex flex-col gap-0.5 w-56 z-50 animate-in fade-in-0 zoom-in-95 duration-100 outline-none select-none"
      >
        <!-- Topic Admins -->
        <DropdownMenuItem
          @click="handleAction('admins')"
          class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all outline-none"
        >
          <span>{{ isOwner ? languageStore.t('مدیریت ادمین‌ها', 'Manage Admins') : languageStore.t('اطلاعات و ادمین‌ها', 'Admins & Info') }}</span>
          <ShieldCheckIcon class="size-3.5 text-primary" />
        </DropdownMenuItem>

        <!-- Edit Topic -->
        <DropdownMenuItem
          v-if="isOwner"
          @click="handleAction('edit')"
          class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all outline-none"
        >
          <span>{{ languageStore.t('ویرایش مشخصات تاپیک', 'Edit Topic Info') }}</span>
          <PencilIcon class="size-3.5 text-muted-foreground" />
        </DropdownMenuItem>

        <!-- Topic Connections -->
        <DropdownMenuItem
          v-if="isOwner"
          @click="handleAction('connections')"
          class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all outline-none"
        >
          <span>{{ languageStore.t('تنظیمات اتصالات تاپیک', 'Topic Connections Settings') }}</span>
          <LinkIcon class="size-3.5 text-muted-foreground" />
        </DropdownMenuItem>

        <!-- Upload Telegram History -->
        <DropdownMenuItem
          v-if="isOwner"
          @click="handleAction('import')"
          class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-foreground hover:bg-secondary/60 flex items-center justify-between cursor-pointer transition-all outline-none"
        >
          <span>{{ languageStore.t('آپلود تاریخچه تلگرام', 'Upload Telegram History') }}</span>
          <UploadCloudIcon class="size-3.5 text-muted-foreground" />
        </DropdownMenuItem>

        <!-- Divider -->
        <DropdownMenuSeparator v-if="isOwner" class="h-px bg-border/40 my-1" />

        <!-- Delete Topic -->
        <DropdownMenuItem
          v-if="isOwner"
          @click="handleAction('delete')"
          class="w-full text-start px-3 py-2 text-xs font-bold rounded-xl text-destructive hover:bg-destructive/10 flex items-center justify-between cursor-pointer transition-all outline-none"
        >
          <span>{{ languageStore.t('حذف تاپیک', 'Delete Topic') }}</span>
          <Trash2Icon class="size-3.5 text-destructive" />
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>
