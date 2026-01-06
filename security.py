# -*- coding: utf-8 -*-
"""
Security Module for Biovarase - Hardware-Locked Configuration Encryption.

This module provides hardware-locked encryption for database credentials,
ensuring that configuration files cannot be transferred between machines.

Features:
- Hardware ID generation (MAC + platform + machine-id)
- AES-128 encryption with Fernet (HMAC-SHA256 authentication)
- PBKDF2 key derivation (100,000 iterations)
- Hardware-locked: config.enc only works on the machine that created it

Usage:
    # First-time setup (creates config.enc)
    credentials = {
        'user': 'biovarase',
        'password': 'mypassword',
        'database': 'biovarase',
        'host': 'localhost'
    }
    success = encrypt_config(credentials, 'config.enc')
    
    # Normal startup (automatic decryption)
    credentials = decrypt_config('config.enc')
    if credentials:
        # Connect to database
        pass

Dependencies:
    - cryptography (pip install cryptography)
    
Python Version:
    - Compatible with Python 3.7+
    
Security Properties:
    - Hardware-locked (non-transferable)
    - AES-128 encryption
    - HMAC-SHA256 authentication
    - 100,000 PBKDF2 iterations
    
Author: 1966bc (Giuseppe Costanzi)
Date: 2025-11-30 (Modified for Python 3.7: 2025-12-03)
"""

import hashlib
import uuid
import platform
import os
from typing import Dict, Optional

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    from cryptography.hazmat.backends import default_backend
except ImportError:
    print("[ERROR] 'cryptography' library not found!")
    print("Install with: pip install cryptography")
    raise

# Constants
PBKDF2_ITERATIONS = 100000
PBKDF2_SALT = b'biovarase_v4_2025_hardware_lock'


def get_hardware_id() -> str:
    """
    Generate unique hardware ID for this machine.
    
    Combines multiple hardware identifiers to create a stable,
    machine-specific ID that persists across reboots but changes
    if hardware changes significantly.
    
    Components:
    - MAC address (primary network interface)
    - Platform system (Windows, Linux, etc.)
    - Node name (hostname)
    - Machine type (x86_64, etc.)
    - Machine ID (Windows: MachineGuid, Linux: machine-id)
    
    Returns:
        SHA-256 hash (64 hex characters) of combined hardware identifiers
        
    Note:
        On Windows, tries to read MachineGuid from registry.
        On Linux, reads /etc/machine-id or /var/lib/dbus/machine-id.
        Falls back to uuid.getnode() if machine ID unavailable.
    """
    components = []
    
    # 1. MAC address (most stable identifier)
    mac = uuid.getnode()
    components.append(str(mac))
    
    # 2. Platform info
    components.append(platform.system())
    components.append(platform.node())
    components.append(platform.machine())
    
    # 3. Machine ID (OS-specific)
    machine_id = _get_machine_id()
    if machine_id:
        components.append(machine_id)
    
    # Combine all components
    combined = '|'.join(components)
    
    # SHA-256 hash for fixed-length output
    hardware_hash = hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    return hardware_hash


def _get_machine_id() -> Optional[str]:
    """
    Get OS-specific machine ID.
    
    Returns:
        Machine ID string, or None if unavailable
    """
    if platform.system() == 'Windows':
        return _get_windows_machine_id()
    elif platform.system() == 'Linux':
        return _get_linux_machine_id()
    else:
        return None


def _get_windows_machine_id() -> Optional[str]:
    """
    Get Windows MachineGuid from registry.
    
    Location: HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid
    
    Returns:
        MachineGuid string, or None if unavailable
    """
    try:
        import winreg
        key_path = r'SOFTWARE\Microsoft\Cryptography'
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        machine_guid, _ = winreg.QueryValueEx(key, 'MachineGuid')
        winreg.CloseKey(key)
        return machine_guid
    except Exception:
        return None


def _get_linux_machine_id() -> Optional[str]:
    """
    Get Linux machine-id from /etc/machine-id or /var/lib/dbus/machine-id.
    
    Returns:
        Machine ID string, or None if unavailable
    """
    for path in ['/etc/machine-id', '/var/lib/dbus/machine-id']:
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return f.read().strip()
        except Exception:
            pass
    return None


