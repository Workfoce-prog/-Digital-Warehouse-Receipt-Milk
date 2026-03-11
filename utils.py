import os
import json
import uuid
from io import BytesIO
from datetime import datetime

import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def csv_path(file_name: str) -> str:
    return os.path.join(BASE_DIR, file_name)

def load_csv(file_name: str) -> pd.DataFrame:
    path = csv_path(file_name)
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def save_csv(df: pd.DataFrame, file_name: str) -> None:
    path = csv_path(file_name)
    df.to_csv(path, index=False)

def load_csv_schema(file_name, schema, seed_df=None):
    path = csv_path(file_name)

    if not os.path.exists(path):
        df = seed_df.copy() if seed_df is not None else pd.DataFrame(columns=schema)
        df.to_csv(path, index=False)
        return df

    df = pd.read_csv(path)

    for col in schema:
        if col not in df.columns:
            df[col] = None

    return df[schema]

def gen_id(prefix: str) -> str:
    stamp = datetime.utcnow().strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{stamp}-{short}"

def log_event(username, event_type, object_type, object_id, details=None, file_name="events.csv"):
    path = csv_path(file_name)

    row = pd.DataFrame([{
        "event_ts": datetime.utcnow().isoformat(),
        "username": username,
        "event_type": event_type,
        "object_type": object_type,
        "object_id": object_id,
        "details_json": json.dumps(details or {}, ensure_ascii=False),
    }])

    if os.path.exists(path):
        try:
            existing = pd.read_csv(path)
            out = pd.concat([existing, row], ignore_index=True)
        except Exception:
            out = row
    else:
        out = row

    out.to_csv(path, index=False)

def compute_coldchain_score(temp_avg_c, temp_breach_count):
    try:
        temp_avg_c = float(temp_avg_c)
    except Exception:
        temp_avg_c = None

    try:
        temp_breach_count = int(temp_breach_count)
    except Exception:
        temp_breach_count = 0

    score = 100

    if temp_avg_c is not None:
        if temp_avg_c < 2 or temp_avg_c > 6:
            score -= 25
        elif temp_avg_c < 3 or temp_avg_c > 5:
            score -= 10

    score -= min(temp_breach_count * 10, 40)
    score = max(0, min(100, score))

    if score >= 85:
        status = "Green"
    elif score >= 60:
        status = "Amber"
    else:
        status = "Red"

    return {"score": score, "status": status}

def make_qr_payload(receipt_id, lot_id, owner_entity_id, custodian_id, issued_at=None, expiry_ts=None, status="active"):
    payload = {
        "receipt_id": receipt_id,
        "lot_id": lot_id,
        "owner_entity_id": owner_entity_id,
        "custodian_id": custodian_id,
        "issued_at": issued_at or datetime.utcnow().isoformat(),
        "expiry_ts": expiry_ts,
        "status": status,
    }
    return json.dumps(payload, ensure_ascii=False)

def _wrap_text(text: str, width: int = 90):
    text = str(text or "")
    return [text[i:i + width] for i in range(0, len(text), width)] or [""]

def generate_receipt_pdf(receipt_row: dict, lot_row=None) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(50, y, "Mali Dairy Digital Warehouse Receipt (DWR / BDN)")
    y -= 30

    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Issued at: {receipt_row.get('issued_at', '')}")
    y -= 20
    pdf.drawString(50, y, f"Receipt ID: {receipt_row.get('receipt_id', '')}")
    y -= 20
    pdf.drawString(50, y, f"Lot ID: {receipt_row.get('lot_id', '')}")
    y -= 20
    pdf.drawString(50, y, f"Owner Entity: {receipt_row.get('owner_entity_id', '')}")
    y -= 20
    pdf.drawString(50, y, f"Custodian: {receipt_row.get('custodian_id', '')}")
    y -= 20
    pdf.drawString(50, y, f"Status: {receipt_row.get('status', '')}")
    y -= 20
    pdf.drawString(50, y, f"Expiry: {receipt_row.get('expiry_ts', '')}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "QR Payload")
    y -= 18

    pdf.setFont("Helvetica", 9)
    for line in _wrap_text(receipt_row.get("qr_payload", ""), 90):
        pdf.drawString(50, y, line)
        y -= 14
        if y < 80:
            pdf.showPage()
            pdf.setFont("Helvetica", 9)
            y = height - 50

    if lot_row:
        y -= 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(50, y, "Lot Details")
        y -= 18

        pdf.setFont("Helvetica", 10)
        fields = [
            ("Product Type", lot_row.get("product_type", "")),
            ("Quantity Liters", lot_row.get("quantity_liters", "")),
            ("Fat %", lot_row.get("fat_pct", "")),
            ("SNF %", lot_row.get("snf_pct", "")),
            ("Acidity", lot_row.get("acidity", "")),
            ("Antibiotic Test", lot_row.get("antibiotic_test", "")),
            ("Bacterial Score", lot_row.get("bacterial_score", "")),
            ("Avg Temp C", lot_row.get("temp_avg_c", "")),
            ("Quality Grade", lot_row.get("quality_grade", "")),
            ("Lot Status", lot_row.get("status", "")),
        ]

        for label, value in fields:
            pdf.drawString(50, y, f"{label}: {value}")
            y -= 18
            if y < 80:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 50

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.read()

