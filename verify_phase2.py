import httpx
import asyncio
import redis.asyncio as redis
import json
import sys

BASE_URL = "http://localhost:8002"
REDIS_URL = "redis://localhost:6381"

async def verify_redis_caching():
    print("Verifying Phase 2: Redis Caching...")
    
    # 1. Setup Redis Client
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        await r.ping()
        print("Connected to Redis.")
    except Exception as e:
        print(f"Failed to connect to Redis: {e}")
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

        # 3. Verify it's in Redis
        cached_value = await r.get(f"task:{task_id}")
        if not cached_value:
            print("Error: Task not found in Redis after creation!")
            return False
        
        cached_json = json.loads(cached_value)
        if cached_json["id"] != task_id:
            print("Error: Redis data mismatch!")
            return False
            
        print("Redis Cache Hit Verified (Write-through on Create).")

        response = await client.get(f"/tasks/{task_id}")
        if response.status_code != 200:
            print(f"Failed to get task: {response.text}")
            return False
            
        print("GET /tasks/{id} successful.")

    await r.aclose()
    return True

if __name__ == "__main__":
    if not asyncio.run(verify_redis_caching()):
        sys.exit(1)
    print("Phase 2 Verification Passed!")
