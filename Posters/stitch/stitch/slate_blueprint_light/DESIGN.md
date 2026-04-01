# Design System Strategy: The Architectural Scholar

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"The Digital Blueprints."** We are moving away from the generic "SaaS Dashboard" aesthetic and toward a high-end, editorial experience that feels like a meticulously drafted technical drawing from a prestigious university.

This system breaks the "template" look through **intentional technical precision.** We replace standard borders with a faint, mathematical cyan grid and use high-contrast typography scales to create a sense of authoritative hierarchy. The goal is to make the user feel like they are interacting with a living document—one that is both intellectually grounded (Academic Serif) and technologically advanced (Clean Sans-Serif and Cyan Accents).

## 2. Colors: The Blueprint Palette
Our color strategy relies on "Technical Clarity." We avoid heavy blacks and muddy greys in favor of a crisp, airy atmosphere.

*   **Primary (#00677d) & Primary Container (#00b4d8):** Use these for high-intent actions. The Primary Container (our signature Cyan) should be used for highlights that mimic a "highlighter" or "cyanotype" effect.
*   **The "No-Line" Rule:** 1px solid borders are strictly prohibited for sectioning. To separate content, use the `surface-container` tiers or the background grid itself. Boundaries must feel like shifts in paper weight or light, not "boxes."
*   **Surface Hierarchy & Nesting:** Treat the UI as layers of vellum. 
    *   **Level 0 (Background):** `surface` (#f8fafb) with a 12px or 16px cyan grid overlay at 5-8% opacity.
    *   **Level 1 (Panels):** `surface_container_lowest` (#ffffff) for floating panels.
    *   **Level 2 (Insets):** `surface_container_low` (#f2f4f5) for nested content like code blocks or metadata sidebars.
*   **The "Glass & Gradient" Rule:** For floating navigation or modal overlays, use a `surface` color with `backdrop-blur: 12px` and 85% opacity. For CTAs, apply a subtle linear gradient from `primary` to `primary_container` at a 135-degree angle to add "ink depth."

## 3. Typography: Editorial Authority
The juxtaposition of `notoSerif` and `inter` creates a "Scholar-meets-Engineer" persona.

*   **Display & Headlines (Noto Serif):** These are your "Titles." They should be used with generous leading. Never use all-caps for Noto Serif; let the letterforms breathe. 
    *   *Usage:* Page titles, section headers, and high-level storytelling.
*   **Body & Labels (Inter):** This is your "Technical Data." Inter provides the crispness required for complex information.
    *   *Usage:* Paragraphs, data tables, and button labels.
*   **The Contrast Rule:** Always pair a `headline-lg` (Serif) with a `label-md` (Sans-Serif) nearby to ground the editorial feel with functional clarity.

## 4. Elevation & Depth: Tonal Layering
We do not use structural lines to define space; we use light and physics.

*   **The Layering Principle:** To separate a card from the background, place a `surface_container_lowest` card on the `surface` background. The subtle shift from #f8fafb to #ffffff provides enough "pop" without visual clutter.
*   **Ambient Shadows:** For floating elements, use a "Cyan-Tinted Shadow." Instead of a grey shadow, use a 4% opacity shadow with a hue of 190 (Cyan).
    *   *Spec:* `0px 10px 30px rgba(0, 103, 125, 0.06)`. This mimics light passing through a blueprint.
*   **The "Ghost Border" Fallback:** If a divider is mandatory for accessibility, use `outline_variant` (#bcc9ce) at 15% opacity. It should be barely visible—a "suggestion" of a line.
*   **Glassmorphism:** Apply to top navigation bars. Use `surface_container_lowest` at 80% opacity with a blur effect to allow the cyan background grid to peak through as the user scrolls.

## 5. Components: The Drafted Elements

*   **Buttons:** 
    *   *Primary:* Solid `primary` with `on_primary` text. Use `rounded-md` (0.375rem).
    *   *Secondary:* `surface_container_high` background with `primary` text. No border.
*   **Input Fields:** Use `surface_container_lowest`. For the "Active" state, do not use a thick border; instead, use a 2px bottom-border of `primary_container` and a very soft cyan outer glow.
*   **Cards:** Use `surface_container_lowest` with the "Ambient Shadow" spec. **Forbid dividers.** Use `3` (1rem) or `4` (1.4rem) spacing to separate header and body content within the card.
*   **Chips:** Use `secondary_container` for a muted, technical look. Font should be `label-sm` in all-caps with 0.05em letter spacing to mimic architectural annotations.
*   **Data Grids:** Use `surface_container_low` for header rows. Use `px` (1px) spacing for the "grid" effect, but make the line color `outline_variant` at 10% opacity.
*   **Architectural Grid Overlay:** A global component. A CSS-pattern background of 24px squares using `primary_fixed_dim` at 5% opacity, serving as the "blueprint" base for all pages.

## 6. Do's and Don'ts

### Do:
*   **Do** use asymmetrical margins. For example, a wider left margin for a headline to create an "editorial" layout.
*   **Do** use the `primary_container` (#00b4d8) as a background for small, high-impact labels or badges.
*   **Do** prioritize whitespace. If a layout feels "tight," double the spacing using the `8` (2.75rem) or `10` (3.5rem) tokens.

### Don't:
*   **Don't** use 100% black text. Always use `on_surface` (#191c1d) to maintain the soft, sophisticated ink feel.
*   **Don't** use heavy drop shadows. If it looks like it’s "hovering" more than a few millimeters off the page, it's too heavy.
*   **Don't** use standard "Success Green." Use the `tertiary` (#914d00) or `primary` tones where possible to keep the palette tight and professional, unless it is a critical system error.