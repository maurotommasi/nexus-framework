import sys
import os
import threading
import argparse
import socket
import uvicorn
import json
import tempfile

from nexus.core.decorators.routingAllowance import route_allow_cli_web
from nexus.core.decorators.cliAllowance import cli_restricted

# Add framework/commandline to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "framework", "commandline"))

from nexus.commandline import nexus_cli
import nexus.interface.autoloader_routes as autoloader_routes  # FastAPI app


def get_free_port() -> int:
    """Find an available port on the system."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def run_web(host: str = "127.0.0.1", port: int = None):
    """Run FastAPI web server with Uvicorn on given host/port (default localhost + free port)."""
    if port is None:
        port = get_free_port()

    print(f"[WEB] Starting FastAPI server on http://{host}:{port}")
    uvicorn.run(
        autoloader_routes.app,
        host=host,
        port=port,
        reload=False,
    )

CLI_LOCK_FILE = os.path.join(tempfile.gettempdir(), "nexus_cli.lock")

def run_cli():
    """Run CLI main function (blocking), single instance enforced."""
    # Check if lock file exists
    if os.path.exists(CLI_LOCK_FILE):
        print("[CLI] Another CLI instance is already running. Exiting.")
        return

    # Create lock file
    with open(CLI_LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    try:
        print("[CLI] Starting Nexus CLI...")
        nexus_cli.main()
    finally:
        # Remove lock file on exit
        if os.path.exists(CLI_LOCK_FILE):
            os.remove(CLI_LOCK_FILE)


def print_summary(summary: dict, json_mode: bool = False, file_path: str = None):
    """Print instance summary in table or JSON format, optionally save to file."""
    if json_mode:
        output = json.dumps(summary, indent=2)
        print(output)
    else:
        output = (
            "\n=== Nexus Instance Summary ===\n"
            f" PID   : {summary['pid']}\n"
        )
        for m in summary["modes"]:
            if m["type"] == "WEB":
                output += f" Mode  : WEB → http://{m['host']}:{m['port']}\n"
            else:
                output += " Mode  : CLI\n"
        output += "==============================\n"
        print(output)

    # Save JSON summary to file if requested
    if file_path:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            print(f"[INFO] Summary written to {file_path}")
        except Exception as e:
            print(f"[ERROR] Could not write summary file: {e}")


def main():
    parser = argparse.ArgumentParser(description="Nexus runner")
    parser.add_argument("--cli", action="store_true", help="Run Nexus CLI")
    parser.add_argument("--web", action="store_true", help="Run Nexus Web (FastAPI)")
    parser.add_argument("--port", type=int, default=None, help="Optional custom port for web mode")
    parser.add_argument("--host", type=str, default="127.0.0.1",
                        help="Host to bind the web server (default: 127.0.0.1, use 0.0.0.0 for external access)")
    parser.add_argument("--json-summary", action="store_true", help="Output startup summary as JSON")
    parser.add_argument("--summary-file", type=str, help="Write JSON summary to file")
    args = parser.parse_args()

    if not args.cli and not args.web:
        parser.print_help()
        sys.exit(1)

    pid = os.getpid()
    summary = {"pid": pid, "modes": []}

    threads = []

    if args.web:
        port = args.port or get_free_port()
        summary["modes"].append({"type": "WEB", "host": args.host, "port": port})
        web_thread = threading.Thread(target=run_web, kwargs={"host": args.host, "port": port}, daemon=True)
        threads.append(web_thread)
        web_thread.start()

    if args.cli:
        summary["modes"].append({"type": "CLI"})
        cli_thread = threading.Thread(target=run_cli)
        threads.append(cli_thread)
        cli_thread.start()

    # Print summary (table or JSON) and optionally save to file
    print_summary(summary, json_mode=args.json_summary, file_path=args.summary_file)

    for t in threads:
        t.join()


if __name__ == "__main__":
    main()
