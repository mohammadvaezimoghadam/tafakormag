<script setup lang="ts">
import { ref, watch } from 'vue'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Badge } from '@/components/ui/badge'
import { 
  UserIcon, 
  MailIcon, 
  ShieldIcon, 
  AlertTriangleIcon, 
  InboxIcon,
  CheckIcon,
  XCircleIcon,
  ActivityIcon
} from '@lucide/vue'

// Prop definitions
interface UserProfile {
  name: string
  email: string
  role: string
  status: 'active' | 'inactive'
}

const props = withDefaults(defineProps<{
  state?: 'idle' | 'loading' | 'error' | 'empty'
  user?: UserProfile
  errorMessage?: string
}>(), {
  state: 'idle',
  user: () => ({
    name: 'شایان مهدوی',
    email: 'shayan@example.com',
    role: 'طراح رابط کاربری (UI/UX)',
    status: 'active'
  }),
  errorMessage: 'خطا در برقراری ارتباط با سرور. لطفا اتصال اینترنت خود را بررسی کنید.'
})

const emit = defineEmits<{
  (e: 'save', updatedUser: UserProfile): void
  (e: 'statusToggle'): void
}>()

// Reactive state for inline edit
const editedName = ref(props.user.name)
const editedEmail = ref(props.user.email)

// Keep inputs in sync if prop changes
watch(() => props.user, (newUser) => {
  editedName.value = newUser.name
  editedEmail.value = newUser.email
}, { deep: true })

const handleSave = () => {
  emit('save', {
    ...props.user,
    name: editedName.value,
    email: editedEmail.value
  })
}
</script>

<template>
  <div class="w-full bg-card border border-border/80 rounded-lg shadow-sm overflow-hidden transition-all duration-300">
    
    <!-- LOADING STATE -->
    <div v-if="state === 'loading'" class="p-6 flex flex-col gap-6">
      <div class="flex items-center gap-4">
        <!-- Avatar skeleton -->
        <Skeleton class="size-14 rounded-full shrink-0" />
        <div class="flex flex-col gap-2 w-full">
          <!-- Name skeleton -->
          <Skeleton class="h-5 w-2/3" />
          <!-- Role skeleton -->
          <Skeleton class="h-4 w-1/2" />
        </div>
      </div>
      
      <div class="flex flex-col gap-3 pt-4 border-t border-border/40">
        <Skeleton class="h-8 w-full" />
        <Skeleton class="h-8 w-full" />
      </div>

      <div class="flex justify-end gap-2 pt-2">
        <Skeleton class="h-8 w-20" />
        <Skeleton class="h-8 w-24" />
      </div>
    </div>

    <!-- EMPTY STATE -->
    <div v-else-if="state === 'empty'" class="p-6 text-center flex flex-col items-center justify-center gap-4">
      <div class="size-12 rounded-full bg-muted flex items-center justify-center border border-border/40 text-muted-foreground">
        <InboxIcon class="size-6" />
      </div>
      <div class="flex flex-col gap-1">
        <h3 class="text-sm font-semibold text-foreground">اطلاعات کاربری یافت نشد</h3>
        <p class="text-xs text-muted-foreground max-w-xs">هیچ حساب کاربری در این بخش وجود ندارد یا دسترسی شما محدود شده است.</p>
      </div>
      <Button size="sm" variant="outline">بارگذاری مجدد</Button>
    </div>

    <!-- ERROR STATE -->
    <div v-else-if="state === 'error'" class="p-6 flex flex-col gap-4">
      <div class="flex items-start gap-3 p-4 bg-destructive/10 text-destructive rounded-lg border border-destructive/20">
        <AlertTriangleIcon class="size-5 shrink-0 mt-0.5" />
        <div class="flex flex-col gap-1 text-right">
          <h4 class="text-sm font-bold">خطای سیستمی رخ داده است</h4>
          <p class="text-xs opacity-90 leading-relaxed">{{ errorMessage }}</p>
        </div>
      </div>
      <div class="flex justify-end pt-2">
        <Button size="sm" variant="outline" class="flex items-center gap-1">
          <XCircleIcon data-icon="inline-start" />
          بستن پیام
        </Button>
      </div>
    </div>

    <!-- IDLE / SUCCESS STATE (Main Card UI) -->
    <div v-else class="flex flex-col">
      <!-- Card Header / Avatar Banner -->
      <div class="p-6 bg-gradient-to-br from-secondary/40 to-secondary/10 border-b border-border/40">
        <div class="flex flex-col sm:flex-row items-center sm:items-start text-center sm:text-right gap-4">
          <!-- Avatar Icon wrapper -->
          <div class="size-16 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary shadow-sm shrink-0">
            <UserIcon class="size-8" />
          </div>
          
          <div class="flex flex-col gap-1 w-full">
            <div class="flex flex-wrap items-center justify-center sm:justify-start gap-2">
              <h3 class="text-lg font-bold text-foreground">{{ user.name }}</h3>
              
              <!-- Badges -->
              <Badge 
                :class="[
                  'text-[10px] font-semibold px-2 py-0.5 rounded-full border',
                  user.status === 'active' 
                    ? 'bg-green-500/10 border-green-500/20 text-green-600 dark:text-green-400' 
                    : 'bg-muted border-border text-muted-foreground'
                ]"
              >
                {{ user.status === 'active' ? 'فعال' : 'غیرفعال' }}
              </Badge>
            </div>
            
            <p class="text-xs text-muted-foreground flex items-center justify-center sm:justify-start gap-1">
              <ShieldIcon class="size-3.5" />
              {{ user.role }}
            </p>
          </div>
        </div>
      </div>

      <!-- Card Body / Edit Form -->
      <div class="p-6 grid gap-4">
        <div class="flex flex-col gap-1">
          <Label for="card-name" class="text-xs text-muted-foreground">نام و نام خانوادگی:</Label>
          <div class="relative">
            <Input id="card-name" v-model="editedName" class="h-8 text-sm" placeholder="نام کاربر را وارد کنید" />
          </div>
        </div>

        <div class="flex flex-col gap-1">
          <Label for="card-email" class="text-xs text-muted-foreground">آدرس ایمیل:</Label>
          <div class="relative">
            <Input id="card-email" v-model="editedEmail" class="h-8 text-sm" placeholder="ایمیل کاربر را وارد کنید" />
          </div>
        </div>
      </div>

      <!-- Card Footer Actions -->
      <div class="px-6 py-4 bg-muted/30 border-t border-border/40 flex justify-between items-center gap-2">
        <Button 
          size="sm" 
          variant="outline" 
          @click="emit('statusToggle')"
          class="text-xs flex items-center gap-1"
        >
          <ActivityIcon data-icon="inline-start" />
          {{ user.status === 'active' ? 'غیرفعال‌سازی' : 'فعال‌سازی حساب' }}
        </Button>

        <div class="flex gap-2">
          <Button 
            size="sm" 
            @click="handleSave"
            class="text-xs flex items-center gap-1.5"
          >
            <CheckIcon data-icon="inline-start" />
            ذخیره تغییرات
          </Button>
        </div>
      </div>

    </div>

  </div>
</template>
