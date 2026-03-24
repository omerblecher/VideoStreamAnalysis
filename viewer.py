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


def run_viewer(from_detector: Queue, video_path: str) -> None:
    """Main loop for the Viewer process.

    Reads DetectorMessage objects from *from_detector*, annotates frames with
    green bounding boxes and an HH:MM:SS timestamp, displays them at the
    original frame rate, and frees each SharedMemory block after display.

    Args:
        from_detector: Queue receiving DetectorMessage (or EOS_SENTINEL) from
                       the Detector process.
        video_path:    Path to the source video file, used only for the window
                       title (filename + FPS).
    """
    # Window title is set once before the loop.  We use a placeholder fps value
    # here and update it after the first real message so the window is already
    # open and named consistently.  The namedWindow call below sets it up.
    basename = os.path.basename(video_path)

    # We don't know FPS until the first message arrives, so defer title creation
    # until then.  Use a sentinel to track whether the window has been created.
    title: str | None = None

    while True:
        msg = from_detector.get()  # blocks until a message is available

        # --- End-of-stream: clean up window and exit ---
        if msg is EOS_SENTINEL:
            cv2.destroyAllWindows()
            return

        # --- Create window on first real message (FPS now known) ---
        if title is None:
            title = f"VideoStreamAnalysis \u2014 {basename} | {msg.fps:.0f}fps"
            cv2.namedWindow(title, cv2.WINDOW_NORMAL)

        # --- Attach to SharedMemory, copy frame, then release the block ---
        shm = SharedMemory(name=msg.shm_name, create=False)
        # Wrap as numpy array backed by the shared buffer (no copy yet).
        frame_view = np.ndarray(msg.frame_shape, dtype=msg.frame_dtype, buffer=shm.buf)
        # Copy immediately so we can close and unlink shm safely.
        frame = frame_view.copy()
        shm.close()    # release local handle
        shm.unlink()   # free the OS-level shared memory block (Viewer is last consumer)

        # --- Annotate: draw green bounding rectangles with "motion" labels ---
        for c in msg.contours:
            x, y, w, h = cv2.boundingRect(c)
            # Green filled-border rectangle, 2px thick
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # "motion" label above the box; clamp y so label stays inside frame
            label_y = y - 5 if y - 5 > 10 else y + 15
            cv2.putText(
                frame, "motion", (x, label_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1,
            )

        # --- Timestamp overlay: HH:MM:SS in top-left with dark background ---
        elapsed = int(msg.frame_index / msg.fps)
        ts = f"{elapsed // 3600:02d}:{(elapsed % 3600) // 60:02d}:{elapsed % 60:02d}"

        # Measure text size to draw a filled background rectangle behind it.
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.7
        thickness = 2
        (text_w, text_h), baseline = cv2.getTextSize(ts, font, font_scale, thickness)

        # Padding around text (pixels)
        pad = 4
        x0, y0 = 10, 10  # top-left corner of background rect
        x1 = x0 + text_w + pad * 2
        y1 = y0 + text_h + baseline + pad * 2

        # Draw dark (near-black) filled rectangle as text background
        cv2.rectangle(frame, (x0, y0), (x1, y1), (30, 30, 30), cv2.FILLED)

        # Draw white timestamp text on top of the background rect
        text_x = x0 + pad
        text_y = y0 + pad + text_h  # baseline-aligned
        cv2.putText(frame, ts, (text_x, text_y), font, font_scale, (255, 255, 255), thickness)

        # --- Display frame ---
        cv2.imshow(title, frame)

        # --- Frame rate control: delay in ms derived from video FPS ---
        delay = max(1, int(1000 / msg.fps))
        cv2.waitKey(delay)
