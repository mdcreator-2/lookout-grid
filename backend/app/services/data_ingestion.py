"""
Data Ingestion Service
======================
Core pipeline that converts raw MQTT JSON payloads into validated
database records.  Each handler follows the same pattern:

    Parse → Validate (Pydantic) → Transform (SQLAlchemy) → Store → Side-effects

This module is called from the MQTT subscriber background task, so it
manages its own async DB sessions rather than relying on FastAPI's
dependency injection.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Union

from pydantic import ValidationError
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.database import async_session_factory
from app.models import SensorReading, Node, Gateway, Alert
from app.schemas.sensor_reading import SensorReadingCreate, SensorReadingBatch
from app.schemas.alert import AlertCreate

logger = logging.getLogger("data_ingestion")


# ──────────────────────────────────────────────
#  Helper: WebSocket broadcast (stub)
# ──────────────────────────────────────────────

async def _broadcast_ws(channel: str, data: Dict[str, Any]) -> None:
    """Push data to connected WebSocket clients.

    This is a placeholder that will be wired up in task 3C.14.
    Keeping it as a no-op allows the rest of the pipeline to be
    exercised end-to-end without a WebSocket manager in place.
    """
    # TODO (3C.14): Import the WebSocket manager and call
    #   await ws_manager.broadcast(channel, data)
    logger.debug("WS broadcast [%s]: %s", channel, data)


# ──────────────────────────────────────────────
#  Helper: Alert engine trigger (stub)
# ──────────────────────────────────────────────

async def _trigger_alert_engine(alert_record: Alert) -> None:
    """Determine recipients and fire notifications.

    This is a placeholder that will be implemented in task 3C.15.
    """
    # TODO (3C.15): Import the alert engine and call
    #   await alert_engine.process(alert_record)
    logger.debug("Alert engine triggered for %s", alert_record.alert_id)


# ══════════════════════════════════════════════
#  1. handle_sensor_data
# ══════════════════════════════════════════════

async def handle_sensor_data(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
    """Ingest one or more sensor reading packets from the ``data`` topic.

    The ``data`` topic can deliver either:
    * A single ``SensorReadingCreate`` dict
    * A batch wrapper ``{"readings": [...]}``, matching ``SensorReadingBatch``

    Invalid packets are logged and silently discarded so that one bad
    reading never blocks the rest of a batch.
    """
    # ── 1. Normalise to a list of raw dicts ──────────────────────
    raw_items: List[Dict[str, Any]] = _normalise_to_list(payload)
    if not raw_items:
        logger.warning("Received empty sensor data payload — skipping")
        return

    # ── 2. Validate & transform ──────────────────────────────────
    db_objects: List[SensorReading] = []
    node_ids_seen: set[str] = set()

    for raw in raw_items:
        reading_obj = _validate_and_transform_reading(raw)
        if reading_obj is not None:
            db_objects.append(reading_obj)
            node_ids_seen.add(reading_obj.node_id)

    if not db_objects:
        logger.warning("All readings in the batch failed validation — nothing to store")
        return

    # ── 3. Store + side-effects inside a single session ──────────
    async with async_session_factory() as session:
        async with session.begin():
            session.add_all(db_objects)

            # Update last_seen_at for every node that reported in
            now = datetime.now(timezone.utc)
            if node_ids_seen:
                await session.execute(
                    update(Node)
                    .where(Node.node_id.in_(node_ids_seen))
                    .values(last_seen_at=now)
                )

    logger.info(
        "Stored %d sensor reading(s) for node(s): %s",
        len(db_objects),
        ", ".join(sorted(node_ids_seen)),
    )

    # ── 4. Broadcast to WebSocket ────────────────────────────────
    for obj in db_objects:
        await _broadcast_ws("sensors:data", _reading_to_ws_payload(obj))


# ══════════════════════════════════════════════
#  2. handle_anomaly
# ══════════════════════════════════════════════

async def handle_anomaly(payload: Dict[str, Any]) -> None:
    """Ingest an anomaly-flagged sensor reading.

    Same pipeline as ``handle_sensor_data`` but additionally:
    * Logs at WARNING level
    * Broadcasts on the dedicated ``sensors:anomaly`` WS channel
    """
    reading_obj = _validate_and_transform_reading(payload)
    if reading_obj is None:
        return

    logger.warning(
        "⚠ Anomaly detected on node %s — score: %s, label: %s",
        reading_obj.node_id,
        reading_obj.anomaly_score,
        reading_obj.edge_label,
    )

    async with async_session_factory() as session:
        async with session.begin():
            session.add(reading_obj)

            await session.execute(
                update(Node)
                .where(Node.node_id == reading_obj.node_id)
                .values(last_seen_at=datetime.now(timezone.utc))
            )

    # Broadcast to both channels so dashboards show the reading AND
    # the anomaly panel highlights it immediately.
    ws_data = _reading_to_ws_payload(reading_obj)
    await _broadcast_ws("sensors:data", ws_data)
    await _broadcast_ws("sensors:anomaly", ws_data)


# ══════════════════════════════════════════════
#  3. handle_new_alert
# ══════════════════════════════════════════════

async def handle_new_alert(payload: Dict[str, Any]) -> None:
    """Ingest a new alert packet from the ``alerts/+/new`` topic.

    The raw MQTT alert payload (documented in ``docs/data_schema.md``
    §1.2) has a nested structure.  We flatten it into the ``AlertCreate``
    schema and then into the ``Alert`` DB model.
    """
    try:
        # Flatten the nested MQTT payload into the shape AlertCreate expects
        flat = _flatten_alert_payload(payload)
        alert_schema = AlertCreate(**flat)
    except (ValidationError, KeyError, TypeError) as exc:
        logger.error("Invalid alert payload — discarding: %s", exc)
        return

    alert_record = Alert(
        alert_id=alert_schema.alert_id,
        timestamp=alert_schema.timestamp,
        source=alert_schema.source,
        gateway_id=alert_schema.gateway_id,
        primary_node_id=alert_schema.primary_node_id,
        alert_level=alert_schema.alert_level,
        alert_type=alert_schema.alert_type,
        alert_subtype=alert_schema.alert_subtype,
        confidence=alert_schema.confidence,
        description=alert_schema.description,
        affected_lat=alert_schema.affected_lat,
        affected_lng=alert_schema.affected_lng,
        affected_radius_km=alert_schema.affected_radius_km,
        affected_area_name=alert_schema.affected_area_name,
        model_name=alert_schema.model_name,
        model_layer=alert_schema.model_layer,
        prediction_data=alert_schema.prediction_data,
    )

    async with async_session_factory() as session:
        async with session.begin():
            session.add(alert_record)

    logger.warning(
        "🚨 New %s alert [%s] — %s (confidence: %.2f)",
        alert_record.alert_level,
        alert_record.alert_id,
        alert_record.alert_type,
        alert_record.confidence,
    )

    # Trigger the alert engine (notifications, escalation)
    await _trigger_alert_engine(alert_record)

    # Broadcast to alerts WS channel
    await _broadcast_ws("alerts:new", {
        "alert_id": alert_record.alert_id,
        "timestamp": alert_record.timestamp.isoformat(),
        "alert_level": alert_record.alert_level,
        "alert_type": alert_record.alert_type,
        "alert_subtype": alert_record.alert_subtype,
        "description": alert_record.description,
        "confidence": alert_record.confidence,
        "gateway_id": alert_record.gateway_id,
        "primary_node_id": alert_record.primary_node_id,
        "affected_area_name": alert_record.affected_area_name,
    })


# ══════════════════════════════════════════════
#  4. handle_heartbeat
# ══════════════════════════════════════════════

async def handle_heartbeat(payload: Dict[str, Any]) -> None:
    """Process a gateway heartbeat and update the ``gateways`` table.

    Heartbeat schema (§1.4 in ``docs/data_schema.md``):
    * ``gateway_id``, ``timestamp``
    * ``connected_nodes``, ``active_nodes``, ``inactive_nodes``
    * ``connectivity``, ``signal_strength_dbm``
    * ``cpu_usage_pct``, ``ram_usage_pct``, ``disk_usage_pct``
    * ``active_alerts``, ``last_model_update``

    We persist the fields that match ``Gateway`` columns and mark any
    reported ``inactive_nodes`` as ``INACTIVE``.
    """
    gateway_id = payload.get("gateway_id")
    if not gateway_id:
        logger.error("Heartbeat payload missing gateway_id — discarding")
        return

    now = datetime.now(timezone.utc)
    total_nodes = payload.get("connected_nodes") or payload.get("active_nodes")
    inactive_node_ids: List[str] = payload.get("inactive_nodes", [])

    async with async_session_factory() as session:
        async with session.begin():
            # Upsert-style update: only touch columns that the Gateway
            # model actually has.  Extra heartbeat fields (cpu, ram, disk)
            # are logged but not stored — extend the model if needed later.
            gateway_update_values: Dict[str, Any] = {
                "last_heartbeat": now,
                "status": "ACTIVE",
            }
            if total_nodes is not None:
                gateway_update_values["total_nodes"] = total_nodes

            await session.execute(
                update(Gateway)
                .where(Gateway.gateway_id == gateway_id)
                .values(**gateway_update_values)
            )

            # Mark inactive nodes
            if inactive_node_ids:
                await session.execute(
                    update(Node)
                    .where(Node.node_id.in_(inactive_node_ids))
                    .values(status="INACTIVE")
                )
                logger.warning(
                    "Nodes marked INACTIVE by gateway %s: %s",
                    gateway_id,
                    ", ".join(inactive_node_ids),
                )

    logger.info(
        "Heartbeat processed for gateway %s — %s nodes connected, %d inactive",
        gateway_id,
        total_nodes or "?",
        len(inactive_node_ids),
    )

    # Log extra telemetry for observability (not stored in DB yet)
    if any(k in payload for k in ("cpu_usage_pct", "ram_usage_pct", "disk_usage_pct")):
        logger.debug(
            "Gateway %s telemetry — CPU: %s%%, RAM: %s%%, Disk: %s%%",
            gateway_id,
            payload.get("cpu_usage_pct"),
            payload.get("ram_usage_pct"),
            payload.get("disk_usage_pct"),
        )


# ══════════════════════════════════════════════
#  Private helpers
# ══════════════════════════════════════════════

def _normalise_to_list(payload: Union[Dict[str, Any], List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """Accept either a single reading dict, a batch wrapper, or a raw list."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        # Batch wrapper: {"readings": [...]}
        if "readings" in payload and isinstance(payload["readings"], list):
            return payload["readings"]
        # Single reading
        return [payload]
    return []


