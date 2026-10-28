"""
Compare OCR engines on one answer-sheet image, so you can choose using real results.

    python compare_ocr.py path\\to\\sheet.jpg                  # engines: easyocr, tesseract, trocr
    python compare_ocr.py sheet.jpg --truth truth.txt         # also prints accuracy vs. your transcript
    python compare_ocr.py sheet.jpg --engines easyocr trocr   # pick engines
    python compare_ocr.py sheet.jpg --truth truth.txt --engines easyocr vlm   # vlm = Ollama/Gemini (see vlm.py)
    set OCR_TARGET_WIDTH=1024   (PowerShell: $env:OCR_TARGET_WIDTH=1024)  # try without upscaling

Then pick the winner with:  $env:OCR_ENGINE="trocr"  before starting uvicorn.
"""
import argparse, re, sys, time
from collections import Counter
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from app.ml.ocr.engine import OCREngine  # noqa: E402

tok = lambda s: re.findall(r"[a-z0-9]+", s.lower())

def score(truth_words, text):
    h = tok(text); g = truth_words
    d = list(range(len(h) + 1))
    for i in range(1, len(g) + 1):
        p = d[:]; d[0] = i
        for j in range(1, len(h) + 1):
            d[j] = min(p[j] + 1, d[j - 1] + 1, p[j - 1] + (g[i - 1] != h[j - 1]))
    c = Counter(h)
    recall = sum(min(v, c[w]) for w, v in Counter(g).items()) / max(len(g), 1)
    return d[len(h)] / max(len(g), 1), recall

ap = argparse.ArgumentParser()
ap.add_argument("image"); ap.add_argument("--truth")
ap.add_argument("--engines", nargs="+", default=["easyocr", "tesseract", "trocr"])
ap.add_argument("--show", type=int, default=0, help="lines to print per engine (0 = all)")
a = ap.parse_args()

truth = tok(Path(a.truth).read_text(encoding="utf-8")) if a.truth else None
img = Image.open(a.image)
eng = OCREngine()
for name in a.engines:
    t = time.time()
    try:
        r = eng._ocr_image(img.copy(), source_name="", engine=name)   # source_name="" skips demo shortcuts
    except Exception as e:
        print(f"\n=== {name}: FAILED: {e}"); continue
    dt = time.time() - t
    line = f"\n=== {name}: used={r['document_type']}  time={dt:.1f}s  lines={len(r['lines'])}  conf={r['confidence_avg']}"
    if truth:
        wer, rec = score(truth, r["raw_text"]); line += f"  WER={wer:.2f}  word_recall={rec:.2f}"
    print(line)
    print("\n".join(r["raw_text"].splitlines()[: a.show or None]))
    if name == "vlm" and r["document_type"] != "HANDWRITTEN_VLM":
        print("   (!) VLM was NOT used - it fell back. See the [OCREngine] messages above.")
    if name == "trocr" and r["document_type"] != "HANDWRITTEN_TROCR":
        print("   (!) TrOCR was NOT used - it fell back. See the [OCREngine] messages above.")
