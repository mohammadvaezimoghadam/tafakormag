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
import { AlertTriangleIcon, Trash2Icon, InfoIcon, XIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'
import { cn } from '@/lib/utils'

const languageStore = useLanguageStore()

interface Props {
  isOpen: boolean
  title?: string
  description?: string
  confirmText?: string
  cancelText?: string
  variant?: 'destructive' | 'warning' | 'info'
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  description: '',
  confirmText: '',
  cancelText: '',
  variant: 'destructive'
})

const emit = defineEmits<{
  (e: 'update:isOpen', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

const localIsOpen = computed({
  get: () => props.isOpen,
  set: (val) => emit('update:isOpen', val)
})

const handleConfirm = () => {
  emit('confirm')
  localIsOpen.value = false
}

const handleCancel = () => {
  emit('cancel')
  localIsOpen.value = false
}

// Icon based on variant
const iconComponent = computed(() => {
  if (props.variant === 'warning') return AlertTriangleIcon
  if (props.variant === 'info') return InfoIcon
  return Trash2Icon
})

// Header Icon colors based on variant
const iconBgClass = computed(() => {
  if (props.variant === 'warning') return 'bg-amber-500/10 text-amber-500'
  if (props.variant === 'info') return 'bg-blue-500/10 text-blue-500'
  return 'bg-destructive/10 text-destructive'
})

// Header gradient background based on variant
const headerBgClass = computed(() => {
  if (props.variant === 'warning') return 'bg-gradient-to-br from-amber-500/10 to-amber-500/5'
  if (props.variant === 'info') return 'bg-gradient-to-br from-blue-500/10 to-blue-500/5'
  return 'bg-gradient-to-br from-destructive/10 to-destructive/5'
})

const confirmButtonVariant = computed(() => {
  if (props.variant === 'destructive') return 'destructive'
  return 'default'
})

const defaultConfirmText = computed(() => {
  if (props.confirmText) return props.confirmText
  return languageStore.isFa ? 'تایید و حذف' : 'Confirm & Delete'
})

const defaultCancelText = computed(() => {
  if (props.cancelText) return props.cancelText
  return languageStore.isFa ? 'انصراف' : 'Cancel'
})
</script>

<template>
  <Dialog v-model:open="localIsOpen">
    <DialogContent 
      :show-close-button="false" 
      class="max-w-[380px] p-0 overflow-hidden flex flex-col text-start font-sans" 
      :dir="languageStore.dir"
    >
      <!-- Header -->
      <DialogHeader :class="cn('px-5 py-4 border-b border-border/40 flex flex-row items-center justify-between', headerBgClass)">
        <div class="flex items-center gap-2">
          <div :class="cn('size-8 rounded-full flex items-center justify-center shadow-xs', iconBgClass)">
            <component :is="iconComponent" class="size-4" />
          </div>
          <DialogTitle class="text-xs font-black text-foreground">
            {{ title }}
          </DialogTitle>
        </div>
        
        <button 
          @click="handleCancel"
          class="size-6.5 rounded-lg flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-muted/80 transition-colors cursor-pointer border-0 outline-none"
          :title="defaultCancelText"
        >
          <XIcon class="size-3.5" />
        </button>
      </DialogHeader>

      <!-- Body -->
      <div class="p-5">
        <DialogDescription class="text-xs text-muted-foreground leading-relaxed font-medium block">
          {{ description }}
        </DialogDescription>
      </div>

      <!-- Footer Actions -->
      <DialogFooter class="px-5 py-3.5 bg-muted/20 border-t border-border/40 flex justify-end gap-2">
        <Button 
          type="button" 
          variant="outline" 
          size="sm" 
          class="text-xs font-bold rounded-2xl cursor-pointer" 
          @click="handleCancel"
        >
          {{ defaultCancelText }}
        </Button>
        <Button 
          type="button" 
          :variant="confirmButtonVariant" 
          size="sm" 
          class="text-xs font-bold rounded-2xl cursor-pointer" 
          @click="handleConfirm"
        >
          <component :is="iconComponent" data-icon="inline-start" />
          {{ defaultConfirmText }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>