def _validate_and_transform_reading(raw: Dict[str, Any]) -> SensorReading | None:
    """Validate a raw dict through Pydantic, then map to the DB model.

    Returns ``None`` (and logs) if validation fails.
    """
    try:
        schema = SensorReadingCreate(**raw)
    except ValidationError as exc:
        logger.error(
            "Sensor reading validation failed for node '%s' — discarding: %s",
            raw.get("node_id", "UNKNOWN"),
            exc,
        )
        return None

    # ── Map flat reading fields ──────────────────────────────────
    readings = schema.readings
    health = schema.device_health
    edge = schema.edge_inference

    return SensorReading(
        time=schema.timestamp,
        node_id=schema.node_id,
        gateway_id=schema.gateway_id,
        # Sensor readings
        water_level_m=readings.water_level_m,
        rainfall_mm_hr=readings.rainfall_mm_hr,
        temperature_c=readings.temperature_c,
        humidity_pct=readings.humidity_pct,
        pressure_hpa=readings.pressure_hpa,
        pm25_ugm3=readings.pm25_ugm3,
        pm10_ugm3=readings.pm10_ugm3,
        smoke_ppm=readings.smoke_ppm,
        soil_moisture_pct=readings.soil_moisture_pct,
        tds_ppm=readings.tds_ppm,
        wind_speed_kmh=readings.wind_speed_kmh,
        uv_index=readings.uv_index,
        co_ugm3=readings.co_ugm3,
        # Device health
        battery_pct=health.battery_pct,
        solar_charging=health.solar_charging,
        signal_strength_dbm=health.signal_strength_dbm,
        uptime_seconds=health.uptime_seconds,
        firmware_version=health.firmware_version,
        # Edge inference (optional block)
        model_version=edge.model_version if edge else None,
        anomaly_detected=edge.anomaly_detected if edge else False,
        anomaly_score=edge.anomaly_score if edge else None,
        inference_time_ms=edge.inference_time_ms if edge else None,
        edge_label=edge.label if edge else None,
    )


