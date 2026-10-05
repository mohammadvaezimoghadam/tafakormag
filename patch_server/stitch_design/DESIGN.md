---
name: Persian OTA Control Plane
colors:
  surface: '#faf8ff'
  surface-dim: '#d2d9f4'
  surface-bright: '#faf8ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f2f3ff'
  surface-container: '#eaedff'
  surface-container-high: '#e2e7ff'
  surface-container-highest: '#dae2fd'
  on-surface: '#131b2e'
  on-surface-variant: '#464555'
  inverse-surface: '#283044'
  inverse-on-surface: '#eef0ff'
  outline: '#777587'
  outline-variant: '#c7c4d8'
  surface-tint: '#4d44e3'
  primary: '#3525cd'
  on-primary: '#ffffff'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#c3c0ff'
  secondary: '#545f73'
  on-secondary: '#ffffff'
  secondary-container: '#d5e0f8'
  on-secondary-container: '#586377'
  tertiary: '#950029'
  on-tertiary: '#ffffff'
  tertiary-container: '#c20038'
  on-tertiary-container: '#ffd0d2'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#d8e3fb'
  secondary-fixed-dim: '#bcc7de'
  on-secondary-fixed: '#111c2d'
  on-secondary-fixed-variant: '#3c475a'
  tertiary-fixed: '#ffdada'
  tertiary-fixed-dim: '#ffb3b6'
  on-tertiary-fixed: '#40000c'
  on-tertiary-fixed-variant: '#920028'
  background: '#faf8ff'
  on-background: '#131b2e'
  surface-variant: '#dae2fd'
typography:
  headline-xl:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '800'
    lineHeight: 40px
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '700'
    lineHeight: 28px
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 26px
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 22px
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 20px
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '600'
    lineHeight: 18px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 16px
  label-sm:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '500'
    lineHeight: 14px
  code-md:
    fontFamily: JetBrains Mono
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 18px
  headline-xl-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '800'
    lineHeight: 34px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 19px
    fontWeight: '700'
    lineHeight: 28px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-lg: 1.5rem
  margin: 1.5rem
  margin-mobile: 1rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style
This design system embodies an austere, high-trust, engineering-first operations console engineered strictly for Persian (Farsi) RTL production environments. Designed for mobile devops engineers, release managers, and platform leads orchestrating live Flutter code-push rollouts, the UI prioritizes clarity, deliberate decision-making, and total operational safety.

The aesthetic fuses **Modern Enterprise Functionalism** with **Surgical Density**:
- **Tone:** Authoritative, measured, resilient, and precise.
- **RTL-First Structure:** Natural eye-scanning from right-to-left, with logical data anchoring, explicit numerical columns, and structural discipline tailored specifically to Perso-Arabic typographic rhythm.
- **Text-First Hierarchy:** Visual noise is stripped away. Iconography is reserved exclusively for system-critical states and direct directional indicators; typography, tabular structures, and precise opacity scales bear the full weight of spatial and categorical meaning.
- **Operational Calm:** Critical actions (such as emergency code-push rollbacks and targeted app freezes) are visually segregated from standard incremental deployments through deliberate spatial contrast and disciplined alert channels.

## Colors
The palette is hyper-restricted, deriving all UI nuances from an explicit opacity ladder across three functional anchors: **Indigo (`#4F46E5`)** for focus, active state, and progressive action; **Slate (`#1E293B`)** for dominant layout structure, text weight, and neutral surfaces; and **Emergency Crimson (`#E11D48`)** solely for destructive actions, kill-switches, and release rollbacks.

