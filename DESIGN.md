# stainful — Architecture & IR Design

> v1 scope: **Python SDK generator**, fully-OSS, clean-room, drop-in
> `stainless.yml`-compatible. The IR is the moat — designed here twice before code.
> Companion to `RESEARCH.md`. Date: 2026-05-19.

---

## 1. Pipeline (deep modules, narrow interfaces)

```
 stainful.yml ─┐                                                   ┌─► Python SDK source
 (== Stainless │                                                   │   (httpx + pydantic v2)
  config fmt)  │                                                   │
               ▼                                                   │
  [config.loader] ──┐                                              │
                    ├─► [ir.builder] ─► IR ─► [emit.python.emitter]─┤
  [openapi.loader] ─┘     (the moat)                                │
       │                                                            └─► vendored
  [openapi.resolver]                                                    [runtime] (hand-written)
  (deref $ref, merge allOf)
```

Each bracket is a module with one public function. No module reaches across the IR
boundary: loaders never know about Python; the emitter never parses OpenAPI. This is the
"build deep modules, minimize interfaces" principle applied — the IR is the *only*
contract between the front half (spec understanding) and back half (code generation).

**Public interfaces (the entire surface area):**

```python
config.loader.load_config(path)          -> Config          # typed stainless.yml
openapi.loader.load_spec(path)           -> OpenAPIDocument  # parsed + resolved
ir.builder.build_ir(spec, config)        -> API              # the IR root
emit.python.emit(api, out_dir)           -> None             # writes the SDK
```

Four functions. Everything else is private. A second language (v3) is *only* a fifth
function `emit.go.emit(api, out_dir)` — it consumes the same `API`, writes nothing back.

---

## 2. Design twice — IR modeling

### Approach A — "Thin IR" (rejected)

IR ≈ normalized OpenAPI + a bag of config annotations. The emitter resolves unions,
decides nullability, walks the resource tree, infers pagination at render time.

- ✅ Less upfront type modeling.
- ❌ The moat (the §4-RESEARCH 13 capabilities) leaks into the emitter. Python-specific
  logic tangles with semantic logic. A second language re-derives everything. The IR is
  untestable in isolation. Special cases multiply in the renderer — exactly the
  "exponential complexity from special cases" failure mode.

### Approach B — "Rich semantic IR" (**chosen**)

IR is a **fully resolved, language-agnostic semantic model**. By the time the IR exists:
all `$ref` dereferenced, all `allOf` merged, every union explicitly discriminated-or-not,
every field's cardinality decided (3-valued, below), pagination/streaming/auth expressed
as *intents*, resources nested into a tree. The emitter is a near-mechanical renderer of
an already-correct model.

- ✅ The moat lives in `ir.builder`, testable without emitting a line of code.
- ✅ Emitter is thin and per-language; v3 reuses the IR untouched.
- ✅ Hard problems (allOf, oneOf, nullable≠optional) solved once, centrally.
- ❌ More upfront design — which is this document.

**Decision: B.** It is the only choice consistent with "build deep modules" and with the
multi-language end-state vision while keeping v1 scope to Python.

---

## 3. The IR type system (the hard part — get this right or nothing else matters)

