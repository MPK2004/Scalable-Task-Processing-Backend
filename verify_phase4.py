import httpx
import asyncio
import sys

BASE_URL = "http://localhost:8005"

async def verify_worker():
    print("Verifying Phase 4: Worker Service...")
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/tasks/")
        if response.status_code != 201:
            print(f"Failed to create task: {response.text}")
            return False
        
        task_data = response.json()
        task_id = task_data["id"]
        print(f"Created Task ID: {task_id}")

        print("Waiting for task completion (expecting ~5s)...")
        for i in range(10):
            await asyncio.sleep(1)
            response = await client.get(f"/tasks/{task_id}")
            task_status = response.json()
            status = task_status["status"]
            print(f"Time {i+1}s: Status = {status}")
            
            if status == "COMPLETED":
                print("Task Completed!")
                if task_status["result"] == "Computed!":
                    print("Result Verified!")
                    return True
                else:
                    print(f"Error: Unexpected result {task_status['result']}")
                    return False
        
        print("Error: Timeout waiting for task completion.")
        return False

if __name__ == "__main__":
    if not asyncio.run(verify_worker()):
        sys.exit(1)
    print("Phase 4 Verification Passed!")