### Opacity Ladder (Base Tints & Fills)
- **Base Canvas:** `#F8FAFC`
- **Surface Layer 1 (Cards, Modals):** `#FFFFFF`
- **Surface Layer 2 (Muted Blocks, Table Headers):** `#1E293B` at 3% (`rgba(30, 41, 59, 0.03)`)
- **Interactive Hover Fill:** `#4F46E5` at 5% (`rgba(79, 70, 229, 0.05)`)
- **Subtle Badges / Pills:** Target tint at 10% opacity with 100% foreground text (e.g., Active Release: `rgba(79, 70, 229, 0.10)` fill, `#4F46E5` text).
- **Hairline Dividers & Borders:** `#1E293B` at 12% (`rgba(30, 41, 59, 0.12)`)
- **Active Focus Rings / Borders:** Target tint at 40%–50% (`rgba(79, 70, 229, 0.50)`).
- **Secondary / Supporting Text:** `#1E293B` at 60% (`rgba(30, 41, 59, 0.60)`).
- **Primary Text:** `#1E293B` at 100% (`#1E293B`).

### Emergency & State Signals
- **Rollback / Kill-Switch Inactive:** Crimson border at 30% (`rgba(225, 29, 72, 0.30)`), text at 100% (`#E11D48`), background at 4% (`rgba(225, 29, 72, 0.04)`).
- **Rollback / Kill-Switch Engaged:** Background solid `#E11D48`, text `#FFFFFF`.
- **Neutral State / Stale Release:** `#1E293B` at 8% fill, text at 60%.

## Typography
Typographic pairing bridges RTL Persian script with LTR technical notation. In production implementations, the primary system font maps directly to **Vazirmatn** (or **Shabnam**), with Western numerical and code tokens falling back to **JetBrains Mono**.

### Structural Rules
- **Bidirectional Discipline:** RTL layout flow is strictly maintained for Persian prose, section headings, and labels. Semantic semantic versions (`v1.4.2+28`), commit SHA hashes (`7f9b2a1`), and patch sizes (`2.4 MB`) render strictly in LTR monospaced format using `label-sm` or `code-md`.
- **Persian Numerals vs. LTR Tokens:** Descriptive metrics and counters utilize native Persian digits, whereas technical identifiers and system flags enforce raw Latin digits for terminal parity.
- **Vertical Metrics:** Persian glyphs have naturally higher ascenders and descenders than Latin typefaces. Line heights are tuned generously (1.6x–1.8x font size) to prevent diacritic clipping and maintain rhythmic scanning across compact table grids.

## Layout & Spacing
The layout model employs a strict 12-column desktop fluid grid designed for density without crowding. The core canvas operates with fixed utility panels anchored to the right side (RTL primary focus) and expanding analytical workspaces on the left.

### Grid & Breakpoints
- **Desktop (>= 1280px):** 12-column grid; 260px right-hand persistent navigation/app-switcher, 24px column gutters, 32px exterior canvas margin.
- **Tablet / Small Desktop (1024px – 1279px):** 12-column grid; 200px collapsed nav, 16px gutters, 24px exterior margin.
- **Compact (< 1023px):** Single-column stacked stream; full-width tables with horizontal scroll anchors, bottom-docked emergency killswitch, 16px margins.

### Spacing Principles
- Spacing units conform to a 4px/8px incremental base.
- Data tables adhere strictly to `space-sm` (8px) vertical cell padding and `space-md` (12px) horizontal padding to maintain high information density across release logs.
- Spatial grouping relies on 1px opacity-driven borders instead of expansive margins, preserving screen real estate for parallel data observation.

## Elevation & Depth
Depth in this system is communicated via **Flat Tonal Boundaries and Low-Contrast Outlines** rather than traditional drop shadows. Shadows are completely prohibited on data tables, input fields, and structure panes to keep the interface clinical and non-distracting.

### Surface Tiers
- **Tier 0 (Viewport Background):** `#F8FAFC` — Base structural foundation.
- **Tier 1 (Cards, Workspaces, Tabular Panes):** `#FFFFFF` bordered with `rgba(30, 41, 59, 0.10)`.
- **Tier 2 (Modals, Context Overlays, Menus):** `#FFFFFF` bordered with `rgba(30, 41, 59, 0.18)`, supported by a subtle low-dispersion ambient depth: `box-shadow: 0 4px 16px -2px rgba(30, 41, 59, 0.08)`.
- **Tier 3 (Destructive Kill-Switch Dialog):** `#FFFFFF` paired with an emergency border accent `rgba(225, 29, 72, 0.25)` and a dimming scrim overlay `rgba(15, 23, 42, 0.40)` with `backdrop-filter: blur(2px)`.

