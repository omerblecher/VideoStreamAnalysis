---
phase: 01-pipeline
verified: 2026-03-24T18:45:00Z
status: human_needed
score: 12/13 must-haves verified
re_verification: false
human_verification:
  - test: "Run: python main.py \"People - 6387.mp4\" and observe the window"
    expected: "Video plays smoothly at original frame rate with green bounding rectangles labeled 'motion' around moving objects, HH:MM:SS timestamp in top-left on dark background, window title contains filename and fps"
    why_human: "Visual playback quality, frame rate smoothness, and motion detection accuracy cannot be verified by static code analysis"
---

# Phase 1: Pipeline Verification Report

**Phase Goal:** Three processes (Streamer, Detector, Viewer) run end-to-end delivering smooth annotated video playback
**Verified:** 2026-03-24T18:45:00Z
**Status:** human_needed — all automated checks pass; one success criterion (end-to-end visual playback) requires human confirmation
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (from ROADMAP.md Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Pipeline plays test video in a window at original frame rate without stuttering | ? HUMAN | viewer.py uses `cv2.waitKey(max(1, int(1000/msg.fps)))` — timing logic correct; actual smoothness needs human observation |
| 2 | Each frame has a HH:MM:SS timestamp in the top-left corner | VERIFIED | `_draw_timestamp()` in viewer.py computes elapsed from `frame_index/fps`, formats `HH:MM:SS`, draws white text on (30,30,30) background rect at (10,10) |
| 3 | Detected motion areas have bounding rectangles drawn by Viewer (not Detector) | VERIFIED | `_draw_motion_boxes()` in viewer.py draws `cv2.rectangle` + label; detector.py has zero drawing calls (confirmed by grep) |
| 4 | Frame data travels via SharedMemory; contours/signals travel via Queue | VERIFIED | Streamer creates `SharedMemory(create=True)`, forwards `shm_name` in `ShmFrameMessage`; Detector attaches `create=False`, copies frame, forwards `shm_name` in `DetectorMessage`; Viewer attaches, reads, unlinks; contours in Queue message |
| 5 | Codebase committed, tagged `phase-a`, pushed to GitHub with SharedMemory design commit message | VERIFIED | Tag `phase-a` confirmed on `origin` via `git ls-remote`; commit `4791b1b` contains full SharedMemory design explanation (IPC rationale, zero-copy reasoning, Queue role) |

**Score (automated): 4/5 truths verified; 1 needs human**

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ipc.py` | IPC contracts: `ShmFrameMessage`, `DetectorMessage`, `EOS_SENTINEL`, `frame_shm_size` | VERIFIED | All four exports present; dataclasses with correct fields; `EOS_SENTINEL = None` at module level |
| `streamer.py` | Streamer process — reads video, writes frames to SharedMemory, enqueues `ShmFrameMessage` | VERIFIED | `run_streamer(video_path, to_detector, release_queue)` — opens VideoCapture, creates SharedMemory per frame, enqueues `ShmFrameMessage`, sends `EOS_SENTINEL` at end |
| `detector.py` | Detector process — consumes `ShmFrameMessage`, runs MOG2 VMD, produces `DetectorMessage` | VERIFIED | `run_detector(from_streamer, to_viewer)` — MOG2 via `createBackgroundSubtractorMOG2()`, Gaussian blur, dilation, contour area filter at 500 px²; no drawing calls |
| `viewer.py` | Viewer process — reads frames from SharedMemory, annotates, displays at correct frame rate | VERIFIED | `run_viewer(from_detector, video_path, release_queue)` — attaches by shm_name, copies frame, calls `shm.unlink()`, draws motion boxes and timestamp, `cv2.waitKey(fps-delay)` |
| `main.py` | Launcher — parses CLI args, spawns Streamer/Detector/Viewer, joins all processes | VERIFIED | CLI validation for arg count and file existence; spawns 3 processes with correct Queue wiring including `release_queue`; joins all |
| `.git` (tag `phase-a`) | Git repository with annotated `phase-a` tag pushed to remote | VERIFIED | `git tag -v phase-a` confirms annotated tag; `git ls-remote --tags origin` returns `refs/tags/phase-a` at commit `4791b1b` |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `streamer.py` | `ipc.py` | `from ipc import ShmFrameMessage, EOS_SENTINEL, frame_shm_size` | VERIFIED | Line 25 of streamer.py |
| `streamer.py` | `multiprocessing.SharedMemory` | `SharedMemory(create=True, size=size)` | VERIFIED | Line 70 of streamer.py; holds handle in `open_handles` dict until release signal |
| `detector.py` | `ipc.py` | `from ipc import ShmFrameMessage, DetectorMessage, EOS_SENTINEL` | VERIFIED | Line 16 of detector.py |
| `detector.py` | `multiprocessing.SharedMemory` | `SharedMemory(name=msg.shm_name, create=False)` | VERIFIED | Line 51 of detector.py |
| `viewer.py` | `ipc.py` | `from ipc import DetectorMessage, EOS_SENTINEL` | VERIFIED | Line 18 of viewer.py |
| `viewer.py` | `multiprocessing.SharedMemory` | `SharedMemory(name=msg.shm_name, create=False)` + `shm.unlink()` | VERIFIED | Lines 23-26 of viewer.py; Viewer is the last consumer and calls unlink |
| `main.py` | `streamer.py, detector.py, viewer.py` | `multiprocessing.Process(target=run_X, ...)` | VERIFIED | Lines 39-41 of main.py; all three processes spawned with correct argument order |
| `git tag phase-a` | `github.com/omerblecher` | `git push origin phase-a` | VERIFIED | `git ls-remote --tags origin` returned `refs/tags/phase-a` pointing to `4791b1b` |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PIPE-01 | 01-01 | Streamer reads local video file path and extracts frames sequentially | SATISFIED | `cv2.VideoCapture(video_path)` + `cap.read()` loop in streamer.py |
| PIPE-02 | 01-01 | Streamer sends each frame to Detector via SharedMemory + Queue | SATISFIED | `SharedMemory(create=True)` + `to_detector.put(ShmFrameMessage(...))` in streamer.py |
| PIPE-03 | 01-02 | Detector receives frame and runs motion detection (frame differencing / threshold / dilate / findContours) | SATISFIED | `createBackgroundSubtractorMOG2` + Gaussian blur + dilate + `findContours` in detector.py (`_detect_motion` helper) |
| PIPE-04 | 01-02 | Detector sends frame + contours to Viewer via SharedMemory + Queue; Detector must NOT draw on frame | SATISFIED | `DetectorMessage` forwarded with original `shm_name`; zero drawing calls in detector.py confirmed by grep |
| PIPE-05 | 01-03 | Viewer draws bounding rectangles around each detected contour | SATISFIED | `_draw_motion_boxes()` calls `cv2.rectangle` and `cv2.putText("motion")` per contour |
| PIPE-06 | 01-03 | Viewer overlays current timestamp (HH:MM:SS) in top-left corner | SATISFIED | `_draw_timestamp()` formats and draws HH:MM:SS with dark background rect at (10,10) |
| PIPE-07 | 01-03 | Viewer displays annotated video at original video frame rate | SATISFIED (code) / HUMAN (behavior) | `cv2.waitKey(max(1, int(1000/msg.fps)))` derives delay from forwarded fps; actual smoothness requires human observation |
| IPC-01 | 01-01 | Frame data transferred between processes via `multiprocessing.SharedMemory` | SATISFIED | All three processes use `SharedMemory`; no frame bytes go through Queue |
| IPC-02 | 01-01 | Metadata (contours, frame shape, dtype, shutdown sentinel) transferred via `multiprocessing.Queue` | SATISFIED | `ShmFrameMessage` and `DetectorMessage` carry all metadata via Queue |
| IPC-03 | 01-01 | Queue sentinel value (None) signals end-of-stream | SATISFIED | `EOS_SENTINEL = None` in ipc.py; checked with `is` in all three processes |
| GIT-01 | 01-04 | Phase committed and pushed to `github.com/omerblecher` | SATISFIED | Remote `origin` = `https://github.com/omerblecher/VideoStreamAnalysis.git`; `git ls-remote` confirmed push succeeded |
| GIT-02 | 01-04 | Phase has git tag `phase-a` | SATISFIED | Annotated tag `phase-a` exists locally and on remote |
| GIT-03 | 01-04 | Commit/tag includes description explaining design decisions (why SharedMemory) | SATISFIED | Commit `4791b1b` body explains zero-copy rationale, Queue-for-metadata separation, per-frame unlink lifecycle |

**All 13 requirements accounted for. No orphaned requirements.**

---

### Architectural Deviation from Plan (Notable, Not a Gap)

The final code diverges from the original `01-01-PLAN.md` and `01-03-PLAN.md` signatures in one respect:

- **Plan specified:** `run_streamer(video_path, to_detector)` and `run_viewer(from_detector, video_path)` (2 args each)
- **Actual code:** `run_streamer(video_path, to_detector, release_queue)` and `run_viewer(from_detector, video_path, release_queue)` (3 args each)

**Reason:** On Windows, a `SharedMemory` block is destroyed when the last handle closes. The original design had Streamer close its handle immediately after enqueueing, which would cause a `FileNotFoundError` when the Detector or Viewer later attempts to attach. The `release_queue` is a back-channel from Viewer to Streamer: Viewer puts the `shm_name` after it finishes with each block; Streamer holds its handle open until it receives that signal.

**Verdict:** This is a correct Windows-compatibility fix. All three processes are consistently updated; `main.py` wires `release_queue` to both Streamer and Viewer. The IPC contract still holds — frame data moves via SharedMemory, coordination via Queue, and EOS_SENTINEL propagates correctly.

---

### Anti-Patterns Found

No TODO/FIXME/PLACEHOLDER/HACK comments found in any source file.
No empty return stubs (`return null`, `return {}`, `return []`) found.
No console-log-only handlers found.
No drawing calls in `detector.py` confirmed by grep.
No `absdiff` or `prev_gray` (frame-differencing) in `detector.py` confirmed by grep.

---

### Human Verification Required

#### 1. End-to-End Visual Playback

**Test:** Run `python main.py "People - 6387.mp4"` (or any test video) from `C:/code/VideoStreamAnalysis`

**Expected:**
1. An OpenCV window opens titled `VideoStreamAnalysis — <filename> | <N>fps`
2. Video plays smoothly at its original frame rate — no obvious fast-forward, no stutter
3. HH:MM:SS timestamp visible in the top-left corner, white text on a dark background
4. Green bounding rectangles labeled "motion" appear around moving objects/people
5. No false bounding boxes when nothing moves
6. Window closes (or process terminates naturally) when the video finishes

**Why human:** Frame rate smoothness is perceptual. Motion detection accuracy (true positive / false positive rate) depends on video content. Window lifecycle after EOS requires live observation. None of these can be confirmed by static code analysis.

---

### Gaps Summary

No gaps. All code is substantive and wired. The one open item (end-to-end visual playback) requires human observation and cannot be automated.

The `release_queue` architectural deviation is an improvement over the original plan, not a defect — it is correctly implemented across all three files and main.py.

---

_Verified: 2026-03-24T18:45:00Z_
_Verifier: Claude (gsd-verifier)_
