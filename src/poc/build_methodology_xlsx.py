"""Build methodology/Methodology.xlsx (Deliverable 3) from the CSV logs kept during the work, and render the
pod-plan table into docs/delivery/pod_plan.md from the same CSV.   Run: make methodology

Sheets (as required by the brief): Time Log, Tool Usage Summary, Decision Log, Pod Plan, Coaching Moments.
"""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

M = Path("methodology")
OUT = M / "Methodology.xlsx"
POD_MD = Path("docs/delivery/pod_plan.md")
REGISTER = Path("docs/corrections_register.md")
FROM_QUESTION = "AI, from Ashok's question"
CATS = ["planning", "modeling", "build", "testing", "documentation"]

HEAD_FILL = PatternFill("solid", fgColor="1F3A5F")
HEAD_FONT = Font(bold=True, color="FFFFFF")
TITLE_FONT = Font(bold=True, size=14, color="1F3A5F")
SUB_FONT = Font(bold=True, size=11, color="1F3A5F")
THIN = Side(style="thin", color="C9D1DB")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
WRAP = Alignment(wrap_text=True, vertical="top")


def read(name: str) -> list[dict]:
    with open(M / name, newline="") as f:
        return list(csv.DictReader(f))


def table(ws, top: int, headers: list[str], rows: list[list], widths: dict | None = None) -> int:
    for j, h in enumerate(headers, 1):
        c = ws.cell(row=top, column=j, value=h)
        c.fill, c.font, c.alignment, c.border = HEAD_FILL, HEAD_FONT, WRAP, BORDER
    for i, r in enumerate(rows, top + 1):
        for j, v in enumerate(r, 1):
            c = ws.cell(row=i, column=j, value=v)
            c.alignment, c.border = WRAP, BORDER
    for col, w in (widths or {}).items():
        ws.column_dimensions[col].width = w
    return top + len(rows) + 1


def sheet_from_csv(wb, title: str, rows: list[dict], headers: dict[str, str], widths: list[int]) -> None:
    ws = wb.create_sheet(title)
    data = [[r[k] for k in headers] for r in rows]
    for k, v in enumerate(data):
        data[k] = [int(x) if isinstance(x, str) and x.isdigit() else x for x in v]
    table(ws, 1, list(headers.values()), data, {get_column_letter(i + 1): w for i, w in enumerate(widths)})
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(headers))}{len(rows) + 1}"


def corrections_by_finder() -> Counter:
    c = Counter()
    for line in REGISTER.read_text().splitlines():
        if line.startswith("- **Found by:**"):
            who = line.split("**Found by:**")[1].strip()
            c[FROM_QUESTION if "from Ashok" in who else "Ashok" if who.startswith("**Ashok**")
              else "AI self-check"] += 1
    return c


