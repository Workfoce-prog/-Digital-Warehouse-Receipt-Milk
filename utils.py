import os
import pandas as pd
from datetime import datetime

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

