from transformers import pipeline
from PIL import Image

class PathologyClassifier:
    def __init__(self):
        # Load a chest X-ray classification model
        self.classifier = pipeline(
            "image-classification",
            model="nickmuchi/vit-finetuned-chest-xray-pneumonia",
            device=-1  # CPU
        )
        
        self.condition_map = {
            "PNEUMONIA": "Pneumonia",
            "NORMAL": "No Finding",
        }
        print("PathologyClassifier loaded (local, CPU)")

    def classify(self, image_path: str) -> dict:
        image = Image.open(image_path).convert("RGB")
        results = self.classifier(image)
        
        # Sort by confidence descending (pipeline usually returns sorted, but just to be sure)
        predictions = sorted(
            [{"condition": res["label"], "confidence": round(res["score"], 4)} for res in results],
            key=lambda x: x["confidence"],
            reverse=True
        )
        
        top_finding = predictions[0]["condition"]
        top_confidence = predictions[0]["confidence"]
        
        suggests_abnormality = (top_finding != "NORMAL" and top_confidence > 0.6)
        
        return {
            "predictions": predictions,
            "top_finding": top_finding,
            "top_confidence": top_confidence,
            "suggests_abnormality": suggests_abnormality
        }

    def format_for_prompt(self, classification: dict) -> str:
        preds_str = "\n     ".join([f"{p['condition']}: {p['confidence']:.1%}" for p in classification["predictions"]])
        
        return f"""Pathology classifier results (pre-LLM analysis):
     Primary finding: {classification['top_finding']} ({classification['top_confidence']:.0%} confidence)
     All predictions:
     {preds_str}
     
     IMPORTANT: Your report must be consistent with these
     classifier findings. If you disagree, explicitly state
     why in the IMPRESSION section."""
