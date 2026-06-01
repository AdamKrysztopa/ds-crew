# Reviewer Credibility Pass — Design Spec

**Date:** 2026-06-01
**Branch:** `fix/reviewer-credibility-pass`
**Status:** Approved (design), pending implementation plan

## Problem

ds-crew's stated thesis is *"never trust code just because it ran — measure."* An external
review found the repo violates that thesis in several places: it makes reliability and
cost claims it has never measured, ships long multi-agent skills whose control flow is only
guaranteed by prose, scatters hardcoded model IDs through routing logic, and has accumulated
14 skills with real overlap. This spec addresses all 12 review items in one phased branch.

**Guiding rule:** every change either makes an unverified claim falsifiable, or stops the
repo asserting something it has not measured. Where a "fix" would itself be theater (item #3),
we say so in writing rather than build a fake.

## Decisions (locked during brainstorming)

1. **Benchmark execution (#1):** Build the full harness + smoke-validate on 2–3 questions
   only. The full 257×3 run is documented as a budgeted operator command, not executed in
   this branch. README stays "not yet benchmarked" until an operator runs it.
2. **Skill sprawl (#7):** Split the README/USAGE surface into an explicit "core 5 / advanced 9"
   grouping. No skill behavior changes, no skill deletions, no moved references.
3. **Loop driver (#3):** Do **not** build a process that claims to enforce Claude's reasoning
   loop — a Python process cannot execute or gate the model's reasoning. Instead ship a
   lightweight run-log schema + validator and an explicit written statement of what prose
   cannot guarantee. Honesty over enforcement theater.
4. **Scope:** All 12 items, one branch, one phased plan, deliverable order A→B→C→D→E.
5. **Upstream scorer (#1):** Vendor InfiAgent-DAEval's deterministic scorer into `benchmarks/`
   with attribution, so CI/smoke does not depend on a live network clone.

## Pre-verified facts (read off the repo, not assumed)

- `LICENSE` already exists (MIT, 2026) → item #9 is satisfied; verify only.
- `.github/workflows/ci.yml` already runs: all `test_*.py` unittest suites, `lint_frontmatter.py`,
  and `validate_manifests.py` → items #8/#10 are **extensions**, not new builds.
- No `CHANGELOG.md` and no git tags yet → item #11 is real work.
- `docs/` has `datasets.md`, `demo.md`, `profiles.md` → #12 quickstart partly overlaps `demo.md`;
  needs a genuine one-dataset / one-command / expected-output doc.
- `package.json` is at `1.3.0`.
- Model IDs are hardcoded in: `skills/ds-star-plus/references/model_routing.md`,
  `skills/ds-star-plus/references/prompts.md`, `skills/ds-star-plus/scripts/route_model.py`,
  `skills/ds-star-plus/scripts/run_manifest.py`, `skills/ds-spike/references/personas.md`.
- `ds-search` explicitly reuses `ds-star-plus/scripts/verify_schema.py` + `references/rubric.md`
  → concretely confirms the #4 verifier-as-reward circularity.
- The "~3.5×" figure is the **paper's** number (DS-STAR vs ReAct input tokens, Table 6:
  154,669 vs 44,691 — i.e. DS-STAR is 3.5× *more* expensive). `ds-star-plus/SKILL.md` reframes
  it as overhead the digest caching "cuts" — that *reduction* is the unmeasured claim, not the
  paper figure itself.

## Known unknowns (resolve during implementation; do not assume)

- **DABench / InfiAgent-DAEval field names** — read off the actual downloaded data files.
- **Exact upstream scorer module path / entry point** — read off the actual cloned repo before
  vendoring. Vendor the real scorer; do not reimplement it.

---

## Phase A — Kill the contradiction (#2)

**Goal:** remove any wording implying *measured* v2 superiority.

- Sweep `README.md`, `ARCHITECTURE.md`, `ROADMAP.md`, `skills/ds-star-plus/SKILL.md`, and
  `docs/STATUS.md` for claims of measured superiority, "cheaper," "faster," "better,"
  "outperforms," etc.
- Replace with the canonical line: *"v2 changes are design extensions grounded in the DS-STAR
  paper, not yet independently benchmarked."*
- Paper figures (3.5× Table 6, Table 4 ablations, Table 2 retrieval gap) remain, **explicitly
  attributed to the paper**, never presented as ds-crew's own results.

**Done when:** no doc asserts a ds-crew-measured comparative result; all retained numbers carry
a paper citation.

## Phase B — Benchmark harness (#1)

**Goal:** a genuinely runnable harness that converts the reliability claim into evidence.

**Layout (repo top level — a dev tool, not shipped with the plugin):**
```
benchmarks/
  data/            DABench / InfiAgent-DAEval questions + datasets (fetched)
  runner.py        drives ds-star, ds-star-plus, ds-spike per question×variant
  score.py         vendored upstream deterministic scorer + thin wrapper
  report.py        results.jsonl → summary.md + manifest.json
  runs/            output dir (gitignored except a committed smoke run)
  prices.json      model → (input $/Mtok, output $/Mtok); shared with #6
  README.md        how to run, budget warning, operator command for full 257×3
```

**`score.py`:** vendor InfiAgent-DAEval's deterministic regex/format scorer (with attribution).
Format-parse failure counts as **WRONG**, never excluded. No hand-rolled comparison logic.

**`runner.py`:** a `Solver` interface with a headless `claude -p` adapter per variant. Per
question×variant it records: `correct`, `input_tokens`, `output_tokens`, `cost_usd`,
`wall_time_s`, `rounds`. **ds-spike cost SUMS all N parallel sub-runs.** Writes `results.jsonl`
(one row per question×variant).

**`report.py`:** emits `summary.md` with the table
`variant | n | accuracy | accuracy-hard | $/task | tokens/task | median rounds`,
and `manifest.json` with `{commit_sha, model_ids, prices, date, N, seed}`.

**This branch:** build everything; smoke-validate end-to-end on a **2–3 question** subset and
commit that smoke run under `runs/`. Document the full run as a budgeted operator command in
`benchmarks/README.md`. Do **not** execute the full paid run here.

**Done when:** `python benchmarks/runner.py` over the smoke subset produces valid
`results.jsonl`, `summary.md`, `manifest.json`; scorer is the vendored upstream one;
format-parse failures score WRONG; ds-spike cost is summed across sub-runs.

## Phase C — Reliability honesty (#3, #4, #5)

- **#4 (do):** Add an explicit "verifier-as-reward circularity" note to `skills/ds-spike/SKILL.md`
  and `skills/ds-search/SKILL.md`: both score with the same A1-rubric verifier they use
  internally, so a biased judge is amplified, not caught. **Enforce:** the meta-aggregator MUST
  use a different model/instance than the in-solver verifier. State this requirement in both
  SKILL.md files.
- **#5 (do):** Soften/remove the unmeasured "cuts ~3.5× overhead" *reduction* claim until #1
  yields a number. Keep the paper's 3.5× as an attributed paper figure (see Phase A).
- **#3 (honest skip):** Do not build a loop-enforcement driver. Instead:
  - Define a small structured **run-log schema** (round count, per-round verifier verdict,
    oscillation flag, and for ds-spike the N sub-run cost sum) and a validator that checks a
    produced log has the required fields.
  - Rewrite the relevant `ds-spike` / `ds-conduct` prose to emit that log.
  - Add an explicit written statement in both SKILLs: a Python process cannot guarantee the
    model followed the loop; the log makes deviations *detectable after the fact*, not
    *impossible*. This is the honest boundary.

**Done when:** both SKILLs document the circularity + different-instance requirement; the 3.5×
reduction claim is gone or paper-attributed; the run-log validator exists with a unit test and
the SKILLs state its limitation plainly.

## Phase D — Structure (#6, #7, #8)

- **#6:** Create one `config/models.json` as the single source of truth mapping
  `alias → model_id → (input_price, output_price)`. Refactor `route_model.py` and
  `run_manifest.py` to read from it; update doc tables to reference aliases. `prices.json`
  (Phase B) is generated from / lives alongside this config — one price list, not two.
- **#7 (split README surface):** Restructure the README "fourteen skills" section and
  `docs/USAGE.md` into an explicit **Core 5 / Advanced 9** grouping. Pure docs; no skill
  behavior change, no deletions.
- **#8:** Add a smoke test (new `test_*.py` picked up by existing CI) asserting that every
  `references/` and `scripts/` path *named inside* each SKILL.md resolves on disk. Frontmatter
  validity is already covered by `lint_frontmatter.py`.

**Done when:** no model ID is hardcoded outside `config/models.json` (routing logic + manifest
read from it); README/USAGE show Core 5 / Advanced 9; the path-resolution smoke test passes and
fails loudly on a deliberately broken reference.

## Phase E — Hygiene (#9–#12)

- **#9:** Verify `LICENSE` is present and adequate (already MIT) — no new file unless missing.
- **#10:** Extend `.github/workflows/ci.yml` to also run the Phase D #8 smoke test.
- **#11:** Add `CHANGELOG.md` (Keep-a-Changelog style) covering the history up to this pass; tag
  a release after merge.
- **#12:** Add a quickstart: one small bundled sample dataset, one command, and the expected
  output, wired into the README's top.

**Done when:** CI runs the smoke test; `CHANGELOG.md` exists and is current; a quickstart with a
real dataset + command + expected output is reproducible from a clean checkout.

---

## Testing strategy

- **Unit tests** for every new Python module (`score.py` wrapper, run-log validator,
  `models.json` loader, path-resolution smoke test, any `runner.py` pure helpers). TDD where
  practical.
- **Smoke run** committed for the benchmark harness (2–3 questions) proving the pipeline
  end-to-end.
- **CI** runs all unittest suites + frontmatter lint + manifest validation + the new path
  smoke test on every PR.
- **Negative tests:** the path smoke test must fail on a broken reference; the scorer must mark
  a format-parse failure as WRONG.

## Risks & mitigations

- **DABench field names / scorer path unknown** → resolve by reading the actual cloned
  repo/data before coding `score.py`; vendor the real scorer, never reimplement.
- **Headless `claude -p` adapter cost** → smoke subset only in this branch; explicit budget
  warning + operator command for the full run.
- **#7 README reorg drifting into behavior change** → constrain to docs files only; no edits
  under `skills/*/SKILL.md` control flow for #7.
- **#6 refactor breaking routing** → keep `route_model.py`'s public `pick_model()` signature
  unchanged; only its internal source of IDs moves to `config/models.json`.

## Out of scope

- Executing the full paid 257×3 benchmark run (operator step, post-merge).
- Deleting or merging any skill (only README surface is regrouped, per #7 decision).
- Any new top-level skill.
