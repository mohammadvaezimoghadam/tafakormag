# Project Memory & Architectural Source of Truth

## 1. Core Stack & Configuration
* **Framework:** Vue.js 3 (Composition API via `<script setup>`, TypeScript)
* **UI Architecture:** shadcn-vue
* **Styling:** Tailwind CSS (Strictly semantic classes, no manual `dark:` overrides)
* **State Management:** Pinia (Setup Stores only)
* **Routing:** Vue Router (Lazy-loaded views)
* **Form Validation:** `vee-validate` + `zod`
* **Notifications:** `vue-sonner`
* **Icons:** Configured library via project settings (e.g., `@lucide/vue`).

## 2. Environment Architecture (The 3-Tier Rule)
* **Env 1 (Main Platform):** `src/views/` and `src/features/`. Production business logic and routing.
* **Env 2 (Design Showcase):** `src/showcase/`. Strictly for shadcn base primitives, typography, and theme variables. No business logic.
* **Env 3 (Test Playground):** `src/playground/`. For testing composite components/cards, responsive behavior, and states (Loading, Error, Empty) using Mock Data.

## 3. Architectural Decision Records (ADRs)

### UI & Component Composition
* **Forms:** Exclusively use `FieldGroup` + `Field`. Never use raw `div`s with `space-y-*` for form layout.
* **Selection (2-7 items):** Always use `ToggleGroup` instead of mapping standard `Button` components.
* **Overlays:** `Dialog`, `Sheet`, and `Drawer` must always include their respective Title components (use `class="sr-only"` if visually hidden for accessibility).
* **Icons:** Use `data-icon="inline-start"` or `data-icon="inline-end"` for icons inside buttons. Never apply sizing classes (like `size-4` or `w-4 h-4`) directly to icons within shadcn components.
* **Spacing & Sizing:** Use `gap-*` (via `flex` or `grid`) instead of `space-y-*`/`space-x-*`. Use `size-*` when width and height are equal.

### State & API Management
* **Global vs. Local:** Pinia is strictly for global/shared state (auth, global settings). Form inputs and temporary UI states (toggles, pending animations) must use local `ref`/`reactive`.
* **API Handling:** Handled in feature-specific directories. Loading states must use `Spinner` (in buttons) or `Skeleton` (for layout). All API errors must trigger `toast.error()` via `vue-sonner`.
* **Immutability:** Never destructure Pinia state directly; always use `storeToRefs()`.

## 4. Agent Operational Rules
* **shadcn CLI:** Never fetch raw component files from GitHub manually. Always use the project's package runner (e.g., `npx shadcn-vue@latest add <component>`).
* **Verification First:** Always run `npx shadcn-vue@latest docs <component>` to verify props/slots before guessing structural code.
* **No z-index Hacks:** Never manually apply `z-index` to overlay components; they manage their own stacking context.

## 5. Ongoing Tasks & Project Nuances
* *(Agent Note: Proactively update this section when new complex workarounds are implemented, dependencies are added, or specific user preferences are established).*