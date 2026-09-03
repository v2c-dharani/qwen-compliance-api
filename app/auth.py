import os
import secrets
import logging
from fastapi import Security, HTTPException, status, Request
from fastapi.security.api_key import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("qwen_api.auth")

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def verify_api_key(request: Request, api_key_header_val: str = Security(api_key_header)) -> str:
    """
    Validates the API key passed in X-API-Key or Authorization header against QWEN_API_KEY / API_KEY.
    Uses secrets.compare_digest for constant-time comparison to prevent timing attacks.
    """
    expected_api_key = os.getenv("QWEN_API_KEY") or os.getenv("API_KEY") or "qwen_secret_key_12345"
    
    # Extract candidate key from X-API-Key header or Authorization Bearer header
    candidate_key = api_key_header_val

    if not candidate_key:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            candidate_key = auth_header.split(" ", 1)[1].strip()

    if not candidate_key or not secrets.compare_digest(candidate_key, expected_api_key):
        logger.warning("Unauthorized API access attempt: Invalid or missing API Key.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key. Provide a valid 'X-API-Key' or 'Authorization: Bearer <key>' header."
        )

    return candidate_key
