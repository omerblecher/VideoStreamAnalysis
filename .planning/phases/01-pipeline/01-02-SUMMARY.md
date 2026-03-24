---
phase: 01-pipeline
plan: 02
subsystem: video-processing
tags: [python, opencv, mog2, background-subtraction, multiprocessing, shared-memory, numpy]

# Dependency graph
requires:
  - phase: 01-01
    provides: "ipc.py contracts: ShmFrameMessage, DetectorMessage, EOS_SENTINEL; streamer.py producer"
provides:
  - "Detector process: run_detector(from_streamer, to_viewer) in detector.py"
  - "MOG2 background subtraction with Gaussian blur pre-processing and area filtering"
  - "Contour list forwarded in DetectorMessage; original SharedMemory reference preserved for Viewer"
affects: [03-viewer, 04-main]

# Tech tracking
tech-stack:
  added: []
  patterns: [mog2-background-subtractor, shm-consumer-copy-then-close, eos-propagation]

key-files:
  created: [detector.py]
  modified: []

key-decisions:
  - "Detector copies frame locally (frame.copy()) before closing its shm handle so it owns independent numpy memory"
  - "Detector never unlinks SharedMemory — Viewer owns cleanup after display"
  - "MIN_CONTOUR_AREA = 500 px² per CONTEXT.md discretion to filter sensor/compression noise"
  - "_detect_motion() extracted as private helper to keep run_detector loop clean and readable"

patterns-established:
  - "SharedMemory consumer pattern: attach (create=False), copy frame, close handle, use copy locally"
  - "EOS propagation: check with 'is EOS_SENTINEL', put to next Queue, return immediately"
  - "MOG2 pipeline: BGR -> grayscale -> GaussianBlur -> bg_sub.apply -> dilate -> findContours -> area filter"

requirements-completed: [PIPE-03, PIPE-04]

# Metrics
duration: 1min
completed: 2026-03-24
---

# Phase 1 Plan 02: Detector Process Summary

**MOG2 background subtraction detector using cv2.createBackgroundSubtractorMOG2 with Gaussian blur pre-processing, dilation, and minimum area filtering — forwards contour list and original SharedMemory reference to Viewer**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-03-24T16:06:32Z
- **Completed:** 2026-03-24T16:07:41Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- `detector.py` implements `run_detector(from_streamer, to_viewer)` — the compute stage of the pipeline
- MOG2 algorithm: BGR to grayscale, (21,21) Gaussian blur, MOG2 apply, 2-iteration dilation, external contour extraction, area filter at 500 px²
- Detector attaches to SharedMemory read-only, copies the frame before closing its handle, then forwards the original `shm_name` in DetectorMessage — Viewer retains exclusive access to unlink
- EOS_SENTINEL propagated correctly: on receipt from Streamer, Detector puts sentinel on to_viewer and returns

## Task Commits

Each task was committed atomically:

1. **Task 1: Detector process with MOG2 background subtraction** - `fdafa48` (feat)

## Files Created/Modified
- `detector.py` - Detector process: attaches to SharedMemory, runs MOG2 VMD, produces DetectorMessage with contour list

## Decisions Made
- `frame.copy()` called before `shm.close()` so Detector's numpy array is fully independent from the shared memory block — no use-after-close risk
- Private helper `_detect_motion(bg_sub, frame)` isolates the algorithm steps from the loop plumbing
- `MIN_CONTOUR_AREA = 500` chosen per CONTEXT.md discretion; appropriate for 640×480 streams
- `list(contours)` wraps the tuple returned by findContours to match the DetectorMessage dataclass field type

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- `detector.py` is ready for Plan 03 (Viewer) to consume DetectorMessage objects
- Viewer must attach to SharedMemory by `shm_name`, display/annotate frame, then unlink the block
- Both queue directions (Streamer→Detector, Detector→Viewer) are now fully implemented

## Self-Check: PASSED

- FOUND: C:/code/VideoStreamAnalysis/detector.py
- FOUND commit: fdafa48 (feat(01-02): implement Detector process with MOG2 background subtraction)
- FOUND: createBackgroundSubtractorMOG2 in detector.py
- FOUND: no absdiff, prev_gray, cv2.rectangle, cv2.putText in detector.py

---
*Phase: 01-pipeline*
*Completed: 2026-03-24*
