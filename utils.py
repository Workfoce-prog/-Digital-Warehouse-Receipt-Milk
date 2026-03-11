import pandas as pd
import os
import json
import uuid
from datetime import datetime


def compute_coldchain_score(temp_avg_c, temp_breach_count, dispute_count=0, spoiled_count=0):
    """
    Returns a dict with score and status.
    """

    try:
        temp_avg_c = float(temp_avg_c)
    except Exception:
        temp_avg_c = None

    try:
        temp_breach_count = int(temp_breach_count)
    except Exception:
        temp_breach_count = 0

    try:
        dispute_count = int(dispute_count)
    except Exception:
        dispute_count = 0

    try:
        spoiled_count = int(spoiled_count)
    except Exception:
        spoiled_count = 0

    score = 100

    # Temperature penalty
    if temp_avg_c is not None:
        if temp_avg_c < 2 or temp_avg_c > 6:
            score -= 25
        elif temp_avg_c < 3 or temp_avg_c > 5:
            score -= 10

    # Breach penalty
    score -= min(temp_breach_count * 10, 40)

    # Dispute penalty
    score -= min(dispute_count * 8, 24)

    # Spoilage penalty
    score -= min(spoiled_count * 20, 40)

    score = max(0, min(100, score))

    if score >= 85:
        status = "Green"
    elif score >= 60:
        status = "Amber"
    else:
        status = "Red"

    return {"score": score, "status": status}


