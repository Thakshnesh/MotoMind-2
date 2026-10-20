import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
from ..simulator.vehicle_simulator import vehicle_simulator
from ..services.health_engine import health_engine

router = APIRouter(tags=["WebSocket"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                self.disconnect(connection)

manager = ConnectionManager()

@router.websocket("/ws/telemetry")
async def websocket_telemetry_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            v_state = vehicle_simulator.get_active_state()
            curr = v_state.latest_telemetry
            if not curr:
                curr = vehicle_simulator.step()

            assessment = health_engine.last_assessments.get(v_state.vehicle_id) or health_engine.assess_telemetry(curr.model_dump())

            payload = {
                "active_vehicle_id": v_state.vehicle_id,
                "active_vehicle_type": v_state.vehicle_type,
                "telemetry": curr.model_dump(),
                "simulator": vehicle_simulator.get_status(v_state.vehicle_id),
                "health": assessment
            }
            await websocket.send_text(json.dumps(payload, default=str))
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
