"""
Test suite for Security functionality (password hashing and encryption).

Tests critical security components:
- Bcrypt password hashing and verification
- Hardware ID generation
- PBKDF2 key derivation
- Configuration file encryption/decryption (hardware-locked)

References:
    - bcrypt: Password hashing with adaptive cost (resist brute force)
    - Fernet: Symmetric encryption (AES-128-CBC + HMAC-SHA256)
    - PBKDF2: Key derivation function (100,000 iterations)
"""
import pytest
import os
import tempfile
import bcrypt
from typing import Dict
from security import (
    get_hardware_id,
    derive_key_from_hardware,
    encrypt_config,
    decrypt_config,
)


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.unit
class TestPasswordHashing:
    """Test bcrypt password hashing and verification."""

    def test_hash_password(self):
        """Test password hash generation."""
        password = b"test_password_123"

        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        assert hashed is not None, "Hash should not be None"
        assert isinstance(hashed, bytes), "Hash should be bytes"
        assert len(hashed) == 60, "Bcrypt hash should be 60 bytes"
        assert hashed.startswith(b"$2b$"), "Bcrypt hash should start with $2b$"

    def test_verify_correct_password(self):
        """Test password verification with correct password."""
        password = b"correct_password"
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        result = bcrypt.checkpw(password, hashed)

        assert result is True, "Correct password should verify"

    def test_verify_incorrect_password(self):
        """Test password verification with incorrect password."""
        password = b"correct_password"
        wrong_password = b"wrong_password"
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        result = bcrypt.checkpw(wrong_password, hashed)

        assert result is False, "Incorrect password should not verify"

    def test_hash_uniqueness(self):
        """Test that same password produces different hashes (due to salt)."""
        password = b"same_password"

        hash1 = bcrypt.hashpw(password, bcrypt.gensalt())
        hash2 = bcrypt.hashpw(password, bcrypt.gensalt())

        assert hash1 != hash2, "Same password should produce different hashes (different salts)"
        # But both should verify
        assert bcrypt.checkpw(password, hash1), "Hash1 should verify"
        assert bcrypt.checkpw(password, hash2), "Hash2 should verify"

    def test_hash_empty_password(self):
        """Test hashing empty password."""
        password = b""

        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        assert hashed is not None, "Empty password should still hash"
        assert bcrypt.checkpw(password, hashed), "Empty password should verify"

    def test_verify_case_sensitivity(self):
        """Test password verification is case-sensitive."""
        password = b"Password123"
        wrong_case = b"password123"
        hashed = bcrypt.hashpw(password, bcrypt.gensalt())

        assert bcrypt.checkpw(password, hashed), "Correct case should verify"
        assert not bcrypt.checkpw(wrong_case, hashed), "Wrong case should not verify"


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.unit
class TestHardwareID:
    """Test hardware ID generation for hardware-locked encryption."""

    def test_hardware_id_consistency(self):
        """Test hardware ID is consistent across calls."""
        hw_id1 = get_hardware_id()
        hw_id2 = get_hardware_id()

        assert hw_id1 == hw_id2, "Hardware ID should be consistent across calls"

    def test_hardware_id_format(self):
        """Test hardware ID format (SHA-256 hex)."""
        hw_id = get_hardware_id()

        assert isinstance(hw_id, str), "Hardware ID should be string"
        assert len(hw_id) == 64, "Hardware ID should be 64 chars (SHA-256 hex)"
        # Check all characters are hex
        assert all(c in '0123456789abcdef' for c in hw_id), "Hardware ID should be hex string"

    def test_hardware_id_not_empty(self):
        """Test hardware ID is never empty."""
        hw_id = get_hardware_id()

        assert hw_id, "Hardware ID should not be empty"
        assert hw_id != "0" * 64, "Hardware ID should not be all zeros"


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.unit
class TestKeyDerivation:
    """Test PBKDF2 key derivation from hardware ID."""

    def test_derive_key_consistency(self):
        """Test same hardware ID produces same key (deterministic)."""
        hw_id = "test_hardware_id_12345"

        key1 = derive_key_from_hardware(hw_id)
        key2 = derive_key_from_hardware(hw_id)

        assert key1 == key2, "Same hardware ID should produce same key"

    def test_derive_key_length(self):
        """Test derived key is 32 bytes (256 bits)."""
        hw_id = "test_hardware_id_12345"

        key = derive_key_from_hardware(hw_id)

        assert len(key) == 32, "Derived key should be 32 bytes (256 bits)"

    def test_derive_key_different_inputs(self):
        """Test different hardware IDs produce different keys."""
        hw_id1 = "hardware_id_1"
        hw_id2 = "hardware_id_2"

        key1 = derive_key_from_hardware(hw_id1)
        key2 = derive_key_from_hardware(hw_id2)

        assert key1 != key2, "Different hardware IDs should produce different keys"

    def test_derive_key_type(self):
        """Test derived key is bytes."""
        hw_id = "test_hardware_id_12345"

        key = derive_key_from_hardware(hw_id)

        assert isinstance(key, bytes), "Derived key should be bytes"


