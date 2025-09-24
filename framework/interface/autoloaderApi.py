import os
import sys
import uuid
import asyncio
import inspect
import importlib
import pkgutil
from pathlib import Path
from fastapi import FastAPI, APIRouter, BackgroundTasks, WebSocket
from fastapi.responses import JSONResponse
from pydantic import create_model
import uvicorn

app = FastAPI(title="Nexus Auto API")

# =========================================
# Environment config
# =========================================
ALLOW_HTTP_REQUESTS = os.getenv("ALLOW_HTTP_REQUESTS", "false").lower() == "true"
HTTPS_CERT_FILE = os.getenv("HTTPS_CERT_FILE", "cert.pem")
HTTPS_KEY_FILE = os.getenv("HTTPS_KEY_FILE", "key.pem")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

# =========================================
# Task storage
# =========================================
tasks_status = {}  # task_id -> status
tasks_logs = {}    # task_id -> asyncio.Queue
global_log_subscribers = set()  # all global subscribers

# =========================================
# WebSocket logger for capturing print()
# =========================================
class WebSocketLogger:
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue

    def write(self, message):
        if message.strip():
            asyncio.create_task(self.queue.put(message.strip()))

    def flush(self):
        pass

async def broadcast_log(message: str):
    """Send a log message to all global subscribers."""
    to_remove = set()
    for ws in global_log_subscribers:
        try:
            await ws.send_text(message)
        except Exception:
            to_remove.add(ws)
    global_log_subscribers.difference_update(to_remove)

# =========================================
# Auto-register routes from framework/
# =========================================
def auto_register_routes(base_package: str, base_path: Path, app: FastAPI):
    router = APIRouter()

    for module_info in pkgutil.walk_packages([str(base_path)], f"{base_package}."):
        module = importlib.import_module(module_info.name)
        module_rel_path = module_info.name.replace(base_package + ".", "")
        module_url = "/".join(module_rel_path.split("."))

        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module_info.name:
                continue

            class_instance = cls()

            for method_name, method in inspect.getmembers(cls, inspect.isfunction):
                if getattr(method, "_is_public", False):
                    route_path = f"/{module_url}/{cls.__name__.lower()}/{method_name}"
                    sig = inspect.signature(method)

                    # Build dynamic Pydantic model
                    fields = {}
                    for name, param in sig.parameters.items():
                        if name == "self":
                            continue
                        param_type = param.annotation if param.annotation != inspect._empty else str
                        default_value = param.default if param.default != inspect._empty else ...
                        fields[name] = (param_type, default_value)

                    RequestModel = create_model(f"{cls.__name__}_{method_name}_Model", **fields)

                    # Endpoint factory
                    async def endpoint_factory(m=method, inst=class_instance):
                        async def endpoint(payload: RequestModel, background_tasks: BackgroundTasks):
                            task_id = str(uuid.uuid4())
                            tasks_status[task_id] = "queued"
                            tasks_logs[task_id] = asyncio.Queue()

                            async def task_runner():
                                queue = tasks_logs[task_id]
                                old_stdout = sys.stdout
                                sys.stdout = WebSocketLogger(queue)
                                try:
                                    tasks_status[task_id] = "running"
                                    print(f"[{task_id}] Input: {payload.dict()}")
                                    await broadcast_log(f"[{task_id}] Input: {payload.dict()}")

                                    result = m(inst, **payload.dict())
                                    if inspect.isawaitable(result):
                                        result = await result

                                    print(f"[{task_id}] Result: {result}")
                                    await broadcast_log(f"[{task_id}] Result: {result}")
                                    tasks_status[task_id] = "done"
                                    return result
                                except Exception as e:
                                    print(f"[{task_id}] Error: {str(e)}")
                                    await broadcast_log(f"[{task_id}] Error: {str(e)}")
                                    tasks_status[task_id] = "error"
                                    return {"error": str(e)}
                                finally:
                                    sys.stdout = old_stdout
                                    await queue.put("__TASK_DONE__")

                            # Try immediate return
                            try:
                                result = await asyncio.wait_for(task_runner(), timeout=0.01)
                                return result
                            except asyncio.TimeoutError:
                                background_tasks.add_task(task_runner)
                                return {"task_id": task_id}

                        return endpoint

                    endpoint = endpoint_factory()
                    router.add_api_route(route_path, endpoint, methods=["POST"])

    app.include_router(router)

# =========================================
# WebSocket endpoints
# =========================================
@app.websocket("/ws/task_logs/{task_id}")
async def websocket_task_logs(websocket: WebSocket, task_id: str):
    """Private per-task logs (only requester sees logs)"""
    await websocket.accept()
    queue = tasks_logs.get(task_id)
    if not queue:
        await websocket.send_text("Unknown task_id")
        await websocket.close()
        return

    while True:
        log = await queue.get()
        if log == "__TASK_DONE__":
            await websocket.send_text("=== TASK DONE ===")
            break
        await websocket.send_text(log)
    await websocket.close()

@app.websocket("/ws/global_logs")
async def websocket_global_logs(websocket: WebSocket):
    """Global logs feed (all subscribers)"""
    await websocket.accept()
    global_log_subscribers.add(websocket)
    try:
        while True:
            await asyncio.sleep(1)
    except Exception:
        pass
    finally:
        global_log_subscribers.remove(websocket)

# =========================================
# Status endpoint
# =========================================
@app.get("/task_status/{task_id}")
async def task_status(task_id: str):
    return JSONResponse({"task_id": task_id, "status": tasks_status.get(task_id, "unknown")})

# =========================================
# Generate function: HTTPS default, HTTP optional
# =========================================
def generate(app: FastAPI):
    ssl_args = {"ssl_certfile": HTTPS_CERT_FILE, "ssl_keyfile": HTTPS_KEY_FILE}
    print(f"Starting HTTPS server on https://{HOST}:{PORT}")
    import threading
    threading.Thread(target=lambda: uvicorn.run(app, host=HOST, port=PORT, **ssl_args), daemon=True).start()

    if ALLOW_HTTP_REQUESTS:
        http_port = PORT + 1
        print(f"ALLOW_HTTP_REQUESTS enabled → starting HTTP server on http://{HOST}:{http_port}")
        threading.Thread(target=lambda: uvicorn.run(app, host=HOST, port=http_port), daemon=True).start()

# =========================================
# App initialization
# =========================================

auto_register_routes("framework", Path(__file__).parent / "framework", app)
