import pandas as pd
from pathlib import Path
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset, TargetDriftPreset, DataQualityPreset

REFERENCE_DATA = Path("data/merged_data.csv") 
CURRENT_DATA = Path("logs/inference_history.csv")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

def drift_analysis():
    if not CURRENT_DATA.exists() or not REFERENCE_DATA.exists():
        print("Required datasets for drift analysis are missing.")
        return

    reference_df = pd.read_csv(REFERENCE_DATA)
    current_df = pd.read_csv(CURRENT_DATA)

    drift_report = Report(metrics=[
        DataQualityPreset(), 
        DataDriftPreset(),
        TargetDriftPreset()
    ])

    drift_report.run(reference_data=reference_df, current_data=current_df)

    output_path = REPORT_DIR / "drift_report.html"
    drift_report.save_html(str(output_path))
    
    report_dict = drift_report.as_dict()
    drift_share = report_dict['metrics'][1]['result']['share_of_drifted_columns']
    
    if drift_share > 0.3:
        print(f"Alert: Statistical Drift Detected ({drift_share:.2%}). Initiating Triggered Retraining.")
    else:
        print(f"Monitoring complete. System stability confirmed ({drift_share:.2%}).")

if __name__ == "__main__":
    drift_analysis()