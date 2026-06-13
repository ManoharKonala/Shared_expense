"""FastAPI application entry point.

Registers all routers, sets up CORS, and initializes audit logging.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, groups, expenses, balances, settlements, imports, audit
from app.utils.audit import setup_audit_listeners

app = FastAPI(
    title="Shared Expenses API",
    description="A production-quality shared expenses tracker for flatmates.",
    version="1.0.0",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(groups.router)
app.include_router(expenses.router)
app.include_router(balances.router)
app.include_router(settlements.router)
app.include_router(imports.router)
app.include_router(audit.router)

# Set up audit logging event listeners
setup_audit_listeners()


@app.get("/")
def root():
    """Health check endpoint."""
    return {
        "app": "Shared Expenses API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
def health():
    """Health check for deployment monitoring."""
    return {"status": "healthy"}
