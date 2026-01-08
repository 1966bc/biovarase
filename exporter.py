# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  1966bc
# mailto:    [giuseppecostanzi@gmail.com]
# modify:   ver MMXXV
# This script has been significantly enhanced through collaboration with a programming assistant aka Gemini.
# -----------------------------------------------------------------------------
""" This is the exporter module of Biovarase."""

import sys
import inspect
import tempfile
from datetime import date, datetime

import openpyxl
from westgards import WESTGARD_ACCEPT
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet


class Exporter:
    """Mixin responsible for Excel export utilities (openpyxl based)."""

    # ------------------------------------------------------------------ #
    #  Generic helpers                                                   #
    # ------------------------------------------------------------------ #

    def __str__(self):
        mro = [cls.__name__ for cls in Exporter.__mro__]
        return "class: {0}\nMRO: {1}".format(self.__class__.__name__, mro)

    def create_workbook(self, title="Biovarase"):
        """Create a new workbook with a single active sheet named *title*."""
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = title
        return wb, ws

    def save_and_launch(self, workbook, suffix=".xlsx"):
        """
        Save the workbook to a temporary file and launch it with the OS handler.

        Returns:
            str: full path of the created file.
        """
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.close()
        path = tmp.name
        workbook.save(path)
        # Launcher mixin: open file with system handler
        self.launch(path)  # type: ignore
        return path

    def get_counts(self, selected_date):
        """
        Export the counts of executed test methods, starting from a given date.

        Fully PROJECT_RULES compliant:
        - read_dict() with clear SQL aliases
        - NO positional indexing
        - descriptive dictionary keys
        """

        try:
            sql = """
                SELECT
                    tm.test_method_id     AS test_method_id,
                    tm.code               AS code,
                    t.description         AS test_description,
                    s.sample              AS sample,
                    c.description         AS category,
                    COUNT(r.batch_id)     AS total_count
                FROM tests AS t
                INNER JOIN test_methods AS tm ON t.test_id = tm.test_id
                INNER JOIN batches      AS b  ON tm.test_method_id = b.test_method_id
                INNER JOIN categories   AS c  ON tm.category_id = c.category_id
                INNER JOIN samples      AS s  ON tm.sample_id = s.sample_id
                INNER JOIN sections     AS se ON tm.section_id = se.section_id
                INNER JOIN labs         AS l  ON se.lab_id = l.lab_id
                INNER JOIN results      AS r  ON b.batch_id = r.batch_id
                WHERE t.status = 1
                  AND tm.status = 1
                  AND se.section_id = ?
                  AND DATE(r.received) >= ?
                  AND r.is_delete = 0
                GROUP BY tm.test_method_id
                ORDER BY t.description;
            """

            args = (self.get_section_id(), selected_date)
            rows = self.read(True, sql, args)

            workbook, worksheet = self.create_workbook("Biovarase")
            row_num = 1

            headers = ("Code", "Test", "Sample", "Category", "Count")
            font_bold = Font(bold=True)

            # Header
            for col_num, text in enumerate(headers, start=1):
                cell = worksheet.cell(row=row_num, column=col_num, value=text)
                cell.font = font_bold

            row_num += 1

            # Data rows
            for row in rows:
                worksheet.cell(row=row_num, column=1, value=row["code"])
                worksheet.cell(row=row_num, column=2, value=row["test_description"])
                worksheet.cell(row=row_num, column=3, value=row["sample"])
                worksheet.cell(row=row_num, column=4, value=row["category"])
                worksheet.cell(row=row_num, column=5, value=row["total_count"])
                row_num += 1

            self.save_and_launch(workbook)

        except Exception as e:
            self.on_log(
                inspect.stack()[0][3],
                sys.exc_info()[1],
                sys.exc_info()[0],
                sys.modules[__name__],
            )

    def get_notes(self, args):
        """
        Export notes data (date ≥ selected_date, filtered by section_id).

        Fully compliant with PROJECT_RULES:
        - uses read_dict() → dictionary rows
        - no positional indexing
        - explicit and readable SQL
        """

        sql = """
            SELECT
                tests.description               AS test_description,
                batches.lot_number              AS batch_lot,
                batches.target                  AS batch_target,
                batches.sd                      AS batch_sd,
                results.result                  AS result_value,
                DATE_FORMAT(results.received, '%d-%m-%Y %H-%i-%s') AS received_fmt,
                actions.description             AS action_description,
                notes.description               AS note_description,
                notes.modified                  AS note_modified,
                equipments.description          AS equipment_description,
                workstations.description        AS workstation_description,
                workstations.serial             AS workstation_serial,
                labs.description                AS lab_description,
                sections.description            AS section_description
            FROM tests
            INNER JOIN test_methods ON tests.test_id = test_methods.test_id
            INNER JOIN batches ON test_methods.test_method_id = batches.test_method_id
            INNER JOIN results ON batches.batch_id = results.batch_id
            INNER JOIN workstations ON results.workstation_id = workstations.workstation_id
            INNER JOIN equipments ON workstations.equipment_id = equipments.equipment_id
            INNER JOIN sections ON workstations.section_id = sections.section_id
            INNER JOIN labs ON sections.lab_id = labs.lab_id
            INNER JOIN notes ON results.result_id = notes.result_id
            INNER JOIN actions ON notes.action_id = actions.action_id
            WHERE DATE(results.received) >= ?
              AND sections.section_id = ?
              AND tests.status  = 1
              AND batches.status = 1
              AND results.is_delete = 0
            ORDER BY notes.modified DESC;
        """

        rows = self.read(True, sql, args)

        workbook, worksheet = self.create_workbook("Biovarase")
        row_num = 1

        headers = (
            "Test", "Batch", "Target", "SD", "Result",
            "Received", "Action", "Description", "Modified",
            "Instrument", "Workstation", "Serial", "Lab", "Section"
        )

        font_bold = Font(bold=True, name="Arial")

        # Header
        for col_num, text in enumerate(headers, start=1):
            cell = worksheet.cell(row=row_num, column=col_num, value=text)
            cell.font = font_bold

        row_num += 1

        # Data rows
        if rows:
            for row in rows:
                worksheet.cell(row=row_num, column=1,  value=row["test_description"])
                worksheet.cell(row=row_num, column=2,  value=row["batch_lot"])
                worksheet.cell(row=row_num, column=3,  value=row["batch_target"])
                worksheet.cell(row=row_num, column=4,  value=round(row["batch_sd"], 3))
                worksheet.cell(row=row_num, column=5,  value=round(row["result_value"], 2))
                worksheet.cell(row=row_num, column=6,  value=row["received_fmt"])
                worksheet.cell(row=row_num, column=7,  value=row["action_description"])
                worksheet.cell(row=row_num, column=8,  value=row["note_description"])
                worksheet.cell(row=row_num, column=9,  value=row["note_modified"])
                worksheet.cell(row=row_num, column=10, value=row["equipment_description"])
                worksheet.cell(row=row_num, column=11, value=row["workstation_description"])
                worksheet.cell(row=row_num, column=12, value=row["workstation_serial"])
                worksheet.cell(row=row_num, column=13, value=row["lab_description"])
                worksheet.cell(row=row_num, column=14, value=row["section_description"])

                row_num += 1

        self.save_and_launch(workbook)

    # ------------------------------------------------------------------ #
    #  Quick data analysis helpers                                       #
    # ------------------------------------------------------------------ #

    def _color(self, name):
        """Return ARGB for openpyxl PatternFill. Uses Tools mixin if available."""
        fn = getattr(self, "_convert_color", None)
        if callable(fn):
            return fn(name)  # type: ignore

        lut = {
            "red": "FFFF0000",
            "yellow": "FFFFFF00",
            "green": "FF00FF00",
        }
        n = str(name).strip().lstrip("#")
        if len(n) in (6, 8) and all(c in "0123456789ABCDEFabcdef" for c in n):
            return n.upper() if len(n) == 8 else ("FF" + n.upper())
        return lut.get(name.lower(), "FF000000")  # default black

    def _normalize_date(self, selected_date):
        """Accept date|datetime|(date,) and return (date_obj, 'YYYY-MM-DD')."""
        d = (
            selected_date[0]
            if isinstance(selected_date, (tuple, list)) and selected_date
            else selected_date
        )

        if isinstance(d, datetime):
            d = d.date()

        if not isinstance(d, date):
            raise TypeError("selected_date must be a date; got: {0}".format(type(d)))

        return d, d.isoformat()

    def _setup_sheet(self, workbook):
        """Create sheet, set widths, header, freeze, filter. Return (worksheet, next_row)."""

        ws = workbook.active
        ws.title = "Biovarase"

        # column widths
        ws.column_dimensions[get_column_letter(1)].width = 8
        ws.column_dimensions[get_column_letter(2)].width = 20
        ws.column_dimensions[get_column_letter(3)].width = 16
        ws.column_dimensions[get_column_letter(4)].width = 14
        ws.column_dimensions[get_column_letter(5)].width = 20
        for col in range(6, 16):
            ws.column_dimensions[get_column_letter(col)].width = 10
        ws.column_dimensions[get_column_letter(16)].width = 14
        ws.column_dimensions[get_column_letter(17)].width = 18
        ws.column_dimensions[get_column_letter(18)].width = 18
        ws.column_dimensions[get_column_letter(19)].width = 18
        ws.column_dimensions[get_column_letter(20)].width = 18

        # header
        header = (
            'Type', 'Test', 'Batch', 'Expiration', 'Equipment',
            'Target', 'Result', 'avg', 'bias', 'SD', 'sd', 'cv',
            'U',          # NEW: expanded uncertainty (absolute units)
            'Wstg',       # Westgard rule
            'Date', 'Category', 'Workstation', 'Control',
            'Supplier', 'Mandatory'
        )

        row = 1
        bold = Font(bold=True, name='Arial')
        for idx, title in enumerate(header, start=1):
            c = ws.cell(row=row, column=idx, value=title)
            c.font = bold

        ws.freeze_panes = "A2"
        ws.auto_filter.ref = "A1:{0}1".format(get_column_letter(len(header)))

        return ws, row + 1

    def _fetch_test_methods(self, lab_id, category_id=None):
        """
        Return test methods for a given lab as list of dicts with keys:
          - test_method_id
          - sample
          - test_description
          - category_description

        Args:
            lab_id: Laboratory ID
            category_id: Optional category filter (None or 0 = all, >0 = specific category)
        """
        sql = """
            SELECT
                tm.test_method_id       AS test_method_id,
                s.sample                AS sample,
                t.description           AS test_description,
                c.description           AS category_description
            FROM tests AS t
            INNER JOIN test_methods AS tm ON t.test_id     = tm.test_id
            INNER JOIN categories  AS c  ON tm.category_id = c.category_id
            INNER JOIN samples     AS s  ON tm.sample_id   = s.sample_id
            INNER JOIN sections    AS se ON tm.section_id  = se.section_id
            INNER JOIN labs        AS l  ON se.lab_id      = l.lab_id
            INNER JOIN sites       AS si ON l.site_id      = si.site_id
            WHERE l.lab_id = ?
              AND t.status = 1
              AND tm.status = 1
        """

        args = [lab_id]

        # Apply category filter if specified (and not 0 which means "All")
        if category_id and category_id > 0:
            sql += " AND tm.category_id = ?"
            args.append(category_id)

        sql += " ORDER BY t.description;"

        return self.read(True, sql, tuple(args)) or []  # type: ignore

    def _fetch_batches(self, test_method_id, lab_id):
        sql = """
            SELECT
                b.batch_id,
                b.lab_id,
                b.control_id,
                b.test_method_id,
                b.workstation_id,
                b.lot_number,
                b.expiration,
                b.target,
                b.sd,
                b.description,
                b.lower,
                b.upper,
                b.rank,
                b.status,
                b.log_time,
                b.log_id,
                b.log_ip,
                DATE_FORMAT(b.expiration, '%d-%m-%Y') AS expiration_fmt,
                w.serial AS workstation_serial,
                e.description AS equipment_description
            FROM batches AS b
            INNER JOIN workstations AS w ON b.workstation_id = w.workstation_id
            INNER JOIN equipments   AS e ON w.equipment_id   = e.equipment_id
            INNER JOIN sections     AS se ON w.section_id    = se.section_id
            INNER JOIN labs         AS l  ON l.lab_id        = se.lab_id
            WHERE b.status = 1
              AND b.test_method_id = ?
              AND l.lab_id = ?
        """
        return self.read(True, sql, (test_method_id, lab_id)) or []

    def _fetch_results(self, batch_id, day_sql, workstation_id):
        """
        Return result rows for a given batch, day and workstation as list of dicts.

        Keys:
          - result_id
          - result_value      (rounded)
          - received_text     (formatted)
          - received_datetime (datetime)
          - workstation_serial
          - workstation_id
          - received_date     (date)
        """
        sql = """
            SELECT
                r.result_id                          AS result_id,
                ROUND(r.result, 2)                   AS result_value,
                DATE_FORMAT(
                    r.received, '%d-%m-%Y %H-%i-%s'
                )                                    AS received_text,
                r.received                           AS received_datetime,
                w.serial                             AS workstation_serial,
                w.workstation_id                     AS workstation_id,
                DATE(r.received)                     AS received_date
            FROM results AS r
            INNER JOIN workstations AS w
                    ON r.workstation_id = w.workstation_id
            WHERE r.batch_id = ?
              AND DATE(r.received) = CAST(? AS DATE)
              AND w.workstation_id = ?
              AND r.status = 1
              AND r.is_delete = 0
            ORDER BY r.received DESC;
        """
        return self.read(True, sql, (batch_id, day_sql, workstation_id)) or []  # type: ignore

    def _fetch_control(self, control_id):
        """Return (control_desc, supplier_desc) or (None, None)."""
        sql = """
            SELECT
                c.description AS control_description,
                s.description AS supplier_description
            FROM controls AS c
            INNER JOIN suppliers AS s
                    ON c.supplier_id = s.supplier_id
            WHERE c.control_id = ?;
        """
        row = self.read(False, sql, (control_id,))  # type: ignore
        if not row:
            return None, None
        return row["control_description"], row["supplier_description"]

    def _compute_series_metrics(self, series):
        """Return (avg, sd, cv) from series."""
        avg = self.get_mean(series)  # type: ignore
        sd = self.get_sd(series)     # type: ignore
        cv = self.get_cv(series)     # type: ignore
        return avg, sd, cv

    def _westgard_rule_safe(self, target, sd, series, batch_row, tm_row):
        """Return Westgard rule or 'NED' if series length is insufficient."""
        if len(series) > 9:
            return self.get_westgard_violation_rule(  # type: ignore
                target,
                sd,
                series,
                batch_row,
                tm_row,
            )
        return "NED"

    def _result_color(self, res, target, sd):
        """Return 'red' (>=3SD), 'yellow' (>=2SD), else None."""
        up_2sd = target + (sd * 2)
        up_3sd = target + (sd * 3)
        dn_2sd = target - (sd * 2)
        dn_3sd = target - (sd * 3)

        if res >= up_3sd or res <= dn_3sd:
            return "red"
        if (up_2sd <= res < up_3sd) or (dn_3sd < res <= dn_2sd):
            return "yellow"
        return None

    def _highlight_expiration(self, ws, row_idx, expiration_date, received_date, expiration_text):
        """Write expiration text and color cell by days remaining."""
        cell = ws.cell(row=row_idx, column=4, value=expiration_text)  # Expiration column

        if expiration_date is None or received_date is None:
            return

        days = (expiration_date - received_date).days
        if days <= 0:
            color = self._color("red")
            cell.fill = PatternFill(
                start_color=color,
                end_color=color,
                fill_type="solid",
            )
        elif days <= 15:
            color = self._color("yellow")
            cell.fill = PatternFill(
                start_color=color,
                end_color=color,
                fill_type="solid",
            )

    def quick_data_analysis(self, selected_date, category_id=None):
        """
        Generate 'Biovarase' Excel report for a given day.

        Args:
            selected_date: Date to generate report for
            category_id: Optional category filter (None = all categories, 0 = all, >0 = specific category)
        """

        # 1) Normalize date
        day_obj, day_sql = self._normalize_date(selected_date)

        # 2) Workbook + sheet
        workbook, worksheet = self.create_workbook('Biovarase')
        worksheet, row_num = self._setup_sheet(workbook)

        # 3) Context
        checked_tests = []
        mandatory_tests = self.get_mandatory()

        # 4) Lab id (no positional indexing, use hierarchical context)
        lab_id = self.get_lab_id()
        if lab_id is None:
            # Fallback: derive lab_id from section_id using a dict result
            row = self.get_idd_by_section_id(self.get_section_id())
            if not row:
                # No valid context → nothing to export
                return
            lab_id = row["lab_id"]

        # 5) Fetch test methods (with optional category filter)
        for row in self._fetch_test_methods(lab_id, category_id):
            tm_id = row["test_method_id"]
            tm_sample = row["sample"]
            tm_test_desc = row["test_description"]
            tm_category_desc = row["category_description"]

            # 6) Batches per test method
            for batch in self._fetch_batches(tm_id, lab_id):

                b_batch_id = batch["batch_id"]
                b_lab_id = batch["lab_id"]
                b_control_id = batch["control_id"]
                b_test_method_id = batch["test_method_id"]
                b_workstation_id = batch["workstation_id"]

                b_lot_number = batch["lot_number"]
                b_expiration = batch["expiration"]
                b_target = batch["target"]
                b_sd = batch["sd"]

                b_description = batch["description"]
                b_lower = batch["lower"]
                b_upper = batch["upper"]
                b_rank = batch["rank"]
                b_status = batch["status"]
                b_log_time = batch["log_time"]
                b_log_id = batch["log_id"]
                b_log_ip = batch["log_ip"]

                b_expiration_fmt = batch["expiration_fmt"]
                b_ws_serial = batch["workstation_serial"]
                b_equipment_desc = batch["equipment_description"]

                # 7) Results of the day
                results = self._fetch_results(b_batch_id, day_sql, b_workstation_id)
                if not results:
                    continue

                # 8) Control info
                control_desc, control_supplier = self._fetch_control(b_control_id)

                for row in results:
                    r_result_id = row["result_id"]
                    r_result_rounded = row["result_value"]
                    r_received_str = row["received_text"]
                    r_received_dt = row["received_datetime"]
                    r_ws_serial = row["workstation_serial"]
                    r_workstation_id = row["workstation_id"]
                    r_received_date = row["received_date"]

                    try:
                        # Series and stats
                        series = self.get_series(
                            b_batch_id,
                            r_workstation_id,
                            int(self.get_observations()),
                            r_result_id,
                        )
                        if not series:
                            continue

                        rule = self._westgard_rule_safe(
                            b_target, b_sd, series,
                            batch,
                            (tm_id, tm_sample, tm_test_desc, tm_category_desc),
                        )

                        avg, sd_calc, cv = self._compute_series_metrics(series)

                        target = float(b_target)
                        sd_set = float(b_sd)
                        res = float(r_result_rounded)
                        bias = self.get_bias(avg, target)

                        # Uncertainty (absolute, same unit as result)
                        uncertainty = self.get_uncertainty(cv, bias)

                        # Colors by SD bands
                        r_color = self._result_color(res, target, sd_set)

                        # Write row cells
                        rc = worksheet.cell(row=row_num, column=1, value=tm_sample)         # Type
                        worksheet.cell(row=row_num, column=2, value=tm_test_desc)      # Test
                        worksheet.cell(row=row_num, column=3, value=b_lot_number)      # Batch

                        # Expiration highlight
                        self._highlight_expiration(worksheet, row_num, b_expiration, r_received_date, b_expiration_fmt)

                        worksheet.cell(row=row_num, column=5, value=b_equipment_desc)  # Equipment
                        worksheet.cell(row=row_num, column=6, value=target)            # Target

                        # Result + fill
                        rc = worksheet.cell(row=row_num, column=7, value=res)
                        if r_color:
                            rc.fill = PatternFill(
                                start_color=self._color(r_color),
                                end_color=self._color(r_color),
                                fill_type="solid",
                            )

                        worksheet.cell(row=row_num, column=8, value=avg)               # avg
                        worksheet.cell(row=row_num, column=9, value=bias)              # bias
                        worksheet.cell(row=row_num, column=10, value=round(sd_set, 2))  # SD (set)
                        worksheet.cell(row=row_num, column=11, value=sd_calc)           # sd (calc)
                        worksheet.cell(row=row_num, column=12, value=cv)                # cv
                        worksheet.cell(row=row_num, column=13, value=uncertainty)       # U (absolute)

                        wc = worksheet.cell(row=row_num, column=14, value=rule)         # Westgard rule
                        if rule not in (WESTGARD_ACCEPT, 'No data'):
                            wc.fill = PatternFill(
                                start_color=self._color("yellow"),
                                end_color=self._color("yellow"),
                                fill_type="solid",
                            )

                        worksheet.cell(row=row_num, column=15, value=r_received_str)    # Date text
                        worksheet.cell(row=row_num, column=16, value=tm_category_desc)  # Category
                        worksheet.cell(row=row_num, column=17, value=r_ws_serial)       # Workstation
                        worksheet.cell(row=row_num, column=18, value=control_desc)      # Control
                        worksheet.cell(row=row_num, column=19, value=control_supplier)  # Supplier (control)

                        checked_tests.append(tm_test_desc)
                        row_num += 1

                    except Exception as e:
                        # Minimal debug without breaking the loop
                        print("result:", (r_result_id, r_result_rounded, r_received_str, r_ws_serial, r_workstation_id))
                        try:
                            print("series/metrics:", (self.get_cv(series), self.get_sd(series), self.get_mean(series)))
                        except Exception as e:
                            print("series/metrics:", None)
                        print("target/sd:", (b_target, b_sd))
                        print(
                            inspect.stack()[0][3],
                            sys.exc_info()[1],
                            sys.exc_info()[0],
                            sys.modules[__name__],
                        )

        # 9) Mark missing mandatory tests (col 20)
        for t in checked_tests[:]:
            if t in mandatory_tests:
                mandatory_tests.remove(t)

        r = 2
        for missing in mandatory_tests:
            mc = worksheet.cell(row=r, column=20, value=missing)
            mc.fill = PatternFill(
                start_color=self._color("red"),
                end_color=self._color("red"),
                fill_type="solid",
            )
            r += 1

        # 10) Save
        self.save_and_launch(workbook)

    def get_analitical_goals(self, limit, rs):
        """
        Build the 'Analytical Goals' Excel report.

        rs is expected to be a list of dictionaries with keys:
        - batch_id
        - sample
        - analyte
        - batch
        - expiration
        - target
        - cvw
        - cvb
        - imp
        - bias
        - teap005
        - teap001
        - workstation_id
        """

        workbook, worksheet = self.create_workbook('Biovarase')

        column_widths = [6, 20, 8, 20, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 6, 10, 25]
        max_width_a = 6
        max_width_c = 8
        max_width_e_q = 6

        # header
        headers = (
            'T', 'analyte', 'batch', 'expiration', 'target', 'avg',
            'CVa', 'CVw', 'CVb', 'Imp%', 'Bias%', 'TEa%', 'CVt',
            'k imp', 'k bias', 'TE%', 'Drc%', 'records', 'wst'
        )
        font_bold = Font(bold=True, name='Arial')
        worksheet.append(list(headers))

        # set bold
        for cell in worksheet[1]:
            cell.font = font_bold

        for col_num, text in enumerate(headers):
            column_widths[col_num] = max(column_widths[col_num], len(str(text)) + 2)
            if col_num == 0:
                column_widths[col_num] = min(column_widths[col_num], max_width_a + 2)
            elif col_num == 2:
                column_widths[col_num] = min(column_widths[col_num], max_width_c + 2)
            elif 4 <= col_num <= 16:
                column_widths[col_num] = min(column_widths[col_num], max_width_e_q + 2)

        row_num = 2

        for row in rs:
            batch_id = row["batch_id"]
            workstation_id = row["workstation_id"]

            # series for this batch/workstation
            series = self.get_series(batch_id, workstation_id, limit)

            if len(series) > 5:
                cva = self.get_cv(series)
                sd = self.get_sd(series)
                avg = self.get_mean(series)
                cvw = row["cvw"]
                cvb = row["cvb"]
                target = float(row["target"])

                formula_imp = self.get_formula_imp(row_num)
                formula_bias = self.get_formula_bias(row_num)
                formula_eta = self.get_formula_eta(row_num)
                formula_cvt = self.get_formula_cvt(row_num)
                formula_k_imp_res = self.get_formula_k_imp(cva, cvw, row_num)
                formula_k_bias_res = self.get_formula_k_bias(
                    avg, target, cvw, cva, row_num
                )
                # ATTENZIONE: metodo si chiama get_tea_tes_comparision
                tea_tes_comparision_res = self.get_tea_tes_comparision(
                    avg, target, cvw, cvb, sd, cva
                )
                formula_drc = self.get_formula_drc(row_num)

                # Workstation description (use read_dict + dict access)
                ws_row = self.read(
                    False,
                    "SELECT description FROM workstations WHERE workstation_id = ?",
                    (workstation_id,),
                )
                workstation_description = ws_row["description"] if ws_row else None

                row_data = [
                    row["sample"],                    # T
                    row["analyte"],                   # analyte
                    str(row["batch"]),                # batch
                    str(row["expiration"]),           # expiration
                    target,                           # target
                    avg,                              # avg
                    float(cva) if cva is not None else None,  # CVa
                    float(cvw) if cvw is not None else None,  # CVw
                    float(cvb) if cvb is not None else None,  # CVb
                    '={0}'.format(formula_imp),                # Imp% (col J)
                    '={0}'.format(formula_bias),               # Bias% (col K)
                    '={0}'.format(formula_eta),                # TEa% (col L)
                    '={0}'.format(formula_cvt),                # CVt (col M)
                    formula_k_imp_res[0] if formula_k_imp_res else None,   # k imp (col N)
                    formula_k_bias_res[0] if formula_k_bias_res else None, # k bias (col O)
                    tea_tes_comparision_res[0] if tea_tes_comparision_res else None,  # TE% (col P)
                    '={0}'.format(formula_drc),                # Drc% (col Q)
                    len(series),                      # records
                    workstation_description,          # workstation description
                ]
                worksheet.append(row_data)

                # blue color for cva
                if cva is not None and cva > self.get_imp(cvw):
                    cell = worksheet.cell(row=row_num, column=7)
                    cell.fill = PatternFill(
                        start_color='FF0000FF',
                        end_color='FF0000FF',
                        fill_type='solid',
                    )

                # Apply colors using helper method
                self._apply_fill_color(worksheet, row_num, 14, formula_k_imp_res)
                self._apply_fill_color(worksheet, row_num, 15, formula_k_bias_res)
                self._apply_fill_color(worksheet, row_num, 16, tea_tes_comparision_res)

                row_num += 1

        # set headers width
        for i, width in enumerate(column_widths):
            worksheet.column_dimensions[get_column_letter(i + 1)].width = width

        self.save_and_launch(workbook)

    # ------------------------------------------------------------------ #
    #  Excel formula helpers                                             #
    # ------------------------------------------------------------------ #

    def get_excel_column_letter(self, col_idx):
        """Return Excel column letter for a zero-based index."""
        return get_column_letter(col_idx + 1)

    def get_formula_imp(self, row):
        """Imp% formula."""
        return "ROUND((H{0} * 0.5), 2)".format(row)

    def get_formula_bias(self, row):
        """Bias% formula."""
        return "ROUND(SQRT(POWER(H{0}, 2) + POWER(I{0}, 2)) * 0.25, 2)".format(row)

    def get_formula_eta(self, row):
        """TEa% formula."""
        return "ROUND(({0} * J{1}) + K{1}, 2)".format(self.get_zscore(), row)  # type: ignore

    def get_formula_cvt(self, row):
        """CVt formula."""
        return "ROUND(SQRT(POWER(G{0}, 2) + POWER(H{0}, 2)), 2)".format(row)

    def get_formula_k_imp(self, cva, cvw, row):
        """
        Return formula and color for k imp.

        Color code:
            green:  0.25 ≤ k ≤ 0.50
            yellow: 0.50 ≤ k ≤ 0.75
            red:    k > 0.75
        """
        try:
            k = round((cva / cvw), 2)

            if 0.25 <= k <= 0.50:
                c = "green"
            elif 0.50 <= k <= 0.75:
                c = "yellow"
            elif k > 0.75:
                c = "red"
            else:
                c = "green"

            f = "ROUND(G{0} / H{0}, 2)".format(row)
            return f, c

        except (ZeroDivisionError, ValueError) as e:
            return None

    def get_formula_k_bias(self, avg, target, cvw, cva, row):
        """
        Return bias k (0.125, 0.25, 0.375) as (formula, color).

        Color code:
            green:  0.125 ≤ k ≤ 0.25
            yellow: 0.25  ≤ k ≤ 0.375
            red:    k > 0.375
        """
        try:
            k = round(
                self.get_bias(avg, target) / self.get_cvt(cva, cvw),  # type: ignore
                2,
            )

            if 0.125 <= k <= 0.25:
                c = "green"
            elif 0.25 <= k <= 0.375:
                c = "yellow"
            elif k > 0.375:
                c = "red"
            else:
                c = "green"

            f = (
                "ROUND((((F{0} - E{0}) / E{0}) * 100) / "
                "SQRT(POWER(H{0}, 2) + POWER(I{0}, 2)), 2)"
            ).format(row)

            return f, c

        except ZeroDivisionError:
            return None, None

    def get_formula_drc(self, row):
        """Calcola la differenza critica (Critical Difference)"""
        f = (
            "ROUND(ROUND(SQRT(POWER(G{0}, 2) + POWER(H{0}, 2)) * 2.77, 2) "
            "* F{0} / 100, 2)"
        ).format(row)
        return f

    # ------------------------------------------------------------------ #
    #  Local color conversion (for TE% cells)                            #
    # ------------------------------------------------------------------ #

    def _convert_color(self, color_name):
        """Map color names to ARGB codes for openpyxl."""
        color_map = {
            "red": "FFFF0000",
            "yellow": "FFFFFF00",
            "blue": "FF0000FF",
            "green": "FF00FF00",
            "teal": "FF008080",
        }
        return color_map.get(color_name.lower(), "FFFFFFFF")  # Default white

    def _apply_fill_color(self, worksheet, row, column, result_tuple):
        """
        Apply fill color to a cell based on a result tuple (value, color_name).

        Args:
            worksheet: openpyxl worksheet
            row: row number (1-based)
            column: column number (1-based)
            result_tuple: tuple like (value, 'red') or None
        """
        if result_tuple and len(result_tuple) > 1 and result_tuple[1]:
            cell = worksheet.cell(row=row, column=column)
            fill_color = self._convert_color(result_tuple[1])
            cell.fill = PatternFill(
                start_color=fill_color,
                end_color=fill_color,
                fill_type='solid',
            )


def main():
    foo = Exporter()
    print(foo)
    input('end')


if __name__ == "__main__":
    main()
