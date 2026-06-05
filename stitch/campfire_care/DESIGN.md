---
name: Campfire Care
colors:
  surface: '#fcfaef'
  surface-dim: '#dcdad0'
  surface-bright: '#fcfaef'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f4e9'
  surface-container: '#f0eee3'
  surface-container-high: '#eae8de'
  surface-container-highest: '#e4e3d8'
  on-surface: '#1b1c16'
  on-surface-variant: '#404a3b'
  inverse-surface: '#30312a'
  inverse-on-surface: '#f3f1e6'
  outline: '#707a69'
  outline-variant: '#bfcab6'
  surface-tint: '#106e00'
  primary: '#106e00'
  on-primary: '#ffffff'
  primary-container: '#76d15e'
  on-primary-container: '#0b5800'
  inverse-primary: '#80dc67'
  secondary: '#00677e'
  on-secondary: '#ffffff'
  secondary-container: '#92e3ff'
  on-secondary-container: '#00667d'
  tertiary: '#6e5e00'
  on-tertiary: '#ffffff'
  tertiary-container: '#d3bc4e'
  on-tertiary-container: '#584b00'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#9bf980'
  primary-fixed-dim: '#80dc67'
  on-primary-fixed: '#022100'
  on-primary-fixed-variant: '#0a5300'
  secondary-fixed: '#b5ebff'
  secondary-fixed-dim: '#81d2ee'
  on-secondary-fixed: '#001f28'
  on-secondary-fixed-variant: '#004e60'
  tertiary-fixed: '#fbe270'
  tertiary-fixed-dim: '#dec657'
  on-tertiary-fixed: '#211b00'
  on-tertiary-fixed-variant: '#534600'
  background: '#fcfaef'
  on-background: '#1b1c16'
  surface-variant: '#e4e3d8'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '800'
    lineHeight: 48px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 28px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-bold:
    fontFamily: Quicksand
    fontSize: 14px
    fontWeight: '700'
    lineHeight: 20px
  label-sm:
    fontFamily: Quicksand
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
rounded:
  sm: 0.5rem
  DEFAULT: 1rem
  md: 1.5rem
  lg: 2rem
  xl: 3rem
  full: 9999px
spacing:
  unit: 8px
  container-padding: 24px
  element-gap: 16px
  section-margin: 40px
  max-width: 1200px
---

## Brand & Style

The design system is inspired by the organic, welcoming aesthetic of "Animal Crossing," tailored specifically for a child-focused intervention system. The brand personality is **nurturing, whimsical, and celebratory**, turning behavioral correction into a collaborative "island life" adventure.

The style is a blend of **Tactile/Skeuomorphism** and **Soft Minimalism**. It utilizes paper-texture backgrounds, subtle shadows that mimic layered cardboard or thick cardstock, and UI elements that feel "squishy" and physically present. Every interaction is designed to reduce the anxiety of "correction" and replace it with the joy of "growth." The emotional response should be one of safety and encouragement, ensuring children feel empowered rather than monitored.

## Colors

The palette is derived from nature to evoke an outdoor, playful atmosphere. 
- **Leaf Green (#76D15E):** Used for growth-related actions, success states, and primary navigation buttons.
- **Sky Blue (#85D6F2):** Applied to informational bubbles, parent-facing data, and calm instructional areas.
- **Sun Yellow (#F9E06E):** Reserved for highlights, rewards, "New Task" alerts, and energetic call-outs.
- **Cream White (#FDFBF0):** The primary surface color, often layered with a subtle grain texture to mimic thick watercolor paper.
- **Text & Accents:** A warm, dark wood brown (#4B3F36) is used instead of pure black to maintain a soft, organic look while ensuring high legibility for young readers.

## Typography

Typography in this design system prioritizes legibility and a "friendly" hand-drawn feel. 

**Plus Jakarta Sans** is used for headlines to provide a modern yet soft geometric structure. For body copy, **Be Vietnam Pro** offers a warm, contemporary tone that remains easy to read during long instructional segments. **Quicksand** is utilized for labels and UI micro-copy, as its rounded terminals reinforce the gentle nature of the brand.

Headlines should use high-contrast weight (700-800) to stand out against textured backgrounds. Line heights are generous to prevent the UI from feeling "crowded," which is essential for maintaining focus in an intervention-based tool.

## Layout & Spacing

The layout philosophy follows a **Fluid Grid** with intentional "wiggle room." Instead of rigid, sharp alignments, the design system encourages slightly offset elements and asymmetrical compositions that feel "tossed onto a desk."

- **Desktop:** A 12-column grid with wide 32px gutters. Content is centered in a max-width container to prevent eye strain.
- **Mobile:** A single-column flow with 24px side margins. Cards should span the full width minus margins to provide large tap targets for small hands.
- **Spacing Rhythm:** Based on an 8px scale. Padding within cards should be generous (min 24px) to ensure a breezy, low-stress information density.

## Elevation & Depth

Depth is achieved through **Tonal Layers and Soft Shadows**, mimicking the look of physical cut-outs.

- **Background:** A base layer of Cream White with a low-opacity paper fiber texture.
- **Surface (Level 1):** Large cards use a very soft, multi-layered shadow with a subtle brown tint (`rgba(75, 63, 54, 0.1)`) to make them feel like they are resting on the paper.
- **Interactive (Level 2):** Buttons and active elements have a thicker, "bottom-heavy" shadow (resembling a 3D block) that disappears or "depresses" when clicked.
- **Overlays:** Modals and tooltips use a light "Cloud" blur (backdrop-filter) to gently obscure the background without completely disconnecting the user from the interface.

## Shapes

The design system strictly avoids sharp corners. All containers, buttons, and icons use **Pill-shaped (Level 3)** or heavily rounded profiles. 

- **Organic Variants:** Where possible, large containers should have a slight "blobtastic" variation—corners that aren't perfectly uniform—to mimic hand-cut paper or natural shapes like leaves and stones.
- **Iconography:** Icons must be "chunky" with thick strokes and rounded ends. No needle-thin lines.

## Components

### Buttons & Inputs
- **The "Bouncy" Button:** Primary buttons are green with a thick dark-green bottom border (3D effect). On hover, they should scale up slightly (1.05x); on click, they should scale down (0.95x) and the bottom border should flatten.
- **Input Fields:** Thick, rounded borders in Sky Blue. The cursor should be a custom soft-brown bar.

### Cards & Communication
- **The "Speech Bubble" Card:** Most content is delivered via cards that have a small triangular "pointer" at the bottom-left, resembling character dialogue from the game.
- **Sticker Chips:** Status indicators (e.g., "Done!", "Helping Out") should look like physical stickers with a thin white border and a slight rotation (±2 degrees).

### Progress & Feedback
- **Growth Bars:** Progress bars use a "Sprout to Tree" metaphor. The bar itself is a hollow vine, and the fill is a vibrant Leaf Green.
- **Reward Modals:** Full-screen Sun Yellow overlays with "Confetti" (leaf shapes) to celebrate task completion.

### Parents' Dashboard
- **Note Cards:** Information for parents is presented on "Sticky Note" style components in a soft blue, pinned with a circular "tack" icon to differentiate adult-level data from the child's playful interface.