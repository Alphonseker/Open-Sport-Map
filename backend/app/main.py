from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.routers import facilities

app = FastAPI(
    title="Open Sport Map API",
    description="Geospatial REST API for querying public outdoor sports facilities.",
    version="1.0.0"
)

# Enable CORS for local web development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Open for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(facilities.router)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "Open Sport Map API"}