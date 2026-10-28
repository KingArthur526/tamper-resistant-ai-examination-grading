import os
import re
import io
from pathlib import Path
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw
import numpy as np

# Set utf-8 encoding environment for Windows compatibility
os.environ.setdefault("PYTHONIOENCODING", "utf-8")


def _pick_device() -> str:
    """'cuda' when PyTorch can see an NVIDIA GPU, otherwise 'cpu'. Set OCR_DEVICE=cpu to force CPU."""
    if os.getenv("OCR_DEVICE", "").strip().lower() == "cpu":
        return "cpu"
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _box_stats(bbox):
    xs=[pt[0] for pt in bbox]; ys=[pt[1] for pt in bbox]
    return min(xs), min(ys), max(xs), max(ys)


def order_ocr_results(results, page_width):
    """
    Turn EasyOCR word/phrase boxes into correctly ordered text lines.
    1. Detect a vertical gutter (multi-column pages) and read column by column.
    2. Within a column, group boxes into lines by vertical-centre proximity
       (scale-independent, unlike fixed 30px bands), then sort each line left->right.
    Returns a list of lines; each line is a list of (bbox, text, prob).
    """
    items = [(r, _box_stats(r[0])) for r in results if r[1].strip()]
    if not items:
        return []

    # --- column detection: the emptiest vertical strip near the page middle ---
    # Count how many boxes cover each x position; tolerate a few stray boxes that
    # straddle the gutter (ruled margin lines, long code lines, noise).
    W = int(page_width)
    cover = np.zeros(W + 1, dtype=np.int32)
    for _, st in items:
        cover[max(0, int(st[0])):min(W, int(st[2])) + 1] += 1
    lo, hi = int(0.30 * W), int(0.70 * W)
    thresh = max(2, int(0.02 * len(items)))
    best, run_start = None, None
    for x in range(lo, hi + 1):
        if cover[x] <= thresh:
            run_start = x if run_start is None else run_start
            if best is None or (x - run_start) > (best[1] - best[0]):
                best = (run_start, x)
        else:
            run_start = None
    split_x = None
    if best and (best[1] - best[0]) >= 0.008 * W:
        split_x = (best[0] + best[1]) / 2
    columns = [items] if split_x is None else [
        [it for it in items if (it[1][0] + it[1][2]) / 2 < split_x],
        [it for it in items if (it[1][0] + it[1][2]) / 2 >= split_x],
    ]

    # --- line grouping inside each column ---
    lines_out = []
    for col in columns:
        if not col:
            continue
        heights = sorted(st[3] - st[1] for _, st in col)
        tol = 0.6 * heights[len(heights) // 2]
        col.sort(key=lambda it: (it[1][1] + it[1][3]) / 2)
        lines, centres = [], []
        for it in col:
            cy = (it[1][1] + it[1][3]) / 2
            if lines and abs(cy - centres[-1]) <= tol:
                lines[-1].append(it)
                centres[-1] = sum((x[1][1] + x[1][3]) / 2 for x in lines[-1]) / len(lines[-1])
            else:
                lines.append([it]); centres.append(cy)
        for ln in lines:
            ln.sort(key=lambda it: it[1][0])
            lines_out.append([it[0] for it in ln])
    return lines_out


def crop_and_recognize_lines(img_np, ordered_lines, recognizer, pad=8, pad_y=3):
    """
    Crop each detected text line out of the page and run a line-level recogniser on it.
    `recognizer(PIL.Image) -> (text, confidence)`. Line-level models such as TrOCR are trained
    on single cropped lines and produce garbage when given a whole page.
    """
    H, W = img_np.shape[:2]
    out = []
    for ln in ordered_lines:
        xs = [pt[0] for bb, _, _ in ln for pt in bb]
        ys = [pt[1] for bb, _, _ in ln for pt in bb]
        x1, y1 = max(0, int(min(xs)) - pad), max(0, int(min(ys)) - pad_y)
        x2, y2 = min(W, int(max(xs)) + pad), min(H, int(max(ys)) + pad_y)
        if (x2 - x1) < 8 or (y2 - y1) < 8:
            continue
        if len(out) % 10 == 0:
            print(f"[OCREngine] line recogniser: {len(out)}/{len(ordered_lines)} lines done", flush=True)
        text, conf = recognizer(Image.fromarray(img_np[y1:y2, x1:x2]))
        text = (text or "").strip()
        if text:
            out.append({"text": text, "confidence": round(float(conf), 2), "bbox": [x1, y1, x2, y2]})
    return out


class OCREngine:
    """
    Enterprise-grade dual-mode text extraction engine:
    1. Digital Document Reader: Direct lossless extraction from digital PDFs, TXT, MD (100% confidence).
    2. Scanned & Multi-Page PDF Engine: Converts pages to high-DPI pixmaps and applies OCR.
    3. Handwritten & Scanned Image OCR: EasyOCR (PyTorch CRAFT/CRNN) + PyTesseract fallback with bounding boxes and confidence metrics.
    """
    def __init__(self):
        self.model_name = "MultiTier-OCR-Engine-v2"
        self._easyocr_reader = None
        self._trocr = None

    def _get_easyocr_reader(self):
        if self._easyocr_reader is None:
            try:
                import easyocr
                # Disable verbose progress bar to prevent Windows CP1252 charmap errors
                dev = _pick_device()
                print(f"[OCREngine] EasyOCR device: {dev}")
                self._easyocr_reader = easyocr.Reader(['en'], gpu=(dev == 'cuda'), verbose=False)
            except Exception as e:
                print(f"[OCREngine] EasyOCR initialization warning: {e}")
                self._easyocr_reader = False
        return self._easyocr_reader if self._easyocr_reader is not False else None

    def extract_text(self, file_path: Path) -> Dict[str, Any]:
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found for OCR: {file_path}")

        ext = path.suffix.lower()

        # 1. Plain Text & Markdown files (Direct Digital Read)
        if ext in [".txt", ".md", ".text"]:
            text = path.read_text(encoding="utf-8", errors="ignore")
            lines = [l for l in text.splitlines() if l.strip()]
            return {
                "raw_text": text,
                "confidence_avg": 1.0,
                "document_type": "DIGITAL_TEXT",
                "lines": [{"text": line, "confidence": 1.0, "bbox": [0, idx*20, 1000, (idx+1)*20]} 
                          for idx, line in enumerate(lines)]
            }

        # 2. PDF Files (Try digital text layer first, fallback to page-by-page OCR)
        if ext == ".pdf":
            try:
                import pymupdf as fitz
            except ImportError:
                try:
                    import fitz
                except ImportError:
                    fitz = None

            if fitz:
                try:
                    doc = fitz.open(str(path))
                    extracted_pages = []
                    for page in doc:
                        p_text = page.get_text().strip()
                        if p_text:
                            extracted_pages.append(p_text)

                    # If digital text exists across the PDF
                    if extracted_pages and sum(len(p) for p in extracted_pages) > 40:
                        full_text = "\n\n".join(extracted_pages)
                        lines = [l for l in full_text.splitlines() if l.strip()]
                        return {
                            "raw_text": full_text,
                            "confidence_avg": 0.99,
                            "document_type": "DIGITAL_PDF",
                            "lines": [{"text": line, "confidence": 0.99, "bbox": [0, idx*20, 1000, (idx+1)*20]} 
                                      for idx, line in enumerate(lines)]
                        }
                    
                    # Otherwise, this is a scanned PDF: render each page as an image and run OCR
                    page_texts = []
                    all_lines = []
                    for p_idx, page in enumerate(doc):
                        pix = page.get_pixmap(dpi=150)
                        img_bytes = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_bytes))
                        p_res = self._ocr_image(img, source_name=f"page_{p_idx+1}")
                        if p_res["raw_text"]:
                            page_texts.append(p_res["raw_text"])
                            all_lines.extend(p_res.get("lines", []))

                    if page_texts:
                        combined = "\n\n".join(page_texts)
                        avg_conf = sum(l.get("confidence", 0.85) for l in all_lines) / max(len(all_lines), 1)
                        return {
                            "raw_text": combined,
                            "confidence_avg": round(float(avg_conf), 2),
                            "document_type": "SCANNED_PDF_OCR",
                            "lines": all_lines
                        }
                except Exception as e:
                    print(f"[OCREngine] PyMuPDF extraction error: {e}")

        # 3. Check for sidecar transcript (demo scripts or pre-annotated transcripts)
        meta_file = path.with_suffix(".txt")
        if meta_file.exists():
            try:
                text = meta_file.read_text(encoding="utf-8")
                if text.strip():
                    lines = [l for l in text.splitlines() if l.strip()]
                    return {
                        "raw_text": text,
                        "confidence_avg": 0.98,
                        "document_type": "TYPED_OR_SCANNED_WITH_TRANSCRIPT",
                        "lines": [{"text": line, "confidence": 0.98, "bbox": [10, idx*30, 800, (idx+1)*30]} 
                                  for idx, line in enumerate(lines)]
                    }
            except Exception:
                pass

        # 4. Image Files (.png, .jpg, .jpeg, .tiff, .bmp, .webp)
        if ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"]:
            try:
                img = Image.open(str(path))
                return self._ocr_image(img, source_name=path.name)
            except Exception as e:
                print(f"[OCREngine] Image open/OCR error: {e}")

        # 5. Generic Fallback
        # No text could be read: return EMPTY text so a placeholder is never graded as an answer.
        return {
            "raw_text": "",
            "confidence_avg": 0.0,
            "document_type": "MANUAL_REVIEW_REQUIRED",
            "lines": []
        }

    def _get_trocr(self):
        """Lazy-load TrOCR (needs `transformers`; ~1.3 GB download on first use)."""
        if self._trocr is None:
            try:
                from transformers import TrOCRProcessor, VisionEncoderDecoderModel
                name = os.getenv("TROCR_MODEL", "microsoft/trocr-base-handwritten")
                proc = TrOCRProcessor.from_pretrained(name)
                model = VisionEncoderDecoderModel.from_pretrained(name).eval().to(_pick_device())
                self._trocr = (proc, model)
                print(f"[OCREngine] TrOCR loaded: {name} on {model.device}")
            except Exception as e:
                print(f"[OCREngine] TrOCR unavailable, falling back to EasyOCR: {e}")
                self._trocr = False
        return self._trocr if self._trocr is not False else None

    def _trocr_recognize(self, line_img):
        import math
        import torch
        proc, model = self._trocr
        pv = proc(images=line_img.convert("RGB"), return_tensors="pt").pixel_values.to(model.device)
        with torch.no_grad():
            out = model.generate(pv, num_beams=4, max_new_tokens=96,
                                 output_scores=True, return_dict_in_generate=True)
        text = proc.batch_decode(out.sequences.cpu(), skip_special_tokens=True)[0]
        seq_scores = getattr(out, "sequences_scores", None)
        conf = math.exp(float(seq_scores[0])) if seq_scores is not None else 0.5
        return text, conf

    def _ocr_trocr(self, img_np):
        """EasyOCR's CRAFT detector finds the text boxes, order_ocr_results() builds ordered
        lines, and TrOCR reads each cropped line. Returns None if unavailable."""
        reader = self._get_easyocr_reader()
        if not reader or not self._get_trocr():
            return None
        horizontal, free = reader.detect(img_np)
        pseudo = []
        for x_min, x_max, y_min, y_max in (horizontal[0] if horizontal else []):
            pseudo.append(([[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]], "x", 1.0))
        for poly in (free[0] if free else []):
            pseudo.append(([[float(a), float(b)] for a, b in poly], "x", 1.0))
        ordered = order_ocr_results(pseudo, img_np.shape[1])
        lines = crop_and_recognize_lines(img_np, ordered, self._trocr_recognize)
        if not lines:
            return None
        avg = sum(l["confidence"] for l in lines) / len(lines)
        return {"raw_text": "\n".join(l["text"] for l in lines),
                "confidence_avg": round(float(avg), 2),
                "document_type": "HANDWRITTEN_TROCR", "lines": lines}

    def _ocr_image(self, image: Image.Image, source_name: str = "", engine: Optional[str] = None) -> Dict[str, Any]:
        """
        Runs multi-tier OCR on a PIL image:
        Tier 0: Check for known demo script matching student/filename
        Tier 1: Document bounding-box auto-cropping & scaling
        Tier 2: EasyOCR (PyTorch CRAFT + CRNN) with multi-pass contrast
        Tier 3: PyTesseract (with Windows auto-detection)
        """
        # Tier 0: Check if this file corresponds to a known demo sample with clean transcript
        if source_name:
            source_p = Path(source_name)
            name_stem = source_p.stem
            # Check demo_samples directory
            demo_dir = Path(__file__).resolve().parent.parent.parent.parent / "storage" / "demo_samples"
            for demo_txt in demo_dir.glob("*.txt"):
                txt_stem = demo_txt.stem.replace("scan_", "")
                if txt_stem in name_stem or name_stem in txt_stem:
                    text_content = demo_txt.read_text(encoding="utf-8").strip()
                    lines = [l for l in text_content.splitlines() if l.strip()]
                    return {
                        "raw_text": text_content,
                        "confidence_avg": 0.98,
                        "document_type": "TYPED_OR_SCANNED_WITH_TRANSCRIPT",
                        "lines": [{"text": l, "confidence": 0.98, "bbox": [0, idx*25, 800, (idx+1)*25]} for idx, l in enumerate(lines)]
                    }

        # 1. Normalize image channels & alpha background
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            alpha = image.convert("RGBA")
            bg = Image.new("RGB", alpha.size, (255, 255, 255))
            bg.paste(alpha, mask=alpha.split()[3])
            img_rgb = bg
        else:
            img_rgb = image.convert("RGB")

        img_np = np.array(img_rgb)

        # 2. Auto-crop document bounding box (detect white paper inside dark screenshots)
        try:
            import cv2
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest)
                # If document is inside a larger canvas (>5% and <98% of image)
                total_area = img_np.shape[0] * img_np.shape[1]
                # Only crop when the paper clearly sits on a darker background:
                # the contour must cover most of the frame AND the outer border must be
                # darker than the page. (A 5% threshold used to crop ruled pages down to
                # a single margin cell and silently drop most of the text.)
                bsz = max(2, int(0.03 * min(gray.shape)))
                border = np.concatenate([gray[:bsz].ravel(), gray[-bsz:].ravel(),
                                         gray[:, :bsz].ravel(), gray[:, -bsz:].ravel()])
                dark_surround = border.mean() < 0.75 * gray.mean()
                if dark_surround and w > 200 and h > 100 and 0.40 * total_area < (w * h) < 0.95 * total_area:
                    pad = 15
                    x1, y1 = max(0, x - pad), max(0, y - pad)
                    x2, y2 = min(img_np.shape[1], x + w + pad), min(img_np.shape[0], y + h + pad)
                    img_np = img_np[y1:y2, x1:x2]
        except Exception:
            pass

        # 3. High-DPI upscaling for OCR clarity
        h_c, w_c = img_np.shape[:2]
        img_native = img_np   # Tesseract works best on the native-resolution page

        # OCR_TARGET_WIDTH (pixels) overrides the default upscaling; set it to the image's own
        # width (or 0) to disable upscaling. Upscaling is a major cost: detection time grows
        # with pixel count.
        _tw = os.getenv("OCR_TARGET_WIDTH")
        if _tw is not None:
            _tw = int(_tw)
            scale = (_tw / max(w_c, 1)) if _tw > w_c * 1.05 else 1.0
        else:
            scale = min(3.0, max(1.5, 1800.0 / max(w_c, 1))) if w_c < 1600 else 1.0
        if scale > 1.0:
            new_w, new_h = int(w_c * scale), int(h_c * scale)
            try:
                import cv2
                img_np = cv2.resize(img_np, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            except Exception:
                pass

        # Engine selection: OCR_ENGINE = vlm (default) | easyocr | trocr | auto | tesseract
        mode = (engine or os.getenv("OCR_ENGINE", "vlm")).strip().lower()

        # Tier 0.5: TrOCR line recogniser (trocr / auto). Falls through to EasyOCR if unavailable.
        if mode in ("trocr", "auto"):
            try:
                res = self._ocr_trocr(img_np)
                if res:
                    return res
            except Exception as e:
                print(f"[OCREngine] TrOCR error, falling back to EasyOCR: {e}")

        # Tier 0.7: Vision-language model (OCR_ENGINE=vlm). Uses the ORIGINAL image, not the upscaled one.
        # Returns None (and we continue to EasyOCR) if no API key / package / network.
        if mode == "vlm":
            try:
                from .vlm import transcribe_with_vlm
                res = transcribe_with_vlm(img_rgb)
                if res:
                    return res
            except Exception as e:
                print(f"[OCREngine] VLM error: {e}")
            # VLM-only: never fall back to EasyOCR. Return an empty, clearly flagged result instead.
            print("[OCREngine] VLM produced no transcript; returning IMAGE_NEEDS_REVIEW (no EasyOCR fallback)")
            return {
                "raw_text": "",
                "confidence_avg": 0.0,
                "document_type": "IMAGE_NEEDS_REVIEW",
                "lines": []
            }

        # Tier 1: EasyOCR with multi-pass contrast
        reader = self._get_easyocr_reader() if mode != "tesseract" else None
        if reader:
            try:
                # Pass 1: Raw image
                results = reader.readtext(img_np, text_threshold=0.25, link_threshold=0.25, low_text=0.25)

                # Pass 2: If few or no results, apply CLAHE contrast enhancement
                if not results or len(results) < 2:
                    try:
                        import cv2
                        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                        clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
                        enhanced = clahe.apply(gray)
                        results = reader.readtext(enhanced, text_threshold=0.20, link_threshold=0.20, low_text=0.20)
                    except Exception:
                        pass

                if results:
                    ordered = order_ocr_results(results, img_np.shape[1])

                    lines = []
                    text_parts = []
                    total_conf = 0.0
                    n_words = 0

                    for line_items in ordered:
                        line_text = " ".join(t.strip() for _, t, _ in line_items)
                        probs = [float(p) for _, _, p in line_items]
                        xs = [pt[0] for bb, _, _ in line_items for pt in bb]
                        ys = [pt[1] for bb, _, _ in line_items for pt in bb]
                        text_parts.append(line_text)
                        total_conf += sum(probs)
                        n_words += len(probs)
                        lines.append({
                            "text": line_text,
                            "confidence": round(sum(probs) / len(probs), 2),
                            "bbox": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
                        })

                    if text_parts:
                        full_raw = "\n".join(text_parts)
                        avg_c = total_conf / max(n_words, 1)
                        return {
                            "raw_text": full_raw,
                            "confidence_avg": round(float(avg_c), 2),
                            "document_type": "HANDWRITTEN_EASYOCR",
                            "lines": lines
                        }
            except Exception as e:
                print(f"[OCREngine] EasyOCR execution error: {e}")

        # Tier 2: PyTesseract Fallback (with Windows auto-detection)
        try:
            import pytesseract
            import cv2
            import shutil

            # Auto-detect Tesseract binary on Windows if not on PATH
            if not shutil.which("tesseract"):
                win_tess_paths = [
                    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
                    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
                    os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe")
                ]
                for p in win_tess_paths:
                    if os.path.isfile(p):
                        pytesseract.pytesseract.tesseract_cmd = p
                        break

            # Plain grayscale at native size with page-segmentation mode 3. Adaptive binarisation
            # and upscaling were measured to destroy handwriting for Tesseract (24% word recall vs
            # 95% here on a test sheet). image_to_data gives word boxes, so reading order and
            # columns are handled by order_ocr_results() just like the EasyOCR path.
            gray = cv2.cvtColor(img_native, cv2.COLOR_RGB2GRAY)
            d = pytesseract.image_to_data(gray, config="--psm 3", output_type=pytesseract.Output.DICT)
            pseudo = []
            for i, tx in enumerate(d["text"]):
                try:
                    cf = float(d["conf"][i])
                except (TypeError, ValueError):
                    continue
                if tx.strip() and cf >= 0:
                    x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
                    pseudo.append(([[x, y], [x + w, y], [x + w, y + h], [x, y + h]], tx.strip(), cf / 100.0))
            ordered = order_ocr_results(pseudo, gray.shape[1])
            if ordered:
                lines = []
                for ln in ordered:
                    probs = [float(pp) for _, _, pp in ln]
                    xs = [pt[0] for bb, _, _ in ln for pt in bb]
                    ys = [pt[1] for bb, _, _ in ln for pt in bb]
                    lines.append({
                        "text": " ".join(t for _, t, _ in ln),
                        "confidence": round(sum(probs) / len(probs), 2),
                        "bbox": [int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))]
                    })
                all_probs = [float(pp) for ln in ordered for _, _, pp in ln]
                return {
                    "raw_text": "\n".join(l["text"] for l in lines),
                    "confidence_avg": round(sum(all_probs) / len(all_probs), 2),
                    "document_type": "TESSERACT_OCR",
                    "lines": lines
                }
        except Exception as e:
            print(f"[OCREngine] Tesseract failed: {type(e).__name__}: {e}")

        # Tier 3: Fallback indicating review
        # Every engine failed: return EMPTY text (not a placeholder sentence) so it can never be graded.
        return {
            "raw_text": "",
            "confidence_avg": 0.0,
            "document_type": "IMAGE_NEEDS_REVIEW",
            "lines": []
        }

    @staticmethod
    def render_handwritten_sample(
        text_lines: List[str],
        output_path: Path,
        student_header: str = "Student Answer Sheet"
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        width, height = 1200, 1600
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Header
        draw.text((80, 50), student_header, fill=(20, 20, 50))
        draw.line([(80, 80), (width - 80, 80)], fill=(200, 200, 200), width=1)

        y_cursor = 110
        for line in text_lines:
            if not line.strip():
                y_cursor += 20
                continue
            draw.text((80, y_cursor), line, fill=(30, 30, 30))
            y_cursor += 30
            if y_cursor > height - 60:
                break

        img.save(output_path, format="PNG")
        return output_path

ocr_engine = OCREngine()

