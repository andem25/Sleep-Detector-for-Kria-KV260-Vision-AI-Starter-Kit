# dpu_handler.py
"""
Gestore per la DPU (Vitis-AI).
Carica il modello, pre-processa le immagini e esegue l'inferenza.
"""
import cv2
import numpy as np
import sys
from .pynq_dpu import DpuOverlay
from .config import BIT_PATH, XMODEL_PATH, CLASS_NAMES
from .src.utils import dbg

class DPUHandler:
    def __init__(self):
        try:
            dbg("Inizializzazione DPUHandler...")
            self.overlay = DpuOverlay(BIT_PATH)
            self.overlay.load_model(XMODEL_PATH)
            dbg("Overlay e modello caricati.")
        except FileNotFoundError as e:
            print(f"[FATAL] Bitstream/XModel mancante: {e}", file=sys.stderr)
            sys.exit(1)

        self.dpu = self.overlay.runner
        inp_tensor = self.dpu.get_input_tensors()[0]
        out_tensor = self.dpu.get_output_tensors()[0]

        if out_tensor.dims[-1] != len(CLASS_NAMES):
            raise ValueError("La dimensione dell'output del modello non corrisponde al numero di classi.")

        self.shape_in = tuple(inp_tensor.dims)
        self.shape_out = tuple(out_tensor.dims)
        self.input_data = [np.empty(self.shape_in, np.float32, order="C")]
        self.output_data = [np.empty(self.shape_out, np.float32, order="C")]
        
        self.H, self.W = self.shape_in[1], self.shape_in[2]
        self.MEAN = np.array([0.485, 0.456, 0.406], np.float32)
        self.STD = np.array([0.229, 0.224, 0.225], np.float32)
        dbg(f"DPU pronta. Input shape: {self.shape_in}")

    def _preprocess(self, image):
        """Prepara l'immagine per l'inferenza."""
        img_resized = cv2.resize(image, (self.W, self.H))
        img_normalized = (img_resized.astype(np.float32) / 255.0 - self.MEAN) / self.STD
        self.input_data[0][0] = img_normalized

    def run_inference(self, image_roi) -> (str, float):
        """Esegue il pre-processing e l'inferenza su un'immagine."""
        self._preprocess(image_roi)
        job_id = self.dpu.execute_async(self.input_data, self.output_data)
        self.dpu.wait(job_id)
        
        probs = self.output_data[0].flatten()
        idx = int(np.argmax(probs))
        label = CLASS_NAMES[idx]
        confidence = float(probs[idx])
        
        dbg(f"Inferenza: {label} (conf: {confidence:.2f})")
        return label, confidence