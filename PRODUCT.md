# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Existing Vue 3 + Vite + Less frontend, Python standard-library HTTP server + SSE, and LangChain/LangGraph agent backend. The redesign must keep the existing build/deploy path: `npm run build` produces `static/dist`, and `python run.py` serves it without Node.

## Users

- **Primary:** developers and learners who are opening an unfamiliar repository and need to understand its stack, structure, and reading order without reading every file first.
- **Secondary:** maintainers returning to a repository to look up a technology, module, risk, or previous report.
- **Tertiary:** people demonstrating RepoLens to others, where the interface itself must explain the product's value quickly.

The confirmed redesign priority is **faster comprehension of the technical stack and report**, with a **more distinctive, memorable product identity** than a generic AI-tool dashboard.

## Product Purpose

RepoLens accepts a local repository path or a public GitHub URL, scans it read-only, and produces a traceable Chinese technical-stack report: which technologies are used, where each is used (file and line), how the project is layered, what risks exist, and how to start reading it. The report can be interrogated through a grounded follow-up agent, including technology deep dives.

Success means a user can move from “I know nothing about this repository” to “I know its main technologies, where they live, and what to read next” without being misled by unverified AI claims or a wall of undifferentiated cards.

## Positioning

RepoLens is not a dependency-list viewer and not a free-form code chatbot. Its mechanism is **scan facts first, then AI interpretation**: the scanner produces deterministic evidence (manifests, imports, file/line modules, confidence), the agent interprets it, and the interface keeps the evidence inspectable. A neighboring product could copy a chat box; it could not truthfully copy the report's evidence trail without building the same scanner-and-agent pipeline.

## Operating Context

- Runs locally on the user's machine at `127.0.0.1`, with no login or multi-tenant account.
- The user may start from a local path, one of the bundled examples, or a public GitHub URL.
- GitHub analysis pauses for an explicit human approval before cloning.
- Analysis can take seconds to minutes; progress, tools, todos, and token usage stream live.
- Reports are saved locally as JSON and can be reopened, exported, or shared by run id.
- The interface is used for both scanning a new repository and returning to an existing report.

## Capabilities and Constraints

Confirmed must-preserve constraints from the product owner:

- All existing functionality and API contracts: local/GitHub analysis, streaming run page, report tabs, module map, architecture, follow-up chat and technology deep dive, history, export, share links.
- HITL clone approval, read-only scanning, sensitive-file rejection, secret masking, local-only default binding.
- Mobile usability at 390px and basic accessibility (keyboard reachability, visible focus, readable contrast).
- No fabricated claims, versions, benchmarks, or project motivations; the agent must distinguish report facts, general technical knowledge, and inference.

Technical constraints:

- The frontend must remain Vue 3 + Vite + Less and build to `static/dist`.
- The Python server, SSE event contract, report JSON shape, and API routes must continue to work.
- No Node runtime is available in production; committed build output is the shipped frontend.
- The product is Chinese-first and must keep accurate technical terminology.

## Brand Commitments

- Product name **RepoLens** and the “technical-stack detective” positioning.
- The existing lens/box mark and dark-first identity are current assets, not immutable constraints for a redesign; any replacement must remain recognizably RepoLens and retain the name.
- The interface should feel trustworthy and evidence-led, not like an ungrounded AI oracle.
- The product's voice is concise, concrete Chinese; avoid marketing hype and generic “AI magic” language.

## Evidence on Hand

- Working product code, API, scanner, agent, and report data model in this repository.
- Bundled demo repository at `examples/demo_shop`.
- Real screenshots in `docs/` for home, run, report, modules, architecture, chat deep dive, HITL, and six visual styles.
- Product documentation: `README.md`, `docs/REQUIREMENTS.md`, `docs/CODE_DOCUMENTATION.md`, `AGENTS.md`.
- No customer testimonials, commercial benchmarks, pricing, or deployment claims; these must not be invented.

## Product Principles

1. **Evidence before interpretation.** Every technical claim should be traceable to a file, line, manifest, or explicitly labeled inference.
2. **Progressive depth.** Give the answer first; expose evidence, modules, risks, and learning path as the user descends.
3. **A living investigation.** The run is not a spinner; show the agent's plan, tools, progress, and uncertainty as part of the product.
4. **Local-first trust.** Read-only, approval-gated network access, masked secrets, and a clear boundary around what leaves the machine.
5. **Teach while analyzing.** The interface should help a beginner understand both the repository and the Agent concepts behind the result.

## Accessibility & Inclusion

- Must remain usable at 390px width without horizontal page overflow.
- Interactive controls must be keyboard reachable with visible focus.
- Text/background contrast must meet a readable baseline in every shipped theme.
- HITL decisions must not rely on color alone and must require an explicit choice.
- Motion must remain subtle and must respect `prefers-reduced-motion`.
