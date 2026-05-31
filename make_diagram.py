#!/usr/bin/env python3
"""Generate architecture-comparison.svg: a mirrored v1-vs-v2 diagram with a shared stage spine."""

W = 1180
PAD = 40
TITLE_H = 150
ROW_H = 60
HDR_H = 44

# palette (warm paper, ink, tier accents) — editorial/technical, not generic AI
PAPER = "#F3EEE3"
PANEL = "#FBF8F1"
INK = "#23221E"
SUB = "#6F6A5E"
LINE = "#CFC7B5"
SPINE = "#1F1E1B"
TIER = {
    "Haiku": "#C2902B",   # ochre
    "Sonnet": "#2E6B6A",  # teal
    "Opus": "#9A3B2C",    # deep rust
    "—": "#8B8676",       # neutral
}

# (stage, v1 text, v2 text, tier label)
ROWS = [
    ("Analyze files",  "1 model · describer per file",     "describer/file + cached digest",    "Haiku"),
    ("Retrieve (lake)","top-K by embedding",               "top-150 + relevance pass → K",      "Haiku"),
    ("Initial step",   "1 model",                          "plan + code",                       "Haiku→Sonnet"),
    ("Implement",      "full descriptions each round",     "digests; full only if touched",     "Sonnet"),
    ("Execute",        "run script",                       "run script",                        "—"),
    ("Verify",         "Yes / No",                         "{sufficient, reason, missing} · 3× vote", "Opus"),
    ("Route",          "add / Step l",                     "add / Step l",                      "Sonnet"),
    ("Refine",         "truncate + regenerate",            "+ anti-repeat · branch on stall",   "Sonnet→Opus"),
    ("Finalize",       "1 model",                          "reformat to spec",                  "Haiku"),
    ("Debug",          "trace + descriptions",             "trim → fix (escalates)",            "Haiku→Sonnet"),
    ("Early exit",     "implicit",                         "explicit guardrail (1 round)",      "—"),
]

H = TITLE_H + HDR_H + ROW_H * len(ROWS) + PAD
cx = W / 2
spine_w = 196
spine_l = cx - spine_w / 2
spine_r = cx + spine_w / 2
col_pad = 18
left_box_r = spine_l - 22
right_box_l = spine_r + 22
box_left_x = PAD
box_right_x = W - PAD


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tier_color(label):
    # for compound labels like "Sonnet→Opus", colour by the higher (last) tier
    last = label.split("→")[-1].strip()
    return TIER.get(last, TIER["—"])


svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{int(H)}" viewBox="0 0 {W} {int(H)}" font-family="Georgia, \'Times New Roman\', serif">')
svg.append(f'<rect width="{W}" height="{int(H)}" fill="{PAPER}"/>')

# title band
svg.append(f'<text x="{PAD}" y="56" font-size="34" fill="{INK}" font-weight="bold">DS-STAR &#8212; architecture, back to back</text>')
svg.append(f'<text x="{PAD}" y="86" font-size="16" fill="{SUB}">Shared six-stage loop down the spine. v1 (faithful) branches left; v2 (hardened) branches right.</text>')
# tier legend
lx = PAD
ly = 116
svg.append(f'<text x="{lx}" y="{ly+4}" font-size="13" fill="{SUB}" font-family="\'Courier New\', monospace">v2 model tier:</text>')
lx += 130
for name in ["Haiku", "Sonnet", "Opus"]:
    svg.append(f'<rect x="{lx}" y="{ly-11}" width="14" height="14" rx="3" fill="{TIER[name]}"/>')
    svg.append(f'<text x="{lx+20}" y="{ly+1}" font-size="13" fill="{INK}" font-family="\'Courier New\', monospace">{name}</text>')
    lx += 110

# column headers
hy = TITLE_H + 28
svg.append(f'<text x="{box_left_x}" y="{hy}" font-size="18" fill="{INK}" font-weight="bold">v1 &#183; ds-star</text>')
svg.append(f'<text x="{cx}" y="{hy}" font-size="15" fill="{SUB}" text-anchor="middle" font-family="\'Courier New\', monospace">STAGE</text>')
svg.append(f'<text x="{box_right_x}" y="{hy}" font-size="18" fill="{INK}" font-weight="bold" text-anchor="end">v2 &#183; ds-star-plus</text>')

