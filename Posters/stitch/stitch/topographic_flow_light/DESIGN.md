# Design System Strategy: Precision Cartography

## 1. Overview & Creative North Star
The Creative North Star for this design system is **"Architectural Clarity."** 

By marrying the organic, fluid nature of topographic patterns with the rigid, sharp-edged precision of minimalist editorial design, we create an experience that feels both human and highly engineered. We are moving away from the "standard web" by utilizing ultra-sharp corners (0px radius) and intentional tonal layering. The system breaks the template look through high-contrast typography and "floating" solid panels that sit atop a textured, warm-white landscape. It is a digital environment that feels like a premium physical portfolio.

## 2. Colors & Texture
The palette is rooted in a warm, sophisticated neutral base, punctuated by a deep, authoritative teal.

### The Palette
- **Primary / Accent:** `#008080` (mapped to `primary_container`). This is our "ink." Use it for key CTAs and primary brand expressions.
- **Background:** `#fbf9f5` (warm white). This is the "paper."
- **Surface:** `#ffffff`. Content panels must be pure white to create a "lift" from the warm background.

### The "No-Line" Rule
Standard 1px borders are strictly prohibited for sectioning. Boundaries must be defined solely through background color shifts. For instance, a `surface_container_low` (`#f5f3ef`) sidebar should sit against a `surface` (`#fbf9f5`) main area. If a separation is needed, use the **Topographic Pattern** (utilizing `primary` at 5-10% opacity) as the transitional element between zones.

### Surface Hierarchy & Nesting
Treat the UI as a series of stacked, sharp-edged sheets. 
- **Base Level:** `background` (#fbf9f5) with topographic teal line-work.
- **Level 1 (Content Panels):** `surface_container_lowest` (#ffffff). These are solid, sharp-edged blocks.
- **Level 2 (In-Panel Details):** Use `surface_container` (#efeeea) for subtle nesting, like code snippets or secondary data points within a white panel.

### Signature Textures
To provide "soul," use a subtle linear gradient on primary buttons: transitioning from `primary` (#006565) to `primary_container` (#008080). This prevents the teal from feeling flat and "Default-Bootstrap."

## 3. Typography: The Editorial Voice
We use **Manrope** exclusively. It is a modern geometric sans-serif that maintains a technical edge.

- **Display (display-lg/md):** Use for hero moments. Set with tight tracking (-0.02em) to emphasize the architectural feel.
- **Headlines (headline-lg/md):** These are your "anchors." Use `on_surface` (#1b1c1a) for maximum contrast against the warm white background.
- **Body (body-lg/md):** Aim for generous line heights (1.6+) to ensure the minimalist aesthetic feels breathable rather than empty.
- **Labels (label-md/sm):** Use `primary` (#006565) and uppercase for small metadata to create a "technical blueprint" aesthetic.

## 4. Elevation & Depth
In this system, depth is a product of **tonal stacking**, not shadow-casting.

- **The Layering Principle:** Depth is achieved by placing a pure `#ffffff` (Lowest) panel over the `#fbf9f5` (Surface) background. The sharp 0px corners will create a natural "cut-out" effect.
- **Ambient Shadows:** Shadows are rarely used. If a floating element (like a Modal) is required, use a massive, soft spread: `box-shadow: 0 20px 80px rgba(0, 80, 80, 0.06);`. This uses the teal accent color as the shadow base, mimicking natural light filtering through the topographic environment.
- **The "Ghost Border" Fallback:** If accessibility requires a border, use `outline_variant` at 15% opacity. Never use high-contrast outlines.
- **Glassmorphism:** For navigation bars, use `surface` at 80% opacity with a `backdrop-filter: blur(20px)`. This allows the topographic lines to bleed through softly as the user scrolls, maintaining a sense of place.

## 5. Components

### Buttons
- **Primary:** Sharp edges (0px). Solid `primary_container` background with `on_primary_container` text. 
- **Secondary:** Sharp edges (0px). `outline` token at 20% opacity for the border. No fill.
- **Tertiary:** Text only in `primary`. Use for low-priority actions.

### Cards & Panels
- **Standard:** Solid `#ffffff` fill, **0px border radius**, no border. 
- **Interactive:** On hover, a card should not move or shadow-up; instead, shift the background color to `surface_container_low` (#f5f3ef).

### Inputs
- **Text Fields:** Underline-only style or a very subtle `surface_container` fill. Sharp corners. Use `on_surface_variant` for placeholders.
- **Focus State:** Transition the underline to 2px `primary` (#006565).

### Chips
- Use `secondary_container` (#c2e7e6) with 0px radius. They should look like small, cut-out labels from a map.

### Lists
- **Rule:** Forbid the use of horizontal dividers. Separate list items using the spacing scale (e.g., `spacing-4` / 1.4rem). If separation is critical, use a tonal shift on alternate rows.

## 6. Do’s and Don’ts

### Do
- **DO** use the topographic pattern sparingly. It should be a background texture, never a foreground element that interferes with text.
- **DO** embrace white space. If a layout feels "too empty," increase the typography size rather than adding more lines or boxes.
- **DO** align everything to a strict grid to reinforce the "architectural" feel, but break the grid occasionally with a single overlapping "floating" image panel.

### Don't
- **DON'T** use rounded corners. Everything must be 0px. Even a 2px radius will break the precision aesthetic of this system.
- **DON'T** use pure black (#000000). Always use `on_surface` (#1b1c1a) to keep the "warm editorial" feel intact.
- **DON'T** use standard grey shadows. Shadows must be tinted with teal or omitted entirely.