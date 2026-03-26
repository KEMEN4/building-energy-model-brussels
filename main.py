import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from loading_data import load_weather
from geometry import compute_geometry
from thermal import compute_thermal_properties
from solar_gain import compute_solar_gain
from internal_gain import compute_internal_gains
from simulation import run_simulation, heating_setpoint
from cop import compute_heat_pump_electricity
from assumption import T_cool_set


# ============================================================
# SETTINGS
# ============================================================
BASE_DIR = Path(__file__).resolve().parents[1]
WEATHER_FILE = BASE_DIR / "data" / "raw" / "brussels_weather_2025.csv.csv"

OUTPUT_DIR = BASE_DIR / "outputs"
PLOTS_DIR = OUTPUT_DIR / "plots"
DATA_DIR = OUTPUT_DIR / "data"

SHOW_MAIN_PLOTS = False
SHOW_FOCUS_PLOTS = True


# ============================================================
# HELPERS
# ============================================================

def ensure_output_folders():
    OUTPUT_DIR.mkdir(exist_ok=True)
    PLOTS_DIR.mkdir(exist_ok=True)
    DATA_DIR.mkdir(exist_ok=True)


def save_plot(x, y_list, labels, title, ylabel, filename, show=False):
    try:
        plt.figure(figsize=(14, 6))

        for y, label in zip(y_list, labels):
            plt.plot(x, y, label=label)

        plt.title(title)
        plt.xlabel("Time")
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        output_file = PLOTS_DIR / filename
        plt.savefig(output_file, dpi=300)

        if show:
            plt.show()

        plt.close()
        print(f"Plot OK: {filename}")

    except Exception as e:
        print(f"Erreur plot {filename}: {e}")
        plt.close()


# ============================================================
# MAIN
# ============================================================

