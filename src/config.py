# config.py
"""
File di configurazione per il Yawn & BlueCoin Monitor.
Centralizza tutte le costanti e i parametri del sistema.
"""
import os

# --- DPU configuration and model ---
BIT_PATH = "dpu.bit"
XMODEL_PATH = "./models/net.xmodel"
CLASS_NAMES = ["no_yawn", "yawn"]

# --- Camera ---
DEVICE = "/dev/video0"
FPS = 10

# --- Yawn Detection Logic ---
YAWN_WINDOW_s = 1 * 60  # 10 minutes
# YAWN_WINDOW_s = 10 * 60  # 10 minutes
YAWN_THRESHOLD = 3       # Yawns to trigger BlueCoin
YAWN_WARNING_COUNT = 5   # Yawns for "coffee" warning
YAWN_DEBOUNCE_s = 3      # Minimum time between two valid yawns

# --- BlueCoin Logic ---
# BLUECOIN_SESSION_s = 5 * 60  # Maximum BlueCoin session duration
BLUECOIN_SESSION_s = 1 * 60  # Maximum BlueCoin session duration
GYRO_THR = 20.0              # Gyroscope rotation alert threshold (°/s)
SCAN_TIME_s = 5              # BLE scan duration
BLUECOIN_TAG = os.getenv("BLUECOIN_TAG")
BLUECOIN_IDX = int(os.getenv("BLUECOIN_INDEX", "1"))

# --- Debug ---
DEBUG = bool(int(os.getenv("DBG", "0")))