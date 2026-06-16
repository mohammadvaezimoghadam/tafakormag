<template>
  <div class="min-h-screen bg-muted/30 text-foreground flex flex-col items-center justify-center p-6 font-sans antialiased" dir="rtl">
    
    <!-- Background Decorative Olive Blurs -->
    <div class="absolute inset-0 -z-10 overflow-hidden">
      <div class="absolute -top-[40%] -right-[20%] w-[80%] aspect-square rounded-full bg-primary/10 blur-[120px]" />
      <div class="absolute -bottom-[40%] -left-[20%] w-[80%] aspect-square rounded-full bg-primary/15 blur-[120px]" />
    </div>

    <div class="w-full max-w-md flex flex-col gap-8">
      
      <!-- Header Section -->
      <div class="text-center flex flex-col gap-3">
        <div class="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-md shadow-primary/20 self-center">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="w-6 h-6" data-icon="inline-start">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
          </svg>
        </div>
        <div class="flex flex-col gap-1.5">
          <h1 class="text-2xl font-black tracking-tight">ورود به تفکر</h1>
          <p class="text-xs text-muted-foreground">با رعایت کامل قواعد طراحی سیستم و کامپوننت‌های رسمی Shadcn</p>
        </div>
      </div>

      <!-- Main Form Card -->
      <div class="p-6 sm:p-8 rounded-3xl border border-border bg-card shadow-sm flex flex-col gap-6">
        
        <Form :validation-schema="formSchema" @submit="onSubmit" class="flex flex-col gap-5">
          
          <!-- Form Field (No custom divs or manual labels) -->
          <FormField v-slot="{ componentField, errorMessage }" name="mobileNumber">
            <FormItem>
              <FormLabel>شماره موبایل</FormLabel>
              <FormControl>
                <div class="relative">
                  <Input 
                    type="tel"
                    placeholder="۰۹۱۲۳۴۵۶۷۸۹" 
                    v-bind="componentField"
                    class="pr-10 text-left font-mono tracking-widest text-base"
                    :aria-invalid="!!errorMessage"
                  />
                  <div class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="w-4 h-4">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3" />
                    </svg>
                  </div>
                </div>
              </FormControl>
              <FormDescription>
                کد تایید پیامکی به این شماره ارسال خواهد شد.
              </FormDescription>
              <FormMessage />
            </FormItem>
          </FormField>

          <!-- Action Buttons (Using standard Shadcn sizes & variants) -->
          <div class="flex flex-col gap-2 pt-2">
            <Button 
              type="submit"
              variant="default" 
              size="lg"
              class="w-full font-bold shadow-sm"
              :disabled="isSubmitting"
            >
              <span>ارسال کد تایید</span>
            </Button>

            <Button 
              type="button"
              variant="outline" 
              size="lg"
              class="w-full font-semibold"
            >
              <span>ورود با رمز عبور ثابت</span>
            </Button>
          </div>

        </Form>

      </div>

      <!-- Footer Info -->
      <div class="text-center flex flex-col gap-2">
        <p class="text-[11px] text-muted-foreground">با ورود به برنامه، قوانین و مقررات تفکر را می‌پذیرید.</p>
        <div>
          <Button variant="link" size="sm" class="text-xs text-muted-foreground hover:text-foreground p-0 h-auto">
            نیاز به پشتیبانی دارید؟ تماس با ما
          </Button>
        </div>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useForm } from 'vee-validate'
import { toTypedSchema } from '@vee-validate/zod'
import * as z from 'zod'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  Form, 
  FormField, 
  FormItem, 
  FormLabel, 
  FormControl, 
  FormDescription, 
  FormMessage 
} from '@/components/ui/form'

// Strict validation for Iranian mobile numbers using Zod
const formSchema = toTypedSchema(
  z.object({
    mobileNumber: z
      .string()
      .nonempty('وارد کردن شماره موبایل الزامی است.')
      .regex(/^09\d{9}$/, 'شماره موبایل نامعتبر است. نمونه: ۰۹۱۲۳۴۵۶۷۸۹')
  })
)

const { handleSubmit, isSubmitting } = useForm({
  validationSchema: formSchema,
})

const onSubmit = handleSubmit((values) => {
  alert(`کد تایید به شماره ${values.mobileNumber} ارسال شد!`)
})
</script>
