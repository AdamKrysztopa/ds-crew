# Role prompts

Reuse these as the instruction for each step of the loop. Placeholders in `{braces}` get
filled at runtime. Keep them terse — each role does exactly one job.

## Analyzer (Stage 1)

> You are an expert data analyst. Generate Python code that loads and describes the content
> of `{filename}`.
>
> Requirements:
> - The file may be unstructured or structured.
> - If there is a lot of structured data, print only a few examples.
> - Print essential information — e.g. all column names (and sheet names for Excel).
> - The code should actually print the content of `{filename}`.
> - It must be a single-file, self-contained program runnable as-is.
> - Respond with a single code block only.
> - Do not invent dummy content; we will debug if an error occurs.
> - Do not use try/except to suppress errors — let them surface for debugging.

## Planner — initial step (Stage 2)

> You are an expert data analyst. To answer the question from the data, plan effectively.
>
> Question: `{question}`
> Given data and summaries: `{filenames + descriptions}`
>
> Task: propose your very first step. It need not be sufficient to answer the question —
> just a simple, runnable starting point. Respond with only that initial step.

## Planner — subsequent step (Stages 2/4)

> You are an expert data analyst. Suggest the next step to answer the question.
>
> Question: `{question}`
> Given data and summaries: `{filenames + descriptions}`
> Current plan: `{step 1 ... step k}`
> Results from running the current plan: `{result}`
>
> Task: propose a simple next step that moves toward the answer (it may, if only a final
> simple step remains, directly answer it). Respond with only the next step, no explanation.

## Coder — initial implementation (Stage 2)

> Given data and summaries: `{filenames + descriptions}`
> Plan: `{plan}`
>
> Implement the plan with the given data. Respond with a single Markdown Python code block,
> no extra headings or text.

## Coder — incremental implementation (Stage 4)

> You are an expert data analyst. Implement the next plan step using the given data.
>
> Given data and summaries: `{filenames + descriptions}`
> Base code (implements the previous steps): ```{base_code}```
> Previous plan: `{step 1 ... step k}`
> Current step to implement: `{step k+1}`
>
> Build on the base code. Respond with a single Markdown Python code block, no extra text.

## Verifier (Stage 3)

> You are an expert data analyst. Check whether the current plan and its implementation are
> enough to answer the question.
>
> Plan: `{step 1 ... step k}`
> Code: ```{code}```
> Execution result: `{result}`
> Question: `{question}`
>
> Answer 'Yes' if it is enough to answer the question, otherwise 'No'.

## Router (Stage 4)

> You are an expert data analyst. The current plan is insufficient; decide how to refine it.
>
> Question: `{question}`
> Given data and summaries: `{filenames + descriptions}`
> Current plan: `{step 1 ... step k}`
> Results from running the current plan: `{result}`
>
> - If one of the existing steps is wrong, answer with that step: `Step 1` ... `Step k`.
> - If a new next step should be added, answer `Add Step`.
> - Respond with only `Step 1`–`Step k` or `Add Step`.

## Finalizer (Stage 5)

> You are an expert data analyst. Using the files below and the reference code, write
> solution code that prints the answer in the required format.
>
> Given data and summaries: `{filenames + descriptions}`
> Reference code: ```{code}```
> Execution result of reference code: `{result}`
> Question: `{question}`
> Guidelines: `{guidelines}`  (e.g. round to 2 dp; exact JSON shape; match sample_result.csv
> column order; save to a named file)
>
> If the answer is already in the reference result, just print it in the desired format.
> Single self-contained file, single code block, no try/except, all files under `data/`.

## Debugger — trim traceback

> Error report: `{traceback}`
> Remove the unnecessary parts of this report but keep where the error occurred (we are
> running `{filename}.py`).

## Debugger — fix analyzer script (descriptions not yet available)

> Code with an error: ```{code}```
> Error: `{trimmed_traceback}`
> Revise the code to fix the error. Provide the improved self-contained script only — no
> extra text, no dummy content, no try/except.

## Debugger — fix solution script (use data context)

> Given data and summaries: `{filenames + descriptions}`
> Code with an error: ```{code}```
> Error: `{trimmed_traceback}`
> Revise the code to fix the error. You only have `{filenames}` available. Provide the
> improved self-contained script only — no extra text, no dummy content, no try/except,
> all files under `data/`.
