import pandas as pd
from pathlib import Path

from building_data import REFERENCE_BRUSSELS_NZEB


# ============================================================
# BUILDING DATA
# ============================================================

def load_building():
    """Return building data."""
    return REFERENCE_BRUSSELS_NZEB


# ============================================================
# WEATHER DATA
# ============================================================

def load_weather(csv_path=None):
    """
    Load NASA POWER weather data.

    If no path is provided, default file from repo is used.
    """

    # 📁 chemin par défaut (GitHub-friendly)
    if csv_path is None:
        csv_path = Path(__file__).resolve().parents[1] / "data" / "raw" / "brussels_weather_2025.csv"

    csv_path = Path(csv_path)

    if not csv_path.exists():
        raise FileNotFoundError(f"Weather file not found: {csv_path}")

    # 🔍 détecter ligne header automatiquement
    header_row = None
    with open(csv_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.startswith("YEAR"):
                header_row = i
                break

    if header_row is None:
        raise ValueError("Header 'YEAR' not found in file.")

    # 📊 lecture
    df = pd.read_csv(csv_path, skiprows=header_row)

    # 🏷 rename
    df = df.rename(columns={
        "YEAR": "year",
        "MO": "month",
        "DY": "day",
        "HR": "hour",
        "T2M": "temperature",
        "ALLSKY_SFC_SW_DWN": "solar",
        "WS10M": "wind",
    })

    # ✅ check colonnes
    required = ["year", "month", "day", "hour", "temperature", "solar", "wind"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # 🕒 datetime
    df["datetime"] = pd.to_datetime(
        df[["year", "month", "day", "hour"]],
        errors="raise"
    )

    # 📦 clean
    df = df[["datetime", "temperature", "solar", "wind"]]
    df = df.set_index("datetime")

    return df


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    building = load_building()
    print("Conditioned area:", building.geometry.conditioned_area_m2)

    weather = load_weather()

    print("\nWeather data:")
    print(weather.head())
