from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from .. import schemas, database, services
from ..dependencies import get_redis
import redis.asyncio as redis

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: schemas.TaskCreate,
    db: AsyncSession = Depends(database.get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    return await services.TaskService.create_task(db, redis_client, task_create)

@router.get("/{task_id}", response_model=schemas.TaskResponse)
async def read_task(
    task_id: int, 
    db: AsyncSession = Depends(database.get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    # Service now returns a Pydantic model compatible with response_model
    return await services.TaskService.get_task(task_id, db, redis_client)
