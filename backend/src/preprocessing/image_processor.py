"""
image_processor.py
───────────────────
Utilities for loading and validating chest X-ray images before sending
them to the Gemini VLM.  Images are NOT resized so the model receives
full native resolution.
"""

import os
from PIL import Image, UnidentifiedImageError


def preprocess_image(image_path: str) -> Image.Image:
    """Open an image and ensure it is in RGB mode.

    Grayscale chest X-rays (mode 'L') are converted to RGB so that
    Gemini's vision endpoint can accept them without further changes.

    Parameters
    ----------
    image_path : str
        Path to the PNG or JPEG image file.

    Returns
    -------
    PIL.Image.Image
        The opened image in RGB mode at its original resolution.

    Raises
    ------
    FileNotFoundError
        If *image_path* does not point to an existing file.
    RuntimeError
        If Pillow cannot decode the file.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")

    try:
        image = Image.open(image_path)
        image.load()  # force decoding so corrupt files fail early
    except (UnidentifiedImageError, OSError) as exc:
        raise RuntimeError(f"Failed to open image '{image_path}': {exc}") from exc

    return image.convert("RGB")


def validate_image(image_path: str) -> bool:
    """Check whether a file exists and is a readable PNG or JPEG image.

    Parameters
    ----------
    image_path : str
        Path to the candidate image file.

    Returns
    -------
    bool
        ``True`` if the file exists and Pillow can open it; ``False`` otherwise.
    """
    if not os.path.isfile(image_path):
        return False

    # Quick extension guard (optional but fast)
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in {".png", ".jpg", ".jpeg"}:
        return False

    try:
        img = Image.open(image_path)
        img.verify()  # verify header integrity without decoding the whole file
        return True
    except Exception:
        return False
