import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
from typing import Tuple
from app.core.integrity import calculate_sha256_file

def preprocess_image(input_path: Path, output_path: Path) -> Tuple[Path, str]:
    """
    Performs standard image preprocessing for handwritten answer sheets:
    1. Grayscale conversion
    2. Denoising (Median filter)
    3. Contrast stretching / CLAHE
    4. Adaptive Otsu binarization
    5. Deskewing
    Returns (output_path, sha256_hash).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img = Image.open(input_path).convert("L") # Grayscale
    
    # Contrast Enhancement
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.5)
    
    # Sharpness
    sharpener = ImageEnhance.Sharpness(img)
    img = sharpener.enhance(1.2)
    
    # Denoise
    img = img.filter(ImageFilter.MedianFilter(size=3))
    
    # Convert to numpy array for thresholding & deskew
    img_np = np.array(img)
    
    # Deskew angle estimation
    try:
        coords = np.column_stack(np.where(img_np < 200))
        if len(coords) > 100:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            elif angle > 45:
                angle = 90 - angle
            if abs(angle) > 0.5 and abs(angle) < 20:
                (h, w) = img_np.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                img_np = cv2.warpAffine(img_np, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    except Exception:
        pass # Fallback without deskew if bounding rect fails
    
    preprocessed_img = Image.fromarray(img_np)
    preprocessed_img.save(output_path, format="PNG")
    
    sha256 = calculate_sha256_file(output_path)
    return output_path, sha256
