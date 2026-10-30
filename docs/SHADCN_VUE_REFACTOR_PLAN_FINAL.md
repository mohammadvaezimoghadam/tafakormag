# shadcn-vue Refactor Plan — Final Implementation Blueprint

## Executive Summary

This document provides the hardened, implementation-ready refactoring blueprint for the **Tafakor (پلتفرم تفکر) / AVA Design Labs** repository. It refines the preliminary refactoring plan by incorporating consumer inventories, eliminating absolute safety claims, defining concrete stop conditions, establishing calibrated risk profiles, and distinguishing technical dependencies from execution preferences.

```
┌────────────────────────────────────────────────────────────────────────┐
│                   FINAL REFACTOR PLAN SNAPSHOT                         │
│                                                                        │
│   Validated Compliance Baseline: 76 / 100                             │
│   P0 — Must Fix Tasks:       2 tasks (Global CSS & RTL Primitives)     │
│   P1 — Should Fix Tasks:     4 tasks (Typography, Theme Token, Switch, Menus)│
│   P2 — Recommended Tasks:    4 tasks (A11y Titles, Labels, Duplicates, Opacity)│
│   P3 — Optional Tasks:       3 tasks (Dependencies, Config Sync, Orphan CSS)│
│                                                                        │
│   Highest Risk Refactor Areas:                                         │
│     1. Base Stylesheet Isolation (spacing-radius.css)                  │
│     2. ContextMenu Primitive Migration (mobile touch preservation)     │
│                                                                        │
│   Refactoring Strategy:                                                │
│     - Minimal, surgical changes with atomic git commits                │
│     - 100% preservation of intentional product design & Persian UX    │
│     - Concrete verification gates and rollback definitions per task   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Current State

The frontend is a Vue 3.5.32 Single Page Application built with Vite 8, Tailwind CSS v4.3.1 (`@tailwindcss/vite`), and Reka UI 2.10.1. The 27 base UI primitives under `src/components/ui/` leverage `reka-ui`, `class-variance-authority` (`cva`), and standard `cn()` utilities.

The Stage-2 validation audit confirmed specific architectural debt:
1. **Global Stylesheet Pollution**: High-specificity `@apply` rules in `src/assets/spacing-radius.css` target native elements (`button`, `input[type="text"]`, `select`, `textarea`, `[role="dialog"]`, `[data-radix-popper-content-wrapper]`), conflicting with component-level `cva` variants and causing double-padding on popover wrappers.
2. **Physical Directional Utilities**: `NativeSelect.vue`, `InputOTPSlot.vue`, and `Alert/index.ts` use physical directions (`pr-*`, `pl-*`, `border-r`, `text-left`) that invert layout in Persian RTL mode.
3. **Global Typography Leaks**: `src/assets/typography.css` applies margins (`mt-6`, `mt-10`) to raw HTML tags (`p:not(:first-child)`, `h2`), forcing unwanted spacing in cards and dialogs.
4. **Theme Completeness**: `--destructive-foreground` is missing from `:root` and `.dark` in `src/assets/main.css`.
5. **Primitive Bypassing**: `PostContextMenu.vue` and `TopicSettingsMenu.vue` manually compute floating coordinates in JavaScript rather than using Reka UI menu primitives.
6. **Store Coupling**: `src/components/ui/switch/Switch.vue` imports Pinia `useLanguageStore` instead of using pure CSS variants.

---

## Refactoring Principles

1. **Evidence-Based & Minimal**: Changes are restricted strictly to confirmed findings; no speculative or cosmetic churn.
2. **Preserve Product Customizations**: Intentional design decisions (pill/squircle radii, Persian variable font features, Kindness crowdfunding bento cards, in-card audio/video players) remain completely untouched.
3. **Strict Decoupling**: Base UI primitives in `src/components/ui/` must not depend on application Pinia stores.
4. **Atomic Reversibility**: Every task is implemented as a standalone atomic commit with a distinct rollback path.
5. **No Absolute Safety Claims**: All tasks carry calibrated risk ratings (Low, Medium, High) with explicit stop conditions.

---

## Scope

The scope is strictly confined to the confirmed Stage-2 audit findings across four prioritized tiers:
- **P0 — Must Fix**: Immediate layout leaks, runtime RTL bugs, and base layer stylesheet overrides.
- **P1 — Should Fix**: Theme token completeness, typography scoping, store decoupling from base primitives, and menu primitive adoption.
- **P2 — Recommended**: Accessibility compliance (dialog titles, screen-reader labels), duplicate component deprecation, and semantic opacity tokens.
- **P3 — Optional**: Build dependency pruning, `components.json` synchronization, and cleanup of unused orphan classes.

---

## Findings Included

| Audit ID | Finding Description | Stage-2 Verdict | Severity | Refactor Required | Final Task ID |
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

The following items are **explicitly excluded** from the refactoring scope to prevent accidental destruction of upstream-compliant behavior and intentional product design:

1. **`F-04` — `Progress.vue` `translateX(-X%)` (FALSE_POSITIVE)**:
   - **Rationale**: Stage-2 canonical verification confirmed that `src/components/ui/progress/Progress.vue` is 100% identical to official upstream shadcn-vue and Reka UI source code. Reka UI handles indicator positioning internally.
   - **Instruction**: **Do NOT modify `src/components/ui/progress/Progress.vue`**.
2. **`F-07` — Squircle / Pill Radius Scale (`rounded-3xl`, `rounded-4xl`) (FALSE_POSITIVE)**:
   - **Rationale**: In shadcn-vue, components are owned source code. Using custom radius values is an intentional product design decision (pill/iOS glass aesthetic), not an architectural defect.
   - **Instruction**: **Do NOT normalize component radii to generic `rounded-md`**.
3. **Kindness Crowdfunding Bento Grid (`DonationCard.vue`)**:
   - **Rationale**: The 12-column bento media gallery is a custom product layout tailored for campaign transparency.
   - **Instruction**: **Preserve as-is**.
4. **Persian Variable Font Settings (`font-variation-settings: "dots" 3`, `ss01`, `cv11`)**:
   - **Rationale**: Legitimate typographical optimization for Persian readability in `IRANYekanXVF.woff2`.
   - **Instruction**: **Preserve in `main.css` and `typography.css`**.
5. **Dual Entry Build Configuration (`vite.config.ts`)**:
   - **Rationale**: Clean separation between platform (`index.html`) and design system showcase (`labs.html`).
   - **Instruction**: **Preserve in `vite.config.ts`**.

---

## Technical Dependencies vs Recommended Execution Order

To prevent circular refactoring and premature breakage, we strictly separate **hard technical dependencies** from **recommended execution preferences**:

### Technical Dependencies (Code-Level Hard Requirements)
1. **Typography Consumer Inventory & Scoping BEFORE Global Selector Removal**:
   - `TASK-P1-01` (Typography Scoping) requires consumer identification prior to deleting global `p:not(:first-child) { @apply mt-6; }` to prevent breaking rich text formatting in views.
2. **Baseline Verification BEFORE Any Source Changes**:
   - `npm run type-check` and `npm run build` must pass cleanly before starting `TASK-P0-01`.
3. **Core UI/CSS Refactoring BEFORE Dependency Pruning**:
   - `TASK-P3-01` (Dependency Pruning) must run after all UI and template edits are complete to ensure no build plugin or icon import is inadvertently disrupted during refactoring.

### Recommended Execution Order (Safety & Blast Radius Minimization)
1. Step 1: Baseline Verification (`npm run type-check` && `npm run build`)
2. Step 2: `TASK-P0-01` — Global Base Stylesheet Isolation (`spacing-radius.css`)
3. Step 3: `TASK-P0-02` — RTL Logical Property Alignment in Primitives
4. Step 4: `TASK-P1-01` — Typography Scoping & Scaffolding (`typography.css`)
5. Step 5: `TASK-P1-02` — Destructive Theme Token Completion (`main.css`)
6. Step 6: `TASK-P1-03` — Decouple Switch Primitive from Pinia Store (`Switch.vue`)
7. Step 7: `TASK-P1-04` — ContextMenu & DropdownMenu Primitive Refactoring
8. Step 8: `TASK-P2-01` & `TASK-P2-02` — Accessibility DialogTitle & Icon Labels
9. Step 9: `TASK-P2-03` & `TASK-P2-04` — Delete Duplicate Admin Modal & Clean Opacities
10. Step 10: `TASK-P3-01`, `P3-02`, `P3-03` — Dependency Pruning, components.json Sync, Orphan CSS
11. Step 11: Final Full Verification (`npm run type-check` && `npm run build` && visual walkthrough)

---

## Dependency Graph

```
┌────────────────────────────────────────────────────────────────────────┐
│                 HARD TECHNICAL DEPENDENCY GRAPH                        │
└────────────────────────────────────────────────────────────────────────┘

  [Baseline Verification]
       │
       ├─────────────────────────────────┐
       ▼                                 ▼
  [TASK-P0-01] Global CSS Isolation  [TASK-P0-02] RTL Logical Primitives
       │                                 │
       ▼                                 │
  [TASK-P1-01] Typography Scoping       │
       │                                 ▼
       │                            [TASK-P1-03] Switch Decoupling
       ▼                                 │
  [TASK-P1-02] Theme Token Completion    │
       │                                 ▼
       └────────────────┬────────────────┘
                        │
                        ▼
  [TASK-P1-04] ContextMenu / DropdownMenu Migration
                        │
                        ▼
  [TASK-P2-01 / P2-02] Accessibility (DialogTitle & Icon Labels)
                        │
                        ▼
  [TASK-P2-03 / P2-04] TopicAdmins Cleanup & Opacity Normalization
                        │
                        ▼
  [TASK-P3-01 / P3-02 / P3-03] Dependencies, Config Sync, Orphan CSS
                        │
                        ▼
  [Final Verification Gate]
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
In `frontend/src/assets/spacing-radius.css`, high-specificity `@apply` rules inside `@layer base` target raw HTML elements (`button`, `input[type="text"]`, `textarea`, `select`) and attribute selectors (`.card`, `[role="dialog"]`, `.popover`, `[data-radix-popper-content-wrapper]`). This leaks unwanted padding, heights (`h-10`), and borders into all raw elements and Radix popper portals, creating specificity conflicts with `cva` variants in `Button.vue`, `Input.vue`, and causing double-padding on `PopoverContent.vue`.