def derive_key_from_hardware(hardware_id: str) -> bytes:
    """
    Derive encryption key from hardware ID using PBKDF2.
    
    Uses PBKDF2-HMAC-SHA256 with 100,000 iterations to derive a 32-byte
    key from the hardware ID. The same hardware ID always produces the
    same key (deterministic).
    
    Args:
        hardware_id: Hardware ID string (from get_hardware_id())
        
    Returns:
        32-byte encryption key
        
    Security:
        - 100,000 iterations (protection against brute force)
        - Fixed salt (same for all installations - enables deterministic key)
        - SHA256 hash function
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=PBKDF2_SALT,
        iterations=PBKDF2_ITERATIONS,
        backend=default_backend()
    )
    key = kdf.derive(hardware_id.encode('utf-8'))
    return key


def encrypt_config(credentials: Dict[str, str], config_path: str = 'config.enc') -> bool:
    """
    Encrypt database credentials and save to file.
    
    Creates a hardware-locked encrypted configuration file that can only
    be decrypted on the same machine.
    
    Args:
        credentials: Dictionary containing:
            - 'user': Database username
            - 'password': Database password
            - 'database': Database name
            - 'host': Database host
        config_path: Path to save encrypted config (default: 'config.enc')
        
    Returns:
        True if encryption successful, False otherwise
        
    Example:
        >>> creds = {
        ...     'user': 'biovarase',
        ...     'password': 'mypassword',
        ...     'database': 'biovarase',
        ...     'host': 'localhost'
        ... }
        >>> success = encrypt_config(creds, 'config.enc')
        >>> print(f"Encryption {'succeeded' if success else 'failed'}")
    """
    try:
        # Get hardware ID
        hardware_id = get_hardware_id()
        
        # Derive encryption key
        key = derive_key_from_hardware(hardware_id)
        
        # Create Fernet cipher
        fernet = Fernet(Fernet.generate_key())  # Generate key
        # Actually, we need to use derived key, not random
        # Convert derived key to base64 URL-safe format for Fernet
        import base64
        key_b64 = base64.urlsafe_b64encode(key)
        fernet = Fernet(key_b64)
        
        # Format credentials as text
        config_text = '\n'.join([
            f"user={credentials.get('user', '')}",
            f"password={credentials.get('password', '')}",
            f"database={credentials.get('database', '')}",
            f"host={credentials.get('host', '')}"
        ])
        
        # Encrypt
        encrypted_data = fernet.encrypt(config_text.encode('utf-8'))
        
        # Save to file
        with open(config_path, 'wb') as f:
            f.write(encrypted_data)
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Failed to encrypt config: {e}")
        return False


def decrypt_config(config_path: str = 'config.enc') -> Optional[Dict[str, str]]:
    """
    Decrypt configuration file and return credentials.
    
    Automatically decrypts the hardware-locked configuration file.
    Only works on the machine that created the file.
    
    Args:
        config_path: Path to encrypted config file (default: 'config.enc')
        
    Returns:
        Dictionary containing credentials if successful:
            - 'user': Database username
            - 'password': Database password
            - 'database': Database name
            - 'host': Database host
        None if decryption failed (wrong machine or corrupted file)
        
    Example:
        >>> credentials = decrypt_config('config.enc')
        >>> if credentials:
        ...     print(f"User: {credentials['user']}")
        ... else:
        ...     print("Decryption failed - wrong machine or corrupted file")
    """
    try:
        # Check if file exists
        if not os.path.exists(config_path):
            return None
        
        # Get hardware ID
        hardware_id = get_hardware_id()
        
        # Derive decryption key
        key = derive_key_from_hardware(hardware_id)
        
        # Convert key to base64 URL-safe format for Fernet
        import base64
        key_b64 = base64.urlsafe_b64encode(key)
        fernet = Fernet(key_b64)
        
        # Read encrypted file
        with open(config_path, 'rb') as f:
            encrypted_data = f.read()
        
        # Decrypt
        decrypted_data = fernet.decrypt(encrypted_data)
        config_text = decrypted_data.decode('utf-8')
        
        # Parse credentials
        credentials = {}
        for line in config_text.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                credentials[key.strip()] = value.strip()
        
        return credentials
        
    except Exception as e:
        print(f"[ERROR] Failed to decrypt config: {e}")
        print("[INFO] This may indicate wrong machine or corrupted file")
        return None


def test_encryption():
    """
    Test encryption and decryption functionality.
    
    Creates a test config, encrypts it, then decrypts to verify.
    Prints results to console.
    """
    print("\n" + "="*60)
    print("Security Module - Encryption Test")
    print("="*60)
    
    # Get hardware ID
    hardware_id = get_hardware_id()
    print(f"\n1. Hardware ID: {hardware_id[:32]}...")
    
    # Test credentials
    test_creds = {
        'user': 'test_user',
        'password': 'test_password_123',
        'database': 'test_db',
        'host': 'localhost'
    }
    print(f"\n2. Test Credentials:")
    print(f"   User: {test_creds['user']}")
    print(f"   Password: {test_creds['password']}")
    print(f"   Database: {test_creds['database']}")
    print(f"   Host: {test_creds['host']}")
    
    # Encrypt
    print(f"\n3. Encrypting...")
    success = encrypt_config(test_creds, 'test_config.enc')
    print(f"   Encryption: {'SUCCESS' if success else 'FAILED'}")
    
    if not success:
        return
    
    # Check file exists
    if os.path.exists('test_config.enc'):
        file_size = os.path.getsize('test_config.enc')
        print(f"   File created: test_config.enc ({file_size} bytes)")
    
    # Decrypt
    print(f"\n4. Decrypting...")
    decrypted_creds = decrypt_config('test_config.enc')
    
    if decrypted_creds:
        print(f"   Decryption: SUCCESS")
        print(f"\n5. Decrypted Credentials:")
        print(f"   User: {decrypted_creds.get('user')}")
        print(f"   Password: {decrypted_creds.get('password')}")
        print(f"   Database: {decrypted_creds.get('database')}")
        print(f"   Host: {decrypted_creds.get('host')}")
        
        # Verify match
        match = (test_creds == decrypted_creds)
        print(f"\n6. Verification: {'PASS' if match else 'FAIL'}")
        
        if match:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Test failed - credentials don't match")
    else:
        print(f"   Decryption: FAILED")
        print("\n❌ Test failed - could not decrypt")
    
    # Cleanup
    try:
        if os.path.exists('test_config.enc'):
            os.remove('test_config.enc')
            print("\n7. Cleanup: test_config.enc removed")
    except OSError:
        pass

    print("="*60 + "\n")


if __name__ == '__main__':
    # Run self-test
    test_encryption()
