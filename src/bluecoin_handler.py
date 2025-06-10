# bluecoin_handler.py
"""
Manages the BlueCoin ST sensor session.
It connects, monitors the gyroscope, and generates alerts based on head rotation.
"""

import time
import threading
import collections
from blue_st_sdk.manager import Manager, ManagerListener
from blue_st_sdk.node import NodeListener
from blue_st_sdk.feature import FeatureListener
from blue_st_sdk.features.feature_gyroscope import FeatureGyroscope
# from blue_st_sdk.features.feature_switch import FeatureSwitch, FeatureCommand, Commands


from .config import SCAN_TIME_s, BLUECOIN_TAG, BLUECOIN_IDX, GYRO_THR, BLUECOIN_SESSION_s, YAWN_THRESHOLD
from .utils import dbg

# --- Listeners BLE specific for this module ---
class _MgrListener(ManagerListener):
    def on_discovery_change(self, mgr, enabled):
        dbg(f"Discovery BLE {'ON' if enabled else 'OFF'}")
    def on_node_discovered(self, mgr, node):
        dbg(f"Discovered {node.get_name()}")

# --- Listeners for BlueCoin Node and Gyroscope feature ---
class _NodeListener(NodeListener):
    def __init__(self, evt: threading.Event):
        self.evt = evt
    def on_connect(self, node):
        print(f"[INFO] {node.get_name()} connected.")
        self.evt.set()
    def on_disconnect(self, node, unexpected=False):
        msg = f"[WARN] {node.get_name()} disconnected"
        if unexpected: msg += " unexpectedly"
        print(msg)

# --- Gyroscope FIFO Listener ---
class _GyroFIFOListener(FeatureListener):
    def __init__(self, fifo: collections.deque):
        self._fifo = fifo
    def on_update(self, feature, sample):
        if isinstance(feature, FeatureGyroscope):
            # The Z-axis is the third element
            self._fifo.append(sample.get_data()[2])

# --- Final warning for drowsiness ---
def _final_warning(mean_z: float):
    """Print the final drowsiness warning."""
    print("\n================  WARNING  ================")
    print("‼️  It seems you are getting drowsy!  ‼️")
    print(f"Average Z rotation: {mean_z:.1f} °/s; yawns: {YAWN_THRESHOLD}+")
    print("=========================================\n")

# --- Main function to run the BlueCoin session ---
def run_bluecoin_session():
    """
    Start a monitoring session with the BlueCoin.
    Lasts `duration_s` or stops if a gyro alert is triggered,
    or after 60 seconds without alerts.
    """
    print("\n### Starting BlueCoin session ###")
    alert_triggered = False
    
    try:
        mgr = Manager.instance()
        mgr.add_listener(_MgrListener())
        mgr.discover(SCAN_TIME_s)
        devices = mgr.get_nodes()
        
        if not devices:
            print("[ERROR] No BlueCoin device found.")
            return False

        print(f"[INFO] BLE devices found: {[n.get_name() for n in devices]}")

        # Select the device based on tag or index
        dev = next((n for n in devices if BLUECOIN_TAG and (n.get_tag() == BLUECOIN_TAG or n.get_name() == BLUECOIN_TAG)), None)
        # If no device found by tag, use the index
        if dev is None:
            dev = devices[min(BLUECOIN_IDX - 1, len(devices) - 1)]
            
        
        
        evt = threading.Event()
        dev.add_listener(_NodeListener(evt))
        print(f"[INFO] Connecting to {dev.get_name()}...")
        # Connect to the device and wait for connection event
        # If connection fails, return False
        if not dev.connect() or not evt.wait(timeout=5):
            print("[ERROR] Connection to BlueCoin failed.")
            return False

        # Get the gyroscope feature
        gyro = dev.get_feature(FeatureGyroscope)
        if gyro is None:
            print("[ERROR] Gyroscope feature not found on device.")
            dev.disconnect()
            return False
        
        # Initialize FIFO for Z-axis rotation data
        z_fifo = collections.deque(maxlen=50)
        # Set up FIFO listener for gyroscope data
        fifo_listener = _GyroFIFOListener(z_fifo)
        gyro.add_listener(fifo_listener)
        dev.enable_notifications(gyro)
        
        t0 = time.time()
        # no_alert_timeout = t0 + 60 # Timeout di 60s se non ci sono alert

        # until the device is connected and the session time has not expired
        while dev.is_connected() and time.time() - t0 < BLUECOIN_SESSION_s and not alert_triggered:
            # Wait for notifications from the gyroscope
            # If no notifications are received, continue to the next iteration
            # If the FIFO is full, calculate the average Z rotation
            # and check if it exceeds the threshold
            # If it does, print an alert and set the alert_triggered flag
            dev.wait_for_notifications(0.1)
            
            if len(z_fifo) == z_fifo.maxlen:
                mean_z = sum(abs(v) for v in z_fifo) / len(z_fifo)
                dbg(f"FIFO full. Average Z rotation: {mean_z:.1f} °/s")
                if mean_z > GYRO_THR:
                    print(f"[ALERT] Head rotation detected! Average Z (50 samples): {mean_z:.1f} °/s > {GYRO_THR}°/s")
                    _final_warning(mean_z)
                    alert_triggered = True
    
    except Exception as e:
        print(f"[ERROR] Error during BlueCoin session: {e}")
    finally:
        # Cleanup: disconnect from the device and remove listeners
        if 'dev' in locals() and dev.is_connected():
            if 'gyro' in locals() and 'fifo_listener' in locals():
                dev.disable_notifications(gyro)
                gyro.remove_listener(fifo_listener)
            dev.disconnect()
        print("### End BlueCoin session ###\n")

    return alert_triggered