def main():
    ensure_output_folders()

    # ============================================================
    # 1. LOAD WEATHER DATA
    # ============================================================

    weather = load_weather(WEATHER_FILE)

    time_index = weather.index
    Tout = weather["temperature"].values
    G_solar = weather["solar"].values
    wind = weather["wind"].values

    # ============================================================
    # 2. GEOMETRY + THERMAL PROPERTIES
    # ============================================================

    geom = compute_geometry()
    thermal_props = compute_thermal_properties()

    # ============================================================
    # 3. SOLAR GAINS
    # ============================================================

    solar_results = compute_solar_gain(G_solar)
    Q_solar = np.asarray(solar_results["Q_sol"], dtype=float)

    # ============================================================
    # 4. INTERNAL GAINS
    # ============================================================

    internal_results = compute_internal_gains(
        weather_index=time_index,
        G_Wm2=G_solar,
    )

    Q_int = np.asarray(internal_results["Q_int"], dtype=float)
    Q_people = np.asarray(internal_results["Q_people"], dtype=float)
    Q_lights = np.asarray(internal_results["Q_lights"], dtype=float)
    Q_equip = np.asarray(internal_results["Q_equip"], dtype=float)
    P_base_elec = np.asarray(internal_results["P_base_elec"], dtype=float)
    occ = np.asarray(internal_results["occ"], dtype=float)

    # ============================================================
    # 5. DYNAMIC BUILDING SIMULATION
    # ============================================================

    #sim_results = run_simulation(
    #    Tout=Tout,
    #    Q_solar=Q_solar,
    #    Q_int=Q_int,
    #    thermal_props=thermal_props,
    #    weather_index=time_index,
    #)
    sim_results = run_simulation(
        Tout=Tout,
        G_solar_raw=G_solar,
        Q_solar=Q_solar,
        Q_int=Q_int,
        thermal_props=thermal_props,
        weather_index=time_index,
    )

    Tin = np.asarray(sim_results["Tin"], dtype=float)
    Tin_free = np.asarray(sim_results["Tin_free"], dtype=float)
    Q_natvent = np.asarray(sim_results["Q_natvent"], dtype=float)
    Q_hvac = np.asarray(sim_results["Q_hvac"], dtype=float)
    Q_heat = np.asarray(sim_results["Q_heat"], dtype=float)
    Q_cool = np.asarray(sim_results["Q_cool"], dtype=float)

    # ============================================================
    # 6. HEAT PUMP ELECTRICITY
    # ============================================================

    hp_results = compute_heat_pump_electricity(
        Q_heat=Q_heat,
        Q_cool=Q_cool,
        Tout=Tout,
    )

    COP_t = hp_results["COP_t"]
    EER_t = hp_results["EER_t"]
    P_heat_elec = np.asarray(hp_results["P_heat_elec"], dtype=float)
    P_cool_elec = np.asarray(hp_results["P_cool_elec"], dtype=float)
    P_hvac_elec = np.asarray(hp_results["P_hvac_elec"], dtype=float)
    heating_on = np.asarray(hp_results["heating_on"], dtype=int)
    cooling_on = np.asarray(hp_results["cooling_on"], dtype=int)

    # ============================================================
    # 7. TOTAL ELECTRICITY
    # ============================================================

    P_total_elec = P_base_elec + P_hvac_elec

    # ============================================================
    # 8. BUILD FINAL DATAFRAME
    # ============================================================

    results = pd.DataFrame(index=time_index)

    # Climate
    results["Tout_C"] = Tout
    results["solar_Wm2"] = G_solar
    results["wind_m_s"] = wind

    # Geometry / thermal constants
    results["A_wall_total_m2"] = geom["A_wall_total"]
    results["A_wall_opaque_m2"] = geom["A_wall_opaque"]
    results["A_window_m2"] = geom["A_window"]
    results["A_roof_m2"] = geom["A_roof"]
    results["A_ground_m2"] = geom["A_ground"]

    results["UA_W_K"] = thermal_props["UA"]
    results["H_vent_W_K"] = thermal_props["H_vent"]
    results["H_total_W_K"] = thermal_props["H_total"]
    results["C_air_J_K"] = thermal_props["C_air"]
    results["C_J_K"] = thermal_props["C"]

    # Internal gains
    results["occupancy_factor"] = occ
    results["Q_people_W"] = Q_people
    results["Q_lights_W"] = Q_lights
    results["Q_equip_W"] = Q_equip
    results["Q_internal_W"] = Q_int

    # Solar gains
    results["Q_solar_W"] = Q_solar

    # Building response
    results["Tin_C"] = Tin
    results["Tin_free_C"] = Tin_free
    results["Q_natvent_W"] = Q_natvent
    results["Q_hvac_W"] = Q_hvac
    results["Q_heat_W"] = Q_heat
    results["Q_cool_W"] = Q_cool

    # Smoothed thermal loads
    results["Q_heat_smooth"] = results["Q_heat_W"].rolling(24).mean()
    results["Q_cool_smooth"] = results["Q_cool_W"].rolling(24).mean()

    # Heat pump
    results["COP"] = COP_t
    results["EER"] = EER_t
    results["heating_on"] = heating_on
    results["cooling_on"] = cooling_on
    results["P_heat_elec_W"] = P_heat_elec
    results["P_cool_elec_W"] = P_cool_elec
    results["P_hvac_elec_W"] = P_hvac_elec

    # Electricity
    results["P_base_elec_W"] = P_base_elec
    results["P_total_elec_W"] = P_total_elec

    # Hourly energy
    results["E_heat_elec_kWh"] = results["P_heat_elec_W"] / 1000.0
    results["E_cool_elec_kWh"] = results["P_cool_elec_W"] / 1000.0
    results["E_hvac_elec_kWh"] = results["P_hvac_elec_W"] / 1000.0
    results["E_base_elec_kWh"] = results["P_base_elec_W"] / 1000.0
    results["E_total_elec_kWh"] = results["P_total_elec_W"] / 1000.0

    # ============================================================
    # 9. EXPORT DATA
    # ============================================================

    csv_file = DATA_DIR / "brussels_hourly_profiles.csv"
    excel_file = DATA_DIR / "brussels_hourly_profiles.xlsx"

    results.to_csv(csv_file, index=True)

    try:
        results.to_excel(excel_file, index=True)
        print(f"Excel exporté : {excel_file}")
    except Exception as e:
        print(f"Export Excel impossible : {e}")

    # ============================================================
    # 10. DAILY / MONTHLY AGGREGATIONS
    # ============================================================

    daily = results.resample("D").sum(numeric_only=True)
    monthly = results.resample("ME").sum(numeric_only=True)

    daily_file = DATA_DIR / "brussels_daily_profiles.csv"
    monthly_file = DATA_DIR / "brussels_monthly_profiles.csv"

    daily.to_csv(daily_file, index=True)
    monthly.to_csv(monthly_file, index=True)

    # ============================================================
    # 11. SUMMARY
    # ============================================================

    summary = {
        "mean_indoor_temperature_C": results["Tin_C"].mean(),
        "mean_outdoor_temperature_C": results["Tout_C"].mean(),
        "annual_heating_electricity_kWh": results["E_heat_elec_kWh"].sum(),
        "annual_cooling_electricity_kWh": results["E_cool_elec_kWh"].sum(),
        "annual_hvac_electricity_kWh": results["E_hvac_elec_kWh"].sum(),
        "annual_base_electricity_kWh": results["E_base_elec_kWh"].sum(),
        "annual_total_electricity_kWh": results["E_total_elec_kWh"].sum(),
        "peak_heating_load_W": results["Q_heat_W"].max(),
        "peak_cooling_load_W": results["Q_cool_W"].max(),
        "peak_total_electric_power_W": results["P_total_elec_W"].max(),
    }

    summary_df = pd.DataFrame.from_dict(summary, orient="index", columns=["value"])
    summary_file = DATA_DIR / "summary_results.csv"
    summary_df.to_csv(summary_file)

    # ============================================================
    # 12. MAIN PLOTS
    # ============================================================

    plot_jobs = [
        {
            "x": results.index,
            "y_list": [results["P_heat_elec_W"], results["P_cool_elec_W"], results["P_hvac_elec_W"]],
            "labels": ["Heating electricity", "Cooling electricity", "Total HVAC electricity"],
            "title": "Heat pump electricity consumption",
            "ylabel": "Electric power [W]",
            "filename": "10_heat_pump_electricity.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["P_base_elec_W"], results["P_hvac_elec_W"], results["P_total_elec_W"]],
            "labels": ["Base electricity", "HVAC electricity", "Total electricity"],
            "title": "Electricity profiles",
            "ylabel": "Electric power [W]",
            "filename": "11_total_electricity.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["Tout_C"]],
            "labels": ["Outdoor temperature"],
            "title": "Brussels outdoor temperature profile",
            "ylabel": "Temperature [°C]",
            "filename": "01_outdoor_temperature.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["solar_Wm2"]],
            "labels": ["Solar radiation"],
            "title": "Brussels solar radiation profile",
            "ylabel": "Solar radiation [W/m²]",
            "filename": "02_solar_radiation.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["wind_m_s"]],
            "labels": ["Wind speed"],
            "title": "Brussels wind speed profile",
            "ylabel": "Wind speed [m/s]",
            "filename": "03_wind_speed.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["Tout_C"], results["Tin_C"], results["Tin_free_C"]],
            "labels": ["Outdoor temperature", "Indoor temperature", "Free-floating indoor temperature"],
            "title": "Indoor and outdoor temperatures",
            "ylabel": "Temperature [°C]",
            "filename": "04_indoor_outdoor_temperatures.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["Q_people_W"], results["Q_lights_W"], results["Q_equip_W"], results["Q_internal_W"]],
            "labels": ["People", "Lighting", "Equipment", "Total internal gains"],
            "title": "Internal gains profiles",
            "ylabel": "Power [W]",
            "filename": "05_internal_gains.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["Q_solar_W"], results["Q_internal_W"]],
            "labels": ["Solar gains", "Internal gains"],
            "title": "Solar and internal gains",
            "ylabel": "Power [W]",
            "filename": "06_solar_internal_gains.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["Q_heat_W"], results["Q_cool_W"]],
            "labels": ["Heating load", "Cooling load"],
            "title": "Heating and cooling loads",
            "ylabel": "Thermal load [W]",
            "filename": "07_heating_cooling_same_figure.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["Q_hvac_W"]],
            "labels": ["HVAC thermal power"],
            "title": "HVAC thermal power profile",
            "ylabel": "Power [W]",
            "filename": "08_hvac_thermal_power.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["Q_natvent_W"]],
            "labels": ["Natural ventilation effect"],
            "title": "Passive cooling by natural ventilation",
            "ylabel": "Power [W]",
            "filename": "09_natural_ventilation.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["P_heat_elec_W"], results["P_cool_elec_W"], results["P_hvac_elec_W"]],
            "labels": ["Heating electricity", "Cooling electricity", "Total HVAC electricity"],
            "title": "Heat pump electricity consumption",
            "ylabel": "Electric power [W]",
            "filename": "10_heat_pump_electricity.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["P_base_elec_W"], results["P_hvac_elec_W"], results["P_total_elec_W"]],
            "labels": ["Base electricity", "HVAC electricity", "Total electricity"],
            "title": "Electricity profiles",
            "ylabel": "Electric power [W]",
            "filename": "11_total_electricity.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": results.index,
            "y_list": [results["COP"], results["EER"]],
            "labels": ["COP", "EER"],
            "title": "Heat pump performance indicators",
            "ylabel": "Performance [-]",
            "filename": "12_cop_eer.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": daily.index,
            "y_list": [daily["E_total_elec_kWh"]],
            "labels": ["Daily total electricity"],
            "title": "Daily total electricity consumption",
            "ylabel": "Energy [kWh/day]",
            "filename": "13_daily_total_electricity.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": monthly.index,
            "y_list": [monthly["E_total_elec_kWh"]],
            "labels": ["Monthly total electricity"],
            "title": "Monthly total electricity consumption",
            "ylabel": "Energy [kWh/month]",
            "filename": "14_monthly_total_electricity.png",
            "show": SHOW_MAIN_PLOTS,
        },
        {
            "x": monthly.index,
            "y_list": [monthly["E_heat_elec_kWh"], monthly["E_cool_elec_kWh"]],
            "labels": ["Monthly heating electricity", "Monthly cooling electricity"],
            "title": "Monthly heating and cooling electricity",
            "ylabel": "Energy [kWh/month]",
            "filename": "15_monthly_heating_cooling.png",
            "show": SHOW_MAIN_PLOTS,
        },
    ]

    for job in plot_jobs:
        save_plot(
            x=job["x"],
            y_list=job["y_list"],
            labels=job["labels"],
            title=job["title"],
            ylabel=job["ylabel"],
            filename=job["filename"],
            show=job["show"],
        )

    # ============================================================
    # 13. FOCUS PLOTS
    # ============================================================

    winter_week = results.loc["2025-01-15":"2025-01-22"]
    summer_week = results.loc["2025-07-15":"2025-07-22"]

    save_plot(
        x=winter_week.index,
        y_list=[winter_week["Q_heat_W"], winter_week["Q_cool_W"]],
        labels=["Heating", "Cooling"],
        title="Heating and cooling - winter week",
        ylabel="Thermal load [W]",
        filename="16_winter_week_heating_cooling.png",
        show=SHOW_FOCUS_PLOTS,
    )

    save_plot(
        x=summer_week.index,
        y_list=[summer_week["Q_heat_W"], summer_week["Q_cool_W"]],
        labels=["Heating", "Cooling"],
        title="Heating and cooling - summer week",
        ylabel="Thermal load [W]",
        filename="17_summer_week_heating_cooling.png",
        show=SHOW_FOCUS_PLOTS,
    )

    save_plot(
        x=results.index,
        y_list=[results["Q_heat_smooth"], results["Q_cool_smooth"]],
        labels=["Heating (24h avg)", "Cooling (24h avg)"],
        title="Smoothed heating and cooling loads",
        ylabel="Thermal load [W]",
        filename="19_smoothed_heating_cooling.png",
        show=SHOW_FOCUS_PLOTS,
    )

    # ============================================================
    # 14. FINAL MESSAGES
    # ============================================================

    print()
    print("Simulation terminée ✔")
    print(f"CSV exporté : {csv_file}")
    print(f"CSV journalier exporté : {daily_file}")
    print(f"CSV mensuel exporté : {monthly_file}")
    print(f"Résumé exporté : {summary_file}")
    print(f"Nombre de figures générées : {len(list(PLOTS_DIR.glob('*.png')))}")
    print("Dossier plots :", PLOTS_DIR.resolve())
    print("Fichiers images :", list(PLOTS_DIR.glob('*.png')))
    print()
    print("Résumé annuel")

    # ============================================================
    # ADDITIONAL PERFORMANCE INDICATORS
    # ============================================================

    Q_heat_served_kWh = results["Q_heat_W"].sum() / 1000.0
    Q_cool_served_kWh = results["Q_cool_W"].sum() / 1000.0

    P_heat_elec_kWh = results["P_heat_elec_W"].sum() / 1000.0
    P_cool_elec_kWh = results["P_cool_elec_W"].sum() / 1000.0

    SCOP = Q_heat_served_kWh / P_heat_elec_kWh if P_heat_elec_kWh > 0 else np.nan
    SEER = Q_cool_served_kWh / P_cool_elec_kWh if P_cool_elec_kWh > 0 else np.nan

    hours_over_26 = (results["Tin_C"] > 26.0).sum()
    hours_below_18 = (results["Tin_C"] < 18.0).sum()

    analysis = {
        "annual_heating_thermal_kWh": Q_heat_served_kWh,
        "annual_cooling_thermal_kWh": Q_cool_served_kWh,
        "annual_heating_electric_kWh": P_heat_elec_kWh,
        "annual_cooling_electric_kWh": P_cool_elec_kWh,
        "SCOP": SCOP,
        "SEER": SEER,
        "hours_Tin_above_26C": hours_over_26,
        "hours_Tin_below_18C": hours_below_18,
    }



    analysis_df = pd.DataFrame.from_dict(analysis, orient="index", columns=["value"])
    analysis_file = DATA_DIR / "analysis_results.csv"
    analysis_df.to_csv(analysis_file)



    print("\nAnalyse complémentaire")
    for key, value in analysis.items():
        if isinstance(value, (int, np.integer)):
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value:.2f}")

    for key, value in summary.items():
        print(f"{key}: {value:.2f}")


if __name__ == "__main__":
    main()
