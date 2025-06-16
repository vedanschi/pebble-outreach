from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Import scheduler functions
from src.core.scheduler import start_scheduler, shutdown_scheduler

# Import routers
from src.auth import routes as auth_routes
from src.campaigns import routes as campaign_routes
from src.followups import routes as followup_routes
from src.llm import routes as llm_routes
from src.users import routes as user_routes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("MainApp (lifespan): Application startup...")
    print("MainApp (lifespan): Starting scheduler...")
    start_scheduler()
    print("MainApp (lifespan): Scheduler should be running if configured.")
    yield
    # Shutdown logic
    print("MainApp (lifespan): Application shutdown...")
    print("MainApp (lifespan): Shutting down scheduler...")
    shutdown_scheduler()
    print("MainApp (lifespan): Scheduler shut down.")

# Create FastAPI app instance
app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include your API routers
app.include_router(auth_routes.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(campaign_routes.router, prefix="/api/v1/campaigns", tags=["Campaigns"])
app.include_router(followup_routes.router, prefix="/api/v1/followups", tags=["Follow-ups"])
app.include_router(llm_routes.router, prefix="/api/v1/llm", tags=["LLM"])
app.include_router(user_routes.router, prefix="/api/v1/users", tags=["Users"])

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Sales Automation Platform API"}

# To run this (example using uvicorn):
# uvicorn main:app --reload
# (assuming this file is named main.py in the directory where you run uvicorn)
```
