import os

class Settings:
    PROJECT_NAME: str = "MotoMind — Self-Learning EV Health Intelligence System"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./motomind.db")
    SIMULATION_INTERVAL_SEC: float = float(os.getenv("SIMULATION_INTERVAL_SEC", "1.0"))
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ]
    # Synthetic battery & motor nominal specs for Electric Two-Wheeler (e.g. 52V pack, 3.2 kWh, 4kW motor)
    NOMINAL_PACK_VOLTAGE: float = 52.0  # Volts
    PACK_CAPACITY_KWH: float = 3.2     # Usable battery capacity in kWh
    NOMINAL_MAX_CURRENT: float = 65.0  # Peak discharge current (Amps)
    NORMAL_MAX_TEMP_BATTERY: float = 48.0 # Deg C warning threshold
    CRITICAL_MAX_TEMP_BATTERY: float = 55.0 # Deg C cutoff assertion threshold
    NORMAL_MAX_TEMP_MOTOR: float = 85.0   # Deg C warning threshold
    CRITICAL_MAX_TEMP_MOTOR: float = 105.0 # Deg C cutoff threshold

settings = Settings()
