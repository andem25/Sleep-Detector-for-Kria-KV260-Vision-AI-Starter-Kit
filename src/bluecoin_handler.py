# bluecoin_handler.py
"""
Gestisce la sessione con il sensore BlueCoin ST.
Si connette, monitora il giroscopio e genera allerte.
"""
import time
import threading
import collections
from blue_st_sdk.manager import Manager, ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features.feature_gyroscope import FeatureGyroscope
from config import (SCAN_TIME_s, BLUECOIN_TAG, BLUECOIN_IDX, GYRO_THR,
                    BLUECOIN_SESSION_s, YAWN_THRESHOLD)
from sleep_detector_cps.src.utils_detector_cps.src.utils import dbg

# --- Listeners BLE specifici per questo modulo ---
class _MgrListener(ManagerListener):
    def on_discovery_change(self, mgr, enabled):
        dbg(f"Discovery BLE {'ON' if enabled else 'OFF'}")
    def on_node_discovered(self, mgr, node):
        dbg(f"Discovered {node.get_name()}")

class _NodeListener(NodeListener):
    def __init__(self, evt: threading.Event):
        self.evt = evt
    def on_connect(self, node):
        print(f"[INFO] {node.get_name()} connesso.")
        self.evt.set()
    def on_disconnect(self, node, unexpected=False):
        msg = f"[WARN] {node.get_name()} disconnesso"
        if unexpected: msg += " inaspettatamente"
        print(msg)

class _GyroFIFOListener(FeatureListener):
    def __init__(self, fifo: collections.deque):
        self._fifo = fifo
    def on_update(self, feature, sample):
        if isinstance(feature, FeatureGyroscope):
            # L'asse Z è il terzo elemento
            self._fifo.append(sample.get_data()[2])

def _final_warning(mean_z: float):
    """Stampa l'avviso finale di sonnolenza."""
    print("\n================  WARNING  ================")
    print("‼️  Sembra che tu ti stia addormentando!  ‼️")
    print(f"Rotazione media Z: {mean_z:.1f} °/s; sbadigli: {YAWN_THRESHOLD}+")
    print("=========================================\n")

def _enable_gyro(device):
    """Tenta di abilitare il giroscopio usando FeatureSwitch o FeatureCommand."""
    try:
        from blue_st_sdk.features.feature_switch import FeatureSwitch
        fsw = device.get_feature(FeatureSwitch)
        gyro = device.get_feature(FeatureGyroscope)
        if fsw and gyro:
            dbg("Abilitazione giroscopio con FeatureSwitch.")
            fsw.switch_on(gyro)
    except Exception:
        dbg("FeatureSwitch non disponibile o fallito.")
    
    try:
        from blue_st_sdk.features.feature_command import FeatureCommand, Commands
        fcmd = device.get_feature(FeatureCommand)
        if fcmd:
            dbg("Abilitazione giroscopio con FeatureCommand (CMD_SENSORFUSION_ON).")
            fcmd.send_command(Commands.CMD_SENSORFUSION_ON)
    except Exception:
        dbg("FeatureCommand non disponibile o fallito.")

def run_bluecoin_session():
    """
    Avvia una sessione di monitoraggio con il BlueCoin.
    Dura `duration_s` o si interrompe se scatta un alert gyro,
    oppure dopo 60 secondi senza alert.
    """
    print("\n### Avvio sessione BlueCoin ###")
    alert_triggered = False
    
    try:
        mgr = Manager.instance()
        mgr.add_listener(_MgrListener())
        mgr.discover(SCAN_TIME_s)
        devices = mgr.get_nodes()
        
        if not devices:
            print("[ERROR] Nessun dispositivo BlueCoin trovato.")
            return False
        
        print(f"[INFO] Dispositivi BLE trovati: {[n.get_name() for n in devices]}")
        
        dev = next((n for n in devices if BLUECOIN_TAG and (n.get_tag() == BLUECOIN_TAG or n.get_name() == BLUECOIN_TAG)), None)
        if dev is None:
            dev = devices[min(BLUECOIN_IDX - 1, len(devices) - 1)]
            
        evt = threading.Event()
        dev.add_listener(_NodeListener(evt))
        
        print(f"[INFO] Connessione a {dev.get_name()}...")
        if not dev.connect() or not evt.wait(timeout=5):
            print("[ERROR] Connessione al BlueCoin fallita.")
            return False

        gyro = dev.get_feature(FeatureGyroscope)
        if gyro is None:
            print("[ERROR] Caratteristica Giroscopio non trovata sul dispositivo.")
            dev.disconnect()
            return False
        
        _enable_gyro(dev)
        
        z_fifo = collections.deque(maxlen=100)
        fifo_listener = _GyroFIFOListener(z_fifo)
        gyro.add_listener(fifo_listener)
        dev.enable_notifications(gyro)
        
        t0 = time.time()
        no_alert_timeout = t0 + 60 # Timeout di 60s se non ci sono alert

        while dev.is_connected() and time.time() - t0 < BLUECOIN_SESSION_s and not alert_triggered:
            dev.wait_for_notifications(0.1)
            
            # Timeout di 60s senza alert
            if time.time() > no_alert_timeout and not alert_triggered:
                dbg("Timeout di 60s per il BlueCoin, nessun alert rilevato.")
                break

            if len(z_fifo) == z_fifo.maxlen:
                mean_z = sum(abs(v) for v in z_fifo) / len(z_fifo)
                dbg(f"FIFO piena. Media rotazione Z: {mean_z:.1f} °/s")
                if mean_z > GYRO_THR:
                    print(f"[ALERT] Rilevata rotazione della testa! Media Z (100 campioni): {mean_z:.1f} °/s > {GYRO_THR}°/s")
                    _final_warning(mean_z)
                    alert_triggered = True
    
    except Exception as e:
        print(f"[ERROR] Errore durante la sessione BlueCoin: {e}")
    finally:
        if 'dev' in locals() and dev.is_connected():
            if 'gyro' in locals() and 'fifo_listener' in locals():
                dev.disable_notifications(gyro)
                gyro.remove_listener(fifo_listener)
            dev.disconnect()
        print("### Fine sessione BlueCoin ###\n")
    
    return alert_triggered