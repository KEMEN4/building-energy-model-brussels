from dataclasses import dataclass, asdict
from typing import Optional


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass(frozen=True)
class BuildingMetadata:
    reference_name: str
    building_type: str
    location: str
    construction_period: str
    renovation_period: str
    energy_label: Optional[str] = None


@dataclass(frozen=True)
class GeometryData:
    number_of_floors: int
    total_area_m2: float
    conditioned_area_m2: float
    unconditioned_area_m2: float
    total_volume_m3: float
    external_wall_area_m2: Optional[float] = None
    roof_area_m2: Optional[float] = None
    floor_area_m2: Optional[float] = None
    windows_area_m2: Optional[float] = None


@dataclass(frozen=True)
class EnvelopeData:
    window_to_wall_ratio_pct: float
    window_u_value_w_m2k: float
    window_g_value: float
    shgc: float
    light_transmittance: Optional[float] = None
    solar_protection: Optional[str] = None
    wall_surface_absorptance: float = 0.0
    external_wall_u_value_w_m2k: float = 0.0
    roof_u_value_w_m2k: float = 0.0
    ground_u_value_w_m2k: float = 0.0
    attic_floor_u_value_w_m2k: float = 0.0


@dataclass(frozen=True)
class AirtightnessData:
    airtightness_50pa_ach: float
    airtightness_50pa_m3_h_m2: Optional[float] = None
    airtightness_4pa_m3_h_m2: Optional[float] = None
    airtightness_4pa_ach: Optional[float] = None


@dataclass(frozen=True)
class OccupancyData:
    number_of_people: int
    occupancy_density_m2_per_person: float
    occupancy_schedule_reference: str
    holidays_schedule_reference: str


@dataclass(frozen=True)
class InternalLoadsData:
    lighting_power_density_min_w_m2: float
    lighting_power_density_max_w_m2: float
    lighting_schedule_reference: str
    equipment_schedule_reference: str


@dataclass(frozen=True)
class VentilationData:
    living_open_kitchen_supply_m3_h: Optional[float] = None
    living_open_kitchen_extract_m3_h: Optional[float] = None
    bedrooms_supply_m3_h: Optional[float] = None
    bathroom_extract_m3_h: Optional[float] = None
    mechanical_ventilation_heat_recovery_efficiency_pct: Optional[float] = None


@dataclass(frozen=True)
class HeatingSetpointsData:
    heating_setpoint_c: Optional[float] = None
    heating_setback_c: Optional[float] = None
    bedroom_setpoint_c: Optional[float] = None
    bathroom_short_presence_setpoint_c: Optional[float] = None


@dataclass(frozen=True)
class BuildingData:
    metadata: BuildingMetadata
    geometry: GeometryData
    envelope: EnvelopeData
    airtightness: AirtightnessData
    occupancy: OccupancyData
    internal_loads: InternalLoadsData
    ventilation: VentilationData
    heating_setpoints: HeatingSetpointsData


# ============================================================
# REFERENCE BUILDING
# ============================================================

REFERENCE_BRUSSELS_NZEB = BuildingData(
    metadata=BuildingMetadata(
        reference_name="Reference terraced nZEB building",
        building_type="Terraced house",
        location="Brussels, Belgium",
        construction_period="1930s",
        renovation_period="After 2010",
        energy_label="A",
    ),
    geometry=GeometryData(
        number_of_floors=3,
        total_area_m2=259.0,
        conditioned_area_m2=173.0,
        unconditioned_area_m2=86.0,
        total_volume_m3=873.0,
        external_wall_area_m2=122.0,
        roof_area_m2=91.0,
        floor_area_m2=259.0,
        windows_area_m2=41.0,
    ),
    envelope=EnvelopeData(
        window_to_wall_ratio_pct=19.0,
        window_u_value_w_m2k=1.2,
        window_g_value=0.6,
        shgc=0.6,
        light_transmittance=0.80,
        solar_protection="Roller Shutters",
        wall_surface_absorptance=0.9,
        external_wall_u_value_w_m2k=0.4,
        roof_u_value_w_m2k=0.3,
        ground_u_value_w_m2k=0.3,
        attic_floor_u_value_w_m2k=0.8,
    ),
    airtightness=AirtightnessData(
        airtightness_50pa_ach=1.58,
        airtightness_50pa_m3_h_m2=31.6,
        airtightness_4pa_m3_h_m2=5.89,
        airtightness_4pa_ach=0.3,
    ),
    occupancy=OccupancyData(
        number_of_people=4,
        occupancy_density_m2_per_person=43.0,
        occupancy_schedule_reference="See Fig. 10",
        holidays_schedule_reference="See Table 5",
    ),
    internal_loads=InternalLoadsData(
        lighting_power_density_min_w_m2=8.0,
        lighting_power_density_max_w_m2=10.0,
        lighting_schedule_reference="Ref. [66] / See Fig. 10",
        equipment_schedule_reference="Ref. [66]",
    ),
    ventilation=VentilationData(
        living_open_kitchen_supply_m3_h=25.0,
        living_open_kitchen_extract_m3_h=30.0,
        bedrooms_supply_m3_h=25.0,
        bathroom_extract_m3_h=25.0,
        mechanical_ventilation_heat_recovery_efficiency_pct=92.0,
    ),
    heating_setpoints=HeatingSetpointsData(
        heating_setpoint_c=21.0,
        heating_setback_c=12.0,
        bedroom_setpoint_c=18.0,
        bathroom_short_presence_setpoint_c=16.0,
    ),
)


