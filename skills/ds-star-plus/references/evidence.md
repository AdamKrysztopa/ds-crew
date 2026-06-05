# Why each v2 change is justified — grounded in the paper

This file is the "explanation why" behind DS-STAR+. Every v2 deviation from the base method
is tied to a specific finding, table, or number in *DS-STAR* (Nam et al., 2025; arXiv
2509.21825v3). Read it alongside `../SKILL.md`. The rule we followed: **do not add machinery
the paper's own evidence does not ask for.**

Two numbers from the paper frame everything below:

- **Cost is real but bounded.** Table 6 (Appendix C): on DABStep with Gemini-2.5-Pro,
  DS-STAR averages **12.7 LLM calls, 154,669 input tokens, 3,373 output tokens, $0.23/task**
  vs ReAct's 7.1 calls / 44,691 input / $0.09. That is **3.46x ReAct's input tokens**, and the
  paper names the cause exactly: *"primarily because our method utilizes comprehensive analytic
  descriptions of each data file."*
- **Correctness is asymmetric and description-driven.** Table 4 ablation: removing the analyzer
  descriptions drops hard-level accuracy from **45.24% → 26.98%** (an 18-point fall). The file
  description is the single largest correctness lever in the whole method.

Those two facts pull in opposite directions — the descriptions are simultaneously the biggest
cost driver *and* the biggest correctness driver. Most of v2 is the resolution of that tension.

---

## 1. Per-role model-tier routing

**Paper baseline.** Everything runs on one model. *"Unless otherwise specified, all experiments
are conducted using Gemini-2.5-Pro"* (§4.1); the only model-swap experiment runs *all* roles on
GPT-5 (Table 4). The paper never routes per role — it is single-tier by construction.

**Evidence that the roles are not equally hard.**
- Table 4 ablation: only two of the seven roles move the needle decisively. Remove the
  **analyzer** → hard 45.24 → 26.98. Remove the **router** (Variant 2, add-only planning) →
  hard 45.24 → 39.95, easy 87.50 → 79.17. The other roles (coder, finalizer, debugger-trim)
  are never shown to need top-tier reasoning.
- Call-volume is lopsided. The analyzer fires **once per file** and is explicitly
  *"parallelized"* (§3.1, Algorithm 1 lines 3–6); on a 7-file DABStep task that is the highest
  call-count role, yet each call is a near-mechanical "describe this file" with *"almost no
  cross-file reasoning."*

**Why v2's response follows.** If roles differ in cognitive load (Table 4) and in call volume
(Algorithm 1), paying top-tier price uniformly is waste. Route by load: high-volume / low-
reasoning roles (analyzer, finalizer, trace-trim) to Haiku; step-level reasoning (planner,
router, coder) to Sonnet; and the one load-bearing judge to Opus. Escalate only on evidence so
no accuracy is sacrificed for the cost win. This directly attacks the $0.23 / 12.7-call profile
in Table 6 without touching the components Table 4 proved are critical.

## 2. Structured verifier (`reason` + `missing`) and self-consistency voting

**Paper baseline.** The verifier output is strictly binary: *"the output v is a binary variable:
sufficient or insufficient"* (§3.2; Algorithm 1 line 13). No rationale, no vote.

**Evidence the verifier is the failure-critical role.** The paper's entire thesis is that
*"executable code does not always guarantee a correct answer"* (§1) and that the verifier exists
precisely to catch the plausible-but-wrong result. The qualitative case in Figure 3 is a *silent*
wrong answer: ReAct assumes a column does not exist and reports a number anyway. A verifier that
says "sufficient" wrongly reproduces exactly that failure, and *nothing downstream catches it* —
the loop terminates on "sufficient" (Algorithm 1 lines 14–15).

**Why v2's response follows.** A false "insufficient" costs one more cheap round; a false
"sufficient" ends the run wrong and unrecoverable. That asymmetry justifies (a) pinning the
verifier to Opus, and (b) forcing it to *show its work*: the `reason` must tie the printed value
to the question's scope/units/format, which converts a silent yes/no into a checkable claim, and
`missing` gives the router/planner a real target instead of a guess. The paper itself blesses
self-consistency as the tool for high-stakes judgements — it lists *"self-consistency"* among the
techniques that harden multi-step pipelines in the Text-to-SQL related work (§2). v2 applies it
to the one decision that can silently end the run: **3× majority vote on borderline verdicts.**

