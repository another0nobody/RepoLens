---
name: RepoLens Type Index
description: A typographic index where technology names are specimens and evidence depth is a readable axis.
colors:
  paper: "#f2eee4"
  paper-surface: "#f8f4e9"
  specimen-ink: "#171410"
  vermilion: "#c8392c"
  warm-gray: "#5e574c"
  rule: "#c9c1b2"
  night-ground: "#141210"
  night-surface: "#1b1814"
  night-ink: "#f1ebdf"
typography:
  display:
    fontFamily: "RepoLens Specimen, Noto Serif SC, Songti SC, Georgia, serif"
    fontSize: "96px"
    fontWeight: 400
    lineHeight: 0.82
    letterSpacing: "-0.04em"
  body:
    fontFamily: "Segoe UI, PingFang SC, Microsoft YaHei, system-ui, sans-serif"
    fontSize: "13px"
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
  section: "62px"
components:
  button-primary:
    backgroundColor: "{colors.vermilion}"
    textColor: "#fff9ed"
    rounded: "{rounded.none}"
    padding: "11px 18px"
  button-primary-hover:
    backgroundColor: "#a52c21"
    textColor: "#fff9ed"
    rounded: "{rounded.none}"
  source-line:
    backgroundColor: "transparent"
    textColor: "{colors.specimen-ink}"
    rounded: "{rounded.none}"
    padding: "9px 0"
  tab-active:
    backgroundColor: "transparent"
    textColor: "{colors.vermilion}"
    rounded: "{rounded.none}"
    padding: "9px 0"
  depth-range:
    backgroundColor: "transparent"
    textColor: "{colors.vermilion}"
    rounded: "{rounded.none}"
    padding: "12px 0"
---

# Design System: RepoLens Type Index

## Overview

**Creative North Star: "The Specimen Index"**

RepoLens is a type specimen for a codebase. Technology names are set at specimen scale; the index is the navigation; the evidence depth axis is the reader's hand. The system uses warm paper, ink, and one vermilion foundry accent, then withholds ornament so the letterforms and the data carry the page.

The left rail is an index, not a decorative sidebar. The report is a two-column reading machine: an index of report legs and an evidence-depth axis on the left, a specimen field on the right. The axis is real: it hides or reveals role and module evidence, teaching the difference between a claim and its evidence.

**Key Characteristics:**
- Warm paper, ink, and one vermilion accent.
- Self-hosted display serif at specimen scale.
- Left index rail and vertical report legs.
- A real evidence-depth axis (name → role → modules).
- Flat rules, no cards, no glass, no gradient text.

## Colors

A printed specimen sheet: warm paper, black ink, one vermilion proof mark.

### Primary
- **Vermilion** (`#c8392c`): active state, primary action, emphasis rules, and the current depth label.
- **Vermilion Deep** (`#a52c21`): primary-action hover only.

### Secondary
- **Specimen Ink** (`#171410`): display type and body.
- **Warm Gray** (`#5e574c`): secondary copy.
- **Rule** (`#c9c1b2`): rules and index separators.

### Neutral
- **Paper** (`#f2eee4`): page ground.
- **Paper Surface** (`#f8f4e9`): drawers and raised input surfaces.
- **Night Ground** (`#141210`), **Night Surface** (`#1b1814`), **Night Ink** (`#f1ebdf`): dark-mode inversion.

### Named Rules
**The One Proof Mark Rule.** Vermilion is the proof mark: use it for the active leg, the live depth value, the primary action, and the selected state. Do not use it as a background wash.

**The Paper Rule.** Depth is a rule on paper. No drop shadows, no glass, no card elevation.

## Typography

**Display Font:** RepoLens Specimen (self-hosted KaTeX Main; fallback Noto Serif SC, Songti SC, Georgia)
**Body Font:** Segoe UI / PingFang SC / Microsoft YaHei
**Label/Mono Font:** Cascadia Code / JetBrains Mono

