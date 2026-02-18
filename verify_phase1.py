import httpx
import asyncio
import sys

BASE_URL = "http://localhost:8002"

async def test_api():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # 1. Test Root
        try:
            response = await client.get("/")
            print(f"GET / status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error: {response.text}")
                return False
        except httpx.ConnectError:
            print("Failed to connect to API")
            return False

        # 2. Create Task
        response = await client.post("/tasks/")
        print(f"POST /tasks/ status: {response.status_code}")
        if response.status_code != 201:
            print(f"Error: {response.text}")
            return False
        
        task_data = response.json()
        task_id = task_data["id"]
        print(f"Created Task ID: {task_id}")

        # 3. Get Task
        response = await client.get(f"/tasks/{task_id}")
        print(f"GET /tasks/{task_id} status: {response.status_code}")
        if response.status_code != 200:
            print(f"Error: {response.text}")
            return False
        
        task_status = response.json()
        print(f"Task Status: {task_status}")
        
    return True

if __name__ == "__main__":
    if not asyncio.run(test_api()):
        sys.exit(1)
    print("Phase 1 Verification Passed!")
