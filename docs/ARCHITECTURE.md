# MotoMind — System Architecture & Engineering Specifications

MotoMind is a modular self-learning EV health intelligence and virtual OTA software update validation platform designed for electric two-wheelers.

```mermaid
flowchart TD
    subgraph EV Health Monitoring Pipeline
        A[Physics Telemetry Simulator] -->|Timestamped Raw Data| B[Data Processing & Validation]
        B -->|Feature Extraction| C1[Deterministic Rule Engine]
        B -->|Vector Scaling| C2[Isolation Forest AI Engine]
        C1 --> D[Health Assessment Engine]
        C2 --> D
        D -->|Health Scores & Anomaly Events| E[Owner Dashboard & Real-Time Alerts]
        D -->|Time Series Persist| DB[(SQLite Database)]
        E <-->|Service Mode & Maintenance| F[Component & Service Manager]
    end

    subgraph Virtual OTA Validation Pipeline (Strictly Isolated)
        V1[Reference Firmware Profile\nv2.4.1-stable] --> T[OTA Test Runner]
        V2[Candidate Firmware Profile\ne.g. v2.5.0-rc1] --> T
        SC[12 Automated Test Scenarios\nSafety & Edge Conditions] --> T
        T -->|Comparative Assertions| R{Result Evaluation}
        R -->|Pass All Assertions| P[VERDICT: PASS]
        R -->|Safety Assertion Failed| B2[VERDICT: BLOCK]
        R --> REP[Audit Validation Report\nJSON / Web View]
    end
```

---

## 1. EV Health Monitoring Pipeline

### A. Physics Telemetry Simulator (`backend/app/simulator/vehicle_simulator.py`)
- Simulates a nominal 52V, 3.2 kWh battery pack (~14S Li-ion / 16S LFP chemistry) coupled with a 4.0 kW peak traction motor.
- **Coulomb Counting**:
  $$\text{SOC}_{t} = \text{SOC}_{t-1} - \frac{I \cdot \Delta t}{3600 \cdot C_{\text{Ah}}} \times 100$$
- **Voltage Sag Modeling**:
  $$V_{\text{terminal}} = V_{\text{oc}}(\text{SOC}) - I \cdot R_{\text{internal}}$$
- **Thermal Heat Generation & Airflow Cooling**:
  $$\dot{Q}_{\text{batt}} = I^2 R_{\text{int}} - k_{\text{cool}}(T_{\text{batt}} - T_{\text{amb}}) - k_{\text{air}} v_{\text{speed}}$$
- **Profiles**:
  - `city_commute`: Stop-and-go acceleration (0-48 km/h), regenerative braking (-8A to -14A), idle traffic stops.
  - `aggressive_sport`: High current discharge surges (30A to 55A) and high thermal buildup.
  - `eco_cruising`: Steady cruising speed (40-45 km/h) with optimal 28 Wh/km consumption.
  - `idle_charging`: Stationary vehicle ($v=0$) with AC grid charging current (-10A to -14A).

### B. Self-Learning AI Module (`backend/app/ml/anomaly_model.py`)
- Unsupervised **Isolation Forest** trained using `scikit-learn`.
- **Feature Vector**:
  $$\mathbf{x} = [V_{\text{batt}}, I_{\text{batt}}, T_{\text{batt}}, T_{\text{motor}}, v_{\text{speed}}, P_{\text{kW}}, \Delta T]$$
- **Contamination Safeguard**: The baseline update routine filters out known fault codes and extreme hardware trips ($T > 48^\circ\text{C}$, $I > 55\text{A}$) to prevent absorbing faulty behaviors into the normal profile.
- **Explainability**: Calculates individual feature Z-score deviations from the learned baseline mean.

### C. Range Estimation Model (`backend/app/services/range_estimator.py`)
- Calculates remaining distance based on instantaneous SOC, usable capacity, dynamic Wh/km consumption, elevation climb potential energy, and traffic factors.
- Displays explicit assumptions and uncertainty bands ($\pm 15\%$).

---

## 2. OTA Software Update Validation Pipeline

The OTA validation module operates as an independent virtual test environment. Results from the OTA suite are isolated from vehicle health telemetry.

### A. Virtual BMS Architecture (`backend/app/ota/virtual_bms.py`)
- Evaluates candidate firmware behavioral profiles against reference configurations.
- Monitors contactor states, allowed charge/discharge currents, and thermal derate modes.

### B. The 12 Automated Test Scenarios (`backend/app/ota/test_scenarios.py`)
1. `TC-001-NORMAL-OPERATING`: Standard cruising current and contactor retention.
2. `TC-002-BOUNDARY-VALUE`: Upper SOC boundary charge current tapering.
3. `TC-003-BATTERY-OVERTEMP`: **Safety Critical** high-temperature cutoff assertion (>55.0°C).
4. `TC-004-BATTERY-UNDERTEMP`: Subzero charging inhibit logic (<0°C).
5. `TC-005-OVER-UNDER-VOLTAGE`: Pack overvoltage contactor trip (>58.8V).
6. `TC-006-OVERCURRENT-PROTECT`: Surge current disconnect (>65A).
7. `TC-007-CHARGING-SAFETY`: Charger plug-in drive interlock.
8. `TC-008-SOC-SOH-FAULT`: Sensor value corrupt frames handling.
9. `TC-009-SENSOR-DRIFT-DISCONNECT`: Analog sensor signal loss limp mode.
10. `TC-010-CAN-COMM-TIMEOUT`: CAN bus watchdog timeout (>250ms).
11. `TC-011-INVALID-STALE-DATA`: Impossible value quarantine.
12. `TC-012-REGRESSION-REFERENCE`: Direct envelope comparison against reference version.

### C. Deliberate Regression Demonstration
- Candidate profile `v2.5.0-rc1-regressed` simulates an accidental bypass of the high-temperature emergency cutoff assertion.
- When tested under 56.5°C battery temperature, candidate fails TC-003.
- The validation engine marks the regression and outputs **BLOCK**.
- Resetting to `v2.5.0-clean` executes all 12 scenarios with zero regressions and outputs **PASS**.

---

## 3. Physical & Virtual Safety Boundaries
- **No Physical Wiring**: Does not connect to live high-voltage traction batteries.
- **No Remote Firmware Execution**: Does not flash or deploy real binaries to physical microcontrollers.
- **Simulation Disclaimer**: Simulation pass/fail status is for testing prototype architectures and does not replace ISO 26262 functional safety road certification.
