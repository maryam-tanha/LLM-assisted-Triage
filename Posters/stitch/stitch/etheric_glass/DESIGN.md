# Design System Document: The Ethereal Edge

## 1. Overview & Creative North Star
**Creative North Star: The Digital Curator**

This design system is built on the philosophy of "The Digital Curator"—a high-end, editorial approach to digital interfaces that treats every screen as a gallery space. We are moving beyond the "flat web" by embracing depth, light refraction, and atmospheric immersion. 

The aesthetic is inspired by premium glassmorphism: a world of multi-layered transparency where content doesn't just sit on a screen, but floats within a rich, three-dimensional space. By leveraging massive backdrop blurs (24px+) and high-contrast typography, we create a signature look that feels expensive, intentional, and calm. We break the rigid, boxy nature of standard grids through intentional asymmetry and "overlapping" glass panels that suggest a physical, tactile stacking of information.

---

## 2. Colors & Surface Logic
The palette is a sophisticated blend of deep navy foundations (`#0e141a`) and vibrant, luminescent teal accents (`#45d8ed`).

### The "No-Line" Rule
Traditional 1px solid borders for sectioning are strictly prohibited. Layout boundaries must be defined through:
1.  **Tonal Shifts:** Placing a `surface-container-low` section against a `surface` background.
2.  **Glass Panels:** Using transparency and backdrop-blur to create a "material" difference rather than a line.

### Surface Hierarchy & Nesting
Treat the UI as a series of nested glass sheets. To create depth, use the Tiered Surface Scale:
*   **Base Layer:** `surface` (#0e141a) – The infinite void.
*   **Lower Tier:** `surface-container-low` (#161c22) – Subtle secondary zones.
*   **Active Tier:** `surface-container-highest` (#2f353c) – For prominent, interactive elements.
*   **The Hero Surface:** Use `surface-tint` at 10% opacity with a `backdrop-blur` of 24px+ to create the signature "Frosted Glass" panel.

### The "Glass & Gradient" Rule
Floating elements should never be solid. Use a linear gradient on the background of glass panels: 
`Top-Left: rgba(255, 255, 255, 0.08)` to `Bottom-Right: rgba(255, 255, 255, 0.02)`.
Apply a **Signature Texture**: A subtle mesh gradient in the background (using `primary` and `secondary_container`) provides the "soul" behind the glass.

---

## 3. Typography
We utilize a dual-font strategy to balance editorial authority with functional clarity.

*   **Display & Headlines (Manrope):** Used for large, expressive moments. `display-lg` (3.5rem) should be used with tight letter-spacing (-0.02em) to create a bold, "locked-in" editorial feel.
*   **Functional UI (Inter):** Used for `title`, `body`, and `label` roles. This ensures maximum legibility against complex, blurred backgrounds.

**Hierarchy as Identity:** Use high contrast in scale. Pair a `display-md` headline with a `body-sm` description to create a sophisticated, "magazine" layout style that feels premium and curated.

---

## 4. Elevation & Depth
In this system, elevation is a product of light and refraction, not just shadows.

*   **The Layering Principle:** Stacking is preferred over shadowing. An inner card (`surface-container-highest`) placed inside a larger panel (`surface-container-low`) creates natural focus.
*   **Ambient Shadows:** If a floating effect is required, shadows must be "Ambient."
    *   **Blur:** 40px - 60px.
    *   **Opacity:** 6% of the `on-surface` color.
    *   **Purpose:** To suggest a soft glow or a lift, never a harsh drop-shadow.
*   **The Glass Edge (Ghost Border):** To simulate the edge of a physical piece of glass, use a 1px inner border (inset) using `outline-variant` at 15% opacity. This "Ghost Border" catches the light without creating a hard visual break.

---

## 5. Components

### Buttons
*   **Primary:** A vibrant `primary` (#45d8ed) fill. For a premium touch, use a subtle gradient from `primary` to `primary_container`. 
*   **Secondary (Glass):** No fill. A 1px `Ghost Border` and a `backdrop-blur` of 12px.
*   **Rounding:** Always use `lg` (2rem) or `full` for buttons to contrast the `md` (1.5rem/24px) panel corners.

### Cards & Lists
*   **The Divider Ban:** Vertical dividers are forbidden. Use spacing `6` (2rem) or a background shift to `surface-container-lowest` to separate content blocks.
*   **Panels:** All main containers must use `md` (1.5rem / 24px) roundness.

### Input Fields
*   **Styling:** Inputs should feel like "recessed" glass. Use `surface-container-lowest` with an inner shadow to simulate a carved-out space in the interface.
*   **Active State:** Transition the border to `primary` at 40% opacity; do not use high-contrast solid lines.

### Glass Tooltips
*   Small-scale components that use the `surface-bright` token at 80% opacity with an aggressive 32px blur to ensure text remains legible over any background noise.

---

## 6. Do's and Don'ts

### Do:
*   **Do** use overlapping elements. Let a glass panel partially cover a background gradient to show off the `backdrop-blur`.
*   **Do** use asymmetrical layouts. Push content to the edges or use wide margins (`spacing-24`) to create breathing room.
*   **Do** ensure accessibility. Check that `on-surface` text on glass panels maintains a 4.5:1 contrast ratio against the blurred background.

### Don't:
*   **Don't** use 100% opaque black or white borders. It breaks the "Ethereal" illusion.
*   **Don't** use sharp corners. Everything must feel smoothed and "water-worn" (Minimum 24px for large panels).
*   **Don't** clutter the "Glass." If a panel has too much information, it loses its premium, lightweight feel. Use `spacing-10` between internal elements to let the content breathe.