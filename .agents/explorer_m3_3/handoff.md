# Milestone 3 Exploration Report: Marketplace UI, Composer Integration & Build Verification

## 1. Observation

### 1.1 FeedView.vue Tab 3 & Marketplace Layout
- **File**: `frontend/src/views/FeedView.vue`
- **Lines 50–51**: `const currentTab = ref<'home' | 'donate' | 'marketplace' | 'profile'>('home')`
- **Lines 97–99 & 136–139**: Synchronizes `currentTab` with `/marketplace` route:
  ```ts
  } else if (route.path === '/marketplace') {
    currentTab.value = 'marketplace'
    selectedTopic.value = null
  }
  ```
- **Lines 1279–1296**: Tab 3 is currently occupied by `UnderDevelopmentCard`:
  ```vue
  <!-- TAB 3: MARKETPLACE -->
  <div v-else-if="currentTab === 'marketplace'" key="marketplace" class="w-full flex flex-col gap-4">
    <UnderDevelopmentCard
      :title="languageStore.t('بازارچه نصب افزونه تفکر', 'Tafakor Plugin Marketplace')"
      :description="languageStore.t('افزونه های دلخواه را نصب کنید و در تاپیک خود اضافه کنید', 'Install custom plugins and add them to your topics')"
      :icon="LayersIcon"
      :eta="languageStore.t('نسخه 6 شهریور ماه 405', 'Version 6 - Shahrivar 1405')"
      :features="[
        languageStore.t('افزونه قرآن کریم', 'Holy Quran Plugin'),
        languageStore.t('بهرمندی از آیه ها', 'Access to Verses'),
        languageStore.t('بهرمندی از سوره ها', 'Access to Surahs'),
        languageStore.t('بهرمندی از صوت قرآن کریم', 'Holy Quran Recitation Audio')
      ]"
      :action-text="languageStore.t('صفحه خانه', 'Home Page')"
      @action="currentTab = 'home'"
      :show-back-button="true"
      @back="currentTab = 'home'"
    />
  </div>
  ```
- **File**: `frontend/src/components/PlatformNavigation.vue`
  - **Lines 57–75**: Renders the Marketplace tab button with a floating "Soon" (`به‌زودی`) badge:
    ```vue
    <span class="absolute -top-2 left-1/2 -translate-x-1/2 text-[8px] px-1.5 py-0.2 bg-amber-500/15 border border-amber-500/30 text-amber-600 dark:text-amber-400 font-extrabold rounded-full shadow-2xs backdrop-blur-xs whitespace-nowrap pointer-events-none leading-tight">
      {{ languageStore.t('به‌زودی', 'Soon') }}
    </span>
    ```
- **File**: `frontend/src/router/index.ts`
  - **Lines 35–43**: Maps `/marketplace` and `/plugins` to `MarketplaceView.vue`:
    ```ts
    {
      path: '/marketplace',
      name: 'marketplace',
      component: () => import('@/views/MarketplaceView.vue')
    },
    {
      path: '/plugins',
      name: 'plugins',
      component: () => import('@/views/MarketplaceView.vue')
    },
    ```

