"""
Dynamic building simulation for the simplified building energy balance model.
"""

import numpy as np
import pandas as pd

from building_data import T_heat_set
from assumption import T_cool_set, dt


# ============================================================
# MODEL LIMITS
# ============================================================

Q_HVAC_MAX = 3000.0  # [W]


# ============================================================
# SETPOINT SCHEDULES
# ============================================================

def heating_setpoint(ts):
    """
    Time-dependent heating setpoint schedule.
    """
    h = ts.hour

    if 0 <= h < 6:
        return 17.0
    elif 6 <= h < 9:
        return 20.0
    elif 9 <= h < 17:
        return 19.0
    else:
        return 21.0


def cooling_setpoint(ts):
    """
    Cooling setpoint schedule.
    """
    return T_cool_set


# ============================================================
# NATURAL VENTILATION
# ============================================================

def natural_ventilation_gain(Tin, Tout, ts):
    """
    Passive cooling by window opening.

    Returns
    -------
    float
        Negative value means passive cooling [W].
    """
    if Tin > 24.0 and Tout < Tin and 8 <= ts.hour <= 22:
        return -600.0 * (Tin - Tout)
    return 0.0


# ============================================================
# FREE-FLOATING STEP
# ============================================================

def free_floating_temperature_step(Tin, Tout, Q_solar, Q_int, Q_natvent, H_total, C, dt_seconds):
    """
    Compute the next indoor temperature without active HVAC.
    """
    return Tin + (dt_seconds / C) * (
        H_total * (Tout - Tin) + Q_solar + Q_int + Q_natvent
    )


# ============================================================
# HVAC CONTROL
# ============================================================

def compute_hvac_power(Tin, Tin_free, Tout, G_solar, Q_solar, Q_int, Q_natvent, H_total, C, dt_seconds, ts):
    """
    Compute target HVAC thermal power.

    Positive = heating
    Negative = cooling
    """
    T_heat_set_k = heating_setpoint(ts)
    T_cool_set_k = cooling_setpoint(ts)

    deadband = 0.5

    heating_allowed = Tout <= 16.0
    cooling_allowed = (Tout >= 25.0) and (G_solar >= 150.0)

    # Heating
    if Tin_free < (T_heat_set_k - deadband) and heating_allowed:
        Q_needed = ((T_heat_set_k - Tin) * C / dt_seconds) - (
            H_total * (Tout - Tin) + Q_solar + Q_int + Q_natvent
        )
        return max(min(Q_needed, Q_HVAC_MAX), 0.0)

    # Cooling
    if Tin_free > (T_cool_set_k + 1.0) and cooling_allowed:
        Q_needed = ((T_cool_set_k - Tin) * C / dt_seconds) - (
            H_total * (Tout - Tin) + Q_solar + Q_int + Q_natvent
        )
        return min(max(Q_needed, -Q_HVAC_MAX), 0.0)

    return 0.0


# ============================================================
# MAIN SIMULATION
# ============================================================

