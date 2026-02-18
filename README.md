# Scalable Task Processing Backend (Interview-Ready)

A production-style asynchronous task processing system built with FastAPI, PostgreSQL, Redis, RabbitMQ, and Docker.

## 🏗️ Architecture

```
+------------+        +---------------+        +-----------+
|   Client   | -----> | FastAPI (API) | -----> | PostgreSQL|
+------------+        +---------------+        +-----------+
                             |
                             v
                       +------------+
                       | RabbitMQ   |
                       +------------+
                             |
                             v
                       +------------+
                       |  Worker    |
                       +------------+
                             |
                             v
                         Redis Cache
```

## 🚀 Request Lifecycle (Full CRUD Flow)

1.  **Submit Task (`POST /tasks`)**
    *   Client sends payload `{"input_data": "hello"}`.
    *   **Service Layer** creates a Task record in **PostgreSQL** with status `PENDING`.
    *   Service pushes the Task ID to **RabbitMQ** queue.
    *   Service caches initial state in **Redis** (Write-through).
    *   Returns `201 Created` with Task ID to client.

2.  **Process Task (Async Worker)**
    *   **Worker** consumes message from RabbitMQ.
    *   Updates DB status to `PROCESSING`.
    *   Performs transformation (String Reversal: "olleh") and simulates delay (5s).
    *   Updates DB status to `COMPLETED` and saves result.
    *   Updates **Redis** with result and sets TTL (60s).

3.  **Check Status (`GET /tasks/{id}`)**
    *   **Service Layer** checks **Redis** first (Cache Hit).
    *   If miss, fetches from **PostgreSQL** and populates Redis (Read-through).
    *   Returns JSON: `{"status": "COMPLETED", "result": "olleh"}`.

## 🛠️ Tech Stack & Key Decisions

*   **FastAPI**: Modern, high-performance, strictly typed (Pydantic).
*   **PostgreSQL (SQLAlchemy + Enum)**: Robust relational data storage with strict schema.
*   **Redis**: High-speed caching layer to reduce DB load on status polling.
*   **RabbitMQ**: Reliable message broker to decouple API from heavy processing.
*   **Docker Compose**: Full system orchestration with Health Checks and Service dependency management.

## 📦 Setup & Running

1.  **Start the System**
    ```bash
    docker compose up -d --build
    ```

2.  **Access API**
    *   Swagger UI: [http://localhost:8005/docs](http://localhost:8005/docs)
    *   API Root: [http://localhost:8005](http://localhost:8005)

3.  **Verify System**
    ```bash
    # Install dependency
    pip install httpx
    
    # Run End-to-End Test
    python verify_phase4.py
    ```

## 🧪 API Endpoints

### `POST /tasks/`
Create a new task.
*   **Body**: `{"input_data": "string to reverse"}`
*   **Response**: `{"id": 1, "status": "PENDING", "result": null}`

### `GET /tasks/{id}`
Get task status.
*   **Response**: `{"id": 1, "status": "COMPLETED", "result": "esrever ot gnirts"}`

## ⚠️ Failure Handling

*   **Worker Crash**: If the worker crashes mid-task, the message is unacknowledged (if configured) or the task remains in `PROCESSING` state in DB.
    *   *Mitigation*: Implement a "Stuck Task Sweeper" cron job or Dead Letter Queue (DLQ).
*   **DB/Queue Down**: The API implements **Retry Logic** (5 attempts) during startup to handle race conditions.
*   **Cache Miss**: System gracefully falls back to DB if Redis is unavailable or key expires.

## 📈 Scalability Strategy

*   **Horizontal Scaling (Workers)**: Spin up multiple worker containers (`docker compose up -d --scale worker=3`). RabbitMQ automatically round-robins tasks.
*   **Database**: Use Read Replicas for `GET` requests and a primary for `POST`.
*   **Redis Cluster**: Use Redis Cluster mode for high availability and partitioning.

## 🛑 Limitations

*   **No Dead Letter Queue**: Failed messages are acked (removed from queue) but marked FAILED in DB. Ideally, retriable errors should go to a DLQ.
*   **Authentication**: Currently open API. Needs OAuth2/JWT for production.
*   **Observability**: Basic logging. Needs Prometheus/Grafana or ELK stack for real monitoring.

## 🔮 Future Improvements

*   **Dead Letter Queue (DLQ)**: Handle tasks that repeatedly fail.
*   **Authentication**: Add JWT (OAuth2) for secure task access.
*   **Prometheus/Grafana**: Monitoring for Queue depth and Worker latency.
