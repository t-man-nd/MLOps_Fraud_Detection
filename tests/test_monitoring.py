import numpy as np

from src.monitoring import (
    append_jsonl,
    build_feedback_events,
    build_prediction_events,
    compute_feedback_metrics,
    evaluate_monitoring_status,
    extract_feature_frame,
    load_feedback_dataframe,
    load_prediction_dataframe,
)


def test_build_prediction_events_adds_ids_and_prefixed_features():
    events = build_prediction_events(
        records=[{"feature_a": 1.5, "feature_b": 2}],
        probabilities=np.array([0.8]),
        predictions=np.array([1]),
        endpoint="/predict",
        model_name="demo_model",
        threshold=0.5,
    )

    assert len(events) == 1
    assert events[0]["event_type"] == "prediction"
    assert events[0]["request_id"]
    assert events[0]["prediction_id"].endswith(":0")
    assert events[0]["feature__feature_a"] == 1.5


def test_prediction_log_roundtrip_and_feature_extraction(tmp_path):
    prediction_log = tmp_path / "predictions.jsonl"
    records = build_prediction_events(
        records=[{"feature_a": 1.0}, {"feature_a": 2.0}],
        probabilities=np.array([0.1, 0.9]),
        predictions=np.array([0, 1]),
        endpoint="/predict",
        model_name="demo_model",
        threshold=0.5,
    )
    append_jsonl(prediction_log, records)

    loaded = load_prediction_dataframe(prediction_log, endpoint="/predict")
    features = extract_feature_frame(loaded)

    assert loaded.shape[0] == 2
    assert list(features.columns) == ["feature_a"]
    assert features["feature_a"].tolist() == [1.0, 2.0]


def test_compute_feedback_metrics_returns_f1_and_auprc(tmp_path):
    prediction_log = tmp_path / "predictions.jsonl"
    feedback_log = tmp_path / "feedback.jsonl"

    prediction_events = build_prediction_events(
        records=[{"feature_a": 1.0}, {"feature_a": 2.0}],
        probabilities=np.array([0.2, 0.9]),
        predictions=np.array([0, 1]),
        endpoint="/predict",
        model_name="demo_model",
        threshold=0.5,
        request_id="req-1",
    )
    append_jsonl(prediction_log, prediction_events)

    feedback_events = build_feedback_events(
        [
            {"prediction_id": "req-1:0", "actual_label": 0},
            {"prediction_id": "req-1:1", "actual_label": 1},
        ]
    )
    append_jsonl(feedback_log, feedback_events)

    prediction_df = load_prediction_dataframe(prediction_log)
    feedback_df = load_feedback_dataframe(feedback_log)
    summary = compute_feedback_metrics(prediction_df, feedback_df)

    assert summary["records_with_feedback"] == 2
    assert summary["f1"] == 1.0
    assert summary["precision"] == 1.0
    assert summary["recall"] == 1.0
    assert summary["auprc"] == 1.0


def test_evaluate_monitoring_status_flags_retraining():
    status = evaluate_monitoring_status(
        {"f1": 0.62},
        {"drifted_columns_share": 0.7, "dataset_drift_detected": True},
        performance_f1_threshold=0.7,
        drift_share_threshold=0.5,
    )

    assert status["performance_below_threshold"] is True
    assert status["drift_detected"] is True
    assert status["should_retrain"] is True
    assert "performance_below_threshold" in status["reasons"]
    assert "data_drift_detected" in status["reasons"]
