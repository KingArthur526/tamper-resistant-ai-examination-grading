import tempfile
from pathlib import Path
from app.core.integrity import calculate_sha256_bytes, calculate_sha256_file, calculate_event_hash, GENESIS_HASH

def test_sha256_hashing_consistency():
    data = b"Student Examination Submission Binary Bytes"
    h1 = calculate_sha256_bytes(data)
    h2 = calculate_sha256_bytes(data)
    assert h1 == h2
    assert len(h1) == 64

def test_file_tamper_detection():
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"Original Untampered Answer Sheet Image")
        tmp_path = Path(tmp.name)

    try:
        original_hash = calculate_sha256_file(tmp_path)
        # Modify 1 byte
        with open(tmp_path, "ab") as f:
            f.write(b"!")
        modified_hash = calculate_sha256_file(tmp_path)
        assert original_hash != modified_hash
    finally:
        if tmp_path.exists():
            tmp_path.unlink()

def test_audit_hash_chain_calculation():
    h1 = calculate_event_hash(
        previous_hash=GENESIS_HASH,
        timestamp="2026-05-15T10:00:00Z",
        action="EXAM_SESSION_CREATED",
        entity_type="ExamSession",
        entity_id="exam-1",
        payload={"name": "Mid-Term"}
    )
    assert h1 != GENESIS_HASH
    assert len(h1) == 64

    # Chained event
    h2 = calculate_event_hash(
        previous_hash=h1,
        timestamp="2026-05-15T10:05:00Z",
        action="ANSWER_SHEET_UPLOADED",
        entity_type="AnswerSheet",
        entity_id="sheet-1",
        payload={"student_id": "STU-001"}
    )
    assert h2 != h1
