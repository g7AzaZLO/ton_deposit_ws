import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.logic import close_mongo_connection, initialize_db
from settings.api_description import description
from db.api import db_router
from ws.deposit import ws_deposit_router

logging.basicConfig(level=logging.INFO)


async def lifespan(app: FastAPI):
    await initialize_db()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="[G7]App",
    description=description,
    version="1.0.0",
    lifespan=lifespan,
)
app.include_router(ws_deposit_router)
app.include_router(db_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
