from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.system import router as system_router
from app.services.mqtt_subscriber import start_mqtt_subscriber

@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Application starting up...")
    print("Starting Database engine")
    print("Initializing firebase")
    # Startup
    mqtt_task = asyncio.create_task(start_mqtt_subscriber())
    yield
    # Shutdown
    print("Application shutting down...")
    mqtt_task.cancel()
    try:
        await mqtt_task
    except asyncio.CancelledError:
        print("Application shut down")
    # await engine.dispose() # Uncomment this once the engine is defined in database.py


def create_app() ->FastAPI:
    app = FastAPI(title="Lookout Grid", lifespan=lifespan)

    # add cors

    app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

    # include routers
    app.include_router(system_router, prefix="/v1", tags=["System"])
    
    return app


app = create_app()