def run_simulation(Tout, G_solar_raw, Q_solar, Q_int, thermal_props, weather_index, dt_seconds=dt):
    """
    Run the dynamic building simulation.

    Parameters
    ----------
    Tout : array-like
        Outdoor temperature [°C]
    G_solar_raw : array-like
        Raw solar radiation from weather data [W/m²]
    Q_solar : array-like
        Solar heat gains [W]
    Q_int : array-like
        Internal heat gains [W]
    thermal_props : dict
        Thermal properties from thermal.py
    weather_index : pandas.DatetimeIndex
        Simulation time index
    dt_seconds : float
        Time step [s]

    Returns
    -------
    dict
        Tin, Tin_free, Q_natvent, Q_hvac, Q_heat, Q_cool
    """
    Tout = np.asarray(Tout, dtype=float)
    G_solar_raw = np.asarray(G_solar_raw, dtype=float)
    Q_solar = np.asarray(Q_solar, dtype=float)
    Q_int = np.asarray(Q_int, dtype=float)
    weather_index = pd.DatetimeIndex(weather_index)

    if not (len(Tout) == len(G_solar_raw) == len(Q_solar) == len(Q_int) == len(weather_index)):
        raise ValueError("Tout, G_solar_raw, Q_solar, Q_int and weather_index must have the same length.")

    N = len(Tout)

    H_total = thermal_props["H_total"]
    C = thermal_props["C"]

    Tin = np.zeros(N)
    Tin_free = np.zeros(N)
    Q_natvent = np.zeros(N)
    Q_hvac = np.zeros(N)
    Q_heat = np.zeros(N)
    Q_cool = np.zeros(N)

    Tin[0] = T_heat_set
    Tin_free[0] = T_heat_set

    for k in range(N - 1):
        ts = weather_index[k]

        # Natural ventilation
        Q_natvent[k] = natural_ventilation_gain(Tin[k], Tout[k], ts)

        # Free-floating indoor temperature
        Tin_free[k + 1] = free_floating_temperature_step(
            Tin=Tin[k],
            Tout=Tout[k],
            Q_solar=Q_solar[k],
            Q_int=Q_int[k],
            Q_natvent=Q_natvent[k],
            H_total=H_total,
            C=C,
            dt_seconds=dt_seconds,
        )

        # Target HVAC power
        Q_target = compute_hvac_power(
            Tin=Tin[k],
            Tin_free=Tin_free[k + 1],
            Tout=Tout[k],
            G_solar=G_solar_raw[k],
            Q_solar=Q_solar[k],
            Q_int=Q_int[k],
            Q_natvent=Q_natvent[k],
            H_total=H_total,
            C=C,
            dt_seconds=dt_seconds,
            ts=ts,
        )

        # HVAC inertia
        alpha = 0.8
        if k > 0:
            Q_hvac[k] = alpha * Q_hvac[k - 1] + (1 - alpha) * Q_target
        else:
            Q_hvac[k] = Q_target

        # Avoid micro-cycles
        Q_MIN = 500.0
        if abs(Q_hvac[k]) < Q_MIN:
            Q_hvac[k] = 0.0

        # Split heating / cooling
        Q_heat[k] = max(Q_hvac[k], 0.0)
        Q_cool[k] = max(-Q_hvac[k], 0.0)

        # Update indoor temperature
        Tin[k + 1] = Tin[k] + (dt_seconds / C) * (
            H_total * (Tout[k] - Tin[k])
            + Q_solar[k]
            + Q_int[k]
            + Q_natvent[k]
            + Q_hvac[k]
        )

    if N > 1:
        Tin_free[-1] = Tin[-1]
        Q_natvent[-1] = Q_natvent[-2]
        Q_hvac[-1] = Q_hvac[-2]
        Q_heat[-1] = Q_heat[-2]
        Q_cool[-1] = Q_cool[-2]

    return {
        "Tin": Tin,
        "Tin_free": Tin_free,
        "Q_natvent": Q_natvent,
        "Q_hvac": Q_hvac,
        "Q_heat": Q_heat,
        "Q_cool": Q_cool,
    }


if __name__ == "__main__":
    idx = pd.date_range("2025-01-01", periods=24, freq="h")

    Tout = np.full(24, 5.0)
    G_solar_raw = np.zeros(24)
    Q_solar = np.zeros(24)
    Q_int = np.full(24, 500.0)

    thermal_props = {
        "H_total": 150.0,
        "C": 1.0e7,
    }

    results = run_simulation(
        Tout=Tout,
        G_solar_raw=G_solar_raw,
        Q_solar=Q_solar,
        Q_int=Q_int,
        thermal_props=thermal_props,
        weather_index=idx,
    )

    print("Simulation test:")
    print("Tin:", results["Tin"][:5])
    print("Q_heat:", results["Q_heat"][:5])
