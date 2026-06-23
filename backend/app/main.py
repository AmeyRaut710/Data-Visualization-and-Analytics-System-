from fastapi import FastAPI
# Trigger backend reload for pyarrow
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(
    title="Data Analytics API",
    description="Agentic AI-Powered Intelligent Data Visualization and Analytics System API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, update in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api.routes import router as api_router

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Data Analytics API"}
