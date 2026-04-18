import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, f1_score, precision_score, recall_score


FEATURE_PREFIX = "feature__"
PREDICTION_LOG_PATH = Path(os.getenv("PREDICTION_LOG_PATH", "logs/predictions.jsonl"))
FEEDBACK_LOG_PATH = Path(os.getenv("FEEDBACK_LOG_PATH", "logs/prediction_feedback.jsonl"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, np.generic):
        return value.item()

    if isinstance(value, np.ndarray):
        return [_json_safe(v) for v in value.tolist()]

    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]

    if pd.isna(value):
        return None

    return value


def ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    ensure_parent_dir(path)
    with path.open("a", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_json_safe(record), ensure_ascii=True) + "\n")


def flatten_feature_record(record: dict[str, Any], prefix: str = FEATURE_PREFIX) -> dict[str, Any]:
    flattened = {}
    for key, value in record.items():
        flattened[f"{prefix}{key}"] = _json_safe(value)
    return flattened


def build_prediction_events(
    records: list[dict[str, Any]],
    probabilities: np.ndarray,
    predictions: np.ndarray,
    *,
    endpoint: str,
    model_name: str,
    threshold: float | None,
    request_id: str | None = None,
    model_ready: bool = True,
) -> list[dict[str, Any]]:
    request_id = request_id or uuid.uuid4().hex
    event_timestamp = utc_now_iso()
    events: list[dict[str, Any]] = []

    for index, record in enumerate(records):
        prediction_id = f"{request_id}:{index}"
        event = {
            "event_type": "prediction",
            "event_timestamp": event_timestamp,
            "endpoint": endpoint,
            "request_id": request_id,
            "prediction_id": prediction_id,
            "record_index": index,
            "model_name": model_name,
            "model_ready": model_ready,
            "threshold": float(threshold) if threshold is not None else None,
            "fraud_probability": float(probabilities[index]),
            "prediction": int(predictions[index]),
        }
        event.update(flatten_feature_record(record))
        events.append(event)

    return events


def build_feedback_events(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events = []
    logged_at = utc_now_iso()

    for item in items:
        event = {
            "event_type": "feedback",
            "event_timestamp": logged_at,
            "prediction_id": str(item["prediction_id"]),
            "request_id": str(item.get("request_id") or "").strip() or None,
            "actual_label": int(item["actual_label"]),
            "observed_at": item.get("observed_at") or logged_at,
            "feedback_source": item.get("feedback_source") or "api",
            "notes": item.get("notes"),
        }
        events.append(event)

    return events


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    source = Path(path)
    if not source.exists():
        return []

    rows: list[dict[str, Any]] = []
    for line in source.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def load_prediction_dataframe(path: str | Path = PREDICTION_LOG_PATH, endpoint: str | None = None) -> pd.DataFrame:
    rows = load_jsonl(path)
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if endpoint is not None and "endpoint" in df.columns:
        df = df[df["endpoint"] == endpoint].copy()
    return df.reset_index(drop=True)


def load_feedback_dataframe(path: str | Path = FEEDBACK_LOG_PATH) -> pd.DataFrame:
    rows = load_jsonl(path)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).reset_index(drop=True)


def extract_feature_frame(df: pd.DataFrame, prefix: str = FEATURE_PREFIX) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    feature_columns = [column for column in df.columns if column.startswith(prefix)]
    extracted = df[feature_columns].copy()
    extracted.columns = [column[len(prefix):] for column in feature_columns]
    return extracted


def compute_feedback_metrics(
    prediction_df: pd.DataFrame,
    feedback_df: pd.DataFrame,
) -> dict[str, Any]:
    if prediction_df.empty or feedback_df.empty:
        return {
            "records_with_feedback": 0,
            "f1": None,
            "precision": None,
            "recall": None,
            "auprc": None,
        }

    merged = prediction_df.merge(feedback_df, on="prediction_id", how="inner", suffixes=("", "_feedback"))
    if merged.empty:
        return {
            "records_with_feedback": 0,
            "f1": None,
            "precision": None,
            "recall": None,
            "auprc": None,
        }

    y_true = merged["actual_label"].astype(int).to_numpy()
    y_pred = merged["prediction"].astype(int).to_numpy()

    summary = {
        "records_with_feedback": int(len(merged)),
        "positive_rate": float(y_true.mean()) if len(y_true) else None,
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "prediction_log_path": str(PREDICTION_LOG_PATH),
        "feedback_log_path": str(FEEDBACK_LOG_PATH),
    }

    if "fraud_probability" in merged.columns and len(np.unique(y_true)) > 1:
        summary["auprc"] = float(average_precision_score(y_true, merged["fraud_probability"].astype(float)))
    else:
        summary["auprc"] = None

    if "event_timestamp" in merged.columns:
        summary["prediction_window_start"] = str(merged["event_timestamp"].min())
        summary["prediction_window_end"] = str(merged["event_timestamp"].max())

    return summary


def evaluate_monitoring_status(
    performance_summary: dict[str, Any] | None = None,
    drift_summary: dict[str, Any] | None = None,
    *,
    performance_f1_threshold: float | None = None,
    drift_share_threshold: float | None = None,
) -> dict[str, Any]:
    performance_summary = performance_summary or {}
    drift_summary = drift_summary or {}

    f1_value = performance_summary.get("f1")
    drift_share = drift_summary.get("drifted_columns_share")
    drift_detected = bool(drift_summary.get("dataset_drift_detected", False))

    performance_below_threshold = (
        performance_f1_threshold is not None
        and f1_value is not None
        and float(f1_value) < float(performance_f1_threshold)
    )
    drift_above_threshold = (
        drift_share_threshold is not None
        and drift_share is not None
        and float(drift_share) >= float(drift_share_threshold)
    )

    reasons = []
    if performance_below_threshold:
        reasons.append("performance_below_threshold")
    if drift_detected or drift_above_threshold:
        reasons.append("data_drift_detected")

    return {
        "performance_f1_threshold": float(performance_f1_threshold)
        if performance_f1_threshold is not None
        else None,
        "drift_share_threshold": float(drift_share_threshold) if drift_share_threshold is not None else None,
        "current_f1": float(f1_value) if f1_value is not None else None,
        "current_drift_share": float(drift_share) if drift_share is not None else None,
        "drift_detected": drift_detected,
        "performance_below_threshold": performance_below_threshold,
        "drift_above_threshold": drift_above_threshold,
        "should_retrain": performance_below_threshold or drift_detected or drift_above_threshold,
        "reasons": reasons,
    }
