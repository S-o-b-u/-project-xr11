import json
import os
import xml.etree.ElementTree as ET


def parse_report(xml_path: str, debug: bool = False) -> dict:
    """Parse a single IU X-ray XML file and extract findings, impression, and image IDs."""
    result = {"findings": "", "impression": "", "image_ids": []}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError:
        return result

    if debug:
        print("--- RAW XML ---")
        print(ET.tostring(root, encoding="unicode")[:2000])
        print("---------------")

    # 1. FINDINGS and IMPRESSION
    for node in root.iter("AbstractText"):
        label = node.attrib.get("Label", "").upper()
        # Use itertext() to handle nested tags like <italic> if they exist
        text = "".join(node.itertext()).strip()
        if label == "FINDINGS":
            result["findings"] = text
        elif label == "IMPRESSION":
            result["impression"] = text

    # 2. IMAGE IDs
    image_ids = []
    
    # Option A: <parentImage id="...">
    for tag in root.iter("parentImage"):
        img_id = tag.attrib.get("id", "").strip()
        if img_id:
            image_ids.append(img_id)
            
    # Option B: <image id="...">
    if not image_ids:
        for tag in root.iter("image"):
            img_id = tag.attrib.get("id", "").strip()
            if img_id:
                image_ids.append(img_id)
                
    # Option C: <figure id="...">
    if not image_ids:
        for tag in root.iter("figure"):
            img_id = tag.attrib.get("id", "").strip()
            if img_id:
                image_ids.append(img_id)

    result["image_ids"] = image_ids
    return result


def build_dataset(reports_dir: str, images_dir: str, output_path: str) -> list:
    """Build dataset.json by finding all XML reports and their matching images."""
    
    # Step 1 — scan images directory, build a lookup dict
    available_images = {}
    if os.path.exists(images_dir):
        for filename in os.listdir(images_dir):
            if filename.lower().endswith(".png") or filename.lower().endswith(".jpg"):
                image_id = filename.rsplit(".", 1)[0]  # strip extension
                available_images[image_id] = os.path.join(images_dir, filename)
    
    print(f"Found {len(available_images)} images in directory")

    # Step 2 — process each XML
    dataset = []
    total_count = 0
    no_text_count = 0
    no_image_count = 0

    if not os.path.exists(reports_dir):
        print(f"Reports directory not found: {reports_dir}")
        return []

    for xml_file in sorted(os.listdir(reports_dir)):
        if not xml_file.lower().endswith(".xml"):
            continue
            
        total_count += 1
        xml_path = os.path.join(reports_dir, xml_file)
        report = parse_report(xml_path)
        
        # Skip reports with missing text
        if not report["findings"] or not report["impression"]:
            no_text_count += 1
            continue
            
        # Find matching images
        matched_images = []
        for img_id in report["image_ids"]:
            if img_id in available_images:
                matched_images.append(available_images[img_id])
                
        if not matched_images:
            no_image_count += 1
            continue
            
        # Use FIRST matched image as primary
        primary_image = matched_images[0]
        
        dataset.append({
            "id": xml_file.replace(".xml", ""),
            "image_path": os.path.abspath(primary_image),  # Storing absolute for now, or rel if preferred
            "all_image_paths": [os.path.abspath(p) for p in matched_images],
            "gold_findings": report["findings"],
            "gold_impression": report["impression"]
        })

    # Print final stats
    print(f"Total XMLs processed: {total_count}")
    print(f"Skipped - no findings/impression: {no_text_count}")
    print(f"Skipped - no matching images: {no_image_count}")
    print(f"Successfully built: {len(dataset)} valid cases")
    
    # Save to output_path
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
        
    return dataset