**Character:** A high-contrast bookish serif for Latin names, a Song-style CJK fallback, and a quiet UI sans. The pairing feels like a printed index rather than a product dashboard.

### Hierarchy
- **Display** (400, clamp 72–96px, 0.82): REPO / LENS only.
- **Headline** (400, clamp 38–62px, 0.9): repository name.
- **Title** (400, 17–23px, 1.05): technology names and index headings.
- **Body** (400, 11–13px, 1.6–1.8): roles, summaries, controls; measure ≤74ch.
- **Label** (400, 8–9px, 0.08em, uppercase): report codes, depth labels, counts.

### Named Rules
**The Specimen Scale Rule.** Latin display type may reach 96px; Chinese body copy never does. The contrast between display and 11–13px data is the hierarchy.

**The Depth Axis Rule.** The depth control is the only “view mode”. Its three named stops are NAME, ROLE, MODULES; do not replace it with a filter or a card toggle.

## Layout

The shell is a fixed 212px left index rail over a flexible content field. Home is a two-column specimen: REPO / LENS, a Chinese subtitle, and a 48ch lede at left; a three-entry index at right. The source field is a full-width ruled line below.

Report is a 178px sticky index column plus a reading column. The report index holds five numbered legs and the evidence-depth axis. The five legs become a five-column strip at 820px; the index note disappears. Tech entries are full-width rows, not a card grid.

## Elevation & Depth

Flat printed matter. There are no shadows, glows, or glass. Depth is conveyed by paper tone, 1px rules, type scale, and the vermilion proof mark. The only animated transition is a short fade-up on a tab panel and a tonal hover on tech rows.

## Shapes

Everything is square (0px): buttons, inputs, tabs, rows, drawers, and depth control. The only circles are the range thumb and the brand’s small “RL” square is rectangular; no pill-shaped chips. Rules are 1px; no side stripes.

## Components

### Buttons
- **Shape:** square (0px).
- **Primary:** vermilion, warm-white text, 11px 18px; single action “开始分析”.
- **Hover / Focus:** deep vermilion; visible vermilion outline; no lift.
- **Text actions:** 10px UI sans, underline on hover.

### Chips
- **Style:** category names as plain text with a count; active uses a vermilion bottom rule, no filled background.
- **State:** muted by default; active vermilion.

### Cards / Rows
- **Corner Style:** 0px.
- **Background:** transparent; hover `--panel-soft`.
- **Border:** 1px bottom rule.
- **Internal Padding:** 13px top/bottom; 7px left inset on hover.
- **Signature:** number, 23px display name, 11px role, category and module/evidence counts at the right.

### Inputs / Fields
- **Style:** transparent input on a 2px ink bottom rule; mono value.
- **Focus:** rule turns vermilion.
- **Disabled:** 60% opacity.

### Navigation
- **Desktop:** fixed 212px left rail with wordmark, numbered index links, model status, and theme toggle.
- **Mobile:** the rail becomes a sticky top strip; index numbers hide; report tabs become five equal columns.

### Evidence Depth (signature)
A native range input with three steps (`0 NAME`, `1 ROLE`, `2 MODULES`) and a live label. It controls the visible detail of every tech row: at NAME only the name/category/version remains; at ROLE the role line appears; at MODULES the counts and evidence appear. It is not persisted and has no hidden state.

## Do's and Don'ts

### Do:
- **Do** keep the specimen display at 96px maximum and body at 11–13px.
- **Do** use the depth axis as the only report view control.
- **Do** keep vermilion for proof marks and active states only.
- **Do** preserve the left index rail on desktop and the five-column tab strip on mobile.
- **Do** keep tech entries as rows with a 1px rule.

### Don't:
- **Don't** introduce cards, rounded containers, glass, glow, or gradient text.
- **Don't** turn the depth axis into a filter or a hidden setting.
- **Don't** set body copy in the display serif.
- **Don't** add a second accent or a second display face.
- **Don't** use the report index as a decorative sidebar with no controls.
