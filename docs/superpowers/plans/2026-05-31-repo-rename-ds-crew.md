# Repo + Plugin Rename → `ds-crew` Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename the *suite identifier* from `ds-star` / `ds-stats-with-claude` to **`ds-crew`** across the GitHub repo, the plugin manifest, the marketplace manifest, the npm package, the git remote, and the README install docs — so the bundle is named for the whole crew, not for one of its members.

**Architecture:** A pure rename. The GitHub repo is renamed first (so the new URL exists and GitHub redirects the old one), then the local remote is repointed, then the four name fields and five README install commands are updated, validated, committed, and pushed. Finally the marketplace is re-registered on the local machine.

**Tech Stack:** `gh` CLI (GitHub repo rename), `git` (remote), JSON manifests, Markdown.

---

## ⚠️ Rename scope — read before touching anything

**RENAME (the suite/plugin identifier only):**
- GitHub repo `ds-stats-with-claude` → `ds-crew`
- `.claude-plugin/plugin.json` `name` → `ds-crew`
- `.claude-plugin/marketplace.json` top-level `name` and `plugins[0].name` → `ds-crew`
- `package.json` `name` → `ds-crew`
- README install ids `ds-star@ds-star` → `ds-crew@ds-crew`, and `AdamKrysztopa/ds-stats-with-claude` → `AdamKrysztopa/ds-crew`

**DO NOT RENAME (these are different things that merely share the string "ds-star"):**
- the skill directory `skills/ds-star/` and its `/ds-star` invocation
- the skill `ds-star-plus` (`/ds-star-plus`)
- the method / paper name **DS-STAR** anywhere in prose
- any of the other skill names (`ds-clarify`, `ds-spike`, `data-profile`, `eda-narrative`)

The install id changes from `ds-star@ds-star` to **`ds-crew@ds-crew`**. Anyone who installed the
old id must `uninstall` + reinstall (this is a fresh personal repo, so impact is ~nil). GitHub
auto-redirects the old repo URL, so an old `marketplace add` still resolves — but docs move to the
new name.

---

## Task 1: Rename the GitHub repository

**Files:** none (remote operation)

- [ ] **Step 1: Confirm `gh` is authenticated**

Run:
```bash
gh auth status
```
Expected: shows logged in to github.com as the repo owner. If not, run `gh auth login` first.

- [ ] **Step 2: Rename the repo**

Run:
```bash
gh repo rename ds-crew --repo AdamKrysztopa/ds-stats-with-claude
```
Expected: `✓ Renamed repository AdamKrysztopa/ds-crew`. (GitHub keeps a redirect from the old name.)

- [ ] **Step 3: Verify**

Run:
```bash
gh repo view AdamKrysztopa/ds-crew --json name,url -q '.name + " " + .url'
```
Expected: `ds-crew https://github.com/AdamKrysztopa/ds-crew`.

---

## Task 2: Repoint the local git remote

**Files:** none (local git config)

- [ ] **Step 1: Update the origin URL**

Run:
```bash
git -C /Users/adamkrysztopa/projects/DS-STAR remote set-url origin git@github.com:AdamKrysztopa/ds-crew.git
```

- [ ] **Step 2: Verify it resolves**

Run:
```bash
git -C /Users/adamkrysztopa/projects/DS-STAR remote get-url origin
git -C /Users/adamkrysztopa/projects/DS-STAR ls-remote --heads origin >/dev/null && echo "REMOTE OK"
```
Expected: prints `git@github.com:AdamKrysztopa/ds-crew.git` then `REMOTE OK`.

---

## Task 3: Update the manifest and package name fields

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `package.json`

- [ ] **Step 1: plugin.json**

In `.claude-plugin/plugin.json`, find this EXACT text (the first line of the object):

```text
  "name": "ds-star",
  "version": "1.1.0",
```

Replace it with:

```text
  "name": "ds-crew",
  "version": "1.1.0",
```

