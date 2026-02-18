from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas, mq
import redis.asyncio as redis
import json
from fastapi import HTTPException

class TaskService:
    @staticmethod
    async def create_task(db: AsyncSession, redis_client: redis.Redis, task_create: schemas.TaskCreate) -> models.Task:
        # 1. Create task in DB
        new_task = models.Task(status=models.TaskStatus.PENDING, input_data=task_create.input_data)
        db.add(new_task)
        await db.commit()
        await db.refresh(new_task)
        
        # 2. Save to Redis (Write-through)
        task_data = schemas.TaskResponse.model_validate(new_task).model_dump()
        await redis_client.set(f"task:{new_task.id}", json.dumps(task_data))
        
        # 3. Push to Queue
        await mq.publish_task(new_task.id, task_create.input_data)
        
        return new_task

    @staticmethod
    async def get_task(task_id: int, db: AsyncSession, redis_client: redis.Redis) -> schemas.TaskResponse:
        # 1. Check Redis first
        cached_task = await redis_client.get(f"task:{task_id}")
        if cached_task:
            # Return Pydantic model from dict, ensuring type consistency
            return schemas.TaskResponse.model_validate_json(cached_task)
        
        # 2. Fetch from DB
        result = await db.get(models.Task, task_id)
        if not result:
            raise HTTPException(status_code=404, detail="Task not found")
            
        # 3. Cache it (Read-through)
        task_data = schemas.TaskResponse.model_validate(result).model_dump()
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=60) # TTL 60s
        
        return schemas.TaskResponse.model_validate(result)
