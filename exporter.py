# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""Sheets out of the data, for the people who ask for them on paper.

One sheet per question, written with openpyxl and opened straight away in
whatever the system uses for spreadsheets. Nothing here computes anything of
its own: the statistics come from the engine, the rules from the Westgard
module, so a number in a sheet and the same number on the screen cannot
disagree.
"""

import datetime
import os
import tempfile

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

#: The colours a cell is filled with, by how far the result is from target.
WARNING = PatternFill("solid", fgColor="FFE8A1")
VIOLATION = PatternFill("solid", fgColor="F5B7B1")
HEADING = PatternFill("solid", fgColor="D6DBDF")


class Exporter:
    """Sheets out of the data: given the engine, it asks it what it needs."""

    def __init__(self, engine):
        #: The engine, for the database, the statistics and the rules.
        self.engine = engine

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    # ----------------------------------------------------------- the sheets

    def get_day(self, day):
        """Every control run on one day, with the series each one belongs to.

        The question asked at the end of a morning: what was run, what came
        out, and is any of it out of control. Each line is a result, and the
        statistics beside it are those of its series up to that moment - not
        of the series as it stands now, which would be reading today's run
        against tomorrow's evidence.

        @param name: day
        @return: path of the file written
        @rtype: string
        """
        sql = """SELECT r.result_id, r.result, r.received, r.batch_id,
                        t.description AS analyte,
                        s.description AS sample,
                        c.description AS category,
                        u.description AS unit,
                        m.description AS method,
                        w.description AS workstation, w.serial,
                        b.lot_number, b.description AS level, b.target, b.sd,
                        ctl.description AS control,
                        sup.description AS supplier,
                        usr.last_name AS entered_by
                   FROM results r
                   JOIN batches b ON b.batch_id = r.batch_id
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                   JOIN methods m ON m.method_id = tm.method_id
                   LEFT JOIN categories c ON c.category_id = tm.category_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                   JOIN controls ctl ON ctl.control_id = b.control_id
                   JOIN suppliers sup ON sup.supplier_id = ctl.supplier_id
                   LEFT JOIN users usr ON usr.user_id = r.created_by
                  WHERE DATE(r.received) = ? AND r.status = 1
               ORDER BY c.description, t.description, w.description, b.rank"""
        rows = self.engine.db.read(True, sql, (day.isoformat(),))

        headings = ("Category", "Analyte", "Sample", "Method", "Workstation",
                    "Serial", "Control", "Supplier", "Lot", "Level", "Unit",
                    "Target", "SD", "Result", "z", "Mean", "sd", "CV%",
                    "Bias%", "U%", "Westgard", "N", "Time", "Entered by")

        book, sheet = self.get_workbook("QC {0}".format(self.engine.format_date(day)))
        self.set_headings(sheet, headings)

        for number, row in enumerate(rows, start=2):
            series = self.engine.get_series(row["batch_id"],
                                            self.engine.get_observations(),
                                            row["result_id"])
            mean = self.engine.qc.get_mean(series)
            cv = self.engine.qc.get_cv(series)
            bias = self.engine.qc.get_bias(mean, row["target"])
            z = self.get_z(row["result"], row["target"], row["sd"])

            values = (row["category"], row["analyte"], row["sample"], row["method"],
                      row["workstation"], row["serial"], row["control"],
                      row["supplier"], row["lot_number"], row["level"], row["unit"],
                      row["target"], row["sd"], row["result"], z, mean,
                      self.engine.qc.get_sd(series), cv, bias,
                      self.engine.qc.get_uncertainty(cv, bias),
                      self.get_rule(row, series), len(series),
                      row["received"].strftime("%H:%M"), row["entered_by"])

            for column, value in enumerate(values, start=1):
                cell = sheet.cell(row=number, column=column, value=value)
                if abs(z) >= 3:
                    cell.fill = VIOLATION
                elif abs(z) >= 2:
                    cell.fill = WARNING

        self.set_widths(sheet, headings)

        return self.save(book, "qc_{0}".format(day.isoformat()))

    def get_rule(self, row, series):
        """The rule read on the series this result closes, or NED."""
        if len(series) < self.engine.get_observations():
            found = "NED"
        else:
            found = self.engine.westgards.get_rule(row["target"], row["sd"],
                                                   series)
        return found

    def get_z(self, result, target, sd):
        """How many standard deviations a result sits from its target."""
        found = 0.0
        if sd != 0:
            found = round((result - target) / sd, 2)

        return found

    def get_notes(self, since):
        """Every note of the period: the log of non conformities, as a sheet.

        What it is asked for is the year rather than the morning - how often
        a calibration was repeated, on which bench, on which analyte - so it
        carries the action as its own column, which is what makes it
        countable in a pivot table by whoever wants one.

        @param name: since
        @return: path of the file written
        @rtype: string
        """
        sql = """SELECT n.modified, a.code, a.description AS action,
                        n.description AS note,
                        t.description AS analyte, s.description AS matrix,
                        w.description AS bench, b.lot_number,
                        b.description AS level, r.result, b.target, b.sd,
                        r.received, u.last_name AS by_whom
                   FROM notes n
                   JOIN actions a ON a.action_id = n.action_id
                   JOIN results r ON r.result_id = n.result_id
                   JOIN batches b ON b.batch_id = r.batch_id
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                   LEFT JOIN users u ON u.user_id = n.created_by
                  WHERE n.status = 1 AND (? IS NULL OR r.received >= ?)
               ORDER BY r.received DESC"""
        rows = self.engine.db.read(True, sql, (since, since))

        headings = ("Date", "Code", "Action", "Note", "Analyte", "Matrix",
                    "Bench", "Lot", "Level", "Result", "Target", "z", "By")

        book, sheet = self.get_workbook("Notes")
        self.set_headings(sheet, headings)

        for number, row in enumerate(rows, start=2):
            values = (self.engine.format_date(row["modified"]), row["code"],
                      row["action"], row["note"], row["analyte"], row["matrix"],
                      row["bench"], row["lot_number"], row["level"],
                      row["result"], row["target"],
                      self.get_z(row["result"], row["target"], row["sd"]),
                      row["by_whom"])
            for column, value in enumerate(values, start=1):
                sheet.cell(row=number, column=column, value=value)

        self.set_widths(sheet, headings)

        return self.save(book, "notes")

    def get_counts(self, since):
        """How much control was run, per analyte and per bench.

        The sheet the laboratory is asked for once a year, by whoever counts
        what was done: how many results per method, over how many days, with
        how many notes and how many results out of limits.

        @param name: since
        @return: path of the file written
        @rtype: string
        """
        sql = """SELECT t.description AS analyte, s.description AS matrix,
                        w.description AS bench, c.description AS panel,
                        COUNT(r.result_id) AS results,
                        COUNT(DISTINCT DATE(r.received)) AS days,
                        MIN(DATE(r.received)) AS first_day,
                        MAX(DATE(r.received)) AS last_day,
                        SUM(CASE WHEN ABS(r.result - b.target) >= 3 * b.sd
                                 THEN 1 ELSE 0 END) AS out_of_limits,
                        (SELECT COUNT(*) FROM notes n
                           JOIN results nr ON nr.result_id = n.result_id
                           JOIN batches nb ON nb.batch_id = nr.batch_id
                          WHERE nb.test_method_id = tm.test_method_id
                            AND nb.workstation_id = b.workstation_id
                            AND n.status = 1) AS notes
                   FROM results r
                   JOIN batches b ON b.batch_id = r.batch_id
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   LEFT JOIN categories c ON c.category_id = tm.category_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE r.status = 1 AND (? IS NULL OR r.received >= ?)
               GROUP BY tm.test_method_id, b.workstation_id
               ORDER BY c.description, t.description"""
        rows = self.engine.db.read(True, sql, (since, since))

        headings = ("Panel", "Analyte", "Matrix", "Bench", "Results", "Days",
                    "First", "Last", "Beyond 3 SD", "Notes")

        book, sheet = self.get_workbook("Counts")
        self.set_headings(sheet, headings)

        for number, row in enumerate(rows, start=2):
            values = (row["panel"], row["analyte"], row["matrix"], row["bench"],
                      row["results"], row["days"], row["first_day"],
                      row["last_day"], row["out_of_limits"], row["notes"])
            for column, value in enumerate(values, start=1):
                sheet.cell(row=number, column=column, value=value)

        self.set_widths(sheet, headings)

        return self.save(book, "counts")

    def get_goals(self):
        """The analytical goals of every method, as they stand.

        Asked for when somebody wants to see the whole table of what the
        laboratory holds itself to, or to check it against a source.

        @return: path of the file written
        @rtype: string
        """
        sql = """SELECT t.description AS analyte, s.description AS matrix,
                        u.description AS unit, m.description AS method,
                        c.description AS panel, tm.code,
                        tm.cvw, tm.cvb, tm.imp, tm.bias, tm.teap005, tm.teap001,
                        tm.is_mandatory, tm.status
                   FROM test_methods tm
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                   JOIN methods m ON m.method_id = tm.method_id
                   LEFT JOIN categories c ON c.category_id = tm.category_id
               ORDER BY c.description, t.description"""
        rows = self.engine.db.read(True, sql, ())

        headings = ("Panel", "Analyte", "Matrix", "Unit", "Method", "Code",
                    "CVi%", "CVg%", "Imprecision%", "Bias%", "TEa% 95",
                    "TEa% 99", "Every day", "In use")

        book, sheet = self.get_workbook("Analytical goals")
        self.set_headings(sheet, headings)

        for number, row in enumerate(rows, start=2):
            values = (row["panel"], row["analyte"], row["matrix"], row["unit"],
                      row["method"], row["code"], row["cvw"], row["cvb"],
                      row["imp"], row["bias"], row["teap005"], row["teap001"],
                      row["is_mandatory"], row["status"])
            for column, value in enumerate(values, start=1):
                sheet.cell(row=number, column=column, value=value)

        self.set_widths(sheet, headings)

        return self.save(book, "analytical_goals")

    # ------------------------------------------------------- the mechanics

    def get_workbook(self, title):
        """A workbook with one sheet, named.

        @param name: title
        @return: book, sheet
        @rtype: tuple
        """
        book = Workbook()
        sheet = book.active
        # Excel refuses a sheet name longer than this, or holding / \ ? * [ ]
        sheet.title = title[:31].replace("/", "-")

        return (book, sheet)

    def set_headings(self, sheet, headings):
        """The first row: the names of the columns, in bold, and frozen."""
        for column, heading in enumerate(headings, start=1):
            cell = sheet.cell(row=1, column=column, value=heading)
            cell.font = Font(bold=True)
            cell.fill = HEADING
            cell.alignment = Alignment(horizontal="center")

        sheet.freeze_panes = "A2"

    def set_widths(self, sheet, headings):
        """Columns as wide as what is in them, up to a point."""
        for column, heading in enumerate(headings, start=1):
            longest = len(str(heading))
            for cell in sheet[get_column_letter(column)]:
                if cell.value is not None:
                    longest = max(longest, len(str(cell.value)))
            sheet.column_dimensions[get_column_letter(column)].width = min(longest + 2,
                                                                           34)

    def save(self, book, name):
        """Write the workbook where the system keeps temporary files, and open it.

        A sheet asked for on a morning is looked at and forgotten: it is
        given a name that says what it is and where it lands, and whoever
        wants to keep it saves it themselves, wherever they keep such things.

        @param name: book, name
        @return: path of the file written
        @rtype: string
        """
        path = os.path.join(tempfile.gettempdir(),
                            "{0}_{1}.xlsx".format(name,
                                                  datetime.datetime.now().strftime("%H%M%S")))
        book.save(path)
        self.engine.open_file(path)

        return path
