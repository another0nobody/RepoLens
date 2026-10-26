# RepoLens redesign directions

Mechanism in one sentence: **the scanner establishes evidence, the agent interprets it, and the interface keeps the evidence inspectable.**
Audience scene: a developer opens an unfamiliar repository and needs a trustworthy map of its stack, structure, and reading order before touching code.
Cultural home: **field research, archives, and evidence documentation** — the places where observations become a record someone else can check.
First surface must prove: **the agent is working, and RepoLens has a character you can recognize without reading a headline.**
Category rut: dark glassy AI dashboard with a glowing orb, six equal stat cards, and a chat box. Predictable opposite: light minimal SaaS with a giant marketing hero and a card grid. Both stay out.

## Seven grounded directions, ordered by resonance

1. **Court exhibit binder.** A physical evidence file with exhibit tabs, Bates numbers, stamps, and redaction bars. Why: the product's promise is trust and chain of custody. Looks: manila and oxblood on ink-black, legal serif + typewriter labels; signature: every claim gets an exhibit tab and a custody line.
2. **Architectural condition survey.** Measured drawings, section cuts, north arrows, annotation leaders. Why: a repository is a structure with layers and defects. Looks: drafting paper, graphite, oxide red, technical grotesque + italic annotations; signature: a section line that cuts from conclusion to evidence.
3. **Observatory photographic plate archive.** Glass plates, coordinate grids, paper sleeves, typed object labels. Why: the agent is an instrument recording a faint object; evidence is the plate. Looks: deep blue-black, bone, amber; archival sans + mono; signature: coordinates crosshair a file and line.
4. **Library finding aid.** Collection boxes, scope notes, folder lists, call numbers. Why: a report is a finding aid for a code collection. Looks: cream, ink, forest green, bookish serif + sans; signature: a call-number spine that organizes technologies.
5. **Museum registration file.** Object labels, accession numbers, condition diagrams, check marks. Why: technologies are accessioned objects with provenance and condition. Looks: stone gray, ultramarine, safety orange; signature: a condition gauge on each technology.
6. **Naturalist field notebook.** Grid paper, specimen labels, collection numbers, pressed samples. Why: field observation is close to scanning a repository. Looks: moss, sepia, graphite; signature: a specimen label mount with provenance.
7. **Contact sheet / darkroom archive.** A 35mm proof sheet with frame numbers, edge codes, grease-pencil selects, and white frames on black. Why: the run is a series of exposures; the agent's steps and evidence are frames you can inspect. Looks: black ground, photo white, silver-gray, one grease red; condensed grotesque + typewriter; signature: a proof sheet of agent frames and technology frames.

**Assigned direction: #7, Contact Sheet.** It is the most lateral grounded direction and directly serves the confirmed first proof: “Agent 在工作”.

## Challenger verdicts (before borrowing)

1. **Warm consumer app surface** — declined. Reads as a consumer utility, not a developer’s evidence tool; donation to the assigned direction: reserve the saturated color strictly for actions, and keep comfortable touch targets.
2. **Doujin event catalog / newsprint** — declined. The packed postage-stamp grid fails 390px readability and would make evidence feel like a novelty; donation: numbered frames and density courage in the contact strip.
3. **Orienteering map** — competitive. Holds distinctiveness and gives report reading a real route; becomes **branch 3**.
4. **Cassette J-card** — declined. The folded physical topology would force the app into a paper artifact; donation: a hard A/B split between run and report.
5. **Zoo and gardens guide map** — declined. The lobe/coastline topology would obscure standard tables and evidence at narrow widths; donation: flat, unmodulated color and absolute confidence in the palette.
6. **Variable-font specimen** — competitive. Holds distinctive typography and a live axis interaction that can become a real evidence-depth control; becomes **branch 2**.

## Three branches

- `design/contact-sheet` — assigned #7. Darkroom proof sheet; dark, silver, grease red; run and evidence as frames.
- `design/type-index` — challenger #6. Type specimen; paper, ink, vermilion; report as an index + specimen with an evidence-depth axis.
- `design/field-map` — challenger #3. Orienteering map; cream, olive, contour brown, course purple; report as a route with legs and controls.

Each branch is a complete world and may change information architecture and report reading. All functionality, API contracts, HITL, read-only safety, 390px layout, and keyboard access must remain.
