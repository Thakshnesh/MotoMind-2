from typing import Dict, Any, List
from ..vehicle_profiles import profile_registry
from ..schemas.health import RangeEstimationRequest, RangeEstimationResponse

class RangeEstimator:
    """
    Adaptive Multi-Vehicle Range Estimator.
    Calculates driving range tailored to 2W vs 4W battery capacity, vehicle mass,
    observed Wh/km consumption, elevation, and traffic drag factors.
    """

    @staticmethod
    def estimate_range(req: RangeEstimationRequest, current_telemetry: Dict[str, Any] = None) -> RangeEstimationResponse:
        vid = req.vehicle_id or (current_telemetry.get("vehicle_id") if current_telemetry else "E2W-SCOOT-01")
        profile = profile_registry.get_profile(vid)
        v_type = profile.vehicle_type

        # Determine SOC
        soc = req.battery_soc
        if soc is None:
            if current_telemetry:
                soc = current_telemetry.get("state_of_charge", 80.0)
            else:
                soc = 80.0

        # Usable capacity
        capacity_kwh = req.battery_capacity_kwh or profile.battery.usable_capacity_kwh
        usable_total_wh = capacity_kwh * 1000.0
        usable_remaining_wh = round(usable_total_wh * (soc / 100.0), 1)

        # Baseline consumption
        if req.average_consumption_wh_km:
            base_consumption = req.average_consumption_wh_km
        elif current_telemetry and current_telemetry.get("energy_consumption"):
            base_consumption = current_telemetry.get("energy_consumption")
        else:
            base_consumption = profile.dynamics.nominal_consumption_wh_km

        assumptions = []
        assumptions.append(f"Vehicle: {profile.display_name} ({profile.category_label}).")
        assumptions.append(f"Configured usable battery capacity: {capacity_kwh:.1f} kWh ({usable_total_wh:.0f} Wh).")
        assumptions.append(f"State of Charge (SOC) is {soc:.1f}%, yielding ~{usable_remaining_wh:.0f} Wh usable energy.")
        assumptions.append(f"Base energy consumption rate: {base_consumption:.1f} Wh/km based on dynamic driving profile.")

        adjusted_consumption = base_consumption

        # Elevation adjustment
        if req.elevation_gain_m and req.elevation_gain_m > 0:
            mass_kg = profile.dynamics.curb_weight_kg + (75.0 if v_type == "two_wheeler" else 150.0)
            climb_energy_wh = (mass_kg * 9.81 * req.elevation_gain_m) / (3600.0 * 0.78)
            trip_km = req.route_distance_km or (25.0 if v_type == "two_wheeler" else 80.0)
            elev_wh_per_km = climb_energy_wh / max(1.0, trip_km)
            adjusted_consumption += elev_wh_per_km
            assumptions.append(f"Added {elev_wh_per_km:.1f} Wh/km overhead for {req.elevation_gain_m:.0f}m elevation gain with {mass_kg:.0f} kg total vehicle mass.")

        # Traffic factor
        if req.traffic_factor and req.traffic_factor != 1.0:
            adjusted_consumption *= req.traffic_factor
            traffic_pct = (req.traffic_factor - 1.0) * 100
            assumptions.append(f"Adjusted consumption by +{traffic_pct:.0f}% for urban stop-and-go congestion.")

        min_wh = 15.0 if v_type == "two_wheeler" else 100.0
        max_wh = 90.0 if v_type == "two_wheeler" else 380.0
        adjusted_consumption = max(min_wh, min(max_wh, adjusted_consumption))

        nominal_range = usable_remaining_wh / adjusted_consumption
        min_range = round(nominal_range * 0.85, 1)
        max_range = round(nominal_range * 1.15, 1)
        nominal_range = round(nominal_range, 1)

        assumptions.append("Uncertainty interval (±15%) accounts for ambient temperature variance, headwind, and tire pressure fluctuations.")

        return RangeEstimationResponse(
            vehicle_id=profile.vehicle_id,
            vehicle_type=v_type,
            estimated_range_km=nominal_range,
            confidence_interval_min_km=min_range,
            confidence_interval_max_km=max_range,
            usable_energy_remaining_wh=usable_remaining_wh,
            assumed_consumption_wh_km=round(adjusted_consumption, 1),
            capacity_used_kwh=capacity_kwh,
            soc_percent=soc,
            assumptions_explanation=assumptions,
            disclaimer="Simulated physics estimation. No external live map or traffic API is connected."
        )

range_estimator = RangeEstimator()
