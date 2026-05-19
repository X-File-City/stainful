# OneBusAway conformance fixture

Verbatim copies from the public, Apache-2.0 [`OneBusAway/sdk-config`](https://github.com/OneBusAway/sdk-config)
repo (fetched 2026-05-19):

- `stainless-config.yml` — a **real, production Stainless config**. This is the
  drop-in-compatibility ground truth: stainful must parse it with zero errors and
  produce a recognizably-equivalent Python SDK.
- `openapi.yml` — the OpenAPI 3.0.0 spec it overlays. Exercises `allOf` envelope
  composition (`ResponseWrapper + {data}`) — the canonical hard case for the resolver.

OneBusAway also publishes the Stainless-*generated* SDKs (python-sdk, etc.); those are
the output oracle for later slices.
