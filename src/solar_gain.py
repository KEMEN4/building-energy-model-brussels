"""
Solar heat gain model for the simplified building energy balance.

The simplified formulation used is:

    Q_sol = A_window * SHGC * G * F_orient * F_shading

where:
- A_window : window area [m²]
- SHGC     : solar heat gain coefficient [-]
- G        : global solar irradiance from weather data [W/m²]
- F_orient : orientation correction factor [-]
- F_shading: simplified shading / solar protection factor [-]
"""

import numpy as np

from building_data import SHGC
from geometry import compute_geometry
from assumption import solar_reduction_factor, solar_orientation_factor


def compute_solar_gain(solar_irradiance):
    """
    Compute solar heat gains through the windows.

    Parameters
    ----------
    solar_irradiance : array-like or float
        Global solar irradiance from weather data [W/m²].

    Returns
    -------
    dict
        Dictionary containing:
        - A_window
        - SHGC
        - solar_irradiance
        - solar_orientation_factor
        - solar_reduction_factor
        - Q_sol
    """
    geom = compute_geometry()
    A_window = geom["A_window"]

    solar_irradiance = np.asarray(solar_irradiance, dtype=float)

    Q_sol = (
        A_window
        * SHGC
        * solar_irradiance
        * solar_orientation_factor
        * solar_reduction_factor
    )

    return {
        "A_window": A_window,
        "SHGC": SHGC,
        "solar_irradiance": solar_irradiance,
        "solar_orientation_factor": solar_orientation_factor,
        "solar_reduction_factor": solar_reduction_factor,
        "Q_sol": Q_sol,
    }


if __name__ == "__main__":
    test_irradiance = np.array([0.0, 100.0, 300.0, 500.0])
    results = compute_solar_gain(test_irradiance)

    print("Solar gains test:")
    print(results["Q_sol"])