def _reading_to_ws_payload(obj: SensorReading) -> Dict[str, Any]:
    """Serialise a ``SensorReading`` ORM object into a dict suitable
    for WebSocket broadcast."""
    return {
        "time": obj.time.isoformat() if obj.time else None,
        "node_id": obj.node_id,
        "gateway_id": obj.gateway_id,
        "water_level_m": obj.water_level_m,
        "rainfall_mm_hr": obj.rainfall_mm_hr,
        "temperature_c": obj.temperature_c,
        "humidity_pct": obj.humidity_pct,
        "pressure_hpa": obj.pressure_hpa,
        "pm25_ugm3": obj.pm25_ugm3,
        "pm10_ugm3": obj.pm10_ugm3,
        "smoke_ppm": obj.smoke_ppm,
        "soil_moisture_pct": obj.soil_moisture_pct,
        "tds_ppm": obj.tds_ppm,
        "wind_speed_kmh": obj.wind_speed_kmh,
        "uv_index": obj.uv_index,
        "co_ugm3": obj.co_ugm3,
        "battery_pct": obj.battery_pct,
        "signal_strength_dbm": obj.signal_strength_dbm,
        "anomaly_detected": obj.anomaly_detected,
        "anomaly_score": obj.anomaly_score,
        "edge_label": obj.edge_label,
    }


