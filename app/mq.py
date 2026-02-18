import aio_pika
import os
import json

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5673/")
QUEUE_NAME = "task_queue"

async def get_connection():
    import asyncio
    for i in range(5):
        try:
            return await aio_pika.connect_robust(RABBITMQ_URL)
        except Exception as e:
            if i == 4:
                raise e
            print(f"RabbitMQ connection failed, retrying in 2s... ({e})")
            await asyncio.sleep(2)

async def publish_task(task_id: int):
    connection = await get_connection()
    async with connection:
        channel = await connection.channel()
        
        # Declare queue
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        
        message_body = json.dumps({"task_id": task_id}).encode()
        
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key=QUEUE_NAME,
        )
