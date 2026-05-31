# Multimodal input handling (Phase 3)

Claude's native vision and PDF support (Claude-native, Principle 0) means ds-star-plus
can handle PDFs-with-tables and image inputs without any additional library.

## Policy: native vision for PDFs and images

When an input file is a PDF or an image (PNG, JPG, etc.):

1. **At ANALYZE stage**, detect the file type by extension or MIME hint.
2. Use Claude's **native PDF reading** (the Read tool's built-in PDF support) or
   **native vision** to extract tabular content, figures, and text.
3. Record extracted tables as intermediate artifacts in the run dir (alongside
   the run manifest) — not in the conversation context.
4. Proceed with the extracted data exactly as with a CSV or JSON input.

## No extra dependency

Do **not** install `pdfplumber`, `camelot`, `pypdf`, or any other PDF/image library
as a ds-crew dependency (Principle 1). The solver's own code may use such libraries
*if they are already installed in the project env* — but ds-crew adds nothing.

## When native vision is enough

- Text-heavy PDFs with clearly bounded tables → native PDF read
- Charts/figures where the value is approximate → native vision
- Multi-page reports → read page by page, accumulate extracted tables

## When to recommend a library (in the solver's code)

If the user's env has `pdfplumber` or `pymupdf` and the PDF has complex table layouts,
the solver's generated code may use them. Surface this as a recommendation, not a
requirement: "for complex table layouts, `pdfplumber` would improve extraction accuracy
if it's available in your env."
