"""
viewer.py — Viewer process for VideoStreamAnalysis pipeline.

Consumes DetectorMessage from the Detector via a Queue, attaches to the
SharedMemory block containing the raw frame, annotates it with bounding
rectangles and a timestamp overlay, displays it at the original frame rate,
and finally unlinks (frees) the SharedMemory block.

The Viewer is the last consumer in the pipeline — it owns SharedMemory cleanup.
"""

import os
import cv2
import numpy as np
from multiprocessing import Queue
from multiprocessing.shared_memory import SharedMemory

from ipc import DetectorMessage, EOS_SENTINEL


def _read_frame(msg: DetectorMessage, release_queue: Queue) -> np.ndarray:
    """Attach to the SharedMemory block, copy the frame, then release it."""
    shm = SharedMemory(name=msg.shm_name, create=False)
    frame = np.ndarray(msg.frame_shape, dtype=msg.frame_dtype, buffer=shm.buf).copy()
    shm.close()
    shm.unlink()  # no-op on Windows; frees named block on Linux
    release_queue.put(msg.shm_name)
    return frame


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


def run_viewer(from_detector: Queue, video_path: str, release_queue: Queue) -> None:
    """Main loop for the Viewer process.

    Args:
        from_detector: Queue receiving DetectorMessage (or EOS_SENTINEL) from
                       the Detector process.
        video_path:    Path to the source video file, used only for the window title.
        release_queue: Queue on which this process puts each shm_name after it
                       has finished with the block, so the Streamer can close its
                       handle (required for Windows SharedMemory cleanup).
    """
    basename = os.path.basename(video_path)
    title: str | None = None

    while True:
        msg = from_detector.get()

        if msg is EOS_SENTINEL:
            cv2.destroyAllWindows()
            return

        if title is None:
            title = f"VideoStreamAnalysis \u2014 {basename} | {msg.fps:.0f}fps"
            cv2.namedWindow(title, cv2.WINDOW_NORMAL)

        frame = _read_frame(msg, release_queue)
        _draw_motion_boxes(frame, msg.contours)
        _draw_timestamp(frame, msg.frame_index, msg.fps)

        cv2.imshow(title, frame)
        cv2.waitKey(max(1, int(1000 / msg.fps)))
