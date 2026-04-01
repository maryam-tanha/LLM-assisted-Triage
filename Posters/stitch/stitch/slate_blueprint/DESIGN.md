# Design System Document: The Scholarly Blueprint

## 1. Overview & Creative North Star
**Creative North Star: "The Digital Architect’s Folio"**

This design system moves away from the static, flat nature of traditional academic posters, instead embracing a layered, high-fidelity editorial experience. We are treating the 40x27 canvas not as a flat sheet, but as a three-dimensional drafting table. 

By leveraging a rigorous architectural grid against deep, atmospheric slate tones, we create a sense of "Emergent Knowledge." The design breaks the "template" look through **intentional asymmetry**: large-scale serif display type should bleed or anchor to the grid in non-traditional ways, while content panels float with sophisticated tonal depth. This isn't just a poster; it’s a high-end data visualization environment.

---

## 2. Colors & Surface Architecture
The palette is rooted in a professional, "Blue-Note" spectrum, using cyan as a functional tool rather than a decorative flourish.

### Palette Strategy
- **Background (`#021525`):** Our foundation. It provides the "infinity" of a dark drafting room.
- **Primary (`#4cd6fb` / Cyan):** Used for highlighting critical data points, callouts, and the underlying grid.
- **Secondary (`#b9c8de` / Cool Slate):** Used for meta-information and supporting text to ensure it doesn't compete with the Primary information.

### The "No-Line" Rule
**Explicit Instruction:** Prohibit 1px solid borders for sectioning. In this system, boundaries are defined by **Surface Nesting**. 
- Use `surface_container_low` for large section backgrounds.
- Use `surface_container_high` for nested cards.
- Transitioning between these tiers creates "soft" edges that feel premium and integrated, rather than "boxed in."

### Glass & Gradient Rule
To achieve a "Blueprint" feel, use **Glassmorphism** for floating overlays. Apply a `surface_variant` at 60% opacity with a `backdrop-filter: blur(12px)`. For main CTAs or section headers, utilize a subtle linear gradient from `primary` to `primary_container` (angled at 135°) to give the cyan a "glowing" neon-ink quality.

---

## 3. Typography: The Editorial Contrast
We juxtapose the classic authority of a serif with the technical precision of a modern sans-serif.

| Level | Token | Font | Size | Character |
| :--- | :--- | :--- | :--- | :--- |
| **Display** | `display-lg` | Noto Serif | 3.5rem | High-contrast, authoritative. Use for the Main Title. |
| **Headline**| `headline-md`| Noto Serif | 1.75rem | Academic rigor. Use for Section Titles (Abstract, Results). |
| **Title** | `title-lg` | Inter | 1.375rem | Bold, technical. Use for Sub-headers and Card Titles. |
| **Body** | `body-md` | Inter | 0.875rem | Maximum legibility. 1.6x line-height for readability. |
| **Label** | `label-sm` | Inter | 0.6875rem | All-caps, tracked out (+5%). Use for grid coordinates and captions. |

---

## 4. Elevation & Depth
In this system, depth is a functional variable, not a decoration.

- **The Layering Principle:** Stacking follows the light source. A `surface_container_lowest` panel should sit on a `surface` background to feel "etched" into the blueprint. A `surface_container_highest` panel should feel "resting" on top.
- **Ambient Shadows:** When a panel must float, use a shadow with a 32px blur and 6% opacity. The shadow color must be a tinted cyan-slate (`#001f27`) to simulate the way light interacts with the deep blue background.
- **The "Ghost Border" Fallback:** If a boundary is visually ambiguous, use the `outline_variant` token at **15% opacity**. This creates a "hairline" guide that mimics a technical drawing without adding visual clutter.
- **Architectural Grid:** The background must feature a faint grid using `primary_container` at 10% opacity. This grid is the "logic" of the poster; all components must snap to it.

---

## 5. Components

### Content Panels (Cards)
*   **Style:** No borders. Background: `surface_container`. 
*   **Spacing:** Use `spacing-6` (2rem) for internal padding to give academic text room to breathe.
*   **Interaction:** On hover/focus, shift background to `surface_bright` and increase shadow spread.

### Data Chips
*   **Style:** Use `secondary_container` for the pill shape. 
*   **Typography:** `label-md` in `on_secondary_container`.
*   **Usage:** Labeling methodology, variables, or tags.

### Buttons & CTAs
*   **Primary:** Fill with `primary` (`#4cd6fb`), text in `on_primary`. High-gloss finish.
*   **Tertiary (Ghost):** No background. `primary` text. Use for less critical links or citations.

### Blueprint Annotations (Unique Component)
*   **Style:** Small `label-sm` text paired with a 1px `primary_fixed_dim` line (at 40% opacity) that "points" to a specific chart or data point. This reinforces the architectural aesthetic.

### Inputs & Fields
*   **Text Fields:** Use `surface_container_highest`. Avoid the "box" look; use a bottom-only indicator line in `outline_variant` that glows `primary` upon focus.

---

## 6. Do’s and Don'ts

### Do:
*   **Use Whitespace as a Separator:** Use `spacing-12` or `spacing-16` between major content blocks rather than lines.
*   **Embrace Asymmetry:** Let the main title take up 2/3 of the top width, leaving 1/3 for "Meta-data" (Authors, Date, Affiliation) to create a modern editorial feel.
*   **Snap to Grid:** Ensure every panel edge aligns perfectly with the underlying cyan grid.

### Don’t:
*   **Don't use 100% White:** Use `on_surface` (`#d1e4fb`) for body text. Pure white (#FFFFFF) is too harsh against the slate and should be reserved for the most extreme highlights or "sparkle" in data points.
*   **Don't use standard Drop Shadows:** Avoid the "fuzzy grey" shadow. If it isn't tinted with the slate/cyan base, it will look like a generic template.
*   **Don't crowd the margins:** Maintain a minimum of `spacing-20` (7rem) as a global "safe zone" around the edges of the 40x27 canvas.