"""
Medical Image Embedding Engine.
Generates vector representations of X-ray images for retrieval.
"""

import numpy as np
from typing import List

class EmbeddingEngine:
    def __init__(self):
        """
        Initializes the embedding engine.
        Tries to load CLIP first. If it fails, falls back to ResNet50.
        """
        self.backend = None
        self.model = None
        self.text_model = None
        self.device = "cpu"

        try:
            import torch
            if torch.cuda.is_available():
                self.device = "cuda"

            from sentence_transformers import SentenceTransformer
            # Load CLIP ViT-B/32
            self.model = SentenceTransformer("clip-ViT-B-32", device=self.device)
            self.backend = "clip"
            print("Successfully loaded CLIP backend (clip-ViT-B-32).")

        except Exception as e:
            print(f"Failed to load CLIP backend: {e}. Falling back to ResNet50.")
            self.backend = "resnet"
            try:
                import torch
                import torchvision.models as models
                import torchvision.transforms as transforms
                
                # Load ResNet50
                resnet = models.resnet50(pretrained=True)
                # Remove the final FC layer (AdaptiveAvgPool2d is the second to last)
                self.model = torch.nn.Sequential(*(list(resnet.children())[:-1]))
                self.model.to(self.device)
                self.model.eval()
                
                self.transform = transforms.Compose([
                    transforms.ToTensor(),
                    transforms.Resize((224, 224), antialias=True),
                    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
                ])
                print("Successfully loaded ResNet50 backend.")
                
                # Try to load the text model for fallback
                try:
                    from sentence_transformers import SentenceTransformer
                    self.text_model = SentenceTransformer("all-MiniLM-L6-v2", device=self.device)
                    print("Successfully loaded text model fallback (all-MiniLM-L6-v2).")
                except Exception as ex:
                    print(f"Failed to load fallback text model: {ex}")
                    self.text_model = None

            except Exception as e2:
                print(f"Failed to load fallback ResNet50 backend: {e2}")

    def encode_image(self, image_array: np.ndarray) -> np.ndarray:
        """
        Encodes a single image into a normalized vector representation.
        
        Parameters
        ----------
        image_array : np.ndarray
            Numpy array of the image (grayscale or RGB).
            
        Returns
        -------
        np.ndarray
            The normalized embedding vector.
        """
        return self.batch_encode_images([image_array])[0]

    def encode_text(self, text: str) -> np.ndarray:
        """
        Encodes text into a normalized vector representation.
        
        Parameters
        ----------
        text : str
            The input string to encode.
            
        Returns
        -------
        np.ndarray
            The normalized text embedding.
        """
        if self.backend == "clip":
            embedding = self.model.encode([text], convert_to_numpy=True)[0]
            # Normalize for cosine similarity
            norm = np.linalg.norm(embedding)
            if norm > 0:
                embedding = embedding / norm
            return embedding
        elif self.backend == "resnet":
            if self.text_model is not None:
                embedding = self.text_model.encode([text], convert_to_numpy=True)[0]
                norm = np.linalg.norm(embedding)
                if norm > 0:
                    embedding = embedding / norm
                return embedding
            else:
                raise RuntimeError("Text model is not available in the fallback backend.")
        else:
            raise RuntimeError("No embedding backend is available.")

    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Computes cosine similarity between two embeddings.
        
        Parameters
        ----------
        embedding1 : np.ndarray
        embedding2 : np.ndarray
        
        Returns
        -------
        float
            The cosine similarity score (-1.0 to 1.0).
        """
        e1_norm = np.linalg.norm(embedding1)
        e2_norm = np.linalg.norm(embedding2)
        if e1_norm == 0 or e2_norm == 0:
            return 0.0
        sim = np.dot(embedding1, embedding2) / (e1_norm * e2_norm)
        return float(sim)

    def batch_encode_images(self, image_arrays: List[np.ndarray]) -> np.ndarray:
        """
        Encodes multiple images into a stacked array of embeddings.
        
        Parameters
        ----------
        image_arrays : list of np.ndarray
        
        Returns
        -------
        np.ndarray
            Stacked embedding vectors (N, D).
        """
        if not image_arrays:
            return np.array([])

        if self.backend == "clip":
            from PIL import Image
            pil_images = []
            for arr in image_arrays:
                # Convert grayscale to RGB if necessary
                if len(arr.shape) == 2:
                    arr = np.stack((arr,)*3, axis=-1)
                elif len(arr.shape) == 3 and arr.shape[-1] == 1:
                    arr = np.concatenate([arr]*3, axis=-1)
                
                # Convert float 0-1 to uint8 0-255
                if arr.dtype == np.float32 or arr.dtype == np.float64:
                    if arr.max() <= 1.0:
                        arr = (arr * 255).astype(np.uint8)
                    else:
                        arr = arr.astype(np.uint8)
                
                pil_images.append(Image.fromarray(arr))
                
            embeddings = self.model.encode(pil_images, convert_to_numpy=True)
            # L2 normalize
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
            norms[norms == 0] = 1
            return embeddings / norms

        elif self.backend == "resnet":
            import torch
            from PIL import Image
            
            tensors = []
            for arr in image_arrays:
                if len(arr.shape) == 2:
                    arr = np.stack((arr,)*3, axis=-1)
                elif len(arr.shape) == 3 and arr.shape[-1] == 1:
                    arr = np.concatenate([arr]*3, axis=-1)
                
                if arr.dtype == np.float32 or arr.dtype == np.float64:
                    if arr.max() <= 1.0:
                        arr = (arr * 255).astype(np.uint8)
                    else:
                        arr = arr.astype(np.uint8)
                
                pil_img = Image.fromarray(arr)
                t_img = self.transform(pil_img)
                tensors.append(t_img)
                
            batch = torch.stack(tensors).to(self.device)
            
            with torch.no_grad():
                features = self.model(batch)
            
            # features is (B, 2048, 1, 1), flatten it
            features = features.view(features.size(0), -1).cpu().numpy()
            
            # L2 normalize
            norms = np.linalg.norm(features, axis=1, keepdims=True)
            norms[norms == 0] = 1
            return features / norms
            
        else:
            raise RuntimeError("No image embedding backend is available.")

if __name__ == "__main__":
    print("Testing EmbeddingEngine...")
    engine = EmbeddingEngine()
    
    # Dummy image
    dummy_img = np.random.rand(224, 224).astype(np.float32)
    # Dummy text
    dummy_text = "Chest X-ray showing bilateral infiltrates"
    
    try:
        img_emb = engine.encode_image(dummy_img)
        print(f"\nImage Embedding Shape: {img_emb.shape}")
        
        text_emb = engine.encode_text(dummy_text)
        print(f"Text Embedding Shape: {text_emb.shape}")
        
        # Compute similarity (only makes sense if embedding dimensions match, like in CLIP)
        if img_emb.shape == text_emb.shape:
            sim = engine.compute_similarity(img_emb, text_emb)
            print(f"Cosine Similarity: {sim:.4f}")
        else:
            print(f"Cannot compute similarity directly: shape mismatch ({img_emb.shape} vs {text_emb.shape}). "
                  "This is expected when using the ResNet50 fallback backend.")
    except Exception as e:
        print(f"Test failed: {e}")
