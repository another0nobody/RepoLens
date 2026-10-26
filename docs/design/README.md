# RepoLens redesigns

Three independent branches, each a complete visual world and a different report-reading model. `main` keeps the current product and the existing six-style picker; these branches are design experiments, not merged.

| Branch | World | Report model | Screenshots |
| --- | --- | --- | --- |
| `design/contact-sheet` | Darkroom contact sheet: black, photo white, grease red, compact grotesque | Technologies as numbered proof frames; run as exposures | [home](contact-sheet/home-desktop.png) · [report](contact-sheet/report-desktop.png) |
| `design/type-index` | Warm paper type specimen: ink, vermilion, self-hosted serif | Left index + evidence-depth axis; technologies as specimen rows | [home](compare/type-home.png) · [report](compare/type-report.png) |
| `design/field-map` | Orienteering map: cream, forest, contour, course purple | Route rail with legs; technologies as control descriptions | [home](compare/field-home.png) · [report](compare/field-report.png) |

All three preserve the analysis pipeline, API contracts, HITL/security, history/export, module map, chat/deep dive, dark/light toggle, and 390px layout. The six-style picker is intentionally not part of these single-world experiments; it remains on `main`.
