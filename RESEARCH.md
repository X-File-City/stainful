# Stainful — Research & Strategy Brief

> Goal: build an open-source alternative to [Stainless](https://www.stainless.com/).
> This document is decision-oriented. It leads with the choices you need to make,
> then gives the evidence behind each. Date: 2026-05-19.

---

## 0. TL;DR — read this first

- **The thing Stainless sells is not "OpenAPI → code." That's free** (OpenAPI Generator, 20k★).
  Stainless sells the *quality gap*: SDKs that read like a principal engineer hand-wrote
  them — auto-pagination, typed errors, retries, streaming, discriminated unions, nested
  resources. That gap is concrete and finite (~13 capabilities, §4).
- **Almost nothing of Stainless's core is open source.** Their GitHub org publishes the
  CLI, a GitHub Action, REST API clients, and an MCP auth proxy. **The generator engine
  is proprietary and hosted.** (§3)
- **This is a $25M Series-A, multi-year engineering output.** A solo/small effort cannot
  clone it. "Open-source Stainless" is not a realistic v1. **A wedge is.** (§1, §2)
- **Fern already occupies "open-core idiomatic SDK generator with an IR."** The first
  strategic question is not *how* but *why stainful instead of contributing to Fern*. (§5)
- Recommended honest framing: pick **one language**, **one killer differentiator**, and
  **one positioning angle** (strong candidate: *agent-native / MCP-first, fully OSS, no
  commercial layer*). Decisions are at the end of this doc.

---

## 1. The decisions you need to make (before any code)

You are a PM — you're right about *what you want*; the *how* is where the traps are.
These four branches determine everything downstream. I'll ask them interactively after
you've read the evidence.

1. **Wedge language.** Stainless ships 9+ targets. You should ship **one, excellently**.
   TypeScript (largest demand, but hey-api owns it) vs Python (AI/LLM clients, high
   value, slightly less crowded) vs Go (underserved, smaller market).
2. **Killer differentiator.** You can't beat Stainless on breadth. You win on *one*
   axis: fully-OSS-no-SaaS, or agent/MCP-first, or local-first/zero-lock-in, or
   spec-quality (best `oneOf`/streaming handling), or "Fern but X."
3. **Clean-room vs build-on-Fern.** Fern is open-core with an IR. Forking/extending it
   is faster but inherits its model; clean-room gives control but is 10x the work.
4. **Scope of v1.** SDK only? Or SDK + MCP server? Or SDK + docs? Each added surface
   multiplies effort. Subtraction beats addition (your own principle).

---

## 2. Honest scope reality (the part I won't soften)

Stainless raised **$25M Series A** ([Crunchbase](https://www.crunchbase.com/organization/stainless-3609)).
The generated-SDK quality bar (§4) is the cumulative output of a funded team over years,
per language. Matching "Stainless across 9 languages" is not a realistic open-source v1
and pretending otherwise wastes your time.

What *is* realistic and valuable:

- **One language, one IR, the ~13 quality capabilities done right.** That alone beats
  free OpenAPI Generator and is genuinely useful to thousands of API teams.
- The moat is **not** secret algorithms. It is: (a) a richer **intermediate
  representation** than raw OpenAPI, (b) a **hand-tuned per-language runtime + emitter**,
  (c) **regeneration-as-CI**. All three are buildable in the open. The bar is high but
  *well-defined*, not mysterious.

Subtraction principle applies hard here: every extra language/surface is a multiplier on
a project that lives or dies by depth in one.

---

## 3. What's actually open vs. closed at Stainless

Inventory of [`github.com/stainless-api`](https://github.com/stainless-api) (live, 2026-05-19):

| Repo | Lang | ★ | License | Role | Is it the generator? |
|---|---|---|---|---|---|
| `stl-api` | TS | 166 | none | Full-stack TS API framework (separate product) | No |
| `mcp-front` | Go | 48 | Other | Auth proxy for MCP servers | No |
| `upload-openapi-spec-action` | TS | 40 | none | GitHub Action: upload spec → trigger hosted build | No (orchestration) |
| `stainless-api-cli` | Go | 22 | Apache-2.0 | CLI client to the hosted service | No (thin client) |
| `stainless-api-go` / `-typescript` | Go/TS | 7/6 | Apache-2.0 | REST API client libs for their platform | No |
| `homebrew-tap` | Ruby | 0 | none | CLI distribution | No |
| `mcp-evals-harness`, `rerereric`, misc | — | low | mixed | Support tooling | No |

**Conclusion: the codegen engine (spec + config → idiomatic multi-language SDK) is
proprietary and hosted. It is not in any public repo.** What *is* public and useful to
you as reference material:

- **The config schema** (fully documented — §6). This is the overlay format that turns
  a flat spec into nested idiomatic resources. Reverse-engineerable.
- **Hundreds of generated SDKs** (OpenAI, Anthropic, etc.) — *golden output examples*.
  `openai-python` README literally states: *"It is generated from our OpenAPI
  specification with Stainless."* These are your quality target, free to study.
- **The CLI + Action** — show the integration contract (spec in repo + `stainless.yml` →
  regenerated SDK PR'd back).

---

## 4. The quality gap that justifies the entire category

Why companies pay $99–$500 / SDK / month instead of using free OpenAPI Generator
([pricing](https://www.stainless.com/pricing/)): OpenAPI Generator emits an **HTTP
transport layer**; Stainless emits an **SDK**. Concretely, verified against the live
`openai-python` SDK:

| # | Capability | Mechanical generator | Stainless-quality (cited from `openai-python`) |
|---|---|---|---|
| 1 | **Pagination** | returns raw page + cursor | `for job in client.fine_tuning.jobs.list(): …` auto-fetches pages; `.has_next_page()/.get_next_page()` for manual control |
| 2 | **Retries** | none | default 2 retries on conn err/408/409/429/≥500, backoff, per-request `.with_options()` |
| 3 | **Timeouts** | static or none | default 10 min, override per client/request |
| 4 | **Errors** | one generic exception + int status | typed hierarchy: `APIError → APIStatusError → RateLimitError`… with parsed body |
| 5 | **Request IDs** | not surfaced | `resp._request_id`, `exc.request_id` from `x-request-id` |
| 6 | **Streaming** | byte stream, parse SSE yourself | `stream=True` → typed event iterator, sync+async identical |
| 7 | **Async parity** | inconsistent | `OpenAI` / `AsyncOpenAI`, identical surface, pluggable HTTP backend |
| 8 | **Unions/discriminators** | degrade to `Any`/`object` | real tagged unions, narrow types — biggest correctness win |
| 9 | **Nested resources** | flat `DefaultApi.usersUserIdGet()` | `client.fine_tuning.jobs.list()` — domain-shaped |
| 10 | **Auth** | static header | env-var convention (`OPENAI_API_KEY`), never logs secrets |
| 11 | **Idempotency** | none | auto idempotency key, safe POST retries |
| 12 | **Long-running ops** | hand-rolled poll loop | `create_and_poll` / `wait_until_done` helpers |
| 13 | **Bundle/runtime** | heavy deps, no tree-shake | minimal deps, edge-compatible (TS) |

**This 13-row table is your product spec.** Closing it in one language = a useful OSS
tool. None of it requires proprietary magic; all of it requires taste + a real IR.

---

## 5. Competitive map — Fern is the one to study

| Tool | OSS? | License | Languages | Tier | Note for you |
|---|---|---|---|---|---|
| **Stainless** | ✗ | proprietary | 9+ | best-in-class | the target |
| **Fern** | **partial** | Apache/MIT + SaaS | TS,Py,Java,Go,C#,Ruby,PHP,Swift | Tier 2 | **closest sibling — open IR + generators. Study/possibly build on.** |
| Speakeasy | core ✗ | proprietary | 9 + Terraform | Tier 2 (top) | strong CI story; reference for DX |
| liblab | ✗ | proprietary | 7 | Tier 2 | thinner moat |
| APIMatic | ✗ | proprietary | 7 | Tier 2 (enterprise) | enterprise/transformation niche |
| **OpenAPI Generator** | ✓ | Apache-2.0 | 50+ | **Tier 1 (mechanical)** | the quality baseline to *beat* |
| swagger-codegen | ✓ | Apache-2.0 | broad | Tier 1 | legacy, lost to OpenAPI Gen |
| Microsoft Kiota | ✓ | MIT | 7 | Tier 1.5 (fluent, consistent) | good cross-lang consistency model |
| **hey-api** | ✓ | MIT | **TS only** | Tier 2 (within TS) | **owns the TS OSS niche — avoid head-on or differentiate hard** |

**Strategic implication:** the open niches are (a) **agent/MCP-first generation**,
(b) **one language done better than Fern**, (c) **fully-OSS with zero commercial layer**
(Fern monetizes hosted docs; Stainless/Speakeasy gate the engine). "stainful = the
no-SaaS, agent-native one" is a defensible wedge that nobody fully owns.

---

## 6. Appendix A — Stainless config schema (the overlay model)

This is the single most important technical artifact. Raw OpenAPI produces ugly SDKs;
the **config is a curated overlay** that injects idiomatic structure the spec lacks.
Top-level keys ([reference](https://www.stainless.com/docs/reference/config/)):

`edition` · `organization` · `settings` · `targets` (per-language pkg/publish) ·
`resources` (nested methods/models/subresources) · `environments` ·
`client_settings` (auth/retries/idempotency) · `pagination` · `query_settings` ·
`multipart_settings` · `security` / `security_schemes` · `readme` · `streaming` ·
`custom_casings` · `constants` · `diagnostics` · `unspecified_endpoints` · `codeflow` ·
`openapi`.

Core mapping pattern — flat OpenAPI ops → nested resources:

```yaml
resources:
  accounts:
    models: { account: "#/components/schemas/Account" }
    methods:
      list: get /accounts          # → client.accounts.list()
      create: post /accounts       # → client.accounts.create()
      retrieve: get /accounts/{id} # → client.accounts.retrieve(id)
    subresources:
      friends:
        methods:
          list: get /accounts/{id}/friends  # → client.accounts.friends.list()
pagination:
  - name: cursor_page
    type: cursor            # cursor | cursor_id | offset | page_number
    request:  { cursor: {type: string}, limit: {type: integer} }
    response: { data: {type: array}, next_cursor: {type: string, nullable: true} }
client_settings:
  idempotency: { header: "Idempotency-Key" }
  opts:
    api_key:
      type: string
      auth: { security_scheme: ApiKeyAuth, header: X-API-Key }
      read_env: MY_API_KEY
streaming: { type: sse, param_discriminator: stream }
```

## 7. Appendix B — real-world config (OneBusAway, abridged)

A live FOSS user's [`stainless-config.yml`](https://github.com/OneBusAway/sdk-config/blob/main/stainless-config.yml)
— note the `# yaml-language-server: $schema=…/config.schema.json` header (their schema
is public JSON Schema), flat resource list, per-target `production_repo` + `publish`,
and `client_settings.opts.api_key.send_as_query_param`. This is exactly the input format
stainful must accept to be a drop-in alternative for existing Stainless users.

## 8. Appendix C — proposed stainful architecture (one language)

```
OpenAPI 3.x spec ─┐
                  ├─► [1] Parser/normalizer ─► [2] IR builder ──► [3] Overlay merge
stainful.yml  ────┘     (deref $ref,           (rich typed       (config: rename,
(Stainless-compatible)   resolve unions)         API model)        nest, paginate)
                                                                        │
                                                                        ▼
                                                        [4] Language emitter (ONE lang)
                                                        + [5] runtime lib (retries,
                                                          pagination, streaming, errors)
                                                                        │
                                                                        ▼
                                                        [6] regenerate-as-CI (GH Action)
```

- **[2] IR is the moat.** Must be richer than OpenAPI: real discriminated unions,
  nullable≠optional≠absent, pagination intent, streaming intent, resource tree.
- **[1] + config compatibility** with `stainless.yml` = instant migration path for
  existing Stainless/FOSS users (huge adoption lever, low cost).
- **[5] runtime lib** is hand-written, not generated — this is where idiomatic quality
  actually lives (the 13 capabilities). Generated code is thin glue over it.
- Study `openai-python` / Anthropic SDKs as golden output; study **Fern's IR** as prior
  art before designing [2].

---

## 9. Decisions made (2026-05-19)

| Branch | Decision |
|---|---|
| Wedge language | **Python** (highest-value AI/LLM SDK demand, less OSS competition than TS) |
| Differentiator | **Fully-OSS, no SaaS + drop-in `stainless.yml` compatibility** (easy migration is the adoption lever) |
| Foundation | **Clean-room** (own IR; study Fern + `openai-python` as prior art only) |
| v1 scope | User said *"matches Stainless"* — see challenge below |

### Locked positioning — "the open-source Stainless"

> **stainful is *the open-source Stainless*.** Not "an OSS SDK generator" (Fern owns
> that product-space and is broader + funded). The asset is the **mind-space**: the
> phrase "the open-source Stainless" is unclaimed and *durably* unclaimed — Fern
> markets as a *peer competitor* to Stainless and structurally will never anchor its
> identity to a rival; Stainless can't (it's the closed original); nobody on X says
> it. This is the Supabase = "open-source Firebase" move: positions are claimed by
> repetition + credible proof, not by being first or most complete.

> **Product definition (the proof that earns the claim):** a fully-open-source,
> no-SaaS, no-upsell Python SDK generator that reads an existing `stainless.yml` +
> OpenAPI spec **unchanged** and emits an idiomatic Python SDK matching the §4 quality
> bar. A current Stainless user points stainful at their existing config and gets a
> recognizably-Stainless SDK with **zero migration**.

Two complementary halves, not alternatives:
- **Narrative = the GTM wedge.** "The open-source Stainless," said first/loudest, in
  the README hero, repo description, and launch. The name itself (`stain·less` →
  `stain·ful`) *is* the positioning — lean fully in.
- **`stainless.yml` drop-in compatibility = the evidence that defends it** against the
  "just a worse Fern" attack. It makes the claim literally true and unmockable, not
  aspirational. A hard constraint, not a nice-to-have. Appendix B (OneBusAway) is the
  conformance fixture and the output-fidelity oracle.

Honest condition: the claim only holds if shippable proof exists — vaporware claiming
"open-source Stainless" gets mocked on the same X that would amplify it. Hence: narrative
ships now as a first-class artifact; slices 2→6 are the proof that backs it.

### ⚠️ Challenge: "matches Stainless" as *v1 scope* is a scope trap

"Matches Stainless" is the right **end-state vision** (SDKs in many languages + docs +
MCP). It is the wrong **v1 scope** — and adopting it as v1 contradicts three of your own
standing principles: *subtraction over addition*, *never sacrifice the core for secondary
systems*, *avoid complexity when a simpler solution exists*.

Stainless's surface = {9 languages} × {SDK + docs + MCP}. A v1 that chases all of it
produces nothing excellent and dies. The honest path that *reaches* the "matches
Stainless" vision is **sequential depth, not parallel breadth**:

- **v1 — Python SDK only.** Nail the 13-capability quality bar + `stainless.yml`
  drop-in. This alone beats OpenAPI Generator and is genuinely useful. Ship it.
- **v2 — MCP server from the same IR.** Reuses v1's IR; matches agent-native angle.
- **v3 — second language** (TS or Go), proving the IR is language-agnostic.
- **v4+ — docs, more languages.** Only after the IR has earned it.

The IR (Appendix C, [2]) is designed from day one to be multi-language and
multi-surface, so v1 doesn't paint us into a corner — but we *build and ship* one slice
at a time. "Matches Stainless" is the destination; **v1 scope = Python SDK only.**
Recommend you confirm this framing before any code.

Next step is **not** scaffolding code — it's confirming the v1-scope framing above,
then designing the IR.
