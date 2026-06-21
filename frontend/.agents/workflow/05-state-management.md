# State Management Workflow (Pinia)

## 1. Architectural Principles
When managing application state, you must strictly separate local component state from global shared state. Avoid polluting the global store with temporary UI states.

## 2. Technical Standards
* **Pinia Setup Stores:** Always use the Setup Store syntax (`defineStore('id', () => { ... })`) instead of the Option Store syntax. This aligns perfectly with the Vue 3 Composition API `<script setup>` pattern.
* **Reactive Destructuring:** Never destructure state directly from a store as it breaks reactivity. Always use `storeToRefs(store)` for state properties, while actions can be destructured directly.
* **Naming Convention:** Store files must be named using camelCase with the `.ts` extension (e.g., `useAuthStore.ts`) and placed inside `src/stores/` or the corresponding feature directory (e.g., `src/features/auth/stores/`).

## 3. Local vs. Global State Guardrails
* **Form States:** Temporary form inputs, validation errors, and pending animations must remain local to the component or managed via form libraries (`vee-validate`/`zod`). Never store unsubmitted form data in a global Pinia store.
* **Global States:** Use Pinia exclusively for data that is shared across multiple independent features or pages, such as user authentication sessions, global theme settings, or cached master data.

## 4. State Mutations
* Always use explicit action functions to mutate state. Do not modify store state directly from components (e.g., use `store.updateProfile(data)` instead of `store.profile = data`).
* Group related state modifications inside a single action to minimize unexpected side-effects and maintain clean devtools tracking.