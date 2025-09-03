import uvicorn
from fastapi import FastAPI, BackgroundTasks
from agents.call import call_handler, list_handler

app = FastAPI(title="Hireloom", description="", version="1.0.0")


@app.get("/")
async def root():
    return {"message": "Server OK"}


@app.post("/make_call")
async def make_call(background_tasks: BackgroundTasks):
    return await call_handler(background_tasks)


@app.get("/get_recordings")
async def get_recordings():
    return list_handler()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
