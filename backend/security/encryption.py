"""
Data Encryption Service

Provides secure encryption for sensitive data:
- Password hashing with Argon2/bcrypt
- Symmetric encryption with Fernet
- Field-level encryption
- Key rotation support
"""

import base64
import hashlib
import logging
import secrets
from typing import Any

from cryptography.fernet import Fernet, MultiFernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from passlib.context import CryptContext

logger = logging.getLogger(__name__)


class PasswordPolicy:
    """Password policy configuration"""

    def __init__(
        self,
        min_length: int = 12,
        require_uppercase: bool = True,
        require_lowercase: bool = True,
        require_digits: bool = True,
        require_special: bool = True,
        max_length: int = 128
    ):
        self.min_length = min_length
        self.max_length = max_length
        self.require_uppercase = require_uppercase
        self.require_lowercase = require_lowercase
        self.require_digits = require_digits
        self.require_special = require_special
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    def validate(self, password: str) -> tuple[bool, list[str]]:
        """
        Validate password against policy.

        Returns:
            Tuple of (is_valid, list of violations)
        """
        violations = []

        if len(password) < self.min_length:
            violations.append(f"Password must be at least {self.min_length} characters")

        if len(password) > self.max_length:
            violations.append(f"Password must be at most {self.max_length} characters")

        if self.require_uppercase and not any(c.isupper() for c in password):
            violations.append("Password must contain at least one uppercase letter")

        if self.require_lowercase and not any(c.islower() for c in password):
            violations.append("Password must contain at least one lowercase letter")

        if self.require_digits and not any(c.isdigit() for c in password):
            violations.append("Password must contain at least one digit")

        if self.require_special and not any(c in self.special_chars for c in password):
            violations.append("Password must contain at least one special character")

        return len(violations) == 0, violations


class PasswordHasher:
    """
    Secure password hashing using industry-standard algorithms.

    Uses Argon2 as primary with bcrypt fallback.
    """

    def __init__(self, policy: PasswordPolicy | None = None):
        self.policy = policy or PasswordPolicy()
        self.context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__memory_cost=65536,  # 64MB
            argon2__time_cost=3,
            argon2__parallelism=4
        )

    def hash(self, password: str, validate: bool = True) -> str:
        """
        Hash a password securely.

        Args:
            password: Plain text password
            validate: Whether to validate against policy

        Returns:
            Hashed password string
        """
        if validate:
            is_valid, violations = self.policy.validate(password)
            if not is_valid:
                raise ValueError(f"Password policy violations: {', '.join(violations)}")

        return self.context.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            password: Plain text password
            hashed: Hashed password

        Returns:
            True if password matches
        """
        try:
            return self.context.verify(password, hashed)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False

    def needs_rehash(self, hashed: str) -> bool:
        """Check if password hash needs to be upgraded"""
        return self.context.needs_update(hashed)


class EncryptionService:
    """
    Symmetric encryption service using Fernet.

    Features:
    - AES-128-CBC encryption
    - HMAC authentication
    - Key rotation support
    - Field-level encryption
    """

    def __init__(
        self,
        encryption_key: str | None = None,
        previous_keys: list[str] | None = None
    ):
        """
        Initialize encryption service.

        Args:
            encryption_key: Primary encryption key (Fernet compatible)
            previous_keys: Previous keys for key rotation
        """
        if encryption_key:
            self.primary_key = encryption_key
        else:
            # Generate a new key (in production, use from secure storage)
            self.primary_key = Fernet.generate_key().decode()

        self.previous_keys = previous_keys or []
        self._setup_fernet()

    def _setup_fernet(self):
        """Setup Fernet instances for encryption"""
        keys = [self.primary_key] + self.previous_keys

        fernet_instances = []
        for key in keys:
            try:
                if isinstance(key, str):
                    key = key.encode()
                fernet_instances.append(Fernet(key))
            except Exception as e:
                logger.error(f"Invalid encryption key: {e}")

        if fernet_instances:
            self.fernet = MultiFernet(fernet_instances)
        else:
            # Fallback to new key
            new_key = Fernet.generate_key()
            self.fernet = Fernet(new_key)
            self.primary_key = new_key.decode()

    def encrypt(self, data: str | bytes) -> str:
        """
        Encrypt data.

        Args:
            data: Data to encrypt (string or bytes)

        Returns:
            Base64 encoded encrypted string
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        encrypted = self.fernet.encrypt(data)
        return base64.urlsafe_b64encode(encrypted).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: Base64 encoded encrypted string

        Returns:
            Decrypted string
        """
        try:
            data = base64.urlsafe_b64decode(encrypted_data.encode("utf-8"))
            decrypted = self.fernet.decrypt(data)
            return decrypted.decode("utf-8")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt data")

    def encrypt_dict(
        self,
        data: dict[str, Any],
        fields_to_encrypt: list[str]
    ) -> dict[str, Any]:
        """
        Encrypt specific fields in a dictionary.

        Args:
            data: Dictionary with data
            fields_to_encrypt: List of field names to encrypt

        Returns:
            Dictionary with encrypted fields
        """
        result = data.copy()

        for field in fields_to_encrypt:
            if field in result and result[field] is not None:
                value = str(result[field])
                result[field] = self.encrypt(value)
                result[f"_encrypted_{field}"] = True

        return result

    def decrypt_dict(
        self,
        data: dict[str, Any],
        fields_to_decrypt: list[str]
    ) -> dict[str, Any]:
        """
        Decrypt specific fields in a dictionary.

        Args:
            data: Dictionary with encrypted data
            fields_to_decrypt: List of field names to decrypt

        Returns:
            Dictionary with decrypted fields
        """
        result = data.copy()

        for field in fields_to_decrypt:
            if field in result and result.get(f"_encrypted_{field}"):
                result[field] = self.decrypt(result[field])
                del result[f"_encrypted_{field}"]

        return result

    def rotate_key(self, new_key: str | None = None) -> str:
        """
        Rotate encryption key.

        Args:
            new_key: New encryption key (generated if not provided)

        Returns:
            New encryption key
        """
        if not new_key:
            new_key = Fernet.generate_key().decode()

        # Move current key to previous keys
        self.previous_keys.insert(0, self.primary_key)
        self.primary_key = new_key

        # Keep only last 3 keys for rotation
        self.previous_keys = self.previous_keys[:3]

        self._setup_fernet()

        logger.info("Encryption key rotated successfully")
        return new_key

    @staticmethod
    def generate_key() -> str:
        """Generate a new Fernet-compatible encryption key"""
        return Fernet.generate_key().decode()

    @staticmethod
    def derive_key_from_password(
        password: str,
        salt: bytes | None = None
    ) -> tuple[str, bytes]:
        """
        Derive an encryption key from a password.

        Args:
            password: Password to derive key from
            salt: Optional salt (generated if not provided)

        Returns:
            Tuple of (derived_key, salt)
        """
        if salt is None:
            salt = secrets.token_bytes(16)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key.decode(), salt


class TokenGenerator:
    """Secure token generation utilities"""

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Generate a URL-safe random token"""
        return secrets.token_urlsafe(length)

    @staticmethod
    def generate_hex_token(length: int = 32) -> str:
        """Generate a hex random token"""
        return secrets.token_hex(length)

    @staticmethod
    def generate_numeric_code(length: int = 6) -> str:
        """Generate a numeric code (for OTP/verification)"""
        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    @staticmethod
    def generate_api_key(prefix: str = "ieap_") -> str:
        """Generate an API key with prefix"""
        return f"{prefix}{secrets.token_urlsafe(32)}"


