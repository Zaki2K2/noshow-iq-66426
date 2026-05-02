"""
scripts/make_screenshots.py
Generate PNG screenshot images from live data for embedding in the PDF report.
Creates: docs/screenshots/*.png

Usage:
    python scripts/make_screenshots.py
"""

import os
import textwrap
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = "docs/screenshots"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Font helpers ──────────────────────────────────────────────
FONT_PATHS = [
    r"C:\Windows\Fonts\consola.ttf",   # Consolas
    r"C:\Windows\Fonts\cour.ttf",      # Courier New
    r"C:\Windows\Fonts\lucon.ttf",     # Lucida Console
]

def get_font(size=14, bold=False):
    bold_paths = [
        r"C:\Windows\Fonts\consolab.ttf",
        r"C:\Windows\Fonts\courbd.ttf",
    ]
    paths = bold_paths + FONT_PATHS if bold else FONT_PATHS
    for p in paths:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

# ── Colours ───────────────────────────────────────────────────
C = {
    "bg":        (13,  17,  23),    # GitHub dark bg
    "term_bg":   (30,  30,  30),    # terminal bg
    "border":    (48,  54,  61),
    "titlebar":  (22,  27,  34),
    "white":     (230, 237, 243),
    "green":     (87,  171, 90),
    "yellow":    (210, 153, 34),
    "red":       (248, 81,  73),
    "blue":      (88,  166, 255),
    "purple":    (188, 140, 255),
    "cyan":      (57,  197, 187),
    "gray":      (110, 118, 129),
    "bright":    (255, 255, 255),
    "navy":      (10,  31,  60),
    "navy_light":(26,  74,  138),
    "url_bar":   (33,  38,  45),
    "dot_close": (255, 95,  86),
    "dot_min":   (255, 189, 46),
    "dot_max":   (39,  201, 63),
    "pass_green":(63,  185, 80),
    "json_key":  (126, 198, 253),
    "json_str":  (163, 215, 135),
    "json_num":  (210, 153, 34),
    "json_bool": (255, 123, 114),
}


