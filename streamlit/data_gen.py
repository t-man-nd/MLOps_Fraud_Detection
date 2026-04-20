import json
from pathlib import Path

import pandas as pd

from data_gen import (
    DEFAULT_INPUT_PATH,
    DEFAULT_NUM_ROWS,
    DEFAULT_TRANSACTION_ID,
    build_payload,
)


STREAMLIT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = STREAMLIT_DIR / "sample_request.json"


def main() -> None:
    df = pd.read_csv(DEFAULT_INPUT_PATH)
    payload = build_payload(
        df,
        transaction_id=DEFAULT_TRANSACTION_ID,
        num_rows=DEFAULT_NUM_ROWS,
    )

    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)

    print(f"Saved RAW samples to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
