"""Main FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import settings
from .routers import worktrees

app = FastAPI(
    title="Worktree Flow API",
    description="Advanced Git worktree workflow management API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(worktrees.router, prefix="/worktrees", tags=["Worktrees"])


@app.get("/")
async def root():
    """API root endpoint."""
    return {
        "name": "Worktree Flow API",
        "version": "0.1.0",
        "docs": "/docs",
        "github": "https://github.com/pv-udpv/worktree-flow",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


def serve(host: str = None, port: int = None, reload: bool = None):
    """Start the API server."""
    import uvicorn

    uvicorn.run(
        "worktree_flow.api.app:app",
        host=host or settings.api_host,
        port=port or settings.api_port,
        reload=reload if reload is not None else settings.api_reload,
    )
