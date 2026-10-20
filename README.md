# MotoMind — Self-Learning EV Health Intelligence System

**MotoMind** is an end-to-end, modular software platform supporting both **Electric Two-Wheelers (E2W)** (e.g. 52V commuter scooter) and **Electric Four-Wheelers (E4W)** (e.g. 400V dual-motor sedan). It features **EV Vehicle Health Monitoring**, **Self-Learning AI Anomaly Detection**, and **Virtual OTA Software Update Validation**.

Built with a **FastAPI (Python)** backend, **scikit-learn** Isolation Forest machine learning, **SQLite/SQLAlchemy** persistence, and a modern **React + TypeScript + Vite + Tailwind CSS** frontend.

---

## Key System Modules & Multi-Vehicle Architecture

1. **Configurable Vehicle Profile Registry**:
   - **Apex Urban 2W (Scooter)**: 52V NMC (14S), 3.2 kWh usable, 65A peak discharge, mid-drive BLDC motor, passive air-cooling, 32 Wh/km nominal consumption.
   - **Vanguard GT 4W (Sedan)**: 400V (96S-108S), 64 kWh usable, 320A peak discharge, dual PMSM/induction motors (220 kW), active liquid glycol cooling loop, cabin HVAC, High Voltage Interlock Loop (HVIL), 165 Wh/km nominal consumption.
   - Dynamic profile switching via the UI header or REST API (`/api/simulator/switch-vehicle`).

2. **Adaptive EV Vehicle Health Monitoring Engine**:
   - Continuous timestamped physics simulation tailored to each vehicle's architecture.
   - Tracks: Battery Voltage, Current, Battery Temp, Primary Motor Temp, Secondary Motor Temp (4W), Coolant Temp (4W), Cabin HVAC Temp (4W), Insulation Resistance (4W), Speed, Wh/km, SOC, SOH, Moisture status (2W), DTC fault codes.
   - **Explicit Sensor Availability & Provenance**: Every sensor reading is strictly marked as `measured`, `simulated`, `estimated`, or `unavailable` (e.g. coolant loop is unavailable on air-cooled 2W without raising false alerts; moisture sensor is unavailable on sealed 4W chassis).
   - Injected fault testbench with vehicle-specific faults:
     - **2W & Universal**: Battery Over-Temp, Motor Overheat, Sudden Voltage Sag, Overcurrent Surge, Moisture Ingress, Sensor Drift, CAN Disconnect, Cell Imbalance.
     - **4W Specific**: Coolant Pump Failure (>70°C derate), Rear Motor Overheat, High Voltage Isolation Breakdown (<100 kΩ contactor trip).

3. **Self-Learning AI Engine (Dual Isolation Forest Baselines)**:
   - Unsupervised multivariate outlier detection using `scikit-learn`.
   - **Independent Baselines**: Separate models and feature matrices for 2W (7 dimensions) and 4W (8 dimensions including coolant loop) to prevent high-voltage/low-voltage distribution cross-contamination.
   - **Baseline Safeguard**: Filters out known fault data and hardware trips so suspicious anomalies are never absorbed into normal operating envelopes.
   - Feature attribution explainability (Z-score deviation per feature dimension).

4. **Transparent Range Estimator**:
   - Instantaneous range calculation scaled for vehicle mass and usable capacity (3.2 kWh for 2W vs 64 kWh for 4W), dynamic Wh/km consumption rate, optional elevation climb, and traffic factors.
   - Transparently displays uncertainty intervals and mathematical assumptions without false claims of external map connections.

5. **Component Lifecycle & Service Mode**:
   - Separate component records and histories per vehicle ID.
   - "Establish New Baseline" action upon component installation (Battery Pack, Traction Motor, BMS Module, Coolant Pump).
   - **Service Mode Hold**: Mark maintenance windows to suppress false driving alerts.
   - Water exposure logging with clear non-diagnostic disclosures.
   - Before vs. After service health score delta comparison.

