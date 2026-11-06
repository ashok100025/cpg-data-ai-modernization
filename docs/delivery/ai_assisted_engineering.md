# AI-assisted engineering – what I would teach the pod

Brief: *"…what you would teach engineers about AI-generated design and code."* These practices come
from what actually happened while building this case study with an AI assistant. Each one cites the
real incident (coaching moments in `methodology/coaching_moments.csv`, corrections in
`docs/corrections_register.md`).

## The working agreement

> **AI drafts and builds at speed – inside gates the lead defines. A human understands and approves
> before anything is shared.**

`explain → agree → build locally → verify → push only on approval` ([C6](../../methodology/coaching_moments.csv), register #9). The AI built and
pushed a whole block before anyone understood it; it was rolled back and this rule set. The same rule
applies to a new engineer.

## Ten practices

| # | Practice | Real incident | How to apply it |
|---|---|---|---|
| 1 | **Feed the real constraints in first** – AI plans from the documents you give it | [C1](../../methodology/coaching_moments.csv): AI planned two weeks from the brief; the real ask was one day | Before any plan: deadline, budget, keys, access, who decides |
| 2 | **Never accept a version, API or flag from AI memory** | [C2](../../methodology/coaching_moments.csv): a pinned package version was withdrawn and broke the install | Install in a clean environment before pinning; read the changelog |
| 3 | **Green tests prove the rules you wrote, not that the rules are right** | [C3](../../methodology/coaching_moments.csv): 52 tests green, 167 harmless retries quarantined as late | Profile outputs (counts by reason, by batch) and ask "is this believable?" |
| 4 | **Prove a test can fail** – break the code on purpose | [C8](../../methodology/coaching_moments.csv): leakage tests passed a deliberately leaked backtest; #27: policy switched off → 5 tests failed (good) | Every new guardrail or rule ships with a mutation check |
| 5 | **Set thresholds from baselines and prove the alert fires** | [C5](../../methodology/coaching_moments.csv): a fixed 1% alert never fired on the real incident | Measure normal, set relative thresholds, replay a known-bad case |
| 6 | **Averages hide the tail** | [C9](../../methodology/coaching_moments.csv): 14.5% overall forecast error hid 30–64% on small series | Look at the distribution; tell consumers which numbers to trust |
| 7 | **Look at the artefact the audience will see** | [C10](../../methodology/coaching_moments.csv): diagram "rendered without errors" was unreadable | Open the picture, the page, the report – not the exit code |
| 8 | **Structured files deserve structured edits** | [C11](../../methodology/coaching_moments.csv), #30: regex edits broke SQL and YAML | Parse or edit by hand; re-run the parser or build immediately |
| 9 | **Know your parsers' and tools' quirks** | [C7](../../methodology/coaching_moments.csv): YAML read `on:` as `true`; Mermaid treats `;` as a statement end | Load and test configuration like code |
| 10 | **Immutable inputs, reproducible outputs** | [C4](../../methodology/coaching_moments.csv): demo mode rewrote landed history | Hash inputs before/after; assert incremental = full rebuild |

## How AI fits the pod's process

| Step | AI does | Engineer does |
|---|---|---|
| Design | Drafts options, ADR text, diagrams | Supplies constraints; chooses; owns the decision and the ADR |
| Code | Writes first drafts, tests, docs | Reviews every line like a colleague's PR; adds the failing case |
| Verification | Runs builds, profiles outputs, renders artefacts | Decides what "correct" means; checks the numbers make business sense |
| Sharing | Never pushes, never merges | Approves; commit message records what AI generated and what was changed |
| Learning | – | Logs each substantive override as a coaching moment; reviews them in retros |

## What to be honest about
- Record **who found what** (corrections register): AI self-checks are valuable *because* the process asked
  for them – claim the process, not the individual finds.
- Label AI co-authorship in commits; keep the time log real.
- An AI-written answer about the client's data must be grounded in certified metrics ([ADR-003](../adr/ADR-003-ai-grounding.md)) – the same
  standard applies to AI-written code about the client's data.