@pytest.mark.critical
@pytest.mark.security
@pytest.mark.integration
class TestConfigEncryption:
    """Test configuration file encryption and decryption."""

    @pytest.fixture
    def temp_config_path(self, tmp_path):
        """Provide temporary config file path."""
        return str(tmp_path / "test_config.enc")

    @pytest.fixture
    def test_credentials(self) -> Dict[str, str]:
        """Provide test database credentials."""
        return {
            'user': 'test_user',
            'password': 'test_password_123',
            'database': 'test_database',
            'host': 'localhost'
        }

    def test_encrypt_config_creates_file(self, test_credentials, temp_config_path):
        """Test encrypt_config creates encrypted file."""
        success = encrypt_config(test_credentials, temp_config_path)

        assert success is True, "Encryption should succeed"
        assert os.path.exists(temp_config_path), "Encrypted file should exist"

        # File should have content
        file_size = os.path.getsize(temp_config_path)
        assert file_size > 0, "Encrypted file should not be empty"

    def test_decrypt_config_retrieves_credentials(self, test_credentials, temp_config_path):
        """Test decrypt_config retrieves original credentials."""
        # Encrypt first
        encrypt_config(test_credentials, temp_config_path)

        # Decrypt
        decrypted = decrypt_config(temp_config_path)

        assert decrypted is not None, "Decryption should succeed"
        assert decrypted['user'] == test_credentials['user'], "User should match"
        assert decrypted['password'] == test_credentials['password'], "Password should match"
        assert decrypted['database'] == test_credentials['database'], "Database should match"
        assert decrypted['host'] == test_credentials['host'], "Host should match"

    def test_encrypt_decrypt_round_trip(self, test_credentials, temp_config_path):
        """Test full round-trip: encrypt then decrypt."""
        # Encrypt
        success = encrypt_config(test_credentials, temp_config_path)
        assert success is True, "Encryption should succeed"

        # Decrypt
        decrypted = decrypt_config(temp_config_path)

        assert decrypted == test_credentials, "Decrypted credentials should match original"

    def test_decrypt_nonexistent_file(self, temp_config_path):
        """Test decrypt_config with non-existent file returns None."""
        result = decrypt_config(temp_config_path)

        assert result is None, "Decrypting non-existent file should return None"

    def test_decrypt_corrupted_file(self, temp_config_path):
        """Test decrypt_config with corrupted file returns None."""
        # Create corrupted file
        with open(temp_config_path, 'wb') as f:
            f.write(b"corrupted_data_not_valid_fernet_token")

        result = decrypt_config(temp_config_path)

        assert result is None, "Decrypting corrupted file should return None"

    def test_decrypt_empty_file(self, temp_config_path):
        """Test decrypt_config with empty file returns None."""
        # Create empty file
        with open(temp_config_path, 'wb') as f:
            f.write(b"")

        result = decrypt_config(temp_config_path)

        assert result is None, "Decrypting empty file should return None"

    def test_encrypt_preserves_all_fields(self, temp_config_path):
        """Test all credential fields are preserved."""
        credentials = {
            'user': 'admin',
            'password': 'very_secure_password_!@#',
            'database': 'biovarase_production',
            'host': '192.168.1.100'
        }

        encrypt_config(credentials, temp_config_path)
        decrypted = decrypt_config(temp_config_path)

        assert decrypted == credentials, "All fields should be preserved"

    def test_encrypt_special_characters(self, temp_config_path):
        """Test encryption handles special characters."""
        credentials = {
            'user': 'user@domain.com',
            'password': 'p@$$w0rd!#%&*()[]{}',
            'database': 'database-name_123',
            'host': 'host.example.com:3306'
        }

        encrypt_config(credentials, temp_config_path)
        decrypted = decrypt_config(temp_config_path)

        assert decrypted == credentials, "Special characters should be preserved"


@pytest.mark.security
@pytest.mark.unit
@pytest.mark.parametrize("password,expected_verify", [
    # Test various password scenarios
    (b"simple", True),
    (b"password123", True),
    (b"P@ssw0rd!#$%", True),
    (b"", True),  # Empty password should work
    (b"very_long_password_with_many_characters_" * 10, True),
])
def test_password_verification_parametrized(password, expected_verify):
    """Parametrized test for password verification."""
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    result = bcrypt.checkpw(password, hashed)
    assert result == expected_verify, \
        f"Password verification for {password!r} should be {expected_verify}"


@pytest.mark.security
@pytest.mark.unit
def test_bcrypt_cost_factor():
    """Test bcrypt uses appropriate cost factor (default 12 for security)."""
    password = b"test_password"
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())

    # Extract cost factor from hash (format: $2b$12$...)
    cost_str = hashed.decode('utf-8').split('$')[2]
    cost = int(cost_str)

    assert cost >= 12, f"Bcrypt cost factor should be >= 12 for security, got {cost}"
