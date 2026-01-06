# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:   [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV
#-----------------------------------------------------------------------------
"""
Importer module for Biovarase.

New rule:
    - The filename MUST contain only the device_id, for example:
          123e4567-e89b-12d3-a456-426614174001
      (extensions like ".txt" are tolerated, but the base name must be
       the device_id).

Key ideas:
    - Use an external INI file (workstation_profiles.ini) to describe how
      to parse each file type for a specific instrument.
    - Select the appropriate profile directly from the device_id extracted
      from the filename.
    - Normalize the output into records with:
        analyte    -> tests.description
        lot_number -> batches.lot_number
        result     -> numeric result (float)

Public API:
    get_generic_file_auto(filepath)
        -> rows, device_id, profile_name

    get_generic_file(filename)
        -> rows      (backward-compatible wrapper)

This module:
    * MUST NOT depend on GUI widgets.
    * MUST NOT use print() or exit().
    * MUST log any exception with self.on_log().
"""

import os
import sys
import re
import csv
import inspect
import configparser
from typing import Dict, List, Optional, Any, Tuple


class Importer:
    """Configuration-driven importer mixin keyed by device_id filenames."""

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get_generic_file_auto(
        self,
        filepath: str,
        device_id: str,
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], Optional[str]]:
        """
        Parse a QC file using the profile associated with the given device_id.

        Args:
            filepath: Path to QC file (any filename accepted)
            device_id: Device UUID from workstations table (e.g., '123e4567-e89b-12d3-a456-426614174001')

        The device_id is retrieved from the workstations table by the caller,
        not extracted from the filename. This allows files to have any name.

        Returns:
            rows, device_id, profile_name

            rows: list of dicts like:
                {
                    "analyte":    <tests.description>,
                    "lot_number": <batches.lot_number>,
                    "result":     <float>,
                    "reagent_lot": <str or None>,  # From file if available
                }

            device_id: the workstation device_id (echoed back from input)
            profile_name: the name of the matched profile (INI section)

        On failure returns (None, None, None).
        """
        try:
            if not filepath:
                return None, None, None

            path = os.path.abspath(filepath)
            if not os.path.isfile(path):
                self._log_warning("get_generic_file_auto", f"File not found: {path}")
                return None, None, None

            if not device_id:
                self._log_warning(
                    "get_generic_file_auto",
                    "device_id parameter is required",
                )
                return None, None, None

            profiles = self._load_profiles()
            if not profiles:
                profiles = self._builtin_profiles()

            profile_key = f"device_{device_id}"
            profile = profiles.get(profile_key)

            if not profile:
                # Optional default profile
                profile = profiles.get("default")
                if not profile:
                    self._log_warning(
                        "get_generic_file_auto",
                        f"No profile found for device_id={device_id}",
                    )
                    return None, None, None
                profile_name = "default"
            else:
                profile_name = profile_key

            if not self._header_matches(path, profile):
                self._log_warning(
                    "get_generic_file_auto",
                    f"Header does not match profile '{profile_name}' for file: {path}",
                )
                return None, None, None

            rows = self._parse_file_with_profile_normalized(path, profile)
            if not rows:
                return None, None, None

            return rows, device_id, profile_name

        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )
            return None, None, None

    def get_generic_file(
        self,
        filename: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Backward-compatible wrapper (DEPRECATED).

        This method extracts device_id from the filename (old behavior)
        and calls get_generic_file_auto().

        New code SHOULD use get_generic_file_auto() directly with device_id
        from the workstations table.
        """
        device_id = self._extract_device_id_from_filename(filename)
        if not device_id:
            return None
        rows, _device_id, _profile = self.get_generic_file_auto(filename, device_id)
        return rows

    # ------------------------------------------------------------------ #
    # Profiles handling
    # ------------------------------------------------------------------ #
    def _profiles_file_path(self) -> str:
        """
        Return the full path of the workstation profiles configuration file.

        This uses the directory of the current module, so it does not depend
        on Engine.get_file(), keeping the mixin self-contained.
        """
        base_dir = os.path.dirname(__file__)
        return os.path.join(base_dir, "workstation_profiles.ini")

    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Load import profiles from 'workstation_profiles.ini'.

        Each section can contain:
            description
            extensions
            delimiter
            component_field
            id_field
            result_field
            reagent_lot_field
            sample_type_field
            sample_type_value
            exclude_suffix
            exclude_prefix
            result_format
        """
        profiles: Dict[str, Dict[str, Any]] = {}

        try:
            path = self._profiles_file_path()
            if not os.path.isfile(path):
                return profiles  # No file: caller will use builtin profiles.

            config = configparser.ConfigParser()
            config.read(path, encoding="utf-8")

            for section in config.sections():
                sec = config[section]

                def _split_list(value: str) -> List[str]:
                    return [
                        x.strip()
                        for x in value.split(",")
                        if x.strip()
                    ]

                profiles[section] = {
                    "description": sec.get("description", "").strip(),
                    "extensions": _split_list(sec.get("extensions", "")),
                    "delimiter": sec.get("delimiter", "tab").strip().lower(),
                    "component_field": sec.get("component_field", "").strip(),
                    "id_field": sec.get("id_field", "").strip(),
                    "result_field": sec.get("result_field", "").strip(),
                    "reagent_lot_field": sec.get("reagent_lot_field", "").strip(),
                    "sample_type_field": sec.get("sample_type_field", "").strip(),
                    "sample_type_value": sec.get("sample_type_value", "").strip(),
                    "exclude_suffix": _split_list(sec.get("exclude_suffix", "")),
                    "exclude_prefix": _split_list(sec.get("exclude_prefix", "")),
                    "result_format": sec.get("result_format", "raw").strip().lower(),
                }

        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

        return profiles

    def _builtin_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Provide a builtin default profile (safety net) used when the
        external file is missing.
        """
        return {
            "default": {
                "description": "Builtin default QC profile",
                "extensions": [".txt", ".csv"],
                "delimiter": "tab",
                "component_field": "Component Name",
                "id_field": "Barcode",
                "result_field": "Mean",
                "reagent_lot_field": "",  # Optional field
                "sample_type_field": "",
                "sample_type_value": "",
                "exclude_suffix": ["_qual"],
                "exclude_prefix": [],
                "result_format": "float3",
            },
        }

    # ------------------------------------------------------------------ #
    # Core parsing logic
    # ------------------------------------------------------------------ #
    @staticmethod
    def _extract_device_id_from_filename(filepath: str) -> Optional[str]:
        """
        Extract device_id from filename.

        Rules:
            - use the basename (without path)
            - search inside it for a UUID-like pattern:
                  8-4-4-4-12 characters with hyphens
            - return the first match found
        """
        base = os.path.basename(filepath)

        # Regex for UUID-like string: 8-4-4-4-12 alphanumeric chars
        pattern = r"[0-9a-zA-Z]{8}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{4}-[0-9a-zA-Z]{12}"
        match = re.search(pattern, base)
        if match:
            return match.group(0)

        return None

    def _get_delimiter(self, name: str) -> str:
        """
        Map a profile delimiter name to an actual character.
        """
        name = (name or "").strip().lower()
        if name == "tab":
            return "\t"
        if name == "semicolon":
            return ";"
        if name == "comma":
            return ","
        # Default: tab (typical for instrument exports)
        return "\t"

    def _header_matches(self, filepath: str, profile: Dict[str, Any]) -> bool:
        """
        Check if the file header contains the required columns declared
        in the profile. It opens the file once and reads only the first line.
        """
        component_field = profile.get("component_field") or ""
        id_field = profile.get("id_field") or ""
        result_field = profile.get("result_field") or ""

        if not component_field or not id_field or not result_field:
            return False

        delimiter = self._get_delimiter(profile.get("delimiter", "tab"))

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.reader(fh, delimiter=delimiter)
                header = next(reader, None)

            if not header:
                return False

            header_norm = [h.strip() for h in header]
            needed = {component_field, id_field, result_field}
            if not needed.issubset(set(header_norm)):
                return False

            return True

        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )
            return False

    def _parse_file_with_profile_normalized(
        self,
        filepath: str,
        profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """
        Parse the file using the given profile and return normalized rows:

            {
                "analyte":    <tests.description>,
                "lot_number": <batches.lot_number>,
                "result":     <float>,
                "reagent_lot": <str or None>,  # Optional, from file if available
            }
        """
        data: List[Dict[str, Any]] = []

        component_field = profile.get("component_field") or ""
        id_field = profile.get("id_field") or ""
        result_field = profile.get("result_field") or ""
        reagent_lot_field = profile.get("reagent_lot_field") or ""

        sample_type_field = profile.get("sample_type_field") or ""
        sample_type_value = profile.get("sample_type_value") or ""

        exclude_suffix = profile.get("exclude_suffix") or []
        exclude_prefix = profile.get("exclude_prefix") or []

        result_format = profile.get("result_format", "raw")

        delimiter = self._get_delimiter(profile.get("delimiter", "tab"))

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.reader(fh, delimiter=delimiter)
                header = next(reader, None)
                if not header:
                    return data

                header_norm = [h.strip() for h in header]

                try:
                    idx_component = header_norm.index(component_field)
                    idx_id = header_norm.index(id_field)
                    idx_result = header_norm.index(result_field)
                except ValueError:
                    self._log_warning(
                        "_parse_file_with_profile_normalized",
                        (
                            "Required columns not found in header for "
                            f"profile '{profile.get('description', '')}'"
                        ),
                    )
                    return []

                idx_sample_type: Optional[int] = None
                if sample_type_field:
                    try:
                        idx_sample_type = header_norm.index(sample_type_field)
                    except ValueError:
                        idx_sample_type = None

                idx_reagent_lot: Optional[int] = None
                if reagent_lot_field:
                    try:
                        idx_reagent_lot = header_norm.index(reagent_lot_field)
                    except ValueError:
                        idx_reagent_lot = None

                for row in reader:
                    if not row:
                        continue

                    if len(row) <= max(idx_component, idx_id, idx_result):
                        continue

                    # Optional Sample Type filter
                    if idx_sample_type is not None and sample_type_value:
                        try:
                            sample_type = row[idx_sample_type].strip()
                        except IndexError:
                            sample_type = ""
                        if sample_type != sample_type_value:
                            continue

                    analyte = row[idx_component].strip()
                    if not analyte:
                        continue

                    # Exclude suffix/prefix (e.g. _qual, IS )
                    if any(analyte.endswith(suf) for suf in exclude_suffix):
                        continue
                    if any(analyte.startswith(pre) for pre in exclude_prefix):
                        continue

                    lot_number = row[idx_id].strip()

                    # Extract reagent lot if column exists
                    reagent_lot = None
                    if idx_reagent_lot is not None:
                        try:
                            reagent_lot = row[idx_reagent_lot].strip() or None
                        except IndexError:
                            reagent_lot = None

                    raw_result = row[idx_result].strip()
                    result_str = self._format_result(raw_result, result_format)
                    if result_str is None:
                        continue

                    try:
                        result_val = float(result_str)
                    except ValueError:
                        continue

                    data.append(
                        {
                            "analyte": analyte,
                            "lot_number": lot_number,
                            "result": result_val,
                            "reagent_lot": reagent_lot,
                        }
                    )

        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                e,
                type(e),
                sys.modules[__name__],
            )

        return data

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _format_result(self, value: str, fmt: str) -> Optional[str]:
        """
        Format the result string according to the profile format.

        Supported formats:
            - "raw" (default): return the value as-is (strip only).
            - "floatN": parse as float and format with N decimals.

        Returns:
            formatted string or None on parsing error.
        """
        value = (value or "").strip()
        if fmt == "raw":
            return value

        if fmt.startswith("float"):
            try:
                decimals_str = fmt.replace("float", "").strip()
                decimals = int(decimals_str) if decimals_str.isdigit() else 2
                num = float(value)
                return f"{num:.{decimals}f}"
            except (ValueError, TypeError) as e:
                return None

        return value

    def _log_warning(self, function: str, message: str) -> None:
        """
        Lightweight wrapper to log non-fatal warnings using on_log().
        """
        try:
            exc = RuntimeError(message)
            self.on_log(
                function,
                exc,
                type(exc),
                sys.modules[__name__],
            )
        except Exception as e:
            # Logging MUST NOT fail
            pass


def main():
    foo = Importer()
    print(foo)
    input("end")


if __name__ == "__main__":
    main()