- [ ] **Step 2: marketplace.json — top-level name**

In `.claude-plugin/marketplace.json`, find this EXACT text (the first two lines):

```text
{
  "name": "ds-star",
  "owner": {
```

Replace it with:

```text
{
  "name": "ds-crew",
  "owner": {
```

- [ ] **Step 3: marketplace.json — plugin entry name**

In `.claude-plugin/marketplace.json`, find this EXACT text:

```text
    {
      "name": "ds-star",
      "source": "./",
```

Replace it with:

```text
    {
      "name": "ds-crew",
      "source": "./",
```

- [ ] **Step 4: package.json**

In `package.json`, find this EXACT text:

```text
  "name": "ds-star",
  "version": "1.1.0",
```

Replace it with:

```text
  "name": "ds-crew",
  "version": "1.1.0",
```

- [ ] **Step 5: Verify all four name fields are `ds-crew` and JSON still parses**

Run:
```bash
cd /Users/adamkrysztopa/projects/DS-STAR
python3 - <<'PY'
import json
pj = json.load(open(".claude-plugin/plugin.json"))
pk = json.load(open("package.json"))
mp = json.load(open(".claude-plugin/marketplace.json"))
assert pj["name"] == "ds-crew", pj["name"]
assert pk["name"] == "ds-crew", pk["name"]
assert mp["name"] == "ds-crew", mp["name"]
assert mp["plugins"][0]["name"] == "ds-crew", mp["plugins"][0]["name"]
print("OK install id ->", mp["plugins"][0]["name"] + "@" + mp["name"])
PY
```
Expected: `OK install id -> ds-crew@ds-crew`.

---

## Task 4: Update the README install docs

**Files:**
- Modify: `README.md`

- [ ] **Step 1: marketplace add URL**

In `README.md`, find this EXACT text:

```text
claude plugin marketplace add AdamKrysztopa/ds-stats-with-claude
```

Replace it with:

```text
claude plugin marketplace add AdamKrysztopa/ds-crew
```

- [ ] **Step 2: the three install commands**

In `README.md`, find this EXACT text:

```text
# All your projects
claude plugin install ds-star@ds-star --scope user

# This project only (saved to .claude/settings.json)
claude plugin install ds-star@ds-star --scope project

# Local override, not committed
claude plugin install ds-star@ds-star --scope local
```

Replace it with:

```text
# All your projects
claude plugin install ds-crew@ds-crew --scope user

# This project only (saved to .claude/settings.json)
claude plugin install ds-crew@ds-crew --scope project

# Local override, not committed
claude plugin install ds-crew@ds-crew --scope local
```

- [ ] **Step 3: update / uninstall commands**

In `README.md`, find this EXACT text:

```text
claude plugin update ds-star@ds-star
claude plugin uninstall ds-star@ds-star
```

Replace it with:

```text
claude plugin update ds-crew@ds-crew
claude plugin uninstall ds-crew@ds-crew
```

- [ ] **Step 4: repository-layout root**

In `README.md`, find this EXACT text (the first line inside the layout code block):

```text
ds-stats-with-claude/
├── skills/
```

Replace it with:

```text
ds-crew/
├── skills/
```

- [ ] **Step 5: Verify no stale identifiers remain in the README**

Run:
```bash
cd /Users/adamkrysztopa/projects/DS-STAR
echo "stale 'ds-stats-with-claude':"; grep -n "ds-stats-with-claude" README.md || echo "  none"
echo "stale 'ds-star@ds-star':";      grep -n "ds-star@ds-star" README.md || echo "  none"
echo "new 'ds-crew@ds-crew' count:";  grep -c "ds-crew@ds-crew" README.md
```
Expected: `none` for both stale checks; the new-id count is `5`.

---

## Task 5: Guardrail check — nothing over-renamed

**Files:** none (verification only)

- [ ] **Step 1: Confirm the skill, command, and method names are intact**

