# ADR-003 – AI insight through the metric catalogue, not free text-to-SQL

- **Status:** Proposed · **Date:** 2026-11-05
- **Decision owner:** Architect proposes; Data Governance and Security approve
- **Related:** D3, D9, D12, D13 · assumptions A-15, A-16, A-17

## Context
The brief asks for an LLM-assisted insight grounded in approved metrics and access policies, with
unsupported or unauthorised answers prevented or flagged. Commercially sensitive measures must be
controlled; answers must be traceable; reviewers must reproduce results without an API key.

## Options

| Option | Grounding | Access control | Traceability | Risk |
|---|---|---|---|---|
| A. LLM writes SQL over the tables (text-to-SQL) | Weak – can invent joins and definitions | Must be enforced in the database only; prompt can try to bypass | SQL varies per run | Wrong numbers that look right; injection |
| B. LLM over a vendor semantic layer (e.g. Genie) | Good | Good | Good | Less control over refusal wording and audit format |
| **C. LLM produces a plan over the metric catalogue; deterministic guardrails, compiler and template answer** | Strong – only certified metrics | Policy applied after planning; row filters forced | SQL, owner, freshness on every answer | Only catalogue questions answerable (by design) |

## Decision
**Option C.** The planner (offline rules by default; Claude optional) turns a question into a
`QueryPlan` and **never writes SQL or sees data**. The plan is re-validated by the metric compiler;
the access policy checks sensitivity and forces the role's row scope; SQL comes only from the compiler
with bound parameters; the answer text is a template over the result rows; every request is audited.

## Consequences
- **+** A misbehaving or manipulated planner cannot reach forbidden data (proven by malicious-planner tests).
- **+** Same definitions as BI and the forecast; every answer shows its SQL, owner and data freshness.
- **+** Reproducible offline; provider can change without changing safety.
- **−** Questions outside the catalogue are refused rather than approximated – the catalogue must grow with demand.
- **−** The rules planner understands fewer phrasings than an LLM; the golden set grows with real questions.

## Validation needed before production
1. Test the LLM planner against the golden set (≥ the offline planner's pass rate) with an enterprise endpoint.
2. Red-team session (prompt injection, data exfiltration, role escalation) with Security.
3. Pilot with one business unit: measure answer accuracy, refusal rate and user feedback.
4. Map roles to real SSO groups and UC row filters (A-15).