6. **Virtual OTA Software Update Validation Module**:
   - Independent virtual testing harness completely isolated from live vehicle health telemetry.
   - **Dual Test Suites**:
     - **Two-Wheeler Suite (12 scenarios)**: 52V commuter pack boundaries, 55°C thermal cutoff, subzero charging inhibit, and CAN timeout.
     - **Four-Wheeler Suite (12 scenarios)**: 400V high-voltage boundaries, CCS2 DC fast-charge taper, 52°C pack cutoff, subzero DC fast charge inhibit, 450V over-voltage trip, High Voltage Interlock Loop (HVIL) open-circuit trip, dual-motor torque sync, coolant loop pump failure derating, and chassis HV isolation breach.
   - **Built-in Deliberate Regression Demonstrations**:
     - 2W regression demo: Candidate bypasses high-temperature cutoff (`BLOCK`).
     - 4W regression demo: Candidate bypasses high-temperature cutoff and HVIL trip (`BLOCK`).
   - **Clean Passing Demonstrations**:
     - Verified candidates for both 2W and 4W passing all 12 safety assertions (`PASS`).
   - Downloadable structured JSON audit reports.

---

## System Architecture

```
motomind 2/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routers (simulator, telemetry, health, anomaly, ota, service, export, ws)
│   │   ├── ml/              # Multi-vehicle Isolation Forest baselines (2W & 4W models)
│   │   ├── models/          # SQLAlchemy database models with vehicle_id & vehicle_type
│   │   ├── ota/             # Virtual BMS, 2W & 4W scenario suites, validation runner
│   │   ├── schemas/         # Pydantic data schemas & switch requests
│   │   ├── services/        # Adaptive health engine, scaled range estimator
│   │   ├── simulator/       # Multi-vehicle physics simulator
│   │   ├── vehicle_profiles.py # Modular VehicleProfileRegistry (E2W & E4W)
│   │   ├── config.py        # Central configuration & thresholds
│   │   └── main.py          # FastAPI application factory & lifespan
│   ├── scripts/
│   │   ├── seed_db.py       # Database seeding script (2W & 4W versions, components, services)
│   │   └── generate_synthetic_data.py # Offline dataset generator
│   └── tests/               # 24 automated pytest test cases
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed API & WebSocket client
│   │   ├── components/      # Sidebar, Header (with vehicle selector), NotificationDrawer
│   │   ├── pages/           # Overview, LiveMonitoring, AiIntelligence, VehicleService, OtaValidation, Settings
│   │   ├── types/           # TypeScript interfaces
│   │   ├── App.tsx          # Root application layout with multi-vehicle state
│   │   └── main.tsx         # Entrypoint
│   └── dist/                # Production Vite build
├── requirements.txt         # Python dependencies
├── pytest.ini               # Pytest configuration
├── run_backend.bat / .ps1   # Backend launcher
└── run_frontend.bat / .ps1  # Frontend launcher
```

---

## Local Setup & Quick Start

### Prerequisites
- Python 3.10+ (Tested on Python 3.14)
- Node.js 18+ and npm

### 1. Backend Setup
```powershell
# Create Python virtual environment (if not already created)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize & seed SQLite database with 2W and 4W profiles, versions, and components
python backend/scripts/seed_db.py
```

### 2. Frontend Setup
```powershell
cd frontend
npm install
npm run build   # Production compile
cd ..
```

### 3. Launching the Application
You can start both services using the provided launcher scripts or commands:

