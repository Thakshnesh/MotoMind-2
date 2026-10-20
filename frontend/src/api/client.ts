import {
  TelemetryData, SimulatorStatus, HealthAssessment, RangeEstimate,
  ModelStatus, AnomalyEvent, SoftwareVersion, ValidationRun,
  ComponentRecord, ServiceRecord, WaterExposureRecord, VehicleProfileSummary
} from '../types';

const BASE_URL = '/api';

export const api = {
  // Simulator & Vehicles
  async listVehicles(): Promise<VehicleProfileSummary[]> {
    const res = await fetch(`${BASE_URL}/simulator/vehicles`);
    return res.json();
  },
  async switchVehicle(vehicleId: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/simulator/switch-vehicle`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ vehicle_id: vehicleId })
    });
    return res.json();
  },
  async getSimulatorStatus(vehicleId?: string): Promise<SimulatorStatus> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/simulator/status${query}`);
    return res.json();
  },
  async startSimulation(vehicleId?: string): Promise<void> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    await fetch(`${BASE_URL}/simulator/start${query}`, { method: 'POST' });
  },
  async pauseSimulation(vehicleId?: string): Promise<void> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    await fetch(`${BASE_URL}/simulator/pause${query}`, { method: 'POST' });
  },
  async resetSimulation(vehicleId?: string): Promise<void> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    await fetch(`${BASE_URL}/simulator/reset${query}`, { method: 'POST' });
  },
  async injectFault(faultType: string, durationSeconds: number = 30, vehicleId?: string): Promise<void> {
    await fetch(`${BASE_URL}/simulator/inject-fault`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        fault_type: faultType,
        duration_seconds: durationSeconds,
        vehicle_id: vehicleId
      })
    });
  },
  async clearFault(vehicleId?: string): Promise<void> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    await fetch(`${BASE_URL}/simulator/clear-fault${query}`, { method: 'POST' });
  },
  async setProfile(profileName: string, vehicleId?: string): Promise<void> {
    await fetch(`${BASE_URL}/simulator/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ profile_name: profileName, vehicle_id: vehicleId })
    });
  },

  // Telemetry
  async getCurrentTelemetry(vehicleId?: string): Promise<TelemetryData> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/telemetry/current${query}`);
    return res.json();
  },
  async getTelemetryHistory(limit: number = 60, vehicleId?: string): Promise<TelemetryData[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (vehicleId) params.append('vehicle_id', vehicleId);
    const res = await fetch(`${BASE_URL}/telemetry/history?${params.toString()}`);
    return res.json();
  },
  async getTelemetrySummary(vehicleId?: string): Promise<any> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/telemetry/summary${query}`);
    return res.json();
  },

  // Health & Range
  async getHealthStatus(vehicleId?: string): Promise<HealthAssessment> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/health/status${query}`);
    return res.json();
  },
  async estimateRange(params: {
    vehicle_id?: string;
    battery_soc?: number;
    battery_capacity_kwh?: number;
    average_consumption_wh_km?: number;
    elevation_gain_m?: number;
    traffic_factor?: number;
  }): Promise<RangeEstimate> {
    const res = await fetch(`${BASE_URL}/health/estimate-range`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params)
    });
    return res.json();
  },

  // AI & Anomaly
  async getModelStatus(vehicleType: string = 'two_wheeler', vehicleId?: string): Promise<ModelStatus> {
    const params = new URLSearchParams({ vehicle_type: vehicleType });
    if (vehicleId) params.append('vehicle_id', vehicleId);
    const res = await fetch(`${BASE_URL}/anomaly/model-status?${params.toString()}`);
    return res.json();
  },
  async trainModel(vehicleType: string = 'two_wheeler', sampleCount: number = 600, contamination: number = 0.03): Promise<any> {
    const res = await fetch(`${BASE_URL}/anomaly/train`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vehicle_type: vehicleType,
        sample_count: sampleCount,
        contamination,
        exclude_known_faults: true
      })
    });
    return res.json();
  },
  async getAnomalyEvents(vehicleId?: string): Promise<AnomalyEvent[]> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/anomaly/events${query}`);
    return res.json();
  },
  async acknowledgeEvent(id: number): Promise<void> {
    await fetch(`${BASE_URL}/anomaly/events/${id}/acknowledge`, { method: 'POST' });
  },

  // Service & Components
  async getServiceRecords(vehicleId?: string): Promise<ServiceRecord[]> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/service/records${query}`);
    return res.json();
  },
  async addServiceRecord(record: {
    vehicle_id?: string;
    service_type: string;
    description: string;
    technician_notes?: string;
    odometer_km?: number;
  }): Promise<ServiceRecord> {
    const res = await fetch(`${BASE_URL}/service/records`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record)
    });
    return res.json();
  },
  async getWaterExposureRecords(vehicleId?: string): Promise<WaterExposureRecord[]> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/service/water-exposure${query}`);
    return res.json();
  },
  async addWaterExposure(record: {
    vehicle_id?: string;
    exposure_type: string;
    severity_level: string;
    duration_minutes: number;
    moisture_sensor_reading: string;
    notes?: string;
  }): Promise<WaterExposureRecord> {
    const res = await fetch(`${BASE_URL}/service/water-exposure`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(record)
    });
    return res.json();
  },
  async getComponents(vehicleId?: string): Promise<ComponentRecord[]> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/service/components${query}`);
    return res.json();
  },
  async addComponent(component: {
    vehicle_id?: string;
    component_type: string;
    serial_number: string;
    nominal_specs: any;
    notes?: string;
    reset_baseline: boolean;
  }): Promise<ComponentRecord> {
    const res = await fetch(`${BASE_URL}/service/components`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(component)
    });
    return res.json();
  },
  async resetComponentBaseline(id: number): Promise<void> {
    await fetch(`${BASE_URL}/service/components/${id}/reset-baseline`, { method: 'POST' });
  },
  async toggleServiceMode(active: boolean, vehicleId?: string): Promise<any> {
    const res = await fetch(`${BASE_URL}/service/service-mode`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ active, vehicle_id: vehicleId })
    });
    return res.json();
  },
  async getBeforeAfterComparison(vehicleId?: string): Promise<any> {
    const query = vehicleId ? `?vehicle_id=${encodeURIComponent(vehicleId)}` : '';
    const res = await fetch(`${BASE_URL}/service/before-after-comparison${query}`);
    return res.json();
  },

  // OTA Validation
  async getSoftwareVersions(targetVehicleType?: string): Promise<SoftwareVersion[]> {
    const query = targetVehicleType ? `?target_vehicle_type=${encodeURIComponent(targetVehicleType)}` : '';
    const res = await fetch(`${BASE_URL}/ota/versions${query}`);
    return res.json();
  },
  async getTestScenarios(targetVehicleType?: string): Promise<any[]> {
    const query = targetVehicleType ? `?target_vehicle_type=${encodeURIComponent(targetVehicleType)}` : '';
    const res = await fetch(`${BASE_URL}/ota/scenarios${query}`);
    return res.json();
  },
  async getValidationRuns(targetVehicleType?: string): Promise<ValidationRun[]> {
    const query = targetVehicleType ? `?target_vehicle_type=${encodeURIComponent(targetVehicleType)}` : '';
    const res = await fetch(`${BASE_URL}/ota/runs${query}`);
    return res.json();
  },
  async getValidationRun(id: string): Promise<ValidationRun> {
    const res = await fetch(`${BASE_URL}/ota/runs/${id}`);
    return res.json();
  },
  async startValidationRun(refId: number, candId: number, targetVehicleType?: string, targetVehicleId?: string): Promise<ValidationRun> {
    const res = await fetch(`${BASE_URL}/ota/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        reference_version_id: refId,
        candidate_version_id: candId,
        target_vehicle_type: targetVehicleType,
        target_vehicle_id: targetVehicleId
      })
    });
    return res.json();
  },
  async runDemoRegression(vehicleType?: string): Promise<ValidationRun> {
    const query = vehicleType ? `?vehicle_type=${encodeURIComponent(vehicleType)}` : '';
    const res = await fetch(`${BASE_URL}/ota/run-demo-regression${query}`, { method: 'POST' });
    return res.json();
  },
  async runDemoPassing(vehicleType?: string): Promise<ValidationRun> {
    const query = vehicleType ? `?vehicle_type=${encodeURIComponent(vehicleType)}` : '';
    const res = await fetch(`${BASE_URL}/ota/run-demo-passing${query}`, { method: 'POST' });
    return res.json();
  }
};
