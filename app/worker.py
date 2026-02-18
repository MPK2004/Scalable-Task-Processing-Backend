import asyncio
import aio_pika
import json
import os
import sys
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import redis.asyncio as redis

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import models, database, mq, schemas

QUEUE_NAME = "task_queue"
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6381))

def heavy_processing(input_str: str) -> str:
    return input_str[::-1]

async def process_task(message: aio_pika.IncomingMessage, redis_pool: redis.ConnectionPool):
    async with message.process():
        body = json.loads(message.body)
        task_id = body.get("task_id")
        print(f"Processing task {task_id}...")
        
        async with database.AsyncSessionLocal() as session:
            try:
                task = await session.get(models.Task, task_id)
                if not task:
                    print(f"Task {task_id} not found DB!")
                    return

                task.status = models.TaskStatus.PROCESSING
                await session.commit()
                
                await asyncio.sleep(5)
                
                input_data = task.input_data if task.input_data else body.get("input_data", f"Task-{task_id}")
                result_val = heavy_processing(input_data)
                
                task.status = models.TaskStatus.COMPLETED
                task.result = result_val
                await session.commit()
                await session.refresh(task)
                
                redis_client = redis.Redis(connection_pool=redis_pool, decode_responses=True)
                try:
                    task_data = schemas.TaskResponse.model_validate(task).model_dump()
                    await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=60)
                    print(f"Task {task_id} COMPLETED. Result: {result_val}")
                finally:
                    await redis_client.aclose()
                    
            except Exception as e:
                print(f"Error processing task {task_id}: {e}")
                
                try:
                    await session.rollback()
                    task = await session.get(models.Task, task_id)
                    if task:
                        task.status = models.TaskStatus.FAILED
                        task.result = str(e)
                        await session.commit()
                        print(f"Task {task_id} marked as FAILED.")
                        
                        redis_client = redis.Redis(connection_pool=redis_pool, decode_responses=True)
                        try:
                            await redis_client.delete(f"task:{task_id}")
                        finally:
                            await redis_client.aclose()
                except Exception as db_err:
                    print(f"CRITICAL: Failed to update task status to FAILED: {db_err}")

async def main():
    redis_pool = redis.ConnectionPool(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    
    try:
        connection = await mq.get_connection()
    except Exception as e:
        print(f"Failed to connect to RabbitMQ after retries: {e}")
        return

    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        
        print("Worker waiting for messages...")
        await channel.set_qos(prefetch_count=1)
        
        async def wrapper(message):
            await process_task(message, redis_pool)

        await queue.consume(wrapper)
        
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker stopped.")
