---
name: llm-local-qwen
description: "Use this skill when the user wants to call the locally deployed vLLM model on port 9001. The served model is qwen3.5-0.8b and the endpoint is OpenAI-compatible. Use it for local text generation, chat completion, structured JSON generation, prompt experiments, and local model inference without external network access."
license: Proprietary. Local workspace tool.
---

# Local Qwen vLLM skill

This folder exposes the local vLLM deployment running on `127.0.0.1:9001`.

The current served model is:

- `qwen3.5-0.8b`

The API is OpenAI-compatible.

## When to use

Use this skill when the task needs any of the following:

- local chat completion
- local prompt testing
- local structured JSON generation
- local text generation without external API calls
- querying the deployed model list or service health

## First step: verify the local service

Always do this before sending generation requests:

```bash
 python3 BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py health
 python3 BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py models
```

Behavior:

- attach to the already-running local vLLM service on `127.0.0.1:9001`
- if the service is unavailable, fail fast and report the endpoint problem to the caller
- Stage3 normal workflow must not redeploy or restart the local service from this skill

Expected runtime:

- base URL: `http://127.0.0.1:9001`
- model id: `qwen3.5-0.8b`

## Capabilities

### 1. Health check

```bash
python3 BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py health
```

Returns direct service status data.

### 2. List models

```bash
python3 BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py models
```

Returns direct model metadata such as:

- `id`
- `owned_by`
- `max_model_len`
- `root`
- permissions metadata when provided by vLLM

### 3. Chat completion

One-shot chat request:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py chat \
  --system "You are a precise assistant." \
  --user "Summarize the key idea in one sentence."
```

Or send a full OpenAI-compatible request from JSON:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py chat-request \
  --request-file /abs/path/to/request.json
```

Example request file:

```json
{
  "model": "qwen3.5-0.8b",
  "messages": [
    {"role": "system", "content": "Return strict JSON."},
    {"role": "user", "content": "Give me a JSON object with keys a and b."}
  ],
  "temperature": 0,
  "max_tokens": 256
}
```

For strict short answers or strict JSON, set `temperature` low and state the output contract explicitly in the prompt. Do not assume the model will naturally stay terse unless instructed.

### 4. Text completion

If a task specifically wants completion-style prompting:

```bash
python3 BENCHCLAW_ROOT/annotation-tool/llm-local/llm_local_client.py completion \
  --prompt "Write a concise title for a report about road segmentation."
```

## Data the skill can return directly

Health response fields:

- HTTP status
- reachability of `/health`

Model listing fields:

- `object`
- `data`
- per-model `id`
- per-model `root`
- per-model `max_model_len`

Chat/completion response fields typically include:

- `id`
- `object`
- `created`
- `model`
- `choices`
- `usage`
- assistant text content from `choices[*].message.content`
- finish reason

The skill returns structured JSON directly. If a task needs files, the agent should decide file paths at call time and write derived artifacts itself.

## Practical guidance

- This skill is aligned with `/home/maqiang/model_api/qwen3.5_0.8B.sh`.
- Prefer `chat` for ordinary local assistant calls.
- Prefer `chat-request` when you need exact OpenAI-compatible request control.
- Prefer `completion` only when the task specifically wants prompt-string completion semantics.
- Do not assume any fixed output directory. Consume returned JSON directly unless the task explicitly needs files.
- If you need strict JSON or bounded output, say so explicitly and keep `temperature` near `0`.
