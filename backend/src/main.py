from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()
origins = ["http://localhost:3000"]

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
    print("Berlin endpoint called")
    return {"coordinates":[52.520008, 13.404954]}

@app.get("/{full_path:path}")
async def spa_handler(full_path: str):
    index_path = os.path.join("build", "index.html")
    return FileResponse(index_path)