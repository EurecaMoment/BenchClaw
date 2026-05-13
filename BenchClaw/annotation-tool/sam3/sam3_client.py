#!/usr/bin/env python3
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request


HOST = os.environ.get("SAM3_HOST", "127.0.0.1")
PORT = int(os.environ.get("SAM3_PORT", "8765"))
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_PATH = os.path.join(ROOT_DIR, "sam3_service.py")
SERVICE_LOG = os.path.join(ROOT_DIR, "service.log")
BASE_URL = f"http://{HOST}:{PORT}"
CONDA_EXE = os.environ.get("CONDA_EXE", "/home/maqiang/miniconda3/bin/conda")


def _http_get(path):
    with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_post(path, payload):
    data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=3600) as response:
        return json.loads(response.read().decode("utf-8"))


def service_is_ready():
    try:
        payload = _http_get("/health")
        return bool(payload.get("ok"))
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError, json.JSONDecodeError):
        return False


def ensure_server(timeout_seconds=180):
    if service_is_ready():
        return {"reused": True, "url": BASE_URL}

    command = [
        CONDA_EXE,
        "run",
        "--no-capture-output",
        "-n",
        "sam3",
        "python3",
        SERVICE_PATH,
        "--host",
        HOST,
        "--port",
        str(PORT),
    ]
    log_handle = open(SERVICE_LOG, "a", encoding="utf-8")
    subprocess.Popen(
        command,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        cwd=ROOT_DIR,
        start_new_session=True,
    )

    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if service_is_ready():
            return {"reused": False, "url": BASE_URL, "log": SERVICE_LOG}
        time.sleep(2)

    raise RuntimeError(f"SAM3 local service did not become ready within {timeout_seconds} seconds")


def print_json(payload):
    print(json.dumps(payload, ensure_ascii=True, indent=2))


def cmd_health(_args):
    print_json(_http_get("/health"))


def cmd_ensure_server(args):
    print_json(ensure_server(timeout_seconds=args.timeout))


def cmd_image_infer(args):
    ensure_server(timeout_seconds=args.timeout)
    payload = {
        "image_path": os.path.abspath(args.image_path),
        "text_prompt": args.text_prompt,
        "save_masks_dir": os.path.abspath(args.save_masks_dir) if args.save_masks_dir else None,
        "confidence_threshold": args.confidence_threshold,
        "checkpoint_path": args.checkpoint_path,
        "include_logits": args.include_logits,
        "box_prompts": [json.loads(item) for item in args.box_prompt],
    }
    print_json(_http_post("/image/infer", payload))


def cmd_image_request(args):
    ensure_server(timeout_seconds=args.timeout)
    with open(args.request_file, "r", encoding="utf-8") as handle:
        request_payload = json.load(handle)
    print_json(_http_post("/image/request", {"request": request_payload}))


def cmd_video_request(args):
    ensure_server(timeout_seconds=args.timeout)
    with open(args.request_file, "r", encoding="utf-8") as handle:
        request_payload = json.load(handle)
    payload = {
        "version": args.version,
        "checkpoint_path": args.checkpoint_path,
        "compile": args.compile,
        "stream": args.stream,
        "request": request_payload,
    }
    print_json(_http_post("/video/request", payload))


def build_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    ensure_parser = subparsers.add_parser("ensure-server")
    ensure_parser.add_argument("--timeout", type=int, default=180)
    ensure_parser.set_defaults(func=cmd_ensure_server)

    health_parser = subparsers.add_parser("health")
    health_parser.set_defaults(func=cmd_health)

    image_parser = subparsers.add_parser("image-infer")
    image_parser.add_argument("--image-path", required=True)
    image_parser.add_argument("--text-prompt", default="")
    image_parser.add_argument("--save-masks-dir")
    image_parser.add_argument("--confidence-threshold", type=float, default=0.2)
    image_parser.add_argument("--box-prompt", action="append", default=[])
    image_parser.add_argument("--checkpoint-path")
    image_parser.add_argument("--include-logits", action="store_true")
    image_parser.add_argument("--timeout", type=int, default=180)
    image_parser.set_defaults(func=cmd_image_infer)

    image_request_parser = subparsers.add_parser("image-request")
    image_request_parser.add_argument("--request-file", required=True)
    image_request_parser.add_argument("--timeout", type=int, default=180)
    image_request_parser.set_defaults(func=cmd_image_request)

    video_parser = subparsers.add_parser("video-request")
    video_parser.add_argument("--request-file", required=True)
    video_parser.add_argument("--version", default="sam3.1")
    video_parser.add_argument("--checkpoint-path")
    video_parser.add_argument("--compile", action="store_true")
    video_parser.add_argument("--stream", action="store_true")
    video_parser.add_argument("--timeout", type=int, default=180)
    video_parser.set_defaults(func=cmd_video_request)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
