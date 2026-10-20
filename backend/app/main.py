import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import settings
from .models.database import init_db, SessionLocal, TelemetryRecord
from .simulator.vehicle_simulator import vehicle_simulator
from .api.simulator import router as simulator_router
from .api.telemetry import router as telemetry_router
from .api.health import router as health_router
from .api.anomaly import router as anomaly_router
from .api.ota import router as ota_router
from .api.service import router as service_router
from .api.export import router as export_router
from .api.websocket import router as ws_router

def db_telemetry_saver(point):
    """Periodically persist every 5th tick to SQLite while maintaining history."""
    if point.id is None and vehicle_simulator.tick_count % 5 == 0:
        db = SessionLocal()
        try:
            record = TelemetryRecord(
                timestamp=point.timestamp,
                vehicle_id=point.vehicle_id,
                vehicle_type=point.vehicle_type,
                battery_voltage=point.battery_voltage,
                battery_current=point.battery_current,
                battery_temperature=point.battery_temperature,
                state_of_charge=point.state_of_charge,
                state_of_health=point.state_of_health,
                motor_temperature=point.motor_temperature,
                secondary_motor_temperature=point.secondary_motor_temperature,
                coolant_temperature=point.coolant_temperature,
                cabin_temperature=point.cabin_temperature,
                hvac_power_kw=point.hvac_power_kw,
                insulation_resistance_kohm=point.insulation_resistance_kohm,
                vehicle_speed=point.vehicle_speed,
                energy_consumption=point.energy_consumption,
                charging_status=point.charging_status,
                ambient_temperature=point.ambient_temperature,
                moisture_status=point.moisture_status,
                sensor_fault_status=point.sensor_fault_status,
                fault_codes=point.fault_codes,
                power_kw=point.power_kw,
                temp_delta=point.temp_delta,
                data_source_type=point.data_source_type,
                sensor_availability=point.sensor_availability,
                operating_context=point.operating_context,
                service_mode_active=point.service_mode_active
            )
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    vehicle_simulator.start_background_loop(db_callback=db_telemetry_saver)
    yield
    vehicle_simulator.stop_background_loop()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Full-stack multi-vehicle EV health monitoring, self-learning anomaly detection, and virtual OTA software update validation system for electric two-wheelers and four-wheelers.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(simulator_router, prefix="/api")
app.include_router(telemetry_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(anomaly_router, prefix="/api")
app.include_router(ota_router, prefix="/api")
app.include_router(service_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(ws_router, prefix="/api")

@app.get("/")
def root():
    return {
        "system": "MotoMind Multi-Vehicle EV Health & OTA Validation System",
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "supported_categories": ["Electric Two-Wheeler (E2W)", "Electric Four-Wheeler (E4W)"],
        "docs_url": "/docs",
        "disclaimer": "Synthetic simulation prototype. Real-vehicle deployment requires physical BMS & hardware sensor calibration."
    }

@app.get("/healthz")
def healthz():
    return {
        "status": "HEALTHY",
        "active_vehicle_id": vehicle_simulator.active_vehicle_id,
        "active_vehicle_type": vehicle_simulator.get_active_state().vehicle_type,
        "simulator_running": vehicle_simulator.is_running,
        "active_profile": vehicle_simulator.current_profile,
        "active_fault": vehicle_simulator.active_injected_fault
    }
