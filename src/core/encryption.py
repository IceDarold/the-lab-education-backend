from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

class TokenEncryption:
    """Handles encryption/decryption of sensitive tokens"""

    _fernet = None

    @classmethod
    def _get_fernet(cls):
        """Get or create Fernet instance for encryption"""
        if cls._fernet is None:
            # Use SECRET_KEY from settings to derive encryption key
            salt = b'the_lab_token_salt'  # Fixed salt for consistency
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
            cls._fernet = Fernet(key)
            logger.debug("Token encryption initialized")
        return cls._fernet

    @classmethod
    def encrypt_token(cls, token: str) -> str:
        """Encrypt a token for storage"""
        try:
            fernet = cls._get_fernet()
            encrypted = fernet.encrypt(token.encode())
            return encrypted.decode()
        except Exception as e:
            logger.error(f"Token encryption failed: {str(e)}")
            raise ValueError("Failed to encrypt token")

    @classmethod
    def decrypt_token(cls, encrypted_token: str) -> str:
        """Decrypt a token from storage"""
        try:
            fernet = cls._get_fernet()
            decrypted = fernet.decrypt(encrypted_token.encode())
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Token decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt token")