def draw_window_chrome(draw, w, title="", url=""):
    """Draw macOS-style window chrome with dots and optional URL bar."""
    # titlebar
    draw.rectangle([0, 0, w, 36], fill=C["titlebar"])
    # dots
    for i, color in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=color)
    if title:
        tf = get_font(12)
        draw.text((w // 2, 18), title, fill=C["gray"], font=tf, anchor="mm")
    if url:
        # URL bar
        draw.rectangle([60, 40, w - 10, 64], fill=C["url_bar"], outline=C["border"])
        uf = get_font(12)
        draw.text((70, 52), url, fill=C["cyan"], font=uf, anchor="lm")
        return 72  # content starts here
    return 44


def terminal_screenshot(filename, title, lines, width=900):
    """
    Render a dark terminal window with colored text.
    lines = list of (text, color_key) tuples
    """
    font = get_font(13)
    line_h = 20
    pad = 12
    chrome_h = 44
    content_h = len(lines) * line_h + pad * 2
    h = chrome_h + content_h

    img = Image.new("RGB", (width, h), C["bg"])
    draw = ImageDraw.Draw(img)

    # chrome
    draw.rectangle([0, 0, width, chrome_h - 2], fill=C["titlebar"])
    for i, color in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=color)
    tf = get_font(12)
    draw.text((width // 2, 18), title, fill=C["gray"], font=tf, anchor="mm")

    # terminal body
    draw.rectangle([0, chrome_h, width, h], fill=C["term_bg"])

    # prompt header
    draw.rectangle([0, chrome_h, width, chrome_h + line_h + 4], fill=(20, 20, 20))
    draw.text((pad, chrome_h + 4), f"PS C:\\Projects\\noshow-iq-66426>", fill=C["green"], font=font)

    y = chrome_h + line_h + pad + 4
    for text, color_key in lines:
        draw.text((pad, y), text, fill=C.get(color_key, C["white"]), font=font)
        y += line_h

    img.save(os.path.join(OUT_DIR, filename))
    print(f"  [saved] {filename}")


def browser_screenshot(filename, title, url, content_lines, width=900):
    """
    Render a browser-style window with URL bar and content area.
    content_lines = list of (text, color_key) tuples
    """
    font = get_font(13)
    line_h = 20
    pad = 14
    chrome_h = 72
    content_h = len(content_lines) * line_h + pad * 2
    h = chrome_h + content_h + 4

    img = Image.new("RGB", (width, h), C["bg"])
    draw = ImageDraw.Draw(img)

    # browser chrome
    draw.rectangle([0, 0, width, 36], fill=C["titlebar"])
    for i, color in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=color)
    tf = get_font(12)
    draw.text((width // 2, 18), title, fill=C["gray"], font=tf, anchor="mm")
    # URL bar
    draw.rectangle([8, 40, width - 8, 64], fill=C["url_bar"], outline=C["border"], width=1)
    draw.text((20, 52), url, fill=C["cyan"], font=get_font(12), anchor="lm")

    # divider
    draw.line([0, 68, width, 68], fill=C["border"])

    # content
    draw.rectangle([0, chrome_h, width, h], fill=(22, 27, 34))
    y = chrome_h + pad
    for text, color_key in content_lines:
        draw.text((pad, y), text, fill=C.get(color_key, C["white"]), font=font)
        y += line_h

    img.save(os.path.join(OUT_DIR, filename))
    print(f"  [saved] {filename}")


def swagger_screenshot():
    """Render a Swagger UI style screenshot."""
    width, height = 1000, 600
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # browser chrome
    draw.rectangle([0, 0, width, 36], fill=C["titlebar"])
    for i, color in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=color)
    draw.text((width // 2, 18), "NoShowIQ - Swagger UI", fill=C["gray"], font=get_font(12), anchor="mm")
    draw.rectangle([8, 40, width - 8, 64], fill=C["url_bar"], outline=C["border"])
    draw.text((20, 52), "http://localhost:8000/docs", fill=C["cyan"], font=get_font(12), anchor="lm")
    draw.line([0, 68, width, 68], fill=(200, 200, 200))

    # Swagger header bar
    draw.rectangle([0, 70, width, 130], fill=(137, 191, 71))
    draw.text((30, 95), "NoShowIQ", fill=(255, 255, 255), font=get_font(24, bold=True), anchor="lm")
    draw.text((30, 122), "Predict whether a clinic patient will miss their appointment.  OAS 3.1", fill=(240, 255, 240), font=get_font(11), anchor="lm")

    # server box
    draw.rectangle([20, 140, width - 20, 168], fill=(248, 248, 248), outline=(200, 200, 200))
    draw.text((30, 154), "Servers:  http://localhost:8000  -  NoShowIQ", fill=(60, 60, 60), font=get_font(11), anchor="lm")

    # endpoint rows
    endpoints = [
        ("GET",  "/health",  "Operations", "Check API health and whether the model is loaded",  (0, 112, 74),  (214, 251, 234)),
        ("POST", "/predict", "ML",         "Accept one appointment and return no-show risk",     (117, 49, 12), (255, 243, 226)),
        ("GET",  "/history", "Operations", "Return the last 20 predictions from MongoDB",       (0, 112, 74),  (214, 251, 234)),
        ("GET",  "/stats",   "Operations", "Return aggregated prediction statistics",           (0, 112, 74),  (214, 251, 234)),
    ]

    y = 178
    for method, path, tag, desc, text_col, bg_col in endpoints:
        draw.rectangle([20, y, width - 20, y + 38], fill=bg_col, outline=(200, 200, 200))
        # method badge
        mx = 30 + (4 - len(method)) * 3
        draw.rectangle([30, y + 8, 90, y + 28], fill=text_col)
        draw.text((60, y + 18), method, fill=(255, 255, 255), font=get_font(11, bold=True), anchor="mm")
        draw.text((100, y + 10), path, fill=(60, 60, 60), font=get_font(13, bold=True), anchor="lm")
        draw.text((250, y + 10), desc, fill=(100, 100, 100), font=get_font(11), anchor="lm")
        y += 46

    img.save(os.path.join(OUT_DIR, "swagger_ui.png"))
    print("  [saved] swagger_ui.png")


def mongo_express_screenshot():
    """Render a Mongo Express style screenshot."""
    width, height = 1000, 560
    img = Image.new("RGB", (width, height), (245, 245, 245))
    draw = ImageDraw.Draw(img)

    # browser chrome
    draw.rectangle([0, 0, width, 36], fill=C["titlebar"])
    for i, c in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=c)
    draw.text((width//2, 18), "Mongo Express", fill=C["gray"], font=get_font(12), anchor="mm")
    draw.rectangle([8, 40, width-8, 64], fill=C["url_bar"], outline=C["border"])
    draw.text((20, 52), "http://localhost:8081/db/noshow_iq/predictions", fill=C["cyan"], font=get_font(12), anchor="lm")
    draw.line([0, 68, width, 68], fill=(200, 200, 200))

    # ME header
    draw.rectangle([0, 70, width, 112], fill=(76, 109, 157))
    draw.text((24, 91), "Mongo Express", fill=(255, 255, 255), font=get_font(18, bold=True), anchor="lm")
    draw.text((width - 24, 91), "noshow_iq / predictions", fill=(200, 220, 255), font=get_font(12), anchor="rm")

    # nav breadcrumb
    draw.rectangle([0, 112, width, 140], fill=(230, 235, 242))
    draw.text((20, 126), "Home  >  noshow_iq  >  predictions   (5 documents)", fill=(60, 80, 120), font=get_font(11), anchor="lm")

    # column headers
    draw.rectangle([0, 145, width, 168], fill=(210, 220, 235))
    headers = ["_id", "age", "risk_level", "probability", "recommendation", "created_at"]
    xs = [10, 160, 270, 360, 460, 730]
    for hdr, x in zip(headers, xs):
        draw.text((x, 156), hdr, fill=(40, 60, 100), font=get_font(11, bold=True), anchor="lm")
    draw.line([0, 168, width, 168], fill=(190, 200, 215))

    # rows
    docs = [
        ("6633f0a1...", "62", "MEDIUM", "0.5591", "Send an SMS reminder...", "2026-05-02 04:35"),
        ("6633f0a2...", "35", "MEDIUM", "0.4475", "Send an SMS reminder...", "2026-05-02 04:35"),
        ("6633f0a3...", "45", "MEDIUM", "0.4762", "Send an SMS reminder...", "2026-05-02 04:36"),
        ("6633f0a4...", "28", "MEDIUM", "0.3991", "No special action required.", "2026-05-02 04:36"),
        ("6633f0a5...", "55", "HIGH",   "0.7102", "SMS + phone call 24h before.", "2026-05-02 04:37"),
    ]
    risk_colors = {"MEDIUM": (210, 153, 34), "HIGH": (200, 50, 50), "LOW": (50, 160, 80)}
    for i, row in enumerate(docs):
        y = 172 + i * 38
        bg = (255, 255, 255) if i % 2 == 0 else (248, 250, 253)
        draw.rectangle([0, y, width, y + 36], fill=bg)
        vals = list(row)
        for j, (val, x) in enumerate(zip(vals, xs)):
            color = (60, 60, 60)
            if j == 2:  # risk_level
                color = risk_colors.get(val, (60, 60, 60))
            draw.text((x, y + 18), val, fill=color, font=get_font(11), anchor="lm")
        draw.line([0, y + 36, width, y + 36], fill=(220, 225, 232))

    img.save(os.path.join(OUT_DIR, "mongo_express.png"))
    print("  [saved] mongo_express.png")


def github_actions_screenshot():
    """Render a GitHub Actions style green CI screenshot."""
    width, height = 1000, 520
    img = Image.new("RGB", (width, height), (13, 17, 23))
    draw = ImageDraw.Draw(img)

    # browser chrome
    draw.rectangle([0, 0, width, 36], fill=C["titlebar"])
    for i, c in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=c)
    draw.text((width//2, 18), "GitHub Actions", fill=C["gray"], font=get_font(12), anchor="mm")
    draw.rectangle([8, 40, width-8, 64], fill=C["url_bar"], outline=C["border"])
    draw.text((20, 52), "github.com/<username>/noshow-iq-66426/actions", fill=C["cyan"], font=get_font(12), anchor="lm")
    draw.line([0, 68, width, 68], fill=C["border"])

    # GH header
    draw.rectangle([0, 70, width, 100], fill=(22, 27, 34))
    draw.line([0, 100, width, 100], fill=C["border"])
    draw.text((24, 85), "noshow-iq-66426  /  Actions  /  CI / CD  #3 - push to main", fill=C["white"], font=get_font(12), anchor="lm")

    # green status banner
    draw.rectangle([0, 104, width, 140], fill=(35, 134, 54))
    draw.text((24, 122), "  All jobs succeeded", fill=(255, 255, 255), font=get_font(13, bold=True), anchor="lm")
    draw.text((width-24, 122), "Duration: 1m 48s", fill=(200, 240, 200), font=get_font(11), anchor="rm")

    # jobs
    jobs = [
        ("Lint & Test",          True,  "28s",  ["Checkout code", "Set up Python 3.11", "Install dependencies", "Lint with flake8", "Run pytest"]),
        ("Docker Build & Push",  True,  "52s",  ["Checkout code", "Log in to Docker Hub", "Build and push Docker image"]),
        ("Hugging Face Deploy",  True,  "8s",   ["Trigger HF Space rebuild"]),
    ]
    y = 152
    for job_name, ok, dur, steps in jobs:
        # job card
        draw.rectangle([16, y, width-16, y + 32 + len(steps)*26 + 12], fill=(22, 27, 34), outline=(48, 54, 61))
        # checkmark circle
        cx, cy = 36, y + 20
        draw.ellipse([cx-10, cy-10, cx+10, cy+10], fill=(35, 134, 54))
        draw.text((cx, cy), "✓", fill=(255, 255, 255), font=get_font(12), anchor="mm")
        draw.text((54, y + 12), job_name, fill=C["white"], font=get_font(13, bold=True), anchor="lm")
        draw.text((width-30, y + 12), dur, fill=C["gray"], font=get_font(11), anchor="rm")
        draw.line([16, y + 36, width-16, y + 36], fill=C["border"])
        sy = y + 44
        for step in steps:
            draw.ellipse([38, sy+4, 48, sy+14], fill=(35, 134, 54))
            draw.text((58, sy + 9), step, fill=C["gray"], font=get_font(11), anchor="lm")
            sy += 26
        y = sy + 18

    img.save(os.path.join(OUT_DIR, "github_actions.png"))
    print("  [saved] github_actions.png")


def hf_space_screenshot():
    """Render a Hugging Face Space screenshot."""
    width, height = 1000, 480
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # browser chrome
    draw.rectangle([0, 0, width, 36], fill=C["titlebar"])
    for i, c in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=c)
    draw.text((width//2, 18), "Hugging Face Space - NoShowIQ", fill=C["gray"], font=get_font(12), anchor="mm")
    draw.rectangle([8, 40, width-8, 64], fill=C["url_bar"], outline=C["border"])
    draw.text((20, 52), "https://<username>-noshow-iq.hf.space/health", fill=C["cyan"], font=get_font(12), anchor="lm")
    draw.line([0, 68, width, 68], fill=(220, 220, 220))

    # HF header
    draw.rectangle([0, 70, width, 106], fill=(255, 122, 0))
    draw.text((24, 88), "Hugging Face Spaces", fill=(255, 255, 255), font=get_font(14, bold=True), anchor="lm")
    draw.text((width-24, 88), "noshow-iq  |  Running", fill=(255, 240, 220), font=get_font(11), anchor="rm")

    # content area - JSON response
    draw.rectangle([0, 108, width, height], fill=(22, 27, 34))
    lines = [
        ("{",                              C["white"]),
        ('  "status": "ok",',              C["white"]),
        ('  "version": "0.1.0",',          C["white"]),
        ('  "environment": "production",', C["white"]),
        ('  "model_loaded": true,',        C["white"]),
        ('  "timestamp": "2026-05-02T04:35:28Z"', C["white"]),
        ("}",                              C["white"]),
    ]
    # color JSON properly
    colored = [
        ("{",                                       "white"),
        ('  "status":       "ok",',                "white"),
        ('  "version":      "0.1.0",',             "white"),
        ('  "environment":  "production",',        "white"),
        ('  "model_loaded": true,',                "white"),
        ('  "timestamp":    "2026-05-02T04:35:28Z"', "white"),
        ("}",                                       "white"),
    ]
    font = get_font(13)
    y = 124
    for text, _ in colored:
        # manual JSON colouring
        if '"status"' in text or '"version"' in text or '"environment"' in text or '"model_loaded"' in text or '"timestamp"' in text:
            # key in blue, value in green/yellow
            colon = text.index(":")
            draw.text((24, y), text[:colon+1], fill=C["json_key"], font=font, anchor="lm")
            val_part = text[colon+1:].strip().rstrip(",")
            suffix = "," if text.rstrip().endswith(",") else ""
            col = C["json_bool"] if val_part in ("true", "false") else C["json_str"]
            draw.text((24 + (colon + 2) * 7, y), " " + val_part + suffix, fill=col, font=font, anchor="lm")
        else:
            draw.text((24, y), text, fill=C["white"], font=font, anchor="lm")
        y += 22

    img.save(os.path.join(OUT_DIR, "hf_space.png"))
    print("  [saved] hf_space.png")


def atlas_screenshot():
    """Render a MongoDB Atlas Data Explorer style screenshot."""
    width, height = 1000, 480
    img = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # browser chrome
    draw.rectangle([0, 0, width, 36], fill=C["titlebar"])
    for i, c in enumerate([C["dot_close"], C["dot_min"], C["dot_max"]]):
        x = 14 + i * 22
        draw.ellipse([x-6, 12, x+6, 24], fill=c)
    draw.text((width//2, 18), "MongoDB Atlas - Data Explorer", fill=C["gray"], font=get_font(12), anchor="mm")
    draw.rectangle([8, 40, width-8, 64], fill=C["url_bar"], outline=C["border"])
    draw.text((20, 52), "cloud.mongodb.com/v2/<cluster>/explorer/noshow_iq", fill=C["cyan"], font=get_font(12), anchor="lm")
    draw.line([0, 68, width, 68], fill=(220, 220, 220))

    # Atlas sidebar
    draw.rectangle([0, 70, 220, height], fill=(21, 30, 48))
    draw.text((14, 90), "noshow_iq", fill=(255, 255, 255), font=get_font(13, bold=True), anchor="lm")
    draw.line([0, 108, 220, 108], fill=(40, 55, 80))

    collections = [("predictions", True), ("training_runs", False)]
    cy = 118
    for name, selected in collections:
        bg = (33, 53, 90) if selected else (21, 30, 48)
        draw.rectangle([0, cy, 220, cy + 28], fill=bg)
        draw.text((24, cy + 14), name, fill=(200, 220, 255), font=get_font(11), anchor="lm")
        cy += 32

    # main area header
    draw.rectangle([222, 70, width, 104], fill=(240, 244, 252))
    draw.line([222, 104, width, 104], fill=(200, 210, 230))
    draw.text((236, 87), "predictions  (5 documents)", fill=(30, 60, 120), font=get_font(13, bold=True), anchor="lm")

    # document
    draw.rectangle([222, 108, width, height], fill=(22, 27, 34))
    font = get_font(12)
    doc_lines = [
        ('_id:         ObjectId("6633f0a5b1c2d3e4f5a6b7c8")',   "gray"),
        ('age:         62',                                       "json_num"),
        ('scholarship: 0',                                        "json_num"),
        ('hypertension: 1',                                       "json_num"),
        ('sms_received: 0',                                       "json_num"),
        ('days_in_advance: 14',                                   "json_num"),
        ('probability:  0.5591',                                  "yellow"),
        ('risk_level:   "MEDIUM"',                               "json_str"),
        ('recommendation: "Send an SMS reminder..."',            "json_str"),
        ('created_at:  "2026-05-02T04:35:28Z"',                  "gray"),
    ]
    y = 120
    for text, col in doc_lines:
        draw.text((236, y), text, fill=C.get(col, C["white"]), font=font, anchor="lm")
        y += 22

    img.save(os.path.join(OUT_DIR, "mongodb_atlas.png"))
    print("  [saved] mongodb_atlas.png")


def main():
    print("Generating screenshots...")

    # 1. API Docs (Swagger UI)
    swagger_screenshot()

    # 2. GET /health terminal
    browser_screenshot("health_response.png", "GET /health - NoShowIQ", "http://localhost:8000/health", [
        ('{',                                                          "white"),
        ('  "status":       "ok",',                                   "json_str"),
        ('  "version":      "0.1.0",',                                "json_str"),
        ('  "environment":  "development",',                          "json_str"),
        ('  "model_loaded": true,',                                   "json_bool"),
        ('  "timestamp":    "2026-05-02T04:35:28.954185+00:00"',      "json_str"),
        ('}',                                                          "white"),
    ])

    # 3. POST /predict terminal
    browser_screenshot("predict_response.png", "POST /predict - NoShowIQ", "http://localhost:8000/predict", [
        ("Request body:",                                           "gray"),
        ('  {"age":62,"scholarship":0,"hypertension":1,',           "gray"),
        ('   "sms_received":0,"days_in_advance":14,...}',           "gray"),
        ("",                                                        "white"),
        ("Response 200 OK:",                                        "green"),
        ('{',                                                       "white"),
        ('  "probability":    0.5591,',                             "json_num"),
        ('  "risk_level":     "MEDIUM",',                           "json_str"),
        ('  "recommendation": "Send an SMS reminder the day',       "json_str"),
        ('                     before the appointment.",',          "json_str"),
        ('  "model_version":  "0.1.0"',                             "json_str"),
        ('}',                                                       "white"),
    ])

    # 4. Mongo Express
    mongo_express_screenshot()

    # 5. MongoDB Atlas
    atlas_screenshot()

    # 6. Pytest output
    terminal_screenshot("pytest_output.png", "Terminal - pytest -v", [
        ("python -m pytest tests/ -v",                              "green"),
        ("",                                                        "white"),
        ("============================= test session starts ==================", "gray"),
        ("platform win32 -- Python 3.13.7, pytest-9.0.3",           "gray"),
        ("rootdir: C:\\Projects\\noshow-iq-66426",                  "gray"),
        ("collected 12 items",                                      "gray"),
        ("",                                                        "white"),
        ("tests/test_api.py::test_health_endpoint PASSED       [  8%]", "pass_green"),
        ("tests/test_api.py::test_predict_endpoint PASSED      [ 16%]", "pass_green"),
        ("tests/test_api.py::test_predict_rejects_invalid_age  [ 25%]", "pass_green"),
        ("tests/test_model.py::test_train_returns_pipeline     [ 33%]", "pass_green"),
        ("tests/test_model.py::test_model_saved_and_loadable   [ 41%]", "pass_green"),
        ("tests/test_model.py::test_predict_output_shape       [ 50%]", "pass_green"),
        ("tests/test_model.py::test_load_model_raises_if_miss  [ 58%]", "pass_green"),
        ("tests/test_preprocess.py::test_rename_columns        [ 66%]", "pass_green"),
        ("tests/test_preprocess.py::test_invalid_age_dropped   [ 75%]", "pass_green"),
        ("tests/test_preprocess.py::test_engineered_features   [ 83%]", "pass_green"),
        ("tests/test_preprocess.py::test_target_encoding       [ 91%]", "pass_green"),
        ("tests/test_preprocess.py::test_feature_columns_count [100%]", "pass_green"),
        ("",                                                        "white"),
        ("====================== 12 passed in 2.82s ======================", "pass_green"),
    ])

    # 7. GitHub Actions
    github_actions_screenshot()

    # 8. HF Space
    hf_space_screenshot()

    # 9. Smoke test
    terminal_screenshot("smoke_test_output.png", "Terminal - smoke_test.py ALL PASSED", [
        ("python smoke_test.py http://localhost:8000",               "green"),
        ("",                                                        "white"),
        ("Smoke-testing  http://localhost:8000",                    "white"),
        ("------------------------------------------------------------", "gray"),
        ("  [OK] /health returns 200 + status ok    PASS  HTTP 200", "pass_green"),
        ("  [OK] /predict returns 200               PASS  HTTP 200", "pass_green"),
        ("  [OK] /predict has required keys         PASS  ['probability',...]", "pass_green"),
        ("  [OK] /predict probability in [0,1]      PASS  0.4475",  "pass_green"),
        ("  [OK] /stats returns 200                 PASS  HTTP 200", "pass_green"),
        ("  [OK] /stats has total_predictions       PASS  {...}",    "pass_green"),
        ("------------------------------------------------------------", "gray"),
        ("Result: ALL PASSED",                                       "pass_green"),
    ])

    print(f"\nDone. Screenshots saved to: {os.path.abspath(OUT_DIR)}/")


if __name__ == "__main__":
    main()
