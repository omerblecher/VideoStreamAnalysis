# VideoStreamAnalysis

A real-time video motion detection pipeline built with Python multiprocessing and shared memory.

## Overview

The pipeline runs three independent OS processes connected by queues:

```
Video file
    │
    ▼
┌─────────┐   ShmFrameMessage   ┌──────────┐   DetectorMessage   ┌────────┐
│ Streamer│ ─────────────────►  │ Detector │ ──────────────────► │ Viewer │
└─────────┘    (Queue + SHM)    └──────────┘    (Queue + SHM)    └────────┘
    ▲                                                                  │
    └──────────────── release_queue (shm_name) ───────────────────────┘
```

- **Streamer** — reads frames from the video file, writes each into a `SharedMemory` block, and puts a reference message on the queue.
- **Detector** — attaches to each shared block, runs MOG2 background subtraction to find motion contours, and forwards the annotated message to the Viewer.
- **Viewer** — attaches to the shared block, draws bounding boxes and a timestamp overlay, displays the frame at the correct playback speed, then releases the shared memory.

Shared memory is used to avoid copying raw frame data through queues. Each block is kept alive by the Streamer until the Viewer signals it is done via `release_queue` — required on Windows where blocks are destroyed when the last handle closes.

## Requirements

- Python 3.10+
- [OpenCV](https://pypi.org/project/opencv-python/) (`opencv-python`)
- [NumPy](https://pypi.org/project/numpy/) (`numpy`)

Install dependencies:

```bash
pip install opencv-python numpy
```

## Usage

```bash
python main.py <video_path>
```

**Example:**

```bash
python main.py sample.mp4
```

The video window opens automatically. It closes and the terminal returns to a prompt when the last frame has been displayed. Press **Ctrl+C** at any time to stop the pipeline cleanly.

## Project structure

```
VideoStreamAnalysis/
├── main.py       — entry point; spawns and joins the three processes
├── streamer.py   — Streamer process
├── detector.py   — Detector process (MOG2 motion detection)
├── viewer.py     — Viewer process (annotation + display)
└── ipc.py        — shared IPC contracts (message dataclasses, EOS sentinel)
```

## Design notes

### Shutdown sequence

The Streamer signals EOF via `multiprocessing.Event` (`stop_event`) as soon as it finishes reading the video. `main.py` waits on this event before joining processes. Processes are joined in dependency order — Detector → Viewer → Streamer — so the Streamer's shared memory handles remain valid until the Viewer has released every frame.

### Logging

Each process configures its own `logging` handler (processes do not share file descriptors). Log output goes to `stderr` in the format:

```
HH:MM:SS [process_name] LEVEL message
```

### Error handling

- **SharedMemory failures** — if a block cannot be opened in the Detector or Viewer, the frame is skipped and a release signal is still sent to the Streamer so it is never left waiting.
- **Unexpected process errors** — each process wraps its main loop in `try/except` and guarantees EOS is forwarded in the `finally` block so downstream processes are not left hanging.
- **Ctrl+C** — `main.py` catches `KeyboardInterrupt`, terminates all child processes, and exits with code 130.
