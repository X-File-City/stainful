"""Auto-pagination base classes — symbol-compatible with openai-python (§5a).

RESEARCH §4 #1: `for item in client.things.list(): ...` transparently walks
pages. OneBusAway doesn't paginate, but Stainless-quality SDKs ship this, so
it is part of the runtime (DESIGN §5b cutline: cursor + offset/page).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, Optional, TypeVar

from ._models import BaseModel

_T = TypeVar("_T")

__all__ = [
    "PageInfo",
    "SyncPage",
    "AsyncPage",
    "SyncCursorPage",
    "AsyncCursorPage",
]


@dataclass
class PageInfo:
    """How to fetch the next page: either query params or an absolute url."""

    params: Optional[dict] = None
    url: Optional[str] = None


class BasePage(BaseModel, Generic[_T]):
    def _get_page_items(self) -> List[_T]:  # pragma: no cover - overridden
        raise NotImplementedError

    def has_next_page(self) -> bool:
        return self.next_page_info() is not None

    def next_page_info(self) -> Optional[PageInfo]:  # pragma: no cover - overridden
        return None


class SyncPage(BasePage[_T], Generic[_T]):
    """Single-shot list (`{"data": [...], "object": "list"}`) — one page."""

    data: List[_T]
    object: Optional[str] = None

    def _get_page_items(self) -> List[_T]:
        return self.data or []

    def next_page_info(self) -> Optional[PageInfo]:
        return None


class AsyncPage(SyncPage[_T], Generic[_T]):
    pass


class SyncCursorPage(BasePage[_T], Generic[_T]):
    """Cursor pagination keyed on `has_more` + the last item's id."""

    data: List[_T]
    has_more: Optional[bool] = None

    def _get_page_items(self) -> List[_T]:
        return self.data or []

    def next_page_info(self) -> Optional[PageInfo]:
        if self.has_more is False or not self.data:
            return None
        last = self.data[-1]
        cursor = getattr(last, "id", None)
        if cursor is None:
            return None
        return PageInfo(params={"after": cursor})


class AsyncCursorPage(SyncCursorPage[_T], Generic[_T]):
    pass
