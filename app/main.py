from fastapi import FastAPI
from .routers import tasks
from .database import engine, Base
import contextlib

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry DB connection
    for i in range(5):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            break
        except Exception as e:
            if i == 4:
                raise e
            import asyncio
            print(f"DB connection failed, retrying in 2s... ({e})")
            await asyncio.sleep(2)
    yield

app = FastAPI(lifespan=lifespan, title="Async Task Backend")

app.include_router(tasks.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Async Task Backend"}
