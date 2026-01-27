import json

from django.db.models import Count, Q
from django.utils import timezone
from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from networktests.models import TestResult
from testgroups.models import TestGroup

W, H = A4


class PDFReport:
    # Layout Constants
    MARGIN_LEFT = 50
    PAGE_WIDTH = W
    PAGE_HEIGHT = H
    MARGIN_RIGHT = PAGE_WIDTH - MARGIN_LEFT
    CONTENT_WIDTH = MARGIN_RIGHT - MARGIN_LEFT

    def __init__(self, buffer):
        self.buffer = buffer
        self.pdf = canvas.Canvas(self.buffer, pagesize=A4)
        self.now = timezone.now()

    def generate(self):
        self.fetch_data()
        self.draw_header()
        self.draw_overview()
        self.draw_group_charts()
        self.draw_group_summary()
        self.draw_recent_logs()
        self.pdf.save()
        return self.buffer

    def fetch_data(self):
        self.results = TestResult.objects.select_related("test_case").order_by(
            "-started_at"
        )[:50]

        groups_with_stats = (
            TestGroup.objects.annotate(
                total_count=Count("testcases__results"),
                pass_count=Count(
                    "testcases__results", filter=Q(testcases__results__result=True)
                ),
            )
            .filter(total_count__gt=0)
            .order_by("name")
        )

        group_labels_all = [g.name for g in groups_with_stats]
        group_passes_all = [g.pass_count for g in groups_with_stats]
        group_fails_all = [(g.total_count - g.pass_count) for g in groups_with_stats]

        self.group_chart_chunks = [
            (
                group_labels_all[i : i + 5],
                group_passes_all[i : i + 5],
                group_fails_all[i : i + 5],
            )
            for i in range(0, len(group_labels_all), 5)
        ]

        self.total_pass = sum(group_passes_all)
        self.total_fail = sum(group_fails_all)
        self.total_tests = self.total_pass + self.total_fail
        self.group_labels_all = group_labels_all
        self.group_passes_all = group_passes_all
        self.group_fails_all = group_fails_all

    def draw_header(self):
        y_pos = self.PAGE_HEIGHT - 90
        self.pdf.setFont("Helvetica-Bold", 30)
        self.pdf.drawString(self.MARGIN_LEFT, y_pos, "DiagNet Test Report")

        y_pos -= 35
        self.pdf.setFont("Helvetica", 16)
        self.pdf.setFillColor(colors.grey)
        self.pdf.drawString(self.MARGIN_LEFT, y_pos, "Automated Network Test Summary")

        y_pos -= 35
        self.pdf.setFillColor(colors.black)
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(
            self.MARGIN_LEFT, y_pos, f"Generated: {self.now.strftime('%Y-%m-%d %H:%M')}"
        )

    def draw_overview(self):
        y_pos = self.PAGE_HEIGHT - 210
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(self.MARGIN_LEFT, y_pos, "Overview")

        y_pos -= 30
        bullet_x = self.MARGIN_LEFT + 20
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(bullet_x, y_pos, f"• Total Test Runs: {self.total_tests}")
        y_pos -= 20
        self.pdf.drawString(bullet_x, y_pos, f"• Passed: {self.total_pass}")
        y_pos -= 20
        self.pdf.drawString(bullet_x, y_pos, f"• Failed: {self.total_fail}")
        y_pos -= 20
        self.pdf.drawString(
            bullet_x, y_pos, f"• TestGroups: {len(self.group_labels_all)}"
        )

        y_pos -= 20
        self.pdf.line(self.MARGIN_LEFT, y_pos, self.MARGIN_RIGHT, y_pos)
        self.pdf.showPage()

    def draw_group_charts(self):
        chart_y = self.PAGE_HEIGHT - 360
        legend_y = self.PAGE_HEIGHT - 390
        pass_legend_x = self.MARGIN_LEFT + 10
        fail_legend_x = self.MARGIN_LEFT + 80

        for idx, (labels, passes, fails) in enumerate(self.group_chart_chunks, start=1):
            self.pdf.setFont("Helvetica-Bold", 20)
            self.pdf.drawString(
                self.MARGIN_LEFT,
                self.PAGE_HEIGHT - 60,
                f"TestGroups – Pass/Fail (Block {idx})",
            )

            drawing = Drawing(self.CONTENT_WIDTH, 280)
            bc = VerticalBarChart()
            bc.x = 40
            bc.y = 50
            bc.width = self.CONTENT_WIDTH - 80
            bc.height = 200
            bc.data = [passes, fails]
            bc.categoryAxis.categoryNames = labels
            bc.bars[0].fillColor = colors.HexColor("#16a34a")
            bc.bars[1].fillColor = colors.HexColor("#dc2626")
            bc.groupSpacing = 12
            bc.barSpacing = 2
            bc.valueAxis.valueMin = 0
            max_val = max(passes + fails) if (passes + fails) else 1
            bc.valueAxis.valueMax = max_val + 1
            bc.valueAxis.valueStep = max(1, max_val // 4 or 1)

            drawing.add(bc)
            renderPDF.draw(drawing, self.pdf, self.MARGIN_LEFT, chart_y)

            self.pdf.setFont("Helvetica", 11)
            self.pdf.setFillColor(colors.HexColor("#16a34a"))
            self.pdf.rect(pass_legend_x, legend_y, 10, 10, fill=True)
            self.pdf.setFillColor(colors.black)
            self.pdf.drawString(pass_legend_x + 15, legend_y - 2, "Pass")
            self.pdf.setFillColor(colors.HexColor("#dc2626"))
            self.pdf.rect(fail_legend_x, legend_y, 10, 10, fill=True)
            self.pdf.setFillColor(colors.black)
            self.pdf.drawString(fail_legend_x + 15, legend_y - 2, "Fail")
            self.pdf.showPage()

    def draw_recent_logs(self):
        header_y = self.PAGE_HEIGHT - 110
        y = header_y
        col_ts = self.MARGIN_LEFT
        col_tc = self.MARGIN_LEFT + 110
        col_result = self.MARGIN_LEFT + 260
        col_msg = self.MARGIN_LEFT + 320
        line_height = 20
        bottom_margin = 70

        self.pdf.setFont("Helvetica-Bold", 20)
        self.pdf.drawString(
            self.MARGIN_LEFT, self.PAGE_HEIGHT - 60, "Recent Logs – error messages"
        )

        def draw_logs_header():
            self.pdf.setFont("Helvetica-Bold", 11)
            self.pdf.drawString(col_ts, y, "Timestamp")
            self.pdf.drawString(col_tc, y, "TestCase")
            self.pdf.drawString(col_result, y, "Result")
            self.pdf.drawString(col_msg, y, "Message")
            self.pdf.line(self.MARGIN_LEFT, y - 4, self.MARGIN_RIGHT, y - 4)

        draw_logs_header()
        y -= 25
        self.pdf.setFont("Helvetica", 10)

        for r in self.results:
            if y < bottom_margin:
                self.pdf.showPage()
                y = header_y
                draw_logs_header()
                y -= 25
                self.pdf.setFont("Helvetica", 10)

            ts = r.started_at.strftime("%Y-%m-%d %H:%M")
            tc = (r.test_case.label or "")[:24]
            raw = r.log
            msg = self.format_message_for_pdf(raw)
            max_len = 60

            self.pdf.drawString(col_ts, y, ts)
            self.pdf.drawString(col_tc, y, tc)

            if r.result:
                self.pdf.setFillColor(colors.HexColor("#16a34a"))
                self.pdf.drawString(col_result, y, "PASS")
                if msg == "Log format not recognized.":
                    if raw:
                        raw_as_string = str(raw)
                        if len(raw_as_string) > max_len:
                            msg = raw_as_string[: max_len - 3] + "..."
                        else:
                            msg = raw_as_string
            else:
                self.pdf.setFillColor(colors.HexColor("#dc2626"))
                self.pdf.drawString(col_result, y, "FAIL")
            self.pdf.setFillColor(colors.black)
            self.pdf.drawString(col_msg, y, msg)
            y -= line_height

    def draw_group_summary(self):
        y = self.PAGE_HEIGHT - 110
        col_group = self.MARGIN_LEFT
        col_pass = self.MARGIN_LEFT + 200
        col_fail = self.MARGIN_LEFT + 270
        col_total = self.MARGIN_LEFT + 330
        pass_right_align = col_pass + 40
        fail_right_align = col_fail + 30
        total_right_align = col_total + 50
        line_height = 20
        header_line_spacing = 24
        bottom_margin = 70
        page_break_y_start = self.PAGE_HEIGHT - 80

        self.pdf.setFont("Helvetica-Bold", 20)
        self.pdf.drawString(self.MARGIN_LEFT, self.PAGE_HEIGHT - 60, "Group Summary")

        def draw_summary_header():
            self.pdf.setFont("Helvetica-Bold", 12)
            self.pdf.drawString(col_group, y, "Group")
            self.pdf.drawString(col_pass, y, "Pass")
            self.pdf.drawString(col_fail, y, "Fail")
            self.pdf.drawString(col_total, y, "Total")
            self.pdf.line(self.MARGIN_LEFT, y - 4, self.MARGIN_RIGHT, y - 4)

        draw_summary_header()
        y -= header_line_spacing
        self.pdf.setFont("Helvetica", 12)

        for name, p, f in zip(
            self.group_labels_all, self.group_passes_all, self.group_fails_all
        ):
            if y < bottom_margin:
                self.pdf.showPage()
                y = page_break_y_start
                draw_summary_header()
                y -= header_line_spacing
                self.pdf.setFont("Helvetica", 12)

            self.pdf.drawString(col_group, y, name[:28])
            self.pdf.setFillColor(colors.HexColor("#16a34a"))
            self.pdf.drawRightString(pass_right_align, y, str(p))
            self.pdf.setFillColor(colors.HexColor("#dc2626"))
            self.pdf.drawRightString(fail_right_align, y, str(f))
            self.pdf.setFillColor(colors.black)
            self.pdf.drawRightString(total_right_align, y, str(p + f))
            y -= line_height
        self.pdf.showPage()

    def format_message_for_pdf(self, raw, max_len=60):
        if not raw:
            return "No log message."
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                if len(raw) > max_len:
                    return raw[: max_len - 3] + "..."
                return raw
        if isinstance(raw, dict) and "tests" in raw:
            for testname, test in raw["tests"].items():
                if test.get("status") == "FAIL":
                    message = test.get("message", "Unknown error")
                    if len(message) > max_len:
                        return message[: max_len - 3] + "..."
                    return message
            return "N/A"
        return "Log format not recognized."
