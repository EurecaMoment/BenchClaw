#!/usr/bin/env python3
import base64
import json
import mimetypes
import os
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_SYSTEM_PROMPT = (
    "You are evaluating benchmark items. Answer concisely and only with the answer. "
    "Do not explain unless the question explicitly asks for explanation."
)


def load_yaml_like(path: Path):
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        try:
            import yaml  # type: ignore

            return yaml.safe_load(text)
        except Exception as exc:
            raise RuntimeError(f"cannot parse roster/config file {path}: {exc}")


def load_roster(benchclaw_root: Path):
    roster_path = benchclaw_root / "modelNeedMeasured" / "model_roster.yaml"
    if not roster_path.exists():
        raise FileNotFoundError(f"missing model roster: {roster_path}")
    data = load_yaml_like(roster_path)
    if not isinstance(data, dict):
        raise RuntimeError(f"invalid model roster content: {roster_path}")
    models = data.get("models") or data.get("candidate_models") or []
    if not isinstance(models, list) or not models:
        raise RuntimeError(f"model roster has no models: {roster_path}")
    return data


def resolve_api_key(roster: dict):
    env_name = roster.get("api_key_env") or "YEYSAI_API_KEY"
    env_value = os.environ.get(env_name, "").strip()
    if env_value and env_value != "xxxx":
        return env_value, env_name
    inline = str(roster.get("api_key") or "").strip()
    if inline and inline != "xxxx":
        return inline, "inline"
    raise RuntimeError(
        f"missing usable API key: set {env_name} or replace placeholder api_key in model_roster.yaml"
    )


def to_data_url(path: Path):
    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{payload}"


def build_user_text(row: dict):
    question = str(row.get("question") or row.get("prompt") or "").strip()
    options = row.get("options") or []
    lines = []
    if question:
        lines.append(question)
    if isinstance(options, list) and options:
        lines.append("")
        lines.append("Options:")
        for idx, opt in enumerate(options):
            lines.append(f"{idx + 1}. {opt}")
    return "\n".join(lines).strip()


def build_messages(row: dict, media_paths):
    content = [{"type": "text", "text": build_user_text(row)}]
    for media_path in media_paths:
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": to_data_url(Path(media_path))},
            }
        )
    return [
        {
            "role": "system",
            "content": [{"type": "text", "text": DEFAULT_SYSTEM_PROMPT}],
        },
        {"role": "user", "content": content},
    ]


def extract_text_from_choice(choice: dict):
    message = choice.get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text") or ""))
        return "\n".join(p for p in parts if p).strip()
    return str(content or "")


def chat_completion(api_base: str, api_key: str, model: str, messages, timeout=180):
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 512,
    }
    req = urllib.request.Request(
        api_base,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail}")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"request failed: {exc}")

    data = json.loads(body)
    choices = data.get("choices") or []
    if not choices:
        raise RuntimeError(f"empty choices in API response: {body[:500]}")
    text = extract_text_from_choice(choices[0]).strip()
    return {
        "prediction": text,
        "response_id": data.get("id"),
        "usage": data.get("usage") or {},
        "raw": data,
    }
