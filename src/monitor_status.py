import argparse
import json
import sys
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.monitoring import evaluate_monitoring_status  # noqa: E402


def load_params_defaults(params_path: Path) -> dict:
    if not params_path.exists():
        return {}
    payload = yaml.safe_load(params_path.read_text(encoding="utf-8")) or {}
    return payload.get("monitoring", {})


def parse_args():
    params_defaults = load_params_defaults(PROJECT_ROOT / "params.yaml")
    parser = argparse.ArgumentParser(
        description="Combine drift and realized performance reports into a retraining status summary."
    )
    parser.add_argument(
        "--performance_summary_path",
        type=str,
        default=params_defaults.get("performance_report_path", "reports/monitoring/performance_summary.json"),
    )
    parser.add_argument(
        "--drift_summary_path",
        type=str,
        default=str(Path(params_defaults.get("drift_report_dir", "reports/drift")) / "data_drift_summary.json"),
    )
    parser.add_argument(
        "--output_path",
        type=str,
        default="reports/monitoring/status_summary.json",
    )
    parser.add_argument(
        "--performance_f1_threshold",
        type=float,
        default=float(params_defaults.get("performance_f1_threshold", 0.7)),
    )
    parser.add_argument(
        "--drift_share_threshold",
        type=float,
        default=float(params_defaults.get("drift_share_threshold", 0.5)),
    )
    return parser.parse_args()


def load_json(path: str | Path) -> dict:
    source = Path(path)
    if not source.exists():
        return {}
    return json.loads(source.read_text(encoding="utf-8"))


def main():
    args = parse_args()

    performance_summary = load_json(args.performance_summary_path)
    drift_summary = load_json(args.drift_summary_path)
    status = evaluate_monitoring_status(
        performance_summary,
        drift_summary,
        performance_f1_threshold=args.performance_f1_threshold,
        drift_share_threshold=args.drift_share_threshold,
    )
    status["performance_summary_path"] = str(args.performance_summary_path)
    status["drift_summary_path"] = str(args.drift_summary_path)

    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(status, indent=2), encoding="utf-8")

    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
