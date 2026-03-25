"""
Model assumptions for the simplified building energy model.

This file contains generic modelling assumptions:
- air properties
- simulation time step
- effective infiltration rate
- thermal mass approximation
- internal gains assumptions
- simplified solar correction factors
- heat pump performance parameters
"""

# ============================================================
# AIR PROPERTIES
# ============================================================

rho_air = 1.2        # [kg/m3]
cp_air = 1005.0      # [J/kg.K]


# ============================================================
# TIME STEP
# ============================================================

dt = 3600.0          # [s] hourly simulation


# ============================================================
# INFILTRATION / VENTILATION
# ============================================================

# Effective air change rate used in the simplified model
ACH = 0.3            # [1/h]


# ============================================================
# THERMAL MASS
# ============================================================

# Effective thermal mass multiplier used to represent
# the building inertia in a simplified way
effective_mass_factor = 10.0

# Simplified ground temperature
ground_temperature_c = 10.0   # [°C]


# ============================================================
# INTERNAL GAINS
# ============================================================

# Sensible heat released per occupant
people_sensible_w = 75.0      # [W/person]

# Equipment power density
EPD = 8.0                     # [W/m2]

# Average lighting power density used in the simplified model
lighting_power_density_w_m2 = 8.5   # [W/m2]


# ============================================================
# SOLAR
# ============================================================

# Global reduction factor representing simplified shading /
# external solar protection (roller shutters, etc.)
solar_reduction_factor = 0.45

# Factor used to convert horizontal global irradiance
# into an effective window solar gain for vertical facades
solar_orientation_factor = 0.10


# ============================================================
# COOLING SETPOINT
# ============================================================

T_cool_set = 26.0     # [°C]


# ============================================================
# HEAT PUMP PARAMETERS
# ============================================================

# Indoor reference temperatures
T_indoor_heat = 20.0  # [°C]
T_indoor_cool = 26.0  # [°C]

# Heat exchanger approach temperatures
dT_hex_heating = 6.0  # [K]
dT_hex_cooling = 6.0  # [K]

# Minimum temperature lift to avoid unrealistically high COP/EER
deltaT_min = 10.0     # [K]

# Modified Carnot efficiency factors
eta_heating = 0.40
eta_cooling = 0.25

# Activation thresholds
heat_cutoff_temp = 15.0   # [°C]
cool_cutoff_temp = 25.0   # [°C]

# Performance limits
COP_min = 1.0
COP_max = 7.0
EER_min = 1.0
EER_max = 8.0
