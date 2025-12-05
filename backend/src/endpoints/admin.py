from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import StreamingResponse
from pathlib import Path
import time
import secrets
import os
from config.settings import ADMIN_USERNAME, ADMIN_PASSWORD

router = APIRouter()
security = HTTPBasic()


LOG_FILE = Path("logs/app.log")

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

@router.get("/admin/logs")
def get_logs(lines: int = 100, auth: bool = Depends(authenticate)):
    """
    Return last `lines` lines from log file.
    """
    if not LOG_FILE.exists():
        return {"logs": []}
    with LOG_FILE.open() as f:
        content = f.readlines()
    return {"logs": content[-lines:]}

@router.get("/admin/logs/stream")
def stream_logs(auth: bool = Depends(authenticate)):
    def event_generator():
        with LOG_FILE.open() as f:
            f.seek(0, os.SEEK_END)
            while True:
                line = f.readline()
                if not line:
                    time.sleep(1)
                    continue
                yield f"data: {line}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")