# central spine line
top = TITLE_H + HDR_H
bot = top + ROW_H * len(ROWS)
svg.append(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{bot}" stroke="{SPINE}" stroke-width="2.5"/>')

for i, (stage, v1, v2, tier) in enumerate(ROWS):
    ry = top + i * ROW_H
    midy = ry + ROW_H / 2
    # spine node
    svg.append(f'<circle cx="{cx}" cy="{midy}" r="5.5" fill="{SPINE}"/>')
    # stage capsule on the spine
    cap_w = spine_w - 10
    svg.append(f'<rect x="{cx-cap_w/2}" y="{midy-15}" width="{cap_w}" height="30" rx="15" fill="{PANEL}" stroke="{SPINE}" stroke-width="1.5"/>')
    svg.append(f'<text x="{cx}" y="{midy+5}" font-size="14" fill="{INK}" text-anchor="middle" font-weight="bold">{esc(stage)}</text>')

    # connectors
    svg.append(f'<line x1="{left_box_r}" y1="{midy}" x2="{cx-cap_w/2}" y2="{midy}" stroke="{LINE}" stroke-width="1.5"/>')
    svg.append(f'<line x1="{cx+cap_w/2}" y1="{midy}" x2="{right_box_l}" y2="{midy}" stroke="{LINE}" stroke-width="1.5"/>')

    # v1 box (left, hugging spine)
    bw = left_box_r - box_left_x
    svg.append(f'<rect x="{box_left_x}" y="{ry+9}" width="{bw}" height="{ROW_H-18}" rx="7" fill="{PANEL}" stroke="{LINE}" stroke-width="1.2"/>')
    svg.append(f'<text x="{left_box_r-col_pad}" y="{midy+5}" font-size="14.5" fill="{INK}" text-anchor="end">{esc(v1)}</text>')

    # v2 box (right) with tier chip
    bx = right_box_l
    bw2 = box_right_x - bx
    accent = tier_color(tier)
    svg.append(f'<rect x="{bx}" y="{ry+9}" width="{bw2}" height="{ROW_H-18}" rx="7" fill="{PANEL}" stroke="{accent}" stroke-width="1.6"/>')
    svg.append(f'<rect x="{bx}" y="{ry+9}" width="6" height="{ROW_H-18}" rx="3" fill="{accent}"/>')
    svg.append(f'<text x="{bx+col_pad}" y="{midy-2}" font-size="14.5" fill="{INK}">{esc(v2)}</text>')
    svg.append(f'<text x="{bx+col_pad}" y="{midy+15}" font-size="11.5" fill="{accent}" font-family="\'Courier New\', monospace">{esc(tier)}</text>')

# loop brackets (Implement..Refine = rows index 3..7)
loop_top = top + 3 * ROW_H + 9
loop_bot = top + 8 * ROW_H - 9
for side, x, label_anchor, tx in [("L", box_left_x - 14, "start", box_left_x - 10), ("R", box_right_x + 14, "end", box_right_x + 10)]:
    arm = 10 if side == "R" else -10
    svg.append(f'<path d="M {x-arm} {loop_top} L {x} {loop_top} L {x} {loop_bot} L {x-arm} {loop_bot}" fill="none" stroke="{SUB}" stroke-width="1.4"/>')
    svg.append(f'<text x="{tx}" y="{(loop_top+loop_bot)/2+4}" font-size="11.5" fill="{SUB}" text-anchor="{label_anchor}" font-family="\'Courier New\', monospace" transform="rotate({90 if side=="R" else -90} {tx} {(loop_top+loop_bot)/2})">loop &#8804; 20 rounds</text>')

svg.append('</svg>')

# v1.1 — update pending v1.2
# v1.2 additions not yet rendered in the SVG:
#   + kernel/DAG/memory/debate/conduct
# To regenerate with v1.2 content, extend ROWS above or add a second section
# (e.g. a separate table block appended below the main diagram rows) covering:
#   - Stateful kernel (kernel_runner.py, track F)
#   - DAG planning (task graph {id, goal, deps, status}, track G)
#   - Cross-session memory (memory_store.py, track E)
#   - Debate in ds-spike (≤2 cross-critique rounds, track I)
#   - ds-conduct orchestrator (Peek→Grill→Assemble→Execute, track K)

out = "architecture-comparison.svg"
with open(out, "w") as f:
    f.write("\n".join(svg))
print("wrote", out)
