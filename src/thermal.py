"""
Thermal properties and heat transfer coefficients for the simplified
building energy balance model.

This module computes:

- transmission heat transfer coefficient (UA)
- ventilation / infiltration heat transfer coefficient (H_vent)
- total heat transfer coefficient (H_total)
- air thermal capacitance (C_air)
- effective thermal capacitance (C)

Formulas used:

1) Transmission through the envelope:
   Q_trans = U * A * ΔT
   => UA = Σ(U_i * A_i)

2) Ventilation / infiltration:
   Q_vent = Vdot * rho_air * cp_air * ΔT
   with:
   Vdot = ACH * V_build / 3600

   => H_vent = rho_air * cp_air * ACH * V_build / 3600
"""

from building_data import U_wall, U_window, U_roof, U_ground, V_build
from assumption import rho_air, cp_air, ACH, effective_mass_factor
from geometry import compute_geometry


def compute_thermal_properties():
    """
    Compute the thermal coefficients of the building.

    Returns
    -------
    dict
        Dictionary containing:
        - UA : transmission heat transfer coefficient [W/K]
        - H_vent : ventilation / infiltration heat transfer coefficient [W/K]
        - H_total : total heat transfer coefficient [W/K]
        - C_air : indoor air thermal capacitance [J/K]
        - C : effective building thermal capacitance [J/K]
    """

    geom = compute_geometry()

    A_wall_opaque = geom["A_wall_opaque"]
    A_window = geom["A_window"]
    A_roof = geom["A_roof"]
    A_ground = geom["A_ground"]

    # ============================================================
    # 1. TRANSMISSION HEAT TRANSFER COEFFICIENT
    # UA = Σ(U_i * A_i)
    # ============================================================

    UA = (
        U_wall * A_wall_opaque
        + U_window * A_window
        + U_roof * A_roof
        + U_ground * A_ground
    )

    # ============================================================
    # 2. VENTILATION / INFILTRATION HEAT TRANSFER COEFFICIENT
    # H_vent = rho_air * cp_air * ACH * V_build / 3600
    # ============================================================

    H_vent = rho_air * cp_air * ACH * V_build / 3600.0

    # ============================================================
    # 3. TOTAL HEAT TRANSFER COEFFICIENT
    # ============================================================

    H_total = UA + H_vent

    # ============================================================
    # 4. THERMAL CAPACITANCE
    # ============================================================

    C_air = rho_air * cp_air * V_build
    C = effective_mass_factor * C_air

    return {
        "UA": UA,
        "H_vent": H_vent,
        "H_total": H_total,
        "C_air": C_air,
        "C": C,
    }


if __name__ == "__main__":
    props = compute_thermal_properties()

    print("Thermal properties:")
    for key, value in props.items():
        print(f"{key} = {value:.2f}")
