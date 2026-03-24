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

import logging
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
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("streamer")

    # Maps shm_name -> SharedMemory handle; closed only after Viewer signals done.
    open_handles: dict[str, SharedMemory] = {}

    try:
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            logger.error("Cannot open video: %s", video_path)
            to_detector.put(EOS_SENTINEL)
            stop_event.set()
            return

        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            logger.warning("Could not read FPS from video header; defaulting to 25.0")
            fps = 25.0

        logger.info("Opened '%s' at %.1f fps", video_path, fps)

        counter = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            try:
                size = frame_shm_size(frame.shape, frame.dtype)
                shm = SharedMemory(create=True, size=size)
            except OSError as exc:
                logger.error("Failed to allocate SharedMemory for frame %d: %s — skipping", counter, exc)
                counter += 1
                continue

            shared_array = np.ndarray(frame.shape, dtype=frame.dtype, buffer=shm.buf)
            shared_array[:] = frame

            # Keep handle open — closing here would destroy the block on Windows before
            # the Detector can attach.  Handle is closed after Viewer sends release signal.
            open_handles[shm.name] = shm

            msg = ShmFrameMessage(
                shm_name=shm.name,
                frame_shape=frame.shape,
                frame_dtype=str(frame.dtype),
                frame_index=counter,
                fps=fps,
            )
            to_detector.put(msg)
            counter += 1

        cap.release()
        logger.info("Video exhausted after %d frame(s) — sending EOS", counter)

        to_detector.put(EOS_SENTINEL)
        stop_event.set()

        # Wait for Viewer to release each frame before closing handles and exiting.
        # This ensures our handles remain valid for the entire time Detector/Viewer
        # need to access each block.
        while open_handles:
            try:
                done_name = release_queue.get()
            except Exception as exc:
                logger.error("Error reading release_queue: %s — aborting handle cleanup", exc)
                break
            shm = open_handles.pop(done_name, None)
            if shm is not None:
                shm.close()

        logger.info("All SharedMemory handles released — exiting")

    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as exc:
        logger.exception("Unexpected error in streamer: %s", exc)
    finally:
        # Guarantee EOS and stop_event are always signalled even after an unexpected error,
        # so downstream processes and main() are never left waiting.
        if not stop_event.is_set():
            logger.warning("Streamer exiting abnormally — signalling stop_event and EOS")
            try:
                to_detector.put(EOS_SENTINEL)
            except Exception:
                pass
            stop_event.set()
        # Close any handles that were not released normally.
        for shm in open_handles.values():
            try:
                shm.close()
            except Exception:
                pass
