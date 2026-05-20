import argparse
import importlib.metadata as md
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

from libero.libero import benchmark
from libero.libero.envs import OffScreenRenderEnv


START_TIME = time.time()
SUITE = benchmark.get_benchmark_dict()["libero_10"]()
TASK = SUITE.get_task(0)


def build_payload(port: int) -> dict:
    return {
        "ok": True,
        "service": "libero",
        "host": "127.0.0.1",
        "port": port,
        "pid": os.getpid(),
        "uptime_seconds": round(time.time() - START_TIME, 3),
        "libero_version": md.version("libero"),
        "robosuite_version": md.version("robosuite"),
        "benchmark": "libero_10",
        "task_name": TASK.name,
        "task_language": TASK.language,
        "offscreen_env_import_ok": bool(OffScreenRenderEnv),
    }


class Handler(BaseHTTPRequestHandler):
    def _write_json(self, status_code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path in {"/", "/health"}:
            self._write_json(200, build_payload(self.server.server_port))
            return
        self._write_json(404, {"ok": False, "error": "not_found", "path": self.path})

    def log_message(self, _format: str, *_args) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a lightweight LIBERO health service"
    )
    parser.add_argument("--port", type=int, default=8402)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"LIBERO service listening on http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
