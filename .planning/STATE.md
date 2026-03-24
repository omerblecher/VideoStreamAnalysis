# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Smooth, correctly pipelined video display at original frame rate with motion detection overlaid — demonstrating Python multiprocessing and SharedMemory IPC
**Current focus:** Phase 2 - Blurring

## Current Position

Phase: 2 of 3 (Blurring)
Plan: 2 of 2 in current phase
Status: Phase 02-blurring complete — all plans done
Last activity: 2026-03-24 — Plan 02-02 complete

Progress: [███████░░░] 67%

## Performance Metrics

**Velocity:**
- Total plans completed: 6
- Average duration: 1.7 min
- Total execution time: 0.10 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-pipeline | 4 | 10 min | 2.5 min |
| 02-blurring | 2 | 4 min | 2 min |

**Recent Trend:**
- Last 5 plans: 01-02 (1 min), 01-03 (2 min), 01-04 (5 min), 02-01 (1 min), 02-02 (3 min)
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- SharedMemory for frames: avoids copying ~6MB BGR arrays per frame between processes
- Queue for metadata/signals: lightweight coordination for contours, frame indices, shutdown sentinel
- Queue per pipeline stage: Streamer→Detector queue + Detector→Viewer queue, natural backpressure
- basic_vmd.py used as-is: assignment requirement, no parameter tuning
- EOS_SENTINEL = None as module constant; all processes check with 'is EOS_SENTINEL' identity comparison
- Streamer closes shm handle but Viewer owns the unlink after display (lifecycle ownership)
- FPS fallback to 25.0 when cv2.CAP_PROP_FPS returns <= 0
- Detector copies frame before closing shm handle so its numpy array is independent of the shared memory block
- Detector never unlinks SharedMemory (Viewer owns cleanup); MIN_CONTOUR_AREA = 500 px²
- Viewer defers window title creation until first message so FPS is known; cv2.namedWindow called once
- Viewer calls shm.close() then shm.unlink() immediately after frame copy — last consumer owns cleanup
- Unbounded Queues in main.py — no maxsize, allows Streamer to run ahead without blocking
- Branch is master (not main); remote origin = https://github.com/omerblecher/VideoStreamAnalysis.git
- Tag phase-a is annotated, pointing to commit 4791b1b (SharedMemory design explanation)
- BLUR_KERNEL_FRACTION = 0.2: kernel is 20% of smaller bbox dimension, forced odd, clamped to [3, 99]
- Blur-then-box ordering in run_viewer: _blur_motion_regions called before _draw_motion_boxes
- cv2.blur (box blur) used instead of cv2.GaussianBlur — GaussianBlur crashed on Python 3.13/Windows; cv2.blur produces equivalent perceptual result
- Tag phase-b is annotated, pointing to commit d45f357 (Phase B complete: blurring verified and pushed)

### Pending Todos

None yet.

### Blockers/Concerns

None.

## Session Continuity

Last session: 2026-03-24
Stopped at: Completed 02-02-PLAN.md — Phase 02-blurring fully complete, phase-b tag pushed to GitHub
Resume file: None
