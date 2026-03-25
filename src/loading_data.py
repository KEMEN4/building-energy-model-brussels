from pathlib import Path
import pandas as pd

from building_data import REFERENCE_BRUSSELS_NZEB


# ============================================================
# BUILDING DATA
# ============================================================

def load_building():
    """Return the reference building data."""
    return REFERENCE_BRUSSELS_NZEB


# ============================================================
# WEATHER FILE PATH
# ============================================================

def find_weather_file(csv_path=None):
    """
    Resolve the weather file path in a robust and portable way.

    Priority:
    1. explicit user-provided path
    2. standard repo path: data/raw/brussels_weather_2025.csv
    3. fallback: first CSV file found in data/raw
    """
    if csv_path is not None:
        csv_path = Path(csv_path)
        if csv_path.exists():
            return csv_path
        raise FileNotFoundError(f"Weather file not found: {csv_path}")

    base_dir = Path(__file__).resolve().parents[1]
    raw_dir = base_dir / "data" / "raw"

    if not raw_dir.exists():
        raise FileNotFoundError(f"Data folder not found: {raw_dir}")

    preferred = raw_dir / "brussels_weather_2025.csv"
    if preferred.exists():
        return preferred

    # fallback: find any CSV in data/raw
    csv_files = sorted(raw_dir.glob("*.csv"))
    if csv_files:
        return csv_files[0]

    raise FileNotFoundError(
        f"No CSV weather file found in: {raw_dir}"
    )


# ============================================================
# WEATHER DATA
# ============================================================

def load_weather(csv_path=None):
    """
    Load NASA POWER weather data.

    Parameters
    ----------
    csv_path : str or Path, optional
        Path to CSV file. If None, the function searches automatically
        inside data/raw/.

    Returns
    -------
    pandas.DataFrame
        Weather dataframe indexed by datetime, with columns:
        - temperature
        - solar
        - wind
    """
    csv_path = find_weather_file(csv_path)

    # Find header line automatically
    header_row = None
    with open(csv_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if line.startswith("YEAR"):
                header_row = i
                break

    if header_row is None:
        raise ValueError(
            f"Could not find header row starting with 'YEAR' in file: {csv_path}"
        )

    # Read CSV from detected header line
    df = pd.read_csv(csv_path, skiprows=header_row)

    # Rename useful columns
    df = df.rename(columns={
        "YEAR": "year",
        "MO": "month",
        "DY": "day",
        "HR": "hour",
        "T2M": "temperature",
        "ALLSKY_SFC_SW_DWN": "solar",
        "WS10M": "wind",
    })

    # Check mandatory columns
    required_columns = ["year", "month", "day", "hour", "temperature", "solar", "wind"]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required weather columns: {missing}")

    # Build datetime index
    df["datetime"] = pd.to_datetime(
        df[["year", "month", "day", "hour"]],
        errors="raise"
    )

    # Keep only useful columns
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
    print("\nWeather file loaded successfully.")
    print(weather.head())
    print("\nRows:", len(weather))
    print("Start:", weather.index.min())
    print("End:", weather.index.max())
