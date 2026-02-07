import os
import pandas as pd
from datetime import datetime
from datetime import datetime
import random
import string
import json
from datetime import datetime

def compute_coldchain_score(
    temp_avg_c: float | int | None = None,
    temp_min_c: float | int | None = None,
    temp_max_c: float | int | None = None,
    breach_count: int | None = None,
    max_allowed_c: float = 4.0,
    min_allowed_c: float = 0.0,
) -> dict:
    """
    Returns a simple cold-chain SLA score + category.
    Score is 0–100 (higher is better).
    - Penalizes temperature breaches and excursions beyond allowed range.
    - Designed to be transparent and easy to audit.
    """

    def fnum(x):
        try:
            return float(x)
        except Exception:
            return None

    temp_avg_c = fnum(temp_avg_c)
    temp_min_c = fnum(temp_min_c)
    temp_max_c = fnum(temp_max_c)
    try:
        breach_count = int(breach_count) if breach_count is not None else 0
    except Exception:
        breach_count = 0

    # Excursion penalties
    excursion_hi = 0.0
    excursion_lo = 0.0

    if temp_max_c is not None and temp_max_c > max_allowed_c:
        excursion_hi = temp_max_c - max_allowed_c
    if temp_min_c is not None and temp_min_c < min_allowed_c:
        excursion_lo = min_allowed_c - temp_min_c

    # Base score
    score = 100.0

    # Penalize breaches heavily (each breach reduces score)
    score -= breach_count * 8.0

    # Penalize excursions (each degree outside range reduces score)
    score -= excursion_hi * 12.0
    score -= excursion_lo * 12.0

    # Small penalty if average is outside allowed range
    if temp_avg_c is not None:
        if temp_avg_c > max_allowed_c:
            score -= (temp_avg_c - max_allowed_c) * 6.0
        if temp_avg_c < min_allowed_c:
            score -= (min_allowed_c - temp_avg_c) * 6.0

    # Clamp 0–100
    score = max(0.0, min(100.0, score))

    # Category
    if score >= 90:
        category = "Excellent"
        rag = "Green"
    elif score >= 75:
        category = "Good"
        rag = "Green"
    elif score >= 60:
        category = "Watch"
        rag = "Amber"
    else:
        category = "Breach"
        rag = "Red"

    return {
        "score": round(score, 1),
        "category": category,
        "rag": rag,
        "inputs": {
            "temp_avg_c": temp_avg_c,
            "temp_min_c": temp_min_c,
            "temp_max_c": temp_max_c,
            "breach_count": breach_count,
            "min_allowed_c": min_allowed_c,
            "max_allowed_c": max_allowed_c,
        },
        "components": {
            "excursion_hi": round(excursion_hi, 2),
            "excursion_lo": round(excursion_lo, 2),
        },
    }


def make_qr_payload(receipt_row: dict) -> str:
    """
    Minimal QR payload (string). Keep it short + stable.
    You can later replace with a signed payload (HMAC) if desired.
    """
    payload = {
        "type": "DWR",
        "receipt_id": str(receipt_row.get("receipt_id", "")),
        "lot_id": str(receipt_row.get("lot_id", "")),
        "owner_entity_id": str(receipt_row.get("owner_entity_id", "")),
        "custodian_id": str(receipt_row.get("custodian_id", "")),
        "status": str(receipt_row.get("status", "")),
        "issued_at": str(receipt_row.get("issued_at", "")),
        "expiry_ts": str(receipt_row.get("expiry_ts", "")),
    }
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


def generate_receipt_pdf(receipt_row: dict, lot_row: dict | None = None, out_path: str | None = None) -> str:
    """
    Create a simple PDF receipt using reportlab.
    Returns the file path written.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    if out_path is None:
        rid = str(receipt_row.get("receipt_id", "RECEIPT"))
        out_path = f"receipts/{rid}.pdf"

    # Ensure folder exists
    import os
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    c = canvas.Canvas(out_path, pagesize=letter)
    width, height = letter

    y = height - 60
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Mali Dairy Digital Warehouse Receipt (DWR/BDN)")
    y -= 25

    c.setFont("Helvetica", 11)
    def line(label, value):
        nonlocal y
        c.drawString(50, y, f"{label}: {value}")
        y -= 16

    line("Receipt ID", receipt_row.get("receipt_id", ""))
    line("Issued At", receipt_row.get("issued_at", ""))
    line("Expiry", receipt_row.get("expiry_ts", ""))
    line("Status", receipt_row.get("status", ""))
    line("Owner Entity", receipt_row.get("owner_entity_id", ""))
    line("Custodian", receipt_row.get("custodian_id", ""))
    line("Lien Active", receipt_row.get("lien_active", ""))
    line("Lien Holder", receipt_row.get("lien_holder_id", ""))

    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Lot details")
    y -= 18
    c.setFont("Helvetica", 11)

    if lot_row:
        line("Lot ID", lot_row.get("lot_id", ""))
        line("Product", lot_row.get("product_type", ""))
        line("Quantity (L)", lot_row.get("quantity_liters", ""))
        line("Quality Grade", lot_row.get("quality_grade", ""))
        line("Temp Avg (C)", lot_row.get("temp_avg_c", ""))
        line("Temp Breaches", lot_row.get("temp_breach_count", ""))
    else:
        line("Lot", "(not provided)")

    # QR payload printed (simple)
    y -= 8
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "QR Payload")
    y -= 16
    c.setFont("Helvetica", 8)
    qr_payload = receipt_row.get("qr_payload", "")
    # wrap payload
    max_chars = 95
    for i in range(0, len(qr_payload), max_chars):
        c.drawString(50, y, qr_payload[i:i+max_chars])
        y -= 10
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 8)

    c.showPage()
    c.save()
    return out_path

def gen_id(prefix: str) -> str:
    """
    Generate a reasonably unique ID like LOT-20260206-142233-7Q3K
    """
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{prefix}-{ts}-{rand}"


DATA_DIR = "data"

def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)

def _path(filename: str) -> str:
    _ensure_data_dir()
    return os.path.join(DATA_DIR, filename)

def load_csv(filename: str, schema=None, seed_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Simple CSV loader (optionally enforce schema)."""
    fp = _path(filename)
    if os.path.exists(fp):
        df = pd.read_csv(fp, dtype=str)  # keep everything safe as text by default
    else:
        df = seed_df.copy() if seed_df is not None else pd.DataFrame()

    if schema is not None:
        for col in schema:
            if col not in df.columns:
                df[col] = ""
        df = df[schema]  # order columns
    return df

def save_csv(filename: str, df: pd.DataFrame) -> None:
    fp = _path(filename)
    df.to_csv(fp, index=False)

def load_csv_schema(filename: str, schema, seed_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Your existing pattern: load + self-heal schema + seed if missing."""
    df = load_csv(filename, schema=schema, seed_df=seed_df)
    # persist immediately so the app "self-heals" broken/missing files
    save_csv(filename, df)
    return df

def log_event(event_type: str, actor: str, details: str = "", entity_id: str = "", ref_id: str = "") -> None:
    """Append-only audit log."""
    schema = ["ts", "event_type", "actor", "entity_id", "ref_id", "details"]
    fp = "audit_log.csv"
    df = load_csv(fp, schema=schema, seed_df=pd.DataFrame(columns=schema))

    row = {
        "ts": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "event_type": event_type,
        "actor": actor,
        "entity_id": entity_id,
        "ref_id": ref_id,
        "details": details,
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_csv(fp, df)

