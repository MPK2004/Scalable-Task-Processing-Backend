import asyncio
import asyncpg
import os

DATABASE_URL = "postgresql://postgres:postgres@localhost:5434/postgres"

async def create_db():
    print(f"Connecting to {DATABASE_URL}...")
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        print("Connected to postgres DB.")
        
        try:
            await conn.execute('CREATE DATABASE task_db')
            print("Database task_db created successfully.")
        except asyncpg.exceptions.DuplicateDatabaseError:
            print("Database task_db already exists.")
        
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(create_db())
