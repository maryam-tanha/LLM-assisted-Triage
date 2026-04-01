# Design System Document: Academic Editorial Excellence

## 1. Overview & Creative North Star
**The Creative North Star: "The Ethereal Archive"**

This design system moves away from the rigid, boxed-in constraints of traditional scientific posters. Instead, it treats the 40x27 canvas as a deep-space environment where data floats. The goal is to create a "Frosted Acetate" effect—mimicking physical layers of translucent material suspended over a dark, networked void. 

To break the "template" look, we employ **intentional asymmetry**. Primary research findings should not sit in perfect rows; they should feel layered, with subtle overlaps and varying levels of frosted transparency that suggest intellectual depth and interconnectedness.

## 2. Colors & Surface Philosophy
The palette is rooted in a high-contrast, near-black environment, punctuated by a "Teal Glow" that represents the spark of data and discovery.

### Surface Hierarchy & Nesting
We reject flat layouts. The UI is a series of physical layers.
- **The Foundation:** Use `surface_dim` (#0e0e0e) for the primary background. 
- **The "No-Line" Rule:** 1px solid borders are strictly prohibited for sectioning. To define a content area, use a background shift. For example, a "Results" section should be a `surface_container_low` (#131313) panel sitting on the `surface` (#0e0e0e) background.
- **The "Glass & Gradient" Rule:** All primary content panels must utilize Glassmorphism. Apply `surface_container` with an opacity of 60-80% and a high `backdrop-filter: blur(20px)`. This allows the "network nodes" of the background to bleed through as soft, diffused shapes.
- **Signature Textures:** Use a subtle radial gradient transitioning from `primary` (#5bf4de) to `primary_container` (#11c9b4) at 15% opacity for hero callouts or key data visualizations to give them a "holographic" pulse.

## 3. Typography
The typography system pairs the authority of classical serif faces with the precision of modern sans-serifs for metadata.

- **Display & Headline (Newsreader/Playfair Display):** Used for the poster title and major section headers. The high contrast of the letterforms evokes a prestigious, archival feel. 
    - *Usage:* `display-lg` for the main title, tracked slightly tighter (-2%) to feel bespoke.
- **Body (Noto Serif/Lora):** Used for the narrative of the research. The serif ensures readability at large scale while maintaining the academic tone.
    - *Usage:* `body-lg` for abstract and conclusions; `body-md` for general methodology.
- **Labels (Inter):** Used for data points, figure captions, and citations. This provides a "technical" contrast to the organic serifs.
    - *Usage:* `label-md` in `on_surface_variant` (#adaaaa) to provide a secondary information layer.

## 4. Elevation & Depth
Depth is the core of the "Frosted Acetate" aesthetic. We achieve this through **Tonal Layering**.

- **The Layering Principle:** Stack `surface_container_highest` (#262626) elements on top of `surface_container_low` (#131313) panels to create a natural lift. The eye perceives the lighter tone as being closer to the viewer.
- **Ambient Shadows:** For floating elements (like a featured graph or a floating QR code), use a shadow with a 40px blur at 8% opacity, using the `primary` (#5bf4de) hue instead of black. This creates a "glow" rather than a "shadow," suggesting the element is emitting light from the network below.
- **The "Ghost Border" Fallback:** If visual separation is failing, use a `0.5px` stroke of `outline_variant` (#494847) at 20% opacity. It should be felt, not seen.
- **Distortion:** All containers must have a `backdrop-filter: saturate(150%) blur(12px)`. This makes the "acetate" feel thick and premium.

## 5. Components

### Content Panels (The "Acetate" Sheets)
- **Styling:** No borders. `surface_container_low` with 70% opacity.
- **Rounding:** Use `xl` (0.75rem) for a modern, architectural feel.
- **Spacing:** Use `10` (3.5rem) padding internally to ensure the text "breathes" against the edges of the glass.

### Data Visualization Callouts (Chips)
- **Selection/Action Chips:** Use `primary_container` (#11c9b4) with `on_primary_container` text. 
- **Rounding:** `full` (9999px) to contrast against the rectangular panels.

### Interaction Elements (Buttons)
- **Primary:** A solid fill of `primary` (#5bf4de) with `on_primary` (#00594f) text. No shadow; use a subtle outer glow of the same color on hover.
- **Tertiary:** Text-only using `primary` color, with an underline that only appears on hover.

### Narrative Flow (Lists & Cards)
- **The "No-Divider" Rule:** Forbid the use of divider lines between list items. Use the Spacing Scale `4` (1.4rem) to create separation through negative space.
- **Input Fields:** For interactive posters, fields should be `surface_container_highest` with a `primary` bottom-border only (2px) when focused.

## 6. Do's and Don'ts

### Do:
- **Do** overlap panels slightly. Let a figure caption hover partially over a photo and partially over the background to emphasize the "layered" nature.
- **Do** use the Teal Glow (`primary`) sparingly. It is a highlighter, not a floodlight.
- **Do** use `surface_container_lowest` (#000000) for deep "void" areas where you want to draw the eye into the background network.

### Don't:
- **Don't** use 100% opaque white for body text. Use `on_surface` or `on_background` which are slightly softened to prevent "halidom" (visual vibrating) on the black background.
- **Don't** use standard "Drop Shadows." They break the illusion of translucency.
- **Don't** align everything to a rigid 12-column grid. Use the Spacing Scale to create "weighted" asymmetry—for example, a wide left margin (Scale `20`) balanced by a dense cluster of data on the right.