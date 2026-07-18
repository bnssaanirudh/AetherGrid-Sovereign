"""
temporal.py
-----------
Timezone-aware normalization of event timestamps to UTC.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple


def normalize_timestamp_to_utc(ts_str: str) -> Tuple[datetime, str]:
    """
    Parses datetime string, extracts original offset, and returns UTC datetime object
    with the source offset metadata.
    """
    # Replace Z with UTC offset representation
    normalized = ts_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
    except ValueError:
        # Fallback to current time if unparseable
        dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    
    # Store source timezone/offset details as metadata string
    source_offset = str(dt.tzinfo) if dt.tzinfo else "+00:00"
    dt_utc = dt.astimezone(timezone.utc)
    return dt_utc, source_offset
