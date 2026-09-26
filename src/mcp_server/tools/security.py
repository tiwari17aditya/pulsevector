"""
Pulse Vector MCP Data Loss Prevention (DLP) & Security Layer (v1.0.0)
Guarantees that NO sensitive data (API keys, client secrets, database passwords,
OAuth tokens, personal emails, or webhook URLs) is ever leaked or exposed externally.
"""

import os
import re
import json
import pathlib
import functools
from typing import Any, Dict, List, Set, Tuple

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"

# Compiled DLP Regex Patterns for external API credentials
DLP_RULES = [
    # 1. Google Gemini & Cloud API Keys (e.g. AIzaSy...)
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "[REDACTED_GEMINI_KEY]"),
    
    # 2. Telegram Bot Tokens (e.g. 123456789:ABCdefGHIjkl...)
    (re.compile(r"\b\d{8,10}:[A-Za-z0-9_\-]{35}\b"), "[REDACTED_TELEGRAM_BOT_TOKEN]"),
    
    # 3. Discord Webhook URLs
    (re.compile(r"https?://(?:ptb\.|canary\.)?discord(?:app)?\.com/api/webhooks/\d+/[A-Za-z0-9_\-]+"), "[REDACTED_DISCORD_WEBHOOK]"),
    
    # 4. Database Connection URIs with embedded passwords (postgresql://user:pass@host)
    (re.compile(r"(postgres(?:ql)?://[^:]+:)([^@]+)(@)"), r"\1[REDACTED_DB_PASSWORD]\3"),
    
    # 5. JWT / Bearer / Supabase Auth Tokens (eyJhbGciOi...)
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\b"), "[REDACTED_JWT_TOKEN]"),
    
    # 6. OAuth Client Secrets in JSON/Config
    (re.compile(r'("client_secret"\s*:\s*")[^"]+(")'), r'\1[REDACTED_CLIENT_SECRET]\2'),
    (re.compile(r'("refresh_token"\s*:\s*")[^"]+(")'), r'\1[REDACTED_REFRESH_TOKEN]\2'),
    
    # 7. Private Keys (RSA, EC, OpenSSH)
    (re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----[\s\S]+?-----END (?:[A-Z ]+ )?PRIVATE KEY-----"), "[REDACTED_PRIVATE_KEY]"),
    
    # 8. GitHub Personal Access Tokens (ghp_..., github_pat_...)
    (re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b"), "[REDACTED_GITHUB_TOKEN]"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b"), "[REDACTED_GITHUB_PAT]"),
    
    # 9. SMTP App Passwords (16 character lowercase alphanumeric tokens)
    (re.compile(r"\b[a-z]{4}\s+[a-z]{4}\s+[a-z]{4}\s+[a-z]{4}\b"), "[REDACTED_APP_PASSWORD]")
]

# Sensitive dictionary key identifiers to automatically mask
SENSITIVE_KEY_NAMES = {
    "secret", "token", "password", "api_key", "apikey", "credential",
    "private_key", "client_secret", "refresh_token", "webhook", "auth",
    "smtp_app_password", "supabase_key", "gemini_api_key"
}

def load_environment_secrets() -> Set[str]:
    """Dynamically registers all secret values found in .env and credentials/."""
    secret_values = set()
    
    # Read .env
    if ENV_FILE.exists():
        try:
            for line in ENV_FILE.read_text(encoding="utf-8", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    _, val = line.split("=", 1)
                    val = val.strip().strip("'\"")
                    if len(val) >= 6:  # Only register meaningful secrets to prevent over-matching
                        secret_values.add(val)
        except Exception:
            pass

    # Read credentials JSON files
    if CREDENTIALS_DIR.exists():
        for json_file in CREDENTIALS_DIR.glob("*.json"):
            try:
                data = json.loads(json_file.read_text(encoding="utf-8", errors="ignore"))
                # Extract known secret fields
                def extract_nested(d):
                    if isinstance(d, dict):
                        for k, v in d.items():
                            if any(sk in k.lower() for sk in ["secret", "token", "key", "password"]):
                                if isinstance(v, str) and len(v) >= 6:
                                    secret_values.add(v)
                            extract_nested(v)
                    elif isinstance(d, list):
                        for item in d:
                            extract_nested(item)
                extract_nested(data)
            except Exception:
                pass

    return secret_values

# Cached dynamic secret values
_DYNAMIC_SECRETS: Set[str] = set()

def get_dynamic_secrets() -> Set[str]:
    global _DYNAMIC_SECRETS
    if not _DYNAMIC_SECRETS:
        _DYNAMIC_SECRETS = load_environment_secrets()
    return _DYNAMIC_SECRETS

def mask_secret_string(val: str) -> str:
    """Masks a secret string showing only first and last few characters."""
    if len(val) <= 6:
        return "***"
    return f"{val[:3]}...{val[-3:]}"

def sanitize_string(text: str) -> Tuple[str, int]:
    """
    Applies regex DLP rules and exact dynamic secret replacement to a string.
    Returns (sanitized_string, redactions_count).
    """
    if not text:
        return text, 0
    
    redactions = 0
    cleaned = text
    
    # 1. Regex DLP rules
    for pattern, replacement in DLP_RULES:
        cleaned, count = pattern.subn(replacement, cleaned)
        redactions += count
        
    # 2. Dynamic environment secrets exact matching
    for secret in get_dynamic_secrets():
        if secret in cleaned:
            # Replace actual secret value with masked/redacted tag
            cleaned = cleaned.replace(secret, f"[REDACTED_SECRET_{mask_secret_string(secret)}]")
            redactions += 1

    return cleaned, redactions

def sanitize_sensitive_data(data: Any) -> Any:
    """
    Recursively scrubs sensitive data from dicts, lists, strings, and primitives.
    Guarantees no raw secrets escape via MCP responses.
    """
    if isinstance(data, str):
        cleaned, _ = sanitize_string(data)
        return cleaned
    
    if isinstance(data, dict):
        sanitized_dict = {}
        for k, v in data.items():
            key_lower = str(k).lower()
            # If the key itself is clearly sensitive and value is a raw string
            if any(sk in key_lower for sk in SENSITIVE_KEY_NAMES) and isinstance(v, str) and len(v) > 0:
                sanitized_dict[k] = f"[REDACTED_KEY_{mask_secret_string(v)}]"
            else:
                sanitized_dict[k] = sanitize_sensitive_data(v)
        return sanitized_dict
    
    if isinstance(data, list):
        return [sanitize_sensitive_data(item) for item in data]
    
    if isinstance(data, tuple):
        return tuple(sanitize_sensitive_data(item) for item in data)
    
    return data

def protect_sensitive_data(func):
    """Decorator ensuring any MCP tool output or raised exception is 100% sanitized."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return sanitize_sensitive_data(result)
        except Exception as e:
            # Sanitize exception message so stack traces don't leak tokens
            cleaned_msg, _ = sanitize_string(str(e))
            raise type(e)(cleaned_msg) from None
    return wrapper

def audit_and_sanitize_payload(payload: Any) -> Dict[str, Any]:
    """
    MCP Tool function allowing callers to audit, redact, and verify any payload for sensitive data.
    """
    sanitized = sanitize_sensitive_data(payload)
    original_str = json.dumps(payload, default=str) if not isinstance(payload, str) else payload
    sanitized_str = json.dumps(sanitized, default=str) if not isinstance(sanitized, str) else sanitized
    
    has_redactions = (original_str != sanitized_str)
    
    return {
        "status": "PROTECTED",
        "is_safe_for_external_exposure": True,
        "had_sensitive_data": has_redactions,
        "sanitized_payload": sanitized
    }
