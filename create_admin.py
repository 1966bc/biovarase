#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create App Admin user for Biovarase.

This script creates a global administrator user with:
    - role = 0 (App Admin)
    - org_id = NULL (global scope)
    - lab_id = NULL (no lab restriction)
    - password = 'pass' (default, change after first login!)

Usage:
    python3 create_admin.py
"""

import sys
import bcrypt

# Add project root to path
sys.path.insert(0, '.')

from security import decrypt_config


def create_admin():
    """Create the admin user."""
    # Get database credentials
    try:
        config = decrypt_config()
        if not config:
            print("ERROR: Cannot decrypt config.enc")
            print("Run setup_wizard.py first to configure database credentials.")
            return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

    # Connect to database
    import mariadb
    try:
        conn = mariadb.connect(
            user=config['user'],
            password=config['password'],
            host=config.get('host', 'localhost'),
            port=int(config.get('port', 3306)),
            database=config['database'],
            autocommit=True
        )
        cursor = conn.cursor(dictionary=True)
    except mariadb.Error as e:
        print(f"ERROR connecting to database: {e}")
        return False

    # Check if admin user exists
    cursor.execute("SELECT user_id, nickname, role, org_id FROM users WHERE nickname = 'admin'")
    existing = cursor.fetchone()

    if existing:
        print(f"Admin user already exists (user_id={existing['user_id']}, role={existing['role']})")
        response = input("Do you want to reset it? (y/n): ").strip().lower()
        if response != 'y':
            print("Aborted.")
            conn.close()
            return False

        # Update existing admin
        hashed_password = bcrypt.hashpw(b'pass', bcrypt.gensalt())
        cursor.execute("""
            UPDATE users
            SET role = 0,
                org_id = NULL,
                lab_id = NULL,
                pswrd = ?,
                status = 1
            WHERE nickname = 'admin'
        """, (hashed_password,))
        print("Admin user reset successfully!")
    else:
        # Create new admin user
        hashed_password = bcrypt.hashpw(b'pass', bcrypt.gensalt())
        cursor.execute("""
            INSERT INTO users (
                last_name, first_name, nickname, pswrd,
                role, org_id, lab_id, elapsing_time, enable_time, status
            ) VALUES (
                'Administrator', 'System', 'admin', ?,
                0, NULL, NULL, 30, 1, 1
            )
        """, (hashed_password,))
        print("Admin user created successfully!")

    # Verify
    cursor.execute("""
        SELECT user_id, last_name, first_name, nickname, role, org_id, lab_id, status
        FROM users WHERE nickname = 'admin'
    """)
    admin = cursor.fetchone()

    print("\n--- Admin User Details ---")
    print(f"  user_id:    {admin['user_id']}")
    print(f"  name:       {admin['first_name']} {admin['last_name']}")
    print(f"  nickname:   {admin['nickname']}")
    print(f"  role:       {admin['role']} (App Admin)")
    print(f"  org_id:     {admin['org_id']} (Global)")
    print(f"  lab_id:     {admin['lab_id']}")
    print(f"  status:     {admin['status']} (Active)")
    print("\n--- Credentials ---")
    print(f"  Username: admin")
    print(f"  Password: pass")
    print("\n  IMPORTANT: Change password after first login!")

    conn.close()
    return True


if __name__ == "__main__":
    print("=" * 50)
    print("  Biovarase - Create App Admin User")
    print("=" * 50)
    print()

    success = create_admin()

    print()
    if success:
        print("Done!")
    else:
        print("Failed!")
        sys.exit(1)
