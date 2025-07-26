from fastapi import FastAPI
from app.routes import router

app = FastAPI(title="Clinical Note Smart Summarizer")
app.include_router(router)
