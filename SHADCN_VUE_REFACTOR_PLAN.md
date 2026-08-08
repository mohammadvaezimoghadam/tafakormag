# shadcn-vue Refactor Plan

## Executive Summary

This document provides a safe, production-ready, step-by-step refactoring plan to resolve all confirmed technical and architectural issues identified in the Stage-2 audit ([SHADCN_VUE_AUDIT.md](file:///f:/AVA/tafakor/SHADCN_VUE_AUDIT.md)).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        REFACTOR PLAN SNAPSHOT                          │
│                                                                        │
│   Validated Compliance Baseline: 76 / 100                             │
│   P0 — Must Fix Tasks:       2 tasks (Global CSS & RTL Logical Primitives)│
│   P1 — Should Fix Tasks:     4 tasks (Typography, Theme Token, Switch, Menus)│
│   P2 — Recommended Tasks:    4 tasks (A11y Titles, Icon Labels, Duplicates)│
│   P3 — Optional Tasks:       3 tasks (Dependencies, Config Sync, Orphan CSS)│
│                                                                        │
│   Highest Risk Areas:                                                  │
│     1. Base Stylesheet Isolation (spacing-radius.css)                  │
│     2. ContextMenu Primitive Migration (mobile touch preservation)     │
└────────────────────────────────────────────────────────────────────────┘
```

The refactoring strategy is structured to make **minimal, surgical changes** that restore architectural alignment with shadcn-vue and Reka UI while **100% preserving product-specific customizations** (Persian variable typography, pill/squircle aesthetics, Kindness crowdfunding bento grid, in-card media players, and AI text refiner).

---

## Current State

The repository runs on Vue 3.5.32, Vite 8, Tailwind CSS v4.3.1 (`@tailwindcss/vite`), and Reka UI 2.10.1. The 27 base UI components located under `src/components/ui/` use `reka-ui` primitives, `class-variance-authority` (`cva`), and `cn()` utilities.

While the core foundation is robust, specific technical debt has accumulated:
1. **Global Stylesheet Pollution**: High-specificity `@apply` rules in `src/assets/spacing-radius.css` target native elements (`button`, `input`, `[role="dialog"]`, `[data-radix-popper-content-wrapper]`), creating specificity conflicts with component variants and double-padding in popovers.
2. **Physical RTL Directions**: `NativeSelect.vue`, `InputOTPSlot.vue`, and `Alert/index.ts` use physical directional classes (`pr-*`, `pl-*`, `border-r`, `text-left`) that invert layout in Persian RTL mode.
3. **Typography Tag Overrides**: `src/assets/typography.css` applies margins (`mt-6`, `mt-10`) to raw HTML tags (`p:not(:first-child)`, `h2`), forcing unwanted spacing in cards and dialogs.
4. **Theme Completeness**: `--destructive-foreground` is missing from `:root` and `.dark` in `src/assets/main.css`.
5. **Primitive Bypassing**: Context menus and dropdowns in `PostContextMenu.vue` and `TopicSettingsMenu.vue` manually compute floating coordinates in JavaScript rather than using Reka UI primitives.
6. **Store Coupling**: `src/components/ui/switch/Switch.vue` directly imports `useLanguageStore` instead of using pure CSS variants.

---

## Refactoring Principles

1. **Architectural Compatibility Over Visual Homogenization**: We preserve the bespoke product design (pill radii, Persian font features, glassmorphism, bento cards) and only remediate structural, accessibility, RTL, and styling architecture issues.
2. **Zero Regressions in Existing Views**: Every change must be backward-compatible with all views (`FeedView.vue`, `HomeView.vue`, `DonationCardPlayground.vue`, `ShowcaseView.vue`, `PlaygroundView.vue`).
3. **Atomic, Isolated Changes**: Each task is independent, verifiable via `npm run type-check` and `npm run build`, and safely rollbackable.
4. **No Over-Refactoring**: If upstream shadcn-vue behaves identically to the repository (e.g. `Progress.vue`), it is left untouched.

---

## Scope

The plan strictly addresses confirmed findings from the Stage-2 audit. Tasks are categorized by priority:

- **P0 — Must Fix**: Immediate layout leaks, runtime RTL bugs, and base layer stylesheet overrides.
- **P1 — Should Fix**: Theme token completeness, typography isolation, store decoupling from base primitives, and menu primitive adoption.
- **P2 — Recommended**: Accessibility compliance (dialog titles, screen-reader labels), duplicate component deprecation, and semantic opacity tokens.
- **P3 — Optional**: Build dependency pruning, `components.json` synchronization, and cleanup of unused orphan classes.

---

## Findings Included

| Audit ID | Finding Description | Stage-2 Verdict | Severity | Refactor Required | Task ID |
|---|---|---|---|---|---|
| **F-01** | Global CSS `@apply` in `spacing-radius.css` overrides `button`, `input`, `[role="dialog"]` | **CONFIRMED** | **HIGH** | Yes | `TASK-P0-01` |
| **F-02** | `components.json` defines `"rtl": false` and stale `"composables"` alias | **PARTIALLY_CONFIRMED** | **LOW** | Yes | `TASK-P3-02` |
| **F-03** | Physical directional classes (`pr-*`, `pl-*`, `border-r`, `text-left`) in RTL | **CONFIRMED** | **HIGH** | Yes | `TASK-P0-02` |
| **F-05** | Global typography `@apply` on `h1-h4`, `p`, `table` in `typography.css` | **CONFIRMED** | **MEDIUM** | Yes | `TASK-P1-01` |
| **F-06** | Missing `--destructive-foreground` token in `main.css` | **CONFIRMED** | **MEDIUM** | Yes | `TASK-P1-02` |
| **F-08** | Custom floating coordinate math in `PostContextMenu.vue` and `TopicSettingsMenu.vue` | **CONFIRMED** | **MEDIUM** | Yes | `TASK-P1-04` |
| **F-09** | Direct coupling of `Switch.vue` to Pinia `useLanguageStore` | **CONFIRMED** | **MEDIUM** | Yes | `TASK-P1-03` |
| **F-10** | Duplicate implementations: `TopicAdminsModal.vue` vs `TopicAdminsView.vue` | **CONFIRMED** | **LOW** | Yes | `TASK-P2-03` |
| **F-11** | Redundant packages (`lucide-vue-next`, `autoprefixer`, `postcss`) in `package.json` | **CONFIRMED** | **LOW** | Yes | `TASK-P3-01` |
| **F-13** | Undefined orphan classes (`cn-rtl-flip`, `cn-menu-translucent`) | **CONFIRMED** | **LOW** | Yes | `TASK-P3-03` |
| **F-14** | Missing `DialogTitle` in `App.vue` login dialog | **CONFIRMED** | **LOW** | Yes | `TASK-P2-01` |

---

## Findings Explicitly Excluded

The following items are **strictly excluded** from refactoring to protect valid product design and avoid false-positive churn:

1. **`F-04` — `Progress.vue` `translateX(-X%)`**:
   - **Reason**: Stage-2 canonical verification confirmed that `Progress.vue` in this repository is 100% identical to the official upstream shadcn-vue and Reka UI implementation. Reka UI handles indicator positioning internally.
   - **Instruction**: **Do NOT modify `src/components/ui/progress/Progress.vue`**.
2. **`F-07` — Pill / Squircle Radii (`rounded-3xl`, `rounded-4xl`)**:
   - **Reason**: In shadcn-vue, components are owned source code. Using a pill/squircle aesthetic across buttons, cards, dialogs, and navigation is an approved product design decision, not an architectural defect.
   - **Instruction**: **Do NOT rewrite component radii to generic `rounded-md`**.
3. **Bento Grid Gallery in `DonationCard.vue`**:
   - **Reason**: The 12-column bento media gallery is a custom product layout tailored for crowdfunding campaigns.
   - **Instruction**: **Preserve as-is**.
4. **Persian Variable Font Dot Settings (`font-variation-settings: "dots" 3`)**:
   - **Reason**: Legitimate typographical optimization for Persian readability in `IRANYekanXVF.woff2`.
   - **Instruction**: **Preserve in `main.css` and `typography.css`**.
5. **Dual Entry Build Configuration (`vite.config.ts`)**:
   - **Reason**: Provides clean separation between the main platform (`index.html`) and the design system showcase (`labs.html`).
   - **Instruction**: **Preserve in `vite.config.ts`**.

---

## Dependency Graph

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TASK DEPENDENCY GRAPH                           │
└────────────────────────────────────────────────────────────────────────┘

  [TASK-P0-01] Global CSS Isolation (spacing-radius.css)
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
  [TASK-P1-01] Typography Scoping   [TASK-P1-02] Destructive Theme Token
       │                                 │
       ▼                                 ▼
  [TASK-P0-02] RTL Logical Classes  [TASK-P1-03] Switch Decoupling
       │                                 │
       └────────────────┬────────────────┘
                        │
                        ▼
  [TASK-P1-04] ContextMenu / DropdownMenu Migration
                        │
                        ▼
  [TASK-P2-01 / P2-02] A11y DialogTitle & Icon Labels
                        │
                        ▼
  [TASK-P2-03 / P2-04] TopicAdminsModal Cleanup & Opacity Tokens
                        │
                        ▼
  [TASK-P3-01 / P3-02 / P3-03] Dependencies, Config Sync, Orphan Classes
```

---

## File Impact Matrix

| File Path | P0 | P1 | P2 | P3 | Blast Radius | Visual Check Required |
|---|---|---|---|---|---|---|
| `frontend/src/assets/spacing-radius.css` | ✓ | | | | Medium | Yes (Verify buttons & inputs) |
| `frontend/src/components/ui/native-select/NativeSelect.vue` | ✓ | | | | Low | Yes (Verify RTL dropdown chevron) |
| `frontend/src/components/ui/input-otp/InputOTPSlot.vue` | ✓ | | | | Low | Yes (Verify OTP border/radius in RTL) |
| `frontend/src/components/ui/alert/index.ts` | ✓ | | | | Low | Yes (Verify alert text alignment) |
| `frontend/src/components/ui/button/index.ts` | ✓ | | | | Low | Yes (Verify icon slot padding) |
| `frontend/src/components/ui/badge/index.ts` | ✓ | | | | Low | Yes (Verify badge icon padding) |
| `frontend/src/components/ui/toggle/index.ts` | ✓ | | | | Low | No |
| `frontend/src/assets/typography.css` | | ✓ | | | Medium | Yes (Verify card/dialog text margins) |
| `frontend/src/assets/main.css` | | ✓ | | | Low | No |
| `frontend/src/components/ui/switch/Switch.vue` | | ✓ | | | Low | Yes (Verify switch slide in LTR/RTL) |
| `frontend/src/components/PostContextMenu.vue` | | ✓ | | | Medium | Yes (Verify touch & right-click menu) |
| `frontend/src/components/TopicSettingsMenu.vue` | | ✓ | | | Medium | Yes (Verify topic settings popup) |
| `frontend/src/App.vue` | | | ✓ | | Low | No |
| `frontend/src/components/PostCard.vue` | | | ✓ | | Low | Yes (Verify audio play button a11y) |
| `frontend/src/components/TopicEditView.vue` | | | ✓ | | Low | No |
| `frontend/src/components/TopicAdminsModal.vue` | | | ✓ | | Low | No (Delete orphaned file) |
| `frontend/package.json` | | | | ✓ | Low | No (Re-run npm install) |
| `frontend/components.json` | | | | ✓ | Low | No |
| `frontend/src/components/ui/calendar/CalendarNextButton.vue` | | | | ✓ | Low | No |
| `frontend/src/components/ui/calendar/CalendarPrevButton.vue` | | | | ✓ | Low | No |
| `frontend/src/components/ui/select/SelectContent.vue` | | | | ✓ | Low | No |

---

## Detailed Refactor Tasks

---

### TASK-P0-01 — Global Base Stylesheet Isolation

**Priority:** P0 (Must Fix)  
**Audit Finding:** F-01  
**Severity:** HIGH  
**Status:** Planned  

#### Problem
In `frontend/src/assets/spacing-radius.css`, high-specificity `@apply` rules are declared inside `@layer base` targeting raw HTML elements (`button`, `input[type="text"]`, `textarea`, `select`) and attribute selectors (`.card`, `[role="dialog"]`, `.popover`, `[data-radix-popper-content-wrapper]`). This leaks unwanted padding, fixed heights (`h-10`), and borders into all raw elements and Radix popper portals, conflicting with `cva` variants in `Button.vue`, `Input.vue`, `PopoverContent.vue`, and `DialogContent.vue`.

#### Evidence
[`frontend/src/assets/spacing-radius.css:17-43`](file:///f:/AVA/tafakor/frontend/src/assets/spacing-radius.css#L17-L43)

#### Current Architecture
Global CSS aggressively formats any `button`, `input`, `[role="dialog"]`, or `[data-radix-popper-content-wrapper]` across the entire DOM, bypassing component encapsulation.

#### Target Architecture
`spacing-radius.css` must retain only font-feature settings and layout utility classes (`.form-group-layout`, `.form-actions-layout`, `.section-padding`). Element styling is delegated entirely to the individual UI components in `src/components/ui/`.

#### Files to Change
- [`frontend/src/assets/spacing-radius.css`](file:///f:/AVA/tafakor/frontend/src/assets/spacing-radius.css)

#### Files to Inspect
- `frontend/src/components/ui/button/Button.vue`
- `frontend/src/components/ui/input/Input.vue`
- `frontend/src/components/ui/dialog/DialogContent.vue`
- `frontend/src/components/ui/popover/PopoverContent.vue`

#### Files That Must Not Change
- `frontend/src/assets/base.css`

#### Implementation Steps
1. Open `frontend/src/assets/spacing-radius.css`.
2. Remove lines 16–43 (the `@apply` blocks for `button, .btn`, `input[type="text"]...`, `.card, [role="dialog"]`, and `.popover, [data-radix-popper-content-wrapper]`).
3. Preserve lines 4–14 (the Persian font-feature settings for inputs and buttons).
4. Preserve lines 45–62 (`@layer utilities` containing `.form-group-layout`, `.form-actions-layout`, `.section-padding`).
5. Run `npm run build` to verify there are no missing utility errors.

#### Before
```css
/* frontend/src/assets/spacing-radius.css */
@layer base {
  button, .btn {
    @apply rounded-md px-4 py-2 text-sm font-medium transition-all gap-2 inline-flex items-center justify-center;
  }
  input[type="text"], input[type="email"], input[type="password"], textarea, select {
    @apply rounded-md border border-input bg-background px-3 py-2 text-sm h-10 w-full;
    @apply focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2;
  }
  .card, [role="dialog"] {
    @apply rounded-lg border bg-card text-card-foreground shadow-sm p-6;
  }
  .popover, [data-radix-popper-content-wrapper] {
    @apply rounded-md border bg-popover text-popover-foreground p-4 shadow-md outline-none;
  }
}
```

#### After
```css
/* frontend/src/assets/spacing-radius.css */
@layer base {
  /* Persian font features for inputs and interactive elements */
  input,
  textarea,
  select,
  button,
  .btn,
  [data-slot="input-otp-slot"] {
    font-family: 'IRANYekanX', var(--font-sans), sans-serif !important;
    font-feature-settings: "ss01" on, "cv11" on !important;
    font-variation-settings: "dots" 3 !important;
  }
}

@layer utilities {
  .form-group-layout {
    @apply grid gap-4 w-full;
  }
  .form-actions-layout {
    @apply flex items-center justify-end gap-3 mt-6;
  }
  .section-padding {
    @apply p-4 md:p-6 lg:p-8;
  }
}
```

#### Why This Is Better
Eliminates specificity wars between global CSS and shadcn-vue `cva` definitions. Prevents poppers, popovers, and dialogs from receiving unwanted double-padding.

#### shadcn-vue Alignment
Strictly adheres to shadcn-vue's component-ownership model where each primitive encapsulates its own styles via `cva`.

#### Regression Risks
Any raw `<button>` in an application component that relied on global `@apply` instead of importing `<Button>` may lose its base padding. (Mitigation: Check views; all major views already import `@/components/ui/button`).

#### Verification
- Launch `npm run dev` and navigate to `/showcase` and `/playground`.
- Open a `Popover` and `Dialog` — verify no double-border or double-padding appears.
- Test `Button` size variants (`size="xs"`, `size="icon"`, `size="sm"`) to verify they render with exact proportions.

#### Rollback
Revert `frontend/src/assets/spacing-radius.css` via git checkout.

#### Estimated Scope
Small (1 file edited, ~30 lines removed).

---

### TASK-P0-02 — RTL Logical Property Alignment in Primitives

**Priority:** P0 (Must Fix)  
**Audit Finding:** F-03  
**Severity:** HIGH  
**Status:** Planned  

#### Problem
Several base UI components use physical directional utility classes (`pr-*`, `pl-*`, `border-r`, `border-l`, `text-left`, `right-*`) that invert or misalign content in Persian RTL layout mode:
1. `NativeSelect.vue`: Hardcodes `pr-8 pl-3` and places the chevron icon at `right-2.5`, obscuring Persian text at the start of the input.
2. `InputOTPSlot.vue`: Hardcodes `border-r first:rounded-l-3xl first:border-l last:rounded-r-3xl`, inverting the outer corner radius and border dividers in RTL.
3. `Alert/index.ts`: Hardcodes `text-left` and `has-data-[slot=alert-action]:pr-18`, left-aligning Persian alerts.
4. `button/index.ts`, `badge/index.ts`, `toggle/index.ts`: Use physical `has-data-[icon=inline-end]:pr-*` and `has-data-[icon=inline-start]:pl-*`.

#### Evidence
- [`NativeSelect.vue:43-49`](file:///f:/AVA/tafakor/frontend/src/components/ui/native-select/NativeSelect.vue#L43-L49)
- [`InputOTPSlot.vue:25`](file:///f:/AVA/tafakor/frontend/src/components/ui/input-otp/InputOTPSlot.vue#L25)
- [`alert/index.ts:9`](file:///f:/AVA/tafakor/frontend/src/components/ui/alert/index.ts#L9)
- [`button/index.ts:19-22`](file:///f:/AVA/tafakor/frontend/src/components/ui/button/index.ts#L19-L22)
- [`badge/index.ts:7`](file:///f:/AVA/tafakor/frontend/src/components/ui/badge/index.ts#L7)
- [`toggle/index.ts:15-17`](file:///f:/AVA/tafakor/frontend/src/components/ui/toggle/index.ts#L15-L17)

#### Current Architecture
Physical CSS utilities assume a permanent Left-to-Right reading order.

#### Target Architecture
Use Tailwind CSS logical properties (`pe-*`, `ps-*`, `border-e`, `border-s`, `rounded-s-*`, `rounded-e-*`, `start-*`, `end-*`, `text-start`) that automatically adapt to both LTR and RTL.

#### Files to Change
- [`frontend/src/components/ui/native-select/NativeSelect.vue`](file:///f:/AVA/tafakor/frontend/src/components/ui/native-select/NativeSelect.vue)
- [`frontend/src/components/ui/input-otp/InputOTPSlot.vue`](file:///f:/AVA/tafakor/frontend/src/components/ui/input-otp/InputOTPSlot.vue)
- [`frontend/src/components/ui/alert/index.ts`](file:///f:/AVA/tafakor/frontend/src/components/ui/alert/index.ts)
- [`frontend/src/components/ui/button/index.ts`](file:///f:/AVA/tafakor/frontend/src/components/ui/button/index.ts)
- [`frontend/src/components/ui/badge/index.ts`](file:///f:/AVA/tafakor/frontend/src/components/ui/badge/index.ts)
- [`frontend/src/components/ui/toggle/index.ts`](file:///f:/AVA/tafakor/frontend/src/components/ui/toggle/index.ts)

#### Files to Inspect
- `frontend/src/showcase/ShowcaseView.vue`
- `frontend/src/components/LoginCard.vue`

#### Implementation Steps
1. **In `NativeSelect.vue`**:
   - Replace `py-1 pr-8 pl-3` with `py-1 pe-8 ps-3`.
   - Replace `top-1/2 right-2.5` on `ChevronDownIcon` with `top-1/2 end-2.5`.
2. **In `InputOTPSlot.vue`**:
   - Replace `border-y border-r text-sm transition-all outline-none first:rounded-l-3xl first:border-l last:rounded-r-3xl` with `border-y border-e text-sm transition-all outline-none first:rounded-s-3xl first:border-s last:rounded-e-3xl`.
3. **In `alert/index.ts`**:
   - Replace `text-left` with `text-start`.
   - Replace `has-data-[slot=alert-action]:pr-18` with `has-data-[slot=alert-action]:pe-18`.
4. **In `button/index.ts`**:
   - In `size.default`: replace `has-data-[icon=inline-end]:pr-2.5 has-data-[icon=inline-start]:pl-2.5` with `has-data-[icon=inline-end]:pe-2.5 has-data-[icon=inline-start]:ps-2.5`.
   - In `size.xs`: replace `has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2` with `has-data-[icon=inline-end]:pe-2 has-data-[icon=inline-start]:ps-2`.
   - In `size.sm`: replace `has-data-[icon=inline-end]:pr-2 has-data-[icon=inline-start]:pl-2` with `has-data-[icon=inline-end]:pe-2 has-data-[icon=inline-start]:ps-2`.
   - In `size.lg`: replace `has-data-[icon=inline-end]:pr-3 has-data-[icon=inline-start]:pl-3` with `has-data-[icon=inline-end]:pe-3 has-data-[icon=inline-start]:ps-3`.
5. **In `badge/index.ts`**:
   - Replace `has-data-[icon=inline-end]:pr-1.5 has-data-[icon=inline-start]:pl-1.5` with `has-data-[icon=inline-end]:pe-1.5 has-data-[icon=inline-start]:ps-1.5`.
6. **In `toggle/index.ts`**:
   - Replace `has-data-[icon=inline-end]:pr-* has-data-[icon=inline-start]:pl-*` with `pe-*` and `ps-*`.

#### Before & After

**NativeSelect.vue:**
```vue
<!-- Before -->
<select :class="cn('... py-1 pr-8 pl-3 ...', props.class)">
<ChevronDownIcon class="... top-1/2 right-2.5 ..." />

<!-- After -->
<select :class="cn('... py-1 pe-8 ps-3 ...', props.class)">
<ChevronDownIcon class="... top-1/2 end-2.5 ..." />
```

**InputOTPSlot.vue:**
```vue
<!-- Before -->
:class="cn('... border-y border-r first:rounded-l-3xl first:border-l last:rounded-r-3xl ...', props.class)"

<!-- After -->
:class="cn('... border-y border-e first:rounded-s-3xl first:border-s last:rounded-e-3xl ...', props.class)"
```

#### Why This Is Better
Ensures seamless visual rendering in both Persian (`dir="rtl"`) and English (`dir="ltr"`). The chevron icon in `NativeSelect` moves to the end of the input, the OTP capsule rounds correctly at both ends, and alerts align with reading direction.

#### shadcn-vue Alignment
Directly aligns with official shadcn-vue RTL documentation ([https://www.shadcn-vue.com/docs/rtl](https://www.shadcn-vue.com/docs/rtl)).

#### Regression Risks
None. Tailwind CSS v4 compiles `pe-*`, `ps-*`, `start-*`, `end-*` to native CSS logical properties (`padding-inline-end`, `padding-inline-start`, `inset-inline-end`, etc.).

#### Verification
- In `ShowcaseView.vue`, inspect `NativeSelect`, `InputOTP`, `Button` with icons, and `Alert` in both Persian and English.
- Verify OTP slots have rounded outer edges on slot 0 and slot 3 in RTL.
- Verify `NativeSelect` chevron is on the left in RTL and right in LTR without overlapping option text.

#### Rollback
Revert the 6 files via git checkout.

#### Estimated Scope
Small (6 files, 1–3 lines changed per file).

---

### TASK-P1-01 — Typography CSS Scoping & Prose Class Isolation

**Priority:** P1 (Should Fix)  
**Audit Finding:** F-05  
**Severity:** MEDIUM  
**Status:** Planned  

#### Problem
In `frontend/src/assets/typography.css`, shadcn-vue typography classes are attached directly to raw HTML tags (`h1`, `h2`, `h3`, `h4`, `p:not(:first-child)`, `table`, `ul`, `ol`). In particular, `p:not(:first-child) { @apply mt-6; }` injects a 24px top margin into every secondary paragraph inside Cards, Dialogs, and Alerts, forcing developers to write manual inline override hacks.

#### Evidence
[`frontend/src/assets/typography.css:13-114`](file:///f:/AVA/tafakor/frontend/src/assets/typography.css#L13-L114)

#### Current Architecture
Global tag selectors mutate standard HTML elements everywhere.

#### Target Architecture
Move typography recipes into composable utility classes (`.typography-h1`, `.typography-h2`, `.typography-p`, etc.) and a `.prose-persian` container class for article/markdown content.

#### Files to Change
- [`frontend/src/assets/typography.css`](file:///f:/AVA/tafakor/frontend/src/assets/typography.css)

#### Files to Inspect
- `frontend/src/components/ui/card/CardTitle.vue`
- `frontend/src/components/ui/dialog/DialogTitle.vue`
- `frontend/src/components/LoginCard.vue`
- `frontend/src/showcase/ShowcaseView.vue`

#### Implementation Steps
1. Open `frontend/src/assets/typography.css`.
2. Convert tag selectors `h1`, `h2`, `h3`, `h4`, `p`, `blockquote`, `table`, `ul`, `ol`, `code` into composable utility classes: `.typography-h1`, `.typography-h2`, `.typography-h3`, `.typography-h4`, `.typography-p`, `.typography-blockquote`, `.typography-table`, `.typography-ul`, `.typography-ol`, `.typography-code`.
3. Wrap longform prose rules under a `.prose-persian` parent selector so markdown content continues to receive automatic paragraph and list spacing.
4. Keep the body font settings (lines 3–10) in `@layer base`.

#### Before & After
```css
/* Before */
@layer base {
  p {
    @apply leading-7 text-foreground/90;
    &:not(:first-child) {
      @apply mt-6;
    }
  }
}

/* After */
@layer utilities {
  .typography-p {
    @apply leading-7 text-foreground/90;
  }
  
  .prose-persian {
    p {
      @apply leading-7 text-foreground/90;
      &:not(:first-child) {
        @apply mt-6;
      }
    }
    h2 {
      @apply scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight mt-10 first:mt-0;
    }
  }
}
```

#### Why This Is Better
Prevents standard UI component text from receiving unwanted paragraph margins (`mt-6`) or heading borders (`border-b pb-2`) while keeping rich text content nicely styled.

#### shadcn-vue Alignment
Directly follows official shadcn-vue typography guidelines ([https://www.shadcn-vue.com/docs/components/typography](https://www.shadcn-vue.com/docs/components/typography)).

#### Regression Risks
Any long-form article view that relied on raw `<p>` tags without utility classes will lose paragraph top margins. (Mitigation: Add `class="prose-persian"` to article containers if present).

#### Verification
- Open `LoginCard.vue`, `PostCard.vue`, `DonationCard.vue` — verify compact paragraph text is not pushed down by 24px margins.
- Open `ShowcaseView.vue` typography section to verify all typography utilities render correctly.

#### Rollback
Revert `frontend/src/assets/typography.css` via git checkout.

#### Estimated Scope
Medium (1 file edited, ~80 lines restructured).

---

### TASK-P1-02 — Destructive Theme Token Completion

**Priority:** P1 (Should Fix)  
**Audit Finding:** F-06  
**Severity:** MEDIUM  
**Status:** Planned  

#### Problem
In `frontend/src/assets/main.css`, `--color-destructive: var(--destructive);` is declared in `@theme inline`, but `--destructive-foreground` / `--color-destructive-foreground` is completely missing from `@theme inline`, `:root`, and `.dark`.

#### Evidence
[`frontend/src/assets/main.css:58, 94, 129`](file:///f:/AVA/tafakor/frontend/src/assets/main.css#L58)

#### Current Architecture
Missing foreground token forces `Button.vue` to use subtle `bg-destructive/10 text-destructive` styling rather than supporting full solid destructive variants.

#### Target Architecture
Define `--destructive-foreground` in `:root`, `.dark`, and `--color-destructive-foreground` in `@theme inline`.

#### Files to Change
- [`frontend/src/assets/main.css`](file:///f:/AVA/tafakor/frontend/src/assets/main.css)

#### Implementation Steps
1. In `src/assets/main.css` under `@theme inline`:
   - Add `--color-destructive-foreground: var(--destructive-foreground);` after `--color-destructive: var(--destructive);`.
2. In `:root`:
   - Add `--destructive-foreground: oklch(0.988 0.003 106.5);` after `--destructive: oklch(0.577 0.245 27.325);`.
3. In `.dark`:
   - Add `--destructive-foreground: oklch(0.988 0.003 106.5);` after `--destructive: oklch(0.704 0.191 22.216);`.

#### Before & After
```css
/* Before */
@theme inline {
  --color-destructive: var(--destructive);
}
:root {
  --destructive: oklch(0.577 0.245 27.325);
}
.dark {
  --destructive: oklch(0.704 0.191 22.216);
}

/* After */
@theme inline {
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
}
:root {
  --destructive: oklch(0.577 0.245 27.325);
  --destructive-foreground: oklch(0.988 0.003 106.5);
}
.dark {
  --destructive: oklch(0.704 0.191 22.216);
  --destructive-foreground: oklch(0.988 0.003 106.5);
}
```

#### Why This Is Better
Completes the semantic theme token contract, enabling solid destructive buttons, destructive alert badges, and destructive toasts.

#### shadcn-vue Alignment
Matches official shadcn-vue theming documentation ([https://www.shadcn-vue.com/docs/theming](https://www.shadcn-vue.com/docs/theming)).

#### Regression Risks
None. Adding new theme variables is purely additive.

#### Verification
- Inspect destructive buttons in `ShowcaseView.vue` to confirm contrast in both light and dark modes.

#### Rollback
Revert the 3 added lines in `src/assets/main.css`.

#### Estimated Scope
Small (1 file, 3 lines added).

---

### TASK-P1-03 — Decouple Switch Primitive from Pinia Store

**Priority:** P1 (Should Fix)  
**Audit Finding:** F-09  
**Severity:** MEDIUM  
**Status:** Planned  

#### Problem
In `frontend/src/components/ui/switch/Switch.vue`, the component directly imports `useLanguageStore` from `@/stores/languageStore` to calculate whether the thumb translation should be `-translate-x-5` or `translate-x-5`. A base primitive in `src/components/ui/` should not be tightly coupled to an application-level Pinia store.

#### Evidence
[`frontend/src/components/ui/switch/Switch.vue:4-6, 48-51`](file:///f:/AVA/tafakor/frontend/src/components/ui/switch/Switch.vue#L4-L6)

#### Current Architecture
`Switch.vue` relies on JavaScript runtime store evaluation to determine slide direction.

#### Target Architecture
Use Tailwind CSS RTL variant classes (`data-[state=checked]:translate-x-5 rtl:data-[state=checked]:-translate-x-5`) so the thumb direction is managed purely via CSS and HTML document direction.

#### Files to Change
- [`frontend/src/components/ui/switch/Switch.vue`](file:///f:/AVA/tafakor/frontend/src/components/ui/switch/Switch.vue)

#### Files to Inspect
- `frontend/src/showcase/ShowcaseView.vue`
- `frontend/src/components/BotConnectionCard.vue`

#### Implementation Steps
1. Open `frontend/src/components/ui/switch/Switch.vue`.
2. Remove `import { useLanguageStore } from "@/stores/languageStore"` and `const languageStore = useLanguageStore()`.
3. In `SwitchThumb`, replace the ternary expression with pure Tailwind classes:
   - For `size="default"`: `'h-5 w-5 data-[state=checked]:translate-x-5 rtl:data-[state=checked]:-translate-x-5 data-[state=unchecked]:translate-x-0'`
   - For `size="sm"`: `'h-3 w-3 data-[state=checked]:translate-x-3 rtl:data-[state=checked]:-translate-x-3 data-[state=unchecked]:translate-x-0'`

#### Before & After
```vue
<!-- Before -->
<script setup lang="ts">
import { SwitchRoot, SwitchThumb } from "reka-ui"
import { cn } from "@/lib/utils"
import { useLanguageStore } from "@/stores/languageStore"

const languageStore = useLanguageStore()
// ...
</script>

<template>
  <SwitchRoot ...>
    <SwitchThumb
      :class="cn(
        'pointer-events-none block rounded-full bg-background shadow-lg ring-0 transition-transform dark:data-[state=checked]:bg-background',
        size === 'default' 
          ? (languageStore.isFa ? 'h-5 w-5 data-[state=checked]:-translate-x-5' : 'h-5 w-5 data-[state=checked]:translate-x-5') 
          : (languageStore.isFa ? 'h-3 w-3 data-[state=checked]:-translate-x-3' : 'h-3 w-3 data-[state=checked]:translate-x-3')
      )"
    />
  </SwitchRoot>
</template>

<!-- After -->
<script setup lang="ts">
import { SwitchRoot, SwitchThumb } from "reka-ui"
import { cn } from "@/lib/utils"

const props = withDefaults(defineProps<{ ... }>(), { size: "default" })
</script>

<template>
  <SwitchRoot ...>
    <SwitchThumb
      :class="cn(
        'pointer-events-none block rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=unchecked]:translate-x-0 dark:data-[state=checked]:bg-background',
        size === 'default'
          ? 'h-5 w-5 data-[state=checked]:translate-x-5 rtl:data-[state=checked]:-translate-x-5'
          : 'h-3 w-3 data-[state=checked]:translate-x-3 rtl:data-[state=checked]:-translate-x-3'
      )"
    />
  </SwitchRoot>
</template>
```

#### Why This Is Better
Restores complete decoupling. `Switch.vue` can now be used in standalone packages, unit tests, and Storybook without initializing Pinia.

#### shadcn-vue Alignment
Matches official shadcn-vue Switch implementation ([https://www.shadcn-vue.com/docs/components/switch](https://www.shadcn-vue.com/docs/components/switch)).

#### Regression Risks
None. Verified with `<ConfigProvider :dir="dir">` and `<html dir="rtl">`.

#### Verification
- Toggle switches in `ShowcaseView.vue` and `BotConnectionCard.vue`.
- Switch language between Farsi and English; verify the thumb slides in the correct direction in both modes.

#### Rollback
Revert `Switch.vue` via git checkout.

#### Estimated Scope
Small (1 file, ~10 lines changed).

---

### TASK-P1-04 — ContextMenu & DropdownMenu Primitive Refactoring

**Priority:** P1 (Should Fix)  
**Audit Finding:** F-08  
**Severity:** MEDIUM  
**Status:** Planned  

#### Problem
`frontend/src/components/PostContextMenu.vue` and `frontend/src/components/TopicSettingsMenu.vue` manually compute floating coordinates (`window.innerWidth`, `window.innerHeight`, `Math.max(16, ...)`) in JavaScript, render fixed-position `div`s, and manage overlay click dismissals manually. This bypasses Reka UI's built-in collision detection, portal boundary management, focus trap, and Escape key handling.

#### Evidence
- [`frontend/src/components/PostContextMenu.vue:35-94`](file:///f:/AVA/tafakor/frontend/src/components/PostContextMenu.vue#L35-L94)
- [`frontend/src/components/TopicSettingsMenu.vue:36-62`](file:///f:/AVA/tafakor/frontend/src/components/TopicSettingsMenu.vue#L36-L62)

#### Current Architecture
Custom JavaScript coordinate math with fixed positioning and manual teleport.

#### Target Architecture
- `PostContextMenu.vue`: Refactor to use `ContextMenu` primitives (`ContextMenuRoot`, `ContextMenuTrigger`, `ContextMenuContent`, `ContextMenuItem`, `ContextMenuSeparator`) while preserving mobile touch long-press trigger logic.
- `TopicSettingsMenu.vue`: Refactor to use `DropdownMenu` primitives (`DropdownMenuRoot`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`).

#### Files to Change
- [`frontend/src/components/PostContextMenu.vue`](file:///f:/AVA/tafakor/frontend/src/components/PostContextMenu.vue)
- [`frontend/src/components/TopicSettingsMenu.vue`](file:///f:/AVA/tafakor/frontend/src/components/TopicSettingsMenu.vue)

#### Files to Inspect
- `frontend/src/components/PostCard.vue`
- `frontend/src/components/PlatformHeader.vue`

#### Implementation Steps
1. Refactor `TopicSettingsMenu.vue` to wrap its options trigger button in `DropdownMenuTrigger` and its menu items in `DropdownMenuContent` with `align="end"`.
2. Remove manual `menuStyle`, `viewportWidth`, and `triggerRect` coordinate calculations.
3. In `PostContextMenu.vue`, wrap post card contents in `ContextMenuTrigger` and use `ContextMenuContent` for the action popup.
4. Preserve existing event emits (`edit`, `delete`, `pin`, `react`, `copy`).

#### Why This Is Better
Provides automatic viewport collision detection, focus restoration, arrow-key navigation, Escape key dismissal, and backdrop blur without custom JavaScript coordinate math.

#### shadcn-vue Alignment
Directly leverages official shadcn-vue `ContextMenu` and `DropdownMenu` components.

#### Regression Risks
On mobile touch devices, verify that long-press triggers the context menu smoothly. (Reka UI `ContextMenu` natively supports long-press on touch).

#### Verification
- Right-click post cards on desktop → context menu appears at cursor.
- Long-press post cards on mobile viewport → context menu appears with haptic feedback.
- Click topic settings button in `PlatformHeader.vue` → dropdown opens aligned to the button.

#### Rollback
Revert `PostContextMenu.vue` and `TopicSettingsMenu.vue` via git checkout.

#### Estimated Scope
Medium (2 files refactored).

---

### TASK-P2-01 — Accessible Name for Login Dialog

**Priority:** P2 (Recommended)  
**Audit Finding:** F-14  
**Severity:** LOW  
**Status:** Planned  

#### Problem
In `frontend/src/App.vue`, `DialogContent` contains `DialogDescription` but omits `DialogTitle`, triggering a Radix/Reka UI accessibility console warning (`DialogContent requires a DialogTitle for accessibility`).

#### Evidence
[`frontend/src/App.vue:113-124`](file:///f:/AVA/tafakor/frontend/src/App.vue#L113-L124)

#### Implementation Steps
1. Open `frontend/src/App.vue`.
2. Import `DialogTitle` from `@/components/ui/dialog`.
3. Add `<DialogTitle class="sr-only">{{ languageStore.t('ورود به حساب کاربری', 'User Login') }}</DialogTitle>` inside `DialogContent`.

#### Before & After
```vue
<!-- Before -->
<Dialog :open="userStore.isLoginModalOpen" @update:open="(val) => userStore.isLoginModalOpen = val">
  <DialogContent :show-close-button="true" class="..." :dir="languageStore.dir">
    <DialogDescription class="sr-only">{{ languageStore.t('ورود به حساب کاربری تفکر', 'Tafakor User Login') }}</DialogDescription>
    <LoginCard @stateChange="handleLoginStateChange" />
  </DialogContent>
</Dialog>

<!-- After -->
<Dialog :open="userStore.isLoginModalOpen" @update:open="(val) => userStore.isLoginModalOpen = val">
  <DialogContent :show-close-button="true" class="..." :dir="languageStore.dir">
    <DialogTitle class="sr-only">{{ languageStore.t('ورود به حساب کاربری', 'User Login') }}</DialogTitle>
    <DialogDescription class="sr-only">{{ languageStore.t('ورود به حساب کاربری تفکر', 'Tafakor User Login') }}</DialogDescription>
    <LoginCard @stateChange="handleLoginStateChange" />
  </DialogContent>
</Dialog>
```

#### Estimated Scope
Small (1 file, 2 lines added).

---

### TASK-P2-02 — Accessible Labels for Icon-Only Actions

**Priority:** P2 (Recommended)  
**Severity:** LOW  
**Status:** Planned  

#### Problem
Several icon-only buttons (such as the audio play/pause toggle in `PostCard.vue:588` and header action icons) lack `aria-label` or `<span class="sr-only">`, preventing screen readers from announcing their purpose.

#### Evidence
[`frontend/src/components/PostCard.vue:588-594`](file:///f:/AVA/tafakor/frontend/src/components/PostCard.vue#L588-L594)

#### Implementation Steps
1. In `PostCard.vue:588`, add `:aria-label="isAudioPlaying ? languageStore.t('توقف صوت', 'Pause audio') : languageStore.t('پخش صوت', 'Play audio')"` to the audio toggle button.
2. In `TopicMessageInput.vue`, add `aria-label` to the voice record, AI refiner, and attachment buttons.

#### Estimated Scope
Small (2 files, 3–4 attributes added).

---

### TASK-P2-03 — Deprecate and Remove Duplicate `TopicAdminsModal.vue`

**Priority:** P2 (Recommended)  
**Audit Finding:** F-10  
**Severity:** LOW  
**Status:** Planned  

#### Problem
`frontend/src/components/TopicAdminsModal.vue` (385 lines) is a duplicate implementation of the active `TopicAdminsView.vue` (600 lines) and is never mounted in any active view.

#### Evidence
[`frontend/src/components/TopicAdminsModal.vue`](file:///f:/AVA/tafakor/frontend/src/components/TopicAdminsModal.vue)

#### Implementation Steps
1. Verify no runtime imports exist for `TopicAdminsModal.vue` (`grep_search` confirmed zero imports).
2. Delete `frontend/src/components/TopicAdminsModal.vue`.

#### Estimated Scope
Small (1 unused file deleted).

---

### TASK-P2-04 — Standardize Literal Opacity Colors to Semantic Tokens

**Priority:** P2 (Recommended)  
**Audit Finding:** F-08 (Theming)  
**Severity:** LOW  
**Status:** Planned  

#### Problem
`PostCard.vue` and `TopicEditView.vue` use literal color opacities (`bg-white/5 dark:bg-black/10`, `bg-white/2 dark:bg-black/2`) instead of semantic tokens (`bg-muted/30`, `bg-card`).

#### Evidence
[`frontend/src/components/PostCard.vue:576, 625, 648`](file:///f:/AVA/tafakor/frontend/src/components/PostCard.vue#L576)

#### Implementation Steps
1. Replace `bg-white/5 dark:bg-black/10` in `PostCard.vue:576` with `bg-muted/30`.
2. Replace `bg-white/2 dark:bg-black/2` in `PostCard.vue:625` with `bg-muted/20`.

#### Estimated Scope
Small (1 file, 3 class strings updated).

---

### TASK-P3-01 — Dependency Pruning

**Priority:** P3 (Optional)  
**Audit Finding:** F-11  
**Severity:** LOW  
**Status:** Planned  

#### Problem
`package.json` contains unused duplicate package `lucide-vue-next` (the repository exclusively imports from `@lucide/vue`) as well as `autoprefixer` and `postcss` in `devDependencies` (which are redundant with Tailwind v4 `@tailwindcss/vite`).

#### Evidence
[`frontend/package.json:21, 37, 39`](file:///f:/AVA/tafakor/frontend/package.json#L21)

#### Implementation Steps
1. In `frontend/package.json`:
   - Remove `"lucide-vue-next": "^1.0.0"` from `dependencies`.
   - Remove `"autoprefixer": "^10.5.0"` and `"postcss": "^8.5.15"` from `devDependencies`.
2. Run `npm install` to update `package-lock.json`.
3. Run `npm run build` to verify the build compiles cleanly without them.

#### Estimated Scope
Small (1 file edited, lockfile updated).

---

### TASK-P3-02 — Sync `components.json` Configuration

**Priority:** P3 (Optional)  
**Audit Finding:** F-02, F-12  
**Severity:** LOW  
**Status:** Planned  

#### Problem
`frontend/components.json` has `"rtl": false` and contains a stale `"composables": "@/composables"` alias pointing to a non-existent directory.

#### Evidence
[`frontend/components.json:14, 21`](file:///f:/AVA/tafakor/frontend/components.json#L14)

#### Implementation Steps
1. In `frontend/components.json`:
   - Set `"rtl": true`.
   - Remove `"composables": "@/composables"` from `aliases`.

#### Estimated Scope
Small (1 file, 2 lines updated).

---

### TASK-P3-03 — Remove Undefined Orphan Classes

**Priority:** P3 (Optional)  
**Audit Finding:** F-13  
**Severity:** LOW  
**Status:** Planned  

#### Problem
`CalendarNextButton.vue`, `CalendarPrevButton.vue`, and `SelectContent.vue` contain ghost utility classes `cn-rtl-flip` and `cn-menu-translucent` that are never defined in CSS.

#### Evidence
- [`CalendarNextButton.vue:29`](file:///f:/AVA/tafakor/frontend/src/components/ui/calendar/CalendarNextButton.vue#L29)
- [`SelectContent.vue:39`](file:///f:/AVA/tafakor/frontend/src/components/ui/select/SelectContent.vue#L39)

#### Implementation Steps
1. In `CalendarNextButton.vue` and `CalendarPrevButton.vue`: replace `class="cn-rtl-flip size-4"` with `class="rtl:rotate-180 size-4"`.
2. In `SelectContent.vue`: remove `cn-menu-translucent` from the class string.

#### Estimated Scope
Small (3 files, 1 line edited per file).

---

## Verification Strategy

### 1. Static Verification
Run all existing repository scripts:
```bash
# Typecheck TypeScript across all components and views
npm run type-check

# Compile production bundle for Vite
npm run build-only

# Run full parallel build pipeline
npm run build
```

### 2. Component Verification Matrix

| Component | LTR Mode | RTL Mode | Light Theme | Dark Theme | Keyboard Trap | Mobile Touch | Focus Ring |
|---|---|---|---|---|---|---|---|
| **NativeSelect** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **InputOTP** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Alert** | ✓ | ✓ | ✓ | ✓ | — | ✓ | — |
| **Button** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Switch** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **PostContextMenu** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (Long-press) | ✓ |
| **TopicSettingsMenu**| ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Dialog (Login)** | ✓ | ✓ | ✓ | ✓ | ✓ (Escape) | ✓ | ✓ |

### 3. Visual Verification Checklist
- **NativeSelect**: Chevron is on the left in Persian RTL (`end-2.5`) and right in English LTR without covering text.
- **InputOTP**: Slot group capsule has rounded start on slot 0 and rounded end on slot 3 in both directions.
- **Switch**: Slides to `-translate-x-5` in Persian RTL and `translate-x-5` in English LTR.
- **Popover & Dialog**: No duplicate padding or double borders from global stylesheets.
- **Prose vs Cards**: Cards and dialogs have tight paragraph spacing without 24px margins.

---

## Regression Risks

| Risk ID | Potential Regression | Impacted Area | Severity | Mitigation & Safety Check |
|---|---|---|---|---|
| **R-01** | Raw `<button>` tags lose padding when removing global `@apply` | Un-migrated legacy buttons | Low | Inspect views; all primary actions use shadcn `<Button>` primitive. |
| **R-02** | Context menu fails to open on mobile touch devices | `PostCard.vue` long-press | Medium | Test `touchstart`/`touchend` events on real touch device or Chrome DevTools touch emulation. |
| **R-03** | Switch thumb doesn't move on checked state toggle | `Switch.vue` | Low | Verified via Tailwind `data-[state=checked]:translate-x-5 rtl:data-[state=checked]:-translate-x-5`. |
| **R-04** | Paragraphs lose spacing in long articles | Rich text prose | Low | Wrapped under `.prose-persian` utility. |

---

## Rollback Strategy

Every task in this plan operates on independent files. To rollback any specific task without affecting others:

1. **Global CSS Isolation Rollback**:
   ```bash
   git checkout origin/main -- frontend/src/assets/spacing-radius.css
   ```
2. **RTL Primitives Rollback**:
   ```bash
   git checkout origin/main -- frontend/src/components/ui/native-select/ frontend/src/components/ui/input-otp/ frontend/src/components/ui/alert/ frontend/src/components/ui/button/
   ```
3. **Switch Decoupling Rollback**:
   ```bash
   git checkout origin/main -- frontend/src/components/ui/switch/Switch.vue
   ```
4. **Context Menu Rollback**:
   ```bash
   git checkout origin/main -- frontend/src/components/PostContextMenu.vue frontend/src/components/TopicSettingsMenu.vue
   ```

---

## Recommended Execution Order

Execute tasks in the following sequential order to guarantee zero broken intermediate states:

```
Step 1: Baseline Verification (`npm run type-check` && `npm run build`)
Step 2: TASK-P0-01 — Global Base Stylesheet Isolation (`spacing-radius.css`)
Step 3: TASK-P0-02 — RTL Logical Property Alignment in Primitives
Step 4: TASK-P1-01 — Typography CSS Scoping (`typography.css`)
Step 5: TASK-P1-02 — Destructive Theme Token Completion (`main.css`)
Step 6: TASK-P1-03 — Decouple Switch Primitive from Pinia Store (`Switch.vue`)
Step 7: TASK-P1-04 — ContextMenu & DropdownMenu Primitive Refactoring
Step 8: TASK-P2-01 & TASK-P2-02 — Accessibility DialogTitle & Icon Labels
Step 9: TASK-P2-03 & TASK-P2-04 — Delete Duplicate Admin Modal & Clean Opacities
Step 10: TASK-P3-01, P3-02, P3-03 — Prune Dependencies, Update components.json & Orphan CSS
Step 11: Final Full Verification (`npm run type-check` && `npm run build` && visual walkthrough)
```

---

## Final Acceptance Criteria

### Architecture
- [ ] No raw global element selectors in `spacing-radius.css` interfere with shadcn-vue `cva` variants.
- [ ] UI primitives in `src/components/ui/` do not import Pinia stores.
- [ ] Context menus and dropdowns delegate collision detection and focus handling to Reka UI primitives.

### RTL Support
- [ ] `NativeSelect.vue` chevron appears at `end-2.5` without overlapping text in RTL.
- [ ] `InputOTPSlot.vue` capsule shape rounds the outer start and end slots correctly in RTL.
- [ ] `Alert` text aligns with document direction (`text-start`).
- [ ] `Button`, `Badge`, and `Toggle` icon slots use `pe-*` and `ps-*`.

### Theming
- [ ] `--destructive-foreground` is defined in `:root`, `.dark`, and `@theme inline`.
- [ ] Light and dark themes switch cleanly without unstyled flashes.

### Accessibility
- [ ] Global Login Dialog in `App.vue` contains `<DialogTitle class="sr-only">`.
- [ ] Icon-only action buttons include descriptive `aria-label` attributes.
- [ ] Keyboard navigation (Tab, Escape, Arrow keys) works across all dialogs, popovers, and menus.

### Quality & Performance
- [ ] `npm run type-check` passes with zero errors.
- [ ] `npm run build` succeeds cleanly.
- [ ] No runtime console accessibility warnings during modal or dropdown interactions.
- [ ] 100% of intentional product designs (Persian variable font, pill radii, bento crowdfunding layout, audio players) remain visually intact.

---

## Important Non-Goals

The following activities are **explicitly out of scope** for this refactoring effort:
- Re-styling components to match the generic shadcn-vue starter theme.
- Changing the approved `rounded-3xl` / `rounded-4xl` squircle radius design language.
- Modifying `src/components/ui/progress/Progress.vue` (upstream-compliant).
- Redesigning Kindness crowdfunding bento cards or media players.
- Upgrading major framework versions (Vue, Vite, Tailwind).
