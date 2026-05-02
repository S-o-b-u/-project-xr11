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

    test_case = dataset[0]
    image_path = test_case["image_path"]

    print(f"🚀 INITIALIZING XR11 FULL VERIFIED PIPELINE 🚀")
    print(f"Testing with image: {image_path}")
    print("-" * 50)
    print("Running pipeline... (Please wait ~30 seconds. Making exactly 5 API calls...) \n")

    try:
        generator = ReportGenerator()
        result = generator.generate_report(image_path)

        print("\n=== 🧠 1. FINAL STRUCTURED REPORT ===")
        print(json.dumps(result.get("final_report", {}), indent=2))

        print("\n=== ⚖️ 2. NLI LOGIC CHECK ===")
        print(json.dumps(result.get("verification", {}).get("nli_results", {}), indent=2))
        
        print("\n=== 🧬 3. RADLEX KNOWLEDGE GRAPH MATCHES ===")
        kg = result.get("verification", {}).get("kg_results", {})
        print(f"Standardization Rate: {kg.get('standardization_rate', 0)}")
        print("Matched ICD-10 Codes:", kg.get("icd10_codes", []))
        
        print("\n=== 🚨 4. HALLUCINATION DETECTION ===")
        hal = result.get("verification", {}).get("hallucination_results", {})
        print(f"Overall Risk: {hal.get('overall_risk', 'UNKNOWN')}")
        print(f"Safe to Use: {hal.get('safe_to_use', False)}")

    except Exception as e:
        print(f"Critical Pipeline Failure: {e}")

if __name__ == "__main__":
    test_ultimate_pipeline()