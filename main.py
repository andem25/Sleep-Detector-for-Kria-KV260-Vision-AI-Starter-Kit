#!/usr/bin/env python3
# main.py
"""
Yawn & BlueCoin Monitor for KV260 - *v1.0*
=========================================
Orchestrate the yawn detection (DPU) and drowsiness monitoring (BlueCoin) modules for a driver alert system.
"""
import sys
import time
import threading
import collections
import signal
import itertools
import signal
import itertools
import cv2

# Import custom modules and configuration
import src.config as cfg
from src.utils import dbg
from src.dpu_handler import DPUHandler
from src.bluecoin_handler import run_bluecoin_session


# --- Global Application State ---
yawn_events = collections.deque(maxlen=cfg.YAWN_THRESHOLD * 8)
bluecoin_active = threading.Event()
last_yawn_time = 0.0

# --- Orchestration Functions ---
def _bluecoin_runner():
    """Wrapper to run the BlueCoin session in a separate thread."""
    try:
        run_bluecoin_session()
    finally:
        bluecoin_active.clear()

def _check_yawn_state():
    """Check the number of yawns and decide whether to trigger alerts or sessions."""
    global last_yawn_time
    now = time.time()

    # Remove old yawns from the time window
    while yawn_events and (now - yawn_events[0] > cfg.YAWN_WINDOW_s):
        yawn_events.popleft()

    dbg(f"Yawns in the window of {cfg.YAWN_WINDOW_s / 60:.0f} min: {len(yawn_events)}")

    # Warning for 5 yawns in 10 minutes
    if len(yawn_events) >= cfg.YAWN_WARNING_COUNT:
        print("\n‼️  You have yawned frequently in the last %d minutes. Take a break or grab a coffee!  ‼️\n" % (cfg.YAWN_WINDOW_s / 60))

    # BLUECOIN session management
    # Start BlueCoin session if threshold is reached
    if len(yawn_events) >= cfg.YAWN_THRESHOLD and not bluecoin_active.is_set():
        print(f"\n>>> Yawn threshold of {cfg.YAWN_THRESHOLD} reached. Starting BlueCoin monitoring...")
        bluecoin_active.set()
        thread = threading.Thread(target=_bluecoin_runner, daemon=True)
        thread.start()

def main_loop():
    """Main application loop."""
    global last_yawn_time
    
    # Initialize DPU handler and face detection
    dpu = DPUHandler()
    
    # Load Haar Cascade for face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    cap = cv2.VideoCapture(cfg.DEVICE if cfg.DEVICE.startswith("/dev/") else int(cfg.DEVICE), cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # Check if the camera is opened successfully
    if not cap.isOpened():
        print("[FATAL] Camera not available.", file=sys.stderr)
        return

    print(f"System ready. Press Ctrl+C to exit. (DEBUG={cfg.DEBUG})")

    try:
        frame_counter = itertools.count()
        while True:
            ret, frame = cap.read()
            if not ret:
                dbg("Frame not captured, skipping.")
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))

            for (x, y, w, h) in faces:
                # Take the mouth region (ROI) with some padding
                pad = int(0.10 * w)
                x0, y0 = max(x - pad, 0), max(y - pad, 0)
                x1, y1 = min(x + w + pad, frame.shape[1]), min(y + h + pad, frame.shape[0])

                # ROI for the mouth (lower half of the face)
                mx = x0 + int(0.20 * (x1 - x0))
                my = y0 + int(0.55 * (y1 - y0))
                mw = int(0.60 * (x1 - x0))
                mh = int(0.30 * (y1 - y0))
                mouth_roi = frame[my:my + mh, mx:mx + mw]
                
                if not mouth_roi.size:
                    dbg("ROI for the mouth is empty.")
                    continue
                # Run DPU inference on the mouth ROI
                label, conf = dpu.run_inference(mouth_roi)

                dbg(f"DPU inference result - label: {label}, conf: {conf:.2f}")
                
                # Check for yawn detection
                if label == "yawn" and conf > 0.6:
                    now = time.time()
                    # if the yawn is detected and debounce time has passed
                    if now - last_yawn_time >= cfg.YAWN_DEBOUNCE_s:
                        last_yawn_time = now
                        print(f"[INFO] YAWN detected (conf: {conf:.2f}) - frame {next(frame_counter)}")
                        yawn_events.append(now)
                        _check_yawn_state()
                    else:
                        # Ignore yawn if within debounce period
                        dbg("YAWN ignored due to debounce.")
                break

    except KeyboardInterrupt:
        print("\nKeyboard interrupt requested...")
    finally:
        cap.release()
        print("Camera released. Goodbye!")

# Handle graceful exit on Ctrl+C
def _handle_exit(*args):
    print("\nExiting...")
    sys.exit(0)

# Register signal handler for graceful exit
if __name__ == "__main__":
    signal.signal(signal.SIGINT, _handle_exit)
    main_loop()