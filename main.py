"""
main.py — Entry point for the VideoStreamAnalysis pipeline.

Parses the video file path from the command line, validates it, then spawns
three separate processes (Streamer, Detector, Viewer) connected by Queues and
waits for all of them to finish naturally.

Usage:
    python main.py <video_path>
"""

import sys
import os
import multiprocessing

from streamer import run_streamer
from detector import run_detector
from viewer import run_viewer

# Seconds to wait for each child process to exit on its own before force-terminating.
SHUTDOWN_TIMEOUT = 5


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.isfile(video_path):
        print(f"Error: video file not found: {video_path}")
        sys.exit(1)

    stop_event = multiprocessing.Event()

    to_detector = multiprocessing.Queue()
    to_viewer = multiprocessing.Queue()
    # Viewer puts shm_name here after each frame; Streamer waits on these signals
    # before closing its handles.  Required on Windows where SharedMemory blocks
    # are destroyed when the last handle closes (unlike Linux where unlink() is used).
    release_queue = multiprocessing.Queue()

    streamer_proc = multiprocessing.Process(target=run_streamer, args=(video_path, to_detector, release_queue, stop_event), name="Streamer")
    detector_proc = multiprocessing.Process(target=run_detector, args=(to_detector, to_viewer, stop_event), name="Detector")
    viewer_proc   = multiprocessing.Process(target=run_viewer,   args=(to_viewer, video_path, release_queue, stop_event),  name="Viewer")

    try:
        for p in [streamer_proc, detector_proc, viewer_proc]:
            p.start()

        for p in [streamer_proc, detector_proc, viewer_proc]:
            p.join(timeout=SHUTDOWN_TIMEOUT)
            if p.is_alive():
                print(f"[main] WARNING: {p.name} did not exit within {SHUTDOWN_TIMEOUT}s — terminating")
                p.terminate()
                p.join()
    finally:
        # Best-effort cleanup for any SharedMemory blocks left in release_queue
        # (handles the abnormal-exit case where Streamer never drained its open_handles).
        # On normal exit this queue is empty; on abnormal exit we log but don't raise.
        drained = 0
        while not release_queue.empty():
            try:
                release_queue.get_nowait()
                drained += 1
            except Exception:
                break
        if drained:
            print(f"[main] WARNING: drained {drained} unreleased shm signal(s) from release_queue")


if __name__ == "__main__":
    main()
