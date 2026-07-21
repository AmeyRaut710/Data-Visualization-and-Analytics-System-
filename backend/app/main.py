from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
# Trigger backend reload for pyarrow
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="Data Analytics API",
    description="Agentic AI-Powered Intelligent Data Visualization and Analytics System API",
    version="1.0.0",
    default_response_class=ORJSONResponse
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, update in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

from app.api.routes import router as api_router
from app.api.dashboard import router as dashboard_router

app.include_router(api_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api/dashboard")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Data Analytics API"}
