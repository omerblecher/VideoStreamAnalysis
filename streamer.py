"""
streamer.py — Streamer process for VideoStreamAnalysis pipeline.

Reads a video file frame-by-frame, writes each frame into a SharedMemory block,
and puts a ShmFrameMessage on the to_detector Queue.

SharedMemory lifecycle (Windows-compatible):
    - Streamer CREATES the block and keeps its handle open in open_handles.
    - On Windows, a SharedMemory block is destroyed when all handles are closed.
      Closing the Streamer's handle before the Detector attaches would cause a
      FileNotFoundError. The Streamer therefore holds its handle open until the
      Viewer signals completion via release_queue.
    - Detector attaches (create=False), copies the frame, closes its handle.
    - Viewer attaches, copies the frame, closes its handle, calls shm.unlink()
      (no-op on Windows; cleans up on Linux), then puts shm_name on release_queue.
    - Streamer receives the release signal, closes its handle, and the OS frees
      the block (Windows: ref-count drops to zero; Linux: already unlinked).
"""

import cv2
import numpy as np
from multiprocessing import Queue
from multiprocessing.shared_memory import SharedMemory

from ipc import ShmFrameMessage, EOS_SENTINEL, frame_shm_size


def run_streamer(video_path: str, to_detector: Queue, release_queue: Queue, stop_event) -> None:
    """Read video frames and forward them to the Detector via SharedMemory + Queue.

    Args:
        video_path:    Path to the video file to stream.
        to_detector:   Queue where ShmFrameMessage objects (and EOS_SENTINEL) are put.
        release_queue: Queue on which the Viewer puts shm_name strings after it has
                       finished with each frame. The Streamer waits for all releases
                       before exiting so its handles stay valid for downstream attach.
        stop_event:    multiprocessing.Event set by this process when EOF is reached,
                       signalling main that the stream is exhausted.

    Behaviour:
        - If the video cannot be opened, puts EOS_SENTINEL on to_detector and
          returns immediately so downstream processes do not hang.
        - Reads FPS from the video header; falls back to 25.0 if unavailable.
        - For each frame: allocates a SharedMemory block, writes the frame bytes,
          keeps the handle open, then enqueues a ShmFrameMessage.
        - After exhausting the video, puts EOS_SENTINEL on to_detector, then
          waits until every frame's release signal has been received before closing
          all remaining handles and returning.
    """
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        to_detector.put(EOS_SENTINEL)
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 25.0

    counter = 0
    # Maps shm_name -> SharedMemory handle; closed only after Viewer signals done.
    open_handles: dict[str, SharedMemory] = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            # Video exhausted
            break

        # Allocate a new SharedMemory block sized for this frame
        size = frame_shm_size(frame.shape, frame.dtype)
        shm = SharedMemory(create=True, size=size)

        # Write frame data into the shared block
        shared_array = np.ndarray(frame.shape, dtype=frame.dtype, buffer=shm.buf)
        shared_array[:] = frame

        # Keep handle open — closing here would destroy the block on Windows before
        # the Detector can attach.  Handle is closed after Viewer sends release signal.
        open_handles[shm.name] = shm

        # Build and enqueue the message
        msg = ShmFrameMessage(
            shm_name=shm.name,
            frame_shape=frame.shape,
            frame_dtype=str(frame.dtype),
            frame_index=counter,
            fps=fps,
        )
        to_detector.put(msg)

        counter += 1

    # Signal end-of-stream so Detector (and transitively Viewer) can shut down
    to_detector.put(EOS_SENTINEL)
    stop_event.set()
    cap.release()

    # Wait for Viewer to release each frame before closing handles and exiting.
    # This ensures our handles remain valid for the entire time Detector/Viewer
    # need to access each block.
    while open_handles:
        done_name = release_queue.get()
        shm = open_handles.pop(done_name, None)
        if shm is not None:
            shm.close()
