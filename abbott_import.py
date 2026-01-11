#!/usr/bin/env python3
"""
Abbott QC Data Importer for Biovarase.

This script imports QC results from Abbott Alinity instruments exported to
/mnt/biovarase_qc/EXPQC/Biovarase/

It auto-creates:
- tests (with Abbott code as description)
- test_methods (linked to section 6)
- workstation_test_methods (external_code mapping)
- batches (with target/SD from file)
- results

Usage:
    python3 abbott_import.py [--dry-run] [--verbose] [--limit N]

Author: Giuseppe Costanzi
License: GNU GPL v3
"""

import os
import sys
import argparse
import mariadb
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Any
from pathlib import Path


# Configuration
ABBOTT_PATH = "/mnt/biovarase_qc/EXPQC/Biovarase"
SECTION_ID = 6  # Sezione Alinity
LAB_ID = 2  # Laboratory ID for Abbott batches/results
VALID_WORKSTATIONS = ("ALCI-1", "ALCI-2", "ALCI-3")
MAPPING_FILE = "CFGTESTQNRANGE.xlsx"  # Excel with test code -> description mapping

# Manual mappings for codes not in Excel
MANUAL_MAPPINGS = {
    'LIPLD': 'Lipasi',
    'LITIO': 'Litio',
    'LipoA': 'Lipoproteina (a)',
    'ETAN': 'Etanolo',
    'HSPCR': 'PCR alta sensibilità',
    'FENO': 'Fenobarbital',
    'APTO': 'Aptoglobina',
    'CK-MB': 'CK-MB massa',
    'HSTROPI': 'Troponina I alta sensibilità',
    'BNP': 'BNP (Peptide natriuretico)',
    'PROT': 'Proteine totali',
    'VITD': 'Vitamina D',
    'B12': 'Vitamina B12',
    'FOL': 'Folati',
    'OMOCIS': 'Omocisteina',
    'CPEP': 'C-Peptide',
    'ATG': 'Anticorpi anti-Tireoglobulina',
    'ATPO': 'Anticorpi anti-TPO',
    'AFP': 'Alfa-fetoproteina',
    'CEA': 'Antigene carcinoembrionario',
    'CA125': 'CA 125',
    'CA153': 'CA 15-3',
    'CA199': 'CA 19-9',
    'PSA': 'PSA totale',
    'PSAF': 'PSA libero',
    'PROG': 'Progesterone',
    'ESTR': 'Estradiolo',
    'TESTO': 'Testosterone',
    'LH': 'Ormone luteinizzante',
    'FSH': 'Ormone follicolo-stimolante',
    'PROL': 'Prolattina',
    'INS': 'Insulina',
    'PTH': 'Paratormone',
    'PROCAL': 'Procalcitonina',
    'TACRO': 'Tacrolimus',
    'CICLO': 'Ciclosporina',
    'SIROL': 'Sirolimus',
    'VANCO': 'Vancomicina',
    'VALP': 'Acido valproico',
    'CARB': 'Carbamazepina',
    'FENI': 'Fenitoina',
    'TEO': 'Teofillina',
    'RF': 'Fattore reumatoide',
    'C3': 'Complemento C3',
    'C4': 'Complemento C4',
    'APOA': 'Apolipoproteina A1',
    'APOB': 'Apolipoproteina B',
    'MYOG': 'Mioglobina',
    'DHEAS': 'DHEA-S',
    'SHBG': 'SHBG',
    'CYFRA': 'Cyfra 21-1',
    'NSE': 'NSE',
    'HE4': 'HE4',
    'TIREO': 'Tireoglobulina',
    'TRAB': 'Anticorpi anti-recettore TSH',
}

# Database credentials
DB_CONFIG = {
    "user": "biovarase",
    "password": "pS2dY^hX1nB5mL",
    "database": "biovarase",
    "host": "localhost",
    "port": 3306,
}


