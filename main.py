from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware 
from fastapi.staticfiles import StaticFiles
from auth import router as auth_router
from quizzes import router as quizzes_router
from contact import router as contact_router

app = FastAPI(title="Evaly API", version="1.0.0") #start server w title w version

#defining chkon rah allowed yaccessi lapi w chkon ma yaccessich, hna rah 3tina access lkolchi, w ila habina nrestrictiw access ldomain wahed ola chi domains n9dro ndirouha hna f allow_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,    prefix="/api")
app.include_router(quizzes_router, prefix="/api")
app.include_router(contact_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "Evaly API is running"}

app.mount("/", StaticFiles(directory=".", html=True), name="static")