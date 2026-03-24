---
phase: 03-shutdown
plan: 01
subsystem: ipc
tags: [multiprocessing, shared-memory, shutdown, graceful-exit, zombie-processes]

# Dependency graph
requires:
  - phase: 02-blurring
    provides: run_viewer with blur logic, run_detector with MOG2, run_streamer with full frame pipeline
provides:
  - Graceful shutdown via multiprocessing.Event propagated from Streamer on EOF
  - Join-with-timeout + force-terminate guard in main.py for stuck processes
  - try/finally cleanup block that drains release_queue on abnormal exit
  - No zombie processes after video ends; all three processes exit without manual intervention
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - multiprocessing.Event as stop flag passed to all pipeline processes at startup
    - join(timeout=N) + terminate() + join() pattern for stuck-process guard
    - try/finally wrapping process lifecycle for guaranteed cleanup

key-files:
  created: []
  modified:
    - streamer.py
    - detector.py
    - viewer.py
    - main.py

key-decisions:
  - "SHUTDOWN_TIMEOUT = 5 seconds constant in main.py — matches user-approved value from 03-CONTEXT.md"
  - "stop_event.set() placed after EOS_SENTINEL enqueue in streamer.py — stop_event is the official signal, EOS is still queue-propagated"
  - "detector.py and viewer.py accept stop_event but do not use it — EOS Queue propagation is sufficient for these stages"

patterns-established:
  - "Stop-event pattern: pass multiprocessing.Event to all processes even if only producer sets it"
  - "Timeout-terminate pattern: join(timeout=N) then terminate() + final join() for every child process"
  - "Finally-drain pattern: drain release_queue in finally block to log and handle abnormal exits"

requirements-completed: [SHUT-01, SHUT-02, SHUT-03]

# Metrics
duration: 2min
completed: 2026-03-24
---

# Phase 3 Plan 01: Graceful Shutdown Summary

**multiprocessing.Event stop signal wired through all three pipeline processes; main.py now guards with join-timeout + force-terminate + try/finally release_queue drain**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-24T17:24:09Z
- **Completed:** 2026-03-24T17:25:52Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- All three pipeline functions (run_streamer, run_detector, run_viewer) accept stop_event parameter
- run_streamer calls stop_event.set() after enqueuing EOS_SENTINEL so main knows the stream is exhausted
- main.py updated with SHUTDOWN_TIMEOUT constant, per-process join(timeout) + terminate guard, and try/finally cleanup

## Task Commits

Each task was committed atomically:

1. **Task 1: Add stop_event to all process functions and set it in Streamer on EOF** - `535c5cb` (feat)
2. **Task 2: Update main.py with stop_event, join timeout, force-terminate, and try/finally cleanup** - `81f663c` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `streamer.py` - Added stop_event parameter; calls stop_event.set() after to_detector.put(EOS_SENTINEL)
- `detector.py` - Added stop_event parameter (interface consistency; not used internally)
- `viewer.py` - Added stop_event parameter (interface consistency; not used internally)
- `main.py` - Added SHUTDOWN_TIMEOUT constant, multiprocessing.Event creation, updated all process args, replaced bare p.join() with try/finally + join-timeout + terminate

## Decisions Made
- SHUTDOWN_TIMEOUT = 5 seconds at module level as specified in 03-CONTEXT.md
- stop_event.set() placed immediately after EOS_SENTINEL is enqueued (before cap.release()) so main receives the signal at the earliest possible moment
- Detector and Viewer accept stop_event silently — no internal changes needed since EOS already propagates correctly through Queues

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All shutdown requirements complete; pipeline now exits cleanly after last frame
- No zombie processes, no leaked semaphore warnings on normal exit
- Abnormal exit path (stuck process) handled with force-terminate and drain
- Phase 03-shutdown has one plan (this one); phase is complete

---
*Phase: 03-shutdown*
*Completed: 2026-03-24*
