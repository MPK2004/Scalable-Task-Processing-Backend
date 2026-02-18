import httpx
import asyncio
import aio_pika
import json
import sys

BASE_URL = "http://localhost:8002"
RABBITMQ_URL = "amqp://guest:guest@localhost:5673/"
QUEUE_NAME = "task_queue"

async def verify_rabbitmq():
    print("Verifying Phase 3: RabbitMQ Integration...")
    
    try:
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)
        await queue.purge()
        print("Connected to RabbitMQ and purged queue.")
    except Exception as e:
        print(f"Failed to connect to RabbitMQ: {e}")
        return False

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 2. Create Task
        response = await client.post("/tasks/")
        if response.status_code != 201:
            print(f"Failed to create task: {response.text}")
            return False
        
        task_data = response.json()
        task_id = task_data["id"]
        print(f"Created Task ID: {task_id}")

        print("Waiting for message in queue...")
        try:
            message = await queue.get(timeout=5)
            async with message.process():
                body = json.loads(message.body)
                print(f"Received message: {body}")
                
                if body.get("task_id") == task_id:
                    print("Message verified! Task ID matches.")
                else:
                    print("Error: Task ID mismatch in message.")
                    return False
        except aio_pika.exceptions.QueueEmpty:
            print("Error: Queue empty! Message not published.")
            return False

    await connection.close()
    return True

if __name__ == "__main__":
    if not asyncio.run(verify_rabbitmq()):
        sys.exit(1)
    print("Phase 3 Verification Passed!")
