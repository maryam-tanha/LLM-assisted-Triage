# Design System Document

## 1. Overview & Creative North Star: "The Cartographic Brutalist"

This design system is engineered to transform the traditional academic poster into a high-end editorial experience. Moving away from the cluttered, "bullet-point" aesthetic of standard research presentations, this system adopts a **Cartographic Brutalist** approach. It combines the organic, fluid movement of topographic data with the rigid, uncompromising precision of architectural minimalism.

The "Flow" is achieved through a dynamic background layer, while the "Structure" is maintained through opaque, razor-sharp geometric panels. By utilizing intentional asymmetry and a high-contrast monochromatic-to-teal palette, we create a visual hierarchy that guides the viewer's eye through complex data with the ease of a curated gallery exhibit.

---

## 2. Colors & Surface Logic

The palette is anchored in deep oceanic tones, punctuated by a singular, high-vibrancy accent. It is designed for maximum legibility in large-format print and high-resolution digital displays.

### Core Palette (Material Design Implementation)
*   **Surface/Background (`#081325`):** The foundation. A deep, "near-black" navy that provides infinite depth.
*   **Primary/Accent (`#FFFFFF`):** Reserved for high-priority data and titles. It provides a stark, surgical contrast against the dark base.
*   **Surface Tint/Teal (`#38DEBB`):** The "Topographic Flow" color. Used for interactive patterns, data visualization accents, and subtle textural shifts.
*   **Surface Container Hierarchy:**
    *   `surface_container_lowest`: `#040E20` (For recessed, background-level information)
    *   `surface_container`: `#152032` (Standard panel background)
    *   `surface_container_highest`: `#2B3548` (For "Active" or high-priority callouts)

### The "No-Line" Rule
Sectioning must never be achieved through 1px solid borders. Boundaries are defined strictly through:
1.  **Tonal Shifts:** Placing a `surface_container_high` panel directly onto the `surface` background.
2.  **Negative Space:** Utilizing the Spacing Scale (specifically `8` to `12`) to create "rivers" of background space that act as natural dividers.

### Signature Textures
The "Topographic Flow" isn't just a static image—it is a living texture. Use the `surface_tint` (`#38DEBB`) at 10-15% opacity for the topographic line work. These lines should weave *behind* the opaque panels, creating a sense of layered depth where the data sits on top of the terrain.

---

## 3. Typography: The Editorial Scale

We utilize **Manrope** (a modern, highly-legible descendant of the Montserrat spirit) to maintain a professional, academic, yet cutting-edge feel.

*   **Display Large (3.5rem / 56px):** Used for the main Research Title. Tracking should be set to `-0.02em` for a tighter, "locked-in" editorial look.
*   **Headline Medium (1.75rem / 28px):** Section headers (e.g., *Methodology*, *Results*). Must be Uppercase to reinforce the Brutalist aesthetic.
*   **Body Large (1rem / 16px):** Primary narrative text. Increase line-height to `1.6` to ensure readability from a standing distance.
*   **Label Small (0.6875rem / 11px):** Captions, data sources, and fine-print citations.

**Typographic Intent:** Hierarchy is established through extreme scale shifts. A massive Display title juxtaposed against a lean Body paragraph creates a "Hero" moment that draws viewers in from across a room.

---

## 4. Elevation & Depth: Tonal Layering

This system rejects drop shadows in favor of **Tonal Layering**. Because the panels are opaque and sharp-edged, depth is a matter of "luminance stacking."

*   **The Layering Principle:** 
    *   Base Layer: `surface` (`#081325`) with Topographic Teal lines.
    *   Mid Layer: `surface_container` (`#152032`) for standard content blocks.
    *   Top Layer: `primary_fixed` (`#5FFBD6`) for critical data highlights or "Floating" navigation.
*   **0px Radius Mandate:** Every component, button, and panel must use a `0px` border radius. This creates a "precision-cut" feel, suggesting the accuracy of the academic data presented.
*   **Ghost Borders:** If a panel requires additional definition against a similarly toned background, use the `outline_variant` (`#3C4A45`) at 20% opacity. It should be felt, not seen.

---

## 5. Components

### Opaque Content Panels
The workhorse of the system.
*   **Background:** `surface_container` (`#152032`).
*   **Corner:** 0px (Sharp).
*   **Padding:** Scale `6` (2rem) minimum to allow the content to "breathe" within the dark void.
*   **Interaction:** No dividers. Use `surface_container_high` for nested sub-sections.

### Data Chips & Tags
*   **Style:** `surface_container_highest` background with `on_surface_variant` text.
*   **Shape:** 0px Rectangular.
*   **Use Case:** Categorizing data points or listing research variables.

### Primary Action / Callout (The "Teal Moment")
*   **Style:** Background `surface_tint` (`#38DEBB`) with `on_primary` text (`#00382D`).
*   **Impact:** Use sparingly. This is the visual "north star" of the poster—ideal for the "Conclusion" or "Key Finding" block.

### Modern List Items
*   **Constraint:** Forbid the use of bullet points.
*   **Implementation:** Use a 2px vertical accent line of `primary_container` to the left of the list item, or use `title-sm` typography with a `primary` color for the first word of every list item to create a rhythmic, structured flow.

---

## 6. Do’s and Don’ts

### Do:
*   **Embrace Asymmetry:** Align the main title to the far left, but allow data visualizations to break the grid and overlap the "Topographic Flow" lines.
*   **Use High-Contrast Spacing:** Use `spacing.20` (7rem) to separate major sections. White space in a dark theme is "Luxurious Space."
*   **Maintain Sharpness:** Ensure all imagery and icons have the same "hard edge" as the panels. No rounded icons or soft-focus photography.

### Don’t:
*   **Don't Use Gradients for Depth:** Rely on flat color shifts between `surface` tiers.
*   **Don't Use 1px Borders:** They clutter the "Flow" and make the design look like a standard spreadsheet.
*   **Don't Use Shadows:** The 0px radius aesthetic is weakened by soft shadows. If you need separation, lighten the panel's background color instead.
*   **Don't Center-Align Everything:** Traditional posters center everything. This system thrives on "Edge-Alignment"—align text to the left or right margins of a panel to emphasize the Brutalist grid.