import hashlib
import hmac
import os
import time
from typing import Optional, Dict, Any
from app.config import settings

SECRET_KEY = settings.LIVEKIT_API_SECRET or "voicehire_jwt_secret_key_production_32_bytes"

def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-256 and a random salt.
    """
    salt = os.urandom(16).hex()
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return f"{salt}:{key.hex()}"

def verify_password(plain_password: str, stored_hash: str) -> bool:
    """
    Verify a password against stored PBKDF2 hash.
    """
    try:
        parts = stored_hash.split(':')
        if len(parts) != 2:
            return False
        salt, key_hex = parts
        computed_key = hashlib.pbkdf2_hmac(
            'sha256',
            plain_password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return hmac.compare_digest(computed_key.hex(), key_hex)
    except Exception:
        return False

def create_access_token(user_id: str, email: str, expires_in_seconds: int = 86400 * 7) -> str:
    """
    Create a lightweight signed JWT-compatible token.
    """
    import base64
    import json
    
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": user_id,
        "email": email,
        "exp": int(time.time()) + expires_in_seconds,
        "iat": int(time.time())
    }
    
    def b64encode(data_dict: dict) -> str:
        data_bytes = json.dumps(data_dict, separators=(',', ':')).encode('utf-8')
        return base64.urlsafe_b64encode(data_bytes).decode('utf-8').rstrip('=')
    
    header_b64 = b64encode(header)
    payload_b64 = b64encode(payload)
    message = f"{header_b64}.{payload_b64}"
    
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode('utf-8').rstrip('=')
    
    return f"{message}.{sig_b64}"

def verify_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify signature and expiry of a JWT token.
    """
    import base64
    import json
    
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        message = f"{header_b64}.{payload_b64}"
        
        expected_sig = hmac.new(
            SECRET_KEY.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode('utf-8').rstrip('=')
        
        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None
        
        # Add padding back to decode base64
        padded_payload = payload_b64 + '=' * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode('utf-8')).decode('utf-8'))
        
        if payload.get("exp", 0) < time.time():
            return None
            
        return payload
    except Exception:
        return None
