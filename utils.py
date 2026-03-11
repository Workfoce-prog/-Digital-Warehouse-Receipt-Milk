import os
import json
import pandas as pd
from datetime import datetime
import uuid


def gen_id(prefix: str) -> str:
    """
    Generate a readable unique ID like LOT-20260311-AB12CD
    """
    stamp = datetime.utcnow().strftime("%Y%m%d")
    short = uuid.uuid4().hex[:6].upper()
    return f"{prefix}-{stamp}-{short}"

# --------------------------------------------------
# Base path
# --------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------
# Generic CSV helpers
# --------------------------------------------------
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

# --------------------------------------------------
# Schema-aware CSV loader
# --------------------------------------------------
def load_csv_schema(file_name, schema, seed_df=None):
    path = csv_path(file_name)

    if not os.path.exists(path):
        if seed_df is None:
            df = pd.DataFrame(columns=schema)
        else:
            df = seed_df.copy()
        df.to_csv(path, index=False)
        return df

    df = pd.read_csv(path)

    for col in schema:
        if col not in df.columns:
            df[col] = None

    return df[schema]

# --------------------------------------------------
# Event logging
# --------------------------------------------------
def log_event(username, event_type, object_type, object_id, details=None, file_name="events.csv"):
    path = csv_path(file_name)

    details_json = json.dumps(details or {}, ensure_ascii=False)

    row = pd.DataFrame([{
        "event_ts": datetime.utcnow().isoformat(),
        "username": username,
        "event_type": event_type,
        "object_type": object_type,
        "object_id": object_id,
        "details_json": details_json,
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

# --------------------------------------------------
# Optional cold-chain scoring helper
# --------------------------------------------------
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
