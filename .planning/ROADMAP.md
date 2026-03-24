# Roadmap: VideoStreamAnalysis

## Overview

Three phases matching the assignment structure: Phase 1 builds the full pipeline (Streamer → Detector → Viewer) with SharedMemory IPC and correct frame-rate playback; Phase 2 adds blur to detected motion regions; Phase 3 adds graceful shutdown propagation. Each phase ends with a git tag and push to GitHub.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work

- [x] **Phase 1: Pipeline** - Three-process pipeline running end-to-end with motion detection overlaid at original frame rate (assignment Phase A) (completed 2026-03-24)
- [ ] **Phase 2: Blurring** - Viewer blurs each detected motion region before drawing bounding boxes (assignment Phase B)
- [ ] **Phase 3: Shutdown** - All processes terminate cleanly when video ends with no resource leaks (assignment Phase C)

## Phase Details

### Phase 1: Pipeline
**Goal**: Three processes (Streamer, Detector, Viewer) run end-to-end delivering smooth annotated video playback
**Depends on**: Nothing (first phase)
**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05, PIPE-06, PIPE-07, IPC-01, IPC-02, IPC-03, GIT-01, GIT-02, GIT-03
**Success Criteria** (what must be TRUE):
  1. Running the pipeline plays the test video in a window at its original frame rate without stuttering
  2. Each frame displayed has a timestamp (HH:MM:SS) in the top-left corner
  3. Detected motion areas have bounding rectangles drawn by the Viewer (not the Detector)
  4. Frame data travels between processes via SharedMemory; contours/signals travel via Queue
  5. Codebase is committed, tagged `phase-a`, and pushed to GitHub with a commit message explaining the SharedMemory design decision
**Plans**: 4 plans

Plans:
- [x] 01-01-PLAN.md — IPC contracts (ipc.py) + Streamer process (streamer.py)
- [x] 01-02-PLAN.md — Detector process with VMD algorithm (detector.py)
- [x] 01-03-PLAN.md — Viewer process + launcher (viewer.py, main.py)
- [ ] 01-04-PLAN.md — End-to-end verification + git commit, tag phase-a, push to GitHub

### Phase 2: Blurring
**Goal**: Viewer blurs each motion region before annotating, making the feature visually verifiable
**Depends on**: Phase 1
**Requirements**: BLUR-01, BLUR-02
**Success Criteria** (what must be TRUE):
  1. Motion regions in the displayed video appear blurred (Gaussian or equivalent) inside their bounding rectangles
  2. Areas outside detected contours are not blurred
  3. Codebase is committed, tagged `phase-b`, and pushed to GitHub
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md — Add _blur_motion_regions to viewer.py (Gaussian blur per bounding rect)
- [ ] 02-02-PLAN.md — Visual verification + git commit, tag phase-b, push to GitHub

### Phase 3: Shutdown
**Goal**: The pipeline terminates itself cleanly when the video file ends, with no leftover processes or leaked SharedMemory
**Depends on**: Phase 2
**Requirements**: SHUT-01, SHUT-02, SHUT-03
**Success Criteria** (what must be TRUE):
  1. After the last frame is played, all three processes exit without manual intervention
  2. No zombie processes remain after the pipeline exits (verified via task manager or ps)
  3. SharedMemory blocks are released on exit (no "leaked semaphore" or unlinked shm warnings)
  4. Codebase is committed, tagged `phase-c`, and pushed to GitHub
**Plans**: TBD

## Progress

**Execution Order:** 1 → 2 → 3

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Pipeline | 4/4 | Complete   | 2026-03-24 |
| 2. Blurring | 0/2 | Not started | - |
| 3. Shutdown | 0/TBD | Not started | - |
