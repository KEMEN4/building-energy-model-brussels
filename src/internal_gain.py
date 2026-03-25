"""
Internal gains model for the simplified building energy balance.

Includes:
- occupancy gains
- lighting gains
- equipment gains
"""

import numpy as np

from building_data import A_cond, n_occ
from assumption import EPD


# ============================================================
# LIGHTING DATA
# ============================================================

LPD_LIVING = 12.0   # W/m²
LPD_BEDROOM = 8.0   # W/m²

# Average simplified value (Brussels)
LPD = 8.5


# ============================================================
# OCCUPANCY PROFILE
# ============================================================

def occupancy_fraction(ts):
    """Return occupancy factor (0 → 1)."""
    h = ts.hour
    dow = ts.dayofweek

    # Weekdays
    if dow < 5:
        if 6 <= h <= 9 or 17 <= h <= 23:
            return 1.0
        return 0.1

    # Weekends
    if 8 <= h <= 23:
        return 1.0
    return 0.1


# ============================================================
# LIGHTING PROFILE
# ============================================================

def lighting_fraction(ts):
    """Return lighting usage factor (0 → 1)."""
    h = ts.hour
    month = ts.month

    if 6 <= h <= 8 or 18 <= h <= 23:
        frac = 1.0
    elif 9 <= h <= 16:
        frac = 0.3
    else:
        frac = 0.1

    # Winter correction (less daylight)
    if month in [11, 12, 1, 2]:
        if 8 <= h <= 10 or 16 <= h <= 17:
            frac = max(frac, 0.6)

    return frac


# ============================================================
# INTERNAL GAINS
# ============================================================

def compute_internal_gains(weather_index, G_Wm2=None):
    """
    Compute internal heat gains.

    Parameters
    ----------
    weather_index : DatetimeIndex
    G_Wm2 : optional solar radiation (used to reduce lighting)

    Returns
    -------
    dict
    """

    occ = weather_index.to_series().apply(occupancy_fraction).values
    light_sched = weather_index.to_series().apply(lighting_fraction).values

    # ============================================================
    # OCCUPANTS
    # ============================================================

    q_person = 75.0  # W/person
    Q_people = q_person * n_occ * occ

    # ============================================================
    # LIGHTING
    # ============================================================

    light_factor = occ * light_sched

    if G_Wm2 is not None:
        G_Wm2 = np.asarray(G_Wm2)
        light_factor = light_factor.copy()

        # daylight reduces artificial lighting
        light_factor[G_Wm2 > 200] *= 0.5
        light_factor[G_Wm2 > 400] *= 0.7

    Q_lights = LPD * A_cond * light_factor

    # ============================================================
    # EQUIPMENT
    # ============================================================

    Q_equip = EPD * A_cond * (0.20 + 0.80 * occ)

    # ============================================================
    # TOTAL
    # ============================================================

    Q_int = Q_people + Q_lights + Q_equip
    P_base_elec = Q_lights + Q_equip

    return {
        "occ": occ,
        "Q_people": Q_people,
        "Q_lights": Q_lights,
        "Q_equip": Q_equip,
        "Q_int": Q_int,
        "P_base_elec": P_base_elec,
    }


if __name__ == "__main__":
    import pandas as pd

    idx = pd.date_range("2025-01-01", periods=24, freq="h")
    results = compute_internal_gains(idx)

    print("Internal gains test:")
    print("Q_int:", results["Q_int"])
