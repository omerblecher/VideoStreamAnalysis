"""
detector.py — Detector process for VideoStreamAnalysis pipeline.

Consumes ShmFrameMessage from the Streamer via a Queue, runs MOG2 background
subtraction to detect motion, and forwards DetectorMessage (with contour list
and the original SharedMemory name) to the Viewer via a second Queue.

The Detector never draws on frames. All annotation is deferred to the Viewer.
"""

import logging
import cv2
import numpy as np
from multiprocessing import Queue
from multiprocessing.shared_memory import SharedMemory

from ipc import ShmFrameMessage, DetectorMessage, EOS_SENTINEL

# Minimum contour area (in pixels²) below which a detected region is treated as
# noise and discarded.  500 px² is a reasonable baseline for a 640×480 frame;
# too small and sensor noise creates false positives, too large and slow-moving
# small objects are missed.
MIN_CONTOUR_AREA: int = 500


def run_detector(from_streamer: Queue, to_viewer: Queue, stop_event) -> None:
    """Main loop for the Detector process.

    Reads ShmFrameMessage objects from *from_streamer*, applies MOG2-based
    video motion detection, and puts DetectorMessage objects onto *to_viewer*.
    Propagates EOS_SENTINEL when the stream ends.

    Args:
        from_streamer: Queue receiving ShmFrameMessage (or EOS_SENTINEL) from
                       the Streamer process.
        to_viewer:     Queue to which DetectorMessage (or EOS_SENTINEL) is sent
                       for the Viewer process.
        stop_event:    multiprocessing.Event accepted for interface consistency
                       but not used; EOS propagates via Queue.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("detector")
    logger.info("Detector started")

    # Initialise MOG2 subtractor once; it builds an adaptive background model
    # over the first several frames so the initial frames may have high recall.
    bg_sub = cv2.createBackgroundSubtractorMOG2()
    processed = 0

    try:
        while True:
            msg = from_streamer.get()  # blocks until a message is available

            # --- End-of-stream propagation ---
            if msg is EOS_SENTINEL:
                logger.info("EOS received — forwarding to viewer after %d frame(s)", processed)
                to_viewer.put(EOS_SENTINEL)
                return

            # --- Attach to SharedMemory and copy the frame locally ---
            try:
                shm = SharedMemory(name=msg.shm_name, create=False)
                frame_view = np.ndarray(msg.frame_shape, dtype=msg.frame_dtype, buffer=shm.buf)
                frame = frame_view.copy()
                shm.close()
            except FileNotFoundError:
                logger.warning("SharedMemory block '%s' not found for frame %d — skipping",
                               msg.shm_name, msg.frame_index)
                # Forward the message with no contours so the Viewer still sends
                # the release signal back to the Streamer.
                to_viewer.put(DetectorMessage(
                    shm_name=msg.shm_name,
                    frame_shape=msg.frame_shape,
                    frame_dtype=msg.frame_dtype,
                    frame_index=msg.frame_index,
                    fps=msg.fps,
                    contours=[],
                ))
                continue
            except Exception as exc:
                logger.error("Error reading frame %d from SharedMemory: %s — skipping", msg.frame_index, exc)
                to_viewer.put(DetectorMessage(
                    shm_name=msg.shm_name,
                    frame_shape=msg.frame_shape,
                    frame_dtype=msg.frame_dtype,
                    frame_index=msg.frame_index,
                    fps=msg.fps,
                    contours=[],
                ))
                continue

            # --- MOG2 video motion detection ---
            try:
                contours = _detect_motion(bg_sub, frame)
            except Exception as exc:
                logger.error("Motion detection failed for frame %d: %s — forwarding empty contours", msg.frame_index, exc)
                contours = []

            # --- Build and forward the downstream message ---
            det_msg = DetectorMessage(
                shm_name=msg.shm_name,
                frame_shape=msg.frame_shape,
                frame_dtype=msg.frame_dtype,
                frame_index=msg.frame_index,
                fps=msg.fps,
                contours=list(contours),
            )
            to_viewer.put(det_msg)
            processed += 1

    except KeyboardInterrupt:
        logger.info("Interrupted")
    except Exception as exc:
        logger.exception("Unexpected error in detector: %s", exc)
    finally:
        # Guarantee EOS is always forwarded so the Viewer is never left hanging.
        try:
            to_viewer.put(EOS_SENTINEL)
        except Exception:
            pass


def _detect_motion(bg_sub: cv2.BackgroundSubtractorMOG2, frame: np.ndarray) -> list:
    """Run MOG2 background subtraction and return filtered contours.

    Steps (per CONTEXT.md Implementation Decisions):
      1. Convert BGR → grayscale.
      2. Apply Gaussian blur for noise reduction before subtraction.
      3. Apply MOG2 subtractor to obtain a binary foreground mask directly
         (no separate threshold step needed — MOG2 produces a binary mask).
      4. Dilate mask to merge nearby regions into fewer, cleaner blobs.
      5. Find external contours.
      6. Filter out contours below MIN_CONTOUR_AREA.

    Args:
        bg_sub: Persistent MOG2 subtractor instance (must be created once and
                reused across frames so the background model accumulates).
        frame:  BGR frame as a numpy array (copy owned by Detector).

    Returns:
        List of contour arrays (each is an (N, 1, 2) int32 numpy array).
    """
    # Step 1: BGR → grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Step 2: Gaussian blur — (21, 21) kernel reduces sensor/compression noise
    #         before the background model sees it.
    blurred = cv2.GaussianBlur(gray, (21, 21), 0)

    # Step 3: MOG2 foreground mask (binary; 255 = foreground, 0 = background)
    fg_mask = bg_sub.apply(blurred)

    # Step 4: Dilate to connect nearby foreground blobs into single regions
    fg_mask = cv2.dilate(fg_mask, None, iterations=2)

    # Step 5: Find external contours on a copy (findContours may modify input)
    cnts, _ = cv2.findContours(fg_mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Step 6: Filter noise — discard contours below the minimum area threshold
    filtered = [c for c in cnts if cv2.contourArea(c) >= MIN_CONTOUR_AREA]

    return filtered
