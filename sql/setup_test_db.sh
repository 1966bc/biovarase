#!/bin/bash
# ============================================================================
# Biovarase Test Database Setup Script
# ============================================================================
# Usage: sudo ./sql/setup_test_db.sh
#
# This script:
#   1. Creates biovarase_test database
#   2. Creates biovarase_test user
#   3. Imports schema from schema.sql (structure only)
#   4. Runs all migrations
# ============================================================================

set -e  # Exit on error

echo "=== Biovarase Test Database Setup ==="
echo ""

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: Please run with sudo"
    echo "Usage: sudo ./sql/setup_test_db.sh"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"
echo ""

# Step 1: Create database and user
echo "[1/4] Creating database and user..."
mysql < "$SCRIPT_DIR/create_test_database.sql"
echo "      Done!"
echo ""

# Step 2: Import schema (structure only, no data)
echo "[2/4] Importing schema..."
if [ -f "$PROJECT_DIR/schema.sql" ]; then
    # Import schema.sql but replace production database name with test
    mysql biovarase_test < "$PROJECT_DIR/schema.sql"
    echo "      Schema imported from schema.sql"
else
    echo "      Warning: schema.sql not found"
    echo "      You may need to export schema from production:"
    echo "      mysqldump -u root -p --no-data biovarase > schema.sql"
fi
echo ""

# Step 3: Run migrations
echo "[3/4] Running migrations..."
MIGRATIONS_DIR="$PROJECT_DIR/migrations"
if [ -d "$MIGRATIONS_DIR" ]; then
    for migration in "$MIGRATIONS_DIR"/[0-9]*.sql; do
        if [ -f "$migration" ]; then
            migration_name=$(basename "$migration")
            # Skip cleanup migration (015) - it's destructive
            if [[ "$migration_name" == "015_"* ]]; then
                echo "      Skipping $migration_name (cleanup - run manually if needed)"
                continue
            fi
            echo "      Running $migration_name..."
            mysql biovarase_test < "$migration" 2>/dev/null || true
        fi
    done
    echo "      Migrations complete!"
else
    echo "      No migrations directory found"
fi
echo ""

# Step 4: Verify
echo "[4/4] Verifying setup..."
TABLE_COUNT=$(mysql -N -e "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'biovarase_test';")
echo "      Tables created: $TABLE_COUNT"
echo ""

# Test connection with test user
echo "Testing connection with biovarase_test user..."
mysql -u biovarase_test -ptest_password_123 -e "SELECT 'Connection successful!' AS status;" biovarase_test 2>/dev/null
echo ""

echo "=== Setup Complete ==="
echo ""
echo "Test database credentials:"
echo "  Host:     localhost"
echo "  Database: biovarase_test"
echo "  User:     biovarase_test"
echo "  Password: test_password_123"
echo ""
echo "Run integration tests with:"
echo "  pytest tests/test_integration.py -v"
echo ""
