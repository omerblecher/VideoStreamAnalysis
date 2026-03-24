# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Smooth, correctly pipelined video display at original frame rate with motion detection overlaid — demonstrating Python multiprocessing and SharedMemory IPC
**Current focus:** Phase 1 - Pipeline

## Current Position

Phase: 1 of 3 (Pipeline)
Plan: 2 of 3 in current phase
Status: In progress
Last activity: 2026-03-24 — Plan 01-02 complete

Progress: [██░░░░░░░░] 20%

## Performance Metrics

**Velocity:**
- Total plans completed: 2
- Average duration: 1.5 min
- Total execution time: 0.05 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-pipeline | 2 | 3 min | 1.5 min |

**Recent Trend:**
- Last 5 plans: 01-01 (2 min), 01-02 (1 min)
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

### Pending Todos

None yet.

### Blockers/Concerns

None yet.

## Session Continuity

Last session: 2026-03-24
Stopped at: Completed 01-pipeline 01-02-PLAN.md (Detector process)
Resume file: None
