# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

## [0.1.0] — 2026-05-20

First public release. **The open-source Stainless** — point your existing
`stainless.yml` at it and get an idiomatic Python SDK.

### Added
- End-to-end generator: `stainless.yml` + OpenAPI 3.x → idiomatic Python SDK
  (typed pydantic models, typed error hierarchy, retries w/ backoff +
  `Retry-After` + idempotency, auto-pagination, SSE streaming, sync+async,
  per-file `types/`, `*Params` TypedDicts, vendored runtime).
- Quality harness measuring stainful's output against the **real**
  Stainless-generated OneBusAway SDK, gated in CI (no-regression baselines).

### Verified vs the real Stainless SDK (CI-gated)
- resource-method recall **1.00**, method-signature match **0.99**
- model-name recall **0.90**, generated code **mypy-clean (0 errors)**
- **28/29** of Stainless's own test files import unchanged against our output
- regeneration is bit-stable; the repo dogfoods itself
  (`examples/onebusaway/sdk`, guard-enforced)

### Known gaps (honest)
Python only; model-name long tail (~10%: a few `*Params`, `SearchFor*`
naming, `trip-details` singular); P3 behavioral-via-Prism not yet run.
Not affiliated with Stainless or Anthropic.

## [0.0.1] — 2026-05-19

First working release. **v1 complete (slices 1–6), 37 tests green.**

### Added
- `stainless.yml`-compatible config loader with position-aware diagnostics and a
  lenient/`strict` mode (drop-in: unknown keys preserved, not rejected).
- OpenAPI 3.x loader + cycle-safe `$ref` / `allOf` resolver.
- Rich, language-agnostic **IR** — 3-valued cardinality
  (`required` ≠ `optional` ≠ `nullable`), `ModelRef` cycle-breaking,
  discriminated unions, pagination/streaming intents.
- Hand-written Python **runtime** vendored into generated SDKs: httpx sync+async
  client, retries (backoff + jitter + `Retry-After` + idempotency keys), typed
  error hierarchy with `request_id`, pagination base classes, SSE streaming.
- **Python emitter**: pydantic v2 models (aliases, discriminated unions),
  nested resource clients, request bodies, query params, streaming `@overload`s,
  sync+async parity, package scaffold + generated `pyproject.toml`.
- Conformance fixtures: OneBusAway (REST/allOf/recursion) and chat
  (streaming/unions/bodies).

### Verified
- Output matches the real Stainless-generated `OneBusAway/python-sdk` on client
  class name, package, env var, and call shape — the drop-in symbol contract.

### Known gaps (v1.1 backlog — see the README Status section)
`to_json()/.to_dict()` helper aliases · rich `APIResponse` object ·
per-file model modules · typed error-body models · `custom_casings`.
