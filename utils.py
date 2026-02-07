import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime, timedelta
import random, string

DATA_DIR = Path(__file__).resolve().parent / "data"

def now_iso():
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"

def gen_id(prefix: str, n: int = 8) -> str:
    return prefix + "".join(random.choice(string.digits) for _ in range(n))

def load_csv(name: str) -> pd.DataFrame:
    path = DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)

def save_csv(df: pd.DataFrame, name: str) -> None:
    (DATA_DIR / name).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(DATA_DIR / name, index=False)

def log_event(actor: str, event_type: str, entity_type: str, entity_id: str, details: dict | None = None) -> None:
    df = load_csv("events.csv")
    row = {
        "event_id": gen_id("EV-", 10),
        "timestamp": now_iso(),
        "actor": actor,
        "event_type": event_type,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details_json": json.dumps(details or {}, ensure_ascii=False),
    }
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    save_csv(df, "events.csv")

def compute_coldchain_score(temp_avg_c: float, temp_breaches: int, disputes: int, spoiled: int) -> int:
    score = 100
    if pd.notna(temp_avg_c):
        if temp_avg_c > 6: score -= min(40, (temp_avg_c-6)*10)
        if temp_avg_c < 1: score -= min(20, (1-temp_avg_c)*10)
    score -= min(40, temp_breaches*8)
    score -= min(20, disputes*5)
    score -= min(50, spoiled*25)
    return int(max(0, min(100, score)))

def dwr_status_guard(receipt_status: str, action: str):
    if action == "list_for_sale" and receipt_status in ["pledged","advance_active","quarantined","expired","released","sold","disputed","pending_sale"]:
        return False, f"Cannot list receipt in status: {receipt_status}"
    if action == "create_lien" and receipt_status in ["sold","released","expired","quarantined","disputed"]:
        return False, f"Cannot lien receipt in status: {receipt_status}"
    if action == "release" and receipt_status in ["pledged","advance_active","quarantined","expired","disputed"]:
        return False, f"Cannot release in status: {receipt_status}"
    return True, ""

def make_qr_payload(receipt_id: str, lot_id: str, owner_entity_id: str, custodian_id: str) -> str:
    return f"receipt_id={receipt_id}&lot_id={lot_id}&owner={owner_entity_id}&custodian={custodian_id}"

def generate_receipt_pdf(receipt: dict, lot: dict, owner: dict, custodian: dict) -> bytes:
    from io import BytesIO
    from reportlab.lib.pagesizes import LETTER
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    import qrcode
    from PIL import Image

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=LETTER)
    w, h = LETTER
    c.setFont("Helvetica-Bold", 16)
    c.drawString(0.8*inch, h-0.9*inch, "BON DE DÉPÔT NUMÉRIQUE (BDN) — LAIT / PRODUITS LAITIERS")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey)
    c.drawString(0.8*inch, h-1.1*inch, "Prototype Mali Dairy DWR (document de démonstration)")
    c.setFillColor(colors.black)

    c.setLineWidth(1)
    c.rect(0.75*inch, h-5.1*inch, w-1.5*inch, 3.6*inch, stroke=1, fill=0)

    x0 = 0.9*inch
    y0 = h-1.6*inch
    c.setFont("Helvetica-Bold", 11)
    c.drawString(x0, y0, f"BDN ID: {receipt.get('receipt_id','')}")
    c.setFont("Helvetica", 10)
    lines = [
        f"Émis le: {receipt.get('issued_at','')}",
        f"Expire le: {receipt.get('expiry_ts','')}",
        "",
        f"Propriétaire: {owner.get('name','')} ({owner.get('entity_id','')})",
        f"Tél: {owner.get('phone','')}",
        "",
        f"Dépositaire: {custodian.get('name','')} ({custodian.get('custodian_id','')})",
        f"Région: {custodian.get('region','')}",
        "",
        f"Produit: {lot.get('product_type','')}",
        f"Quantité: {lot.get('quantity_liters','')} L",
        f"Matière grasse: {lot.get('fat_pct','')} %",
        f"Test antibiotiques: {lot.get('antibiotic_test','')}",
        f"Température moyenne: {lot.get('temp_avg_c','')} °C",
        "",
        f"Statut: {receipt.get('status','')}",
        f"Sûreté active: {receipt.get('lien_active','')}",
    ]
    y = y0 - 0.25*inch
    for ln in lines:
        c.drawString(x0, y, ln)
        y -= 0.18*inch

    qr_payload = receipt.get("qr_payload","")
    if qr_payload:
        qr_img = qrcode.make(qr_payload)
        img_buf = BytesIO()
        qr_img.save(img_buf, format="PNG")
        img_buf.seek(0)
        pil = Image.open(img_buf)
        tmp = BytesIO()
        pil.save(tmp, format="PNG")
        tmp.seek(0)
        c.drawInlineImage(tmp, w-2.6*inch, h-3.9*inch, 1.6*inch, 1.6*inch)

    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawString(0.8*inch, 0.8*inch, "NB: Prototype. La validité légale dépend du cadre réglementaire adopté par l'État.")
    c.setFillColor(colors.black)
    c.showPage()
    c.save()
    pdf = buf.getvalue()
    buf.close()
    return pdf
