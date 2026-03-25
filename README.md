# building-energy-model-brussels
Dynamic building energy simulation using a simplified RC model. Includes heating, cooling, solar gains, and heat pump electricity modeling for Brussels climate.

# 🏠 Building Energy Simulation – Brussels nZEB

This project simulates the thermal behavior and energy consumption of a residential building located in Brussels.

It computes:
- Indoor temperature
- Heating and cooling demand
- Heat pump electricity consumption

---

## ⚙️ Model Description

The model is based on a simplified energy balance:

C · dT/dt = H · (Tout - Tin) + Qsolar + Qinternal + Qhvac

Main components:
- Weather data (temperature, solar radiation)
- Solar gains through windows
- Internal gains (people, lighting, equipment)
- HVAC system (heating + cooling)
- Heat pump (COP / EER model)

---

## 📁 Project Structure
via/scr

---

## 📊 Outputs

The simulation generates:
- CSV files (hourly, daily, monthly results)
- Plots (temperature, loads, electricity)

---

## 📌 Key Assumptions

- Single-zone building model  
- Cooling setpoint: 26°C  
- Heating setpoint: 17–21°C (schedule-based)  
- Simplified solar and occupancy models  

