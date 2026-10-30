<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { 
  HistoryIcon, 
  CheckIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon, 
  ChevronDownIcon 
} from '@lucide/vue'
import { useLanguageStore } from '@/stores/languageStore'

const languageStore = useLanguageStore()

interface ChangelogSection {
  version: string
  title: string
  changes: string[]
}

const isOpen = ref(false)
const changelogData = ref<ChangelogSection[]>([])
const latestVersion = ref('')
const expandedVersions = ref<Record<string, boolean>>({})

const toggleVersion = (version: string) => {
  expandedVersions.value[version] = !expandedVersions.value[version]
}

const fetchAndParseChangelog = async () => {
  try {
    const response = await fetch('/changelog.md')
    if (!response.ok) throw new Error('Failed to fetch changelog')
    const text = await response.text()
    
    // Parse markdown into sections
    // Split by version headers: ### نسخه X.Y.Z or ### Version X.Y.Z
    const rawSections = text.split(/###\s+(?:نسخه|Version)\s+/i)
    const parsedSections: ChangelogSection[] = []

    // Index 0 contains the title "# تغییرات ...", so we start from index 1
    for (let i = 1; i < Math.min(rawSections.length, 6); i++) {
      const sectionText = rawSections[i]?.trim()
      if (!sectionText) continue
      const lines = sectionText.split('\n')
      
      // Parse header line: "X.Y.Z - عنوان"
      const firstLine = lines[0]
      if (!firstLine) continue
      const headerLine = firstLine.trim()
      const match = headerLine.match(/^([\d\.]+)\s*-\s*(.+)$/)
      
      if (match) {
         const version = match[1]
         const title = match[2]
         const changes: string[] = []

         if (version && title) {
           // Parse list items starting with "-"
           for (let j = 1; j < lines.length; j++) {
             const line = lines[j]?.trim()
             if (line && line.startsWith('-')) {
               // Remove bullet point and format bold text
               const changeText = line.substring(1).trim()
               changes.push(changeText)
             }
           }

           parsedSections.push({ version, title, changes })
         }
      }
    }

    changelogData.value = parsedSections

    // Set the first version (latest) to be open by default, and others to be collapsed
    const initialExpanded: Record<string, boolean> = {}
    parsedSections.forEach((section, idx) => {
      initialExpanded[section.version] = idx === 0
    })
    expandedVersions.value = initialExpanded

    if (parsedSections.length > 0) {
      const firstSection = parsedSections[0]
      if (firstSection) {
        latestVersion.value = firstSection.version
        
        // Check if user has seen this latest version
        const seenVersion = localStorage.getItem('seen_changelog_version')
        if (seenVersion !== latestVersion.value) {
          isOpen.value = true
        }
      }
    }
  } catch (error) {
    console.error('Error fetching or parsing changelog:', error)
  }
}

onMounted(() => {
  fetchAndParseChangelog()
})

const handleConfirm = () => {
  if (latestVersion.value) {
    localStorage.setItem('seen_changelog_version', latestVersion.value)
  }
  isOpen.value = false
}

// Formatting helper for bold markdown text: **bold**: text -> HTML tags
const formatChange = (change: string) => {
  let formatted = change.replace(/\*\*(.*?)\*\*/g, '<strong class="font-extrabold text-foreground text-xs">$1</strong>')
  return formatted
}
</script>

<template>
  <Dialog :open="isOpen" @update:open="(val) => { if (!val) handleConfirm() }">
    <DialogContent 
      :show-close-button="false" 
      class="max-w-[440px] p-0 overflow-hidden flex flex-col rounded-3xl bg-card/95 backdrop-blur-2xl border border-border/80 dark:border-border/60 shadow-[0_20px_50px_rgba(0,0,0,0.2)] text-start" 
      :dir="languageStore.dir"
    >
      
      <!-- Accessibility Description -->
      <DialogDescription class="sr-only">
        {{ languageStore.t('تغییرات و بروزرسانی‌های اخیر پلتفرم تفکر شامل بهبودهای رابط کاربری، سیستم اعلان خطا و تفکیک رنگ‌ها.', 'Recent updates and changes in Tafakor Platform, including UI improvements, error notification systems, and color themes.') }}
      </DialogDescription>

      <!-- Header -->
      <DialogHeader class="px-6 py-5 border-b border-border/40 flex flex-row items-center justify-between bg-gradient-to-br from-primary/10 to-primary/5 space-y-0">
        <div class="flex items-center gap-2.5">
          <div class="size-9 rounded-2xl bg-primary/15 border border-primary/20 flex items-center justify-center text-primary shadow-xs">
            <HistoryIcon class="size-4.5" />
          </div>
          <DialogTitle class="text-xs font-black text-foreground">{{ languageStore.t('آخرین بروزرسانی‌های تفکر', 'Tafakor Latest Updates') }}</DialogTitle>
        </div>
      </DialogHeader>

      <!-- Content (Scrollable List) -->
      <div class="px-6 py-4 max-h-[360px] overflow-y-auto flex flex-col gap-5 scrollbar-none">
        <div 
          v-for="(section, idx) in changelogData" 
          :key="section.version"
          class="flex flex-col gap-2 relative pb-1 ps-3 border-s border-border/60"
        >
          <!-- Timeline point -->
          <div 
            class="absolute top-1.5 size-2 rounded-full border border-background bg-primary start-[-4.5px]"
          />

          <!-- Version Title (Accordion Trigger) -->
          <div 
            @click="toggleVersion(section.version)"
            class="flex items-center justify-between flex-wrap gap-2 cursor-pointer hover:text-primary transition-colors select-none"
          >
            <div class="flex items-center gap-2">
              <span class="text-xs font-black text-foreground">{{ languageStore.t('نسخه', 'Version') }} {{ section.version }}</span>
              <span class="text-[10px] font-bold text-muted-foreground bg-muted/60 px-2 py-0.5 rounded-lg border border-border/40">{{ section.title }}</span>
            </div>
            <ChevronDownIcon 
              class="size-3.5 text-muted-foreground transition-transform duration-200" 
              :class="{ 'rotate-180 text-primary': expandedVersions[section.version] }" 
            />
          </div>

          <!-- Changes List (Accordion Content) -->
          <transition name="accordion-slide">
            <ul 
              v-show="expandedVersions[section.version]" 
              class="flex flex-col gap-1.5 mt-1 overflow-hidden ps-1"
            >
              <li 
                v-for="(change, cIdx) in section.changes" 
                :key="cIdx"
                class="text-[10.5px] text-muted-foreground leading-relaxed flex items-start gap-1.5"
              >
                <component 
                  :is="languageStore.isFa ? ChevronLeftIcon : ChevronRightIcon" 
                  class="size-3 text-primary/60 shrink-0 mt-1" 
                />
                <span v-html="formatChange(change)" />
              </li>
            </ul>
          </transition>
        </div>
      </div>

      <!-- Footer -->
      <DialogFooter class="p-5 border-t border-border/40 bg-muted/20">
        <Button 
          @click="handleConfirm" 
          class="w-full h-10 text-xs font-bold rounded-xl cursor-pointer shadow-sm shadow-primary/10"
        >
          <CheckIcon class="size-4" data-icon="inline-start" />
          {{ languageStore.t('متوجه شدم', 'Got it') }}
        </Button>
      </DialogFooter>

    </DialogContent>
  </Dialog>
</template>

<style scoped>
/* Hide scrollbar for Chrome, Safari and Opera */
.scrollbar-none::-webkit-scrollbar {
  display: none;
}
/* Hide scrollbar for IE, Edge and Firefox */
.scrollbar-none {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

/* Accordion transition animation */
.accordion-slide-enter-active,
.accordion-slide-leave-active {
  transition: all 0.2s ease-in-out;
  max-height: 250px;
}

.accordion-slide-enter-from,
.accordion-slide-leave-to {
  max-height: 0;
  opacity: 0;
}
</style>
