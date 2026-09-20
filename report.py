# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# project:  biovarase
# authors:  Giuseppe Costanzi (1966bc)
# licence:  GPL-3.0-or-later, see LICENSE
# -----------------------------------------------------------------------------
"""The controls of a day as a PDF: the form that is printed, signed and filed.

A sheet and a form are two different things. The sheet is for the data -
sorted, filtered, pasted somewhere else - and it is written by exporter.py.
This is the record: it does not change after it is made, it says whose
laboratory it belongs to, who produced it and when, which program and which
version made it, and it leaves a line for the signature of whoever takes
responsibility for the run.

ISO 15189 asks for records of the quality control results and for their
review; what it wants of a record is that it identify itself. The heading
and the footer here are that identification, and they are the reason this
file exists beside a perfectly good spreadsheet.
"""

import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (BaseDocTemplate, Frame, PageTemplate, Paragraph,
                                Spacer, Table, TableStyle)

#: How far a result may sit from its target before the row is coloured.
WARNING = 2
VIOLATION = 3

#: The colours, the same the windows use.
WARNING_FILL = colors.HexColor("#fdebd0")
VIOLATION_FILL = colors.HexColor("#f5b7b1")
HEADING_FILL = colors.HexColor("#d6dbdf")


class Report:
    """The quality control of one day, as a document."""

    #: The columns of the table, and how wide they are in millimetres.
    COLUMNS = (("Analyte", 38), ("Matrix", 18), ("Bench", 16), ("Lot", 24),
               ("Level", 16), ("Unit", 14), ("Target", 16), ("Result", 16),
               ("z", 12), ("Mean", 16), ("CV%", 14), ("Bias%", 14),
               ("Westgard", 18), ("N", 10), ("Time", 14))

    def __init__(self, engine):
        self.engine = engine

    def __str__(self):
        return "class: {0}".format(self.__class__.__name__)

    def get_day(self, day, path):
        """Write the form for one day, and return where it was written.

        @param name: day, path
        @return: path
        @rtype: string
        """
        self.day = day
        self.printed = datetime.datetime.now()
        self.heading = "Internal quality control"

        document = BaseDocTemplate(path, pagesize=landscape(A4),
                                   leftMargin=12 * mm, rightMargin=12 * mm,
                                   topMargin=26 * mm, bottomMargin=20 * mm,
                                   title="Quality control {0}".format(day.isoformat()),
                                   author=self.engine.log_user.get("last_name", ""))

        frame = Frame(document.leftMargin, document.bottomMargin,
                      document.width, document.height, id="body")
        document.addPageTemplates([PageTemplate(id="day", frames=[frame],
                                                onPage=self.set_page)])
        document.build(self.get_body())

        return path

    # ------------------------------------------------------------ the page

    def set_page(self, canvas, document):
        """The heading and the footer, on every page.

        Drawn on the canvas and not flowed with the text, so that a form of
        four pages identifies itself on all four: a page photocopied out of a
        folder has to say what it is by itself.
        """
        site, lab, section = self.engine.get_laboratory()
        width, height = landscape(A4)

        canvas.saveState()

        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(12 * mm, height - 14 * mm, "{0} - {1}".format(site, lab))
        canvas.setFont("Helvetica", 9)
        canvas.drawString(12 * mm, height - 19 * mm, section)

        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawRightString(width - 12 * mm, height - 14 * mm, self.heading)
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(width - 12 * mm, height - 19 * mm,
                               self.engine.format_date(self.day))

        canvas.setLineWidth(0.5)
        canvas.line(12 * mm, height - 22 * mm, width - 12 * mm, height - 22 * mm)

        # The footer says who made the record, with what, and when: a record
        # that cannot say where it came from is not a record.
        canvas.setFont("Helvetica", 7)
        canvas.drawString(12 * mm, 12 * mm,
                          "{0} {1} - printed {2} by {3}".format(
                              self.engine.app_title,
                              self.engine.get_version(),
                              self.printed.strftime("%d-%m-%Y %H:%M"),
                              self.get_who()))
        canvas.drawCentredString(width / 2.0, 12 * mm,
                                 "ddof {0}, z {1}, observations {2}".format(
                                     self.engine.qc.get_ddof(),
                                     self.engine.qc.get_zscore(),
                                     self.engine.get_observations()))
        canvas.drawRightString(width - 12 * mm, 12 * mm,
                               "page {0}".format(document.page))

        canvas.restoreState()

    def get_goals(self, path):
        """The analytical goals of every method, as a document.

        A table of reference that is read, checked against its sources and
        filed with the procedure, and never rearranged: which is what makes
        it a form and not a sheet. What is on it is what the laboratory holds
        itself to, and the heading says which laboratory and when it was
        printed.

        @param name: path
        @return: path
        @rtype: string
        """
        self.day = self.engine.get_today()
        self.printed = datetime.datetime.now()
        self.heading = "Analytical goals"

        document = BaseDocTemplate(path, pagesize=landscape(A4),
                                   leftMargin=12 * mm, rightMargin=12 * mm,
                                   topMargin=26 * mm, bottomMargin=20 * mm,
                                   title="Analytical goals",
                                   author=self.engine.log_user.get("last_name", ""))
        frame = Frame(document.leftMargin, document.bottomMargin,
                      document.width, document.height, id="body")
        document.addPageTemplates([PageTemplate(id="goals", frames=[frame],
                                                onPage=self.set_page)])
        document.build(self.get_goals_body())

        return path

    def get_goals_body(self):
        """The table of goals, and the line that says where they come from."""
        styles = getSampleStyleSheet()
        small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8)

        sql = """SELECT t.description AS analyte, s.description AS matrix,
                        u.description AS unit, m.description AS method,
                        c.description AS panel,
                        tm.cvw, tm.cvb, tm.imp, tm.bias, tm.teap005
                   FROM test_methods tm
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                   JOIN methods m ON m.method_id = tm.method_id
                   LEFT JOIN categories c ON c.category_id = tm.category_id
                  WHERE tm.status = 1
               ORDER BY c.description, t.description, s.description"""
        rows = self.engine.db.read(True, sql, ())

        columns = (("Panel", 34), ("Analyte", 42), ("Matrix", 20), ("Unit", 16),
                   ("Method", 26), ("CVi%", 16), ("CVg%", 16),
                   ("Imprecision%", 24), ("Bias%", 16), ("TEa%", 16))

        data = [[heading for heading, width in columns]]
        for row in rows:
            data.append([row["panel"], row["analyte"], row["matrix"], row["unit"],
                         row["method"], row["cvw"] or "", row["cvb"] or "",
                         row["imp"], row["bias"], row["teap005"]])

        table = Table(data, colWidths=[width * mm for heading, width in columns],
                      repeatRows=1)
        table.setStyle(TableStyle([("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7),
                                   ("BACKGROUND", (0, 0), (-1, 0), HEADING_FILL),
                                   ("FONT", (0, 1), (-1, -1), "Helvetica", 7),
                                   ("ALIGN", (5, 1), (-1, -1), "RIGHT"),
                                   ("GRID", (0, 0), (-1, -1), 0.25, colors.grey)]))

        return [table,
                Spacer(1, 6 * mm),
                Paragraph("An analyte with a biological variation of its own is"
                          " held to it: CVa = 0.5 x CVi, bias = 0.25 x"
                          " sqrt(CVi&sup2; + CVg&sup2;), TEa = k x CVa + bias,"
                          " k = {0}. A drug has none - the concentration is what"
                          " the dose made it - and is held to the state of the"
                          " art, which is the total error in the last column"
                          " with the imprecision and the bias read back out of"
                          " it.".format(self.engine.qc.get_zscore()), small)]

    def get_who(self):
        """Who produced the record."""
        return "{0} {1}".format(self.engine.log_user.get("last_name", ""),
                                self.engine.log_user.get("first_name") or "").strip()

    # ------------------------------------------------------------ the body

    def get_body(self):
        """The table, what was not run, and the line for the signature."""
        styles = getSampleStyleSheet()
        small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8)

        rows = self.get_rows()
        story = [self.get_table(rows), Spacer(1, 6 * mm)]

        missing = self.get_missing()
        if missing:
            story.append(Paragraph("<b>Not run today</b>: {0}".format(
                ", ".join(missing)), small))
            story.append(Spacer(1, 4 * mm))

        story.append(Paragraph(self.get_summary(rows), small))
        story.append(Spacer(1, 10 * mm))
        story.append(Paragraph(
            "Reviewed by ______________________________ "
            "&nbsp;&nbsp;&nbsp; Date __________________", small))

        return story

    def get_rows(self):
        """Every control of the day, with the statistics of its series."""
        sql = """SELECT r.result_id, r.result, r.received, r.batch_id,
                        t.description AS analyte, s.description AS matrix,
                        u.description AS unit, w.description AS bench,
                        b.lot_number, b.description AS level, b.target, b.sd
                   FROM results r
                   JOIN batches b ON b.batch_id = r.batch_id
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN units u ON u.unit_id = tm.unit_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE DATE(r.received) = ? AND r.status = 1
               ORDER BY w.description, t.description, b.rank"""
        rows = self.engine.db.read(True, sql, (self.day.isoformat(),))

        found = []
        for row in rows:
            series = self.engine.get_series(row["batch_id"],
                                            self.engine.get_observations(),
                                            row["result_id"])
            mean = self.engine.qc.get_mean(series)
            cv = self.engine.qc.get_cv(series)
            found.append({"analyte": row["analyte"],
                          "matrix": row["matrix"],
                          "bench": row["bench"],
                          "lot": row["lot_number"],
                          "level": row["level"],
                          "unit": row["unit"],
                          "target": row["target"],
                          "result": row["result"],
                          "z": self.get_z(row["result"], row["target"], row["sd"]),
                          "mean": mean,
                          "cv": cv,
                          "bias": self.engine.qc.get_bias(mean, row["target"]),
                          "rule": self.get_rule(row, series),
                          "n": len(series),
                          "time": row["received"].strftime("%H:%M")})

        return found

    def get_z(self, result, target, sd):
        """How many standard deviations a result sits from its target."""
        found = 0.0
        if sd != 0:
            found = round((result - target) / sd, 2)

        return found

    def get_rule(self, row, series):
        """The rule read on the series up to this result, or NED."""
        if len(series) < self.engine.get_observations():
            found = "NED"
        else:
            found = self.engine.westgards.get_westgard_violation_rule(row["target"],
                                                                      row["sd"],
                                                                      series)
        return found

    def get_table(self, rows):
        """The controls as a table, with the rows out of limits coloured."""
        data = [[heading for heading, width in self.COLUMNS]]
        style = [("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7),
                 ("BACKGROUND", (0, 0), (-1, 0), HEADING_FILL),
                 ("FONT", (0, 1), (-1, -1), "Helvetica", 7),
                 ("ALIGN", (6, 1), (13, -1), "RIGHT"),
                 ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                 ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]

        for number, row in enumerate(rows, start=1):
            data.append([row["analyte"], row["matrix"], row["bench"], row["lot"],
                         row["level"], row["unit"], row["target"], row["result"],
                         row["z"], row["mean"], row["cv"], row["bias"],
                         row["rule"], row["n"], row["time"]])

            if abs(row["z"]) >= VIOLATION:
                style.append(("BACKGROUND", (0, number), (-1, number), VIOLATION_FILL))
            elif abs(row["z"]) >= WARNING:
                style.append(("BACKGROUND", (0, number), (-1, number), WARNING_FILL))

        table = Table(data, colWidths=[width * mm for heading, width in self.COLUMNS],
                      repeatRows=1)
        table.setStyle(TableStyle(style))

        return table

    def get_missing(self):
        """The methods that had to be controlled today and were not.

        What is not on a page is as much of an answer as what is, and it is
        the one nobody notices by reading: a mandatory method with no control
        today is the line that has to be explained.

        @return: the methods, named
        @rtype: list
        """
        sql = """SELECT t.description AS analyte, s.description AS matrix,
                        w.description AS bench
                   FROM batches b
                   JOIN test_methods tm ON tm.test_method_id = b.test_method_id
                   JOIN tests t ON t.test_id = tm.test_id
                   JOIN samples s ON s.sample_id = tm.sample_id
                   JOIN workstations w ON w.workstation_id = b.workstation_id
                  WHERE b.status = 1 AND tm.status = 1 AND tm.is_mandatory = 1
                    AND NOT EXISTS (SELECT 1 FROM results r
                                     WHERE r.batch_id = b.batch_id
                                       AND DATE(r.received) = ?)
               GROUP BY tm.test_method_id, w.workstation_id
               ORDER BY t.description"""
        rows = self.engine.db.read(True, sql, (self.day.isoformat(),))

        return ["{0} ({1}) on {2}".format(row["analyte"], row["matrix"], row["bench"])
                for row in rows]

    def get_summary(self, rows):
        """One line: how many controls, and how many outside the limits."""
        warnings = len([row for row in rows if WARNING <= abs(row["z"]) < VIOLATION])
        violations = len([row for row in rows if abs(row["z"]) >= VIOLATION])

        return ("<b>{0}</b> controls, <b>{1}</b> beyond 2 SD, "
                "<b>{2}</b> beyond 3 SD.").format(len(rows), warnings, violations)
