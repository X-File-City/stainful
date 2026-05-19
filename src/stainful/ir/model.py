"""The IR API model (DESIGN.md §4) — language-agnostic semantic model.

Built by ir.builder from (OpenAPI spec + Stainless config). Consumed read-only by
emitters. This is the single contract between spec-understanding and code-generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from stainful.ir.types import Model, Property, Type


class HTTPVerb(str, Enum):
    GET = "get"
    POST = "post"
    PUT = "put"
    PATCH = "patch"
    DELETE = "delete"


class PaginationStyle(str, Enum):
    CURSOR = "cursor"
    CURSOR_ID = "cursor_id"
    OFFSET = "offset"
    PAGE_NUMBER = "page_number"


class StreamingTransport(str, Enum):
    SSE = "sse"
    JSONL = "jsonl"


class ContentType(str, Enum):
    JSON = "application/json"
    MULTIPART = "multipart/form-data"
    FORM = "application/x-www-form-urlencoded"
    BINARY = "binary"


@dataclass(frozen=True)
class SecurityScheme:
    name: str
    # apiKey | http-bearer | http-basic
    kind: str
    # where the credential goes: header | query
    location: str | None = None
    param_name: str | None = None
    read_env: str | None = None


@dataclass(frozen=True)
class PaginationIntent:
    style: PaginationStyle
    # request-side param names and response-side data/next paths.
    request_params: dict[str, str] = field(default_factory=dict)
    data_path: str = "data"
    next_path: str | None = None
    continue_on_empty_items: bool = False


@dataclass(frozen=True)
class StreamingIntent:
    transport: StreamingTransport
    event_type: Type
    discriminator: str | None = None


@dataclass(frozen=True)
class BodyShape:
    content_type: ContentType
    type: Type
    required: bool = True


@dataclass(frozen=True)
class Method:
    name: str                       # idiomatic verb from config (list/create/retrieve…)
    http_verb: HTTPVerb
    path: str
    path_params: tuple[Property, ...] = ()
    query_params: tuple[Property, ...] = ()
    header_params: tuple[Property, ...] = ()
    body: BodyShape | None = None
    # per-status response types: "200","2XX","4XX","default" -> Type.
    # Multi-valued so the typed error hierarchy can be generated (RESEARCH §4 #4).
    responses: dict[str, Type] = field(default_factory=dict)
    unwrap: str | None = None       # config unwrap_response (e.g. "data")
    pagination: PaginationIntent | None = None
    streaming: StreamingIntent | None = None
    idempotent: bool = False
    # explicit escape hatch for emitter-only, non-semantic config hints:
    # positional_params, body_param_name, skip_test_reason, per-language skip.
    emit_hints: dict = field(default_factory=dict)
    docs: str | None = None
    deprecated: bool = False


@dataclass
class Resource:
    name: str
    docs: str | None = None
    methods: list[Method] = field(default_factory=list)
    subresources: list["Resource"] = field(default_factory=list)


@dataclass
class API:
    name: str
    version: str
    environments: dict[str, str] = field(default_factory=dict)
    auth: list[SecurityScheme] = field(default_factory=list)
    models: dict[str, Model] = field(default_factory=dict)
    # config `$client:` methods live on root (no parent resource).
    root: Resource = field(default_factory=lambda: Resource(name="$client"))
