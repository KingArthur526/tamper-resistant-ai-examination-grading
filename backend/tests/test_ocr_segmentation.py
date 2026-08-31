import pytest
from app.ml.segmentation.parser import segmenter

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
