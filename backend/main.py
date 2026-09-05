"""AssessBridge FastAPI application entrypoint."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_routes import router as auth_router
from database import engine
from models import Base
from routers.conversion import router as conversion_router
from routers.activity import router as activity_router
from routers.titles import router as titles_router

app = FastAPI(title="AssessBridge", version="1.0.0")

# Create database tables
Base.metadata.create_all(bind=engine)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://[::1]:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

app.include_router(auth_router)
app.include_router(titles_router)
app.include_router(conversion_router)
app.include_router(activity_router)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
