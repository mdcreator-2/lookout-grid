import asyncio
import json
import logging
import aiomqtt

from app.services.data_ingestion import (
    handle_sensor_data,
    handle_anomaly,
    handle_new_alert,
    handle_heartbeat,
)

# Configure a basic logger for the service
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mqtt_subscriber")

# ==========================================
# Handlers that are NOT yet in data_ingestion
# ==========================================

async def handle_gateway_status(payload):
    logger.info(f"Handling gateway status: {payload}")
    # TODO: Add logic


# ==========================================
# Main MQTT Subscriber loop
# ==========================================

async def start_mqtt_subscriber():
    """
    Connects to the MQTT broker, subscribes to required topics,
    and routes incoming messages to the correct handlers.
    """
    broker_url = "localhost" # Adjust this if your broker is hosted elsewhere
    
    # aiomqtt handles the reconnection loop gracefully inside the context manager
    try:
        async with aiomqtt.Client(broker_url) as client:
            # Subscribe to the required patterns
            # The '+' wildcard matches exactly one level (e.g., any gateway ID)
            await client.subscribe("lookoutgrid/sensors/+/data")
            await client.subscribe("lookoutgrid/sensors/+/anomaly")
            await client.subscribe("lookoutgrid/alerts/+/new")
            await client.subscribe("lookoutgrid/gateways/+/heartbeat")
            await client.subscribe("lookoutgrid/gateways/+/status")
            
            logger.info(f"Connected to MQTT broker at {broker_url} and subscribed to topics.")
            
            # This async loop runs indefinitely, processing messages as they arrive
            async for message in client.messages:
                # It's good practice to wrap processing in a try/except so 
                # a single bad message doesn't crash the entire background task
                try:
                    # MQTT payloads are bytes, so we decode them to strings and parse the JSON
                    payload = json.loads(message.payload.decode())
                    
                    # The message.topic object has a handy .matches() method 
                    # that understands MQTT wildcards like '+' and '#'
                    if message.topic.matches("lookoutgrid/sensors/+/data"):
                        await handle_sensor_data(payload)
                    
                    elif message.topic.matches("lookoutgrid/sensors/+/anomaly"):
                        await handle_anomaly(payload)
                    
                    elif message.topic.matches("lookoutgrid/alerts/+/new"):
                        await handle_new_alert(payload)
                    
                    elif message.topic.matches("lookoutgrid/gateways/+/heartbeat"):
                        await handle_heartbeat(payload)
                    
                    elif message.topic.matches("lookoutgrid/gateways/+/status"):
                        await handle_gateway_status(payload)
                        
                    else:
                        logger.warning(f"Received message on unhandled topic: {message.topic}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON payload on topic {message.topic}: {e}")
                    logger.error(f"Raw payload received was: {message.payload.decode()}")
                except Exception as e:
                    logger.error(f"Error processing message on topic {message.topic}: {e}")

    except aiomqtt.MqttError as error:
        logger.error(f"MQTT connection error: {error}")

# Note: to actually run this in FastAPI, you typically hook it into the app lifecycle events 
# (e.g., using @app.on_event("startup") or the lifespan context manager)
