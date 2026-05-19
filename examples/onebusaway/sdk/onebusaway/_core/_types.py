"""Shared type aliases — symbol-compatible with openai-python (DESIGN §5a)."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ._sentinels import Omit, Omittable

# A header value may be explicitly removed with `omit`.
Headers = Mapping[str, Union[str, Omit]]
Query = Mapping[str, object]
Body = object

__all__ = ["Headers", "Query", "Body", "Omittable", "Any"]
