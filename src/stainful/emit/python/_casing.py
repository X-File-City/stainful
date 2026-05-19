"""Naming transforms. Wire names (camelCase, kebab) -> idiomatic Python.

The emitter chooses snake_case symbols and carries the original wire name as a
pydantic `alias` (DESIGN §3 / golden target). PascalCase for classes.
"""

from __future__ import annotations

import re

_CAMEL_1 = re.compile(r"(.)([A-Z][a-z]+)")
_CAMEL_2 = re.compile(r"([a-z0-9])([A-Z])")
_NON_ALNUM = re.compile(r"[^0-9A-Za-z]+")


def snake(name: str) -> str:
    # Any separator/punctuation (`-`, `.`, space, `/`, …) collapses to `_`,
    # so arbitrary OpenAPI property names become valid identifiers.
    s = _NON_ALNUM.sub("_", name)
    s = _CAMEL_1.sub(r"\1_\2", s)
    s = _CAMEL_2.sub(r"\1_\2", s)
    return re.sub(r"_+", "_", s).strip("_").lower()


def pascal(name: str) -> str:
    parts = _NON_ALNUM.split(_CAMEL_2.sub(r"\1_\2", name))
    return "".join(p[:1].upper() + p[1:] for p in parts if p)


# Tokens Stainless renders ALL-CAPS in class names (verified: the real
# Stainless-generated OneBusAway SDK client class is `OnebusawaySDK`).
_INITIALISMS = {"sdk", "api", "id", "url", "http", "io", "ai", "sql", "cli"}


def brand(api_name: str) -> str:
    """`onebusaway-sdk` -> `OnebusawaySDK` (matches the real Stainless output).

    The client class name is a *symbol-level drop-in contract*: a user's
    `from onebusaway import OnebusawaySDK` must keep compiling. `sdk` is kept
    and upper-cased as an initialism, NOT stripped.
    """
    tokens = _NON_ALNUM.split(_CAMEL_2.sub(r"\1_\2", api_name))
    out = []
    for tok in tokens:
        if not tok:
            continue
        out.append(tok.upper() if tok.lower() in _INITIALISMS
                   else tok[:1].upper() + tok[1:])
    return "".join(out)


def package(api_name: str) -> str:
    """`onebusaway-sdk` -> `onebusaway` (importable package name).

    The package dir drops `-sdk` (the real published package is `onebusaway`),
    even though the *class* keeps `SDK`.
    """
    base = re.sub(r"[-_]sdk$", "", api_name, flags=re.IGNORECASE)
    return snake(base)
