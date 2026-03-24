# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Smooth, correctly pipelined video display at original frame rate with motion detection overlaid — demonstrating Python multiprocessing and SharedMemory IPC
**Current focus:** Phase 1 - Pipeline

## Current Position

Phase: 1 of 3 (Pipeline)
Plan: 4 of 4 in current phase
Status: Phase 1 complete (all plans done; push to GitHub pending user action)
Last activity: 2026-03-24 — Plan 01-04 complete

Progress: [████░░░░░░] 40%

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: 1.75 min
- Total execution time: 0.09 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-pipeline | 4 | 10 min | 2.5 min |

**Recent Trend:**
- Last 5 plans: 01-01 (2 min), 01-02 (1 min), 01-03 (2 min), 01-04 (5 min)
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

### Pending Todos

None yet.

### Blockers/Concerns

- GitHub repository https://github.com/omerblecher/VideoStreamAnalysis does not exist yet — user must create it and then run `git push -u origin master && git push origin phase-a`

## Session Continuity

Last session: 2026-03-24
Stopped at: Completed 01-pipeline 01-04-PLAN.md (Git commit + tag phase-a; push pending GitHub repo creation)
Resume file: None
