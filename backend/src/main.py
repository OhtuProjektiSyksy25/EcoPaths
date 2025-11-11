"""FastAPI main entrypoint. Exposes the app instance for uvicorn."""
from app import create_app, lifespan_context

app = create_app(lifespan_context)