Run:
```bash
cd /Users/adamkrysztopa/projects/DS-STAR
test -d skills/ds-star && echo "skills/ds-star/ intact"
test -d skills/ds-star-plus && echo "skills/ds-star-plus/ intact"
grep -q "^name: ds-star$" skills/ds-star/SKILL.md && echo "ds-star skill frontmatter intact"
grep -q "DS-STAR" README.md && echo "DS-STAR method name intact in prose"
echo "invocations still listed:"; grep -E "^/ds-star( |$)|/ds-star  " README.md | head -1
```
Expected: all four "intact" lines print; the skill dirs and method name are unchanged.

- [ ] **Step 2: Confirm only the four manifest name fields changed identifier (no accidental skill rename)**

Run:
```bash
cd /Users/adamkrysztopa/projects/DS-STAR
echo "remaining '\"name\": \"ds-star\"' (should be 0):"
grep -rn '"name": "ds-star"' .claude-plugin/ package.json || echo "  0 — good"
```
Expected: `0 — good`.

---

## Task 6: Commit and push to the renamed remote

**Files:** none (git)

- [ ] **Step 1: Stage, commit, push**

Run:
```bash
cd /Users/adamkrysztopa/projects/DS-STAR
git add -A
git commit -m "chore: rename suite ds-star -> ds-crew (repo, plugin, marketplace, package)

The plugin/marketplace/package identifier is renamed from ds-star to ds-crew
so the bundle is named for the whole crew of skills, not the single ds-star
member. Install id is now ds-crew@ds-crew. The ds-star skill, ds-star-plus,
the /ds-star command, and the DS-STAR method name are unchanged.

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"
git push origin main
```
Expected: push succeeds to `github.com:AdamKrysztopa/ds-crew`.

---

## Task 7: Re-register the marketplace on the local machine

**Files:** none (local Claude config)

The old marketplace was registered under the name `ds-star`. Refresh it so local installs resolve
to `ds-crew`. (This affects only the user's machine, not the repo.)

- [ ] **Step 1: Remove the old registration and add the new one**

Run:
```bash
claude plugin marketplace remove ds-star 2>/dev/null || true
claude plugin marketplace add AdamKrysztopa/ds-crew
```
Expected: the new marketplace `ds-crew` is added.

- [ ] **Step 2: Reinstall under the new id (if it was installed before)**

Run:
```bash
claude plugin uninstall ds-star@ds-star 2>/dev/null || true
claude plugin install ds-crew@ds-crew --scope user
```
Expected: `ds-crew@ds-crew` installs; `/ds-star`, `/ds-star-plus`, `/ds-clarify`, `/ds-spike`,
`/data-profile`, `/eda-narrative` are all available.

---

## Optional: rename the local working directory

Cosmetic only — the folder name is independent of the repo name. If desired:

```bash
cd /Users/adamkrysztopa/projects
mv DS-STAR ds-crew
```
Then reopen the session in the new path. Skip if you prefer to keep the local path stable.

---

## Self-Review (completed during planning)

**Coverage:** all 11 in-repo occurrences from the grep are handled — README ×7 (1 add-URL + 5
install ids + 1 layout root), manifests ×3 name fields, package.json ×1 — plus the GitHub rename
(Task 1), the git remote (Task 2), and local re-registration (Task 7).

**Placeholder scan:** none — every step has exact find/replace text or an exact command.

**Over-rename guard:** Task 5 explicitly asserts `skills/ds-star/`, `ds-star-plus`, the `/ds-star`
command, the `ds-star` skill frontmatter, and the `DS-STAR` method name are untouched, and that no
stray `"name": "ds-star"` remains in the manifests.

**Ordering:** GitHub rename (Task 1) precedes the remote repoint (Task 2) and the doc updates
(Tasks 3–4), so the new URL exists before anything references it; push (Task 6) lands on the renamed
remote.
