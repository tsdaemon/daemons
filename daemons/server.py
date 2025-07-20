
from fastapi import FastAPI
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from phoenix.otel import register

from daemons.web import argus

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Welcome to Daemons!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

app.include_router(argus.router)

register(project_name="daemons")
SmolagentsInstrumentor().instrument()