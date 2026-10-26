---
name: RepoLens Field Map
description: A technical-terrain interface where the report is a route and each technology is a control.
colors:
  course-purple: "#6b3fa0"
  forest-green: "#4f6f3a"
  contour-brown: "#9a6b43"
  paper-ground: "#f3eedf"
  surface: "#fbf7e9"
  ink: "#2d2d27"
  muted-ink: "#5b5a4f"
  boundary: "#c8c0ad"
  night-ground: "#171c16"
  night-surface: "#1d241b"
  night-ink: "#f1eddc"
typography:
  display:
    fontFamily: "RepoLens Map, Arial Narrow, PingFang SC, sans-serif"
    fontSize: "96px"
    fontWeight: 700
    lineHeight: 0.84
    letterSpacing: "-0.04em"
  body:
    fontFamily: "Segoe UI, PingFang SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.8
  label:
    fontFamily: "Cascadia Code, JetBrains Mono, Consolas, monospace"
    fontSize: "9px"
    fontWeight: 400
    lineHeight: 1.4
rounded:
  none: "0px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "18px"
  xl: "26px"
  section: "56px"
components:
  button-primary:
    backgroundColor: "{colors.course-purple}"
    textColor: "{colors.surface}"
    rounded: "{rounded.none}"
    padding: "10px 15px"
  button-primary-hover:
    backgroundColor: "#522e7c"
    textColor: "{colors.surface}"
    rounded: "{rounded.none}"
  source-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "7px 0"
  tab-active:
    backgroundColor: "transparent"
    textColor: "{colors.course-purple}"
    rounded: "{rounded.none}"
    padding: "8px 0"
  control-row:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    rounded: "{rounded.none}"
    padding: "13px 2px"
---

# Design System: RepoLens Field Map

## Overview

**Creative North Star: "The Orienteering Sheet"**

RepoLens is a terrain, not a dashboard. The interface borrows the discipline of an orienteering map: a cream paper field, contour lines that describe the shape of the ground, a legend that names what the colours mean, and one course purple that belongs only to the active route. The report is read as a sequence of legs; each technology is a control description with a code, a name, a category, and the evidence count that lets a reader verify it.

The world stays out of the layout. Navigation, filters, inputs, tables, and drawers remain standard web controls. The map contributes four things only: the type voice, the palette, the density, and the course-line signature.

**Key Characteristics:**
- Cream paper ground with flat forest, contour, and course colours.
- One active route in purple; no glow, no glass, no gradient text.
- A route rail with nodes in the report; rows read as control descriptions.
- Authored contour lines only on the home surface, never as decorative card texture.
- No rounded cards, no lifted panels, no ambient shadow language.

## Colors

The palette is a map legend: forest for scanned ground, contour brown for structure, and one purple that means “you are here”.

### Primary
- **Course Purple** (`#6b3fa0`): active tab, route line, primary action, interactive focus, and the selected control. It is never used as a decorative wash.
- **Course Purple Deep** (`#522e7c`): primary-action hover only.

### Secondary
- **Forest Green** (`#4f6f3a`): scan and confirmed-evidence states; legend swatch for “扫描事实”.
- **Contour Brown** (`#9a6b43`): structure, report-proof legend, and authored contour strokes.

### Neutral
- **Paper Ground** (`#f3eedf`): page field in light mode.
- **Surface** (`#fbf7e9`): start control and elevated reading surface.
- **Ink** (`#2d2d27`): primary type.
- **Muted Ink** (`#5b5a4f`): supporting copy.
- **Boundary** (`#c8c0ad`): rules and table separators.
- **Night Ground** (`#171c16`) / **Night Surface** (`#1d241b`) / **Night Ink** (`#f1eddc`): the dark-mode translation of the same map.

### Named Rules
**The Purple Course Rule.** Purple is the active route. A screen may use it for the current leg, the primary action, and selection; never for a heading, a decorative rule, or an inactive icon.

**The Legend Rule.** Every colour that carries meaning must be explainable in the header legend or the control description. If a colour cannot be named, remove it.

## Typography

**Display Font:** RepoLens Map (self-hosted KaTeX Sans Serif; fallback Arial Narrow, PingFang SC)
**Body Font:** Segoe UI / PingFang SC / Microsoft YaHei
**Label/Mono Font:** Cascadia Code / JetBrains Mono

