# Routing & Page Architecture Workflow

## 1. Directory Structure & File Organization
* **Views vs. Components:** Code placed in `src/views/` (or `pages/`) must serve purely as page-level layout wrappers that tie together individual features. They must contain minimal business logic.
* **Feature Encapsulation:** Pages must import cohesive blocks from `src/features/`. For example, `src/views/LoginView.vue` should simply render `<LoginForm />` imported from `@/features/auth/components/LoginForm.vue`.

## 2. Vue Router Configuration
* **Lazy Loading:** All route components within the router configuration (`src/router/index.ts`) must use dynamic imports (`component: () => import('@/views/HomeView.vue')`) to optimize bundle sizes and code-splitting.
* **Route Layouts:** Use nested routes or dedicated layout components (`DefaultLayout.vue`, `AuthLayout.vue`) to keep page structures clean and avoid redundant navbar/sidebar rendering.

## 3. Route Meta & Navigation Guards
* **Access Control:** Protect private routes by defining custom `meta` properties, such as `meta: { requiresAuth: true }`.
* **Navigation Guards:** Implement `router.beforeEach` to guard routes. Sync access states directly with your global authentication store (`useAuthStore`) to prevent unauthorized view rendering.
* **Query Params & States:** Use route query parameters (`route.query`) to persist minor UI states (like active tabs or search filters) across page refreshes when appropriate.