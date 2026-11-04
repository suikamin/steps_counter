# core/magage_data.py
"""ユーザーデータ（日別歩数記録および身長設定）の永続化を担当するモジュール。"""

import json
from pathlib import Path
from typing import Any, Dict

DATA_FILE = Path(__file__).resolve().parent / "data.json"
DEFAULT_HEIGHT: float = 170.0


def load_data() -> Dict[str, Any]:
    """`data.json` から歩数記録と身長データを読み込む。"""
    if not DATA_FILE.exists():
        return {"records": {}, "height": DEFAULT_HEIGHT}
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            raw_data = json.load(f)
    except Exception:
        return {"records": {}, "height": DEFAULT_HEIGHT}

    records: Dict[str, int] = {}
    if isinstance(raw_data, dict) and isinstance(raw_data.get("records"), dict):
        for k, v in raw_data["records"].items():
            if isinstance(v, (int, float)):
                records[str(k)] = int(v)

    height = DEFAULT_HEIGHT
    if isinstance(raw_data, dict) and isinstance(raw_data.get("height"), (int, float)):
        if raw_data["height"] > 0:
            height = float(raw_data["height"])

    return {"records": records, "height": height}


def save_data(data: Dict[str, Any]) -> bool:
    """歩数記録と身長データを `data.json` へアトミックに保存する。"""
    raw_records = data.get("records", {})
    records: Dict[str, int] = {}
    if isinstance(raw_records, dict):
        for k, v in raw_records.items():
            if isinstance(v, (int, float)):
                records[str(k)] = int(v)

    raw_height = data.get("height", DEFAULT_HEIGHT)
    height = (
        float(raw_height)
        if isinstance(raw_height, (int, float)) and raw_height > 0
        else DEFAULT_HEIGHT
    )

    normalized = {"records": records, "height": height}

    temp_file = DATA_FILE.with_suffix(".tmp")
    try:
        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(normalized, f, ensure_ascii=False, indent=2)
        temp_file.replace(DATA_FILE)
        return True
    except Exception:
        if temp_file.exists():
            try:
                temp_file.unlink()
            except OSError:
                pass
        return False
