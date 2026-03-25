"""
Heat pump electricity model based on a modified Carnot approach.
"""

import numpy as np

from assumption import (
    T_indoor_heat,
    T_indoor_cool,
    dT_hex_heating,
    dT_hex_cooling,
    deltaT_min,
    eta_heating,
    eta_cooling,
    heat_cutoff_temp,
    cool_cutoff_temp,
    COP_min,
    COP_max,
    EER_min,
    EER_max,
)


# ============================================================
# HELPERS
# ============================================================

def to_kelvin(T_c):
    """Convert °C → K."""
    return np.asarray(T_c, dtype=float) + 273.15


# ============================================================
# PERFORMANCE MODELS
# ============================================================

def cop_carnot_heating(Tout_C, Tindoor_C=T_indoor_heat):
    """
    Modified Carnot COP (heating mode).
    """
    Tout_C = np.asarray(Tout_C, dtype=float)

    T_cond_K = to_kelvin(Tindoor_C + dT_hex_heating)
    T_evap_K = to_kelvin(Tout_C - dT_hex_heating)

    delta_T = np.maximum(T_cond_K - T_evap_K, deltaT_min)

    cop = eta_heating * (T_cond_K / delta_T)

    return np.clip(cop, COP_min, COP_max)


def eer_carnot_cooling(Tout_C, Tindoor_C=T_indoor_cool):
    """
    Modified Carnot EER (cooling mode).
    """
    Tout_C = np.asarray(Tout_C, dtype=float)

    T_cond_K = to_kelvin(Tout_C + dT_hex_cooling)
    T_evap_K = to_kelvin(Tindoor_C - dT_hex_cooling)

    delta_T = np.maximum(T_cond_K - T_evap_K, deltaT_min)

    eer = eta_cooling * (T_evap_K / delta_T)

    return np.clip(eer, EER_min, EER_max)


# ============================================================
# OPERATING CONDITIONS
# ============================================================

def heating_active_mask(Q_heat, Tout_C):
    Q_heat = np.asarray(Q_heat, dtype=float)
    Tout_C = np.asarray(Tout_C, dtype=float)

    return (Q_heat > 0.0) & (Tout_C <= heat_cutoff_temp)


def cooling_active_mask(Q_cool, Tout_C):
    Q_cool = np.asarray(Q_cool, dtype=float)
    Tout_C = np.asarray(Tout_C, dtype=float)

    return (Q_cool > 0.0) & (Tout_C >= cool_cutoff_temp)


# ============================================================
# MAIN FUNCTION
# ============================================================

def compute_heat_pump_electricity(
    Q_heat,
    Q_cool,
    Tout,
):
    """
    Compute heat pump electricity consumption.

    Returns
    -------
    dict
    """

    Q_heat = np.asarray(Q_heat, dtype=float)
    Q_cool = np.asarray(Q_cool, dtype=float)
    Tout = np.asarray(Tout, dtype=float)

    if not (Q_heat.shape == Q_cool.shape == Tout.shape):
        raise ValueError("Q_heat, Q_cool, Tout must have same shape")

    Q_heat = np.maximum(Q_heat, 0.0)
    Q_cool = np.maximum(Q_cool, 0.0)

    # Performance
    COP_t = cop_carnot_heating(Tout)
    EER_t = eer_carnot_cooling(Tout)

    # Operating masks
    heating_on = heating_active_mask(Q_heat, Tout)
    cooling_on = cooling_active_mask(Q_cool, Tout) & (~heating_on)

    # Served loads
    Q_heat_served = np.where(heating_on, Q_heat, 0.0)
    Q_cool_served = np.where(cooling_on, Q_cool, 0.0)

    # Electricity
    P_heat_elec = np.where(heating_on, Q_heat_served / COP_t, 0.0)
    P_cool_elec = np.where(cooling_on, Q_cool_served / EER_t, 0.0)

    return {
        "COP_t": COP_t,
        "EER_t": EER_t,
        "Q_heat_served": Q_heat_served,
        "Q_cool_served": Q_cool_served,
        "P_heat_elec": P_heat_elec,
        "P_cool_elec": P_cool_elec,
        "P_hvac_elec": P_heat_elec + P_cool_elec,
        "heating_on": heating_on,
        "cooling_on": cooling_on,
    }


# Alias
compute_hvac_electricity = compute_heat_pump_electricity


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    Tout = np.array([0, 5, 10, 20, 30])
    Q_heat = np.array([2000, 1500, 500, 0, 0])
    Q_cool = np.array([0, 0, 0, 500, 1500])

    res = compute_heat_pump_electricity(Q_heat, Q_cool, Tout)

    print("COP:", res["COP_t"])
    print("EER:", res["EER_t"])
    print("Electricity:", res["P_hvac_elec"])
