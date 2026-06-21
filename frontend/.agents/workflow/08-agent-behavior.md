# Agent Behavior, Git, & Execution Protocols

## 1. Code Discovery Protocol
Before creating or editing any code, you must explore existing foundations to maintain consistency:
* **Project Context Inspection:** Always verify project environment fields like `packageManager`, `tailwindVersion`, and `iconLibrary` by ensuring you check the project configuration.
* **Registry Lookup:** Before building a custom UI element, search the available component registries using `npx shadcn-vue@latest search` to see if a primitive or block already exists.
* **API Verification:** Run `npx shadcn-vue@latest docs <component>` and fetch the URLs to verify the exact allowed props and slots before guessing structural code.

## 2. Iterative Development & Verification
* **Atomic Tasks:** Break down complex feature requests into smaller, testable steps. Do not rewrite five files at once.
* **The Three-Tier Rule:** Verify component primitives in Environment 2 (Showcase), composite blocks in Environment 3 (Playground) with rich mock data, and full workflows in Environment 1 (Main Platform).
* **Code Review Check:** After adding any block, read the generated file to ensure it complies with the styling constraints (e.g., using `size-*` instead of `w-* h-*` when equal, and avoiding `space-y-*` layout hacks).

## 3. Git & Commit Protocols
If authorized to commit changes, follow the Conventional Commits specification:
* **Format:** `<type>(<scope>): <short summary>`
* **Types:**
  * `feat:` A new user-facing feature.
  * `fix:` A bug fix.
  * `docs:` Documentation modifications only.
  * `style:` Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons).
  * `refactor:` A code change that neither fixes a bug nor adds a feature.

## 4. Stop-and-Ask Protocol
* **Ambiguity:** If a user prompt leaves styling requirements, color palettes, or data relationships ambiguous, **do not assume or hallucinate values**. Stop execution, present the trade-offs, and ask for clear direction.