---
phase: 01-pipeline
plan: 03
subsystem: video-processing
tags: [python, opencv, shared-memory, multiprocessing, numpy, annotation, frame-rate-control]

# Dependency graph
requires:
  - phase: 01-02
    provides: "detector.py producing DetectorMessage with contour list and SharedMemory reference"
  - phase: 01-01
    provides: "ipc.py contracts: DetectorMessage, EOS_SENTINEL; streamer.py producer"
provides:
  - "Viewer process: run_viewer(from_detector, video_path) in viewer.py"
  - "Pipeline launcher: main.py with CLI arg parsing and process spawning"
  - "Full three-process pipeline runnable with: python main.py <video_path>"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns: [shm-last-consumer-unlink, cv2-named-window-before-loop, fps-derived-waitkey-delay, timestamp-overlay-with-background-rect]

key-files:
  created: [viewer.py, main.py]
  modified: []

key-decisions:
  - "Window title deferred until first message so FPS is known; cv2.namedWindow called once before the display loop"
  - "shm.close() then shm.unlink() immediately after frame copy — Viewer is the exclusive unlinker"
  - "label_y clamped so 'motion' label stays inside frame when contour is near the top edge"
  - "Timestamp background rect drawn with (30,30,30) near-black fill for legibility on any frame content"
  - "Unbounded Queues in main.py — no maxsize, allows Streamer to run ahead without blocking"

patterns-established:
  - "SharedMemory last-consumer pattern: copy frame, close handle, unlink block immediately"
  - "OpenCV window lifecycle: namedWindow once before loop, imshow+waitKey in loop, destroyAllWindows on EOS"
  - "FPS-derived delay: delay = max(1, int(1000 / fps)) to never drop below 1ms"

requirements-completed: [PIPE-05, PIPE-06, PIPE-07]

# Metrics
duration: 2min
completed: 2026-03-24
---

# Phase 1 Plan 03: Viewer Process and Launcher Summary

**OpenCV Viewer process that annotates frames with green bounding boxes, HH:MM:SS timestamp (white text on dark background), plays at original FPS via waitKey delay, and frees SharedMemory blocks; plus main.py single-command launcher with CLI validation**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-24T16:10:04Z
- **Completed:** 2026-03-24T16:12:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `viewer.py` implements `run_viewer(from_detector, video_path)` — the display end of the pipeline
- Frame annotation: green 2px bounding rectangles with "motion" label above each contour (clamped to stay in frame)
- HH:MM:SS timestamp overlay with near-black background rect for legibility on any scene content
- SharedMemory lifecycle completed: Viewer is the last consumer and calls `shm.unlink()` after copying frame
- `main.py` ties together all three processes — validates video path, creates Queues, spawns Streamer/Detector/Viewer, joins all

## Task Commits

Each task was committed atomically:

1. **Task 1: Viewer process** - `64acd70` (feat)
2. **Task 2: Launcher main.py** - `b8fec3e` (feat)

## Files Created/Modified
- `viewer.py` - Viewer process: attaches to SharedMemory, annotates frame, displays at correct FPS, unlinks block
- `main.py` - Launcher: CLI arg validation, spawns all three processes with correct Queue wiring

## Decisions Made
- Window title creation deferred until first message arrives so FPS is known; `cv2.namedWindow` called once outside the loop using that title
- `label_y` clamped: if `y - 5 <= 10`, label placed at `y + 15` instead to avoid drawing outside the frame boundary
- Timestamp background uses `(30, 30, 30)` near-black rather than pure black to look less harsh while still providing contrast
- `max(1, int(1000 / fps))` ensures waitKey delay is never 0 (which would disable the delay entirely in OpenCV)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Full pipeline is complete: `python main.py "People - 6387.mp4"` launches all three processes
- Phase 1 (Pipeline) is fully delivered: Streamer + Detector + Viewer + Launcher
- Phase 2 (Blur) can add frame blurring as a pre-processing step in the Detector
- Phase 3 (Shutdown) can add graceful termination (Ctrl+C handler, process cleanup)

## Self-Check: PASSED

- FOUND: C:/code/VideoStreamAnalysis/viewer.py
- FOUND: C:/code/VideoStreamAnalysis/main.py
- FOUND commit: 64acd70 (feat(01-03): implement Viewer process)
- FOUND commit: b8fec3e (feat(01-03): add launcher main.py)

---
*Phase: 01-pipeline*
*Completed: 2026-03-24*
