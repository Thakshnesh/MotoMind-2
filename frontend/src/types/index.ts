export interface VehicleProfileSummary {
  vehicle_id: string;
  vehicle_type: 'two_wheeler' | 'four_wheeler';
  display_name: string;
  category_label: string;
  battery_voltage?: number;
  capacity_kwh?: number;
  cooling_type?: string;
  motor_configuration?: string;
  is_active?: boolean;
  battery?: {
    nominal_voltage: number;
    usable_capacity_kwh: number;
    max_discharge_current_a?: number;
    chemistry?: string;
  };
  motor?: {
    motor_count?: number;
    configuration?: string;
    cooling_type?: string;
    rated_power_kw?: number;
  };
  dynamics?: {
    curb_weight_kg?: number;
    nominal_consumption_wh_km?: number;
    top_speed_kmh?: number;
  };
  supported_sensors?: Record<string, string>;
}

export interface TelemetryData {
  timestamp: string;
  vehicle_id?: string;
  vehicle_type?: 'two_wheeler' | 'four_wheeler' | string;
  battery_voltage: number;
  battery_current: number;
  battery_temperature: number;
  state_of_charge: number;
  state_of_health?: number;
  motor_temperature: number;
  secondary_motor_temperature?: number | null;
  coolant_temperature?: number | null;
  cabin_temperature?: number | null;
  hvac_power_kw?: number | null;
  insulation_resistance_kohm?: number | null;
  vehicle_speed: number;
  energy_consumption: number;
  charging_status: string;
  ambient_temperature: number;
  moisture_status: string;
  sensor_fault_status: boolean;
  fault_codes: string[];
  power_kw: number;
  temp_delta: number;
  data_source_type: string;
  sensor_availability?: Record<string, string>;
  operating_context: string;
  service_mode_active: boolean;
}

export interface SimulatorStatus {
  is_running: boolean;
  active_vehicle_id?: string;
  active_vehicle_type?: 'two_wheeler' | 'four_wheeler' | string;
  current_profile: string;
  active_injected_fault?: string | null;
  tick_count: number;
  service_mode_active: boolean;
  latest_telemetry?: TelemetryData | null;
  available_vehicles?: VehicleProfileSummary[];
  data_source_indicator: string;
  disclaimer: string;
}

export interface HealthAssessment {
  id?: number;
  timestamp: string;
  vehicle_id?: string;
  vehicle_type?: string;
  overall_status: 'Normal' | 'Warning' | 'High Anomaly' | 'Insufficient Data';
  battery_health_score: number;
  motor_health_score: number;
  electrical_health_score: number;
  anomaly_detected: boolean;
  anomaly_score: number;
  reasons: string[];
  triggered_values: Record<string, any>;
  rule_violations: string[];
  disclaimer: string;
}

export interface RangeEstimate {
  estimated_range_km: number;
  confidence_interval_min_km: number;
  confidence_interval_max_km: number;
  usable_energy_remaining_wh: number;
  assumed_consumption_wh_km: number;
  capacity_used_kwh: number;
  soc_percent: number;
  assumptions_explanation: string[];
  disclaimer: string;
}

export interface ModelStatus {
  is_trained: boolean;
  vehicle_type?: string;
  vehicle_id?: string;
  training_sample_count: number;
  last_trained_at?: string | null;
  contaminated_samples_filtered: number;
  contamination_rate: number;
  features_used: string[];
  model_type: string;
  operational_state: string;
  disclaimer: string;
}

export interface AnomalyEvent {
  id: number;
  timestamp: string;
  vehicle_id?: string;
  vehicle_type?: string;
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  category: string;
  title: string;
  description: string;
  anomaly_score: number;
  features_involved: Record<string, any>;
  acknowledged: boolean;
  resolved: boolean;
}

export interface SoftwareVersion {
  id: number;
  version_string: string;
  version_type: 'REFERENCE' | 'CANDIDATE';
  target_vehicle_type?: string;
  release_notes?: string;
  created_at: string;
  bms_profile_config: Record<string, any>;
  is_active_reference: boolean;
}

export interface TestResultItem {
  id?: number;
  scenario_id: string;
  scenario_name: string;
  category: string;
  severity: 'CRITICAL' | 'MAJOR' | 'MINOR';
  status: 'PASS' | 'FAIL';
  expected_behavior: string;
  actual_behavior: string;
  reference_behavior?: string;
  is_regression: boolean;
  evidence_data: Record<string, any>;
  execution_time_ms: number;
}

export interface ValidationRun {
  id: string;
  timestamp: string;
  target_vehicle_type?: string;
  target_vehicle_id?: string;
  reference_version_id: number;
  candidate_version_id: number;
  reference_version_string?: string;
  candidate_version_string?: string;
  test_suite_version: string;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  blocked_tests: number;
  overall_result: 'PASS' | 'BLOCK';
  block_reason?: string | null;
  coverage_percentage: number;
  execution_duration_sec: number;
  regression_detected: boolean;
  results?: TestResultItem[];
  disclaimer: string;
}

export interface ComponentRecord {
  id: number;
  vehicle_id?: string;
  vehicle_type?: string;
  component_type: string;
  serial_number: string;
  installed_at: string;
  retired_at?: string | null;
  is_active: boolean;
  baseline_established_at?: string | null;
  nominal_specs: Record<string, any>;
  notes?: string;
}

export interface ServiceRecord {
  id: number;
  vehicle_id?: string;
  vehicle_type?: string;
  timestamp: string;
  service_type: string;
  description: string;
  technician_notes?: string;
  odometer_km: number;
  pre_service_health_score?: number;
  post_service_health_score?: number;
  component_replaced_id?: number;
  is_service_mode_session: boolean;
}

export interface WaterExposureRecord {
  id: number;
  vehicle_id?: string;
  vehicle_type?: string;
  timestamp: string;
  exposure_type: string;
  severity_level: string;
  duration_minutes: number;
  moisture_sensor_reading: string;
  post_exposure_inspected: boolean;
  notes?: string;
  disclaimer: string;
}