def _flatten_alert_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten the nested MQTT alert packet (§1.2) into the shape
    that ``AlertCreate`` expects.

    The MQTT packet nests data under ``hazard``, ``trigger_data``, and
    ``model_prediction`` keys.  ``AlertCreate`` uses flat field names.
    """
    hazard = raw.get("hazard", {})
    trigger = raw.get("trigger_data", {})
    model = raw.get("model_prediction", {})
    affected = hazard.get("affected_area", {})

    return {
        "alert_id": raw.get("alert_id"),
        "timestamp": raw.get("timestamp"),
        "source": raw.get("source"),
        "gateway_id": raw.get("gateway_id"),
        "primary_node_id": trigger.get("primary_node") or raw.get("primary_node_id"),
        "alert_level": raw.get("alert_level"),
        "alert_type": raw.get("alert_type") or hazard.get("type"),
        "alert_subtype": hazard.get("subtype"),
        "confidence": raw.get("confidence_score") or raw.get("confidence"),
        "description": hazard.get("description"),
        "affected_lat": affected.get("center_lat"),
        "affected_lng": affected.get("center_lng"),
        "affected_radius_km": affected.get("radius_km"),
        "affected_area_name": affected.get("area_name"),
        "model_name": model.get("model_name"),
        "model_layer": model.get("model_layer"),
        "prediction_data": model if model else None,
    }
