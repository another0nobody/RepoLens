---
name: RepoLens Contact Sheet
description: A darkroom proof sheet where every technical claim is a frame with a source.
colors:
  darkroom-black: "#0b0b0a"
  frame-panel: "#1b1916"
  photo-white: "#f2eee2"
  silver: "#bdb7a9"
  grease-red: "#e04435"
  proof-paper: "#e9e5d8"
  proof-ink: "#171613"
typography:
  display:
    fontFamily: "RepoLens Grotesk, Arial Narrow, PingFang SC, sans-serif"
    fontSize: "96px"
    fontWeight: 500
    lineHeight: 0.93
    letterSpacing: "-0.045em"
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
    backgroundColor: "{colors.grease-red}"
    textColor: "#fff8ec"
    rounded: "{rounded.none}"
    padding: "11px 14px"
  button-primary-hover:
    backgroundColor: "#b83226"
    textColor: "#fff8ec"
    rounded: "{rounded.none}"
  source-roll:
    backgroundColor: "{colors.frame-panel}"
    textColor: "{colors.photo-white}"
    rounded: "{rounded.none}"
    padding: "12px"
  tab-active:
    backgroundColor: "#2a2722"
    textColor: "{colors.grease-red}"
    rounded: "{rounded.none}"
    padding: "10px 14px"
  tech-frame:
    backgroundColor: "{colors.frame-panel}"
    textColor: "{colors.photo-white}"
    rounded: "{rounded.none}"
    padding: "9px 10px"
---

# Design System: RepoLens Contact Sheet

## Overview

**Creative North Star: "The Proof Sheet"**

RepoLens is a darkroom where a repository is developed into evidence. The interface is a contact sheet: black ground, white frame borders, silver edge codes, and a single grease-pencil red that marks what can be pressed or what is currently selected. Every technology is a numbered frame; the agent's run is a strip of exposures; the report is the proof sheet you read after the roll is developed.

The world contributes type, palette, density, and one signature only. Navigation, filters, inputs, drawers, and tables remain standard web controls. The darkroom does not become a simulated terminal or a fake camera.

**Key Characteristics:**
- Flat darkroom black and photo-paper white with silver metadata.
- One grease red reserved for actions and active selection.
- Contact-sheet frames, edge codes, and numbered technology cards.
- Self-hosted compact geometric grotesque; typewriter for data.
- No glass, glow, gradient text, or rounded dashboard cards.

## Colors

A darkroom print: carbon black, paper white, silver-gray, and a single red grease pencil.

### Primary
- **Grease Red** (`#e04435`): primary action, active tab, selected frame, focus ring, and current-state marks.
- **Deep Grease** (`#b83226`): primary-action hover only.

### Secondary
- **Photo White** (`#f2eee2`): primary type and frame borders.
- **Silver** (`#bdb7a9`): secondary copy and metadata.

### Neutral
- **Darkroom Black** (`#0b0b0a`): page ground.
- **Frame Panel** (`#1b1916`): frame and source-card surfaces.
- **Proof Paper** (`#e9e5d8`): light-mode ground.
- **Proof Ink** (`#171613`): light-mode type.
- **Line** (`rgba(242, 238, 226, 0.18)`): frame rules.
- **Muted** (`#bdb7a9`) and **Faint** (`#8d877a`): secondary and metadata.

### Named Rules
**The Grease Pencil Rule.** Red is a mark, not a mood. Use it for the action, the active state, and the selected frame; never for a headline, an inactive icon, or a decorative wash.

**The Frame Rule.** Every panel is a rectangle with a 1px rule. No rounded card, no glass, no floating shadow.

## Typography

**Display Font:** RepoLens Grotesk (self-hosted Montserrat; fallback Arial Narrow, PingFang SC)
**Body Font:** Segoe UI / PingFang SC / Microsoft YaHei
**Label/Mono Font:** Cascadia Code / JetBrains Mono

