from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from auth import router as auth_router
from quizzes import router as quizzes_router
from contact import router as contact_router

app = FastAPI(title="Evaly API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production : remplacez par l'URL de votre frontend
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,    prefix="/api")
app.include_router(quizzes_router, prefix="/api")
app.include_router(contact_router, prefix="/api")

@app.get("/")
def root():
    return {"status": "Evaly API is running"}
