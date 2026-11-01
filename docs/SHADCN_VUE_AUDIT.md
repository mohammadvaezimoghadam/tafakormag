# shadcn-vue Engineering Audit

## Executive Summary

This report provides a validated, evidence-based engineering audit of the **Tafakor (پلتفرم تفکر) / AVA Design Labs** repository against current official [shadcn-vue](https://www.shadcn-vue.com/) and [Reka UI](https://reka-ui.com/) architecture, conventions, styling philosophy, accessibility requirements, RTL model, theming system, and dark mode standards.

This Stage-2 audit validates, challenges, and refines previous audit findings against canonical Vue 3 / Reka UI component sources. It eliminates false positives (such as misclassifying canonical upstream code or product-specific design customizations as architectural violations), contextualizes CLI configuration vs runtime behavior, and presents a realistic, prioritized remediation roadmap.

---

## Repository Overview

- **Application Name**: Tafakor (پلتفرم تفکر) / AVA Design Labs
- **Repository Architecture**: Single Page Application (Vite 8 + Vue 3.5) with dual-mode build entry points:
  - Platform Mode (`--mode platform` → `index.html` → `src/main.ts` → `src/App.vue`)
  - Labs / Showcase Mode (`--mode labs` → `labs.html` → `src/labs-main.ts` → `src/LabsApp.vue`)
- **Core Product Features**:
  - Telegram & Bale Bot Connection Hub with webhook status validation
  - Topic-based messaging feeds with in-card audio waveform players and video renderers
  - AI Text Refiner Assistant with translation and style shifting
  - Kindness (پویش‌های مهربانی) crowdfunding campaigns with 12-column Bento Grid media galleries
  - User authentication and profile management
- **Language & Direction**: Bilingual (Persian `fa` as primary, English `en` as secondary); runtime direction controlled by `languageStore` via `<ConfigProvider :dir="languageStore.dir">` and `<html dir="rtl" lang="fa">`.

---

## Environment & Versions

| Technology / Package | Detected Version | Ecosystem Role | Official Baseline Comparison | Status |
|---|---|---|---|---|
| **Vue** | `^3.5.32` | Core Framework | Vue 3.5.x (Latest Stable) | Current & Supported |
| **TypeScript** | `~6.0.0` / `@types/node ^24.13.2` | Language | TypeScript 5.x / 6.x | Modern & Type-safe |
| **Tailwind CSS** | `^4.3.1` | Styling Engine | Tailwind CSS v4 Engine | Current (V4 Architecture) |
| **@tailwindcss/vite** | `^4.3.1` | Vite Plugin | Official Tailwind v4 Vite integration | Current |
| **Reka UI** | `^2.10.1` | Headless Primitives | Canonical shadcn-vue primitive engine | Current (Upstream parity) |
| **shadcn-vue (Package)** | `^2.7.4` | Component Registry | shadcn-vue v2 (Reka-based) | Current |
| **Class Variance Authority** | `^0.7.1` (`cva`) | Variant System | Standard `cva` package | Canonical |
| **clsx & tailwind-merge** | `^2.1.1` & `^3.6.0` | Class Composition | Standard `cn()` foundation | Canonical |
| **@vueuse/core** | `^14.3.0` | Reactivity Utilities | Used for `useDark`, `reactiveOmit`, `useVModel` | Standard |
| **Icon Libraries** | `@lucide/vue ^1.26.0` | Icons | Canonical Lucide icons for Vue | Active (`lucide-vue-next` is unused duplicate) |
| **Pinia** | `^3.0.4` | State Management | Vue Store | Active |
| **Vue Router** | `^5.1.0` (Lockfile: `5.1.0`) | Client Routing | Routing engine | Active |

---

## Overall Compliance Score

```
┌──────────────────────────────────────────────────────────────────┐
│   Validated shadcn-vue Engineering Compliance: 76 / 100          │
│   Status: PRODUCTION-CAPABLE WITH SPECIFIC TECHNICAL DEBT        │
└──────────────────────────────────────────────────────────────────┘
```

The validated score reflects a solid Reka UI foundation with full variant composition via `cva` and `cn()`. The deduction is driven by specific, verifiable technical debt: global CSS overrides in `@layer base`, physical directional classes in RTL-rendered components, custom floating math replacing existing menu primitives, and missing theme tokens.

---

## Scorecard

| Area | Score | Status | Primary Driver |
|---|---:|---|---|
| **Component Architecture** | **82 / 100** | Good | Reka UI primitives properly wrapped; deducted for custom overlay math in context menus. |
| **Theming** | **76 / 100** | Moderate | Modern OKLCH color scale; deducted for missing `--destructive-foreground` and direct opacity colors. |
| **Dark Mode** | **88 / 100** | Strong | Excellent VueUse `useDark` with `.dark` selector; semantic CSS variable adaptation. |
| **RTL Support** | **64 / 100** | Moderate Concern | Strong runtime RTL container, but physical directional classes (`pr-*`/`pl-*`/`border-r`) degrade specific components. |
| **Typography** | **66 / 100** | Moderate | Superb Persian variable font integration; deducted for blanket `@apply` on base HTML tags (`p`, `h2`, `table`). |
| **Accessibility** | **74 / 100** | Good | Reka UI primitives provide keyboard traps and ARIA; minor omissions (`DialogTitle` in login modal, icon button labels). |
| **Tailwind / CSS** | **72 / 100** | Good | Tailwind v4 `@theme inline` properly configured; global `@apply` in `spacing-radius.css` requires cleanup. |
| **Consistency** | **78 / 100** | Good | `cn()` used across all components; radius scale is intentionally customized. |
| **Maintainability** | **76 / 100** | Good | Clean Pinia stores and modular structure; orphaned duplicate `TopicAdminsModal.vue` needs removal. |
| **Responsive Design** | **88 / 100** | Strong | Excellent mobile bottom sheets, responsive bento grids, and touch/mouse interaction handling. |

---

## Previous Audit Validation

The following table records the verdict for every significant finding from the initial audit after validating against official documentation, Reka UI sources, and repository code:

| ID | Finding Description | Verdict | Validated Severity | Evidence & Technical Rationale |
|---|---|---|---|---|
| **F-01** | Global CSS `@apply` in `spacing-radius.css` overrides `button`, `input`, `[role="dialog"]`, and `[data-radix-popper-content-wrapper]` | **CONFIRMED** | **HIGH** | `spacing-radius.css:17-43` injects high-specificity styles into raw tags and Radix popper wrappers, creating double padding on popovers. |
| **F-02** | `components.json` defines `"rtl": false` in an RTL application | **PARTIALLY_CONFIRMED** | **LOW** | Initial audit rated this CRITICAL. Validation shows `"rtl": false` in `components.json` is a CLI generator preference that does not break runtime direction (`<ConfigProvider :dir="dir">` controls runtime). However, setting it to `true` ensures future CLI-added components generate logical classes. |
| **F-03** | Physical directional classes (`pr-*`, `pl-*`, `border-r`, `text-left`) in `NativeSelect`, `InputOTP`, `Button`, `Badge`, `Toggle`, `Alert` | **CONFIRMED** | **HIGH** | `NativeSelect.vue:43` positions chevron at `right-2.5` over Persian text; `InputOTPSlot.vue:25` rounds inner corners in RTL; `Alert` forces `text-left`. |
| **F-04** | `Progress.vue` `translateX(-X%)` is a critical RTL bug | **FALSE_POSITIVE** | **INFO** | Canonical shadcn-vue `Progress.vue` upstream uses this exact line. Reka UI ProgressIndicator uses `translateX(-X%)` as standard. While adapting for RTL is a useful enhancement, the component is 100% upstream compliant. |
| **F-05** | Global typography `@apply` on `h1-h4`, `p`, `table`, `ul`, `ol` in `typography.css` | **CONFIRMED** | **MEDIUM** | `typography.css:55-60` applies `mt-6` to every `p:not(:first-child)`, forcing unwanted margins inside Cards and Modals. |
| **F-06** | Missing `--destructive-foreground` token in `main.css` | **CONFIRMED** | **MEDIUM** | `main.css:58` defines `--color-destructive` but omits `--destructive-foreground`, forcing `Button.vue` to use subtle `bg-destructive/10 text-destructive`. |
| **F-07** | Custom radius values (`rounded-3xl`, `rounded-4xl`) violate shadcn-vue theme system | **FALSE_POSITIVE** | **INFO** | In shadcn-vue, the user owns the source code. Customizing component radii to a pill/squircle aesthetic is an intentional product design decision, not an architectural violation. |
| **F-08** | Custom floating coordinate math in `PostContextMenu.vue` and `TopicSettingsMenu.vue` | **CONFIRMED** | **MEDIUM** | Both components manually calculate `top`/`left` coordinates in JavaScript instead of leveraging Reka UI `ContextMenu` / `DropdownMenu` primitives. |
| **F-09** | Direct coupling of `Switch.vue` to `useLanguageStore` | **CONFIRMED** | **MEDIUM** | `Switch.vue:4-6` imports Pinia `useLanguageStore` to calculate `-translate-x-5` instead of using Tailwind logical variants (`rtl:data-[state=checked]:-translate-x-5`). |
| **F-10** | Duplicate implementations: `TopicAdminsModal.vue` vs `TopicAdminsView.vue` | **CONFIRMED** | **LOW** | `TopicAdminsModal.vue` is an unmounted duplicate (385 lines) only referenced in `PlaygroundView.vue`. |
| **F-11** | Redundant dependencies: `lucide-vue-next`, `autoprefixer`, `postcss` | **CONFIRMED** | **LOW** | `lucide-vue-next` is never imported (`@lucide/vue` is used everywhere); `autoprefixer` and `postcss` are redundant with Tailwind v4 `@tailwindcss/vite`. |
| **F-12** | Stale alias `"composables": "@/composables"` in `components.json` | **CONFIRMED** | **LOW** | Directory `src/composables/` does not exist in the repository. |
| **F-13** | Undefined orphan classes: `cn-rtl-flip` and `cn-menu-translucent` | **CONFIRMED** | **LOW** | Used in `CalendarNextButton.vue`, `CalendarPrevButton.vue`, and `SelectContent.vue` but never defined in CSS. |
| **F-14** | Missing `DialogTitle` in `App.vue` login dialog | **CONFIRMED** | **LOW** | `DialogContent` in `App.vue:113` contains `DialogDescription` but omits `DialogTitle`, triggering a console accessibility warning. |

---

## Canonical Component Comparison

The following matrix compares key repository components against the official canonical shadcn-vue implementations:

| Component | Canonical shadcn-vue Pattern | Current Repository Pattern | Architectural Difference | Verdict |
|---|---|---|---|---|
| **Button** | `cva` with `variant` (`default`, `destructive`, `outline`, `secondary`, `ghost`, `link`) and `size` (`default`, `sm`, `lg`, `icon`) | Extended `cva` with `xs`, `icon-xs`, `icon-sm`, `icon-lg`; `rounded-4xl`; subtle destructive variant | Extra sizes and subtle destructive styling are valid customizations; physical `pr-2.5`/`pl-2.5` on `data-icon` should use `pe-2.5`/`ps-2.5`. | **PARTIALLY_CONFIRMED** |
| **Progress** | `ProgressRoot` + `ProgressIndicator` with `:style="'transform: translateX(-' + (100 - (modelValue ?? 0)) + '%);'"` | Identical upstream implementation; `h-3 rounded-full` | Exactly matches official shadcn-vue upstream code. | **FALSE_POSITIVE** |
| **Switch** | `SwitchRoot` + `SwitchThumb` with `data-[state=checked]:translate-x-5` | `SwitchThumb` imports `useLanguageStore` and computes ternary translation | Direct store coupling inside UI primitive is unnecessary; can be replaced with `rtl:` variant. | **CONFIRMED** |
| **Dialog** | `DialogPortal` + `DialogOverlay` + `DialogContent` with `DialogClose` at `top-4 right-4` | Identical primitive wrapping; close button at `top-4 right-4`; `rounded-4xl` | Close button is identical to upstream default; in RTL, logical `end-4` is preferred. | **CONTEXT_DEPENDENT** |
| **Input** | `input` with `h-9 rounded-md border border-input bg-transparent px-3 py-1 text-sm` | `input` with `h-9 rounded-3xl border bg-input/50 px-3 py-1 text-xs font-semibold` | Visual styling (pill shape, smaller text) is an intentional design choice; conflicts with global CSS in `spacing-radius.css`. | **CONTEXT_DEPENDENT** |
| **Native Select** | `select` with `py-1 ps-3 pe-8` and chevron icon at `end-2.5` | `select` with `py-1 pr-8 pl-3` and chevron at `right-2.5` | Physical directions cause chevron to cover text start in RTL. | **CONFIRMED** |
| **Input OTP** | `InputOTPSlot` with `border-y border-e first:border-s first:rounded-s-md last:rounded-e-md` | `InputOTPSlot` with `border-y border-r first:border-l first:rounded-l-3xl last:rounded-r-3xl` | Physical classes invert border and corner radius positions in RTL. | **CONFIRMED** |
| **Alert** | `alertVariants` with `relative w-full rounded-lg border p-4 text-start` | `alertVariants` with `text-left has-data-[slot=alert-action]:pr-18` | `text-left` explicitly breaks RTL alignment for Persian alerts. | **CONFIRMED** |

---

## Validated Findings by Category

### 1. Global Stylesheet Overrides
- **Finding**: [`frontend/src/assets/spacing-radius.css`](file:///f:/AVA/tafakor/frontend/src/assets/spacing-radius.css#L17-L43) applies `@apply` to `button`, `input`, `[role="dialog"]`, and `[data-radix-popper-content-wrapper]`.
- **Impact**: Interferes with component-level variant classes (`cva`) and causes double padding on Radix popper wrappers.
- **Recommended Action**: Remove tag-level and attribute-level `@apply` blocks from `spacing-radius.css`.
- **Severity**: **HIGH** | **Confidence**: **HIGH**

### 2. Physical vs. Logical Directional Classes
- **Finding**: Several UI primitives use physical directions instead of Tailwind CSS logical equivalents:
  - [`NativeSelect.vue:43`](file:///f:/AVA/tafakor/frontend/src/components/ui/native-select/NativeSelect.vue#L43): `py-1 pr-8 pl-3` → change to `py-1 pe-8 ps-3`; chevron `right-2.5` → change to `end-2.5`.
  - [`InputOTPSlot.vue:25`](file:///f:/AVA/tafakor/frontend/src/components/ui/input-otp/InputOTPSlot.vue#L25): `border-r first:rounded-l-3xl first:border-l last:rounded-r-3xl` → change to `border-e first:rounded-s-3xl first:border-s last:rounded-e-3xl`.
  - [`alert/index.ts:9`](file:///f:/AVA/tafakor/frontend/src/components/ui/alert/index.ts#L9): `text-left has-data-[slot=alert-action]:pr-18` → change to `text-start has-data-[slot=alert-action]:pe-18`.
  - [`button/index.ts:19`](file:///f:/AVA/tafakor/frontend/src/components/ui/button/index.ts#L19), [`badge/index.ts:7`](file:///f:/AVA/tafakor/frontend/src/components/ui/badge/index.ts#L7), [`toggle/index.ts:15`](file:///f:/AVA/tafakor/frontend/src/components/ui/toggle/index.ts#L15): `pr-2.5`/`pl-2.5` on icon slots → change to `pe-2.5`/`ps-2.5`.
- **Impact**: Corrects RTL alignment and visual flow in Persian forms, inputs, and badges.
- **Severity**: **HIGH** | **Confidence**: **HIGH**

### 3. Store Coupling in Base UI Primitive
- **Finding**: [`frontend/src/components/ui/switch/Switch.vue`](file:///f:/AVA/tafakor/frontend/src/components/ui/switch/Switch.vue#L4-L6) imports Pinia `useLanguageStore` to toggle `-translate-x-5` vs `translate-x-5`.
- **Impact**: Couples a reusable UI component to an application-level store.
- **Recommended Action**: Replace with pure CSS variant: `class="data-[state=checked]:translate-x-5 rtl:data-[state=checked]:-translate-x-5"`.
- **Severity**: **MEDIUM** | **Confidence**: **HIGH**

### 4. Global Typography Base Layer Leaks
- **Finding**: [`frontend/src/assets/typography.css`](file:///f:/AVA/tafakor/frontend/src/assets/typography.css#L55-L60) binds shadcn-vue typography classes to global HTML tags (`h1-h4`, `p:not(:first-child)`, `table`, `ul`, `ol`).
- **Impact**: Injects `margin-top: 1.5rem` into `<p>` elements inside Cards, Dialogs, and Alerts, forcing inline reset hacks.
- **Recommended Action**: Move prose styles to utility classes (e.g. `.typography-p`, `.typography-h2`) or scope them under a `.prose-persian` container for markdown/article content.
- **Severity**: **MEDIUM** | **Confidence**: **HIGH**

### 5. Custom Coordinate Math in Context Menus
- **Finding**: [`frontend/src/components/PostContextMenu.vue`](file:///f:/AVA/tafakor/frontend/src/components/PostContextMenu.vue#L35-L94) and [`TopicSettingsMenu.vue`](file:///f:/AVA/tafakor/frontend/src/components/TopicSettingsMenu.vue#L36-L62) manually compute viewport coordinates and fixed positioning.
- **Impact**: Bypasses Reka UI's built-in collision detection, keyboard navigation, and focus management.
- **Recommended Action**: Refactor `PostContextMenu.vue` to use shadcn-vue `ContextMenu` primitives, and `TopicSettingsMenu.vue` to use `DropdownMenu`.
- **Severity**: **MEDIUM** | **Confidence**: **HIGH**

### 6. Theme Token Completeness
- **Finding**: [`frontend/src/assets/main.css`](file:///f:/AVA/tafakor/frontend/src/assets/main.css#L58) defines `--color-destructive: var(--destructive);` but omits `--destructive-foreground`.
- **Impact**: Prevents solid destructive components from inheriting a compliant foreground text color.
- **Recommended Action**: Add `--destructive-foreground: oklch(0.988 0.003 106.5);` to `:root`, `.dark`, and `@theme inline`.
- **Severity**: **MEDIUM** | **Confidence**: **HIGH**

### 7. Dependency & Config Cleanup
- **Finding**:
  - `lucide-vue-next` in `package.json` is redundant (`@lucide/vue` is the active library).
  - `autoprefixer` and `postcss` in `devDependencies` are redundant with Tailwind v4 `@tailwindcss/vite`.
  - `components.json` contains stale alias `"composables": "@/composables"` and `"rtl": false`.
  - `CalendarNextButton.vue`, `CalendarPrevButton.vue`, and `SelectContent.vue` reference undefined classes `cn-rtl-flip` and `cn-menu-translucent`.
- **Recommended Action**: Remove unused dependencies, update `components.json` (`"rtl": true`), and replace orphan classes with standard Tailwind utilities.
- **Severity**: **LOW** | **Confidence**: **HIGH**

---

## Intentional Customizations (Preserved & Approved)

The following aspects of the codebase represent **legitimate, high-quality product design decisions** and should **NOT** be reverted to generic starter styles:

1. **Persian Typography System (`IRANYekanXVF.woff2`)**:
   Variable font configuration with connected dots (`dots 3`) and Persian number ligature features (`ss01`, `cv11`).
2. **Pill / Squircle Radius Aesthetic (`rounded-3xl`, `rounded-4xl`)**:
   Cohesive modern design language across buttons, cards, dialogs, and navigation elements.
3. **Kindness Crowdfunding Bento Grid (`DonationCard.vue`)**:
   Responsive 12-column bento media layout (7 cols main image, 5 cols thumbnail grid) tailored for donation campaign transparency.
4. **Interactive In-Card Media Players (`PostCard.vue`)**:
   Custom audio seeker and video playback overlay integrated directly into feed post cards.
5. **AI Refiner Assistant Drawer (`AIRefinerDrawer.vue`)**:
   Interactive translation chips, tone presets, and streaming simulation drawer for Farsi/English message composition.
6. **Dual-Mode Vite Configuration (`vite.config.ts`)**:
   Clean separation between main platform bundle (`index.html`) and design system showcase (`labs.html`).

---

## Prioritized Remediation Roadmap

```
┌────────────────────────────────────────────────────────────────────────┐
│                        VALIDATED REMEDIATION PLAN                      │
│                                                                        │
│   P0 — Must Fix (RTL Directionality & Stylesheet Isolation)            │
│   P1 — Should Fix (Menu Primitives, Theme Tokens, Typography Scope)    │
│   P2 — Recommended (A11y Labels, Store Decoupling, Duplicate Cleanup)  │
│   P3 — Optional (Dependency & Stale Config Housekeeping)               │
└────────────────────────────────────────────────────────────────────────┘
```

### P0 — Must Fix (Runtime Bugs & Layout Leaks)
- **RTL Logical Classes**: Update `NativeSelect.vue`, `InputOTPSlot.vue`, `Alert/index.ts`, `Button/index.ts`, `Badge/index.ts`, `Toggle/index.ts` to use `pe-*`, `ps-*`, `border-s`, `border-e`, `start-*`, `end-*`.
- **Isolate Base Stylesheet**: Remove blanket `@apply` rules from `src/assets/spacing-radius.css`.

### P1 — Should Fix (Architectural Integrity & Theme Completeness)
- **Scope Typography Rules**: Move `h1-h4`, `p`, `table` rules in `typography.css` from raw HTML tags to composable classes (`.typography-h2`, `.typography-p`, etc.).
- **Add Missing Theme Token**: Add `--destructive-foreground` to `:root`, `.dark`, and `@theme inline` in `main.css`.
- **Decouple Switch**: Remove `useLanguageStore` from `Switch.vue`; use `rtl:data-[state=checked]:-translate-x-5`.
- **Adopt Menu Primitives**: Migrate `PostContextMenu.vue` to `ContextMenu` and `TopicSettingsMenu.vue` to `DropdownMenu`.

### P2 — Recommended (Consistency & Accessibility)
- **Fix Missing `DialogTitle`**: Add `<DialogTitle class="sr-only">` inside `App.vue` login dialog.
- **Add Accessible Button Names**: Add `aria-label` or `<span class="sr-only">` to icon-only action buttons in `PostCard.vue` and `TopicMessageInput.vue`.
- **Remove Duplicate Admin Modal**: Delete orphaned `TopicAdminsModal.vue` in favor of `TopicAdminsView.vue`.
- **Replace Literal Opacity Colors**: Convert `bg-white/5 dark:bg-black/10` in `PostCard.vue` and `TopicEditView.vue` to `bg-muted/30` or `bg-card`.

### P3 — Optional (Housekeeping)
- **Dependency Pruning**: Remove `lucide-vue-next`, `autoprefixer`, `postcss` from `package.json`.
- **Sync `components.json`**: Update `"rtl": true` and remove stale `"composables"` alias.
- **Clean Orphan Classes**: Replace `cn-rtl-flip` with `rtl:rotate-180` in Calendar buttons, and remove `cn-menu-translucent`.

---

## Files Requiring Attention

| File | Issue | Severity | Recommended Action | Safe to Automate? | Visual Check Needed? |
|---|---|---|---|---|---|
| `frontend/src/assets/spacing-radius.css` | Global `@apply` on native tags | **HIGH** | Remove element-level `@apply` blocks | Yes | Yes |
| `frontend/src/components/ui/native-select/NativeSelect.vue` | Physical `pr-8 pl-3` and chevron at `right-2.5` | **HIGH** | Use `pe-8 ps-3` and chevron at `end-2.5` | Yes | Yes |
| `frontend/src/components/ui/input-otp/InputOTPSlot.vue` | Physical `border-r`, `first:rounded-l-3xl` | **HIGH** | Use `border-e`, `first:rounded-s-3xl`, `last:rounded-e-3xl` | Yes | Yes |
| `frontend/src/components/ui/alert/index.ts` | `text-left`, physical `pr-18` | **HIGH** | Use `text-start`, `pe-18` | Yes | No |
| `frontend/src/components/ui/button/index.ts` | Physical `pr-2.5`/`pl-2.5` on icon slots | **MEDIUM** | Use `pe-2.5`/`ps-2.5` | Yes | No |
| `frontend/src/components/ui/badge/index.ts` | Physical `pr-1.5`/`pl-1.5` on icon slots | **MEDIUM** | Use `pe-1.5`/`ps-1.5` | Yes | No |
| `frontend/src/components/ui/toggle/index.ts` | Physical `pr-2.5`/`pl-2.5` on icon slots | **MEDIUM** | Use `pe-2.5`/`ps-2.5` | Yes | No |
| `frontend/src/components/ui/switch/Switch.vue` | Direct coupling to `useLanguageStore` | **MEDIUM** | Use `rtl:data-[state=checked]:-translate-x-5` | Yes | Yes |
| `frontend/src/assets/typography.css` | Global `@apply` on `h1-h4`, `p`, `table`, `ul` | **MEDIUM** | Move to composable utility classes | Yes | Yes |
| `frontend/src/assets/main.css` | Missing `--destructive-foreground` token | **MEDIUM** | Add token to `:root`, `.dark`, `@theme` | Yes | No |
| `frontend/src/components/PostContextMenu.vue` | Custom floating coordinate math | **MEDIUM** | Refactor to shadcn-vue `ContextMenu` | No | Yes |
| `frontend/src/components/TopicSettingsMenu.vue` | Custom floating coordinate math | **MEDIUM** | Refactor to shadcn-vue `DropdownMenu` | No | Yes |
| `frontend/src/components/TopicAdminsModal.vue` | Duplicate of `TopicAdminsView.vue` | **LOW** | Delete orphaned file | Yes | No |
| `frontend/src/App.vue` | Missing `DialogTitle` in login modal | **LOW** | Add `<DialogTitle class="sr-only">` | Yes | No |
| `frontend/components.json` | `"rtl": false`, stale `composables` alias | **LOW** | Set `"rtl": true`, remove stale alias | Yes | No |
| `frontend/package.json` | Unused `lucide-vue-next`, `autoprefixer`, `postcss` | **LOW** | Remove from dependencies | Yes | No |

---

## Final Assessment

- **Current Assessed Alignment**: The repository achieves **76 / 100** compliance with the official shadcn-vue engineering standard.
- **Primary Confirmed Issues**: High-specificity global base stylesheet overrides, physical directional classes in RTL primitives, custom floating math replacing standard context/dropdown menus, and a missing theme token.
- **False Positives Eliminated**: Canonical `Progress.vue` `translateX(-X%)` behavior and custom pill/squircle radius scales were confirmed as compliant upstream code and intentional product design choices, respectively.
- **Refactoring Scope**: The technical debt can be resolved incrementally across P0–P3 without breaking existing views, store logic, or visual branding.

---

## Audit Methodology

1. **Static Analysis & File Inspection**: Inspected `package.json`, `package-lock.json`, `components.json`, `vite.config.ts`, all CSS entry points (`main.css`, `base.css`, `typography.css`, `spacing-radius.css`), all 27 component implementations under `src/components/ui/`, and 25 application components.
2. **Canonical Baseline Comparison**: Benchmarked every finding against current official [shadcn-vue documentation](https://www.shadcn-vue.com/) and upstream Reka UI component sources.
3. **Verdict Verification**: Applied rigorous classification (`CONFIRMED`, `PARTIALLY_CONFIRMED`, `FALSE_POSITIVE`, `CONTEXT_DEPENDENT`, `OUTDATED`, `UNVERIFIABLE`) to eliminate assumptions.

---

## Official References

- **shadcn-vue Documentation**: [https://www.shadcn-vue.com/](https://www.shadcn-vue.com/)
- **shadcn-vue Theming**: [https://www.shadcn-vue.com/docs/theming](https://www.shadcn-vue.com/docs/theming)
- **shadcn-vue Dark Mode**: [https://www.shadcn-vue.com/docs/dark-mode](https://www.shadcn-vue.com/docs/dark-mode)
- **shadcn-vue RTL Guide**: [https://www.shadcn-vue.com/docs/rtl](https://www.shadcn-vue.com/docs/rtl)
- **shadcn-vue Typography**: [https://www.shadcn-vue.com/docs/components/typography](https://www.shadcn-vue.com/docs/components/typography)
- **shadcn-vue Skills & Conventions**: [https://www.shadcn-vue.com/docs/skills](https://www.shadcn-vue.com/docs/skills)
- **Reka UI Primitives**: [https://reka-ui.com/](https://reka-ui.com/)
