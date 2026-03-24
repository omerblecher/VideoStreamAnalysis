# Phase 2: Blurring - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Viewer blurs each detected motion region (within its bounding rectangle) before drawing bounding boxes. Changes are isolated to viewer.py. Codebase is committed, tagged `phase-b`, and pushed to GitHub. Restore command and detection algorithm changes are out of scope.

</domain>

<decisions>
## Implementation Decisions

### Blur strength
- Use `cv2.GaussianBlur` (per requirement suggestion; standard, fast, smooth)
- Blur should be obviously visible — strong enough that motion regions are clearly obscured
- Kernel size scales proportionally with each bounding box size (small regions get lighter blur, large regions get stronger)
- Kernel size defined as a named constant at the top of viewer.py (easy to tweak, no CLI arg)

### Blur edge blending
- Hard cutoff at the bounding rectangle boundary — no feathering or gradient blend
- Blur region is the full bounding rectangle (not the precise contour polygon mask) — per BLUR-02
- Bounding box rectangle is drawn on top of the blurred region (blur first, then draw box) — consistent with Phase 1 annotation style
- If a bounding rectangle extends beyond the frame edge, clip coordinates to valid frame bounds

### Overlapping regions
- Blur each contour's bounding rectangle independently in a loop (no merging logic)
- Double-blurring in overlap zones is acceptable — visually fine, keeps code simple
- Frames with no detected contours pass through unchanged (no blur applied)

### Commit message design
- Commit message explains the design decision to blur the full bounding rectangle rather than the precise contour polygon mask — simpler, satisfies BLUR-02 exactly, and produces a clean visual result
- Changes committed: viewer.py only (no README update)
- Tag: `phase-b`, pushed to GitHub

### Claude's Discretion
- Exact proportional kernel size formula (e.g. percentage of bbox dimension, clamped to odd number)
- Order of operations within the Viewer's frame-drawing loop
- Defensive handling of zero-size or degenerate bounding boxes

</decisions>

<specifics>
## Specific Ideas

- No specific references — open to standard cv2.GaussianBlur patterns

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-blurring*
*Context gathered: 2026-03-24*