class HashingService:
    """General-purpose hashing utilities"""

    @staticmethod
    def hash_sha256(data: str | bytes) -> str:
        """Generate SHA-256 hash"""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_sha512(data: str | bytes) -> str:
        """Generate SHA-512 hash"""
        if isinstance(data, str):
            data = data.encode("utf-8")
        return hashlib.sha512(data).hexdigest()

    @staticmethod
    def hash_with_salt(
        data: str,
        salt: str | None = None
    ) -> tuple[str, str]:
        """
        Hash data with salt.

        Returns:
            Tuple of (hash, salt)
        """
        if salt is None:
            salt = secrets.token_hex(16)

        combined = f"{salt}{data}"
        hashed = hashlib.sha256(combined.encode()).hexdigest()

        return hashed, salt

    @staticmethod
    def verify_hash_with_salt(data: str, expected_hash: str, salt: str) -> bool:
        """Verify data against a salted hash"""
        computed_hash, _ = HashingService.hash_with_salt(data, salt)
        return secrets.compare_digest(computed_hash, expected_hash)


# Global instances
_password_hasher: PasswordHasher | None = None
_encryption_service: EncryptionService | None = None


def get_password_hasher() -> PasswordHasher:
    """Get global password hasher instance"""
    global _password_hasher
    if _password_hasher is None:
        _password_hasher = PasswordHasher()
    return _password_hasher


def get_encryption_service() -> EncryptionService:
    """Get global encryption service instance"""
    global _encryption_service
    if _encryption_service is None:
        try:
            from config import get_settings
            settings = get_settings()
            key = settings.security.encryption_key.get_secret_value()
            _encryption_service = EncryptionService(encryption_key=key if key else None)
        except Exception:
            _encryption_service = EncryptionService()
    return _encryption_service


# Convenience functions
def hash_password(password: str) -> str:
    """Hash a password"""
    return get_password_hasher().hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return get_password_hasher().verify(password, hashed)


def encrypt_data(data: str) -> str:
    """Encrypt data"""
    return get_encryption_service().encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data"""
    return get_encryption_service().decrypt(encrypted_data)