**v2.1 extension (DeepVerifier, [2601.15808](https://arxiv.org/abs/2601.15808)).** DeepVerifier
shows the binary judge is the weak link and replaces it with a rubric-guided, *decomposed*
verifier: failures are pre-classified into a fixed taxonomy, verification is split into a few
targeted follow-up checks rather than one holistic call, and the verdict is graded. It beats a
vanilla LLM-judge by **12–48% F1**, lifting recall of catching wrong answers from **14% → 71%**
(their GAIA-Web ablation) — with no training and at modest cost (decomposition stays to ≤3 checks).
v2.1 ports this: a six-item DS-failure rubric (`references/rubric.md`), ≤3 decomposed `checks`, and
a graded 1–4 `score` where sufficiency requires `score == 4` with no rubric `fail`. The contract is
enforced by `scripts/verify_schema.py` so a malformed or over-optimistic verdict fails loudly.

## 3. Oscillation handling and the anti-repeat list

**Paper baseline.** On a wrong step, the router truncates and the planner *regenerates by random
sampling* rather than editing in place, because *"revising a specific incorrect step often leads
to an overly complex replacement, therefore frequently flagged again by the router in a next
iteration"* (§3.2). The paper establishes the truncate-and-resample behaviour but does **not**
address the failure mode where resampling returns a near-identical wrong step and the loop spins.

**Evidence the loop can spin.** The method runs to a hard cap of **20 rounds** (Algorithm 1
line 12; §4.1), and the sensitivity study (Fig 4b) shows accuracy still climbing as the cap rises
— i.e. some tasks are burning the full budget. Random resampling with no memory of what was
already rejected is exactly the process that wastes those rounds.

**Why v2's response follows.** Keep the paper's truncate-and-resample (it is empirically
justified), but give resampling a memory: an **anti-repeat list** of already-rejected step
descriptions so the planner must propose something materially different. If the same step index
is truncated twice, that is the paper's "flagged again next iteration" pathology made concrete —
escalate the planner/router to Opus and switch from one greedy sample to **2–3 candidate steps
with a verifier pick** (a light search, consistent with the resampling philosophy the paper
already endorses). This spends the 20-round budget on new strategies instead of re-derivations.

## 4. Schema-digest caching — compress the description, never delete it

**Paper baseline.** The full descriptions `{d_i}` are re-fed to the planner, coder, router, and
debugger on **every round** (Algorithm 1 lines 8, 9, 24, 26; §3.2–3.3). Appendix C names this
re-feeding as the reason for the 154,669-token input bill — 3.5x ReAct.

**The trap to avoid.** Table 4 is unambiguous: the descriptions are the biggest correctness lever
(remove them → hard 45.24 → 26.98). So the naive cost fix — "just send less data context" — would
walk straight into an 18-point accuracy cliff. The cost driver and the correctness driver are the
same object.

**Why v2's response follows.** Resolve the tension by *compressing, not removing*. Keep a compact
**schema digest** per file (name, columns + dtypes, sheet names, one-line note) and pass that by
default — enough for planning and routing, which the paper's own prompts use mainly to know *what
columns exist*. Send the **full verbose description only to the coder/debugger for the specific
file they touch**, which is exactly where Table 4's correctness signal is consumed. Cache both so
the analyzer runs once. This targets the precise token line item Appendix C blames, while leaving
the Table-4-critical signal intact at the point of use. The claim is "meaningful token savings
with no accuracy loss" — and it is falsifiable: if digests ever degrade a plan, the role asks for
the full description, which is the escalation path built into the prompts.

## 5. Two-stage retrieval for data lakes

**Paper baseline.** For N > 100 files the retriever takes *"top-K most relevant data files... by
computing the cosine similarity between the embedding of the user's query and each description"*
(§3.3); KramaBench uses top-100 via Gemini-Embedding-001 (§4.1).

**Evidence the single-stage retriever leaves accuracy on the table.** **DS-STAR's own Table 2**
(this paper, evaluated on KramaBench — *not* a KramaBench-paper table): with retrieval DS-STAR
scores **44.69 total**; in the relevant-files **oracle** setting (relevant files handed in) it
scores **52.55** — the paper states accuracy "increases by **8 percentage points**", a gap
attributable purely to retrieval misses. It concedes the lever directly: *"while our current
retrieval method is effective, advanced data discovery is a promising direction for unlocking the
full potential of DS-STAR."* The scale is real — KramaBench's Astronomy domain alone has **1,556
files**. (Note: KramaBench's *own* "oracle" setting is input-obfuscation, a different thing; the
44.69/52.55 retrieval-oracle numbers are DS-STAR's.)

**Why v2's response follows.** Pure embedding cosine misses files that are clearly on-topic by
name/columns but embed poorly against the query phrasing. v2 keeps the cheap embedding stage to get
from thousands of files down to a top-~150 candidate pool (Stage 1), adds a **cheap Haiku relevance
pass** (Stage 2), and — within that same pass — a **column-level / value-matching re-rank** (Stage 3:
column-name overlap, low-cardinality value containment, join-key reachability) with a **recall-biased
keep rule** (carry a file if it is strong on *either* the embedding or any structural signal). It is
a direct, low-cost attempt at the "advanced data discovery" the paper names as the lever for closing
that 8-point oracle gap. See `retrieval.md` for the operational protocol; it adds **no new tooling or
call** — the structural judgments fold into the existing Haiku pass.

## 6. Early-exit guardrail

**Paper evidence.** §4.3 / Fig 4a: easy tasks average **3.0 rounds** and **>50% are solved by the
initial plan p₀ alone**, while hard tasks average **5.6 rounds** and **98% need ≥1 refinement.**

**Why v2's response follows.** The distribution is bimodal: a large mass of one-shot-solvable easy
tasks and a long tail of genuinely iterative hard ones. Running the full verify/route loop on a
task the initial plan already answered is pure overhead against the Table 6 cost profile. v2 makes
the paper's implicit behaviour explicit: if the initial result cleanly answers the question and the
(now structured) verifier's `reason` ties output to the question with no `missing` items, finalize
in one round. The heavy loop is reserved for the 5.6-round tail where the paper shows it pays.

---

## What v2 deliberately did NOT change

Grounding cuts both ways — these are paper-validated and left alone:

- **Analyze-first.** Biggest correctness lever (Table 4). v2 compresses how it is *passed*, never
  whether it is *computed*.
- **Verify on real execution output, not plan text.** §3.2's grounding insight is the whole point;
  v2 only enriches the verdict's shape.
- **Truncate-and-regenerate over in-place edit.** §3.2's empirical finding; v2 adds memory around
  it, not a replacement for it.
- **20-round cap.** §4.1 default; Fig 4b shows more rounds help, so v2 keeps the cap and spends it
  more wisely rather than lowering it.