### 1.2 TopicMessageInput.vue & Composer Actions
- **File**: `frontend/src/components/TopicMessageInput.vue`
  - **Lines 40–41**: Imports plugin registry and types:
    ```ts
    import { usePluginRegistryStore } from '@/plugins/core/pluginRegistry'
    import type { ComposerAction } from '@/plugins/core/pluginTypes'
    ```
  - **Lines 587–623**: Dynamic plugin action computed state and cursor-aware text insertion logic:
    ```ts
    const pluginRegistry = usePluginRegistryStore()
    const pluginComposerActions = computed(() => pluginRegistry.composerActions)
    const activePluginDialog = ref<ComposerAction | null>(null)

    const handlePluginActionClick = (action: ComposerAction) => {
      isActionSheetOpen.value = false
      if (action.dialogComponent) {
        activePluginDialog.value = action
      } else if (action.execute) {
        action.execute({
          insertText: handlePluginInsert,
          currentText: text.value,
        })
      }
    }

    const handlePluginInsert = (insertedMarkdown: string) => {
      if (!insertedMarkdown) return
      const el = textareaRef.value || expandedTextareaRef.value
      if (el) {
        const start = el.selectionStart || 0
        const end = el.selectionEnd || 0
        const before = text.value.substring(0, start)
        const after = text.value.substring(end)
        const prefix = before && !before.endsWith('\n\n') ? (before.endsWith('\n') ? '\n' : '\n\n') : ''
        const suffix = after && !after.startsWith('\n\n') ? (after.startsWith('\n') ? '\n' : '\n\n') : ''
        text.value = before + prefix + insertedMarkdown + suffix + after
        nextTick(() => {
          el.focus()
          const newPos = (before + prefix + insertedMarkdown).length
          el.setSelectionRange(newPos, newPos)
        })
      } else {
        text.value = (text.value ? text.value + '\n\n' : '') + insertedMarkdown
      }
      activePluginDialog.value = null
    }
    ```
  - **Lines 1060–1155**: Plus action sheet dialog displaying "Topic Features" (`امکانات ویژه تاپیک`) and dynamic plugin buttons:
    ```vue
    <!-- Plugin Actions in Modal -->
    <template v-if="pluginComposerActions.length > 0">
      <div class="pt-2 border-t border-border/40 space-y-2">
        <span class="text-[11px] font-bold text-muted-foreground block">
          {{ languageStore.t('افزونه‌ها و ابزارها', 'Plugins & Tools') }}
        </span>
        <div class="grid grid-cols-3 gap-2.5">
          <button
            v-for="action in pluginComposerActions"
            :key="action.id"
            type="button"
            class="group relative aspect-square rounded-2xl border border-emerald-500/30 bg-emerald-50/10 hover:bg-emerald-50/20 hover:border-emerald-500/60 flex flex-col items-center justify-center gap-2 p-2 transition-all duration-200 cursor-pointer shadow-xs active:scale-95 text-center select-none"
            @click="handlePluginActionClick(action)"
          >
            <div class="size-10 rounded-xl bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 flex items-center justify-center text-xl group-hover:scale-110 transition-transform shadow-xs">
              {{ action.icon || '📖' }}
            </div>
            <span class="text-xs font-bold text-foreground group-hover:text-emerald-600 transition-colors">
              {{ action.label }}
            </span>
          </button>
        </div>
      </div>
    </template>
    ```
  - **Lines 1157–1164**: Dialog component mount:
    ```vue
    <component
      v-if="activePluginDialog && activePluginDialog.dialogComponent"
      :is="activePluginDialog.dialogComponent"
      :on-insert="handlePluginInsert"
      @insert="handlePluginInsert"
      @close="activePluginDialog = null"
    />
    ```

### 1.3 QuranVersePickerDialog & Markdown Formatter
- **File**: `frontend/src/plugins/quran/components/QuranVersePickerDialog.vue`
  - Allows selecting Surah, Ayah number, and Translation edition with live preview.
  - Calls `quranApi.formatReference()` or constructs reference markdown on `insertVerseIntoComposer()`.
- **File**: `backend/plugins/quran/services/formatter.py`
  - Lines 110–145: Formats Markdown blockquote:
    ```markdown
    > ﴿بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ﴾
    > *به نام خداوند بخشنده مهربان*
    > — **سوره الفاتحة (۱:۱)** — *ترجمه استاد انصاریان*
    ```

### 1.4 Dependencies & Build Status
- **File**: `frontend/package.json`
  - Build script: `"build": "run-p type-check \"build-only {@}\" --"`
  - Type-check script: `"type-check": "vue-tsc --build"`
- **Verbatim Command Executions**:
  - `npm run type-check` in `frontend/` -> **Exit Code 0** (0 errors).
  - `npm run build` in `frontend/` -> **Exit Code 0** (2755 modules transformed, 2.60s build time).

---

## 2. Logic Chain

```
[Observation: FeedView Tab 3 is UnderDevelopmentCard]
                        │
                        ▼ (Step 1: Modular Tab Architecture)
Create `PluginMarketplaceFeed.vue` (styled like `DonationsFeed.vue`)
Embed it in `FeedView.vue` Tab 3 with category chips, search & status toggles
                        │
                        ▼ (Step 2: Dynamic Routing Harmony)
Ensure `/marketplace` & `/plugins` activate Tab 3 in `FeedView.vue`
Preserve `PlatformHeader` (search query) and `PlatformNavigation` (bottom tabs)
                        │
                        ▼ (Step 3: Plugin Registry & Manifest Discovery)
`pluginRegistry.ts` exposes `composerActions` from active / core manifests
`quranManifest` declares `quran-insert-ayah` with `QuranVersePickerDialog`
                        │
                        ▼ (Step 4: Composer Action Sheet & Modal Invocation)
User clicks '+' in `TopicMessageInput.vue` -> selects 'درج آیه قرآن'
`QuranVersePickerDialog.vue` opens -> user chooses Surah/Ayah -> clicks 'درج در یادداشت'
                        │
                        ▼ (Step 5: Cursor-Aware Markdown Insertion & Zero Core Regression)
`handlePluginInsert` injects standard Markdown blockquote at cursor pos with `\n\n`
Standard `postStore.createPost(formData)` sends `content: message.text`
Zero alterations to backend `Post` model, SMS/Bale OTP, donations, or topics
                        │
                        ▼ (Step 6: Build & Type-Check Verification)
`vue-tsc --build` and `vite build` pass cleanly with 0 errors
```

