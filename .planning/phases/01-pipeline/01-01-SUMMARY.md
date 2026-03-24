---
phase: 01-pipeline
plan: 01
subsystem: ipc
tags: [python, multiprocessing, shared-memory, opencv, numpy, dataclasses]

# Dependency graph
requires: []
provides:
  - "IPC contracts: ShmFrameMessage, DetectorMessage, EOS_SENTINEL, frame_shm_size in ipc.py"
  - "Streamer process: run_streamer reads video, writes frames to SharedMemory, enqueues ShmFrameMessage"
affects: [02-detector, 03-viewer, 04-main]

# Tech tracking
tech-stack:
  added: [numpy, opencv-python]
  patterns: [shared-memory-producer, queue-message-dataclass, eos-sentinel-pattern]

key-files:
  created: [ipc.py, streamer.py]
  modified: []

key-decisions:
  - "EOS_SENTINEL = None as module constant so all processes share the same identity check (is EOS_SENTINEL)"
  - "Streamer closes shm handle but does not unlink — Viewer owns the unlink after display"
  - "fps fallback to 25.0 when cv2.CAP_PROP_FPS returns <= 0 to avoid zero-delay playback"
  - "numpy and opencv-python installed as first runtime dependencies"

patterns-established:
  - "IPC contracts module (ipc.py): single source of truth for all cross-process message types and helpers"
  - "SharedMemory producer pattern: create block, write via np.ndarray buffer, close handle, enqueue name"
  - "EOS sentinel: module-level None constant checked with 'is' comparison for safe shutdown signaling"

requirements-completed: [PIPE-01, PIPE-02, IPC-01, IPC-02, IPC-03]

# Metrics
duration: 2min
completed: 2026-03-24
---

# Phase 1 Plan 01: IPC Contracts and Streamer Process Summary

**SharedMemory IPC contracts (ipc.py) and Streamer producer (streamer.py) using dataclasses and multiprocessing.shared_memory**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-03-24T16:01:48Z
- **Completed:** 2026-03-24T16:03:30Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- `ipc.py` defines all cross-process contracts: `frame_shm_size`, `ShmFrameMessage`, `DetectorMessage`, and `EOS_SENTINEL`
- `streamer.py` implements `run_streamer` — reads video via OpenCV, allocates SharedMemory per frame, forwards messages via Queue
- All downstream processes (Detector, Viewer, main) can import ipc.py as single source of truth

## Task Commits

Each task was committed atomically:

1. **Task 1: IPC contracts module** - `0b2dc2e` (feat)
2. **Task 2: Streamer process** - `79bc5b6` (feat)

## Files Created/Modified
- `ipc.py` - IPC contracts: frame_shm_size helper, ShmFrameMessage and DetectorMessage dataclasses, EOS_SENTINEL constant
- `streamer.py` - Streamer process: reads video, writes frames to SharedMemory, enqueues ShmFrameMessage, sends EOS_SENTINEL at end

## Decisions Made
- EOS_SENTINEL is `None` (module-level constant) so all processes do `if msg is EOS_SENTINEL` — identity check, not equality
- Streamer closes its SharedMemory handle after writing but never unlinks; Viewer is responsible for cleanup after display
- FPS fallback to 25.0 when video header returns 0 or negative to prevent zero-delay or broken playback

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed numpy and opencv-python before Task 1 verification**
- **Found during:** Task 1 verification
- **Issue:** numpy not installed in environment; ipc.py import failed with ModuleNotFoundError
- **Fix:** Ran `pip install numpy opencv-python`
- **Files modified:** None (environment only)
- **Verification:** Import verification passed; frame_shm_size((480,640,3), 'uint8') returned 921600
- **Committed in:** 0b2dc2e (part of Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking — missing dependency)
**Impact on plan:** Required dependency install; no scope creep or architectural changes.

## Issues Encountered
- numpy not pre-installed in environment; resolved by installing numpy and opencv-python before Task 1 verification could complete.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- ipc.py provides the complete IPC contract for Plan 02 (Detector) and Plan 03 (Viewer)
- streamer.py is the complete producer end of the Streamer→Detector leg
- Plan 02 (Detector) can import from ipc.py and streamer.py immediately

## Self-Check: PASSED

- FOUND: ipc.py
- FOUND: streamer.py
- FOUND: .planning/phases/01-pipeline/01-01-SUMMARY.md
- FOUND commit: 0b2dc2e (feat(01-01): add IPC contracts module)
- FOUND commit: 79bc5b6 (feat(01-01): implement Streamer process)

---
*Phase: 01-pipeline*
*Completed: 2026-03-24*
