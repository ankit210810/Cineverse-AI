"""Streamlit Community Cloud default entrypoint redirect for Cineverse AI."""
import runpy
from pathlib import Path

# Run main app.py in __main__ scope
_app_file = Path(__file__).resolve().parent / "app.py"
runpy.run_path(str(_app_file), run_name="__main__")