**Terminal 1 (Backend - Port 8000):**
```powershell
.\run_backend.ps1
# Or: .\venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation (Swagger UI) is available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

**Terminal 2 (Frontend - Port 5173):**
```powershell
.\run_frontend.ps1
# Or: cd frontend; npm run dev
```
Open your browser at: [http://127.0.0.1:5173](http://127.0.0.1:5173)

---

## Running Automated Tests

MotoMind includes 24 comprehensive unit and integration tests covering multi-vehicle profiles, adaptive health evaluation, ML Isolation Forest baselines, OTA assertion suites, and REST endpoints:

```powershell
.\venv\Scripts\pytest -v
```

All 24 tests pass with 100% success rate:
- `test_multi_vehicle.py`: Profile registry, vehicle switching, 4W telemetry properties, adaptive health engine (skipping coolant checks on 2W, enforcing on 4W), multi-vehicle ML isolation, 4W HVIL and over-voltage trips, and OTA 4W scenarios.
- `test_simulator.py`: Nominal steps, start/pause/reset, fault injection, operating profiles.
- `test_health_engine.py`: Normal points, battery overtemperature (>55°C), sensor disconnect handling.
- `test_ml_anomaly.py`: Isolation Forest training, normal vs. outlier scoring, explainability Z-scores.
- `test_ota_validation.py`: Virtual BMS logic, deliberate regression detection (BLOCK), clean candidate verification (PASS).
- `test_api_endpoints.py`: REST endpoints, simulator controls, telemetry history, range estimation, and OTA demo endpoints.

---

## How to Test the Multi-Vehicle Workflows

1. **Switching Between Two-Wheeler and Four-Wheeler**:
   - In the top header, click the vehicle selector pill.
   - Switch between **Apex Urban 2W (Scooter - 52V • 3.2kWh)** and **Vanguard GT 4W (Sedan - 400V • 64kWh)**.
   - Notice that the voltage scale updates (52V nominal vs 400V nominal), the cooling indicator adapts (air-cooled vs liquid-cooled loop), and sensor provenance updates.

2. **Vehicle-Specific Sensor Availability & Health**:
   - On the **Overview** page, inspect the *Sensor Availability & Provenance Tagging* card:
     - On 2W, Coolant Loop, Secondary Motor, and HVIL are labeled `unavailable` without triggering false alarms.
     - On 4W, Coolant Loop, Secondary Motor, and HVIL are active and supervised.
   - Check the *Transparent Range Estimation Model* which scales from 3.2 kWh to 64 kWh automatically.

3. **Multi-Vehicle Fault Injection & Real-Time Monitoring**:
   - On **Live Monitoring**, switch to the 4W Sedan.
   - The Voltage chart adapts its Y-axis domain dynamically to 320V–460V, and the thermal chart displays Coolant Loop and Rear Motor lines.
   - Select **Coolant Pump Thermal Failure** or **HV Chassis Isolation Loss** and click **Inject Selected Fault**.
   - Observe the health engine flag `WARN_COOLANT_HIGH_TEMP` or open contactors for isolation breach.

4. **Self-Learning AI Baselines**:
   - On **AI Health Intelligence**, notice the active vehicle badge and feature vector (7 features for 2W vs 8 features for 4W).
   - Click **Retrain 4W Baseline** to train the four-wheeler Isolation Forest on 400V distributions without affecting the 2W baseline.

5. **OTA Validation for 2W and 4W**:
   - On the **OTA Validation Center**, toggle between **Two-Wheeler Suite** and **Four-Wheeler Suite**.
   - Click **Run Deliberate Regression Demo (BLOCK)**:
     - For 4W, it tests candidate `v4.2.0-rc1-regressed` against `v4.1.0-sedan-stable`, catching thermal cutoff bypass and issuing **BLOCK**.
   - Click **Run Clean Candidate (PASS)**:
     - For 4W, verified candidate `v4.2.0-rc2-verified` runs all 12 400V high-voltage assertions and outputs **PASS**.

---

## Physical Safety & Regulatory Disclosures

- **Simulation Sandbox**: This platform is a software simulation and virtual testbed. It does not connect to live high-voltage traction batteries or physical motor inverters.
- **OTA Virtual Validation**: Virtual test results validate logical behavioral assertions within simulated scenarios and do not constitute physical vehicle road safety certification or formal ISO 26262 compliance.
- **Informational Warnings**: Anomaly scores and service recommendations are informational algorithmic suggestions and do not replace professional hands-on technician diagnosis.
