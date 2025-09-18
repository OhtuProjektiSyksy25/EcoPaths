""" FastAPI application """
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
origins = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """ returns hello world JSON
    response format: {"message: "Hello World}
    """
    return {"message": "Hello World"}

@app.get("/berlin")
async def berlin():
    """ returns Berlin coordinates as JSON
        response format: {"coordinates":[latitude, longitude]}
    """
    return {"coordinates":[52.520008, 13.404954]}
