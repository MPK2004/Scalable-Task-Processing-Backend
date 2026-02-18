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

async def process_task(message: aio_pika.IncomingMessage):
    async with message.process():
        body = json.loads(message.body)
        task_id = body.get("task_id")
        print(f"Processing task {task_id}...")
        
        await asyncio.sleep(5)
        
        async with database.AsyncSessionLocal() as session:
            result = await session.get(models.Task, task_id)
            if result:
                result.status = models.TaskStatus.COMPLETED
                result.result = "Computed!"
                await session.commit()
                await session.refresh(result)
                
                redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
                try:
                    task_data = schemas.TaskResponse.model_validate(result).model_dump()
                    await redis_client.set(f"task:{task_id}", json.dumps(task_data))
                    print(f"Task {task_id} completed and cache updated.")
                finally:
                    await redis_client.aclose()
            else:
                print(f"Task {task_id} not found in DB!")

async def main():
    try:
        connection = await mq.get_connection()
    except Exception as e:
        print(f"Failed to connect to RabbitMQ after retries: {e}")
        return

    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        
        print("Worker waiting for messages...")
        await queue.consume(process_task)
        
        await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Worker stopped.")
