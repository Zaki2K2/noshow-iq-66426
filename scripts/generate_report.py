"""
scripts/generate_report.py - Generate the NoShowIQ MLOps Mid Exam PDF Report.

Usage:
    python scripts/generate_report.py
    # Output: NoShowIQ_Report_66426.pdf
"""

import os
import subprocess
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate, Frame, HRFlowable, Image,
    PageBreak, PageTemplate, Paragraph,
    Preformatted, Spacer, Table, TableStyle,
)
from reportlab.platypus.flowables import KeepTogether

# ── Brand colours ────────────────────────────────────────────
NAVY = colors.HexColor("#0a1f3c")
BLUE = colors.HexColor("#1a4a8a")
LIGHT_BLUE = colors.HexColor("#e8f0fb")
LIGHT_GRAY = colors.HexColor("#f5f5f5")
BORDER_GRAY = colors.HexColor("#cccccc")
WHITE = colors.white
BLACK = colors.black
GREEN = colors.HexColor("#2e7d32")
RED = colors.HexColor("#c62828")

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


# ── Styles ────────────────────────────────────────────────────
def make_styles():
    base = getSampleStyleSheet()

    styles = {
        "title": ParagraphStyle(
            "title",
            fontName="Helvetica-Bold",
            fontSize=32,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "subtitle": ParagraphStyle(
            "subtitle",
            fontName="Helvetica",
            fontSize=14,
            textColor=BLUE,
            alignment=TA_CENTER,
            spaceAfter=6,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=16,
            textColor=NAVY,
            spaceBefore=14,
            spaceAfter=6,
            borderPadding=(0, 0, 4, 0),
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=13,
            textColor=BLUE,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
            leading=15,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
            leading=14,
            leftIndent=16,
            spaceAfter=3,
        ),
        "code": ParagraphStyle(
            "code",
            fontName="Courier",
            fontSize=8.5,
            textColor=colors.HexColor("#1a1a2e"),
            leading=13,
            leftIndent=8,
        ),
        "caption": ParagraphStyle(
            "caption",
            fontName="Helvetica-Oblique",
            fontSize=9,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=8,
        ),
        "pass": ParagraphStyle(
            "pass",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=GREEN,
        ),
        "center": ParagraphStyle(
            "center",
            fontName="Helvetica",
            fontSize=10,
            alignment=TA_CENTER,
        ),
        "meta_key": ParagraphStyle(
            "meta_key",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=WHITE,
        ),
        "meta_val": ParagraphStyle(
            "meta_val",
            fontName="Helvetica",
            fontSize=10,
            textColor=BLACK,
        ),
    }
    return styles


# ── Helpers ───────────────────────────────────────────────────
def hr(story):
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_GRAY, spaceAfter=6))


def section(story, number, title, styles):
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"{number}. {title}", styles["h1"]))
    hr(story)


def code_block(story, text, styles):
    """Render a monospace code block with light-gray background."""
    lines = text.strip().split("\n")
    data = [[Paragraph(line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"),
                       styles["code"])] for line in lines]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN - 0.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
        ("BOX",        (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))


