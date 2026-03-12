import hashlib

def checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
