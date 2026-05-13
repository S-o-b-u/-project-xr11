import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.preprocessing.report_parser import parse_report

def main():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    reports_dir = os.path.join(base_dir, "data", "raw", "reports")
    images_dir = os.path.join(base_dir, "data", "raw", "images")
    
    if not os.path.exists(reports_dir):
        print(f"Reports dir not found: {reports_dir}")
        return
        
    xml_files = [f for f in sorted(os.listdir(reports_dir)) if f.lower().endswith(".xml")]
    if not xml_files:
        print("No XML files found.")
        return
        
    # Open the FIRST xml file
    first_xml = xml_files[0]
    xml_path = os.path.join(reports_dir, first_xml)
    print(f"--- Processing {first_xml} ---")
    
    # Call parse_report with debug=True
    report = parse_report(xml_path, debug=True)
    
    # Print what image_ids were found
    image_ids = report.get("image_ids", [])
    print(f"\nExtracted image IDs: {image_ids}")
    
    # Build available_images dict to check
    available_images = {}
    if os.path.exists(images_dir):
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(".png") or filename.lower().endswith(".jpg"):
                image_id = filename.rsplit(".", 1)[0]
                available_images[image_id] = filename
                
    # Check if image files exist
    matched = []
    for img_id in image_ids:
        if img_id in available_images:
            matched.append(available_images[img_id])
            
    if matched:
        print(f"Found {len(matched)} matching images: {matched}")
    else:
        print("NO IMAGES FOUND")
        
    # Print first 5 entries from available_images
    print("\n--- Available Images Sample (first 5) ---")
    count = 0
    for img_id, filename in available_images.items():
        print(f"ID: {img_id} -> Filename: {filename}")
        count += 1
        if count >= 5:
            break

if __name__ == "__main__":
    main()
