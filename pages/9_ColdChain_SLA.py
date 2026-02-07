import os, sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import numpy as np

from utils import load_csv, save_csv, compute_coldchain_score, log_event
from auth import require_login

user = require_login()

st.set_page_config(page_title="Cold Chain SLA", layout="wide")
st.title("Cold Chain SLA Dashboard (Pilot)")

if user["role"] not in ["platform", "government"]:
    st.error("Access denied.")
    st.stop()

custodians = load_csv("custodians.csv")
lots = load_csv("dairy_lots.csv")
disputes = load_csv("disputes.csv")
sla = load_csv("sla_coldchain.csv")

month = pd.Timestamp.today().strftime("%Y-%m")

rows = []

for cid in custodians["custodian_id"].tolist():
    l = lots[lots["custodian_id"] == cid]

    lots_received = int(l["lot_id"].nunique()) if not l.empty else 0
    avg_temp = (
        float(np.nanmean(pd.to_numeric(l["temp_avg_c"], errors="coerce")))
        if lots_received > 0
        else np.nan
    )
    breaches = (
        int(pd.to_numeric(l["temp_breach_count"], errors="coerce").fillna(0).sum())
        if lots_received > 0
        else 0
    )
    spoiled = int((l["status"] == "spoiled").sum()) if lots_received > 0 else 0

    rec = load_csv("dwr_receipts.csv")
    rids = rec[rec["custodian_id"] == cid]["receipt_id"].tolist() if not rec.empty else []
    disp = disputes[disputes["receipt_id"].isin(rids)] if rids else pd.DataFrame()
    dispute_rate = (len(disp) / max(1, len(rids))) if rids else 0.0

    # --- compute score ---
    score = compute_coldchain_score(avg_temp, breaches, len(disp), spoiled)

    # --- make score numeric (robust) ---
    score_val = score

    if isinstance(score_val, dict):
        score_val = score_val.get("score")

    # If score is a string like "72" or "72%" or ""
    if isinstance(score_val, str):
        s = score_val.strip().replace("%", "")
        score_val = float(s) if s else None

    # If score is still missing, default to NaN (don't crash the whole page)
    if score_val is None:
        score_val = np.nan

    # Ensure numeric float if possible
    try:
        score_val = float(score_val)
    except Exception:
        score_val = np.nan

    # --- penalty logic ---
    penalty = "none"
    if np.isnan(score_val):
        penalty = "unknown"
    elif score_val < 40:
        penalty = "suspend_review"
    elif score_val < 60:
        penalty = "warning"
    else:
        penalty = "ok"

    rows.append({
        "month": month,
        "custodian_id": cid,
        "lots_received": lots_received,
        "avg_temp_c": None if np.isnan(avg_temp) else round(avg_temp, 2),
        "temp_breaches": breaches,
        "spoiled_lots": spoiled,
        "dispute_rate": round(dispute_rate, 3),
        "sla_score": score_val,          # numeric score for sorting
        "penalty_status": penalty
    })

out = pd.DataFrame(rows).merge(
    custodians[["custodian_id", "name", "region", "license_status"]],
    on="custodian_id",
    how="left"
)

st.dataframe(out.sort_values("sla_score"), use_container_width=True)

if st.button("Save SLA snapshot"):
    sla_new = pd.DataFrame(rows)
    if not sla.empty and "month" in sla.columns:
        sla = pd.concat([sla[sla["month"] != month], sla_new], ignore_index=True)
    else:
        sla = sla_new

    save_csv(sla, "sla_coldchain.csv")
    log_event(user["username"], "sla_saved", "sla", month, {"rows": len(rows)})
    st.success("Saved.")
