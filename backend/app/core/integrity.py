import hashlib
import json
from pathlib import Path
from typing import Union, Dict, Any, Optional

def calculate_sha256_bytes(data: bytes) -> str:
    sha256 = hashlib.sha256()
    sha256.update(data)
    return sha256.hexdigest()

def calculate_sha256_file(file_path: Union[str, Path]) -> str:
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found for hash calculation: {file_path}")
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()

def calculate_sha256_text(text: str) -> str:
    return calculate_sha256_bytes(text.encode("utf-8"))

def calculate_event_hash(
    previous_hash: str,
    timestamp: str,
    action: str,
    entity_type: str,
    entity_id: Optional[str],
    payload: Dict[str, Any]
) -> str:
    canonical_payload = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"))
    raw_str = f"{previous_hash}|{timestamp}|{action}|{entity_type}|{entity_id or ''}|{canonical_payload}"
    return calculate_sha256_text(raw_str)

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
