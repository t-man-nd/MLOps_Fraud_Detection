import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring import compute_feedback_metrics, load_feedback_dataframe, load_prediction_dataframe  # noqa: E402


def parse_args():
    parser = argparse.ArgumentParser(
        description="Summarize realized model performance from prediction and feedback logs."
    )
    parser.add_argument("--prediction_log_path", type=str, default="logs/predictions.jsonl")
    parser.add_argument("--feedback_log_path", type=str, default="logs/prediction_feedback.jsonl")
    parser.add_argument("--output_path", type=str, default="reports/monitoring/performance_summary.json")
    parser.add_argument("--endpoint", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()

    prediction_df = load_prediction_dataframe(args.prediction_log_path, endpoint=args.endpoint)
    feedback_df = load_feedback_dataframe(args.feedback_log_path)
    summary = compute_feedback_metrics(prediction_df, feedback_df)
    summary["prediction_log_path"] = str(args.prediction_log_path)
    summary["feedback_log_path"] = str(args.feedback_log_path)
    summary["endpoint"] = args.endpoint

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
