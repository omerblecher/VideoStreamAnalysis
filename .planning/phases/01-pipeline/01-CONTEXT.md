# Phase 1: Pipeline - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Three processes (Streamer, Detector, Viewer) run end-to-end delivering smooth annotated video playback. Streamer reads frames from a video file and puts them in SharedMemory; Detector reads from SharedMemory and sends contours via Queue; Viewer reads from SharedMemory and Queue to display annotated frames at original frame rate. Blurring, shutdown, and any UI beyond the display window are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Launch & Startup
- Single launcher script — `main.py` spawns all three processes automatically
- Video file path is a required CLI argument: `python main.py video.mp4`
- If the video file isn't found or the pipeline fails to start, print a clear error message and exit with a non-zero exit code

### Annotation Appearance
- Bounding boxes: green, 2px thick
- Bounding boxes include a "motion" label
- Timestamp (HH:MM:SS) in top-left corner: white text with a dark background for legibility on any frame content

### Motion Detection Tuning
- Background subtractor: MOG2
- Apply Gaussian blur to frames before background subtraction (noise reduction)
- Filter out small contours below a minimum area threshold (e.g., 500px²) to reduce noise
- Dilate and merge nearby contours before sending to Viewer (fewer, cleaner bounding boxes)

### Frame Rate Control
- Viewer uses `cv2.waitKey` with delay calculated from video FPS (ms per frame)
- Streamer reads FPS from the video file (`cv2.CAP_PROP_FPS`) and passes it to other processes
- Viewer waits for every frame — never drops frames, even if detection is slow
- Playback window title shows filename and FPS: e.g., "VideoStreamAnalysis — video.mp4 | 30fps"

### Claude's Discretion
- Exact minimum contour area threshold value
- Dilation kernel size for merging contours
- Timestamp font size and exact padding/position
- SharedMemory layout (how frame dimensions and metadata are communicated alongside pixel data)
- Queue message format for contour data and end-of-stream signals

</decisions>

<specifics>
## Specific Ideas

No specific references given — open to standard OpenCV/multiprocessing patterns.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-pipeline*
*Context gathered: 2026-03-24*
