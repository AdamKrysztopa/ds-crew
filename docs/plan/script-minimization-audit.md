# Script-minimization audit — existing bundled scripts vs Philosophy B

**Branch:** `chore/script-minimization-audit` · **Status:** audit/triage only — no script changed here.

Follow-up to `missing-patterns.md`. The three new patterns shipped as prose + JSONL (zero code).
This audits the **existing** bundled scripts against the same standing rule, so the suite is
consistent rather than philosophically split.

## The test (Philosophy B)

The question is **not** "is it Python?" but:

1. **Does the *user's analysis* have to call it — does it run in the user's runtime, against the
   user's data?** If yes, a bundled `.py` imposes Python on a data scientist who may work in R,
   Julia, JS, SQL, or Rust → it should be a **prose protocol** Claude executes in *their* language,
   with the script kept only as an *optional, clearly-labelled* reference implementation.
2. **Is it judgment or deterministic mechanics?** Judgment (matching, ranking, clustering,
   distillation) → prose. Mechanics on *Claude's own* artifacts that the user never sees (a JSONL
   store, a verdict parser, model-tier routing) → fine to keep as optional internal plumbing; the
   **data format / protocol is the contract**, the script is a convenience.

**Out of scope:** repo tooling under `.github/workflows/scripts/`, `scripts/`, `benchmarks/`,
`config/`. These run in **CI / maintainer workflows**, never in a user's analysis, so they impose
nothing on the user. Leave them as-is.

## Triage of the 12 bundled skill scripts

### Tier A — touches the user's data/runtime → lead with prose (3 scripts)

These are the *only* real "imposes Python on the user" surface. Recommend: make the SKILL protocol
**prose-first**, keep the script as an optional Python reference impl labelled as such.

| Script | Why it's Tier A | Recommendation |
|---|---|---|
| `ds-star-plus/scripts/analyze_file.py` **and** `ds-star/scripts/analyze_file.py` | Profiles the *user's* data file with pandas (shape, dtypes, head, low-card uniques). A user in R/Julia/SQL profiles differently. **Also duplicated across two skills.** | Prose-first digest protocol ("produce: shape, columns+dtypes, sheet/table names, low-card value lists, candidate keys — in your project's language"). Consolidate the duplicate to one optional reference impl, cross-referenced. |
| `ds-star-plus/scripts/kernel_runner.py` | Executes the user's analysis code in a persistent **IPython** kernel. Wrong runtime if the project is R/Julia/Rust. | Prose-first execution protocol ("run each step in the user's runtime; keep state across steps"). Keep the Python kernel as an optional convenience for Python projects. |
| `data-profile/scripts/detect_pii.py` | Heuristic scan over the *user's* column names + sample values. Runs on user data; also judgment-flavoured. | Prose-first scan protocol ("flag columns whose names/values look like PII: emails, SSNs, card numbers, …"). Keep the regex script as an optional convenience. |

### Tier B — internal plumbing, never on the user's analysis path → keep as optional (6 scripts)

Deterministic mechanics on **Claude's own** artifacts (stores, verdicts, run logs, routing). They
impose nothing on the user's analysis. Keep; the only change is a one-line label that the **format /
protocol is the contract and the script is an optional convenience**.

| Script | Role | Verdict |
|---|---|---|
| `ds-memory/scripts/memory_store.py` | Cross-session recipe/rules/experience JSONL store | Keep — already grandfathered in `missing-patterns.md`; JSONL schema is the contract |
| `ds-star-plus/scripts/verify_schema.py` | Parses Claude's *own* structured verifier verdict | Keep — deterministic parse of Claude output, not user data |
| `ds-star-plus/scripts/route_model.py` | Picks model tier per role | Keep — internal config logic |
| `ds-star-plus/scripts/run_manifest.py` | Writes a reproducibility manifest | Keep — internal bookkeeping |
| `ds-spike/scripts/runlog.py` | Spike run log | Keep — internal bookkeeping |
| `ds-spike/scripts/aggregate.py` | Clusters N solver answers → consensus (numeric tolerance) | Keep — the numeric-tolerance matching is genuinely better as code than prose; operates on solver outputs, not user data |
| `ds-model/scripts/leaderboard.py` | Tracks model/solution scores | Keep — internal bookkeeping |

### Tier C — scoped-by-design (1 script)

| Script | Note |
|---|---|
| `ds-env-setup/scripts/check_env.py` | `ds-env-setup` is **explicitly** a Python-environment skill (detects uv/venv/conda/poetry/pipenv). Not a Philosophy-B violation — it is language-specific *by definition*. Action: **label the skill's scope** ("Python projects") so it's honest, and optionally note sibling guidance for other ecosystems is out of scope. |

## Findings

- **The real surface is small.** Only **3** scripts (`analyze_file.py`, `kernel_runner.py`,
  `detect_pii.py`) actually touch the user's data/runtime. The suite is far less Python-locked than
  it first looked.
- **One concrete DRY bug:** `analyze_file.py` is duplicated in `ds-star` and `ds-star-plus`.
- **Tier B is fine.** None of it is on the user's analysis path; "no new code" for *new* patterns
  plus "keep existing plumbing" is a consistent position, not a contradiction.

## Suggested execution (each its own small, squash-merged PR — none done here)

1. **`analyze_file` → prose-first + de-dup.** Add a language-agnostic "produce this digest" protocol
   to the profiling step; consolidate the two copies into one optional reference impl.
2. **`kernel_runner` → prose-first execution protocol**, Python kernel kept as optional convenience.
3. **`detect_pii` → prose-first scan protocol**, regex script kept as optional convenience.
4. **Labelling pass (Tier B + C):** one line per script/skill stating "the protocol/format is the
   contract; this script is an optional convenience" and scoping `ds-env-setup` to Python projects.

Steps 1–4 are independent. Until then this document is the record so the language-agnostic principle
is applied consistently and the existing scripts are not mistaken for debt they aren't.
