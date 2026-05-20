import argparse
import importlib.metadata as md
import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import habitat
import habitat_sim


START_TIME = time.time()


def build_payload(port: int) -> dict:
    return {
        "ok": True,
        "service": "habitat",
        "host": "127.0.0.1",
        "port": port,
        "pid": os.getpid(),
        "uptime_seconds": round(time.time() - START_TIME, 3),
        "habitat_sim_version": md.version("habitat-sim"),
        "habitat_lab_version": md.version("habitat-lab"),
        "habitat_sim_path": habitat_sim.__file__,
        "habitat_path": habitat.__file__,
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
        description="Run a lightweight Habitat health service"
    )
    parser.add_argument("--port", type=int, default=8401)
    args = parser.parse_args()

    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    print(f"Habitat service listening on http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
