# Sandbox execution policy and provenance

## Resource policy

- Default wall-clock timeout: 30s per script execution (configurable via `timeout` param)
- Memory: no hard ceiling by default; scripts should avoid loading more data than needed
- Network: disabled for solver code by default — analysis scripts must be self-contained; external fetches require explicit user opt-in

## Working directory discipline

- Each run executes in a dedicated temp directory (`tempfile.mkdtemp()`)
- Scripts MUST NOT write outside their temp dir; read input files as read-only
- The temp dir is the only place output files, result CSVs, and plots should land
- Clean up temp dirs after use (or let the OS do it on reboot) — never accumulate in /tmp

## Provenance

- At FINALIZE stage, call `run_manifest.write_manifest(build_manifest(...), run_dir)` to emit `run_manifest.json`
- The manifest records: question, input file list, SHA-256 of the final code, the answer, verifier verdict, model used, and UTC timestamp
- Script: `scripts/run_manifest.py` — `from run_manifest import build_manifest, write_manifest`
- Reproducibility guarantee: re-running the same code on the same inputs must produce the same answer

## What to surface to the user

- At end of run: print the manifest path and `code_sha256` so the user can reproduce or audit
- Format: `[manifest] <path>/run_manifest.json  sha256=<hash>`
