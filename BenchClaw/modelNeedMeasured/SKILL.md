# modelNeedMeasured

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

Provide the fixed multimodal model roster and the concrete API calling contract used by BenchClaw Stage5 evaluation.

This skill is the canonical source for:

1. the candidate models that must be evaluated in Stage5;
2. the OpenAI-compatible multimodal request format for `https://yeysai.com/v1/chat/completions`;
3. the API credential lookup rule;
4. the local client script that turns Stage4 eval items plus media files into real model predictions.

## Required Candidate Models

Stage5 must evaluate all of the following models:

```text
qwen3-vl-235b-a22b-instruct
kimi-k2.5
llama-4-maverick-17b-128e-instruct
grok-4-fast
gpt-5.4-mini-2026-03-17
glm-4.5v
gemini-3-flash-preview
claude-haiku-4-5-20251001-thinking
claude-sonnet-4-5-20250929
```

Stage5 must not silently drop, replace, rename, or subset this roster.

## API Contract

Use the OpenAI-compatible chat completions endpoint:

```text
POST https://yeysai.com/v1/chat/completions
Authorization: Bearer <api_key>
Content-Type: application/json
```

Credential lookup order:

1. `YEYSAI_API_KEY` environment variable;
2. `api_key` field in `BENCHCLAW_ROOT/modelNeedMeasured/model_roster.yaml` if it is not the placeholder `xxxx`.

If the resolved API key is empty or still equals `xxxx`, the caller must block instead of fabricating predictions.

## Multimodal Message Format

For image-based eval items, build `messages` in OpenAI-compatible multimodal format:

```json
[
  {
    "role": "system",
    "content": [
      {"type": "text", "text": "You are evaluating benchmark items. Answer concisely and only with the requested answer."}
    ]
  },
  {
    "role": "user",
    "content": [
      {"type": "text", "text": "<question and options>"},
      {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]
  }
]
```

The local client script must resolve Stage4 `image_refs` / `media_refs` to files under `WORKSPACE_ROOT/stage4/37-benchmark-artifact-pack/EVALSET_DATASET/media/`, encode them as data URLs, and call the endpoint with the selected model name.

## Files

- `BENCHCLAW_ROOT/modelNeedMeasured/model_roster.yaml`
- `BENCHCLAW_ROOT/modelNeedMeasured/yeysai_multimodal_client.py`

## Non-negotiable Constraints

- This skill defines a fixed required evaluation roster for Stage5.
- It does not authorize synthetic predictions, cached placeholders, or rule-based substitutes.
- If a model call fails, the caller must log the failure and keep the model in the evaluation summary with explicit missing/error counts.
- If an eval item references images, the caller must send a real multimodal request rather than downgrading the sample to text-only without explicit evidence that the sample has no media.
