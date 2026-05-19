# Changelog

All notable changes to this project are documented here.
Format loosely follows [Keep a Changelog](https://keepachangelog.com/).

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

### Known gaps (v1.1 backlog — see `DESIGN.md §7`)
`to_json()/.to_dict()` helper aliases · rich `APIResponse` object ·
per-file model modules · typed error-body models · `custom_casings`.
