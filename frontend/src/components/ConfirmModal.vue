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
import { AlertTriangleIcon, Trash2Icon, InfoIcon } from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

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
  if (props.variant === 'warning') return 'bg-amber-100 dark:bg-amber-950/40 text-amber-600 dark:text-amber-400'
  if (props.variant === 'info') return 'bg-blue-100 dark:bg-blue-950/40 text-blue-600 dark:text-blue-400'
  return 'bg-red-100 dark:bg-red-950/40 text-red-600 dark:text-red-400'
})

const confirmButtonVariant = computed(() => {
  if (props.variant === 'warning') return 'default'
  if (props.variant === 'info') return 'default'
  return 'destructive'
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
    <DialogContent class="sm:max-w-[425px] overflow-hidden rounded-2xl border border-border/50 bg-background/95 backdrop-blur-lg p-6 shadow-2xl">
      
      <!-- Premium Top Accent Glow -->
      <div 
        class="absolute top-0 left-0 right-0 h-1"
        :class="{
          'bg-red-500': variant === 'destructive',
          'bg-amber-500': variant === 'warning',
          'bg-blue-500': variant === 'info'
        }"
      />

      <div class="flex flex-col items-center text-center space-y-4 pt-2">
        <!-- Icon Badge -->
        <div :class="['p-3 rounded-full', iconBgClass, 'transition-transform duration-300 hover:scale-110']">
          <component :is="iconComponent" class="size-6" />
        </div>

        <DialogHeader class="space-y-2">
          <DialogTitle class="text-base font-extrabold text-foreground tracking-tight">
            {{ title }}
          </DialogTitle>
          <DialogDescription class="text-xs text-muted-foreground/90 leading-relaxed font-medium">
            {{ description }}
          </DialogDescription>
        </DialogHeader>
      </div>

      <!-- Action Buttons -->
      <DialogFooter class="grid grid-cols-2 gap-3 mt-6 sm:justify-start">
        <Button 
          type="button" 
          variant="outline" 
          class="rounded-xl border border-border/60 hover:bg-muted font-bold text-xs h-10 transition-all duration-200" 
          @click="handleCancel"
        >
          {{ defaultCancelText }}
        </Button>
        <Button 
          type="button" 
          :variant="confirmButtonVariant" 
          class="rounded-xl font-bold text-xs h-10 shadow-lg shadow-primary/15 transition-all duration-200 hover:shadow-none" 
          @click="handleConfirm"
        >
          {{ defaultConfirmText }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