# ============================================================
# HELPER
# ============================================================

def to_dict() -> dict:
    """Return the building data as a nested dictionary."""
    return {
        "metadata": asdict(REFERENCE_BRUSSELS_NZEB.metadata),
        "geometry": asdict(REFERENCE_BRUSSELS_NZEB.geometry),
        "envelope": asdict(REFERENCE_BRUSSELS_NZEB.envelope),
        "airtightness": asdict(REFERENCE_BRUSSELS_NZEB.airtightness),
        "occupancy": asdict(REFERENCE_BRUSSELS_NZEB.occupancy),
        "internal_loads": asdict(REFERENCE_BRUSSELS_NZEB.internal_loads),
        "ventilation": asdict(REFERENCE_BRUSSELS_NZEB.ventilation),
        "heating_setpoints": asdict(REFERENCE_BRUSSELS_NZEB.heating_setpoints),
    }


# ============================================================
# SHORTCUTS FOR THE REST OF THE MODEL
# ============================================================

# Geometry
A_cond = REFERENCE_BRUSSELS_NZEB.geometry.conditioned_area_m2
A_window = REFERENCE_BRUSSELS_NZEB.geometry.windows_area_m2
A_wall = REFERENCE_BRUSSELS_NZEB.geometry.external_wall_area_m2
A_roof = REFERENCE_BRUSSELS_NZEB.geometry.roof_area_m2
#A_ground = REFERENCE_BRUSSELS_NZEB.geometry.
A_ground = REFERENCE_BRUSSELS_NZEB.geometry.roof_area_m2
V_build = REFERENCE_BRUSSELS_NZEB.geometry.total_volume_m3

# Envelope
U_wall = REFERENCE_BRUSSELS_NZEB.envelope.external_wall_u_value_w_m2k
U_window = REFERENCE_BRUSSELS_NZEB.envelope.window_u_value_w_m2k
U_roof = REFERENCE_BRUSSELS_NZEB.envelope.roof_u_value_w_m2k
U_ground = REFERENCE_BRUSSELS_NZEB.envelope.ground_u_value_w_m2k
SHGC = REFERENCE_BRUSSELS_NZEB.envelope.shgc
g_value = REFERENCE_BRUSSELS_NZEB.envelope.window_g_value
WWR = REFERENCE_BRUSSELS_NZEB.envelope.window_to_wall_ratio_pct / 100.0

# Airtightness
ACH_50Pa = REFERENCE_BRUSSELS_NZEB.airtightness.airtightness_50pa_ach
ACH_4Pa = REFERENCE_BRUSSELS_NZEB.airtightness.airtightness_4pa_ach

# Occupancy
n_occ = REFERENCE_BRUSSELS_NZEB.occupancy.number_of_people

# Ventilation
vent_supply_living = REFERENCE_BRUSSELS_NZEB.ventilation.living_open_kitchen_supply_m3_h
vent_extract_living = REFERENCE_BRUSSELS_NZEB.ventilation.living_open_kitchen_extract_m3_h
vent_supply_bedrooms = REFERENCE_BRUSSELS_NZEB.ventilation.bedrooms_supply_m3_h
vent_extract_bathroom = REFERENCE_BRUSSELS_NZEB.ventilation.bathroom_extract_m3_h
heat_recovery_efficiency = (
    REFERENCE_BRUSSELS_NZEB.ventilation.mechanical_ventilation_heat_recovery_efficiency_pct / 100.0
)

# Setpoints
T_heat_set = REFERENCE_BRUSSELS_NZEB.heating_setpoints.heating_setpoint_c
T_heat_setback = REFERENCE_BRUSSELS_NZEB.heating_setpoints.heating_setback_c
T_bedroom_set = REFERENCE_BRUSSELS_NZEB.heating_setpoints.bedroom_setpoint_c
T_bathroom_set = REFERENCE_BRUSSELS_NZEB.heating_setpoints.bathroom_short_presence_setpoint_c


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    import pprint

    pprint.pp(to_dict())

    print("\n--- Shortcuts ---")
    print("A_cond =", A_cond)
    print("A_wall =", A_wall)
    print("A_window =", A_window)
    print("U_wall =", U_wall)
    print("V_build =", V_build)
    print("n_occ =", n_occ)
    print("T_heat_set =", T_heat_set)
