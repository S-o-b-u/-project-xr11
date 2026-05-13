import os
import json
import pickle
import numpy as np
from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class VisualRetriever:
    def __init__(self):
        # This is CLIP — embeds both images and text in the same vector space.
        self.model = SentenceTransformer("clip-ViT-B-32")
        self.image_index = None
        self.metadata = []
        print("VisualRetriever loaded (local CLIP, CPU)")

    def build_image_index(self, dataset: list, index_save_path: str):
        embeddings = []
        metadata = []
        
        for i, entry in enumerate(dataset):
            image_path = entry.get("image_path")
            if image_path and os.path.exists(image_path):
                try:
                    img = Image.open(image_path).convert("RGB")
                    emb = self.model.encode([img])[0]
                    embeddings.append(emb)
                    metadata.append({
                        "id": entry.get("id", str(i)),
                        "gold_findings": entry.get("findings", ""),
                        "gold_impression": entry.get("impression", "")
                    })
                except Exception as e:
                    print(f"Error processing {image_path}: {e}")
                    
            if (i + 1) % 100 == 0:
                print(f"Indexed {i + 1}/{len(dataset)} images...")
                
        if embeddings:
            self.image_index = np.array(embeddings)
            self.metadata = metadata
            
            # Save to disk
            os.makedirs(os.path.dirname(index_save_path), exist_ok=True)
            np.save(index_save_path + ".npy", self.image_index)
            with open(index_save_path + "_meta.pkl", "wb") as f:
                pickle.dump(self.metadata, f)
            print(f"Successfully built and saved visual index with {len(embeddings)} images.")
        else:
            print("No images were successfully indexed.")

    def load_index(self, index_path: str):
        if os.path.exists(index_path + ".npy") and os.path.exists(index_path + "_meta.pkl"):
            self.image_index = np.load(index_path + ".npy")
            with open(index_path + "_meta.pkl", "rb") as f:
                self.metadata = pickle.load(f)
            return True
        return False

    def retrieve_similar(self, query_image_path: str, k: int = 3) -> list:
        if self.image_index is None or len(self.metadata) == 0:
            return []
            
        try:
            img = Image.open(query_image_path).convert("RGB")
            query_embedding = self.model.encode([img])
            
            scores = cosine_similarity(query_embedding, self.image_index)[0]
            
            # Get top k indices
            top_indices = np.argsort(scores)[::-1][:k]
            
            results = []
            for i in top_indices:
                results.append({
                    "id": self.metadata[i].get("id", "Unknown"),
                    "gold_findings": self.metadata[i].get("gold_findings", ""),
                    "gold_impression": self.metadata[i].get("gold_impression", ""),
                    "similarity_score": float(scores[i]),
                    "retrieval_method": "visual-CLIP"
                })
            return results
        except Exception as e:
            print(f"Retrieval error: {e}")
            return []
