<script setup lang="ts">
import { 
  XIcon, 
  Trash2Icon, 
  ShoppingBagIcon, 
  PlusIcon, 
  MinusIcon, 
  ArrowLeftIcon,
  CheckCircle2Icon
} from '@lucide/vue'
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/dialog'
import { useStoreCatalog } from '@/composables/useStoreCatalog'
import { useToastStore } from '@/stores/toastStore'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
}>()

const { 
  cartItems, 
  cartCount, 
  cartTotalAmount, 
  removeFromCart, 
  updateCartQuantity, 
  clearCart, 
  formatToman 
} = useStoreCatalog()

const toastStore = useToastStore()

const handleCheckout = () => {
  toastStore.triggerToast('سفارش شما با موفقیت ثبت اولیه شد. درگاه پرداخت در مرحله نهایی است.', 'success')
  clearCart()
  emit('update:open', false)
}
</script>

<template>
  <Dialog :open="open" @update:open="(val) => emit('update:open', val)">
    <DialogContent 
      :show-close-button="false"
      class="max-w-[460px] p-0 overflow-hidden rounded-3xl bg-card border-border/80 shadow-2xl flex flex-col max-h-[85vh]"
    >
      <DialogTitle class="sr-only">سبد خرید فروشگاه تفکر</DialogTitle>
      <DialogDescription class="sr-only">مشاهده اقلام انتخابی و تسویه حساب</DialogDescription>

      <!-- Header -->
      <div class="px-5 py-4 border-b border-border/60 flex items-center justify-between bg-muted/20 shrink-0">
        <div class="flex items-center gap-2">
          <div class="size-8 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
            <ShoppingBagIcon class="size-4" />
          </div>
          <div class="flex flex-col text-start">
            <span class="text-sm font-black text-foreground">سبد خرید شما</span>
            <span class="text-[10px] text-muted-foreground">{{ cartCount }} قلم کالا انتخاب شده</span>
          </div>
        </div>

        <div class="flex items-center gap-1.5">
          <button 
            v-if="cartItems.length > 0"
            @click="clearCart"
            class="text-[11px] font-semibold text-muted-foreground hover:text-destructive px-2 py-1 rounded-lg transition-colors cursor-pointer"
          >
            خالی کردن
          </button>
          <button 
            @click="emit('update:open', false)"
            class="size-8 rounded-full bg-secondary flex items-center justify-center hover:opacity-100 transition-opacity text-foreground cursor-pointer"
            title="بستن"
          >
            <XIcon class="size-4" />
          </button>
        </div>
      </div>

      <!-- Items List -->
      <div class="p-5 overflow-y-auto flex-1 flex flex-col gap-3 font-sans scrollbar-none no-scrollbar">
        <!-- Empty State -->
        <div 
          v-if="cartItems.length === 0"
          class="flex flex-col items-center justify-center py-12 text-center text-muted-foreground gap-3"
        >
          <div class="size-16 rounded-2xl bg-muted/40 flex items-center justify-center text-muted-foreground/40">
            <ShoppingBagIcon class="size-8 stroke-[1.5]" />
          </div>
          <span class="text-xs font-bold text-foreground">سبد خرید شما در حال حاضر خالی است</span>
          <span class="text-[11px] max-w-[240px]">کتاب‌ها و محصولات فرهنگی مورد علاقه خود را انتخاب کنید.</span>
        </div>

        <!-- Items Cards -->
        <div 
          v-for="ci in cartItems" 
          :key="ci.item.id"
          class="flex items-center gap-3 p-2.5 rounded-2xl bg-muted/20 border border-border/50 text-start"
        >
          <!-- Thumbnail -->
          <img 
            :src="ci.item.cover_image || ci.item.images?.[0]?.image_url || ''" 
            :alt="ci.item.title"
            class="size-16 rounded-xl object-cover shrink-0 bg-muted/60"
          />

          <!-- Info -->
          <div class="flex-1 min-w-0 flex flex-col justify-between py-0.5">
            <span class="text-xs font-bold text-foreground truncate">
              {{ ci.item.title }}
            </span>
            <span class="text-[10px] text-muted-foreground mt-0.5">
              {{ ci.item.category_name }}
            </span>
            <div class="flex items-baseline gap-1 mt-1">
              <span v-if="ci.item.deal_type === 'donation'" class="text-xs font-bold text-foreground">
                رایگان (اهدایی)
              </span>
              <template v-else>
                <span class="text-xs font-black text-foreground">
                  {{ formatToman(ci.item.effective_price * ci.quantity) }}
                </span>
                <span class="text-[9px] text-muted-foreground">تومان</span>
              </template>
            </div>
          </div>

          <!-- Quantity Stepper -->
          <div class="flex items-center bg-background rounded-xl border border-border/60 p-0.5 shrink-0">
            <button 
              @click="updateCartQuantity(ci.item.id, ci.quantity + 1)"
              :disabled="!ci.item.is_unlimited_stock && ci.quantity >= ci.item.stock"
              class="size-6 rounded-lg flex items-center justify-center hover:bg-muted text-foreground disabled:opacity-30 cursor-pointer"
            >
              <PlusIcon class="size-3" />
            </button>
            <span class="w-5 text-center text-xs font-bold">{{ ci.quantity }}</span>
            <button 
              @click="updateCartQuantity(ci.item.id, ci.quantity - 1)"
              class="size-6 rounded-lg flex items-center justify-center hover:bg-muted text-foreground cursor-pointer"
            >
              <Trash2Icon v-if="ci.quantity === 1" class="size-3 text-destructive" />
              <MinusIcon v-else class="size-3" />
            </button>
          </div>
        </div>
      </div>

      <!-- Footer Checkout Summary -->
      <div 
        v-if="cartItems.length > 0"
        class="p-4 border-t border-border/60 bg-muted/10 flex flex-col gap-3 shrink-0"
      >
        <div class="flex items-center justify-between text-xs">
          <span class="text-muted-foreground">مبلغ نهایی محصولات:</span>
          <div class="flex items-baseline gap-1">
            <span class="text-base font-black text-foreground">{{ formatToman(cartTotalAmount) }}</span>
            <span class="text-[10px] text-muted-foreground">تومان</span>
          </div>
        </div>

        <button
          @click="handleCheckout"
          class="w-full py-3 rounded-2xl bg-primary text-primary-foreground text-xs font-bold flex items-center justify-center gap-2 hover:bg-primary/95 active:scale-[0.99] transition-all shadow-md cursor-pointer"
        >
          <CheckCircle2Icon class="size-4" />
          <span>تکمیل و نهایی‌سازی سفارش</span>
        </button>
      </div>

    </DialogContent>
  </Dialog>
</template>

<style scoped>
.scrollbar-none,
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
.scrollbar-none::-webkit-scrollbar,
.no-scrollbar::-webkit-scrollbar {
  display: none;
}
</style>
