from fastapi import FastAPI

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/berlin")
async def root():
    return {"coordinates":[52.520008, 13.404954]}