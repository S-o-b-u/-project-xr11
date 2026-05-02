"""
report_parser.py
────────────────
Parses IU X-ray XML reports and pairs them with their corresponding PNG
images to produce a clean JSON dataset.

Image matching strategy
~~~~~~~~~~~~~~~~~~~~~~~
IU X-ray XML files (1.xml, 2.xml …) embed the real image stem inside a
``<parentImage id="CXR1_1_IM-0001-3001">`` tag.  We extract that id and
look for ``{id}.png`` in images_dir — we never rely on the XML filename.
"""

import json
import os
import xml.etree.ElementTree as ET


def _extract_parent_image_id(root: ET.Element) -> str | None:
    """Return the ``id`` attribute of the first ``<parentImage>`` element, or None."""
    for node in root.iter("parentImage"):
        img_id = node.attrib.get("id", "").strip()
        if img_id:
            return img_id
    return None


def parse_report(xml_path: str) -> dict:
    """Parse a single IU X-ray XML file.

    Extracts:
    * ``findings``   — text of ``<AbstractText Label="FINDINGS">``
    * ``impression`` — text of ``<AbstractText Label="IMPRESSION">``
    * ``image_id``   — ``id`` attribute of the first ``<parentImage>`` tag

    Parameters
    ----------
    xml_path : str
        Absolute or relative path to the ``.xml`` report file.

    Returns
    -------
    dict
        ``{"findings": str, "impression": str, "image_id": str | None}``
        Text fields are empty strings when absent; ``image_id`` is None when
        the ``<parentImage>`` tag is missing.
    """
    result = {"findings": "", "impression": "", "image_id": None}

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError:
        return result

    for node in root.iter("AbstractText"):
        label = node.attrib.get("Label", "").upper()
        text = (node.text or "").strip()
        if label == "FINDINGS":
            result["findings"] = text
        elif label == "IMPRESSION":
            result["impression"] = text

    result["image_id"] = _extract_parent_image_id(root)
    return result


def build_dataset(reports_dir: str, images_dir: str, output_path: str) -> list:
    """Build a dataset JSON from XML reports matched via ``<parentImage id>``.

    For each XML file the function:
    1. Parses the XML tree.
    2. Extracts the ``id`` attribute from the first ``<parentImage>`` tag.
    3. Looks for ``{id}.png`` in *images_dir*.
    4. Adds the entry only when the image exists **and** the findings/
       impression pass the quality checks.

    The XML filename stem is **never** used for image matching.

    Parameters
    ----------
    reports_dir : str
        Directory containing ``.xml`` IU X-ray report files.
    images_dir : str
        Directory containing ``.png`` chest X-ray images.
    output_path : str
        Destination path for the output ``dataset.json`` file.

    Returns
    -------
    list[dict]
        List of valid entries: ``{id, image_path, gold_findings, gold_impression}``.
    """
    xml_files = sorted(
        f for f in os.listdir(reports_dir) if f.lower().endswith(".xml")
    )
    total = len(xml_files)
    dataset = []

    for xml_name in xml_files:
        xml_path = os.path.join(reports_dir, xml_name)
        report_id = os.path.splitext(xml_name)[0]  # e.g. "1" from "1.xml"

        # ── Parse XML ──────────────────────────────────────────────────────
        report = parse_report(xml_path)
        findings  = report["findings"]
        impression = report["impression"]
        image_id   = report["image_id"]   # e.g. "CXR1_1_IM-0001-3001"

        # ── Require a <parentImage> tag ────────────────────────────────────
        if not image_id:
            print(f"[SKIP] {xml_name}: no <parentImage> tag found")
            continue

        # ── Check the specific {image_id}.png exists ───────────────────────
        image_path = os.path.join(images_dir, f"{image_id}.png")
        if not os.path.isfile(image_path):
            print(f"[SKIP] {xml_name}: image '{image_id}.png' not found")
            continue

        # ── Quality filters on text ────────────────────────────────────────
        if not findings or not impression:
            continue
        if findings.lower().strip() in ("xxxx", "x", ""):
            continue
        if len(findings) < 20:
            continue

        dataset.append({
            "id": report_id,
            "image_path": os.path.abspath(image_path),
            "gold_findings": findings,
            "gold_impression": impression,
        })

    # ── Persist ────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(dataset, fp, indent=2, ensure_ascii=False)

    print(f"Built dataset: {len(dataset)} valid cases from {total} total XML files")
    return dataset
