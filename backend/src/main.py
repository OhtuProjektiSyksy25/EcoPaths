from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://0.0.0.0:8000"
]

app.mount("/static", StaticFiles(directory="build/static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/berlin")
async def berlin():
    """ returns Berlin coordinates as JSON
        response format: {"coordinates":[longitude, latitude]}
    """
    return {"coordinates": [13.404954, 52.520008]}

@app.get("/{full_path:path}")
async def spa_handler(full_path: str):
    index_path = os.path.join("build", "index.html")
    return FileResponse(index_path)