OpenAPI conflates three distinct ideas into `required` + `nullable`. Mechanical
generators collapse them and lose compile-time safety exactly where APIs are complex
(RESEARCH §4 #8). stainful's IR makes cardinality **3-valued and explicit**:

| IR concept | Meaning | OpenAPI source | Python rendering |
|---|---|---|---|
| **required** | key always present, non-null | in `required`, not `nullable` | `x: T` |
| **optional** | key may be absent | not in `required` | `x: T \| NotGiven = not_given` |
| **nullable** | key present, value may be `null` | `nullable: true` / `null` in `type` | `x: T \| None` |

optional and nullable are orthogonal and co-occur as `x: T | None | NotGiven = not_given`.
This single distinction is the highest-leverage correctness decision in the project.

**Verified against `openai-python` main (the golden fixture), do not drift:** the
omission sentinel is class `NotGiven`, singleton **`not_given`** (primary), with
`NOT_GIVEN` kept as a back-compat alias — emit both. `Omit`/`omit` is a *separate*
sentinel for header/param *removal* (`Headers = Mapping[str, str | Omit]`), NOT the
optional-arg sentinel. Earlier drafts conflated them; they are distinct.

### Type ADT (`ir/types.py`, plain dataclasses — zero runtime deps in the IR)

```
Type =
  | PrimitiveType(kind: str, format: str|None)      # string,integer,number,boolean,
  |                                                 #   bytes,date,datetime,decimal,uuid
  | NullType
  | AnyType                                         # genuinely unconstrained
  | EnumType(name, base: PrimitiveType, members: [EnumMember])
  | ArrayType(item: Type)
  | MapType(value: Type)                            # additionalProperties
  | ObjectType(properties: [Property], extra: Type|None)
  | UnionType(variants: [Type],
  |           discriminator: Discriminator|None)    # oneOf/anyOf; tagged when possible
  | ModelRef(name: str)                             # → a named Model (codegen reuse)

Property  = (name, type: Type, required: bool, nullable: bool, docs, deprecated, default)
Discriminator = (property_name: str, mapping: {tag: ModelRef})
Model     = (name, type: Type, docs)               # becomes a pydantic class / alias
```

Resolution rules enforced in the builder (not the emitter):

- `allOf` → deep-merged single `ObjectType` (OneBusAway's `ResponseWrapper + {data}` is
  the canonical fixture for this).
- `oneOf`/`anyOf` + `discriminator` → `UnionType` with `Discriminator` → emits a
  Pydantic discriminated union (real tagged union, RESEARCH §4 #8).
- `oneOf`/`anyOf` without discriminator → `UnionType` w/ structural fallback (`Union[...]`).
- `nullable`/`type: [..., "null"]` sets `Property.nullable`, never folded into optional.
- **Promotion rule (precise):** a schema becomes a `Model` **iff it is referenced by
  `$ref` under `components`**. Inline schemas stay inline. No structural-equality
  dedup in v1 (that swamp is out of scope; `config.models.deduplicate` is deferred).
  Matches how `openai-python` reads.
- **Cycle safety:** `ModelRef` is the cycle-breaker. The builder maintains a visiting-set
  during `allOf` merge and inline traversal; on revisit it emits a `ModelRef` instead of
  recursing. Recursive schemas are therefore representable, not a crash.
- **Optional sentinel:** `NotGiven` / `not_given` (+ `NOT_GIVEN` alias) — see the
  verified note in §3. Drop-in users must not see a different sentinel name than their
  Stainless-generated SDK used; this is a *symbol-level* compatibility contract.

---

## 4. The IR API model (`ir/model.py`)

```
API
 ├─ name, version
 ├─ environments: {name: base_url}            # client(env="production")
 ├─ auth: [SecurityScheme]                    # apiKey/http-bearer/basic, env-var + placement
 ├─ models: {name: Model}                     # the shared type universe
 └─ root: Resource                            # config `$client:` maps here (client-level
        ├─ name, docs                         #   methods live on API.root, no parent)
        ├─ subresources: [Resource]           # nested → client.accounts.friends.list()
        └─ methods: [Method]
              ├─ name                          # idiomatic verb from config (list/create/…)
              ├─ http_verb, path
              ├─ path_params, query_params, header_params: [Property]
              ├─ body: BodyShape|None          # see below — content-type aware
              ├─ responses: {status: Type}      # "200","2XX","4XX","default" → per-status
              ├─ unwrap: str|None               # config unwrap_response (e.g. "data")
              ├─ pagination: PaginationIntent|None
              ├─ streaming: StreamingIntent|None
              ├─ idempotent: bool
              ├─ emit_hints: dict               # explicit escape hatch: positional_params,
              │                                 #   body_param_name, skip_test_reason,
              │                                 #   per-language skip — emitter-only, not
              │                                 #   semantic intent
              └─ docs, deprecated

BodyShape = (content_type, type: Type, required: bool)
            # content_type ∈ application/json | multipart/form-data
            #              | application/x-www-form-urlencoded | binary
            # multipart carries the file-upload case (RESEARCH §4 #10)
```

**Why `responses` is a map, not one type:** the typed error hierarchy (RESEARCH §4 #4 —
`RateLimitError`/`BadRequestError` carrying *parsed* bodies) is impossible without
per-status response types. `2XX` → return type; `4XX`/`5XX`/`default` → typed exception
bodies wired to the runtime's error classes. Skipping this now would block slice 4.

**`unwrap`:** OneBusAway wraps every payload in `ResponseWrapper{data}` and the Stainless
config sets `unwrap_response: data`. The emitter returns the unwrapped inner type while
the runtime still parses the envelope. Without `Method.unwrap`, output diverges from
Stainless on the *canonical fixture* — i.e. drop-in compat fails on example #1.

`PaginationIntent` = (style ∈ {cursor, cursor_id, offset, page_number}, request param
names, response data path, next-token path, terminal rule). The emitter turns this into
an auto-paginating iterator (RESEARCH §4 #1) — it does **not** re-infer pagination.

`StreamingIntent` = (transport ∈ {sse, jsonl}, event Type, discriminator) → typed event
iterator, sync+async identical (RESEARCH §4 #6).

The config overlay is what populates idiomatic `name`s, the resource *tree shape*, and
the intents — turning OpenAPI's flat operation list into a domain-shaped client. This is
precisely the value Stainless's proprietary engine adds; here it is the open `ir.builder`.

---

## 5. Tech stack (decided, with rationale — no fallbacks)

| Concern | Choice | Why |
|---|---|---|
| Generator IR | **plain dataclasses** | zero deps, trivially testable, fast |
| YAML/JSON load | **PyYAML + json (stdlib)** | clean-room control over `$ref` resolution; no opinionated OpenAPI lib imposing its model |
| `$ref`/allOf resolution | **our own resolver** | the moat needs full control; cycle-safe |
| Config validation | **dataclasses + explicit checks** | precise, quotable error messages > hidden exceptions |
| Emitter | **Jinja2 for files + Python type-renderer** | files are templatable; nested type rendering is real logic, kept in Python |
| Generated SDK HTTP | **httpx** (sync + async) | one lib, both clients, identical surface — the proven `openai-python` stack |
| Generated SDK models | **pydantic v2** | typed models, discriminated unions, validation — same choice the §4 quality bar SDKs make |
| CLI | **argparse (stdlib) → `stainful generate`** | one entry point, no dep |
| Packaging / dev | **uv + pyproject.toml**, ruff, pytest | matches user CLAUDE.md standard tooling |

The **runtime** package (retries w/ backoff+jitter, idempotency keys, pagination base
classes, SSE parser, typed error hierarchy, auth/env-var injection) is **hand-written
once and vendored** into every generated SDK. Generated code is thin glue over it. This
is the deliberate inversion: idiomatic quality lives in human-written runtime, not in
templates. It is how the §4 13-capability bar is met without per-endpoint template hacks.

**Vendoring layout (decided):** the emitter copies `src/stainful/runtime/` verbatim
into `<out>/<package>/_core/` and generated modules import from `<package>._core`. The
generated `pyproject.toml` declares only external deps `httpx + pydantic` (the
`generated-runtime` extra in our own pyproject mirrors this). Pattern cloned from
`openai-python`, which vendors `_base_client.py` etc. in-package. The runtime is
**brand-agnostic**: the catchable symbols (`APIError`, `RateLimitError`, …) are generic
and identical across SDKs (that *is* the drop-in contract); only the client class names
(`Onebusaway`/`AsyncOnebusaway`) and an optional `<Brand>Error = APIError` alias are
emitter-generated.

### 5a. Verified symbol-compatibility contract (`openai-python` main, 2026-05-19)

Drop-in compatibility is a **symbol-level** contract — a user swapping the package
name on an `openai-python` import must still compile. Locked, do not drift:

- **Sentinels:** `NotGiven`/`not_given`(+`NOT_GIVEN`); `Omit`/`omit`; `Omittable[_T]`.
- **Exceptions:** `APIError(Exception base)` → `APIStatusError`(+`response,status_code,
  request_id`) → `BadRequestError`400 `AuthenticationError`401 `PermissionDeniedError`403
  `NotFoundError`404 `ConflictError`409 `UnprocessableEntityError`422 `RateLimitError`429
  `InternalServerError`5xx; siblings `APIConnectionError`,`APITimeoutError`,
  `APIResponseValidationError`. (OAuth/webhook/websocket/finish-reason = OpenAI-domain,
  excluded.)
- **Pagination:** base `SyncPage`/`AsyncPage` (`data`,`object`,`_get_page_items`,
  `next_page_info`); `SyncCursorPage`/`AsyncCursorPage` (+`has_more`,`has_next_page`,
  `next_page_info`→`PageInfo`).
- **Resource shape:** `<R>(SyncAPIResource)`/`Async<R>(AsyncAPIResource)` +
  `<R>WithRawResponse`/`<R>WithStreamingResponse` (and async). Method sig tail:
  `*, extra_headers: Headers|None=None, extra_query: Query|None=None,
  extra_body: Body|None=None, timeout: float|httpx.Timeout|None|NotGiven=not_given`.
  Calls `self._get/_post/_delete/_get_api_list(..., options=make_request_options(...),
  cast_to=...)`. `with_raw_response`/`with_streaming_response`/`with_options` present.

### 5b. Slice 4 cutline (explicit — defer the rest to v1.1)

**In slice 4:** sync+async base client; retries (backoff+jitter, `Retry-After`,
idempotency keys); the full typed error hierarchy above incl. `request_id`; base
pagination (cursor + offset/page); SSE parser; auth/env-var injection; `NotGiven`/`Omit`;
`with_options`/`with_raw_response`/`with_streaming_response`. **Deferred to v1.1:**
long-running-operation pollers, multipart/file uploads, webhook unwrap (OneBusAway
exercises none; see §7).

---

## 6. Build order (vertical slices, subtraction over addition)

1. **Config loader** — parse full `stainless.yml`; conformance: OneBusAway parses clean.
2. **OpenAPI loader + resolver** — parse 3.x, deref `$ref`, merge `allOf` (OneBusAway).
3. **IR builder** — spec + config → `API`; unit-tested on the IR alone, no emission.
4. **Runtime library** — hand-written Python base (the quality bar).
5. **Python emitter** — render `API` → SDK over the runtime.
6. **End-to-end** — generated OneBusAway SDK imports, type-checks, makes a real call.
   **Gated on a second fixture:** OneBusAway has no streaming, discriminated unions,
   typed error bodies, uploads, or signal-bearing `nullable`. "Green on OneBusAway" is
   necessary, not sufficient, for the §4 claim. Before slice 6 declares victory, add a
   curated slice of `openai/openai-openapi` (streaming + `oneOf` discriminator + typed
   errors) so the proof isn't partial.

Each slice is independently testable and shippable. We do not start slice N+1 until N is
green. The OneBusAway repo (config + spec + their Stainless-generated SDKs) is the
ground-truth oracle at every step: our output should be *recognizably the same shape* as
what Stainless produced for them.

**Stack note:** config/spec loaders use `ruamel.yaml` (carries source line/column) so
diagnostics can quote exact positions — cashing in the CLAUDE.md principle "precise,
quotable errors > hidden exceptions". `safe_load` semantics, position-aware.

---

## 6a. Slice-6 fidelity vs the REAL Stainless OneBusAway SDK (2026-05-19)

Verified our output against the actual Stainless-generated `OneBusAway/python-sdk`:

| Surface | Real Stainless | stainful | Match |
|---|---|---|---|
| Client class | `OnebusawaySDK` / `AsyncOnebusawaySDK` | same | ✓ (after `brand()` initialism fix) |
| Package | `onebusaway` | `onebusaway` | ✓ |
| API-key env | `ONEBUSAWAY_API_KEY` | same | ✓ |
| Call shape | `client.current_time.retrieve()` | same | ✓ |
| Async parity | `AsyncOnebusawaySDK` | same | ✓ |
| Response models | pydantic + `.to_json()/.to_dict()` | pydantic (helpers → v1.1) | ~ |

The drop-in symbol contract holds: `from onebusaway import OnebusawaySDK` compiles
against stainful's output exactly as against Stainless's. Proven on two fixtures
(OneBusAway: REST/allOf/recursion; chat: streaming/discriminated-union/body).

## 7. Explicitly out of v1 scope (named so they don't pull on the design)

README generation · generated test suites · custom-code injection blocks · multi-edition
schema migration · `unspecified_endpoints` handling · `models.deduplicate` /
structural-equality dedup · Terraform/CLI/SQL targets · second language · docs site ·
MCP server. The IR has slots (`emit_hints`, deferred config keys parsed-but-ignored) so
adding these later is additive, never a redesign. v1 ships **one excellent Python SDK**.

**v1.1 polish backlog (discovered during slices 4–6, working but not yet matched):**
`BaseModel.to_json()/.to_dict()` Stainless helper aliases · rich `APIResponse`
object behind `with_raw_response` (currently signature-compatible passthrough) ·
per-file model modules (v1 emits one `types/models.py`) · model field
forward-referencing a discriminated-union alias by name (aliases emitted after
classes; rare) · typed error-body models on exceptions (runtime already attaches
parsed `.body` + the typed class) · `brand()` initialism list is heuristic
(`sdk/api/id/url/...`) — Stainless uses `custom_casings` config.
