# Auto API Framework

A Python FastAPI framework that:

* Auto-generates REST endpoints from classes and methods in `framework/`
* Background task execution with immediate return if possible
* Private and global WebSocket log streaming
* HTTPS by default, HTTP optional via environment variable
* Dynamic route visibility via decorators (`public`, `restricted`, `cli_enabled`)

---

## Features

1. **Auto route generation**: `framework/<folder>/<file>.py` → `/folder/<classname>/<method>`
2. **Dynamic input parsing** with Pydantic models
3. **Background execution** with task IDs
4. **Per-task logs** via WebSocket (private)
5. **Global logs** via WebSocket (all tasks)
6. **Print statements streaming** to WebSocket
7. **HTTPS default**, HTTP optional (`ALLOW_HTTP_REQUESTS`)
8. **Dynamic route visibility**:

   * `@route_public` → always exposed
   * `@route_restricted()` → debug mode only
   * `@cli_enabled()` → CLI debug only

---

## Environment Variables

| Variable              | Default  | Description                  |
| --------------------- | -------- | ---------------------------- |
| `ALLOW_HTTP_REQUESTS` | false    | Allow HTTP server (insecure) |
| `HTTPS_CERT_FILE`     | cert.pem | Path to SSL certificate      |
| `HTTPS_KEY_FILE`      | key.pem  | Path to SSL private key      |
| `PORT`                | 8000     | Server port                  |
| `HOST`                | 0.0.0.0  | Server host                  |

---

## Installation

```bash
git clone <repo-url>
cd <repo-folder>
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn pydantic
```

---

## Example Framework Class

`framework/users/user_manager.py`

```python
from framework.core.decorators.routingAllowance import route_public, route_restricted
from framework.core.decorators.cliAllowance import cli_enabled
import asyncio

class UserManager:

    @route_public
    def create_user(self, name: str, age: int):
        print("Starting user creation...")
        return {"name": name, "age": age, "status": "created"}

    @route_restricted()
    async def debug_task(self, message: str, delay: int = 2):
        await asyncio.sleep(delay)
        print(f"Processed message: {message}")
        return {"message": message.upper(), "status": "done"}

    @cli_enabled()
    def cli_only_task(self, command: str):
        print(f"Executing CLI command: {command}")
        return f"Executed: {command}"
```

---

## Running the Server

```python
from fastapi import FastAPI
from nexus import auto_register_routes, generate
from pathlib import Path

app = FastAPI(title="Auto API")
auto_register_routes("framework", Path(__file__).parent / "framework", app)
generate(app)
```

---

## Example Usage

### 1. Create a user (fast sync method)

```http
POST /users/usermanager/create_user
Content-Type: application/json

{
  "name": "Alice",
  "age": 30
}
```

Response:

```json
{
  "name": "Alice",
  "age": 30,
  "status": "created"
}
```

---

### 2. Run a debug task (async, restricted)

```http
POST /users/usermanager/debug_task
Content-Type: application/json

{
  "message": "hello world",
  "delay": 3
}
```

Response (if slow):

```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480"
}
```

---

### 3. Run CLI task (requires `APP_CLI_DEBUG=true`)

```http
POST /users/usermanager/cli_only_task
Content-Type: application/json

{
  "command": "ls -la"
}
```

Response:

```json
{
  "task_id": "cli-task-id"
}
```

---

### 4. Check task status

```http
GET /task_status/f47ac10b-58cc-4372-a567-0e02b2c3d480
```

Response:

```json
{
  "task_id": "f47ac10b-58cc-4372-a567-0e02b2c3d480",
  "status": "running"
}
```

---

### 5. Connect to private WebSocket for task logs

```javascript
const ws = new WebSocket("ws://localhost:8000/ws/task_logs/f47ac10b-58cc-4372-a567-0e02b2c3d480");
ws.onmessage = (e) => console.log(e.data);
```

Output:

```
[task_id] Input: {...}
Starting user creation...
[task_id] Result: {...}
=== TASK DONE ===
```

---

### 6. Connect to global WebSocket logs

```javascript
const wsGlobal = new WebSocket("ws://localhost:8000/ws/global_logs");
wsGlobal.onmessage = (e) => console.log(e.data);
```

Output (all tasks):

```
[task_id1] Input: {...}
[task_id1] Result: {...}
[task_id2] Input: {...}
[task_id2] Result: {...}
```

---

### 7. Call method with nested folder

```http
POST /users/usermanager/debug_task
```

The endpoint is automatically generated based on folder/class/method structure.

---

### 8. Use environment variable for HTTP access

```bash
export ALLOW_HTTP_REQUESTS=true
python main.py
```

Server now listens on both HTTPS (default) and HTTP.

---

### 9. Run multiple tasks concurrently

Send multiple `debug_task` requests; all will run in background and stream logs independently.

---

### 10. Print statements auto-streamed

Any `print()` inside methods is automatically visible in per-task WebSocket and optionally in global feed.

---

### 11. Optional: Check logs of finished task

Connect to `/ws/task_logs/{task_id}` even after completion to see final output (queue stores logs until task finishes).

---

### 12. Security/Debug

* `route_restricted()` endpoints appear only if `APP_ROUTE_DEBUG=true`
* `cli_enabled()` endpoints appear only if `APP_CLI_DEBUG=true`

---

This README provides a **full overview**, usage examples, and instructions to integrate your **auto-router FastAPI framework** with private and global WebSocket logging, HTTPS support, and task management.
