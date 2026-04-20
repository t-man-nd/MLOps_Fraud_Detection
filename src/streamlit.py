from pathlib import Path
import runpy


APP_PATH = Path(__file__).resolve().parents[1] / "streamlit" / "app.py"


if __name__ == "__main__":
    runpy.run_path(str(APP_PATH), run_name="__main__")