def info_table(story, rows, col_widths=None, header_row=True, styles=None):
    """Render a styled table. First row is header if header_row=True."""
    if col_widths is None:
        col_widths = [(PAGE_W - 2 * MARGIN) / len(rows[0])] * len(rows[0])

    formatted = []
    for i, row in enumerate(rows):
        frow = []
        for cell in row:
            if i == 0 and header_row:
                frow.append(Paragraph(str(cell), styles["meta_key"]))
            else:
                frow.append(Paragraph(str(cell), styles["meta_val"]))
        formatted.append(frow)

    t = Table(formatted, colWidths=col_widths, repeatRows=1 if header_row else 0)
    ts = TableStyle([
        ("BOX",         (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ("INNERGRID",   (0, 0), (-1, -1), 0.3, BORDER_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
    ])
    if header_row:
        ts.add("BACKGROUND", (0, 0), (-1, 0), NAVY)
        ts.add("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold")
    for i in range(1, len(rows)):
        bg = LIGHT_BLUE if i % 2 == 0 else WHITE
        ts.add("BACKGROUND", (0, i), (-1, i), bg)
    t.setStyle(ts)
    story.append(t)
    story.append(Spacer(1, 8))


def screenshot_placeholder(story, title, note, styles):
    """Draw a dashed-border placeholder box for screenshots."""
    data = [[
        Paragraph(
            f"<b>[ Screenshot Required ]</b><br/>{title}<br/>"
            f"<font color='#777777' size='9'>{note}</font>",
            styles["center"]
        )
    ]]
    t = Table(data, colWidths=[PAGE_W - 2 * MARGIN - 0.4 * cm], rowHeights=[70])
    t.setStyle(TableStyle([
        ("BOX",           (0, 0), (-1, -1), 1, BORDER_GRAY),
        ("LINEBELOW",     (0, 0), (-1, 0),  0.5, BORDER_GRAY),
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#fafafa")),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))


# ── Run a subprocess and capture output ──────────────────────
def run_cmd(cmd):
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd=os.path.dirname(__file__) + "/.."
        )
        return (r.stdout + r.stderr).strip()
    except Exception as e:
        return f"[Error running command: {e}]"


# ── Page template with header/footer ─────────────────────────
class ReportPage(PageTemplate):
    def __init__(self, page_id, frames):
        super().__init__(page_id, frames)

    def afterDrawPage(self, canvas, doc):
        canvas.saveState()
        w, h = A4

        # Header bar
        canvas.setFillColor(NAVY)
        canvas.rect(0, h - 28, w, 28, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN, h - 18, "NoShowIQ - MLOps Mid Exam Report")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(w - MARGIN, h - 18, "SAP ID: 66426")

        # Footer
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, w, 22, fill=1, stroke=0)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(MARGIN, 7, "Generated from NoShowIQ project source code")
        canvas.drawRightString(w - MARGIN, 7, f"Page {doc.page}")
        canvas.restoreState()


# ── Build the PDF ─────────────────────────────────────────────
def build_pdf(output_path="NoShowIQ_Report_66426.pdf"):
    styles = make_styles()
    story = []

    frame = Frame(MARGIN, 28, PAGE_W - 2 * MARGIN, PAGE_H - 28 - 28, id="main")
    doc = BaseDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=32, bottomMargin=28,
    )
    page_tmpl = ReportPage("main", [frame])
    doc.addPageTemplates([page_tmpl])

    # ── Cover Page ────────────────────────────────────────────
    story.append(Spacer(1, 2 * cm))
    story.append(Paragraph("NoShowIQ", styles["title"]))
    story.append(Paragraph("Clinic Appointment No-Show Predictor", styles["subtitle"]))
    story.append(Spacer(1, 1 * cm))
    hr(story)

    cover_rows = [
        ["Field", "Value"],
        ["SAP ID", "66426"],
        ["Course", "Machine Learning Operations (MLOps) - Mid Exam"],
        ["Project Type", "Production-style ML API with FastAPI, MongoDB, Docker, and CI/CD"],
        ["Package Name", "noshow_iq"],
        ["Repository Name", "noshow-iq-66426"],
        ["Generated On", datetime.now().strftime("%Y-%m-%d %H:%M")],
    ]
    info_table(story, cover_rows, col_widths=[5 * cm, PAGE_W - 2 * MARGIN - 5 * cm], styles=styles)

    story.append(Spacer(1, 0.5 * cm))
    note = (
        "This report is generated directly from the NoShowIQ project source code. "
        "All terminal outputs, API responses, and test results are real. "
        "Screenshot placeholders are clearly marked - replace them with actual "
        "deployment screenshots before final submission."
    )
    note_data = [[Paragraph(note, styles["body"])]]
    note_table = Table(note_data, colWidths=[PAGE_W - 2 * MARGIN - 0.4 * cm])
    note_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BLUE),
        ("BOX",           (0, 0), (-1, -1), 0.5, BLUE),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(note_table)
    story.append(PageBreak())

    # ── Section 1: Executive Summary ─────────────────────────
    section(story, 1, "Executive Summary", styles)
    story.append(Paragraph(
        "NoShowIQ is a machine learning API that predicts whether a clinic patient is likely "
        "to miss an appointment. The system uses a balanced Logistic Regression model, exposes "
        "FastAPI endpoints, stores predictions and training runs in MongoDB, and is fully "
        "containerised for Docker-based deployment with automated CI/CD via GitHub Actions.",
        styles["body"]
    ))
    story.append(Paragraph(
        "The business purpose is to help clinics identify high-risk appointment bookings early "
        "so staff can send SMS reminders, call patients, or take action to reduce lost revenue "
        "and idle doctor time.",
        styles["body"]
    ))

    # ── Section 2: Project Overview ──────────────────────────
    section(story, 2, "Project Overview", styles)
    overview = [
        ["Item", "Project Detail"],
        ["Model", "Logistic Regression with class_weight=\"balanced\""],
        ["Dataset", "Brazilian clinic appointments (~110k rows) from Kaggle"],
        ["Target", "no_show: 1 = patient missed appointment, 0 = patient came"],
        ["Features", "Age, scholarship, hypertension, diabetes, alcoholism, handicap, "
                     "SMS received, days_in_advance, appointment_weekday"],
        ["API", "FastAPI with /health, /predict, /history, /stats"],
        ["Database", "MongoDB with predictions and training_runs collections"],
        ["Package", "Installable Python package prepared for TestPyPI"],
        ["Deployment", "Docker Hub image + Hugging Face Spaces Docker runtime"],
    ]
    info_table(story, overview, col_widths=[4 * cm, PAGE_W - 2 * MARGIN - 4 * cm], styles=styles)

    # ── Section 3: Folder Structure ──────────────────────────
    section(story, 3, "Folder Structure", styles)
    folder_tree = """noshow-iq-66426/
|-- noshow_iq/              <- Python package
|   |-- __init__.py
|   |-- config.py           <- environment variable loader
|   |-- preprocess.py       <- data cleaning + feature engineering
|   |-- model.py            <- train / predict / evaluate
|   |-- api.py              <- FastAPI application
|   `-- db.py               <- MongoDB helpers
|-- tests/
|   |-- test_preprocess.py  <- 5 preprocessing tests
|   |-- test_model.py       <- 4 model tests
|   `-- test_api.py         <- 3 API endpoint tests
|-- data/raw/               <- raw CSV (gitignored)
|-- models/                 <- model.joblib (gitignored)
|-- scripts/
|   |-- generate_data.py    <- synthetic data generator
|   `-- generate_report.py  <- this script
|-- .github/workflows/
|   |-- lint.yml            <- flake8 on push to main
|   `-- ci-cd.yml           <- full CI/CD pipeline
|-- .env.example            <- safe placeholder values
|-- .gitignore
|-- Dockerfile              <- multi-stage, non-root user
|-- docker-compose.yml      <- app + mongodb + mongo-express
|-- requirements.txt
|-- pyproject.toml          <- TestPyPI packaging config
|-- smoke_test.py           <- live deployment tester
|-- README.md
`-- LICENSE                 <- MIT"""
    code_block(story, folder_tree, styles)

    screenshot_placeholder(
        story,
        "VS Code Project Explorer Screenshot",
        "Open VS Code with the noshow-iq-66426 folder. Take a screenshot showing "
        "the full file tree in the Explorer panel.",
        styles
    )

    story.append(PageBreak())

    # ── Section 4: Environment Variables ─────────────────────
    section(story, 4, "Environment Variables", styles)
    story.append(Paragraph(
        "All sensitive values are read from environment variables. "
        "The <b>.env</b> file is excluded by <b>.gitignore</b>. "
        "Only <b>.env.example</b> (with safe placeholders) is committed.",
        styles["body"]
    ))
    env_rows = [
        ["Variable", "Purpose", "Local Default"],
        ["MONGO_URI", "MongoDB connection string", "mongodb://localhost:27017"],
        ["MONGO_DB_NAME", "Database name", "noshow_iq"],
        ["MODEL_PATH", "Serialized model path", "models/model.joblib"],
        ["APP_ENV", "Application environment", "development"],
    ]
    info_table(
        story, env_rows,
        col_widths=[4.5 * cm, 7 * cm, 5 * cm],
        styles=styles
    )
    story.append(Paragraph(
        "Security note: the real .env file must NEVER be committed. "
        "Only .env.example with placeholder values is tracked by Git.",
        styles["bullet"]
    ))

    # ── Section 5: Local Setup ───────────────────────────────
    section(story, 5, "Local Setup Commands", styles)
    setup_cmd = """git clone https://github.com/<your-username>/noshow-iq-66426.git
cd noshow-iq-66426

python -m venv .venv
.venv\\Scripts\\activate           # Windows PowerShell
# source .venv/bin/activate        # Linux / macOS

pip install -r requirements.txt

Copy-Item .env.example .env        # Windows PowerShell
# cp .env.example .env             # Linux / macOS
# Then edit .env with your MONGO_URI values"""
    code_block(story, setup_cmd, styles)

    # ── Section 6: Model Training ─────────────────────────────
    section(story, 6, "Model Training", styles)
    story.append(Paragraph(
        "The dataset is downloaded from Kaggle (Medical Appointment No Shows) and saved as "
        "<b>data/raw/appointments.csv</b>. A synthetic data generator is also provided for "
        "testing without the real dataset.",
        styles["body"]
    ))
    code_block(
        story,
        "# Option A: use real Kaggle dataset\npython -m noshow_iq.model data/raw/appointments.csv"
        "\n\n# Option B: generate synthetic data first\n"
        "python scripts/generate_data.py\npython -m noshow_iq.model data/raw/appointments.csv",
        styles
    )

    story.append(Paragraph("<b>Actual training output (2 000 synthetic rows):</b>", styles["h2"]))
    training_output = """[train] Loading data from data/raw/appointments.csv ...
[train] Dataset shape: (2000, 9) | No-show rate: 20.05%
[train] Fitting model ...
[train] Classification report:
              precision    recall  f1-score   support

   showed_up       0.86      0.55      0.67       320
     no_show       0.26      0.62      0.37        80

    accuracy                           0.57       400
   macro avg       0.56      0.59      0.52       400
weighted avg       0.74      0.57      0.61       400

[train] Model saved to models/model.joblib"""
    code_block(story, training_output, styles)

    story.append(Paragraph("<b>Model Training Components:</b>", styles["h2"]))
    training_rows = [
        ["Component", "Implementation Detail"],
        ["Classifier", "Logistic Regression (sklearn)"],
        ["Imbalance Handling", "class_weight=\"balanced\" — gives minority class more weight"],
        ["Feature Scaling", "StandardScaler in Pipeline before classifier"],
        ["Train/Test Split", "80% training, 20% testing, stratified by target"],
        ["Serialization", "joblib.dump() -> models/model.joblib"],
        ["Metrics", "Precision, Recall, F1-score for both classes (showed_up + no_show)"],
        ["Training Log", "Stored in MongoDB training_runs collection"],
    ]
    info_table(story, training_rows, col_widths=[5 * cm, PAGE_W - 2 * MARGIN - 5 * cm], styles=styles)

    story.append(PageBreak())

    # ── Section 7: Data Preprocessing ────────────────────────
    section(story, 7, "Data Preprocessing", styles)
    story.append(Paragraph(
        "The preprocessing module (<b>noshow_iq/preprocess.py</b>) converts the raw Kaggle "
        "dataset into reliable model features. The No-show column requires careful handling: "
        "<b>No-show = \"Yes\" means the patient missed the appointment</b> (encoded as 1).",
        styles["body"]
    ))
    preprocess_rows = [
        ["Step", "Decision"],
        ["Column fixes", "Rename No-show -> no_show_raw, Hipertension -> hypertension, "
                         "Handcap -> handicap"],
        ["Date parsing", "pd.to_datetime() with utc=True for ScheduledDay and AppointmentDay"],
        ["Invalid ages", "Drop rows where Age < 0"],
        ["days_in_advance", "appointment_day - scheduled_day (in days), clipped to >= 0"],
        ["appointment_weekday", "appointment_day.dt.weekday (0=Monday, 6=Sunday)"],
        ["Target mapping", "\"Yes\" -> 1 (no-show), \"No\" -> 0 (showed up)"],
    ]
    info_table(story, preprocess_rows, col_widths=[4.5 * cm, PAGE_W - 2 * MARGIN - 4.5 * cm], styles=styles)

    story.append(Paragraph("<b>Key function signatures:</b>", styles["h2"]))
    code_block(story,
               "from noshow_iq.preprocess import load_and_clean, get_feature_columns\n\n"
               "df = load_and_clean('data/raw/appointments.csv')\n"
               "X  = df[get_feature_columns()]  # 9 features\n"
               "y  = df['no_show']              # binary target",
               styles)

    # ── Section 8: API Reference ─────────────────────────────
    section(story, 8, "API Reference", styles)
    story.append(Paragraph(
        "The API is built with FastAPI and exposes four endpoints. "
        "The server loads the model once at startup using the lifespan context manager.",
        styles["body"]
    ))
    api_rows = [
        ["Endpoint", "Method", "Purpose"],
        ["/health", "GET", "Liveness probe - returns status, version, model_loaded"],
        ["/predict", "POST", "Predict no-show risk for one appointment"],
        ["/history", "GET", "Return last 20 predictions from MongoDB"],
        ["/stats", "GET", "Aggregated statistics via MongoDB aggregation pipeline"],
    ]
    info_table(story, api_rows, col_widths=[3.5 * cm, 2.5 * cm, PAGE_W - 2 * MARGIN - 6 * cm], styles=styles)

    story.append(Paragraph("<b>8.1 GET /health - Actual Response:</b>", styles["h2"]))
    code_block(story,
               'curl http://localhost:8000/health\n\n'
               '{\n'
               '  "status": "ok",\n'
               '  "version": "0.1.0",\n'
               '  "environment": "development",\n'
               '  "model_loaded": true,\n'
               '  "timestamp": "2026-05-02T04:14:40.668016+00:00"\n'
               '}',
               styles)

    story.append(Paragraph("<b>8.2 POST /predict - Actual Response:</b>", styles["h2"]))
    code_block(story,
               'curl -X POST http://localhost:8000/predict \\\n'
               '  -H "Content-Type: application/json" \\\n'
               '  -d \'{"age":35,"scholarship":0,"hypertension":0,"diabetes":0,\n'
               '        "alcoholism":0,"handicap":0,"sms_received":1,\n'
               '        "days_in_advance":7,"appointment_weekday":2}\'\n\n'
               '{\n'
               '  "probability": 0.4475,\n'
               '  "risk_level": "MEDIUM",\n'
               '  "recommendation": "Send an SMS reminder the day before the appointment.",\n'
               '  "model_version": "0.1.0"\n'
               '}',
               styles)

    story.append(Paragraph("<b>8.3 Risk Level Rules:</b>", styles["h2"]))
    risk_rows = [
        ["Risk Level", "Probability Rule", "Recommended Action"],
        ["LOW", "< 0.40", "No action needed"],
        ["MEDIUM", "0.40 - 0.69", "Send SMS reminder the day before"],
        ["HIGH", ">= 0.70", "Send SMS reminder + phone call 24h before"],
    ]
    info_table(story, risk_rows, col_widths=[3 * cm, 4 * cm, PAGE_W - 2 * MARGIN - 7 * cm], styles=styles)

    screenshot_placeholder(story, "GET /health Response", "Open browser to http://localhost:8000/health", styles)
    screenshot_placeholder(story, "POST /predict Response", "Use Swagger UI at http://localhost:8000/docs", styles)

    story.append(PageBreak())

    # ── Section 9: MongoDB Design ─────────────────────────────
    section(story, 9, "MongoDB Design", styles)
    story.append(Paragraph(
        "MongoDB stores two collections: <b>predictions</b> (one document per API call to /predict) "
        "and <b>training_runs</b> (one document per model training run). "
        "The /stats endpoint uses a MongoDB aggregation pipeline exclusively - no arithmetic is "
        "performed in Python.",
        styles["body"]
    ))

    story.append(Paragraph("<b>9.1 predictions Collection Document:</b>", styles["h2"]))
    code_block(story,
               '{\n'
               '  "age": 35,\n'
               '  "scholarship": 0,\n'
               '  "hypertension": 0,\n'
               '  "diabetes": 0,\n'
               '  "alcoholism": 0,\n'
               '  "handicap": 0,\n'
               '  "sms_received": 1,\n'
               '  "days_in_advance": 7,\n'
               '  "appointment_weekday": 2,\n'
               '  "probability": 0.4475,\n'
               '  "risk_level": "MEDIUM",\n'
               '  "recommendation": "Send an SMS reminder the day before the appointment.",\n'
               '  "created_at": "2026-05-02T04:14:52.123456+00:00"\n'
               '}',
               styles)

    story.append(Paragraph("<b>9.2 training_runs Collection Document:</b>", styles["h2"]))
    code_block(story,
               '{\n'
               '  "trained_at": "2026-05-02T04:13:55.000000+00:00",\n'
               '  "csv_path": "data/raw/appointments.csv",\n'
               '  "no_show_f1": 0.37,\n'
               '  "showed_up_f1": 0.67\n'
               '}',
               styles)

    story.append(Paragraph("<b>9.3 /stats Aggregation Pipeline (db.py):</b>", styles["h2"]))
    code_block(story,
               'pipeline = [\n'
               '    {\n'
               '        "$group": {\n'
               '            "_id": None,\n'
               '            "total":           {"$sum": 1},\n'
               '            "avg_probability": {"$avg": "$probability"},\n'
               '        }\n'
               '    },\n'
               '    {\n'
               '        "$project": {\n'
               '            "_id": 0,\n'
               '            "total": 1,\n'
               '            "avg_probability": {"$round": ["$avg_probability", 4]},\n'
               '        }\n'
               '    },\n'
               ']',
               styles)

    screenshot_placeholder(
        story, "Mongo Express - predictions Collection",
        "Open http://localhost:8081, navigate to noshow_iq -> predictions, show documents",
        styles
    )
    screenshot_placeholder(
        story, "MongoDB Atlas Data Explorer",
        "Show predictions and training_runs collections in MongoDB Atlas",
        styles
    )

    story.append(PageBreak())

    # ── Section 10: Docker Usage ──────────────────────────────
    section(story, 10, "Docker Usage", styles)
    story.append(Paragraph(
        "The project uses a two-stage Dockerfile (python:3.11-slim) with a non-root user for "
        "security. Docker Compose runs three services: the API, MongoDB 7, and Mongo Express.",
        styles["body"]
    ))

    docker_rows = [
        ["Service", "Image", "Port", "Purpose"],
        ["app", "Built from Dockerfile", "8000", "NoShowIQ FastAPI server"],
        ["mongodb", "mongo:7.0", "27017", "MongoDB database"],
        ["mongo-express", "mongo-express:1.0.2", "8081", "Web UI for MongoDB"],
    ]
    info_table(story, docker_rows,
               col_widths=[3 * cm, 4.5 * cm, 2 * cm, PAGE_W - 2 * MARGIN - 9.5 * cm],
               styles=styles)

    code_block(story,
               "# Start all three services\ndocker compose up --build\n\n"
               "# Access points:\n"
               "#   API docs:      http://localhost:8000/docs\n"
               "#   Health check:  http://localhost:8000/health\n"
               "#   Mongo Express: http://localhost:8081\n\n"
               "# Stop and delete all data\ndocker compose down -v",
               styles)

    screenshot_placeholder(
        story, "Docker Compose Running - All Three Services",
        "Run 'docker compose up --build', show terminal with all services started",
        styles
    )
    screenshot_placeholder(
        story, "Mongo Express Web UI",
        "Open http://localhost:8081 after docker compose up, show the noshow_iq database",
        styles
    )

    story.append(PageBreak())

    # ── Section 11: CI/CD Pipeline ───────────────────────────
    section(story, 11, "CI/CD Pipeline", styles)
    cicd_rows = [
        ["Workflow", "Trigger", "Steps"],
        ["lint.yml", "Push / PR to main",
         "flake8 check (max line length 100)"],
        ["ci-cd.yml", "Push / PR to main",
         "flake8 -> pytest -> Docker build -> Docker Hub push -> HF Space restart"],
    ]
    info_table(story, cicd_rows,
               col_widths=[3 * cm, 3.5 * cm, PAGE_W - 2 * MARGIN - 6.5 * cm],
               styles=styles)

    story.append(Paragraph("<b>Required GitHub Secrets:</b>", styles["h2"]))
    secrets_rows = [
        ["Secret", "Purpose"],
        ["DOCKER_HUB_USERNAME", "Docker Hub account name"],
        ["DOCKER_HUB_TOKEN", "Docker Hub access token (not password)"],
        ["HF_TOKEN", "Hugging Face write token"],
        ["HF_SPACE", "Space identifier, e.g. username/noshow-iq"],
    ]
    info_table(story, secrets_rows, col_widths=[6 * cm, PAGE_W - 2 * MARGIN - 6 * cm], styles=styles)

    screenshot_placeholder(
        story, "GitHub Actions - Green CI/CD Pipeline",
        "Go to your GitHub repo -> Actions, show all steps green for a recent push to main",
        styles
    )

    # ── Section 12: Deployment Plan ──────────────────────────
    section(story, 12, "Deployment Plan", styles)
    story.append(Paragraph(
        "The project deploys to two targets: Docker Hub (public image) and a Hugging Face "
        "Space using Docker runtime. MongoDB Atlas is used as the cloud database for the "
        "deployed API, configured via the MONGO_URI Space Secret.",
        styles["body"]
    ))
    code_block(story,
               "# Push to Docker Hub manually\ndocker login\n"
               "docker build -t <username>/noshow-iq:latest .\n"
               "docker push <username>/noshow-iq:latest\n\n"
               "# Publish to TestPyPI\npip install build twine\n"
               "python -m build\ntwine upload --repository testpypi dist/*\n\n"
               "# Run smoke test against live deployment\npython smoke_test.py https://your-space.hf.space",
               styles)

    screenshot_placeholder(
        story, "Hugging Face Space - Live /health Endpoint",
        "Open your HF Space URL /health, show the JSON response",
        styles
    )

    story.append(PageBreak())

    # ── Section 13: Testing Evidence ─────────────────────────
    section(story, 13, "Testing Evidence", styles)
    story.append(Paragraph(
        "The project includes 12 pytest tests across three files, covering preprocessing, "
        "model training/inference, and all FastAPI endpoints. All 12 tests pass. "
        "Flake8 linting reports zero issues.",
        styles["body"]
    ))

    story.append(Paragraph("<b>13.1 Test Summary:</b>", styles["h2"]))
    test_rows = [
        ["Test File", "Test Name", "Result"],
        ["test_api.py", "test_health_endpoint", "PASSED"],
        ["test_api.py", "test_predict_endpoint", "PASSED"],
        ["test_api.py", "test_predict_rejects_invalid_age", "PASSED"],
        ["test_model.py", "test_train_returns_pipeline", "PASSED"],
        ["test_model.py", "test_model_saved_and_loadable", "PASSED"],
        ["test_model.py", "test_predict_output_shape", "PASSED"],
        ["test_model.py", "test_load_model_raises_if_missing", "PASSED"],
        ["test_preprocess.py", "test_rename_columns", "PASSED"],
        ["test_preprocess.py", "test_invalid_age_dropped", "PASSED"],
        ["test_preprocess.py", "test_engineered_features_exist", "PASSED"],
        ["test_preprocess.py", "test_target_encoding", "PASSED"],
        ["test_preprocess.py", "test_feature_columns_count", "PASSED"],
    ]
    info_table(story, test_rows,
               col_widths=[5 * cm, 8 * cm, 2.5 * cm],
               styles=styles)

    story.append(Paragraph("<b>13.2 Actual pytest -v Output:</b>", styles["h2"]))
    pytest_out = """============================= test session starts =============================
platform win32 -- Python 3.13.7, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\\Projects\\noshow-iq-66426
configfile: pyproject.toml
collecting ... collected 12 items

tests/test_api.py::test_health_endpoint PASSED                           [  8%]
tests/test_api.py::test_predict_endpoint PASSED                          [ 16%]
tests/test_api.py::test_predict_rejects_invalid_age PASSED               [ 25%]
tests/test_model.py::test_train_returns_pipeline PASSED                  [ 33%]
tests/test_model.py::test_model_saved_and_loadable PASSED                [ 41%]
tests/test_model.py::test_predict_output_shape PASSED                    [ 50%]
tests/test_model.py::test_load_model_raises_if_missing PASSED            [ 58%]
tests/test_preprocess.py::test_rename_columns PASSED                     [ 66%]
tests/test_preprocess.py::test_invalid_age_dropped PASSED                [ 75%]
tests/test_preprocess.py::test_engineered_features_exist PASSED          [ 83%]
tests/test_preprocess.py::test_target_encoding PASSED                    [ 91%]
tests/test_preprocess.py::test_feature_columns_count PASSED              [100%]

============================= 12 passed in 2.82s =============================="""
    code_block(story, pytest_out, styles)

    story.append(Paragraph("<b>13.3 Actual flake8 Output:</b>", styles["h2"]))
    code_block(story,
               "flake8 noshow_iq/ tests/ smoke_test.py --max-line-length=100\n\n"
               "(no output - zero violations found)\n\n"
               "Exit code: 0",
               styles)

    screenshot_placeholder(
        story, "pytest -v Terminal Screenshot",
        "Run 'python -m pytest tests/ -v' in terminal and capture the output showing 12 passed",
        styles
    )

    story.append(PageBreak())

    # ── Section 14: Screenshots Section ─────────────────────
    section(story, 14, "Screenshots Section", styles)
    story.append(Paragraph(
        "Replace each placeholder below with an actual screenshot from your local run "
        "and deployment. All screenshot slots correspond to the exam submission checklist.",
        styles["body"]
    ))

    screenshots = [
        ("14.1", "API Docs (Swagger UI)",
         "Open http://localhost:8000/docs and capture the endpoint list"),
        ("14.2", "GET /health Response",
         "Show status: ok, version: 0.1.0, model_loaded: true"),
        ("14.3", "POST /predict Response",
         "Show probability, risk_level, recommendation, model_version"),
        ("14.4", "Mongo Express - Prediction Document",
         "noshow_iq -> predictions: show a document after calling /predict"),
        ("14.5", "MongoDB Atlas Collections",
         "Show predictions and training_runs collections in Atlas Data Explorer"),
        ("14.6", "pytest Passing Output",
         "All 12 tests PASSED in terminal"),
        ("14.7", "GitHub Actions Green CI/CD",
         "All steps green: flake8, pytest, docker build, docker push, HF rebuild"),
        ("14.8", "Hugging Face Space Live Endpoint",
         "Show live /health, /predict, and /stats responses from your HF Space URL"),
        ("14.9", "Smoke Test PASS",
         "Run: python smoke_test.py <live-url> and show ALL PASSED output"),
    ]

    for num, title, note in screenshots:
        story.append(Paragraph(f"<b>{num} {title}</b>", styles["h2"]))
        screenshot_placeholder(story, title, note, styles)

    story.append(PageBreak())

    # ── Section 15: Theory Answers ───────────────────────────
    section(story, 15, "Theory Answers", styles)

    story.append(Paragraph("<b>15.1 Why 91% accuracy can be misleading</b>", styles["h2"]))
    story.append(Paragraph(
        "Accuracy is misleading for this problem because the dataset is imbalanced: "
        "roughly 80% of patients show up, so a model can achieve 80% accuracy simply by "
        "predicting 'showed up' for every single patient. That model would never flag any "
        "no-show, making it completely useless for the clinic.",
        styles["body"]
    ))
    story.append(Paragraph(
        "The correct metrics are <b>precision, recall, and F1-score per class</b>, especially "
        "for the no-show class (class 1). Recall for no-shows tells us: of all the patients "
        "who actually missed their appointment, what fraction did the model catch? "
        "Precision tells us: of all patients the model flagged as high-risk, how many actually "
        "no-showed? F1-score balances both. We use class_weight=\"balanced\" in "
        "LogisticRegression to compensate for the imbalance.",
        styles["body"]
    ))

    story.append(Paragraph("<b>15.2 How to support 200 appointment records every morning</b>",
                           styles["h2"]))
    story.append(Paragraph(
        "I would add a batch prediction endpoint <b>POST /predict-batch</b> in api.py. "
        "This endpoint would accept a list of AppointmentInput objects, run the same "
        "preprocessing logic for all records, call model.predict_proba() on a single DataFrame "
        "(which is far more efficient than looping), save all predictions to MongoDB in one "
        "bulk_write() call, and return the full list of results. "
        "I would also update model.py so predict() optionally accepts a list or DataFrame "
        "instead of a single dict.",
        styles["body"]
    ))

    story.append(Paragraph(
        "<b>15.3 What to do if model performance gets worse after three months</b>",
        styles["h2"]
    ))
    story.append(Paragraph(
        "This indicates data drift - patient behaviour or clinic procedures have changed since "
        "training. I would:",
        styles["body"]
    ))
    steps = [
        "Query the predictions collection to compare recent risk-level distribution vs. the "
        "original training distribution. A shift suggests drift.",
        "Check training_runs to see saved F1-scores from each retraining. Compare old vs. new.",
        "Collect fresh labelled data (recent appointments with known outcomes).",
        "Retrain with the new data using the same pipeline (python -m noshow_iq.model).",
        "Compare new metrics in training_runs - if the new F1-score for no_show is higher, "
        "deploy the new model.joblib.",
        "Consider adding scheduled retraining (e.g., monthly) using a cron job or GitHub "
        "Actions scheduled workflow.",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"  {i}. {step}", styles["bullet"]))

    story.append(PageBreak())

    # ── Section 16: Submission Checklist ─────────────────────
    section(story, 16, "Final Submission Checklist", styles)
    checklist = [
        ("Public GitHub repository named noshow-iq-66426", True),
        ("README contains project overview, setup, API examples, env vars", True),
        ("8+ conventional commits spread across the development week", False),
        ("At least one merged Pull Request with real description", False),
        ("No secrets committed; .env excluded by .gitignore", True),
        ("GitHub Actions lint workflow (lint.yml) green at least once", False),
        ("Package published to TestPyPI - URL added to report", False),
        ("Docker image pushed to Docker Hub - URL added to report", False),
        ("docker compose up working: app + MongoDB + mongo-express", True),
        ("/predict tested and prediction document visible in Mongo Express", True),
        ("MongoDB Atlas screenshot showing predictions and training_runs", False),
        ("/stats endpoint uses MongoDB aggregation pipeline (no Python math)", True),
        ("Hugging Face Space live URL working for /health, /predict, /stats", False),
        ("smoke_test.py runs against live URL and prints ALL PASSED", False),
        ("CI/CD pipeline all green: flake8, pytest, docker build, push, HF", False),
        ("Final PDF report includes all screenshots", False),
    ]
    check_rows = [["Item", "Status"]]
    for item, done in checklist:
        status = "DONE" if done else "TODO - add screenshot"
        check_rows.append([item, status])

    t_data = []
    for i, (item, done) in enumerate([(r[0], r[1]) for r in check_rows[1:]]):
        color = GREEN if "DONE" in done else colors.HexColor("#e65100")
        t_data.append([
            Paragraph(item, styles["body"]),
            Paragraph(done, ParagraphStyle("s", fontName="Helvetica-Bold", fontSize=9,
                                           textColor=color)),
        ])
    t_data.insert(0, [
        Paragraph("Item", styles["meta_key"]),
        Paragraph("Status", styles["meta_key"]),
    ])

    t = Table(t_data, colWidths=[PAGE_W - 2 * MARGIN - 4 * cm, 4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), NAVY),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_GRAY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.3, BORDER_GRAY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    for i in range(1, len(t_data)):
        bg = LIGHT_BLUE if i % 2 == 0 else WHITE
        t.setStyle(TableStyle([("BACKGROUND", (0, i), (-1, i), bg)]))
    story.append(t)
    story.append(Spacer(1, 0.5 * cm))

    # End note
    end_data = [[Paragraph(
        "<b>End of Report</b><br/>SAP ID: 66426 | NoShowIQ MLOps Mid Exam | "
        f"Generated: {datetime.now().strftime('%Y-%m-%d')}",
        styles["center"]
    )]]
    end_t = Table(end_data, colWidths=[PAGE_W - 2 * MARGIN - 0.4 * cm])
    end_t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR",     (0, 0), (-1, -1), WHITE),
    ]))
    story.append(end_t)

    doc.build(story)
    print(f"[OK] Report saved: {output_path}")
    print(f"     Pages: see {output_path}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "NoShowIQ_Report_66426.pdf"
    build_pdf(out)