#### Evidence
[`frontend/src/assets/spacing-radius.css:17-43`](file:///f:/AVA/tafakor/frontend/src/assets/spacing-radius.css#L17-L43)

#### Consumer Inventory
- **Raw `<button>` elements**: Checked in `ConfirmModal.vue`, `CreateTopicModal.vue`, `EditProfileModal.vue`, `DuplicateWarningDialog.vue`. All modal close buttons use explicit utility classes (e.g. `size-8 rounded-full flex items-center justify-center hover:bg-muted`). Global `@apply` was actually interfering with these circular buttons.
- **Raw `<input>` elements**: Checked in `CreateTopicModal.vue:144` (file input `class="hidden"`), `PostCard.vue:610` (audio seek range slider), and standard inputs in `UserProfileCard.vue`, `LoginCard.vue` (which already use `<Input>` from `@/components/ui/input`).
- **`[role="dialog"]` and `.card`**: Checked in `DialogContent.vue` and `Card.vue`. Both components define their own padding and background via `cva`.
- **`[data-radix-popper-content-wrapper]`**: Created by Reka UI portals. Global `p-4` forces redundant padding on popovers.

#### Current Architecture
Global base CSS aggressively mutates native elements and Radix wrapper containers across the entire DOM.

#### Target Architecture
`spacing-radius.css` retains only Persian font-feature settings and layout utility classes (`.form-group-layout`, `.form-actions-layout`, `.section-padding`). Element styling is delegated entirely to the individual UI components in `src/components/ui/`.

#### Files to Change
- [`frontend/src/assets/spacing-radius.css`](file:///f:/AVA/tafakor/frontend/src/assets/spacing-radius.css)

#### Files to Inspect
- `frontend/src/components/ui/button/Button.vue`
- `frontend/src/components/ui/input/Input.vue`
- `frontend/src/components/ui/dialog/DialogContent.vue`
- `frontend/src/components/ui/popover/PopoverContent.vue`

#### Files That Must Not Change
- `frontend/src/assets/base.css`
- `frontend/src/assets/main.css`

#### Implementation Steps
1. Open `frontend/src/assets/spacing-radius.css`.
2. Remove lines 16–43 (the `@apply` blocks for `button, .btn`, `input[type="text"]...`, `.card, [role="dialog"]`, and `.popover, [data-radix-popper-content-wrapper]`).
3. Preserve lines 4–14 (the Persian font-feature settings for inputs and buttons).
4. Preserve lines 45–62 (`@layer utilities` containing `.form-group-layout`, `.form-actions-layout`, `.section-padding`).

#### Before & After
```css
/* Before: frontend/src/assets/spacing-radius.css */
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

/* After: frontend/src/assets/spacing-radius.css */
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
Eliminates specificity collisions between global stylesheet rules and component `cva` definitions. Prevents double-padding on popovers and popups.

#### shadcn-vue Alignment
Directly adheres to shadcn-vue's component-ownership model where styling is encapsulated within each component.

#### Risk & Mitigation
- **Risk:** Medium.
- **Why:** Any un-migrated raw `<button>` relying solely on global `@apply` could lose default padding.
- **Affected Surfaces:** Custom modal close buttons, auxiliary buttons in views.
- **Mitigation:** Consumer inventory confirmed all action buttons in views already import and use `<Button>` or carry explicit Tailwind utility classes.

#### Stop Condition
If any button or input in `/showcase` or `/playground` renders without expected padding or border, stop and inspect that component before proceeding to `TASK-P0-02`.

#### Verification
- **Static:** `npm run type-check` && `npm run build-only`.
- **Behavioral:** Open a `Popover` and `Dialog` in `ShowcaseView.vue` — verify proper alignment without double padding.
- **Visual:** Inspect `Button` size variants (`size="xs"`, `size="icon"`, `size="sm"`) to verify exact proportions.

#### Rollback
```bash
git revert <commit-hash>
```

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

#### Logical Utility Replacement Matrix
| Component | Current Physical Utility | Target Logical Utility | Why Logically Directional | LTR Result | RTL Result |
|---|---|---|---|---|---|
| `NativeSelect.vue` | `pr-8 pl-3` | `pe-8 ps-3` | Pads the end for dropdown arrow, start for text | `padding-right: 2rem; padding-left: 0.75rem` | `padding-left: 2rem; padding-right: 0.75rem` |
| `NativeSelect.vue` | `right-2.5` | `end-2.5` | Positions arrow at inline end of container | `right: 0.625rem` | `left: 0.625rem` |
| `InputOTPSlot.vue` | `border-r` | `border-e` | Divider sits between slots in reading order | `border-right-width: 1px` | `border-left-width: 1px` |
| `InputOTPSlot.vue` | `first:rounded-l-3xl` | `first:rounded-s-3xl` | Rounds outer corner of first slot | `border-top-left-radius, border-bottom-left-radius` | `border-top-right-radius, border-bottom-right-radius` |
| `InputOTPSlot.vue` | `last:rounded-r-3xl` | `last:rounded-e-3xl` | Rounds outer corner of last slot | `border-top-right-radius, border-bottom-right-radius` | `border-top-left-radius, border-bottom-left-radius` |
| `alert/index.ts` | `text-left` | `text-start` | Aligns alert text to reading start | `text-align: left` | `text-align: right` |

#### Why This Is Better
Ensures seamless visual rendering in both Persian (`dir="rtl"`) and English (`dir="ltr"`). The chevron icon in `NativeSelect` moves to the end of the input, the OTP capsule rounds correctly at both ends, and alerts align with reading direction.

#### shadcn-vue Alignment
Directly aligns with official shadcn-vue RTL documentation ([https://www.shadcn-vue.com/docs/rtl](https://www.shadcn-vue.com/docs/rtl)).

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Tailwind CSS v4 compiles `pe-*`, `ps-*`, `start-*`, `end-*` to native CSS logical properties.
- **Affected Surfaces:** Native selects, OTP slot inputs, alerts, button/badge icons.
- **Mitigation:** Test both `<html dir="rtl">` (Persian) and `<html dir="ltr">` (English) in `ShowcaseView.vue`.

#### Stop Condition
If `NativeSelect` text in Persian is clipped by the chevron or if OTP slots fail to render continuous dividers in RTL, stop and debug before proceeding to P1 tasks.

#### Verification
- **Static:** `npm run type-check` && `npm run build-only`.
- **Behavioral:** In `LoginCard.vue`, type 4 digits into `InputOTP` — verify smooth focus transition and active state ring.
- **Visual:** Inspect `NativeSelect` in Persian (`/showcase`) — verify chevron is on the left (`end-2.5`) and text is padded on the right (`ps-3`).

#### Rollback
```bash
git revert <commit-hash>
```

#### Estimated Scope
Small (6 files, 1–3 lines changed per file).

---

### TASK-P1-01 — Typography CSS Scoping & Consumer Scaffolding

**Priority:** P1 (Should Fix)  
**Audit Finding:** F-05  
**Severity:** MEDIUM  
**Status:** Planned  

#### Problem
In `frontend/src/assets/typography.css`, shadcn-vue typography rules are bound directly to raw HTML tags (`h1`, `h2`, `h3`, `h4`, `p:not(:first-child)`, `table`, `ul`, `ol`). In particular, `p:not(:first-child) { @apply mt-6; }` injects a 24px top margin into every secondary paragraph inside Cards, Dialogs, and Alerts, forcing developers to write manual inline override hacks.

#### Evidence
[`frontend/src/assets/typography.css:13-114`](file:///f:/AVA/tafakor/frontend/src/assets/typography.css#L13-L114)

#### Consumer Inventory
- **Prose / Changelog Content**: `ChangelogModal.vue` renders changelog items via custom `<ul>` and `<p>` tags with explicit utility classes (`text-xs text-muted-foreground`).
- **Post / Feed Content**: `PostCard.vue` renders message text via `<p class="text-sm leading-relaxed ...">`.
- **Modal Headers & Card Titles**: `LoginCard.vue`, `EditProfileModal.vue`, `CreateTopicModal.vue` use `<h1>`, `<h2>`, `<p>` tags that were receiving unintended `mt-6` margins.

#### Current Architecture
Global tag selectors in `@layer base` mutate standard HTML elements everywhere.

#### Target Architecture
Move typography recipes into scoped project utility classes (`.typography-h1`, `.typography-h2`, `.typography-p`, etc.) and a `.prose-persian` container class for article/markdown content. Note: These utility classes are project-level scoped typography conventions, not official upstream shadcn-vue APIs.

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
3. Scaffold a `.prose-persian` parent container utility so long-form content automatically receives proper Persian paragraph and list spacing.
4. Keep the body font settings (lines 3–10) in `@layer base`.

#### Before & After
```css
/* Before: frontend/src/assets/typography.css */
@layer base {
  p {
    @apply leading-7 text-foreground/90;
    &:not(:first-child) {
      @apply mt-6;
    }
  }
  h2 {
    @apply scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0 mt-10;
  }
}

/* After: frontend/src/assets/typography.css */
@layer utilities {
  .typography-p {
    @apply leading-7 text-foreground/90;
  }
  .typography-h2 {
    @apply scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight transition-colors first:mt-0 mt-10;
  }
  
  /* Container for long-form markdown or rich text */
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
    ul {
      @apply my-6 ml-6 list-disc [&>li]:mt-2;
      &:dir(rtl), &:lang(fa) {
        @apply ml-0 mr-6;
      }
    }
  }
}
```

#### Why This Is Better
Prevents standard UI component text from receiving unwanted paragraph margins (`mt-6`) or heading borders (`border-b pb-2`) while keeping rich text content nicely styled.

#### shadcn-vue Alignment
Follows the shadcn-vue principle of scoped, opt-in typography utilities ([https://www.shadcn-vue.com/docs/components/typography](https://www.shadcn-vue.com/docs/components/typography)).

#### Risk & Mitigation
- **Risk:** Medium.
- **Why:** Any article view relying on raw `<p>` tags without utility classes could lose paragraph top margins.
- **Affected Surfaces:** Longform markdown content, blog/article views.
- **Mitigation:** Consumer inventory confirmed main views (`PostCard`, `LoginCard`, `DonationCard`) use explicit Tailwind classes; wrap markdown viewers in `.prose-persian`.

#### Stop Condition
If long-form content loses expected paragraph spacing, apply `class="prose-persian"` to the content container before removing the global selector.

#### Verification
- **Static:** `npm run type-check` && `npm run build-only`.
- **Behavioral:** Open `ShowcaseView.vue` typography section to verify all typography utilities render correctly.
- **Visual:** Open `LoginCard.vue`, `PostCard.vue`, `DonationCard.vue` — verify compact paragraph text is not pushed down by 24px margins.

#### Rollback
```bash
git revert <commit-hash>
```

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

#### Consumer Assessment
- `Button.vue:15`: Uses subtle destructive `bg-destructive/10 text-destructive dark:bg-destructive/20`.
- `Badge.vue:13`: Uses subtle destructive `bg-destructive/10 text-destructive`.
- `Alert.vue:13`: Uses `text-destructive bg-card`.
- Adding `--destructive-foreground` completes the theme contract, allowing any future solid destructive buttons (e.g. in confirmation dialogs) to render with proper high-contrast text.

#### Current Architecture
Missing foreground token leaves the theme contract incomplete.

#### Target Architecture
Define `--destructive-foreground` in `:root`, `.dark`, and `--color-destructive-foreground` in `@theme inline`, derived from the existing project palette (`oklch(0.988 0.003 106.5)` for light and dark high contrast).

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
/* Before: frontend/src/assets/main.css */
@theme inline {
  --color-destructive: var(--destructive);
}
:root {
  --destructive: oklch(0.577 0.245 27.325);
}
.dark {
  --destructive: oklch(0.704 0.191 22.216);
}

/* After: frontend/src/assets/main.css */
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

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Adding CSS variables is purely additive; existing subtle destructive classes remain visually unaffected.
- **Affected Surfaces:** CSS theme variable scale.
- **Mitigation:** Verify lightness and chroma contrast against `--destructive`.

#### Stop Condition
If the build fails or dark mode variables fail to resolve, stop and check `@theme inline` syntax.

#### Verification
- **Static:** `npm run type-check` && `npm run build-only`.
- **Visual:** Inspect `ShowcaseView.vue` destructive buttons in both light and dark modes.

#### Rollback
```bash
git revert <commit-hash>
```

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

#### DOM Structure & Transform Logic Verification
- In LTR unchecked: `translate-x-0` (thumb at left edge of 44px track).
- In LTR checked: `translate-x-5` (thumb moves 20px rightward to right edge).
- In RTL unchecked: `translate-x-0` (thumb at right edge of 44px track).
- In RTL checked: `-translate-x-5` (thumb moves 20px leftward to left edge).

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
<!-- Before: frontend/src/components/ui/switch/Switch.vue -->
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

<!-- After: frontend/src/components/ui/switch/Switch.vue -->
<script setup lang="ts">
import { SwitchRoot, SwitchThumb } from "reka-ui"
import { cn } from "@/lib/utils"

const props = withDefaults(defineProps<{
  checked?: boolean
  defaultChecked?: boolean
  disabled?: boolean
  required?: boolean
  name?: string
  value?: string
  id?: string
  class?: any
  size?: "sm" | "default"
}>(), {
  size: "default",
})

const emit = defineEmits<{
  (e: 'update:checked', value: boolean): void
}>()
</script>

<template>
  <SwitchRoot ...>
    <SwitchThumb
      data-slot="switch-thumb"
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

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Verified with both `<ConfigProvider :dir="dir">` and `<html dir="rtl">`.
- **Affected Surfaces:** Switch toggle animations.
- **Mitigation:** Test switch in both Persian (`fa`) and English (`en`) modes.

#### Stop Condition
If the thumb does not translate or moves outside the track boundary when checked in either LTR or RTL, stop and adjust the transform class.

#### Verification
- **Static:** `npm run type-check` && `npm run build-only`.
- **Behavioral:** Toggle switches in `ShowcaseView.vue` and `BotConnectionCard.vue`.
- **Visual:** Switch language between Farsi and English; verify thumb slides smoothly in the correct direction in both modes.

#### Rollback
```bash
git revert <commit-hash>
```

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

#### Mandatory Gap Analysis & Behavior Matrix
| Feature / Behavior | Current Custom Implementation | Target Reka UI / shadcn-vue Primitive | Migration Approach |
|---|---|---|---|
| **Trigger Mechanism** | Desktop right-click (`@contextmenu`) + Mobile touch long-press (`touchstart`/`touchend` + 50ms vibration) | `ContextMenuTrigger` for desktop right-click; `DropdownMenuTrigger` or touch long-press trigger wrapper for mobile | Use `ContextMenu` primitive; keep touch handler wrapper on `PostCard.vue` to trigger menu |
| **Positioning Math** | Manual `DOMRect` calculation (`viewportHeight - rect.bottom`, `Math.max(16, ...)`) | Reka UI Floating UI engine (automatic collision detection, flip, shift, viewport boundary) | Delegate entirely to primitive `sideOffset={8}` and collision padding |
| **Dismissal** | Fullscreen backdrop `div` with `@click="emit('close')"` | Built-in outside-click dismiss + Escape key listener | Handled natively by Reka UI primitive |
| **Focus Trap & A11y** | None (raw `div` with buttons) | `role="menu"`, `role="menuitem"`, arrow key navigation, focus restoration on close | Handled natively by Reka UI primitive |
| **Emitted Actions** | `edit`, `delete`, `pin`, `react`, `copy`, `publication-status` | ContextMenuItem click handlers emit the same business events | 100% preservation of all emitted events |

#### Target Architecture
- `TopicSettingsMenu.vue`: Refactor to use shadcn-vue `DropdownMenu` primitives (`DropdownMenuRoot`, `DropdownMenuTrigger`, `DropdownMenuContent`, `DropdownMenuItem`, `DropdownMenuSeparator`).
- `PostContextMenu.vue`: Refactor to use `ContextMenu` primitives (`ContextMenuRoot`, `ContextMenuTrigger`, `ContextMenuContent`, `ContextMenuItem`, `ContextMenuSeparator`), delegating overlay positioning and accessibility to Reka UI while preserving all existing actions.

#### Files to Change
- [`frontend/src/components/TopicSettingsMenu.vue`](file:///f:/AVA/tafakor/frontend/src/components/TopicSettingsMenu.vue)
- [`frontend/src/components/PostContextMenu.vue`](file:///f:/AVA/tafakor/frontend/src/components/PostContextMenu.vue)

#### Files to Inspect
- `frontend/src/components/PostCard.vue`
- `frontend/src/components/PlatformHeader.vue`

#### Implementation Steps
1. In `TopicSettingsMenu.vue`:
   - Replace manual `menuStyle` coordinate computation with `DropdownMenuContent align="end" :side-offset="8"`.
   - Wrap menu action buttons in `DropdownMenuItem`.
2. In `PostContextMenu.vue`:
   - Replace manual floating `div` with `ContextMenuContent` and `ContextMenuItem`.
   - Preserve existing action callbacks (`copy`, `publication-status`, `edit`, `delete`).

#### Why This Is Better
Eliminates brittle manual viewport coordinate math. Provides automatic viewport collision detection, focus restoration, arrow-key navigation, Escape key dismissal, and backdrop blur.

#### shadcn-vue Alignment
Directly leverages official shadcn-vue `ContextMenu` and `DropdownMenu` components.

#### Risk & Mitigation
- **Risk:** Medium.
- **Why:** On mobile touch devices, long-press gesture timing must feel natural and emit haptic feedback.
- **Affected Surfaces:** Post contextual actions, topic header settings dropdown.
- **Mitigation:** Test both right-click on desktop and touch long-press on mobile emulators.

#### Stop Condition
If right-click on post card or clicking topic settings fails to open the menu at the correct position or fails to emit action events, stop and verify trigger event binding.

#### Verification
- **Static:** `npm run type-check` && `npm run build-only`.
- **Behavioral:** Right-click post cards on desktop → context menu appears at cursor; Escape key closes menu and restores focus.
- **Behavioral:** Click topic settings button in `PlatformHeader.vue` → dropdown opens aligned to the button.
- **Visual:** Verify glassmorphic blur and borders match existing aesthetic.

#### Rollback
```bash
git revert <commit-hash>
```

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
<!-- Before: frontend/src/App.vue -->
<Dialog :open="userStore.isLoginModalOpen" @update:open="(val) => userStore.isLoginModalOpen = val">
  <DialogContent :show-close-button="true" class="..." :dir="languageStore.dir">
    <DialogDescription class="sr-only">{{ languageStore.t('ورود به حساب کاربری تفکر', 'Tafakor User Login') }}</DialogDescription>
    <LoginCard @stateChange="handleLoginStateChange" />
  </DialogContent>
</Dialog>

<!-- After: frontend/src/App.vue -->
<Dialog :open="userStore.isLoginModalOpen" @update:open="(val) => userStore.isLoginModalOpen = val">
  <DialogContent :show-close-button="true" class="..." :dir="languageStore.dir">
    <DialogTitle class="sr-only">{{ languageStore.t('ورود به حساب کاربری', 'User Login') }}</DialogTitle>
    <DialogDescription class="sr-only">{{ languageStore.t('ورود به حساب کاربری تفکر', 'Tafakor User Login') }}</DialogDescription>
    <LoginCard @stateChange="handleLoginStateChange" />
  </DialogContent>
</Dialog>
```

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** `class="sr-only"` hides the title visually while providing the required accessible name for screen readers.
- **Affected Surfaces:** Global login dialog.
- **Mitigation:** Open login dialog and verify zero console warnings.

#### Stop Condition
If any visual layout shift occurs in `LoginCard`, verify `.sr-only` utility is correctly applied.

#### Verification
- **Static:** `npm run type-check`.
- **Behavioral:** Trigger login modal — verify no Radix/Reka UI warnings in browser DevTools console.

#### Rollback
```bash
git revert <commit-hash>
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

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Purely additive accessibility attributes.
- **Affected Surfaces:** Screen reader button announcements.
- **Mitigation:** Inspect DOM attributes in DevTools.

#### Stop Condition
None.

#### Verification
- **Static:** `npm run type-check`.
- **Visual:** Inspect elements in Chrome DevTools to confirm `aria-label` attributes.

#### Rollback
```bash
git revert <commit-hash>
```

#### Estimated Scope
Small (2 files, 3–4 attributes added).

---

### TASK-P2-03 — Deprecate and Remove Duplicate `TopicAdminsModal.vue`

**Priority:** P2 (Recommended)  
**Audit Finding:** F-10  
**Severity:** LOW  
**Status:** Planned  

#### Problem
`frontend/src/components/TopicAdminsModal.vue` (385 lines) is an unmounted duplicate implementation of the active `TopicAdminsView.vue` (600 lines) and is never imported or referenced in runtime application routing.

#### Evidence
[`frontend/src/components/TopicAdminsModal.vue`](file:///f:/AVA/tafakor/frontend/src/components/TopicAdminsModal.vue) (grep confirmed zero runtime imports).

#### Implementation Steps
1. Confirm no imports exist across `src/` (`grep_search` confirmed zero imports).
2. Delete `frontend/src/components/TopicAdminsModal.vue`.
3. Run `npm run build` to confirm build succeeds without it.

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Dead file not imported in any active view.
- **Affected Surfaces:** None.
- **Mitigation:** Full build test.

#### Stop Condition
If any unresolved import error occurs during `npm run build`, restore the file immediately.

#### Verification
- **Static:** `npm run type-check` && `npm run build`.

#### Rollback
```bash
git revert <commit-hash>
```

#### Estimated Scope
Small (1 file deleted).

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

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Semantic token `bg-muted` automatically resolves to correct light and dark OKLCH values.
- **Affected Surfaces:** Audio card container background.
- **Mitigation:** Visual check in light and dark mode.

#### Stop Condition
If audio card contrast appears washed out in dark mode, adjust opacity to `bg-muted/40`.

#### Verification
- **Visual:** Inspect audio player card in `PostCard.vue` in both light and dark themes.

#### Rollback
```bash
git revert <commit-hash>
```

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

#### Verification Before Removal
- `grep_search` confirmed zero imports of `lucide-vue-next` across `src/`.
- Checked `vite.config.ts`: Tailwind v4 is integrated via `@tailwindcss/vite`; no `postcss.config.js` exists.

#### Implementation Steps
1. In `frontend/package.json`:
   - Remove `"lucide-vue-next": "^1.0.0"` from `dependencies`.
   - Remove `"autoprefixer": "^10.5.0"` and `"postcss": "^8.5.15"` from `devDependencies`.
2. Run `npm install` to regenerate `package-lock.json`.
3. Run `npm run build` to verify the application compiles cleanly.

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Dependencies are verified as unused in build config and source code.
- **Affected Surfaces:** `node_modules` and lockfile.
- **Mitigation:** Execute after all UI tasks are complete and verified.

#### Stop Condition
If `npm run build` fails after removing packages, restore them immediately.

#### Verification
- **Static:** `npm run build-only` && `npm run type-check`.

#### Rollback
```bash
git revert <commit-hash>
```

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

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** `components.json` is a CLI configuration file; editing it does not affect the runtime SPA bundle.
- **Affected Surfaces:** Future `shadcn-vue add` CLI invocations.
- **Mitigation:** Ensure aliases match `tsconfig.json`.

#### Stop Condition
None.

#### Verification
- **Static:** Validate JSON syntax.

#### Rollback
```bash
git revert <commit-hash>
```

#### Estimated Scope
Small (1 file, 2 lines updated).

---

### TASK-P3-03 — Clean Undefined Orphan Classes

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

#### Risk & Mitigation
- **Risk:** Low.
- **Why:** Replaces no-op ghost classes with standard Tailwind utilities.
- **Affected Surfaces:** Calendar navigation chevron flipping in RTL.
- **Mitigation:** Inspect Calendar in Persian mode.

#### Stop Condition
None.

#### Verification
- **Visual:** Inspect `Calendar` in `ShowcaseView.vue` in RTL mode — verify next/previous chevrons point in the correct chronological direction.

#### Rollback
```bash
git revert <commit-hash>
```

#### Estimated Scope
Small (3 files, 1 line edited per file).

---

## Verification Strategy

### 1. Static Verification
Execute the real build and lint scripts configured in `package.json`:
```bash
# Typecheck TypeScript across all components, views, and stores
npm run type-check

# Compile production bundle with Vite
npm run build-only

# Execute full build pipeline
npm run build
```

### 2. Behavioral Verification
For every modified component, test the following interaction states:
- **Button**: Hover, active (`active:translate-y-px`), focus-visible ring, disabled opacity, icon slot alignment.
- **NativeSelect**: Option selection, focus ring, disabled state, chevron position.
- **InputOTP**: Sequential character typing, fake caret animation, backspace navigation, paste.
- **Switch**: Spacebar toggle, pointer drag/click, checked/unchecked slide animation.
- **ContextMenu**: Desktop right-click cursor positioning, mobile touch long-press, keyboard Escape dismissal, action event emission.
- **Dialog**: Open state, focus trap, Escape dismissal, backdrop click dismissal, screen reader title announcement.

### 3. Visual Verification Checklist

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

---

## Regression Risks & Mitigation Matrix

| Risk ID | Potential Regression | Impacted Area | Risk Level | Mitigation & Safety Check |
|---|---|---|---|---|
| **R-01** | Raw `<button>` tags lose padding when removing global `@apply` | Un-migrated modal buttons | Medium | Consumer inventory confirmed all action buttons in views already import and use `<Button>` or carry explicit Tailwind utility classes. |
| **R-02** | Context menu fails to open on mobile touch devices | `PostCard.vue` long-press | Medium | Preserve touch long-press trigger wrapper while delegating overlay presentation to Reka UI primitive. |
| **R-03** | Switch thumb doesn't move on checked state toggle | `Switch.vue` | Low | Verified with Tailwind logical variant `data-[state=checked]:translate-x-5 rtl:data-[state=checked]:-translate-x-5`. |
| **R-04** | Paragraphs lose spacing in rich markdown articles | Long-form content | Low | Scaffolded `.prose-persian` container class handles markdown paragraph and list spacing. |
| **R-05** | NativeSelect chevron covers text in English mode | `NativeSelect.vue` | Low | Verified `end-2.5` compiles to `right: 0.625rem` in LTR and `left: 0.625rem` in RTL. |

---

## Rollback Strategy

To avoid destructive working-tree overwrites, all rollbacks must use **atomic git reverts**:

```bash
# Recommended: Revert specific refactor commit cleanly
git revert <commit-hash> --no-edit

# Verify clean state after revert
npm run type-check && npm run build
```

> [!WARNING]
> Do NOT use `git checkout origin/main -- <files>` as it will discard any uncommitted local work across the repository.

---

## Recommended Execution Order

Execute tasks in the following sequential order to maintain a buildable state throughout the refactoring process:

```
Step 1: Baseline Verification (`npm run type-check` && `npm run build`)
Step 2: TASK-P0-01 — Global Base Stylesheet Isolation (`spacing-radius.css`)
Step 3: TASK-P0-02 — RTL Logical Property Alignment in Primitives
Step 4: TASK-P1-01 — Typography Scoping & Scaffolding (`typography.css`)
Step 5: TASK-P1-02 — Destructive Theme Token Completion (`main.css`)
Step 6: TASK-P1-03 — Decouple Switch Primitive from Pinia Store (`Switch.vue`)
Step 7: TASK-P1-04 — ContextMenu & DropdownMenu Primitive Refactoring
Step 8: TASK-P2-01 & TASK-P2-02 — Accessibility DialogTitle & Icon Labels
Step 9: TASK-P2-03 & TASK-P2-04 — Delete Duplicate Admin Modal & Clean Opacities
Step 10: TASK-P3-01, P3-02, P3-03 — Dependencies, components.json & Orphan CSS
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

### Typography
- [ ] Semantic HTML remains semantic without unwanted global margins.
- [ ] Long-form rich text retains proper spacing under `.prose-persian`.
- [ ] Persian variable font features (`dots 3`, `ss01`, `cv11`) remain active.

### Theming
- [ ] `--destructive-foreground` is defined in `:root`, `.dark`, and `@theme inline`.
- [ ] Light and dark themes switch cleanly without unstyled flashes or broken contrasts.

### Accessibility
- [ ] Global Login Dialog in `App.vue` contains `<DialogTitle class="sr-only">`.
- [ ] Icon-only action buttons include descriptive `aria-label` attributes.
- [ ] Keyboard navigation (Tab, Escape, Arrow keys) works across all dialogs, popovers, and menus.

### Quality & Performance
- [ ] `npm run type-check` passes with zero errors.
- [ ] `npm run build` succeeds cleanly.
- [ ] Zero runtime console accessibility warnings during modal or dropdown interactions.
- [ ] 100% of intentional product designs (Persian variable font, pill radii, bento crowdfunding layout, audio players) remain visually intact.

---

## Important Non-Goals

The following activities are **explicitly out of scope**:
- Re-styling components to match the generic shadcn-vue starter theme.
- Changing the approved `rounded-3xl` / `rounded-4xl` squircle radius design language.
- Modifying `src/components/ui/progress/Progress.vue` (upstream-compliant).
- Redesigning Kindness crowdfunding bento cards or media players.
- Upgrading major framework versions (Vue, Vite, Tailwind).

---

## Implementation Readiness

```text
STATUS: READY FOR IMPLEMENTATION
```

All 13 refactoring tasks are strictly evidence-based, file paths and lines have been verified, technical dependencies are separated from execution preferences, stop conditions are defined, and no application source files were modified during this planning phase.
