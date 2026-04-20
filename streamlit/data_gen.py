import pandas as pd
import json

# Load RAW data 
df = pd.read_csv("../data/merged_train_data.csv")

# Get data in validation range
start_index = df[df['TransactionID'] == 3577280].index[0]

target_rows = df.iloc[start_index : start_index + 70]

payload = {
    "records": target_rows.to_dict(orient="records")
}

with open("sample_request.json", "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print("Saved RAW samples to sample_request.json")

