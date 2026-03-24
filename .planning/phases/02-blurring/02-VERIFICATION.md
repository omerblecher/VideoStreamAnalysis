---
phase: 02-blurring
verified: 2026-03-24T15:30:00Z
status: human_needed
score: 2/3 must-haves verified automatically
human_verification:
  - test: "Run python main.py and observe the displayed video window while motion is detected"
    expected: "Motion region rectangles contain visibly blurred pixels; areas outside the green bounding boxes are sharp and unaffected; green bounding boxes are drawn on top of the blur (not obscured by it); the HH:MM:SS timestamp in the top-left corner is clear and visible"
    why_human: "Visual blur quality and the perceptual correctness of selective blurring cannot be verified by static code analysis — requires running the pipeline against a video with motion"
---

# Phase 2: Blurring Verification Report

**Phase Goal:** Viewer blurs each motion region before annotating, making the feature visually verifiable
**Verified:** 2026-03-24T15:30:00Z
**Status:** human_needed — all automated checks pass; one truth requires visual confirmation
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Motion regions in the displayed video appear blurred (Gaussian or equivalent) inside their bounding rectangles | ? HUMAN NEEDED | `_blur_motion_regions` calls `cv2.blur` per-contour ROI (line 56); correct call order confirmed at lines 108-109; visual confirmation required |
| 2 | Areas outside detected contours are not blurred | VERIFIED | Function iterates only over `contours`; writes back only `frame[y1:y2, x1:x2]`; no whole-frame operation present |
| 3 | Codebase is committed, tagged phase-b, and pushed to GitHub | VERIFIED | Commit `d45f357` exists; annotated tag `phase-b` points to it; `git ls-remote` confirms tag at origin; `git status` reports branch up to date with origin/master |

**Score:** 2/3 truths verified automatically (1 requires human visual confirmation)

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `viewer.py` | `_blur_motion_regions` function applying blur to each motion region's bounding rect | VERIFIED | Function defined at line 36; 21 lines of substantive implementation; uses `cv2.blur` with proportional kernel; clips coords to frame bounds; skips degenerate rects |
| `viewer.py` | `BLUR_KERNEL_FRACTION` constant | VERIFIED | Defined at line 23 as `0.2` |
| `viewer.py` | `run_viewer` loop calling blur before boxes | VERIFIED | Line 108: `_blur_motion_regions(frame, msg.contours)`; line 109: `_draw_motion_boxes(frame, msg.contours)` — correct order |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `run_viewer` loop | `_blur_motion_regions` | called before `_draw_motion_boxes` on each frame | VERIFIED | Line 108 precedes line 109 in the same sequential block |
| `_blur_motion_regions` | `cv2.blur` | per-contour bounding rect slice | VERIFIED (with deviation) | Plan spec required `cv2.GaussianBlur`; implementation uses `cv2.blur` (box blur). Per the prompt note, `cv2.blur` satisfies the "Gaussian or equivalent" success criterion. The substitution was made because `cv2.GaussianBlur` crashed on Python 3.13/Windows. |

#### Deviation Note: cv2.blur vs cv2.GaussianBlur

The PLAN frontmatter key_link specifies `cv2.GaussianBlur` as the pattern. The actual implementation uses `cv2.blur` (box blur). This was an intentional deviation documented in both SUMMARY files:
- Plan 02-01 SUMMARY: GaussianBlur "crashed on Python 3.13/Windows with cv2.error"
- Plan 02-02 SUMMARY: "cv2.blur produces visually equivalent results and is stable"
- The phase success criterion says "Gaussian or equivalent" — `cv2.blur` satisfies this.
- `cv2.blur` does not require an odd kernel size, so the odd-enforcement step from the original plan (`if k % 2 == 0: k += 1`) was correctly omitted in the implementation.

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BLUR-01 | 02-01-PLAN.md, 02-02-PLAN.md | Viewer applies a blur (e.g. Gaussian) to each detected motion region before drawing bounding boxes | SATISFIED | `_blur_motion_regions` called at viewer.py line 108, before `_draw_motion_boxes` at line 109; uses `cv2.blur` per contour |
| BLUR-02 | 02-01-PLAN.md, 02-02-PLAN.md | Blurring is applied only within the bounding rectangle of each contour | SATISFIED | ROI slice `frame[y1:y2, x1:x2]` with clipped coords; only that slice is written back; docstring explicitly documents "BLUR-02" compliance |

