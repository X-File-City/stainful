"""$ref resolution + allOf deep-merge (DESIGN §3, §6 slice 2).

Two narrow, pure functions. Both are cycle-safe by *not* deep-recursing into
properties — that recursion (and its cycles) belongs to the IR builder, which
breaks cycles with `ModelRef` (DESIGN §3). Here we only:

  * `resolve_ref`  — one hop of an internal JSON pointer, reporting whether the
                     target is a named component schema (the Model boundary);
  * `flatten_allof` — collapse an `allOf` node into one object schema, the single
                     place an anonymous merged shape is genuinely needed (the
                     `ResponseWrapper + {data}` envelope).

No silent fallbacks: external refs and pathological `allOf` cycles raise SpecError.
"""

from __future__ import annotations

from dataclasses import dataclass

from stainful.errors import SourceLoc, SpecError
from stainful.openapi.loader import OpenAPIDocument

_SCHEMA_PREFIX = "#/components/schemas/"


@dataclass
class Ref:
    """Result of one ref hop."""

    # component schema name if this ref points at #/components/schemas/<name>,
    # else None. This is what lets the builder emit a ModelRef vs. inline.
    schema_name: str | None
    target: dict


def _json_pointer(doc: OpenAPIDocument, ref: str) -> dict:
    if not ref.startswith("#/"):
        raise SpecError(
            f"unsupported $ref {ref!r}: external/file refs are out of stainful v1 "
            f"scope (bundle the spec first)",
            SourceLoc(doc.source),
        )
    node: object = doc.raw
    for token in ref[2:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if not isinstance(node, dict) or token not in node:
            raise SpecError(f"$ref {ref!r} does not resolve", SourceLoc(doc.source))
        node = node[token]
    if not isinstance(node, dict):
        raise SpecError(
            f"$ref {ref!r} must point at a mapping", SourceLoc(doc.source)
        )
    return node


def resolve_ref(doc: OpenAPIDocument, ref: str) -> Ref:
    """Resolve a single internal `$ref` hop. Does not recurse further."""
    target = _json_pointer(doc, ref)
    name = ref[len(_SCHEMA_PREFIX):] if ref.startswith(_SCHEMA_PREFIX) else None
    return Ref(schema_name=name, target=target)


def _merge_object(into: dict, src: dict, doc: OpenAPIDocument) -> None:
    if src.get("type", "object") != "object":
        raise SpecError(
            f"allOf member is non-object (type={src.get('type')!r}); stainful v1 "
            f"only merges object schemas",
            SourceLoc(doc.source),
        )
    props = into.setdefault("properties", {})
    for k, v in (src.get("properties", {}) or {}).items():
        if k in props and props[k] != v:
            # last-wins, but surface it — silent clobbering hides real conflicts.
            raise SpecError(
                f"allOf property conflict on {k!r}: incompatible definitions",
                SourceLoc(doc.source),
            )
        props[k] = v
    req = dict.fromkeys(into.get("required", []))
    req.update(dict.fromkeys(src.get("required", []) or []))
    into["required"] = list(req)
    if "additionalProperties" in src:
        into.setdefault("additionalProperties", src["additionalProperties"])


def flatten_allof(
    doc: OpenAPIDocument, schema: dict, _seen: frozenset[str] = frozenset()
) -> dict:
    """Return `schema` with a top-level `allOf` collapsed into one object schema.

    Schemas without `allOf` are returned unchanged (we do NOT walk properties —
    that is the builder's job, where ModelRef breaks cycles). Recurses only
    through allOf-of-allOf, guarded by ref-name cycle detection.
    """
    if "allOf" not in schema:
        return schema

    merged: dict = {"type": "object", "properties": {}, "required": []}
    # carry through sibling keywords (description, title, …) that coexist w/ allOf
    for k, v in schema.items():
        if k != "allOf":
            merged.setdefault(k, v)

    for member in schema["allOf"]:
        m = member
        if "$ref" in m:
            ref = m["$ref"]
            name = (
                ref[len(_SCHEMA_PREFIX):]
                if ref.startswith(_SCHEMA_PREFIX)
                else ref
            )
            if name in _seen:
                raise SpecError(
                    f"allOf cycle through {ref!r}: not representable",
                    SourceLoc(doc.source),
                )
            m = resolve_ref(doc, ref).target
            m = flatten_allof(doc, m, _seen | {name})
        elif "allOf" in m:
            m = flatten_allof(doc, m, _seen)
        _merge_object(merged, m, doc)

    if not merged["required"]:
        del merged["required"]
    return merged
