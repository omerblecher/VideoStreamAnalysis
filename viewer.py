"""
viewer.py — Viewer process for VideoStreamAnalysis pipeline.

Consumes DetectorMessage from the Detector via a Queue, attaches to the
SharedMemory block containing the raw frame, annotates it with bounding
rectangles and a timestamp overlay, displays it at the original frame rate,
and finally unlinks (frees) the SharedMemory block.

The Viewer is the last consumer in the pipeline — it owns SharedMemory cleanup.
"""

import logging
import os
import cv2
import numpy as np
from multiprocessing import Queue
from multiprocessing.shared_memory import SharedMemory

from ipc import DetectorMessage, EOS_SENTINEL

# Blur kernel size as a fraction of the bounding box's smaller dimension.
# Produces a kernel of ~20 % of the smaller side, clamped to [3, 99] and
# forced to be odd (required by GaussianBlur).
BLUR_KERNEL_FRACTION = 0.2


def _read_frame(msg: DetectorMessage, release_queue: Queue, logger: logging.Logger):
    """Attach to the SharedMemory block, copy the frame, then release it.

    Returns the frame as a numpy array, or None if the block could not be
    opened (e.g. race condition on abnormal shutdown).  The release signal is
    sent to release_queue in both cases so the Streamer is never left waiting.
    """
    try:
        shm = SharedMemory(name=msg.shm_name, create=False)
        frame = np.ndarray(msg.frame_shape, dtype=msg.frame_dtype, buffer=shm.buf).copy()
        shm.close()
        shm.unlink()  # no-op on Windows; frees named block on Linux
    except FileNotFoundError:
        logger.warning("SharedMemory block '%s' not found for frame %d — skipping display",
                       msg.shm_name, msg.frame_index)
        release_queue.put(msg.shm_name)
        return None
    except Exception as exc:
        logger.error("Error reading frame %d from SharedMemory: %s", msg.frame_index, exc)
        release_queue.put(msg.shm_name)
        return None

    release_queue.put(msg.shm_name)
    return frame


def _blur_motion_regions(frame: np.ndarray, contours: list) -> None:
    """Gaussian-blur the bounding rectangle of each motion contour in-place.

    Blur is applied only within the bounding rectangle (BLUR-02).
    Coordinates are clipped to frame bounds so partial off-edge boxes are safe.
    Kernel size scales with the bounding box (proportional to BLUR_KERNEL_FRACTION),
    clamped to odd values in [3, 99].
    Overlapping bounding rectangles are each blurred independently; double-blur
    in overlap zones is acceptable.
    """
    h, w = frame.shape[:2]
    for c in contours:
        x, y, bw, bh = cv2.boundingRect(c)
        # Clip to frame bounds
        x1, y1 = max(0, x), max(0, y)
        x2, y2 = min(w, x + bw), min(h, y + bh)
        if x2 <= x1 or y2 <= y1:
            continue  # degenerate / fully out of frame — skip
        # Proportional kernel: fraction of the smaller bbox dimension, clamped to [3, 99]
        k = max(3, min(99, int(min(bw, bh) * BLUR_KERNEL_FRACTION)))
        frame[y1:y2, x1:x2] = cv2.blur(frame[y1:y2, x1:x2], (k, k))


def _draw_motion_boxes(frame: np.ndarray, contours: list) -> None:
    """Draw green bounding rectangles with 'motion' labels in-place."""
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        label_y = y - 5 if y - 5 > 10 else y + 15
        cv2.putText(frame, "motion", (x, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)


def _draw_timestamp(frame: np.ndarray, frame_index: int, fps: float) -> None:
    """Overlay HH:MM:SS timestamp in the top-left corner with a dark background."""
    elapsed = int(frame_index / fps)
    ts = f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"

    font, font_scale, thickness = cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2
    (text_w, text_h), baseline = cv2.getTextSize(ts, font, font_scale, thickness)

    pad = 4
    x0, y0 = 10, 10
    cv2.rectangle(frame, (x0, y0), (x0 + text_w + pad * 2, y0 + text_h + baseline + pad * 2), (30, 30, 30), cv2.FILLED)
    cv2.putText(frame, ts, (x0 + pad, y0 + pad + text_h), font, font_scale, (255, 255, 255), thickness)


def run_viewer(from_detector: Queue, video_path: str, release_queue: Queue, stop_event) -> None:
    """Main loop for the Viewer process.

    Args:
        from_detector: Queue receiving DetectorMessage (or EOS_SENTINEL) from
                       the Detector process.
        video_path:    Path to the source video file, used only for the window title.
        release_queue: Queue on which this process puts each shm_name after it
                       has finished with the block, so the Streamer can close its
                       handle (required for Windows SharedMemory cleanup).
        stop_event:    multiprocessing.Event accepted for interface consistency
                       but not used; EOS propagates via Queue and triggers
                       cv2.destroyAllWindows on receipt.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("viewer")
    logger.info("Viewer started")

    basename = os.path.basename(video_path)
    title: str | None = None
    displayed = 0

    try:
        while True:
            msg = from_detector.get()

            if msg is EOS_SENTINEL:
                logger.info("EOS received — displayed %d frame(s)", displayed)
                cv2.destroyAllWindows()
                return

            frame = _read_frame(msg, release_queue, logger)
            if frame is None:
                continue  # SharedMemory read failed; release signal already sent

            try:
                if title is None:
                    title = f"VideoStreamAnalysis \u2014 {basename} | {msg.fps:.0f}fps"
                    cv2.namedWindow(title, cv2.WINDOW_NORMAL)

                _blur_motion_regions(frame, msg.contours)
                _draw_motion_boxes(frame, msg.contours)
                _draw_timestamp(frame, msg.frame_index, msg.fps)

                cv2.imshow(title, frame)
                cv2.waitKey(max(1, int(1000 / msg.fps)))
                displayed += 1
            except Exception as exc:
                logger.error("Display error on frame %d: %s — skipping", msg.frame_index, exc)

    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as exc:
        logger.exception("Unexpected error in viewer: %s", exc)
    finally:
        cv2.destroyAllWindows()
