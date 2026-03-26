"""
Heat pump electricity model based on a modified Carnot approach.

This module computes:
- heating COP
- cooling EER
- heat pump operating masks
- HVAC electricity demand
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


def to_kelvin(T_c):
    """Convert temperature from °C to K."""
    return np.asarray(T_c, dtype=float) + 273.15


def cop_carnot_heating(Tout_C, Tindoor_C=T_indoor_heat):
    """
    Modified Carnot COP in heating mode.
    """
    Tout_C = np.asarray(Tout_C, dtype=float)

    T_cond_K = to_kelvin(Tindoor_C + dT_hex_heating)
    T_evap_K = to_kelvin(Tout_C - dT_hex_heating)

    delta_T = np.maximum(T_cond_K - T_evap_K, deltaT_min)
    cop_real = eta_heating * (T_cond_K / delta_T)

    return np.clip(cop_real, COP_min, COP_max)


def eer_carnot_cooling(Tout_C, Tindoor_C=T_indoor_cool):
    """
    Modified Carnot EER in cooling mode.
    """
    Tout_C = np.asarray(Tout_C, dtype=float)

    T_cond_K = to_kelvin(Tout_C + dT_hex_cooling)
    T_evap_K = to_kelvin(Tindoor_C - dT_hex_cooling)

    delta_T = np.maximum(T_cond_K - T_evap_K, deltaT_min)
    eer_real = eta_cooling * (T_evap_K / delta_T)

    return np.clip(eer_real, EER_min, EER_max)


def heating_active_mask(Q_heat, Tout_C, cutoff=heat_cutoff_temp):
    Q_heat = np.asarray(Q_heat, dtype=float)
    Tout_C = np.asarray(Tout_C, dtype=float)

    return (Q_heat > 0.0) & (Tout_C <= cutoff)


def cooling_active_mask(Q_cool, Tout_C, cutoff=cool_cutoff_temp):
    Q_cool = np.asarray(Q_cool, dtype=float)
    Tout_C = np.asarray(Tout_C, dtype=float)

    return (Q_cool > 0.0) & (Tout_C >= cutoff)


def compute_heat_pump_electricity(
    Q_heat,
    Q_cool,
    Tout,
    Tindoor_heat_C=T_indoor_heat,
    Tindoor_cool_C=T_indoor_cool,
):
    """
    Compute heat pump electricity demand.

    Parameters
    ----------
    Q_heat : array-like
        Heating thermal demand [W]
    Q_cool : array-like
        Cooling thermal demand [W]
    Tout : array-like
        Outdoor air temperature [°C]
    """
    Q_heat = np.asarray(Q_heat, dtype=float)
    Q_cool = np.asarray(Q_cool, dtype=float)
    Tout = np.asarray(Tout, dtype=float)

    if not (Q_heat.shape == Q_cool.shape == Tout.shape):
        raise ValueError("Q_heat, Q_cool, and Tout must have the same shape.")

    Q_heat = np.maximum(Q_heat, 0.0)
    Q_cool = np.maximum(Q_cool, 0.0)

    COP_t_raw = cop_carnot_heating(Tout, Tindoor_C=Tindoor_heat_C)
    EER_t_raw = eer_carnot_cooling(Tout, Tindoor_C=Tindoor_cool_C)

    heating_on = heating_active_mask(Q_heat, Tout)
    cooling_on = cooling_active_mask(Q_cool, Tout) & (~heating_on)

    Q_heat_served = np.where(heating_on, Q_heat, 0.0)
    Q_cool_served = np.where(cooling_on, Q_cool, 0.0)

    P_heat_elec = np.where(heating_on, Q_heat_served / COP_t_raw, 0.0)
    P_cool_elec = np.where(cooling_on, Q_cool_served / EER_t_raw, 0.0)

    return {
        "COP_t": np.where(heating_on, COP_t_raw, np.nan),
        "EER_t": np.where(cooling_on, EER_t_raw, np.nan),
        "Q_heat_served": Q_heat_served,
        "Q_cool_served": Q_cool_served,
        "P_heat_elec": P_heat_elec,
        "P_cool_elec": P_cool_elec,
        "P_hvac_elec": P_heat_elec + P_cool_elec,
        "heating_on": heating_on,
        "cooling_on": cooling_on,
    }


compute_hvac_electricity = compute_heat_pump_electricity
