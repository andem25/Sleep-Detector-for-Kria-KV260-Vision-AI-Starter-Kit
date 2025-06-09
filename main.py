#!/usr/bin/env python3
# main.py
"""
Yawn & BlueCoin Monitor for KV260 – *v1.5*
=========================================
Orchestra i moduli di rilevamento sbadigli (DPU) e monitoraggio
sonnolenza (BlueCoin) per un sistema di allerta guidatore.
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

# Importa i moduli custom e la configurazione
from src import config as cfg
from src.utils import dbg # Vedi nota sotto
from src.dpu_handler import DPUHandler
from src.bluecoin_handler import run_bluecoin_session


# --- Stato Globale dell'Applicazione ---
yawn_events = collections.deque(maxlen=cfg.YAWN_THRESHOLD * 8)
bluecoin_active = threading.Event()
last_yawn_time = 0.0
coffee_warned = False # Stato per il warning dei 5 sbadigli

# --- Funzioni di Orchestrazione ---
def _bluecoin_runner():
    """Wrapper per eseguire la sessione BlueCoin in un thread separato."""
    global coffee_warned
    try:
        run_bluecoin_session()
    finally:
        # Resetta lo stato dopo la fine della sessione
        bluecoin_active.clear()
        yawn_events.clear()
        coffee_warned = False
        print("[INFO] Stato sbadigli e allerta resettato.")

def _check_yawn_state():
    """Controlla il numero di sbadigli e decide se avviare allarmi o sessioni."""
    global last_yawn_time, coffee_warned
    now = time.time()

    # Rimuovi sbadigli vecchi dalla finestra temporale
    while yawn_events and (now - yawn_events[0] > cfg.YAWN_WINDOW_s):
        yawn_events.popleft()
    
    dbg(f"Sbadigli nella finestra di {cfg.YAWN_WINDOW_s / 60:.0f} min: {len(yawn_events)}")

    # Warning per 5 sbadigli in 10 minuti
    if len(yawn_events) >= cfg.YAWN_WARNING_COUNT and not coffee_warned:
        print("\n‼️  Hai sbadigliato 5 volte in 10 minuti. Riposati o prendi un caffè!  ‼️\n")
        coffee_warned = True

    # Avvio sessione BlueCoin se si raggiunge la soglia
    if len(yawn_events) >= cfg.YAWN_THRESHOLD and not bluecoin_active.is_set():
        print(f"\n>>> Raggiunta soglia di {cfg.YAWN_THRESHOLD} sbadigli. Avvio monitoraggio BlueCoin...")
        bluecoin_active.set()
        thread = threading.Thread(target=_bluecoin_runner, daemon=True)
        thread.start()

def main_loop():
    """Ciclo principale dell'applicazione."""
    global last_yawn_time
    
    dpu = DPUHandler()
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    cap = cv2.VideoCapture(cfg.DEVICE if cfg.DEVICE.startswith("/dev/") else int(cfg.DEVICE), cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("[FATAL] Camera non disponibile.", file=sys.stderr)
        return

    print(f"Sistema pronto. Premi Ctrl+C per uscire. (DEBUG={cfg.DEBUG})")
    
    try:
        frame_counter = itertools.count()
        while True:
            ret, frame = cap.read()
            if not ret:
                dbg("Frame non acquisito, salto.")
                time.sleep(0.1)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.2, 5, minSize=(80, 80))

            for (x, y, w, h) in faces:
                # Estrai la regione della bocca (ROI) con un po' di padding
                pad = int(0.10 * w)
                x0, y0 = max(x - pad, 0), max(y - pad, 0)
                x1, y1 = min(x + w + pad, frame.shape[1]), min(y + h + pad, frame.shape[0])
                
                # ROI per la bocca (metà inferiore del viso)
                mx = x0 + int(0.20 * (x1 - x0))
                my = y0 + int(0.55 * (y1 - y0))
                mw = int(0.60 * (x1 - x0))
                mh = int(0.30 * (y1 - y0))
                mouth_roi = frame[my:my + mh, mx:mx + mw]
                
                if not mouth_roi.size:
                    dbg("ROI della bocca vuota.")
                    continue

                label, conf = dpu.run_inference(mouth_roi)
                
                if label == "yawn" and conf > 0.6:
                    now = time.time()
                    if now - last_yawn_time >= cfg.YAWN_DEBOUNCE_s:
                        last_yawn_time = now
                        print(f"[INFO] SBADIGLIO rilevato (conf: {conf:.2f}) - frame {next(frame_counter)}")
                        yawn_events.append(now)
                        _check_yawn_state()
                    else:
                        dbg("Sbadiglio ignorato per debounce.")
                
                # Interrompi il ciclo sui volti dopo averne processato uno
                break 
    
    except KeyboardInterrupt:
        print("\nInterruzione da tastiera richiesta...")
    finally:
        cap.release()
        print("Camera rilasciata. Arrivederci!")

def _handle_exit(*args):
    """Handler per terminare il programma in modo pulito."""
    print("\nUscita in corso...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, _handle_exit)
    main_loop()