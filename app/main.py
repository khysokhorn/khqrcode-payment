from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api.khqr import router as khqr_router
from app.api.bakong import router as bakong_router
from app.core.db import create_db_and_tables
import os

app = FastAPI(
    title="Payment Microservice",
    description="Microservice for handling multiple payment gateways, starting with ABA PayWay.",
    version="1.0.0",
)

# Ensure static directory exists
if not os.path.exists("static/qr_codes"):
    os.makedirs("static/qr_codes")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# Configure CORS to allow integration with other backends/frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(khqr_router, prefix="/api/v1")
app.include_router(bakong_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Payment Microservice is running",
        "docs": "/docs",
        "supported_gateways": ["ABA PayWay"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8002, reload=True)
