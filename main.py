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
import logging
import multiprocessing

from streamer import run_streamer
from detector import run_detector
from viewer import run_viewer


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger("main")

    if len(sys.argv) != 2:
        print("Usage: python main.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.isfile(video_path):
        logger.error("Video file not found: %s", video_path)
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

    processes = [streamer_proc, detector_proc, viewer_proc]

    try:
        for p in processes:
            p.start()
            logger.info("Started %s (pid=%d)", p.name, p.pid)

        # Wait for Streamer to signal video EOF before joining.
        # Without this the join fires while the video is still playing.
        stop_event.wait()
        logger.info("EOF signalled — waiting for pipeline to drain")

        # Join in dependency order: Detector exits first (after EOS from Streamer),
        # then Viewer (after EOS from Detector), then Streamer (after Viewer releases
        # all SharedMemory handles via release_queue).  Joining Streamer first would
        # deadlock because Streamer waits for Viewer's release signals.
        #
        # No per-process timeout: Streamer reads ahead of real-time so queues can
        # hold many frames that Viewer drains at playback speed (cv2.waitKey adds
        # ~40ms/frame delay).  EOS_SENTINEL propagation is the correct exit mechanism.
        for p in [detector_proc, viewer_proc, streamer_proc]:
            p.join()
            logger.info("%s exited (exit code %s)", p.name, p.exitcode)

    except KeyboardInterrupt:
        logger.warning("Interrupted — terminating pipeline processes")
        for p in processes:
            if p.is_alive():
                p.terminate()
                p.join()
                logger.info("Terminated %s", p.name)
        sys.exit(130)  # standard exit code for Ctrl+C

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
            logger.warning("Drained %d unreleased shm signal(s) from release_queue", drained)


if __name__ == "__main__":
    main()
