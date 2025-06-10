# dpu_handler.py
"""
# dpu_handler.py
Handles the DPU overlay, model loading, and inference execution.
"""
import cv2
import numpy as np
import sys
from pynq_dpu import DpuOverlay
from .config import BIT_PATH, XMODEL_PATH, CLASS_NAMES
from .utils import dbg

class DPUHandler:
    # Initializes the DPU overlay and model, prepares input/output tensors.
    def __init__(self):
        try:
            dbg("Initializing DPUHandler...")
            self.overlay = DpuOverlay(BIT_PATH)
            self.overlay.load_model(XMODEL_PATH)
            dbg("Overlay and model loaded.")
        except FileNotFoundError as e:
            print(f"[FATAL] Bitstream/XModel missing: {e}", file=sys.stderr)
            sys.exit(1)

        # Initialize DPU runner and input/output tensors
        self.dpu = self.overlay.runner
        inp_tensor = self.dpu.get_input_tensors()[0]
        out_tensor = self.dpu.get_output_tensors()[0]
        
        # Validate input and output tensor dimensions
        if out_tensor.dims[-1] != len(CLASS_NAMES):
            raise ValueError("Output tensor size does not match number of classes.")
        # Initialize shapes and data buffers
        self.shape_in = tuple(inp_tensor.dims)
        self.shape_out = tuple(out_tensor.dims)
        self.input_data = [np.empty(self.shape_in, np.float32, order="C")]
        self.output_data = [np.empty(self.shape_out, np.float32, order="C")]
        
        # Set input dimensions
        self.H, self.W = self.shape_in[1], self.shape_in[2]
        # Set mean and standard deviation for normalization
        self.MEAN = np.array([0.485, 0.456, 0.406], np.float32)
        self.STD = np.array([0.229, 0.224, 0.225], np.float32)
        dbg(f"DPU ready. Input shape: {self.shape_in}")
    
    # Preprocess the input image for inference.
    def _preprocess(self, image):
        """Prepares the image for inference."""
        # Resize and normalize the input image.
        img_resized = cv2.resize(image, (self.W, self.H))
        img_normalized = (img_resized.astype(np.float32) / 255.0 - self.MEAN) / self.STD
        self.input_data[0][0] = img_normalized

    # Executes preprocessing and inference on an image ROI.
    def run_inference(self, image_roi) -> (str, float):
        """Executes preprocessing and inference on an image ROI."""
        self._preprocess(image_roi)
        job_id = self.dpu.execute_async(self.input_data, self.output_data)
        self.dpu.wait(job_id)
        
        probs = self.output_data[0].flatten()
        idx = int(np.argmax(probs))
        label = CLASS_NAMES[idx]
        confidence = float(probs[idx])

        dbg(f"Inference: {label} (conf: {confidence:.2f})")
        # Return the label and confidence score
        return label, confidence