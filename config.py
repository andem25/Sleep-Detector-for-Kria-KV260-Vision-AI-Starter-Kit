# config.py
"""
File di configurazione per il Yawn & BlueCoin Monitor.
Centralizza tutte le costanti e i parametri del sistema.
"""
import os

# --- Configurazione DPU e Modello ---
BIT_PATH = "dpu.bit"
XMODEL_PATH = "a.xmodel"
CLASS_NAMES = ["no_yawn", "yawn"]

# --- Configurazione Camera ---
DEVICE = "/dev/video0"
FPS = 10

# --- Logica di Rilevamento Sbadigli ---
YAWN_WINDOW_s = 10 * 60  # 10 minuti
YAWN_THRESHOLD = 3       # Sbadigli per avviare BlueCoin
YAWN_WARNING_COUNT = 5   # Sbadigli per il warning "caffè"
YAWN_DEBOUNCE_s = 3      # Tempo minimo tra due sbadigli validi

# --- Logica BlueCoin ---
BLUECOIN_SESSION_s = 5 * 60  # Durata massima sessione BlueCoin
GYRO_THR = 35.0              # Soglia di allerta rotazione giroscopio (°/s)
SCAN_TIME_s = 5              # Durata scansione BLE
BLUECOIN_TAG = os.getenv("BLUECOIN_TAG")
BLUECOIN_IDX = int(os.getenv("BLUECOIN_INDEX", "1"))

# --- Debug ---
# DEBUG = bool(int(os.getenv("DBG", "1")))
DEBUG = False