def main() -> int:
    tl, alloc = read("time_log.csv"), read("time_allocation.csv")
    dec, coach, pod = read("decision_log.csv"), read("coaching_moments.csv"), read("pod_plan.csv")
    akey = {(a["block"], a["date"], a["start"]): a for a in alloc}
    for r in tl:
        a = akey.get((r["block"], r["date"], r["start"]))
        if a is None or sum(int(a[c]) for c in CATS) != int(r["duration_min"]):
            raise SystemExit(f"time_allocation.csv does not match time_log row {r['block']} {r['date']} {r['start']}")
        r.update({c: a[c] for c in CATS})

    wb = Workbook()
    wb.remove(wb.active)

    # 1 Time Log
    sheet_from_csv(wb, "Time Log", tl, {
        "block": "Block", "date": "Date", "start": "Start (IST)", "end": "End (IST)", "duration_min": "Duration (min)",
        "work_area": "Work area", "ai_tool": "AI tool", "generated_output": "Generated output",
        "verified_or_changed": "What was verified or changed (and by whom)",
        "planning": "Planning (min, est.)", "modeling": "Modelling (min, est.)", "build": "Build (min, est.)",
        "testing": "Testing (min, est.)", "documentation": "Documentation (min, est.)"},
        [7, 11, 9, 9, 10, 30, 24, 45, 70, 10, 10, 10, 10, 13])

    # 2 Tool Usage Summary
    ws = wb.create_sheet("Tool Usage Summary")
    ws["A1"], ws["A1"].font = "Tool usage summary", TITLE_FONT
    total = sum(int(r["duration_min"]) for r in tl)
    ws["A2"] = (f"Total logged time: {total} min ({total / 60:.1f} h) across {len(tl)} time blocks, "
                f"{len({r['block'] for r in tl})} work blocks. Category split is an estimate per time block "
                "(methodology/time_allocation.csv).")
    ws["A2"].alignment = WRAP
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = 32
    ws["A4"], ws["A4"].font = "Time by category", SUB_FONT
    split = [[c.capitalize() if c != "modeling" else "Modelling", sum(int(r[c]) for r in tl),
              f"{100 * sum(int(r[c]) for r in tl) / total:.0f}%"] for c in CATS]
    row = table(ws, 5, ["Category", "Minutes", "Share"], split + [["Total", total, "100%"]])
    ws.cell(row=row + 1, column=1, value="Time by block").font = SUB_FONT
    blocks = {}
    for r in tl:
        blocks.setdefault(r["block"], 0)
        blocks[r["block"]] += int(r["duration_min"])
    names = {"0": "Brief analysis and planning", "1": "Repo and decisions", "2": "Data pipeline",
             "3": "Metrics and forecast", "4": "AI assistant, Docker, CI", "5": "Architecture pack",
             "6": "Governance, delivery, methodology", "7": "Critical review", "8": "Video", "9": "Submission"}
    row = table(ws, row + 2, ["Block", "Content", "Minutes"], [[b, names.get(b, ""), m] for b, m in blocks.items()])

    ws.cell(row=row + 1, column=1, value="AI contribution").font = SUB_FONT
    finder = corrections_by_finder()
    contrib = [
        ["Tool", "Claude (Opus) in the Claude app, with a shell on the candidate's computer and a cloud renderer"],
        ["What the AI generated", "First drafts of nearly all code (generator, dbt models, metric compiler, forecast, "
         "assistant, tests, CI, Docker) and documents (explanations, models, architecture, ADRs, governance, delivery)"],
        ["What the candidate contributed", "Constraints (one-day timeline, no API key), stack and scope decisions, the "
         "explain-agree-build-verify-push gates, review questions that exposed gaps, approval of every push"],
        ["Corrections recorded", f"{sum(finder.values())} in docs/corrections_register.md - found by Ashok: {finder['Ashok']}; "
         f"by the AI from Ashok's questions: {finder[FROM_QUESTION]}; "
         f"AI self-checks inside the review process: {finder['AI self-check']}"],
        ["Coaching moments", f"{len(coach)} substantive overrides (Coaching Moments sheet)"],
        ["Decisions where the AI's first suggestion was changed",
         f"{sum(1 for d in dec if d['ai_suggestion'].strip().lower() != 'same as chosen')} of {len(dec)} (Decision Log sheet)"],
    ]
    row = table(ws, row + 2, ["Item", "Detail"], contrib)
    ws.cell(row=row + 1, column=1, value="Biggest useful output and most material miss").font = SUB_FONT
    table(ws, row + 2, ["", ""], [
        ["Biggest useful output", "The metric compiler + governed assistant design: one YAML definition of every "
         "measure used by the mart, the forecast and the AI, with guardrails proven by malicious-planner and "
         "mutation tests (Blocks 3-4)."],
        ["Most material miss", "C3 - the late-data rule ran before de-duplication: all 52 tests were green while "
         "167 harmless retries were quarantined as late, understating revenue. Caught only by profiling outputs. "
         "Runner-up: C8 - leakage tests that could not detect a leaked backtest."],
        ["Process miss", "C6 - the AI built and pushed a whole block before the candidate understood it; rolled back "
         "and replaced by explain-agree-build-verify-push gates."],
    ])
    ws.column_dimensions["A"].width, ws.column_dimensions["B"].width = 34, 110
    ws.column_dimensions["C"].width = 12

    # 3 Decision Log
    sheet_from_csv(wb, "Decision Log", dec, {
        "id": "ID", "business_requirement": "Business requirement", "options": "Options", "criteria": "Criteria",
        "chosen_design": "Chosen design", "ai_suggestion": "AI suggestion", "evidence": "Evidence",
        "trade_off": "Trade-off", "owner": "Owner"}, [6, 34, 34, 34, 40, 30, 40, 34, 26])

    # 4 Pod Plan
    sheet_from_csv(wb, "Pod Plan", pod, {
        "workstream_id": "ID", "workstream": "Workstream", "owner": "Owner",
        "adr_or_contract_owner": "ADR / contract owner", "dependencies": "Dependencies",
        "acceptance_criteria": "Acceptance criteria", "handoff_classification": "Handoff classification",
        "partner_teams": "Required partner teams"}, [6, 28, 26, 34, 30, 60, 28, 32])

    # 5 Coaching Moments
    sheet_from_csv(wb, "Coaching Moments", coach, {
        "id": "ID", "what_ai_proposed": "What AI proposed", "what_changed": "What changed",
        "why_it_mattered": "Why it mattered", "what_i_would_teach": "What I would teach an engineer"},
        [6, 40, 45, 50, 55])

    OUT.parent.mkdir(exist_ok=True)
    wb.save(OUT)

    # pod plan table in markdown, from the same CSV
    md = ["| ID | Workstream | Owner | ADR / contract owner | Dependencies | Acceptance criteria | Handoff | Partner teams |",
          "|---|---|---|---|---|---|---|---|"]
    md += ["| " + " | ".join(r[k].replace("|", "/") for k in ["workstream_id", "workstream", "owner", "adr_or_contract_owner",
           "dependencies", "acceptance_criteria", "handoff_classification", "partner_teams"]) + " |" for r in pod]
    text = POD_MD.read_text()
    text = re.sub(r"<!-- POD_PLAN_TABLE:START -->.*<!-- POD_PLAN_TABLE:END -->",
                  "<!-- POD_PLAN_TABLE:START -->\n" + "\n".join(md) + "\n<!-- POD_PLAN_TABLE:END -->", text, flags=re.S)
    POD_MD.write_text(text)
    print(f"Wrote {OUT} (Time Log {len(tl)}, Decision Log {len(dec)}, Pod Plan {len(pod)}, "
          f"Coaching Moments {len(coach)}; {total} min logged) and the pod-plan table in {POD_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
