import json
import os
from src.model.report_generator import ReportGenerator

def test_ultimate_pipeline():
    dataset_path = "data/processed/dataset.json"
    
    if not os.path.exists(dataset_path):
        print("Dataset not found!")
        return

    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    # Let's test the very first image
    test_case = dataset[0]
    image_path = test_case["image_path"]

    print(f"🚀 INITIALIZING XR11 FULL PIPELINE 🚀")
    print(f"Testing with image: {image_path}")
    print(f"Gold Standard Impression: {test_case['gold_impression']}")
    print("-" * 50)
    
    # Warning the user about the time it takes
    print("Running pipeline... (Please wait 15-30 seconds.")
    print("The system is currently making 7 separate API calls to Google...) \n")

    try:
        generator = ReportGenerator()
        result = generator.generate_report(image_path)

        print("=== 🧠 1. RAG MEMORY ===")
        if result.get("rag_context_used"):
            print("Successfully retrieved historical cases to ground the AI.")
        else:
            print("No RAG context used / RAG failed.")

        print("\n=== 🎲 2. UNCERTAINTY ANALYSIS (Safety Net) ===")
        print(json.dumps(result.get("uncertainty", {}), indent=2))

        print("\n=== ✍️ 3. FINAL STRUCTURED REPORT (After 2-Round Refinement) ===")
        print(json.dumps(result.get("final_report", {}), indent=2))

    except Exception as e:
        print(f"Critical Pipeline Failure: {e}")

if __name__ == "__main__":
    test_ultimate_pipeline()