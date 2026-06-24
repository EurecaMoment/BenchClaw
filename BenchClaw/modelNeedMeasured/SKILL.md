# modelNeedMeasured

全局路径约束：`BENCHCLAW_ROOT` 仅作只读输入；`WORKSPACE_ROOT` 是本次流程唯一总工作目录，所有写操作和流程产物只能落在其下。

## Role

This skill defines how Stage5 reads and uses the model template configuration stored in:

- `BENCHCLAW_ROOT/modelNeedMeasured/model_config.json`

This skill itself no longer hardcodes any concrete model roster. All provider settings, model aliases, and test-group assignments must come from the JSON template.

## What The JSON Controls

`model_config.json` is the single source of truth for:

1. provider definitions in an opencode-style structure;
2. model aliases under each provider;
3. the default model fields;
4. the `grey_test` model group;
5. the `full_test` model group;
6. request-level defaults such as endpoint, API key placeholder, timeout, and multimodal capability flags.

## Required Read Order

Before Stage5 starts any real model call, the caller must:

1. read `BENCHCLAW_ROOT/modelNeedMeasured/model_config.json`;
2. resolve the provider and model alias referenced by the active test group;
3. verify that every selected model exists in `provider.<provider_id>.models`;
4. verify that the selected provider exposes an OpenAI-compatible endpoint;
5. block if the config is incomplete instead of fabricating or silently replacing models.

## Config Conventions

The JSON uses an opencode-like top-level layout:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "provider": {},
  "model": "provider_id/model_id",
  "small_model": "provider_id/model_id",
  "grey_test": {},
  "full_test": {}
}
```

Interpretation rules:

- `provider` contains provider definitions and their `models`.
- `model` is the default primary model reference.
- `small_model` is the default lightweight model reference.
- `grey_test.models` lists the models used for canary or small-batch evaluation.
- `full_test.models` lists the models used for full benchmark evaluation.

## How Stage5 Chooses Models

When running grey validation:

- load `grey_test.models`;
- evaluate only that group unless the user explicitly overrides the stage behavior;
- preserve listed order unless the caller has a documented scheduling reason.

When running full evaluation:

- load `full_test.models`;
- treat that group as the full evaluation target set;
- do not silently inherit grey-only models unless they are also listed in `full_test.models`.

If any configured model is missing, disabled, or unresolved, the caller must fail loudly and record the exact config problem.

## Multimodal Calling Contract

Providers referenced by this template are expected to expose an OpenAI-compatible chat completions API. For image-based eval items, callers should build multimodal `messages` in standard OpenAI-compatible format, for example:

```json
[
  {
    "role": "system",
    "content": [
      {
        "type": "text",
        "text": "You are evaluating benchmark items. Answer concisely and only with the requested answer."
      }
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

The local caller must resolve Stage4 `image_refs` or `media_refs` to real files, encode them as data URLs when required by the selected provider, and submit the request using the provider settings declared in `model_config.json`.

## Files

- `BENCHCLAW_ROOT/modelNeedMeasured/model_config.json`

## Non-negotiable Constraints

- This skill is a usage guide for the JSON template, not a hardcoded model roster.
- Concrete model names must live in `model_config.json`, not in this document.
- If the resolved API key, base URL, or model alias is missing, the caller must block instead of fabricating predictions.
- If an eval item references images, the caller must send a real multimodal request unless the selected config explicitly marks that model as text-only.
- If a model call fails, the caller must log the failure and keep the model in the evaluation summary with explicit missing or error counts.