**Character:** A technical map face with narrow counters and a matter-of-fact voice, paired with a quiet UI sans. The display face is for terrain names and control headings; mono is reserved for coordinates, counts, and file data.

### Hierarchy
- **Display** (700, clamp 54–96px, 0.84): the home terrain name; never more than two lines.
- **Headline** (700, clamp 38–64px, 0.88): repository name on the report.
- **Title** (700, 18–23px, 1.05): control names and route-note groups.
- **Body** (400, 10.5–15px, 1.6–1.8): role descriptions and report prose; measure ≤74ch.
- **Label** (400, 7.5–9px, 0.08em, uppercase): legend, coordinates, counts, and metadata.

### Named Rules
**The Code Is Not a Kicker Rule.** Control codes (`C01`) and route numbers are coordinates in the data, not labels above headings. Do not add codes to a heading that has no coordinate in the product.

## Layout

The shell is a 1320px top bar over a 34px gutter; no permanent sidebar. Home is a 1160px terrain field with a two-part first viewport: headline and source start control on the left, three course legs below. Report is a 176px route rail plus a flexible reading column; the rail is sticky on desktop and becomes a five-column horizontal tab strip on mobile.

The spacing rhythm is 4/8/12/18/26/56px. Compact metadata is 8–10px; body copy is 10.5–15px; display is the only large type. Rows are separated by 1px rules, not backgrounds.

## Elevation & Depth

Flat by default. There are no drop shadows, glows, or glass surfaces. Depth is conveyed by the paper ground, one-pixel boundaries, type scale, and the single purple route line. The only hover state is a tonal wash at `--panel-soft`.

## Shapes

Everything is square: buttons, inputs, rows, tabs, drawers, and the start control use 0px radius. Circles appear only as course nodes and the map brand mark; they are route geometry, not chip decoration. Borders are 1px; no side stripes.

## Components

### Buttons
- **Shape:** square (0px).
- **Primary:** course purple, cream text, 10px 15px; reserved for “开始分析”.
- **Hover / Focus:** deep purple hover; visible purple focus outline; no transform or shadow.
- **Secondary / Ghost:** text-only actions in muted ink with underline on hover.

### Chips
- **Style:** flat category names with a small 5px colour square; active chip gets a 1px purple underline, not a filled pill.
- **State:** inactive muted, active purple, counts in mono at one step smaller.

### Control Rows / Containers
- **Corner Style:** 0px.
- **Background:** transparent; hover `--panel-soft`.
- **Border:** 1px bottom rule.
- **Internal Padding:** 13px 2px, increasing to 7px left inset on hover.
- **Signature:** `C01` code in purple mono, name in display face, role below, category and `1M / 2E` evidence count at the right, then a small arrow.

### Inputs / Fields
- **Style:** square, surface background, 1px boundary, mono value.
- **Focus:** 2px inset course-purple bottom rule.
- **Disabled:** 60% opacity; no colour change beyond that.

### Navigation
- **Desktop:** top bar with brand at left, text nav and theme at right, legend strip below; report route rail uses 9px nodes and a 1px purple course line.
- **Mobile:** the same top bar compresses; legend scrolls horizontally; report tabs become a five-column strip with purple active underline.

### Route Note (signature)
The report note is set in the display face at 20–27px over a 74ch measure, preceded by `ROUTE NOTE / 01`. Its highlights are muted lines each led by a purple em dash. It never becomes a card.

## Do's and Don'ts

### Do:
- **Do** keep purple for the active route and primary action only.
- **Do** use one-pixel rules, flat paper, and square geometry as the depth system.
- **Do** keep `C01` codes, `1M / 2E` counts, and legend swatches explainable.
- **Do** keep the authored contour lines on the home surface only.
- **Do** keep the mobile tab strip to five equal columns.

### Don't:
- **Don't** introduce rounded cards, glass, gradient text, or glow.
- **Don't** use purple as a decorative wash or inactive state.
- **Don't** turn route nodes into chip ornaments; they mark actual report legs.
- **Don't** add a second display face or a system display face.
- **Don't** replace the control rows with equal-sized card grids.