class AbbottImporter:
    """Imports Abbott QC data into Biovarase database."""

    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.con = None
        self.test_name_mapping = self._load_test_mapping()
        self.stats = {
            "files_processed": 0,
            "files_skipped": 0,
            "results_inserted": 0,
            "results_skipped": 0,
            "tests_created": 0,
            "test_methods_created": 0,
            "mappings_created": 0,
            "batches_created": 0,
            "errors": 0,
        }
        # Cache for lookups
        self._workstation_cache: Dict[str, int] = {}
        self._mapping_cache: Dict[Tuple[int, str], int] = {}
        self._batch_cache: Dict[Tuple[str, int, int, int], int] = {}

    def _load_test_mapping(self) -> Dict[str, str]:
        """Load test code -> description mapping from Excel and manual mappings."""
        mapping = dict(MANUAL_MAPPINGS)  # Start with manual mappings

        # Try to load from Excel
        script_dir = Path(__file__).parent
        excel_path = script_dir / MAPPING_FILE

        if excel_path.exists():
            try:
                import openpyxl
                wb = openpyxl.load_workbook(excel_path)
                ws = wb.active
                for row in ws.iter_rows(min_row=2):
                    code = str(row[0].value).strip() if row[0].value else None
                    desc = row[1].value
                    if code and desc and code not in mapping:
                        mapping[code] = desc
                self.log(f"Loaded {len(mapping)} test mappings from {MAPPING_FILE}")
            except Exception as e:
                self.log(f"Warning: Could not load Excel mapping: {e}")

        return mapping

    def get_test_description(self, code: str) -> str:
        """Get test description from code, or return code if not found."""
        return self.test_name_mapping.get(code, code)

    def connect(self) -> bool:
        """Connect to database."""
        try:
            self.con = mariadb.connect(**DB_CONFIG, autocommit=False)
            return True
        except mariadb.Error as e:
            print(f"[ERROR] Database connection failed: {e}")
            return False

    def disconnect(self):
        """Close database connection."""
        if self.con:
            self.con.close()

    def log(self, msg: str):
        """Print message if verbose mode enabled."""
        if self.verbose:
            print(f"  {msg}")

    def fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict]:
        """Execute query and return single row."""
        try:
            cur = self.con.cursor(dictionary=True)
            cur.execute(sql, params)
            result = cur.fetchone()
            cur.close()
            return result
        except mariadb.Error as e:
            print(f"[ERROR] SQL failed: {e}\n  Query: {sql}\n  Params: {params}")
            self.stats["errors"] += 1
            return None

    def fetch_all(self, sql: str, params: tuple = ()) -> List[Dict]:
        """Execute query and return all rows."""
        try:
            cur = self.con.cursor(dictionary=True)
            cur.execute(sql, params)
            result = cur.fetchall()
            cur.close()
            return result
        except mariadb.Error as e:
            print(f"[ERROR] SQL failed: {e}\n  Query: {sql}\n  Params: {params}")
            self.stats["errors"] += 1
            return []

    def insert(self, sql: str, params: tuple = ()) -> Optional[int]:
        """Execute INSERT and return lastrowid."""
        if self.dry_run:
            self.log(f"[DRY-RUN] Would execute: {sql[:80]}...")
            return -1
        try:
            cur = self.con.cursor()
            cur.execute(sql, params)
            lastrowid = cur.lastrowid
            cur.close()
            return lastrowid
        except mariadb.Error as e:
            print(f"[ERROR] SQL failed: {e}\n  Query: {sql}\n  Params: {params}")
            self.stats["errors"] += 1
            return None

    # -------------------------------------------------------------------------
    # Lookup / Create methods
    # -------------------------------------------------------------------------

    def get_workstation_id(self, device_id: str) -> Optional[int]:
        """Get workstation_id from device_id (cached)."""
        if device_id in self._workstation_cache:
            return self._workstation_cache[device_id]

        row = self.fetch_one(
            "SELECT workstation_id FROM workstations WHERE device_id = ?",
            (device_id,)
        )
        if row:
            self._workstation_cache[device_id] = row["workstation_id"]
            return row["workstation_id"]
        return None

    def get_test_method_id(self, workstation_id: int, external_code: str) -> Optional[int]:
        """Get test_method_id from workstation mapping (cached)."""
        cache_key = (workstation_id, external_code)
        if cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]

        row = self.fetch_one(
            """SELECT test_method_id FROM workstation_test_methods
               WHERE workstation_id = ? AND external_code = ?""",
            (workstation_id, external_code)
        )
        if row:
            self._mapping_cache[cache_key] = row["test_method_id"]
            return row["test_method_id"]
        return None

    def create_test_and_method(self, external_code: str, workstation_id: int) -> Optional[int]:
        """Create test, test_method, and mapping. Returns test_method_id."""
        # Get description from mapping (or use code if not found)
        description = self.get_test_description(external_code)

        # 1. Create test
        test_id = self.insert(
            "INSERT INTO tests (description, status) VALUES (?, 1)",
            (description,)
        )
        if not test_id:
            # If description already exists, try with suffix
            try:
                test_id = self.insert(
                    "INSERT INTO tests (description, status) VALUES (?, 1)",
                    (f"{description} (Alinity)",)
                )
            except:
                return None
        if not test_id:
            return None
        self.stats["tests_created"] += 1
        self.log(f"Created test: {external_code} -> {description} (id={test_id})")

        # 2. Create test_method
        test_method_id = self.insert(
            """INSERT INTO test_methods (test_id, org_id, category_id, sample_id, code, status)
               VALUES (?, ?, 29, 1, ?, 1)""",
            (test_id, SECTION_ID, external_code)
        )
        if not test_method_id:
            return None
        self.stats["test_methods_created"] += 1
        self.log(f"Created test_method: {external_code} (id={test_method_id})")

        # 3. Create mapping for this workstation
        self.insert(
            """INSERT INTO workstation_test_methods
               (workstation_id, test_method_id, external_code) VALUES (?, ?, ?)""",
            (workstation_id, test_method_id, external_code)
        )
        self.stats["mappings_created"] += 1

        # Cache it
        self._mapping_cache[(workstation_id, external_code)] = test_method_id
        return test_method_id

    def get_or_create_test_method(self, workstation_id: int, external_code: str) -> Optional[int]:
        """Get existing test_method_id or create new one."""
        test_method_id = self.get_test_method_id(workstation_id, external_code)
        if test_method_id:
            return test_method_id
        return self.create_test_and_method(external_code, workstation_id)

    def get_batch_id(
        self, lot_number: str, level: int, test_method_id: int, workstation_id: int
    ) -> Optional[int]:
        """Get batch_id (cached)."""
        # Batch key includes level in lot_number for uniqueness
        batch_lot = f"{lot_number}-L{level}"
        cache_key = (batch_lot, test_method_id, workstation_id, level)

        if cache_key in self._batch_cache:
            return self._batch_cache[cache_key]

        row = self.fetch_one(
            """SELECT batch_id FROM batches
               WHERE lot_number = ? AND test_method_id = ? AND workstation_id = ? AND status = 1""",
            (batch_lot, test_method_id, workstation_id)
        )
        if row:
            self._batch_cache[cache_key] = row["batch_id"]
            return row["batch_id"]
        return None

    def create_batch(
        self,
        lot_number: str,
        level: int,
        test_method_id: int,
        workstation_id: int,
        target: float,
        sd: float,
        expiration: str,
        control_name: str,
        lab_id: int = 2
    ) -> Optional[int]:
        """Create new batch. Returns batch_id."""
        # Include level in lot_number
        batch_lot = f"{lot_number}-L{level}"

        # Parse expiration date (YYYYMMDD -> YYYY-MM-DD)
        try:
            exp_date = datetime.strptime(expiration, "%Y%m%d").strftime("%Y-%m-%d")
        except ValueError:
            exp_date = "2099-12-31"  # fallback

        # Description: control name + level
        description = f"{control_name} L{level}"

        batch_id = self.insert(
            """INSERT INTO batches
               (lab_id, test_method_id, workstation_id, lot_number, description,
                target, sd, expiration, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (lab_id, test_method_id, workstation_id, batch_lot, description,
             target, sd, exp_date)
        )
        if batch_id:
            self.stats["batches_created"] += 1
            self.log(f"Created batch: {batch_lot} - {description} (id={batch_id})")
            cache_key = (batch_lot, test_method_id, workstation_id, level)
            self._batch_cache[cache_key] = batch_id
        return batch_id

    def get_or_create_batch(
        self,
        lot_number: str,
        level: int,
        test_method_id: int,
        workstation_id: int,
        target: float,
        sd: float,
        expiration: str,
        control_name: str
    ) -> Optional[int]:
        """Get existing batch or create new one."""
        batch_id = self.get_batch_id(lot_number, level, test_method_id, workstation_id)
        if batch_id:
            return batch_id
        return self.create_batch(
            lot_number, level, test_method_id, workstation_id,
            target, sd, expiration, control_name
        )

    def result_exists(self, batch_id: int, workstation_id: int, received: datetime) -> bool:
        """Check if result already exists (avoid duplicates)."""
        row = self.fetch_one(
            """SELECT result_id FROM results
               WHERE batch_id = ? AND workstation_id = ? AND received = ?""",
            (batch_id, workstation_id, received)
        )
        return row is not None

    def insert_result(
        self,
        batch_id: int,
        workstation_id: int,
        result_value: float,
        received: datetime
    ) -> bool:
        """Insert QC result."""
        # Check for duplicate
        if self.result_exists(batch_id, workstation_id, received):
            self.stats["results_skipped"] += 1
            return False

        result_id = self.insert(
            """INSERT INTO results
               (batch_id, lab_id, run_number, workstation_id, result, received,
                status, validated, is_delete, log_id)
               VALUES (?, ?, '0', ?, ?, ?, 1, 0, 0, 1)""",
            (batch_id, LAB_ID, workstation_id, result_value, received)
        )
        if result_id:
            self.stats["results_inserted"] += 1
            return True
        return False

    # -------------------------------------------------------------------------
    # File parsing
    # -------------------------------------------------------------------------

    def parse_abbott_line(self, line: str) -> Optional[Dict]:
        """
        Parse single Abbott QC line.

        Format: pipe-delimited, key fields:
        - [7]  Control name (MCHEMIA, PCT, etc.)
        - [8]  Lot number (032807240)
        - [9]  Expiration (YYYYMMDD)
        - [10] Level (1, 2, 3)
        - [12] Test code (311, VITD, etc.)
        - [14] DateTime (YYYYMMDDHHMMSSmmm)
        - [15] Result value
        - [16] Workstation (ALCI-1, ALCI-2, ALCI-3)
        - [18] Target
        - [19] SD
        """
        parts = line.strip().split("|")
        if len(parts) < 20:
            return None

        try:
            workstation = parts[16].strip()
            if workstation not in VALID_WORKSTATIONS:
                return None

            # Parse datetime (YYYYMMDDHHMMSSmmm)
            dt_str = parts[14].strip()
            if len(dt_str) >= 14:
                received = datetime.strptime(dt_str[:14], "%Y%m%d%H%M%S")
            else:
                return None

            return {
                "control_name": parts[7].strip(),
                "lot_number": parts[8].strip(),
                "expiration": parts[9].strip(),
                "level": int(parts[10].strip()),
                "test_code": parts[12].strip(),
                "received": received,
                "result": float(parts[15].strip()),
                "workstation": workstation,
                "target": float(parts[18].strip()) if parts[18].strip() else 0.0,
                "sd": float(parts[19].strip()) if parts[19].strip() else 0.0,
            }
        except (ValueError, IndexError) as e:
            self.log(f"Parse error: {e}")
            return None

    def process_file(self, filepath: Path) -> int:
        """Process single Abbott file. Returns number of results inserted."""
        count = 0
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    data = self.parse_abbott_line(line)
                    if not data:
                        continue

                    # 1. Get workstation_id
                    workstation_id = self.get_workstation_id(data["workstation"])
                    if not workstation_id:
                        self.log(f"Unknown workstation: {data['workstation']}")
                        continue

                    # 2. Get or create test_method
                    test_method_id = self.get_or_create_test_method(
                        workstation_id, data["test_code"]
                    )
                    if not test_method_id:
                        continue

                    # 3. Get or create batch
                    batch_id = self.get_or_create_batch(
                        lot_number=data["lot_number"],
                        level=data["level"],
                        test_method_id=test_method_id,
                        workstation_id=workstation_id,
                        target=data["target"],
                        sd=data["sd"],
                        expiration=data["expiration"],
                        control_name=data["control_name"],
                    )
                    if not batch_id:
                        continue

                    # 4. Insert result
                    if self.insert_result(
                        batch_id, workstation_id, data["result"], data["received"]
                    ):
                        count += 1

        except IOError as e:
            print(f"[ERROR] Cannot read file {filepath}: {e}")
            self.stats["errors"] += 1

        return count

    def get_imported_files(self) -> set:
        """Get set of already imported filenames."""
        rows = self.fetch_all("SELECT filename FROM abbott_imported_files")
        return {row["filename"] for row in rows}

    def mark_file_imported(self, filename: str, records_count: int):
        """Mark file as imported."""
        if not self.dry_run:
            self.insert(
                "INSERT INTO abbott_imported_files (filename, records_count) VALUES (?, ?)",
                (filename, records_count)
            )

    def run(self, limit: Optional[int] = None):
        """Run the import process."""
        print(f"Abbott QC Importer - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Source: {ABBOTT_PATH}")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        print("-" * 60)

        if not self.connect():
            return

        # Check if tracking table exists
        row = self.fetch_one(
            "SELECT COUNT(*) as cnt FROM information_schema.tables "
            "WHERE table_schema = 'biovarase' AND table_name = 'abbott_imported_files'"
        )
        if not row or row["cnt"] == 0:
            print("[ERROR] Table 'abbott_imported_files' does not exist.")
            print("Please run: migrations/006_abbott_import.sql")
            self.disconnect()
            return

        # Get already imported files
        imported_files = self.get_imported_files()
        print(f"Already imported: {len(imported_files)} files")

        # Scan directory
        if not os.path.isdir(ABBOTT_PATH):
            print(f"[ERROR] Directory not found: {ABBOTT_PATH}")
            print("Is the share mounted? Try: sudo mount /mnt/biovarase_qc")
            self.disconnect()
            return

        files = sorted(Path(ABBOTT_PATH).glob("*.txt"))
        print(f"Found: {len(files)} files")

        # Filter new files
        new_files = [f for f in files if f.name not in imported_files]
        print(f"New files: {len(new_files)}")

        if limit:
            new_files = new_files[:limit]
            print(f"Limited to: {limit} files")

        print("-" * 60)

        # Process files
        for filepath in new_files:
            print(f"Processing: {filepath.name}")
            count = self.process_file(filepath)

            if count > 0 or not self.dry_run:
                self.mark_file_imported(filepath.name, count)
                self.stats["files_processed"] += 1
            else:
                self.stats["files_skipped"] += 1

            if not self.dry_run:
                self.con.commit()

        # Final commit
        if not self.dry_run:
            self.con.commit()

        self.disconnect()

        # Print summary
        print("-" * 60)
        print("SUMMARY")
        print(f"  Files processed:    {self.stats['files_processed']}")
        print(f"  Files skipped:      {self.stats['files_skipped']}")
        print(f"  Results inserted:   {self.stats['results_inserted']}")
        print(f"  Results skipped:    {self.stats['results_skipped']} (duplicates)")
        print(f"  Tests created:      {self.stats['tests_created']}")
        print(f"  Test methods:       {self.stats['test_methods_created']}")
        print(f"  Mappings created:   {self.stats['mappings_created']}")
        print(f"  Batches created:    {self.stats['batches_created']}")
        print(f"  Errors:             {self.stats['errors']}")


def main():
    parser = argparse.ArgumentParser(description="Import Abbott QC data into Biovarase")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Simulate import without writing to database"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Print detailed progress"
    )
    parser.add_argument(
        "--limit", "-l", type=int, default=None,
        help="Limit number of files to process"
    )
    args = parser.parse_args()

    importer = AbbottImporter(dry_run=args.dry_run, verbose=args.verbose)
    importer.run(limit=args.limit)


if __name__ == "__main__":
    main()
