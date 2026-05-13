"""
Module for pathology detection using TorchXRayVision.
"""

import numpy as np
from typing import Dict, Any

class PathologyDetector:
    """
    Detects pathological findings in medical images using TorchXRayVision DenseNet.
    """
    
    def __init__(self, device: str = "cpu"):
        """
        Initializes the PathologyDetector.
        """
        self.device = device
        self.use_fallback = False
        
        try:
            import torch
            import torchxrayvision as xrv
            self.xrv = xrv
            self.torch = torch
            
            # Load model
            self.model = xrv.models.DenseNet(weights="densenet121-res224-all")
            self.model.to(self.device)
            self.model.eval()
            
            # TorchXRayVision resizer
            self.transform = xrv.datasets.XRayResizer(224)
            
        except ImportError:
            print("Install torchxrayvision: pip install torchxrayvision")
            print("Falling back to existing CheXNet model.")
            self.use_fallback = True
            try:
                # Fallback to medical_models.chexnet
                from src.medical_models.chexnet import CheXNetModel
                self.model = CheXNetModel(device=self.device)
            except ImportError:
                print("Failed to load fallback CheXNet model as well.")
                self.model = None

    def get_severity(self, confidence: float) -> str:
        """
        Maps a confidence score to a qualitative severity label.
        
        Parameters
        ----------
        confidence : float
            Confidence score between 0 and 1.
            
        Returns
        -------
        str
            Severity string: "normal", "mild", "moderate", or "severe".
        """
        if confidence < 0.3:
            return "normal"
        elif confidence < 0.5:
            return "mild"
        elif confidence < 0.75:
            return "moderate"
        else:
            return "severe"

    def to_clinical_summary(self, detection_result: Dict[str, Any]) -> str:
        """
        Generates a brief text summary from the detection result.
        
        Example: "Positive findings: Atelectasis (0.87), Effusion (0.72). No pneumothorax detected."
        """
        positive = detection_result.get("positive_findings", [])
        findings_dict = detection_result.get("findings", {})
        
        if not positive:
            return "No positive findings detected. No pneumothorax detected."
        
        summary_parts = []
        for finding in positive:
            conf = findings_dict[finding]["confidence"]
            summary_parts.append(f"{finding} ({conf:.2f})")
            
        summary_text = f"Positive findings: {', '.join(summary_parts)}."
        
        # Explicitly mention pneumothorax if not in positive findings
        if "Pneumothorax" not in positive:
            summary_text += " No pneumothorax detected."
            
        return summary_text

    def detect(self, image_array: np.ndarray) -> Dict[str, Any]:
        """
        Detects pathologies and returns their confidence scores and presence.
        
        Parameters
        ----------
        image_array : np.ndarray
            Numpy array of the image (grayscale, float32, 0-1 range).
            
        Returns
        -------
        dict
            Dictionary containing finding confidences, positive findings, and summary.
        """
        if self.use_fallback:
            if self.model is None:
                return {}
            # Delegate to fallback if needed
            return self.model.detect(image_array)

        # Ensure dependencies are available
        xrv = getattr(self, "xrv", None)
        torch = getattr(self, "torch", None)
        
        if not xrv or not torch:
            return {}

        # Ensure image is in the right shape: (1, H, W) or (H, W) for grayscale
        if len(image_array.shape) == 3:
            # If RGB, convert to grayscale
            if image_array.shape[-1] == 3:
                img = image_array.mean(axis=-1)
            elif image_array.shape[0] == 3:
                img = image_array.mean(axis=0)
            elif image_array.shape[0] == 1:
                img = image_array[0]
            else:
                img = image_array
        else:
            img = image_array

        # a. Resize image to 224x224
        img = self.transform(img)

        # b. Normalize WITHOUT reshape
        img = xrv.datasets.normalize(img, maxval=1, reshape=False)

        # c. Ensure shape is [1,224,224]
        if len(img.shape) == 2:
            img = np.expand_dims(img, axis=0)

        # d. Convert to tensor
        img_tensor = torch.from_numpy(img).float()

        # e. Add batch dimension → [1,1,224,224]
        img_tensor = img_tensor.unsqueeze(0).to(self.device)

        print("FINAL INPUT SHAPE:", img_tensor.shape)

        # d. Run inference with torch.no_grad()
        with torch.no_grad():
            outputs = self.model(img_tensor)
            
        # e. Get predictions as sigmoid output
        outputs = torch.sigmoid(outputs)
        preds = outputs[0].cpu().numpy()

        # f. Map predictions to TorchXRayVision pathology labels
        pathologies = self.model.pathologies
        pred_dict = dict(zip(pathologies, preds))

        # List of required findings to return
        required_findings = [
            "Atelectasis", "Consolidation", "Infiltration", "Pneumothorax", 
            "Edema", "Emphysema", "Fibrosis", "Effusion", "Pneumonia", 
            "Pleural_Thickening", "Cardiomegaly", "Nodule", "Mass", "Hernia"
        ]

        # g. Return dict with confidence calibration
        findings = {}
        positive_findings = []
        raw_confidences = []
        calibrated_confidences = []

        PATHOLOGY_THRESHOLD = 0.7

        def _calibrate(raw: float, threshold: float = PATHOLOGY_THRESHOLD) -> float:
            """Rescale raw score: values below threshold → near 0; above → [0,1]."""
            if raw <= threshold:
                # compress sub-threshold scores into [0, 0.3] range
                return float(max(0.0, (raw / threshold) * 0.3))
            else:
                # linearly rescale (threshold, 1.0) → (0.3, 1.0)
                return float(0.3 + ((raw - threshold) / (1.0 - threshold)) * 0.7)

        def _tier(calibrated: float) -> str:
            if calibrated >= 0.7:
                return "high"
            elif calibrated >= 0.4:
                return "moderate"
            return "low"

        for finding in required_findings:
            finding_key = finding.replace("_", " ") if finding not in pred_dict else finding
            raw_confidence = float(pred_dict.get(finding_key, 0.0))
            calibrated = _calibrate(raw_confidence)
            present = raw_confidence > PATHOLOGY_THRESHOLD
            
            findings[finding] = {
                "present": present,
                "confidence": round(calibrated, 4),
                "raw_confidence": round(raw_confidence, 4),
                "confidence_tier": _tier(calibrated)
            }
            raw_confidences.append(raw_confidence)
            calibrated_confidences.append(calibrated)
            
            if present:
                positive_findings.append(finding)

        top_finding_idx = int(np.argmax(raw_confidences))
        top_finding = required_findings[top_finding_idx]
        top_raw_confidence = raw_confidences[top_finding_idx]
        
        if not positive_findings:
            if top_raw_confidence > 0.45:
                positive_findings.append(top_finding)
                findings[top_finding]["present"] = True
            else:
                top_finding = "No acute cardiopulmonary abnormality"

        # Use calibrated confidences for overall score
        confidences = calibrated_confidences

        overall_abnormality_score = float(np.mean(confidences))

        return {
            "findings": findings,
            "positive_findings": positive_findings,
            "top_finding": top_finding,
            "overall_abnormality_score": overall_abnormality_score,
            "model_used": "TorchXRayVision-DenseNet121",
            "inference_device": self.device
        }

if __name__ == "__main__":
    import json
    
    print("Testing PathologyDetector...")
    detector = PathologyDetector()
    
    # Create a dummy 224x224 random numpy array (0-1 range)
    dummy_img = np.random.rand(224, 224).astype(np.float32)
    
    print("Running detection on dummy image...")
    # NOTE: If this is the first run, torchxrayvision will try to download weights.
    # On Windows command line, this might throw a UnicodeEncodeError due to the progress bar.
    # Set PYTHONIOENCODING=utf-8 if running from a basic terminal.
    try:
        result = detector.detect(dummy_img)
        
        print("\nDetection Result (Partial):")
        print(json.dumps({
            "positive_findings": result.get("positive_findings"),
            "top_finding": result.get("top_finding"),
            "overall_abnormality_score": result.get("overall_abnormality_score"),
            "model_used": result.get("model_used")
        }, indent=2))
        
        print("\nClinical Summary:")
        print(detector.to_clinical_summary(result))
    except Exception as e:
        print(f"Error during detection: {e}")
