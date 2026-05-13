import os
import sys
import json

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.medical_models.medclip_retriever import VisualRetriever

def main():
    dataset_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'dataset.json')
    index_save_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed', 'visual_index')
    
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}")
        return
        
    print(f"Loading dataset from {dataset_path}...")
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
        
    print(f"Loaded {len(dataset)} items.")
    
    retriever = VisualRetriever()
    print("Building visual index...")
    retriever.build_image_index(dataset, index_save_path)
    
if __name__ == "__main__":
    main()
