# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Smooth, correctly pipelined video display at original frame rate with motion detection overlaid — demonstrating Python multiprocessing and SharedMemory IPC
**Current focus:** Phase 1 - Pipeline

## Current Position

Phase: 1 of 3 (Pipeline)
Plan: 3 of 3 in current phase
Status: Phase 1 complete
Last activity: 2026-03-24 — Plan 01-03 complete

Progress: [███░░░░░░░] 33%

## Performance Metrics

**Velocity:**
- Total plans completed: 3
- Average duration: 1.7 min
- Total execution time: 0.08 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-pipeline | 3 | 5 min | 1.7 min |

**Recent Trend:**
- Last 5 plans: 01-01 (2 min), 01-02 (1 min), 01-03 (2 min)
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

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-24
Stopped at: Completed 01-pipeline 01-03-PLAN.md (Viewer process and Launcher — Phase 1 complete)
Resume file: None
