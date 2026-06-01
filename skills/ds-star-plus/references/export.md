# Report export — Markdown and HTML (Phase 3)

At FINALIZE, the solver can produce a portable report alongside the run manifest.
No bundled library needed — the solver's own code writes the file (Principle 1).

## Markdown report

The solver writes a `.md` file to the run dir with:
- The question and key assumptions
- The answer + supporting evidence (tables, numbers)
- The verifier verdict summary
- Caveats and scope decisions made

## Optional HTML rendering

For a self-contained HTML report, the solver's code can use this minimal template
(stdlib only — no Jinja2, no markdown library bundled):

```python
import markdown_text  # or just format the HTML directly

def md_to_html(title, md_body):
    # Minimal HTML wrapper — no external lib needed for simple reports
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>{title}</title>
<style>body{{font-family:sans-serif;max-width:800px;margin:2em auto;}}
pre{{background:#f4f4f4;padding:1em;overflow-x:auto;}}</style>
</head><body>
<h1>{title}</h1>
<pre>{md_body}</pre>
</body></html>"""
```

Or, if `markdown` (the Python package) is available in the project env:
```python
import markdown
html = markdown.markdown(md_body, extensions=["tables"])
```
Either works — ds-crew itself has no opinion on which.

## Explicitly skip

- **Notion export** — thin payoff, rabbit hole; not supported.
- **Cloud storage** — out of scope.
- **PDF rendering** — use the HTML report + browser print if a PDF is needed.
