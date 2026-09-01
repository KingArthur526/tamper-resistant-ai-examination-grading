import pytest
from pathlib import Path
from app.ml.segmentation.parser import segmenter
from app.ml.ocr.engine import ocr_engine

def test_question_segmentation_multiformat():
    ocr_sample = """
    NAME: Alice | ID: STU-101
    Question 1:
    The OSI Reference Model is a 7 layer architecture with physical and data link layers.

    Question 2:
    TCP uses a 3-way handshake with SYN, SYN-ACK, and ACK segments.

    Question 3A:
    Distance vector uses Bellman-Ford algorithm to compute routing vectors.
    """
    res = segmenter.segment_answers(ocr_sample, ["1", "2", "3A", "3B"])
    assert "1" in res
    assert "2" in res
    assert "3a" in res
    assert "7 layer" in res["1"]["text"]
    assert "3-way handshake" in res["2"]["text"]
    assert "Bellman-Ford" in res["3a"]["text"]

def test_question_segmentation_ocr_artifacts():
    ocr_sample = """
    1. The OSI model contains physical layer, data link layer, network layer, and transport layer.
    2. TCP connection is established through SYN, SYN-ACK, and ACK handshake sequence.
    """
    res = segmenter.segment_answers(ocr_sample, ["1", "2"])
    assert "1" in res and "OSI model" in res["1"]["text"]
    assert "2" in res and "SYN" in res["2"]["text"]

def test_ocr_engine_text_file_extraction(tmp_path):
    f = tmp_path / "answer.txt"
    f.write_text("Question 1:\nRelational databases enforce ACID properties.\n\nQuestion 2:\nB-tree indexing provides logarithmic lookup.", encoding="utf-8")
    res = ocr_engine.extract_text(f)
    assert res["document_type"] == "DIGITAL_TEXT"
    assert res["confidence_avg"] == 1.0
    assert "ACID" in res["raw_text"]

def test_segmentation_fallback_distribution():
    text = "Physical layer transmits raw signals.\n\nTCP ensures reliable transmission with sequence numbers."
    res = segmenter.segment_answers(text, ["1", "2"])
    assert "1" in res and len(res["1"]["text"]) > 0
    assert "2" in res and len(res["2"]["text"]) > 0

