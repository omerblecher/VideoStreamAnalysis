"""
ipc.py — Inter-Process Communication contracts for VideoStreamAnalysis pipeline.

All three processes (Streamer, Detector, Viewer) import from this module to ensure
they agree on SharedMemory layout, Queue message structure, and shutdown signaling.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


# ---------------------------------------------------------------------------
# SharedMemory sizing helper
# ---------------------------------------------------------------------------

def frame_shm_size(shape: tuple, dtype) -> int:
    """Return the byte size needed to store a frame with the given shape and dtype.

    Used by both producer (Streamer) and consumer (Detector/Viewer) so they
    allocate and read the same number of bytes from a SharedMemory block.

    Args:
        shape: Frame dimensions, e.g. (H, W, C) or (H, W).
        dtype: numpy dtype or dtype string, e.g. np.uint8 or "uint8".

    Returns:
        int: Total byte count.
    """
    return int(np.prod(shape) * np.dtype(dtype).itemsize)


# ---------------------------------------------------------------------------
# Queue message dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ShmFrameMessage:
    """Message put on the Streamer→Detector Queue.

    Carries everything the Detector needs to locate the frame in SharedMemory
    and forward timing information downstream to the Viewer.
    """
    shm_name: str        # Name of the SharedMemory block containing the frame
    frame_shape: tuple   # (H, W, C), e.g. (480, 640, 3)
    frame_dtype: str     # numpy dtype string, e.g. "uint8"
    frame_index: int     # Monotonically increasing counter (0-based)
    fps: float           # Video FPS read from file header; forwarded so Viewer can compute delay


@dataclass
class DetectorMessage:
    """Message put on the Detector→Viewer Queue.

    Detector forwards the same SharedMemory reference (does NOT copy frame data)
    and appends the detected contours. Viewer uses this to display and annotate
    the frame, then unlinks the SharedMemory block when done.
    """
    shm_name: str        # Same SharedMemory block name as in ShmFrameMessage
    frame_shape: tuple   # (H, W, C)
    frame_dtype: str     # numpy dtype string, e.g. "uint8"
    frame_index: int     # Monotonically increasing counter
    fps: float           # Video FPS; Viewer uses this to compute cv2.waitKey delay
    contours: list       # List of numpy arrays from cv2.findContours; empty = no motion


# ---------------------------------------------------------------------------
# End-of-stream sentinel
# ---------------------------------------------------------------------------

# A single module-level constant so all processes use the same check:
#   if msg is EOS_SENTINEL: ...
EOS_SENTINEL = None