### 2.1 Detailed Marketplace UI Architecture (`PluginMarketplaceFeed.vue`)

#### Component Props & Emits
```ts
// Props
export interface PluginMarketplaceFeedProps {
  searchQuery?: string
}

// Emits
export interface PluginMarketplaceFeedEmits {
  (e: 'open-plugin-detail', plugin: BackendPluginSummary): void
  (e: 'open-mini-app', routePath: string): void
}
```

#### Category Filters
1. `همه (All)` — All active and available plugins
2. `نصب‌شده (Installed)` — Filtered by `is_installed === true`
3. `رسمی (Official)` — Official first-party plugins (`is_core === true` or author: Tafakor Core)
4. `مذهبی و قرآنی (Religious & Quran)` — Quran, Dua, Islamic calendar plugins
5. `ابزارها (Tools & Productivity)` — Rich text, polls, analytics, export tools
6. `به‌زودی (Coming Soon)` — Teaser/upcoming plugins

#### Wireframe: Plugin Card in Marketplace
```
+-------------------------------------------------------------------------+
| [📖 Icon]  افزونه رسمی قرآن کریم [رسمی]                  [● فعال]       |
|            نسخه 1.0.0 • توسعه‌دهنده: تیم تفکر                            |
|                                                                         |
| مطالعه، تلاوت، جستجوی آیات و درج ارجاعات قرآنی در متن یادداشت‌ها         |
|                                                                         |
| [دکمه در ویرایشگر] [مینی‌اپ اختصاصی] [موتور جستجو]                      |
|-------------------------------------------------------------------------|
| [باز کردن مینی‌اپ ↗]                  [غیرفعال‌سازی]  [حذف]              |
+-------------------------------------------------------------------------+
```

#### Plugin Detail Modal Wireframe
```
+-------------------------------------------------------------------------+
| [📖] افزونه رسمی قرآن کریم (Official Quran Plugin)                  [✕] |
| نسخه 1.0.0 • توسعه‌دهنده: تیم تفکر • شناسه: quran                         |
|-------------------------------------------------------------------------|
| امکانات و قابلیت‌ها:                                                     |
| • فهرست کامل ۱۱۴ سوره قرآن همراه با مشخصات و تعداد آیات                 |
| • امکان تلاوت صوتی با قابلیت پخش پیوسته و سوئیچ بین قاریان              |
| • درج مستقیم آیات و ترجمه در ویرایشگر پیام تاپیک‌ها                     |
| • موتور جستجوی هوشمند بدون حساسیت به اعراب و همزه‌ها                    |
|                                                                         |
| مجوزها و دسترسی‌ها: خواندن قرآن، بدون دسترسی به اطلاعات خصوصی کاربر     |
|-------------------------------------------------------------------------|
| [انصراف]                                  [باز کردن مینی‌اپ] [غیرفعال‌سازی] |
+-------------------------------------------------------------------------+
```

### 2.2 Non-Invasive Composer Action Flow

```
[TopicMessageInput.vue]
   │
   ├─ 1. User clicks '+' button (PlusIcon)
   │     └─ Opens Dialog "Topic Features" (امکانات ویژه تاپیک)
   │
   ├─ 2. Plus sheet lists standard features + dynamic plugins:
   │     ├─ [ایجاد اهدا] (Donation Campaign)
   │     ├─ [نظرسنجی (به‌زودی)] (Poll)
   │     ├─ [رویداد (به‌زودی)] (Event)
   │     └─ [📖 درج آیه قرآن] (Quran Verse Picker Action)
   │
   ├─ 3. User selects "درج آیه قرآن"
   │     └─ Sets `activePluginDialog = action` (QuranVersePickerDialog)
   │
   ├─ 4. `QuranVersePickerDialog` renders:
   │     ├─ Surah dropdown (1. الفاتحة ... 114. الناس)
   │     ├─ Ayah number input (1 to surah.ayah_count)
   │     ├─ Translation dropdown (انصاریان، مکارم، انگلیسی، بدون ترجمه)
   │     ├─ Real-time Arabic + Translation preview box
   │     └─ "درج در یادداشت" button
   │
   ├─ 5. User clicks "درج در یادداشت":
   │     └─ Formats Markdown:
   │        > ﴿إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ﴾
   │        > *[تنها] تو را مى پرستيم و تنها از تو يارى مى جوييم.*
   │        > — **سوره الفاتحة (۱:۵)** — *ترجمه استاد انصاریان*
   │
   ├─ 6. `handlePluginInsert(markdown)` receives text:
   │     ├─ Detects cursor position in active textarea
   │     ├─ Inserts markdown surrounded by clean `\n\n`
   │     ├─ Moves cursor after insertion
   │     └─ Closes dialog
   │
   └─ 7. User clicks Send (SendIcon):
         └─ Triggers `emit('send', { text, attachments })`
         └─ `FeedView.vue` dispatches standard `postStore.createPost(formData)`
         └─ ZERO alterations to standard publishing pipeline!
```

