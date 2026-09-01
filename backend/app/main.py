from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers.system import router as system_router


@asynccontextmanager
async def lifespan(app:FastAPI):
    print("Application starting up...")
    print("Starting Database engine")
    print("Initializing firebase")
    # Startup
    yield
    # Shutdown
    print("Application shutting down...")
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