**Character:** A compact geometric grotesque for names and codes, paired with a quiet UI sans and a typewriter for measurements. It reads like a lab label, not a terminal costume.

### Hierarchy
- **Display** (500, clamp 48–96px, 0.93): the home promise; maximum two lines.
- **Headline** (500, clamp 32–52px, 0.98): repository name.
- **Title** (500, 16–23px, 1.1): technology frame names and proof-note labels.
- **Body** (400, 10.5–15px, 1.6–1.8): role copy and report prose; measure ≤74ch.
- **Label** (400, 8–9px, 0.08–0.14em, uppercase): edge codes, frame numbers, counts.

### Named Rules
**The Edge-Code Rule.** Mono is reserved for data that behaves like a frame number, coordinate, version, or count. Do not set body copy in mono to signal “technical”.

## Layout

The shell is a 1320px top bar over a 1280px content field; no sidebar. Home is a two-column contact sheet: a large headline and source roll at left, a fixed three-frame proof strip at right. Report is a single reading column with a six-cell stat strip, a proof note, horizontal tab row, and a three-column frame grid that collapses to one at 820px.

The spacing rhythm is 4/8/12/18/26/56px. Compact metadata is 8–9px, body 10.5–15px, display up to 96px. Frames have 9–13px internal padding; section separation is carried by 26–38px.

## Elevation & Depth

Flat ink. There are no drop shadows, glows, or glass surfaces. Depth comes from the hard 1px frame border, the difference between black ground and photo-white type, and the red mark. Hover raises a frame only by border color and a one-step background tint.

## Shapes

Square by default. Buttons, inputs, frames, tabs, drawers, and the source roll use 0px radius. Circles appear only as small category dots and confidence dots; they are data markers, not decorative pills. Borders are 1px; no side stripes.

## Components

### Buttons
- **Shape:** square (0px).
- **Primary:** grease red, warm-white text, 11px 14px; used only for “开始分析”.
- **Hover / Focus:** deep red hover; visible red focus outline; no shadow, no lift.
- **Secondary / Text:** silent text actions with a red underline on hover.

### Chips
- **Style:** flat bordered chips; active chip uses a red border and red text, not a filled pill.
- **State:** inactive muted; active red; counts in mono.

### Cards / Frames
- **Corner Style:** 0px.
- **Background:** frame panel; hover one tonal step.
- **Border:** 1px line, 1px strong line on hover.
- **Internal Padding:** 9–13px.
- **Signature:** frame number `01`, category dot, display-size technology name, role, then counts and an arrow.

### Inputs / Fields
- **Style:** source field inside a framed roll card; transparent input, mono value.
- **Focus:** red border on the roll card; no glow.
- **Disabled:** button loses the red fill and uses the neutral line.

### Navigation
- **Desktop:** sticky top bar with an edge rail, wordmark, model status, history, knowledge, and theme.
- **Mobile:** edge rail reduces to two labels; nav labels collapse to icons; model status hides; the proof strip becomes a three-column row at 820px and a stacked list at 560px.

### Proof Strip (signature)
The home right column is a 3-frame proof strip: `01 SCAN`, `02 AGENT`, `03 PROOF`, each with a small abstract frame graphic, a title, and a one-line purpose. It is a sequence, not a decorative card stack.

## Do's and Don'ts

### Do:
- **Do** use red only for action, selection, and active state.
- **Do** keep every frame square and bordered at 1px.
- **Do** number frames and use mono for counts, versions, and edge codes.
- **Do** keep the proof strip horizontal at desktop and stack it at mobile.
- **Do** keep the report's stat row as six flat cells, never six cards.

### Don't:
- **Don't** introduce rounded cards, glass, glow, gradient text, or a colored left stripe.
- **Don't** use red for headings or inactive icons.
- **Don't** turn the contact sheet into a simulated camera or terminal.
- **Don't** add a second display face or a system display face.
- **Don't** replace the report table with a grid of equal cards.