Both BLUR requirements are marked complete in REQUIREMENTS.md traceability table. No orphaned requirements found — REQUIREMENTS.md maps only BLUR-01 and BLUR-02 to Phase 2, both claimed by plans 02-01 and 02-02.

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none) | — | — | — | — |

No TODOs, FIXMEs, placeholders, empty returns, or stub implementations found in viewer.py.

---

### Git / Delivery State

| Check | Result |
|-------|--------|
| Commit for blurring implementation | `1702de7` — feat(02-01): add _blur_motion_regions to viewer.py |
| Commit with design-decision message | `d45f357` — feat(phase-b): blur motion regions in Viewer before drawing bounding boxes |
| Annotated tag `phase-b` | Present, points to `d45f357` |
| Tag pushed to origin | Confirmed via `git ls-remote --tags origin phase-b` → `3749a88...refs/tags/phase-b` |
| master pushed to origin | `git status` reports "Your branch is up to date with 'origin/master'" |
| Working tree clean of source files | viewer.py is committed; only untracked non-source items (`.claude/`, `People - 6387.mp4`, `__pycache__/`) and a modified planning file remain |

---

### Human Verification Required

#### 1. Visual blur correctness in running pipeline

**Test:** Run `python main.py` from `C:/code/VideoStreamAnalysis`. Wait until motion is detected (the application displays motion with green bounding boxes).
**Expected:**
1. The area inside each green bounding rectangle should appear visually blurred/smeared — not sharp
2. The rest of the frame outside the green boxes should remain sharp and unaffected
3. Green bounding boxes are drawn on top of the blurred area (the blur is under the box, not over it)
4. The HH:MM:SS timestamp in the top-left corner is still clearly readable
**Why human:** Perceptual blur quality and selective-blur correctness cannot be verified by static code analysis. The automated checks confirm the code path exists and is wired correctly, but only running the pipeline against a video with actual motion proves the visual output is correct.

---

### Implementation Notes

The `_blur_motion_regions` function at viewer.py lines 36-56 implements the following verified behaviors:

- **Scope:** Iterates only over the provided `contours` list — no global frame operation
- **ROI extraction:** `cv2.boundingRect(c)` → clipped to `[0, w) x [0, h)` frame bounds
- **Degenerate guard:** Skips any rect where `x2 <= x1` or `y2 <= y1` (fully off-screen or zero-area)
- **Kernel sizing:** `max(3, min(99, int(min(bw, bh) * 0.2)))` — proportional to smaller dimension, clamped; odd enforcement omitted because `cv2.blur` does not require it
- **In-place modification:** `frame[y1:y2, x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (k, k))` — zero extra allocation
- **Call order in run_viewer:** blur (line 108) → draw boxes (line 109) → draw timestamp (line 110) → imshow (line 112)

---

### Gaps Summary

No code gaps found. All automated checks pass:
- `_blur_motion_regions` exists, is substantive, and is correctly wired
- Call order is correct (blur before boxes)
- BLUR-01 and BLUR-02 are both satisfied
- Tag `phase-b` is annotated, points to the correct commit, and is pushed to GitHub
- viewer.py passes Python syntax check

The single human_needed item is the visual confirmation of blur output during live pipeline execution — this is inherently a runtime/perceptual check that cannot be replaced by static analysis.

---

_Verified: 2026-03-24T15:30:00Z_
_Verifier: Claude (gsd-verifier)_
