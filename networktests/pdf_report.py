import json
import logging
from datetime import datetime

from reportlab.graphics import renderPDF
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from networktests.models import TestResult
from testgroups.models import TestGroup

logger = logging.getLogger(__name__)


W, H = A4


class PDFReport:
    def __init__(self, buffer):
        self.buffer = buffer
        self.pdf = canvas.Canvas(self.buffer, pagesize=A4)
        self.now = datetime.now()

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
        self.groups = TestGroup.objects.all().prefetch_related("testcases")

        group_labels_all: list[str] = []
        group_passes_all: list[int] = []
        group_fails_all: list[int] = []

        for g in self.groups:
            tcs = g.testcases.all()
            p = TestResult.objects.filter(test_case__in=tcs, result=True).count()
            f = TestResult.objects.filter(test_case__in=tcs, result=False).count()

            if p == 0 and f == 0:
                continue

            group_labels_all.append(g.name)
            group_passes_all.append(p)
            group_fails_all.append(f)

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
        self.pdf.setFont("Helvetica-Bold", 30)
        self.pdf.drawString(50, H - 90, "DiagNet Test Report")
        self.pdf.setFont("Helvetica", 16)
        self.pdf.setFillColor(colors.grey)
        self.pdf.drawString(50, H - 125, "Automated Network Test Summary")
        self.pdf.setFillColor(colors.black)
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(
            50, H - 160, f"Generated: {self.now.strftime('%Y-%m-%d %H:%M')}"
        )
        try:
            logo = ImageReader("static/images/diagnet_logo.png")
            self.pdf.drawImage(
                logo, W - 180, H - 170, width=130, preserveAspectRatio=True
            )
        except Exception:
            logger.debug("diagnet logo not found or could not be loaded")

    def draw_overview(self):
        self.pdf.setFont("Helvetica-Bold", 14)
        self.pdf.drawString(50, H - 210, "Overview")
        self.pdf.setFont("Helvetica", 12)
        self.pdf.drawString(70, H - 240, f"• Total Test Runs: {self.total_tests}")
        self.pdf.drawString(70, H - 260, f"• Passed: {self.total_pass}")
        self.pdf.drawString(70, H - 280, f"• Failed: {self.total_fail}")
        self.pdf.drawString(70, H - 300, f"• TestGroups: {len(self.group_labels_all)}")
        self.pdf.line(50, H - 320, W - 50, H - 320)
        self.pdf.showPage()

    def draw_group_charts(self):
        for idx, (labels, passes, fails) in enumerate(self.group_chart_chunks, start=1):
            self.pdf.setFont("Helvetica-Bold", 20)
            self.pdf.drawString(50, H - 60, f"TestGroups – Pass/Fail (Block {idx})")

            drawing = Drawing(500, 280)
            bc = VerticalBarChart()
            bc.x = 40
            bc.y = 50
            bc.width = 420
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
            renderPDF.draw(drawing, self.pdf, 50, H - 360)

            self.pdf.setFont("Helvetica", 11)
            self.pdf.setFillColor(colors.HexColor("#16a34a"))
            self.pdf.rect(60, H - 390, 10, 10, fill=True)
            self.pdf.setFillColor(colors.black)
            self.pdf.drawString(75, H - 388, "Pass")
            self.pdf.setFillColor(colors.HexColor("#dc2626"))
            self.pdf.rect(130, H - 390, 10, 10, fill=True)
            self.pdf.setFillColor(colors.black)
            self.pdf.drawString(145, H - 388, "Fail")
            self.pdf.showPage()

    def draw_recent_logs(self):
        self.pdf.setFont("Helvetica-Bold", 20)
        self.pdf.drawString(50, H - 60, "Recent Logs – error messages")
        y = H - 110

        def draw_logs_header():
            self.pdf.setFont("Helvetica-Bold", 11)
            self.pdf.drawString(50, y, "Timestamp")
            self.pdf.drawString(160, y, "TestCase")
            self.pdf.drawString(310, y, "Result")
            self.pdf.drawString(370, y, "Message")
            self.pdf.line(50, y - 4, W - 50, y - 4)

        draw_logs_header()
        y -= 25
        self.pdf.setFont("Helvetica", 10)

        for r in self.results:
            if y < 70:
                self.pdf.showPage()
                y = H - 110
                draw_logs_header()
                y -= 25
                self.pdf.setFont("Helvetica", 10)

            ts = r.started_at.strftime("%Y-%m-%d %H:%M")
            tc = (r.test_case.label or "")[:24]
            raw = r.log
            msg = self.format_message_for_pdf(raw)

            self.pdf.drawString(50, y, ts)
            self.pdf.drawString(160, y, tc)

            if r.result:
                self.pdf.setFillColor(colors.HexColor("#16a34a"))
                self.pdf.drawString(310, y, "PASS")
            else:
                self.pdf.setFillColor(colors.HexColor("#dc2626"))
                self.pdf.drawString(310, y, "FAIL")
            self.pdf.setFillColor(colors.black)
            self.pdf.drawString(370, y, msg)
            y -= 20

    def draw_group_summary(self):
        self.pdf.setFont("Helvetica-Bold", 20)
        self.pdf.drawString(50, H - 60, "Group Summary")
        y = H - 110
        self.pdf.setFont("Helvetica-Bold", 12)
        self.pdf.drawString(50, y, "Group")
        self.pdf.drawString(250, y, "Pass")
        self.pdf.drawString(320, y, "Fail")
        self.pdf.drawString(380, y, "Total")
        self.pdf.line(50, y - 4, W - 50, y - 4)
        y -= 24
        self.pdf.setFont("Helvetica", 12)

        for name, p, f in zip(
            self.group_labels_all, self.group_passes_all, self.group_fails_all
        ):
            if y < 70:
                self.pdf.showPage()
                y = H - 80
                self.pdf.setFont("Helvetica-Bold", 12)
                self.pdf.drawString(50, y, "Group")
                self.pdf.drawString(250, y, "Pass")
                self.pdf.drawString(320, y, "Fail")
                self.pdf.drawString(380, y, "Total")
                self.pdf.line(50, y - 4, W - 50, y - 4)
                y -= 24
                self.pdf.setFont("Helvetica", 12)

            self.pdf.drawString(50, y, name[:28])
            self.pdf.setFillColor(colors.HexColor("#16a34a"))
            self.pdf.drawRightString(290, y, str(p))
            self.pdf.setFillColor(colors.HexColor("#dc2626"))
            self.pdf.drawRightString(350, y, str(f))
            self.pdf.setFillColor(colors.black)
            self.pdf.drawRightString(420, y, str(p + f))
            y -= 20
        self.pdf.showPage()

    def format_message_for_pdf(self, raw, max_len=60):
        if not raw:
            return "No log message."
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return raw[:max_len]
        if isinstance(raw, dict) and "tests" in raw:
            for testname, test in raw["tests"].items():
                if test["status"] == "FAIL":
                    return test["message"][:max_len]
        return "Log format not recognized."
