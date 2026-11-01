# Three-Tier Component Environments Workflow

## 1. Project Environments Structure
Our project operates simultaneously across three completely distinct environments. As an AI agent, you are required to strictly adhere to the rules of these three environments whenever generating, editing, or installing components:

### Environment 1: Main Platform (Main Development / Production)
* **Description:** The core application environment containing actual pages, routing (Vue Router), and business logic.
* **Execution Port:** `localhost:3000` (or the specific port defined in the Vite/Nuxt config file).
* **Development Rule:** Components must only be integrated into the pages of this environment *after* they have been fully tested and approved in Environments 2 and 3.

### Environment 2: Design System Showcase
* **Description:** A completely isolated environment used **exclusively** for displaying base UI primitives (installed from shadcn-vue), typography, theme color palettes (Dark/Light), and sizing scales.
* **File Path:** `src/showcase/` (or similar systems like Storybook/Histoire if installed).
* **Development Rule:** No complex business logic, API calls, or large composite components should ever be placed in this environment. It is strictly for base styles and default shadcn behaviors.

### Environment 3: Component Playground (Test Lab)
* **Description:** This environment is dedicated to testing and simulating larger, custom-built composite components and cards (e.g., Login Forms, Profile Cards, Data Tables).
* **File Path:** `src/playground/` (or a dedicated component testing directory).
* **Development Rule:** Mock data must be used here for simulation. All component states (Loading, Error, Success), animations, and responsive behaviors must be fully rendered and tested in this environment.

---

## 2. Mandatory Workflow

### A) When Installing a Base Component from shadcn-vue
Whenever requested to add a new primitive from `shadcn-vue` (e.g., Button or Input), you must execute the following steps **in order**:
1. Run the component installation command (via the shadcn CLI).
2. Create or update the corresponding file in **Environment 2 (Showcase)**.
3. Inside the Showcase file, render the new component with *all* its style variants (Sizes, Variants, Colors) to ensure it functions perfectly across both Dark and Light themes.

### B) When Building Composite & Large Components
Whenever you develop a business component or a complex card (e.g., `LoginForm.vue` or `UserProfileCard.vue`), you must follow these steps:
1. Develop the component and place it in its standard architectural path (e.g., `src/features/auth/components/`).
2. Create a test scenario file in **Environment 3 (Playground)**.
3. In the Playground, wrap the component in a resizable container to rigorously test its **Responsive Design** across mobile and desktop viewports.
4. Simulate and implement the following interactive states using Mock data:
   * Default / Idle State
   * Hover / Active State (including animations/transitions)
   * Loading State (Skeleton or Spinner)
   * Empty State (if applicable)
   * Error State (UI error handling)

---

## 3. Strict Rules
* **No Interference:** Never introduce environment variables or backend-specific logic from the Main Platform (Environment 1) into Environments 2 and 3.
* **Visual Isolation:** The testing environments must operate in complete isolation. An API failure in the main app must not break the component rendering in the Playground.
* **TypeScript Strictness:** Mock data used in the Playground (Environment 3) must strictly adhere to the exact same interfaces and types (`types.ts`) that the actual component expects in production.