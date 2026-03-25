from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from loading import load_weather
from geometry import compute_geometry
from thermal import compute_thermal_properties
from solar_gain import compute_solar_gain
from internal_gain import compute_internal_gains
from simulation import run_simulation, heating_setpoint
from cop import compute_heat_pump_electricity
from assumption import T_cool_set


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_PLOTS_DIR = OUTPUT_DIR / "plots"
OUTPUT_DATA_DIR = OUTPUT_DIR / "data"

WEATHER_FILE = RAW_DATA_DIR / "brussels_weather_2025.csv"

SHOW_MAIN_PLOTS = False
SHOW_FOCUS_PLOTS = True


# ============================================================
# HELPERS
# ============================================================

def ensure_output_folders():
    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_PLOTS_DIR.mkdir(exist_ok=True)
    OUTPUT_DATA_DIR.mkdir(exist_ok=True)


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

        output_file = OUTPUT_PLOTS_DIR / filename
        plt.savefig(output_file, dpi=300)

        if show:
            plt.show()

        plt.close()
        print(f"Plot OK: {filename}")

    except Exception as e:
        print(f"Erreur plot {filename}: {e}")
        plt.close()


def save_step_plot(x, y, title, ylabel, filename, show=False):
    try:
        plt.figure(figsize=(14, 4))
        plt.step(x, y, where="post", label="Setpoint")
        plt.title(title)
        plt.xlabel("Time")
        plt.ylabel(ylabel)
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        output_file = OUTPUT_PLOTS_DIR / filename
        plt.savefig(output_file, dpi=300)

        if show:
            plt.show()

        plt.close()
        print(f"Step plot OK: {filename}")

    except Exception as e:
        print(f"Erreur step plot {filename}: {e}")
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

    COP_t = np.asarray(hp_results["COP_t"], dtype=float)
    EER_t = np.asarray(hp_results["EER_t"], dtype=float)
    Q_heat_served = np.asarray(hp_results["Q_heat_served"], dtype=float)
    Q_cool_served = np.asarray(hp_results["Q_cool_served"], dtype=float)
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
    # 8. SETPOINT PROFILES
    # ============================================================

    T_heat_set_profile = np.array([heating_setpoint(ts) for ts in time_index], dtype=float)
    T_cool_set_profile = np.full(len(time_index), T_cool_set, dtype=float)

    # ============================================================
    # 9. BUILD FINAL DATAFRAME
    # ============================================================

    results = pd.DataFrame(index=time_index)

    # Climate
    results["Tout_C"] = Tout
    results["solar_Wm2"] = G_solar
    results["wind_m_s"] = wind

    # Geometry
    results["A_wall_total_m2"] = geom["A_wall_total"]
    results["A_wall_opaque_m2"] = geom["A_wall_opaque"]
    results["A_window_m2"] = geom["A_window"]
    results["A_roof_m2"] = geom["A_roof"]
    results["A_ground_m2"] = geom["A_ground"]

    # Thermal properties
    results["UA_W_K"] = thermal_props["UA"]
    results["H_vent_W_K"] = thermal_props["H_vent"]
    results["H_total_W_K"] = thermal_props["H_total"]
    results["C_air_J_K"] = thermal_props["C_air"]
    results["C_J_K"] = thermal_props["C"]

    # Setpoints
    results["T_heat_set_C"] = T_heat_set_profile
    results["T_cool_set_C"] = T_cool_set_profile

    # Internal gains
    results["occupancy_factor"] = occ
    results["Q_people_W"] = Q_people
    results["Q_lights_W"] = Q_lights
    results["Q_equip_W"] = Q_equip
    results["Q_internal_W"] = Q_int

    # Solar
    results["Q_solar_W"] = Q_solar

    # Dynamic building response
    results["Tin_C"] = Tin
    results["Tin_free_C"] = Tin_free
    results["Q_natvent_W"] = Q_natvent
    results["Q_hvac_W"] = Q_hvac
    results["Q_heat_W"] = Q_heat
    results["Q_cool_W"] = Q_cool

    # Smoothed loads
    results["Q_heat_smooth"] = results["Q_heat_W"].rolling(24).mean()
    results["Q_cool_smooth"] = results["Q_cool_W"].rolling(24).mean()

    # Heat pump
    results["COP"] = COP_t
    results["EER"] = EER_t
    results["heating_on"] = heating_on
    results["cooling_on"] = cooling_on
    results["Q_heat_served_W"] = Q_heat_served
    results["Q_cool_served_W"] = Q_cool_served
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

    # Comfort indicators
    results["over_26C"] = (results["Tin_C"] > 26.0).astype(int)
    results["below_18C"] = (results["Tin_C"] < 18.0).astype(int)

    # ============================================================
    # 10. EXPORT DATA
    # ============================================================

    csv_file = OUTPUT_DATA_DIR / "brussels_hourly_profiles.csv"
    excel_file = OUTPUT_DATA_DIR / "brussels_hourly_profiles.xlsx"

    results.to_csv(csv_file, index=True)

    try:
        results.to_excel(excel_file, index=True)
        print(f"Excel exporté : {excel_file}")
    except Exception as e:
        print(f"Export Excel impossible : {e}")

    # ============================================================
    # 11. DAILY / MONTHLY AGGREGATIONS
    # ============================================================

    daily = results.resample("D").sum(numeric_only=True)
    monthly = results.resample("ME").sum(numeric_only=True)

    daily_file = OUTPUT_DATA_DIR / "brussels_daily_profiles.csv"
    monthly_file = OUTPUT_DATA_DIR / "brussels_monthly_profiles.csv"

    daily.to_csv(daily_file, index=True)
    monthly.to_csv(monthly_file, index=True)

    # ============================================================
    # 12. SUMMARY
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
    summary_file = OUTPUT_DATA_DIR / "summary_results.csv"
    summary_df.to_csv(summary_file)

    # ============================================================
    # 13. ADDITIONAL ANALYSIS
    # ============================================================

    Q_heat_served_kWh = results["Q_heat_served_W"].sum() / 1000.0
    Q_cool_served_kWh = results["Q_cool_served_W"].sum() / 1000.0

    P_heat_elec_kWh = results["P_heat_elec_W"].sum() / 1000.0
    P_cool_elec_kWh = results["P_cool_elec_W"].sum() / 1000.0

    SCOP = Q_heat_served_kWh / P_heat_elec_kWh if P_heat_elec_kWh > 0 else np.nan
    SEER = Q_cool_served_kWh / P_cool_elec_kWh if P_cool_elec_kWh > 0 else np.nan

    hours_over_26 = int((results["Tin_C"] > 26.0).sum())
    hours_below_18 = int((results["Tin_C"] < 18.0).sum())

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
    analysis_file = OUTPUT_DATA_DIR / "analysis_results.csv"
    analysis_df.to_csv(analysis_file)

    # ============================================================
    # 14. MAIN PLOTS
    # ============================================================

    plot_jobs = [
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
    # 15. FOCUS PLOTS
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

    # Setpoint profile example
    week = results.loc["2025-03-01":"2025-03-07"]
    T_week = np.array([heating_setpoint(ts) for ts in week.index], dtype=float)

    save_step_plot(
        x=week.index,
        y=T_week,
        title="Heating setpoint schedule (example week)",
        ylabel="Temperature [°C]",
        filename="18_heating_setpoint_profile.png",
        show=SHOW_FOCUS_PLOTS,
    )

    # ============================================================
    # 16. FINAL MESSAGES
    # ============================================================

    print()
    print("Simulation terminée ✔")
    print(f"CSV exporté : {csv_file}")
    print(f"Excel exporté : {excel_file}")
    print(f"CSV journalier exporté : {daily_file}")
    print(f"CSV mensuel exporté : {monthly_file}")
    print(f"Résumé exporté : {summary_file}")
    print(f"Analyse exportée : {analysis_file}")
    print(f"Nombre de figures générées : {len(list(OUTPUT_PLOTS_DIR.glob('*.png')))}")
    print("Dossier plots :", OUTPUT_PLOTS_DIR.resolve())
    print("Fichiers images :", list(OUTPUT_PLOTS_DIR.glob("*.png")))
    print()

    print("Analyse complémentaire")
    for key, value in analysis.items():
        if isinstance(value, (int, np.integer)):
            print(f"{key}: {value}")
        else:
            print(f"{key}: {value:.2f}")

    print()
    print("Résumé annuel")
    for key, value in summary.items():
        print(f"{key}: {value:.2f}")


if __name__ == "__main__":
    main()
