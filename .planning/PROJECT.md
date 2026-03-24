# VideoStreamAnalysis

## What This Is

A Python multi-process video stream analysis pipeline built as a job interview assignment. Three independent processes — Streamer, Detector, and Viewer — are connected in a pipeline that reads video frames, detects motion, and displays results with overlaid annotations in real time.

## Core Value

A smooth, correctly pipelined video display at original frame rate, with motion detection overlaid — demonstrating mastery of Python multiprocessing, shared memory, and IPC.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Streamer process reads video frame-by-frame and sends frames to Detector
- [ ] Detector process runs motion detection (basic_vmd.py algorithm) and sends frame + contours to Viewer
- [ ] Detector must NOT draw on frames
- [ ] Viewer process draws bounding boxes on detected motion areas
- [ ] Viewer writes current timestamp to top-left corner of each frame
- [ ] Viewer displays the video on screen at original frame rate (smooth playback)
- [ ] Viewer blurs each detected motion area (Phase B)
- [ ] System shuts down all processes gracefully when video ends (Phase C)

### Out of Scope

- Improving detection quality/parameters — use basic_vmd.py as-is
- Mobile or web UI — display via OpenCV window only
- Recording/saving output video — display only
- URL-based streaming — local file path only for this assignment

## Context

- Interview assignment with 3 phases (A: pipeline, B: blurring, C: shutdown)
- Each phase must be Git-tagged separately; GitHub repo: https://github.com/omerblecher
- Test video: `C:\code\VideoStreamAnalysis\People – 6387.mp4`
- `basic_vmd.py` already exists — uses frame differencing + contour detection (cv2.absdiff, threshold, dilate, findContours)
- Virtual environment already set up at `.venv/`
- Time constraint: ~3 hours total

## Constraints

- **Language**: Python only
- **IPC**: `multiprocessing.SharedMemory` for frame data + `multiprocessing.Queue` for signaling/coordination — demonstrates GIL awareness, memory efficiency for 1920×1080 arrays at video frame rate
- **Libraries**: OpenCV, NumPy, imutils (already implied by basic_vmd.py)
- **Architecture**: Strictly 3 separate processes; only Viewer draws on frames
- **Synchronization**: Viewer must not fall behind Streamer; playback must match original frame rate

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| SharedMemory for frames | Avoids copying large NumPy arrays between processes — 1920×1080 BGR frame is ~6MB; copying every frame would bottleneck pipeline | — Pending |
| Queue for metadata/signals | Lightweight signaling for contours, frame indices, and shutdown signals; coordinates flow without frame data overhead | — Pending |
| Queue per pipeline stage | Streamer→Detector queue, Detector→Viewer queue — clean separation, natural backpressure | — Pending |
| basic_vmd.py used as-is | Assignment requirement — no parameter tuning | — Pending |

---
*Last updated: 2026-03-24 after initialization*