## Shapes
The shape language is strictly **Soft (Level 1)**, projecting technical rigidity, precision engineering, and spatial efficiency. Rounding is applied systematically to soften mechanical edge interactions without introducing playful consumer curves.

- **Badges, Inline Hash Pills, Status Tags:** 4px (`0.25rem`) border radius.
- **Buttons, Form Inputs, App Selectors:** 6px (`0.375rem`) border radius.
- **Data Cards, Modals, Tabular Containers:** 8px (`0.5rem`) border radius (`rounded-lg`).
- **Pill Shapes:** Disallowed throughout the entire interface; all rectangular elements retain structural corners.

## Components

### Buttons
- **Primary Deploy Action:** Background `#4F46E5`, text `#FFFFFF`, border none. Hover: `rgba(79, 70, 229, 0.90)`. Active: `rgba(79, 70, 229, 1.0)`.
- **Secondary / Action Ghost:** Background transparent, text `#1E293B`, border 1px solid `rgba(30, 41, 59, 0.16)`. Hover: background `rgba(30, 41, 59, 0.04)`.
- **Emergency Kill-Switch Button:** High-prominence destructive action. Idle: background `rgba(225, 29, 72, 0.06)`, border 1px solid `rgba(225, 29, 72, 0.35)`, text `#E11D48`. Armed/Hover: background `#E11D48`, text `#FFFFFF`, border 1px solid `#E11D48`.

### Status Badges & Release Pills
- Text-driven status indicators without bullet dots or graphic icons:
  - **Active / Released:** Text `#4F46E5`, background `rgba(79, 70, 229, 0.08)`, border 1px solid `rgba(79, 70, 229, 0.20)`.
  - **Rolled Back / Revoked:** Text `#E11D48`, background `rgba(225, 29, 72, 0.08)`, border 1px solid `rgba(225, 29, 72, 0.20)`.
  - **Draft / Staged:** Text `rgba(30, 41, 59, 0.70)`, background `rgba(30, 41, 59, 0.05)`, border 1px solid `rgba(30, 41, 59, 0.12)`.

### Multi-App Switcher
- Placed at the top-right in natural Persian reading orientation.
- Compact selector dropdown displaying current Flutter App Name, platform targets (`iOS`, `Android`), and current engine version. Framed with a 1px border `rgba(30, 41, 59, 0.12)` on surface `#FFFFFF`.

### Version Rollback Matrix Table
- **Header:** Background `rgba(30, 41, 59, 0.03)`, text `rgba(30, 41, 59, 0.70)`, font `label-lg`, bottom border 1px solid `rgba(30, 41, 59, 0.12)`.
- **Rows:** Alternating transparent and subtle rows. Border bottom 1px solid `rgba(30, 41, 59, 0.06)`. Hover state `rgba(79, 70, 229, 0.03)`.
- **Alignment:** Persian labels and patch descriptions align firmly to the right. Versions, build numbers, file sizes, and rollout percentages (`JetBrains Mono`) align strictly to the left for immediate comparative scanning.

### Patch Publisher Drawer / Modal
- Dedicated workflow surface for publishing `.patch` bundles.
- Includes binary hash validation box, targeted semver range inputs, canary traffic slider (0% to 100%), and a mandatory confirmation toggle for mandatory forced-updates.

### Client Activity Feed (Live Terminal)
- Monospaced, high-density stream anchored to the bottom or sidebar.
- Background `#FFFFFF`, inner container border 1px solid `rgba(30, 41, 59, 0.10)`.
- Log lines render timestamps in Persian digits, paired with LTR device UUIDs and HTTP/OTA sync status codes (`200 OK`, `304 Not Modified`, `410 Patch Revoked`).