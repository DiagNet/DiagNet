import json

from django.db.models import Count, Q
from django.utils import timezone
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

from networktests.models import TestResult
from testgroups.models import TestGroup

W, H = A4

# ── Brand colours ────────────────────────────────────────────────────────────
BLUE = colors.HexColor("#00267F")
ORANGE = colors.HexColor("#c2410c")
GREEN = colors.HexColor("#16a34a")
RED = colors.HexColor("#dc2626")
LIGHT_GREY = colors.HexColor("#f1f5f9")
MID_GREY = colors.HexColor("#94a3b8")
DARK_GREY = colors.HexColor("#334155")


def _truncate(text: str, max_width_pt: float, font: str, size: int) -> str:
    """Truncate *text* so it fits within *max_width_pt* points."""
    if not text:
        return ""
    if stringWidth(text, font, size) <= max_width_pt:
        return text
    while text and stringWidth(text + "…", font, size) > max_width_pt:
        text = text[:-1]
    return text + "…"


class PDFReport:
    # ── Layout ────────────────────────────────────────────────────────────────
    ML = 48  # margin left
    MR = W - 48  # margin right
    CW = MR - ML  # content width  ≈ 499 pt on A4
    MB = 55  # bottom margin (space for footer)

    # Column x-positions for the logs table
    _COL_TS = ML  # timestamp   (~100 pt)
    _COL_TC = ML + 105  # testcase    (~130 pt)
    _COL_RES = ML + 238  # result      (~52 pt)
    _COL_MSG = ML + 293  # message     (remaining ≈ 203 pt)

    # Column x-positions for group summary table
    _COL_GRP = ML  # group name  (~195 pt)
    _COL_PASS = ML + 200  # pass
    _COL_FAIL = ML + 270  # fail
    _COL_TOTAL = ML + 335  # total

    def __init__(self, buffer, group=None):
        self.buffer = buffer
        self.pdf = canvas.Canvas(self.buffer, pagesize=A4)
        self.now = timezone.now()
        self.group = group
        self._page = 0

    # ── Public entry point ────────────────────────────────────────────────────
    def generate(self):
        self.fetch_data()
        self._cover_page()
        self._draw_charts()
        self._draw_group_summary()
        self._draw_recent_logs()
        self.pdf.save()
        return self.buffer

    # ── Data ──────────────────────────────────────────────────────────────────
    def fetch_data(self):
        results_qs = TestResult.objects.select_related("test_case").order_by(
            "-started_at"
        )
        if self.group:
            tc_ids = self.group.testcases.values_list("pk", flat=True)
            results_qs = results_qs.filter(test_case_id__in=tc_ids)

        # Only failed results in the log section — keeps the page readable
        self.failed_results = list(results_qs.filter(result=False)[:40])
        self.pass_results = list(results_qs.filter(result=True)[:10])

        groups_qs = TestGroup.objects.all()
        if self.group:
            groups_qs = groups_qs.filter(pk=self.group.pk)

        groups_with_stats = (
            groups_qs.annotate(
                total_count=Count("testcases__results"),
                pass_count=Count(
                    "testcases__results",
                    filter=Q(testcases__results__result=True),
                ),
            )
            .filter(total_count__gt=0)
            .order_by("name")
        )

        labels = [g.name for g in groups_with_stats]
        passes = [g.pass_count for g in groups_with_stats]
        fails = [(g.total_count - g.pass_count) for g in groups_with_stats]

        self.group_chart_chunks = [
            (labels[i : i + 5], passes[i : i + 5], fails[i : i + 5])
            for i in range(0, len(labels), 5)
        ]

        self.total_pass = sum(passes)
        self.total_fail = sum(fails)
        self.total_tests = self.total_pass + self.total_fail
        self.group_labels = labels
        self.group_passes = passes
        self.group_fails = fails

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _new_page(self, title: str = ""):
        self._page += 1
        self.pdf.showPage()
        self._draw_footer()
        if title:
            self._section_header(title)

    def _start_page(self, title: str = ""):
        """Mark the start of a fresh page (first page after showPage already called)."""
        self._page += 1
        self._draw_footer()
        if title:
            self._section_header(title)

    def _draw_footer(self):
        y = 30
        self.pdf.setFont("Helvetica", 8)
        self.pdf.setFillColor(MID_GREY)
        label = "DiagNet Automated Network Test Report"
        if self.group:
            label += f" — {self.group.name}"
        self.pdf.drawString(self.ML, y, label)
        self.pdf.drawRightString(
            self.MR, y, f"Page {self._page}  ·  {self.now.strftime('%Y-%m-%d %H:%M')}"
        )
        self.pdf.setStrokeColor(LIGHT_GREY)
        self.pdf.setLineWidth(0.5)
        self.pdf.line(self.ML, y + 10, self.MR, y + 10)
        self.pdf.setFillColor(colors.black)

    def _section_header(self, title: str, y: float = None):
        if y is None:
            y = H - 58
        # Accent bar
        self.pdf.setFillColor(BLUE)
        self.pdf.rect(self.ML, y - 4, 4, 26, fill=True, stroke=False)
        self.pdf.setFont("Helvetica-Bold", 18)
        self.pdf.setFillColor(DARK_GREY)
        self.pdf.drawString(self.ML + 12, y, title)
        self.pdf.setFillColor(colors.black)

    def _h_rule(self, y: float, color=None):
        self.pdf.setStrokeColor(color or LIGHT_GREY)
        self.pdf.setLineWidth(0.5)
        self.pdf.line(self.ML, y, self.MR, y)
        self.pdf.setStrokeColor(colors.black)
        self.pdf.setLineWidth(1)

    # ── Cover page ────────────────────────────────────────────────────────────
    def _cover_page(self):
        self._page += 1
        pdf = self.pdf

        # Top accent band
        pdf.setFillColor(BLUE)
        pdf.rect(0, H - 110, W, 110, fill=True, stroke=False)

        # Title
        pdf.setFillColor(colors.white)
        pdf.setFont("Helvetica-Bold", 28)
        title = "DiagNet Test Report"
        if self.group:
            title = f"DiagNet — {self.group.name}"
        pdf.drawString(self.ML, H - 60, title)

        pdf.setFont("Helvetica", 13)
        pdf.setFillColor(colors.HexColor("#bfdbfe"))
        subtitle = "Automated Network Infrastructure Test Summary"
        if self.group:
            subtitle = f"Report for test group: {self.group.name}"
        pdf.drawString(self.ML, H - 84, subtitle)

        # Meta line
        pdf.setFillColor(DARK_GREY)
        pdf.setFont("Helvetica", 11)
        pdf.drawString(
            self.ML,
            H - 130,
            f"Generated:  {self.now.strftime('%A, %d %B %Y  at  %H:%M')}",
        )

        # Overview stat boxes
        stats = [
            ("Total Runs", str(self.total_tests), DARK_GREY),
            ("Passed", str(self.total_pass), GREEN),
            ("Failed", str(self.total_fail), RED),
            ("Test Groups", str(len(self.group_labels)), BLUE),
        ]
        box_w = 110
        box_h = 70
        box_y = H - 240
        box_gap = 14
        total_boxes_w = len(stats) * box_w + (len(stats) - 1) * box_gap
        box_start_x = self.ML + (self.CW - total_boxes_w) / 2

        for i, (label, value, col) in enumerate(stats):
            bx = box_start_x + i * (box_w + box_gap)
            # Shadow
            pdf.setFillColor(colors.HexColor("#e2e8f0"))
            pdf.roundRect(bx + 2, box_y - 2, box_w, box_h, 6, fill=True, stroke=False)
            # Box
            pdf.setFillColor(colors.white)
            pdf.roundRect(bx, box_y, box_w, box_h, 6, fill=True, stroke=False)
            # Top colour strip
            pdf.setFillColor(col)
            pdf.roundRect(bx, box_y + box_h - 6, box_w, 6, 3, fill=True, stroke=False)
            # Value
            pdf.setFont("Helvetica-Bold", 26)
            pdf.setFillColor(col)
            pdf.drawCentredString(bx + box_w / 2, box_y + 22, value)
            # Label
            pdf.setFont("Helvetica", 9)
            pdf.setFillColor(MID_GREY)
            pdf.drawCentredString(bx + box_w / 2, box_y + 10, label.upper())

        # Pass-rate bar
        if self.total_tests > 0:
            bar_y = box_y - 48
            bar_h = 14
            bar_w = self.CW

            pdf.setFillColor(colors.HexColor("#f1f5f9"))
            pdf.roundRect(
                self.ML, bar_y, bar_w, bar_h, bar_h / 2, fill=True, stroke=False
            )

            pass_w = bar_w * self.total_pass / self.total_tests
            if pass_w > 0:
                pdf.setFillColor(GREEN)
                pdf.roundRect(
                    self.ML, bar_y, pass_w, bar_h, bar_h / 2, fill=True, stroke=False
                )

            rate = round(100 * self.total_pass / self.total_tests, 1)
            pdf.setFont("Helvetica-Bold", 9)
            pdf.setFillColor(DARK_GREY)
            pdf.drawCentredString(self.ML + bar_w / 2, bar_y + 2, f"Pass rate: {rate}%")

        self._draw_footer()
        self._h_rule(self.MB + 12)

    # ── Charts ────────────────────────────────────────────────────────────────
    def _draw_charts(self):
        for idx, (labels, passes, fails) in enumerate(self.group_chart_chunks, start=1):
            self.pdf.showPage()
            self._start_page(
                f"Pass / Fail by Test Group  (block {idx} of {len(self.group_chart_chunks)})"
            )

            drawing = Drawing(self.CW, 290)
            bc = VerticalBarChart()
            bc.x = 45
            bc.y = 55
            bc.width = self.CW - 90
            bc.height = 210
            bc.data = [passes, fails]
            bc.categoryAxis.categoryNames = labels
            bc.categoryAxis.labels.fontSize = 9
            bc.valueAxis.labels.fontSize = 9
            bc.bars[0].fillColor = GREEN
            bc.bars[1].fillColor = RED
            bc.groupSpacing = 14
            bc.barSpacing = 3
            bc.valueAxis.valueMin = 0
            max_val = max(passes + fails) if (passes + fails) else 1
            bc.valueAxis.valueMax = max_val + 1
            bc.valueAxis.valueStep = max(1, max_val // 5 or 1)

            drawing.add(bc)
            renderPDF.draw(drawing, self.pdf, self.ML, H - 390)

            # Legend
            leg_y = H - 405
            self.pdf.setFont("Helvetica", 10)
            self.pdf.setFillColor(GREEN)
            self.pdf.rect(self.ML, leg_y, 10, 10, fill=True, stroke=False)
            self.pdf.setFillColor(DARK_GREY)
            self.pdf.drawString(self.ML + 14, leg_y + 1, "Pass")
            self.pdf.setFillColor(RED)
            self.pdf.rect(self.ML + 70, leg_y, 10, 10, fill=True, stroke=False)
            self.pdf.setFillColor(DARK_GREY)
            self.pdf.drawString(self.ML + 84, leg_y + 1, "Fail")
            self.pdf.setFillColor(colors.black)

    # ── Group summary ─────────────────────────────────────────────────────────
    def _draw_group_summary(self):
        self.pdf.showPage()
        self._start_page("Group Summary")

        y = H - 90
        lh = 22
        header_h = 26

        def _table_header(y_):
            self.pdf.setFillColor(LIGHT_GREY)
            self.pdf.rect(self.ML, y_ - 6, self.CW, header_h, fill=True, stroke=False)
            self.pdf.setFont("Helvetica-Bold", 10)
            self.pdf.setFillColor(DARK_GREY)
            self.pdf.drawString(self._COL_GRP + 4, y_, "Test Group")
            self.pdf.drawRightString(self._COL_PASS + 36, y_, "Pass")
            self.pdf.drawRightString(self._COL_FAIL + 30, y_, "Fail")
            self.pdf.drawRightString(self._COL_TOTAL + 48, y_, "Total")
            self._h_rule(y_ - 7)

        _table_header(y)
        y -= lh + 4
        self.pdf.setFont("Helvetica", 11)

        for row_i, (name, p, f) in enumerate(
            zip(self.group_labels, self.group_passes, self.group_fails)
        ):
            if y < self.MB + 20:
                self.pdf.showPage()
                self._start_page("Group Summary (continued)")
                y = H - 90
                _table_header(y)
                y -= lh + 4
                self.pdf.setFont("Helvetica", 11)

            # Alternating row bg
            if row_i % 2 == 0:
                self.pdf.setFillColor(colors.HexColor("#f8fafc"))
                self.pdf.rect(self.ML, y - 5, self.CW, lh, fill=True, stroke=False)

            max_name_w = self._COL_PASS - self._COL_GRP - 8
            self.pdf.setFillColor(DARK_GREY)
            self.pdf.setFont("Helvetica", 11)
            self.pdf.drawString(
                self._COL_GRP + 4, y, _truncate(name, max_name_w, "Helvetica", 11)
            )
            self.pdf.setFillColor(GREEN)
            self.pdf.drawRightString(self._COL_PASS + 36, y, str(p))
            self.pdf.setFillColor(RED)
            self.pdf.drawRightString(self._COL_FAIL + 30, y, str(f))
            self.pdf.setFillColor(DARK_GREY)
            self.pdf.drawRightString(self._COL_TOTAL + 48, y, str(p + f))
            y -= lh

        # Total row
        self._h_rule(y + 2)
        y -= 8
        self.pdf.setFont("Helvetica-Bold", 11)
        self.pdf.setFillColor(DARK_GREY)
        self.pdf.drawString(self._COL_GRP + 4, y, "Total")
        self.pdf.setFillColor(GREEN)
        self.pdf.drawRightString(self._COL_PASS + 36, y, str(self.total_pass))
        self.pdf.setFillColor(RED)
        self.pdf.drawRightString(self._COL_FAIL + 30, y, str(self.total_fail))
        self.pdf.setFillColor(DARK_GREY)
        self.pdf.drawRightString(self._COL_TOTAL + 48, y, str(self.total_tests))

    # ── Recent logs ───────────────────────────────────────────────────────────
    def _draw_recent_logs(self):
        self.pdf.showPage()
        self._start_page("Failed Test Runs — Error Details")

        # Available widths per column (used for truncation)
        _w_ts = self._COL_TC - self._COL_TS - 6  # ~99 pt
        _w_tc = self._COL_RES - self._COL_TC - 6  # ~127 pt
        _w_res = self._COL_MSG - self._COL_RES - 4  # ~49 pt  (just PASS/FAIL)
        _w_msg = self.MR - self._COL_MSG - 4  # ~203 pt

        y = H - 90
        lh = 18
        header_h = 24

        def _table_header(y_):
            self.pdf.setFillColor(LIGHT_GREY)
            self.pdf.rect(self.ML, y_ - 6, self.CW, header_h, fill=True, stroke=False)
            self.pdf.setFont("Helvetica-Bold", 9)
            self.pdf.setFillColor(DARK_GREY)
            self.pdf.drawString(self._COL_TS + 2, y_, "Timestamp")
            self.pdf.drawString(self._COL_TC + 2, y_, "Test Case")
            self.pdf.drawString(self._COL_RES + 2, y_, "Result")
            self.pdf.drawString(self._COL_MSG + 2, y_, "Error Message")
            self._h_rule(y_ - 7)

        _table_header(y)
        y -= lh + 4

        def _render_rows(results, is_fail: bool):
            nonlocal y
            font = "Helvetica"
            self.pdf.setFont(font, 9)

            for row_i, r in enumerate(results):
                if y < self.MB + 14:
                    self.pdf.showPage()
                    section = (
                        "Failed Test Runs (continued)"
                        if is_fail
                        else "Passed Test Runs"
                    )
                    self._start_page(section)
                    y = H - 90
                    _table_header(y)
                    y -= lh + 4
                    self.pdf.setFont(font, 9)

                if row_i % 2 == 0:
                    self.pdf.setFillColor(colors.HexColor("#f8fafc"))
                    self.pdf.rect(self.ML, y - 4, self.CW, lh, fill=True, stroke=False)

                ts = r.started_at.strftime("%Y-%m-%d %H:%M")
                tc = _truncate(r.test_case.label or "", _w_tc, font, 9)
                msg = _truncate(self._extract_message(r.log, is_fail), _w_msg, font, 9)

                self.pdf.setFillColor(DARK_GREY)
                self.pdf.drawString(self._COL_TS + 2, y, ts)
                self.pdf.drawString(self._COL_TC + 2, y, tc)

                if r.result:
                    self.pdf.setFillColor(GREEN)
                    self.pdf.drawString(self._COL_RES + 2, y, "PASS")
                else:
                    self.pdf.setFillColor(RED)
                    self.pdf.drawString(self._COL_RES + 2, y, "FAIL")

                self.pdf.setFillColor(DARK_GREY)
                self.pdf.drawString(self._COL_MSG + 2, y, msg)
                y -= lh

        _render_rows(self.failed_results, is_fail=True)

        # Separator before the passed section
        if self.pass_results:
            if y < self.MB + 40:
                self.pdf.showPage()
                self._start_page("Passed Test Runs — Sample")
                y = H - 90
            else:
                y -= 14
                self._h_rule(y + 8)
                y -= 6

            # Mini sub-header for passed section
            self.pdf.setFillColor(colors.HexColor("#dcfce7"))
            self.pdf.rect(self.ML, y - 6, self.CW, header_h, fill=True, stroke=False)
            self.pdf.setFont("Helvetica-Bold", 9)
            self.pdf.setFillColor(GREEN)
            self.pdf.drawString(
                self.ML + 4, y, f"Passed Runs — last {len(self.pass_results)} shown"
            )
            self._h_rule(y - 7, color=GREEN)
            y -= lh + 4

            _render_rows(self.pass_results, is_fail=False)

    # ── Helpers ───────────────────────────────────────────────────────────────
    @staticmethod
    def _extract_message(log, prefer_fail: bool = True) -> str:
        if not log:
            return "No log data."
        if isinstance(log, str):
            try:
                log = json.loads(log)
            except (json.JSONDecodeError, TypeError):
                return log[:120]
        if isinstance(log, dict) and "tests" in log:
            # Return first FAIL message, or first PASS message as fallback
            first_pass = None
            for data in log["tests"].values():
                msg = data.get("message") or ""
                if data.get("status") == "FAIL":
                    return msg
                if first_pass is None:
                    first_pass = msg
            return first_pass or "All modules passed."
        return str(log)[:120]
