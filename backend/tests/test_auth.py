import pytest
from app.core.security import get_password_hash, verify_password, create_access_token, decode_token

def test_password_hashing_and_verification():
    raw_pass = "SecureExamPass2026!"
    hashed = get_password_hash(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False

def test_jwt_token_generation_and_decoding():
    user_id = "test-teacher-uuid-123"
    token = create_access_token(user_id, role="teacher")
    assert isinstance(token, str)
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == "teacher"
