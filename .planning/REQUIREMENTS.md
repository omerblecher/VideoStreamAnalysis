# Requirements: VideoStreamAnalysis

**Defined:** 2026-03-24
**Core Value:** A smooth, correctly pipelined video display at original frame rate with motion detection overlaid — demonstrating Python multiprocessing and SharedMemory IPC

## v1 Requirements

Requirements for all three assignment phases.

### Pipeline (Phase A)

- [x] **PIPE-01**: Streamer process reads a local video file path and extracts frames sequentially
- [x] **PIPE-02**: Streamer sends each frame to Detector via SharedMemory + Queue
- [x] **PIPE-03**: Detector receives each frame and runs motion detection using basic_vmd.py algorithm (frame differencing, threshold, dilate, findContours)
- [x] **PIPE-04**: Detector sends frame + contours metadata to Viewer via SharedMemory + Queue — Detector must NOT draw on the frame
- [x] **PIPE-05**: Viewer draws bounding rectangles around each detected contour on the frame
- [x] **PIPE-06**: Viewer overlays current timestamp (HH:MM:SS) in the top-left corner of each frame
- [x] **PIPE-07**: Viewer displays the annotated video on screen at the original video frame rate (smooth, not stuttering or sped up)

### Blurring (Phase B)

- [x] **BLUR-01**: Viewer applies a blur (e.g. Gaussian) to each detected motion region before drawing bounding boxes
- [x] **BLUR-02**: Blurring is applied only within the bounding rectangle of each contour

### Shutdown (Phase C)

- [x] **SHUT-01**: When the video ends (Streamer exhausts all frames), a shutdown signal propagates through the pipeline
- [x] **SHUT-02**: All three processes (Streamer, Detector, Viewer) terminate cleanly on video end
- [x] **SHUT-03**: No zombie processes or resource leaks (SharedMemory cleaned up)

### IPC Design

- [x] **IPC-01**: Frame data is transferred between processes via `multiprocessing.SharedMemory` (zero-copy for large NumPy arrays)
- [x] **IPC-02**: Metadata (contours, frame shape, dtype, shutdown sentinel) is transferred via `multiprocessing.Queue`
- [x] **IPC-03**: A Queue sentinel value (e.g. `None`) signals end-of-stream to downstream processes

### Git / Delivery

- [x] **GIT-01**: Each phase is committed and pushed to `github.com/omerblecher`
- [x] **GIT-02**: Each phase has a git tag (`phase-a`, `phase-b`, `phase-c`)
- [x] **GIT-03**: Each commit/tag includes a description explaining design decisions (e.g. why SharedMemory was chosen)

## v2 Requirements

### Future

- **V2-01**: Support URL-based video streams (RTSP, HTTP)
- **V2-02**: Multiple detector algorithms selectable at runtime
- **V2-03**: Recording output to file

## Out of Scope

| Feature | Reason |
|---------|--------|
| Drawing in Detector | Explicitly forbidden by assignment |
| Detection parameter tuning | Assignment says use algorithm as-is |
| Web/mobile UI | Display via OpenCV window only |
| Multi-camera support | Single video file per run |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-01 | Phase 1 | Complete |
| PIPE-02 | Phase 1 | Complete |
| PIPE-03 | Phase 1 | Complete |
| PIPE-04 | Phase 1 | Complete |
| PIPE-05 | Phase 1 | Complete |
| PIPE-06 | Phase 1 | Complete |
| PIPE-07 | Phase 1 | Complete |
| IPC-01 | Phase 1 | Complete |
| IPC-02 | Phase 1 | Complete |
| IPC-03 | Phase 1 | Complete |
| GIT-01 | Phase 1 | Complete |
| GIT-02 | Phase 1 | Complete |
| GIT-03 | Phase 1 | Complete |
| BLUR-01 | Phase 2 | Complete |
| BLUR-02 | Phase 2 | Complete |
| SHUT-01 | Phase 3 | Complete |
| SHUT-02 | Phase 3 | Complete |
| SHUT-03 | Phase 3 | Complete |

**Coverage:**
- v1 requirements: 18 total
- Mapped to phases: 18
- Unmapped: 0 (100% coverage)

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 after 01-03 plan completion (PIPE-05, PIPE-06, PIPE-07 complete)*
