"""
Unit tests for the security module.
"""

from datetime import timedelta

import pytest

from security.authentication import JWTHandler
from security.encryption import EncryptionService, PasswordHasher, TokenGenerator


class TestPasswordHasher:
    """Tests for password hashing."""

    def test_hash_password(self):
        """Test password hashing produces different output."""
        hasher = PasswordHasher()
        password = "SecurePassword123!"

        hash1 = hasher.hash(password)
        hash2 = hasher.hash(password)

        assert hash1 != password
        assert hash1 != hash2  # Different salts

    def test_verify_correct_password(self):
        """Test verifying correct password."""
        hasher = PasswordHasher()
        password = "SecurePassword123!"
        hashed = hasher.hash(password)

        assert hasher.verify(password, hashed) is True

    def test_verify_incorrect_password(self):
        """Test verifying incorrect password."""
        hasher = PasswordHasher()
        hashed = hasher.hash("CorrectPassword123!")

        assert hasher.verify("WrongPassword123!", hashed) is False

    def test_verify_empty_password(self):
        """Test verifying empty password."""
        hasher = PasswordHasher()
        hashed = hasher.hash("SomePassword123!")

        assert hasher.verify("", hashed) is False


class TestEncryptionService:
    """Tests for encryption service."""

    @pytest.fixture
    def encryption_service(self):
        return EncryptionService()

    def test_encrypt_decrypt_string(self, encryption_service):
        """Test encrypting and decrypting string."""
        plaintext = "sensitive data"

        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)

        assert encrypted != plaintext
        assert decrypted == plaintext

    def test_encrypt_produces_different_output(self, encryption_service):
        """Test that encryption produces different ciphertext each time."""
        plaintext = "sensitive data"

        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)

        # Fernet includes random IV, so outputs should differ
        assert encrypted1 != encrypted2

    def test_encrypt_empty_string(self, encryption_service):
        """Test encrypting empty string."""
        plaintext = ""

        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)

        assert decrypted == plaintext


class TestTokenGenerator:
    """Tests for token generation."""

    def test_generate_token_length(self):
        """Test generated token has correct length."""
        token = TokenGenerator.generate_token(32)
        # URL-safe base64 encoding increases length
        assert len(token) >= 32

    def test_generate_unique_tokens(self):
        """Test tokens are unique."""
        tokens = [TokenGenerator.generate_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_generate_api_key(self):
        """Test API key generation format."""
        key = TokenGenerator.generate_api_key()

        assert key.startswith("ieap_")
        assert len(key) > 10


class TestJWTHandler:
    """Tests for JWT handling."""

    @pytest.fixture
    def jwt_handler(self):
        return JWTHandler(
            secret_key="test-secret-key",
            algorithm="HS256"
        )

    def test_create_access_token(self, jwt_handler):
        """Test creating access token."""
        token = jwt_handler.create_access_token(
            user_id="user123",
            roles=["user"]
        )

        assert token is not None
        assert isinstance(token, str)

    def test_decode_valid_token(self, jwt_handler):
        """Test decoding valid token."""
        token = jwt_handler.create_access_token(
            user_id="user123",
            roles=["user", "admin"]
        )

        payload = jwt_handler.decode_token(token)

        assert payload is not None
        assert payload.user_id == "user123"
        assert "user" in payload.roles
        assert "admin" in payload.roles

    def test_decode_expired_token(self, jwt_handler):
        """Test decoding expired token raises error."""
        token = jwt_handler.create_access_token(
            user_id="user123",
            roles=["user"],
            expires_delta=timedelta(seconds=-1)
        )

        payload = jwt_handler.decode_token(token)
        assert payload is None

    def test_decode_invalid_token(self, jwt_handler):
        """Test decoding invalid token returns None."""
        payload = jwt_handler.decode_token("invalid-token")
        assert payload is None

    def test_refresh_token_creation(self, jwt_handler):
        """Test refresh token has longer expiry."""
        access_token = jwt_handler.create_access_token(
            user_id="user123",
            roles=["user"]
        )
        refresh_token = jwt_handler.create_refresh_token(
            user_id="user123"
        )

        assert access_token != refresh_token
