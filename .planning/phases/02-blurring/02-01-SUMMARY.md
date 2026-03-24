---
phase: 02-blurring
plan: 01
subsystem: video-processing
tags: [opencv, gaussian-blur, motion-detection, viewer]

# Dependency graph
requires:
  - phase: 01-pipeline
    provides: viewer.py with run_viewer loop and _draw_motion_boxes already in place
provides:
  - Gaussian blur applied to each motion region's bounding rect before bounding box drawing
  - _blur_motion_regions function with proportional odd kernel and safe coordinate clipping
  - BLUR_KERNEL_FRACTION constant for tuning blur strength
affects: [03-output, any phase that modifies viewer.py display pipeline]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Blur-then-box ordering: apply visual transforms before drawing overlays"
    - "Proportional kernel sizing: kernel = max(3, int(min(bw,bh)*fraction)), rounded up to odd, clamped to 99"
    - "Defensive ROI clipping: clip all bounding rect coords to frame bounds before slicing"

key-files:
  created: []
  modified:
    - viewer.py

key-decisions:
  - "BLUR_KERNEL_FRACTION = 0.2 — kernel size is 20% of the smaller bbox dimension, clamped to odd [3, 99]"
  - "Blur applied in-place via frame[y1:y2, x1:x2] slice assignment for zero-copy within ROI"
  - "Degenerate/fully-off-edge bounding rects skipped silently (x2 <= x1 or y2 <= y1 guard)"

patterns-established:
  - "In-place frame modification pattern: all annotate/transform functions take frame as first arg and modify in-place"
  - "Proportional blur kernel: scales with motion region size rather than fixed kernel"

requirements-completed: [BLUR-01, BLUR-02]

# Metrics
duration: 1min
completed: 2026-03-24
---

# Phase 2 Plan 01: Blurring Summary

**Gaussian blur via cv2.GaussianBlur applied in-place to each motion region's bounding rect before box drawing, using proportional odd kernel clamped to [3, 99] with safe coordinate clipping**

## Performance

- **Duration:** 1 min
- **Started:** 2026-03-24T00:03:32Z
- **Completed:** 2026-03-24T00:04:16Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Added `BLUR_KERNEL_FRACTION = 0.2` named constant after imports in viewer.py
- Added `_blur_motion_regions` function that Gaussian-blurs each contour's bounding rect in-place with proportional odd kernel clamped to [3, 99] and safe coordinate clipping
- Updated `run_viewer` loop to call `_blur_motion_regions` before `_draw_motion_boxes` (blur-then-box order)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add _blur_motion_regions to viewer.py** - `1702de7` (feat)

**Plan metadata:** (docs commit to follow)

## Files Created/Modified
- `viewer.py` - Added BLUR_KERNEL_FRACTION constant, _blur_motion_regions function, and updated run_viewer call order

## Decisions Made
- BLUR_KERNEL_FRACTION = 0.2: kernel is 20% of the smaller bounding box dimension, forced odd, clamped to [3, 99]
- In-place ROI assignment: `frame[y1:y2, x1:x2] = cv2.GaussianBlur(roi, (k, k), 0)` avoids extra allocations
- Degenerate bounding rects (fully outside frame or zero-area) are silently skipped

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Motion blur is complete and satisfies assignment Phase B requirement
- viewer.py is ready for any further Phase 3 output/recording tasks
- No blockers

---
*Phase: 02-blurring*
*Completed: 2026-03-24*
