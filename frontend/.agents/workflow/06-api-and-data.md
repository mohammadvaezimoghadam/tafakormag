# API Integration & Data Fetching Workflow

## 1. Data Fetching Architecture
* **Centralization:** All API endpoints must be organized as service modules or hooks within the corresponding feature folder (e.g., `src/features/auth/services/authApi.ts`) or a central `src/lib/api.ts` client.
* **TypeScript Synchronization:** All API requests and responses must be explicitly typed using interfaces defined in the local or global `types.ts` files. Never use `any` for API responses.

## 2. Interactive States & Component Composition
When hooking up API endpoints to the UI, you must follow the core component rules:
* **Loading States:** Buttons triggering API calls must never use an `isPending` or `isLoading` prop. You must compose the loading state by disabling the button and rendering a `Spinner` component with the `data-icon="inline-start"` attribute.
* **Skeleton Placeholders:** For initial page loading or data fetching, use the `Skeleton` component instead of custom `animate-pulse` divs or raw text placeholders.

## 3. Strict Error Handling & Validation
* **Global Notification:** Every caught API error must trigger a user-facing notification using `toast.error()` from `vue-sonner`. Never silently swallow catch blocks.
* **Form Validation Linkage:** API validation errors (e.g., 422 Unprocessable Entity) must map back to the UI. Apply `data-invalid` on the `Field` container and `aria-invalid` on the input control to properly style and announce the error state.

## 4. Environment Variables
* Always reference backend URLs using Vite's environment variable syntax (`import.meta.env.VITE_API_BASE_URL`). Never hardcode domain names or IPs anywhere in the source code.