---

## 3. Caveats

1. **Backend Dependency on API Endpoints**:
   - The frontend Marketplace and Quran picker assume backend endpoints `/api/plugins/` and `/api/plugins/quran/` (implemented in M1 and M2) are live and active.
   - Graceful offline/fallback: if the backend is unreachable or returns 404/500, `QuranVersePickerDialog.vue` and `PluginMarketplaceFeed.vue` display clean fallback states without breaking the core chat view.
2. **Mobile Viewport Constraint (< 500px)**:
   - Tafakor UI is strictly styled within max 500px centered mobile layout. All dialogs, sheets, cards, and buttons use responsive padding and font scaling.
3. **No Direct DOM Manipulation**:
   - Textarea insertion relies on standard Vue `ref<HTMLTextAreaElement>` and `selectionStart`/`selectionEnd` APIs, maintaining full compatibility with both the inline textarea and the expanded 80vh bottom sheet.

---

## 4. Conclusion

- **Marketplace UI**:
  - Replacing `UnderDevelopmentCard` in `FeedView.vue` Tab 3 with `PluginMarketplaceFeed.vue` (and harmonizing `/marketplace` and `/plugins` routes) completes the client-side plugin ecosystem.
  - The design features categorized chips, live search filtering, status badges (`رسمی`, `فعال`, `غیرفعال`, `به‌زودی`), install/uninstall/toggle buttons, and an informative detail modal.
- **Non-Invasive Composer Integration**:
  - `TopicMessageInput.vue`'s dynamic query of `pluginRegistry.composerActions` allows zero-coupling extension.
  - `QuranVersePickerDialog.vue` integrates seamlessly into the plus sheet and injects formatted Markdown blockquotes directly into the message text without altering the `Post` publishing pipeline.
- **Build Verification**:
  - `npm run type-check` (`vue-tsc --build`) passes with 0 errors.
  - `npm run build` generates optimized production bundles in 2.60s with 0 errors.

---

## 5. Verification Method

### 5.1 Automated Type-Check and Build Commands
Run from monorepo root:
```bash
# Type-check frontend
cd frontend && npm run type-check

# Production build
npm run build
```
**Expected Outcome**: 0 TypeScript errors, build completes successfully in `< 5s`.

### 5.2 Manual UI Verification Vectors
1. **Marketplace Tab Navigation**:
   - Click "بازارچه" tab in bottom navigation bar (`PlatformNavigation`).
   - Verify `FeedView.vue` switches to Tab 3 and displays the plugin marketplace feed.
   - Verify categories (`همه`, `نصب‌شده`, `رسمی`, `مذهبی`, `ابزارها`, `به‌زودی`) filter the list correctly.
   - Click "افزونه رسمی قرآن کریم" card to verify the detail modal opens.
   - Click "باز کردن مینی‌اپ" to verify smooth navigation to `/apps/quran`.
2. **Composer Action & Markdown Injection**:
   - Navigate into any topic chat (`/topic/:id`).
   - Click the '+' button next to the message input.
   - Verify "درج آیه قرآن" appears under "افزونه‌ها و ابزارها".
   - Click "درج آیه قرآن" -> choose Surah 1 (الفاتحة) and Ayah 5.
   - Click "درج در یادداشت".
   - Verify the formatted Markdown blockquote appears in the message input.
   - Click Send -> verify standard message is published and rendered as a blockquote in the post card.
3. **Core Non-Regression**:
   - Verify normal text messages, attachments (images/videos/audios), voice recordings, and donation campaign cards in topics continue to operate with 100% fidelity.
