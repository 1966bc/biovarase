#!/usr/bin/env python3
"""
Abbott QC Data Importer v2 (Simplified) for Biovarase.

Prerequisites (already configured):
- tests, test_methods, workstations, workstation_test_methods

This script only creates:
- batches (with target/SD from file)
- results

Usage:
    python3 abbott_import_v2.py [--dry-run] [--verbose] [--limit N]

Author: Giuseppe Costanzi
License: GNU GPL v3
"""

import os
import sys
import argparse
import mariadb
from datetime import datetime
from typing import Optional, Dict, Tuple
from pathlib import Path


# Configuration
ABBOTT_PATH = "/mnt/biovarase_qc/EXPQC/Biovarase"
SECTION_ID = 6
LAB_ID = 2
CONTROL_ID = 71
VALID_WORKSTATIONS = ("ALCI-1", "ALCI-2", "ALCI-3")

# Database credentials
DB_CONFIG = {
    "user": "biovarase",
    "password": "pS2dY^hX1nB5mL",
    "database": "biovarase",
    "host": "localhost",
    "port": 3306,
}


class AbbottImporter:
    """Simplified Abbott QC data importer."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.con = None
        self.cur = None

        # Caches
        self.workstation_cache: Dict[str, int] = {}  # device_id -> workstation_id
        self.test_method_cache: Dict[Tuple[str, int], int] = {}  # (external_code, ws_id) -> test_method_id
        self.batch_cache: Dict[Tuple[int, int, str], int] = {}  # (tm_id, ws_id, lot_level) -> batch_id

        # Stats
        self.stats = {
            'files_processed': 0,
            'records_read': 0,
            'batches_created': 0,
            'results_created': 0,
            'skipped_no_test_method': 0,
            'skipped_duplicate': 0,
            'skipped_invalid_ws': 0,
            'errors': 0,
        }

    def connect(self):
        """Connect to database."""
        self.con = mariadb.connect(**DB_CONFIG, autocommit=False)
        self.cur = self.con.cursor(dictionary=True)
        self._load_caches()

    def _load_caches(self):
        """Load workstations and test_method mappings into cache."""
        # Load workstations for section
        self.cur.execute(
            'SELECT workstation_id, device_id FROM workstations WHERE section_id = ?',
            (SECTION_ID,)
        )
        for row in self.cur.fetchall():
            self.workstation_cache[row['device_id']] = row['workstation_id']

        if self.verbose:
            print(f"Loaded {len(self.workstation_cache)} workstations")

        # Load workstation_test_methods mappings
        self.cur.execute('''
            SELECT wtm.external_code, wtm.workstation_id, wtm.test_method_id
            FROM workstation_test_methods wtm
            JOIN workstations w ON wtm.workstation_id = w.workstation_id
            WHERE w.section_id = ?
        ''', (SECTION_ID,))
        for row in self.cur.fetchall():
            if row['external_code']:
                key = (row['external_code'], row['workstation_id'])
                self.test_method_cache[key] = row['test_method_id']

        if self.verbose:
            print(f"Loaded {len(self.test_method_cache)} test_method mappings")

    def close(self):
        """Close database connection."""
        if self.cur:
            self.cur.close()
        if self.con:
            self.con.close()

    def parse_line(self, line: str) -> Optional[Dict]:
        """Parse a single line from Abbott export file."""
        fields = line.strip().split('|')
        if len(fields) < 20:
            return None

        try:
            workstation = fields[16]
            if workstation not in VALID_WORKSTATIONS:
                return None

            # Parse datetime: YYYYMMDDHHMMSSmmm
            dt_str = fields[14]
            if len(dt_str) >= 14:
                received = datetime.strptime(dt_str[:14], '%Y%m%d%H%M%S')
            else:
                return None

            # Parse expiration: YYYYMMDD
            exp_str = fields[9]
            expiration = None
            if exp_str and len(exp_str) == 8:
                try:
                    expiration = datetime.strptime(exp_str, '%Y%m%d').date()
                except ValueError:
                    pass

            return {
                'testcode': fields[12].strip(),
                'workstation': workstation,
                'lot': fields[8].strip(),
                'level': fields[10].strip(),
                'result': float(fields[15]),
                'target': float(fields[18]) if fields[18] else 0.0,
                'sd': float(fields[19]) if fields[19] else 0.0,
                'received': received,
                'expiration': expiration,
                'reagent_lot': fields[17] if len(fields) > 17 else None,
            }
        except (ValueError, IndexError) as e:
            if self.verbose:
                print(f"  Parse error: {e}")
            return None

    def get_test_method_id(self, testcode: str, workstation_id: int) -> Optional[int]:
        """Get test_method_id from external_code and workstation."""
        key = (testcode, workstation_id)
        return self.test_method_cache.get(key)

    def get_or_create_batch(self, test_method_id: int, workstation_id: int,
                           lot: str, level: str, target: float, sd: float,
                           expiration) -> int:
        """Get existing batch or create new one."""
        lot_level = f"{lot}-L{level}"
        cache_key = (test_method_id, workstation_id, lot_level)

        if cache_key in self.batch_cache:
            return self.batch_cache[cache_key]

        # Check if batch exists in DB
        self.cur.execute('''
            SELECT batch_id FROM batches
            WHERE test_method_id = ? AND workstation_id = ? AND lot_number = ?
        ''', (test_method_id, workstation_id, lot_level))
        row = self.cur.fetchone()

        if row:
            self.batch_cache[cache_key] = row['batch_id']
            return row['batch_id']

        # Create new batch
        if not self.dry_run:
            self.cur.execute('''
                INSERT INTO batches
                (lab_id, control_id, test_method_id, workstation_id, lot_number,
                 expiration, target, sd, description, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (LAB_ID, CONTROL_ID, test_method_id, workstation_id, lot_level,
                  expiration, target, sd, f"L{level}"))
            batch_id = self.cur.lastrowid
        else:
            batch_id = -1  # Dummy for dry run

        self.batch_cache[cache_key] = batch_id
        self.stats['batches_created'] += 1

        if self.verbose:
            print(f"  Created batch: {lot_level} (tm={test_method_id}, ws={workstation_id})")

        return batch_id

    def result_exists(self, batch_id: int, workstation_id: int, received: datetime) -> bool:
        """Check if result already exists (duplicate detection)."""
        self.cur.execute('''
            SELECT 1 FROM results
            WHERE batch_id = ? AND workstation_id = ? AND received = ?
            LIMIT 1
        ''', (batch_id, workstation_id, received))
        row = self.cur.fetchone()
        # Consume any remaining results to avoid sync issues
        while self.cur.fetchone():
            pass
        return row is not None

    def create_result(self, batch_id: int, workstation_id: int,
                     result: float, received: datetime, reagent_lot: str) -> bool:
        """Create a new result record."""
        if self.dry_run:
            self.stats['results_created'] += 1
            return True

        try:
            self.cur.execute('''
                INSERT INTO results
                (batch_id, run_number, workstation_id, reagent_lot, result,
                 received, status, validated, is_delete)
                VALUES (?, ?, ?, ?, ?, ?, 1, 0, 0)
            ''', (batch_id, '', workstation_id, reagent_lot, result, received))
            self.stats['results_created'] += 1
            return True
        except mariadb.Error as e:
            if self.verbose:
                print(f"  Error creating result: {e}")
            self.stats['errors'] += 1
            return False

    def process_file(self, filepath: str) -> int:
        """Process a single Abbott export file. Returns number of results created."""
        results_created = 0

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if not line.strip():
                        continue

                    self.stats['records_read'] += 1
                    data = self.parse_line(line)

                    if not data:
                        continue

                    # Get workstation_id
                    workstation_id = self.workstation_cache.get(data['workstation'])
                    if not workstation_id:
                        self.stats['skipped_invalid_ws'] += 1
                        continue

                    # Get test_method_id
                    test_method_id = self.get_test_method_id(data['testcode'], workstation_id)
                    if not test_method_id:
                        self.stats['skipped_no_test_method'] += 1
                        if self.verbose:
                            print(f"  No test_method for: {data['testcode']} on {data['workstation']}")
                        continue

                    # Get or create batch
                    batch_id = self.get_or_create_batch(
                        test_method_id, workstation_id,
                        data['lot'], data['level'],
                        data['target'], data['sd'],
                        data['expiration']
                    )

                    # Check duplicate
                    if not self.dry_run and self.result_exists(batch_id, workstation_id, data['received']):
                        self.stats['skipped_duplicate'] += 1
                        continue

                    # Create result
                    if self.create_result(batch_id, workstation_id, data['result'],
                                         data['received'], data['reagent_lot']):
                        results_created += 1

            self.stats['files_processed'] += 1

        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            self.stats['errors'] += 1

        return results_created

    def run(self, limit: Optional[int] = None):
        """Run the import process."""
        print(f"Abbott Importer v2 {'(DRY RUN)' if self.dry_run else ''}")
        print(f"Path: {ABBOTT_PATH}")
        print("-" * 60)

        if not os.path.exists(ABBOTT_PATH):
            print(f"ERROR: Path not found: {ABBOTT_PATH}")
            return

        # Get list of files
        files = sorted([
            f for f in os.listdir(ABBOTT_PATH)
            if f.endswith('.txt')
        ])

        if limit:
            files = files[:limit]

        print(f"Files to process: {len(files)}")
        print()

        for i, filename in enumerate(files):
            filepath = os.path.join(ABBOTT_PATH, filename)

            if self.verbose:
                print(f"[{i+1}/{len(files)}] {filename}")

            self.process_file(filepath)

            # Commit every 100 files
            if not self.dry_run and (i + 1) % 100 == 0:
                self.con.commit()
                if self.verbose:
                    print(f"  Committed at file {i+1}")

        # Final commit
        if not self.dry_run:
            self.con.commit()

        # Print stats
        print()
        print("=" * 60)
        print("RESULTS")
        print("=" * 60)
        print(f"Files processed:        {self.stats['files_processed']}")
        print(f"Records read:           {self.stats['records_read']}")
        print(f"Batches created:        {self.stats['batches_created']}")
        print(f"Results created:        {self.stats['results_created']}")
        print(f"Skipped (no test_method): {self.stats['skipped_no_test_method']}")
        print(f"Skipped (duplicate):    {self.stats['skipped_duplicate']}")
        print(f"Skipped (invalid ws):   {self.stats['skipped_invalid_ws']}")
        print(f"Errors:                 {self.stats['errors']}")


def main():
    parser = argparse.ArgumentParser(description='Abbott QC Data Importer v2')
    parser.add_argument('--dry-run', '-d', action='store_true',
                       help='Run without making database changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--limit', '-l', type=int,
                       help='Limit number of files to process')

    args = parser.parse_args()

    importer = AbbottImporter(dry_run=args.dry_run, verbose=args.verbose)

    try:
        importer.connect()
        importer.run(limit=args.limit)
    finally:
        importer.close()


if __name__ == '__main__':
    main()
