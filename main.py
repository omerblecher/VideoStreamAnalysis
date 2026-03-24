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


def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.isfile(video_path):
        print(f"Error: video file not found: {video_path}")
        sys.exit(1)

    to_detector = multiprocessing.Queue()
    to_viewer = multiprocessing.Queue()
    # Viewer puts shm_name here after each frame; Streamer waits on these signals
    # before closing its handles.  Required on Windows where SharedMemory blocks
    # are destroyed when the last handle closes (unlike Linux where unlink() is used).
    release_queue = multiprocessing.Queue()

    streamer_proc = multiprocessing.Process(target=run_streamer, args=(video_path, to_detector, release_queue), name="Streamer")
    detector_proc = multiprocessing.Process(target=run_detector, args=(to_detector, to_viewer), name="Detector")
    viewer_proc   = multiprocessing.Process(target=run_viewer,   args=(to_viewer, video_path, release_queue),  name="Viewer")

    for p in [streamer_proc, detector_proc, viewer_proc]:
        p.start()

    for p in [streamer_proc, detector_proc, viewer_proc]:
        p.join()


if __name__ == "__main__":
    main()
