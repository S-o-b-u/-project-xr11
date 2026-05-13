"""
image_processor.py
───────────────────
Utilities for loading and validating chest X-ray images.
Contains the legacy functions (preprocess_image, validate_image) for backward compatibility
and the new EnhancedImageProcessor for the V2 architecture pipeline.
"""

import os
from typing import Dict, Any

import numpy as np
from PIL import Image, UnidentifiedImageError

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    from PIL import ImageEnhance, ImageOps

# ---------------------------------------------------------------------------
# Legacy Functions (Kept for backward compatibility)
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# V2 Pipeline Classes
# ---------------------------------------------------------------------------

class EnhancedImageProcessor:
    """
    Enhanced medical image preprocessing pipeline for chest X-rays.
    Provides standardizations including CLAHE, Gaussian blurring,
    resizing, and region extraction for down-stream modeling.
    """

    def preprocess(self, image_path: str) -> Dict[str, Any]:
        """
        Executes the full preprocessing pipeline on a medical image.

        Steps:
        1. Load image as grayscale using Pillow.
        2. Convert to numpy array (float32).
        3. Normalize to 0-1 range.
        4. Apply CLAHE contrast enhancement (or fallback to PIL ImageEnhance).
        5. Apply Gaussian blur for noise reduction.
        6. Resize to 224x224.
        7. Apply histogram equalization.
        8. Detect lung field region.
        9. Compute quality score based on contrast.

        Parameters
        ----------
        image_path : str
            Path to the image file.

        Returns
        -------
        dict
            Dictionary containing the processed output and metadata.
            
        Raises
        ------
        ValueError
            If the image cannot be read or processed.
        """
        steps_done = []

        if not os.path.isfile(image_path):
            raise ValueError(f"Image not found or cannot be read: {image_path}")

        try:
            # a. Load image as grayscale using Pillow
            pil_img = Image.open(image_path).convert("L")
            original_size = pil_img.size  # (width, height)
            steps_done.append("Loaded as grayscale")

            # b. Convert to numpy array (float32)
            arr = np.array(pil_img, dtype=np.float32)
            steps_done.append("Converted to numpy float32")

            # c. Normalize to 0-1 range
            arr_min = arr.min()
            arr_max = arr.max()
            if arr_max > arr_min:
                arr = (arr - arr_min) / (arr_max - arr_min)
            else:
                arr = np.zeros_like(arr)
            steps_done.append("Normalized to 0-1 range")

            # d. Apply CLAHE contrast enhancement
            if HAS_CV2:
                # Convert back to uint8 0-255 for cv2 CLAHE
                arr_uint8 = (arr * 255).astype(np.uint8)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                arr_clahe = clahe.apply(arr_uint8)
                arr = arr_clahe.astype(np.float32) / 255.0
                steps_done.append("Applied OpenCV CLAHE")
            else:
                # Fallback to PIL ImageEnhance
                pil_enhance = Image.fromarray((arr * 255).astype(np.uint8))
                enhancer = ImageEnhance.Contrast(pil_enhance)
                pil_enhanced = enhancer.enhance(2.0)
                arr = np.array(pil_enhanced, dtype=np.float32) / 255.0
                steps_done.append("Applied PIL Contrast Enhancement (Fallback)")

            # e. Apply Gaussian blur for noise reduction (kernel 3x3, sigma 0.5)
            if HAS_CV2:
                # cv2.GaussianBlur expects uint8 or float32. We have float32.
                arr = cv2.GaussianBlur(arr, (3, 3), 0.5)
                steps_done.append("Applied OpenCV Gaussian Blur")
            else:
                steps_done.append("Skipped Gaussian Blur (cv2 missing)")

            # f. Resize to 224x224 for model input
            target_size = (224, 224)
            if HAS_CV2:
                arr = cv2.resize(arr, target_size, interpolation=cv2.INTER_LINEAR)
            else:
                pil_resized = Image.fromarray((arr * 255).astype(np.uint8)).resize(target_size, Image.Resampling.BILINEAR)
                arr = np.array(pil_resized, dtype=np.float32) / 255.0
            steps_done.append(f"Resized to {target_size}")

            # g. Apply histogram equalization as secondary pass
            if HAS_CV2:
                arr_uint8 = (arr * 255).astype(np.uint8)
                arr_eq = cv2.equalizeHist(arr_uint8)
                arr = arr_eq.astype(np.float32) / 255.0
                steps_done.append("Applied Histogram Equalization")
            else:
                pil_eq = ImageOps.equalize(Image.fromarray((arr * 255).astype(np.uint8)))
                arr = np.array(pil_eq, dtype=np.float32) / 255.0
                steps_done.append("Applied Histogram Equalization (Fallback)")

            # h. Detect approximate lung field region
            # We don't modify the image, just note that the step is done as we will call the method
            _ = self.get_lung_region(arr)
            steps_done.append("Detected approximate lung field")

            # i. Compute quality score = mean contrast (std of pixel values)
            quality_score = float(np.std(arr))
            quality_score = min(max(quality_score, 0.0), 1.0)
            steps_done.append("Computed quality score")

        except Exception as e:
            raise ValueError(f"Failed to process image '{image_path}': {e}") from e
            
        processed_pil = Image.fromarray((arr * 255).astype(np.uint8))

        return {
            "processed_image": processed_pil,
            "normalized_array": arr,
            "original_size": original_size,
            "processed_size": (224, 224),
            "preprocessing_steps": steps_done,
            "quality_score": quality_score
        }

    def get_lung_region(self, processed_array: np.ndarray) -> Dict[str, int]:
        """
        Calculates the bounding box for the approximate lung field region using a simple heuristic.
        (Center 60% of width, rows 20%-85% of height).

        Parameters
        ----------
        processed_array : np.ndarray
            The processed image array (2D).

        Returns
        -------
        dict
            A dictionary with 'top', 'bottom', 'left', 'right' integer indices.
        """
        height, width = processed_array.shape[:2]
        
        # Center 60% of width -> left 20%, right 80%
        left = int(width * 0.20)
        right = int(width * 0.80)
        
        # Rows 20%-85% of height
        top = int(height * 0.20)
        bottom = int(height * 0.85)

        return {
            "top": top,
            "bottom": bottom,
            "left": left,
            "right": right
        }

    def prepare_for_clip(self, processed_array: np.ndarray) -> np.ndarray:
        """
        Converts a 2D grayscale numpy array to a 3-channel RGB array by stacking channels.
        This is required for models like CLIP which expect 3 channels.

        Parameters
        ----------
        processed_array : np.ndarray
            The 2D grayscale image array.

        Returns
        -------
        np.ndarray
            The 3D numpy array representing the image in RGB.
        """
        if len(processed_array.shape) == 2:
            return np.stack((processed_array,) * 3, axis=-1)
        return processed_array


if __name__ == "__main__":
    import tempfile

    print("Testing EnhancedImageProcessor...")
    processor = EnhancedImageProcessor()
    
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
        # Create a dummy 512x512 white image
        dummy_img = np.ones((512, 512), dtype=np.uint8) * 255
        Image.fromarray(dummy_img).save(tmp.name)
        tmp_path = tmp.name

    try:
        result = processor.preprocess(tmp_path)
        print("\nPreprocess Result Keys:")
        for k in result.keys():
            print(f"- {k}")
        
        print(f"\nOriginal Size: {result['original_size']}")
        print(f"Processed Size: {result['processed_size']}")
        print(f"Quality Score: {result['quality_score']:.4f}")
        
        lung_region = processor.get_lung_region(result["normalized_array"])
        print(f"\nLung Region Box: {lung_region}")
        
        clip_ready = processor.prepare_for_clip(result["normalized_array"])
        print(f"CLIP Ready Array Shape: {clip_ready.shape}")
        
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
