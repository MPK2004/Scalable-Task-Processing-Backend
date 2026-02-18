from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models, schemas, database
from ..dependencies import get_redis
from .. import mq
import redis.asyncio as redis
import json

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    db: AsyncSession = Depends(database.get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    # Create task in DB
    new_task = models.Task(status=models.TaskStatus.PENDING)
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    
    # Save to Redis
    task_data = schemas.TaskResponse.model_validate(new_task).model_dump()
    await redis_client.set(f"task:{new_task.id}", json.dumps(task_data))
    
    # Push to Queue
    await mq.publish_task(new_task.id)
    
    return new_task

@router.get("/{task_id}", response_model=schemas.TaskResponse)
async def read_task(
    task_id: int, 
    db: AsyncSession = Depends(database.get_db),
    redis_client: redis.Redis = Depends(get_redis)
):
    # Check Redis first
    cached_task = await redis_client.get(f"task:{task_id}")
    if cached_task:
        return json.loads(cached_task)
    
    result = await db.get(models.Task, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Cache it
    task_data = schemas.TaskResponse.model_validate(result).model_dump()
    await redis_client.set(f"task:{task_id}", json.dumps(task_data))
    
    return result
