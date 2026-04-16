from __future__ import annotations

from collections.abc import Sequence


class DummyResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return self

    def all(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        if self.value is None:
            raise RuntimeError("No scalar value available")
        return self.value


class FakeSession:
    def __init__(self, execute_results: Sequence[DummyResult] | None = None):
        self._results = list(execute_results or [])
        self.added = []
        self.commits = 0
        self.refreshed = []

    async def execute(self, _query):
        if self._results:
            return self._results.pop(0)
        return DummyResult(None)

    def add(self, obj):
        self.added.append(obj)

    async def commit(self):
        self.commits += 1

    async def refresh(self, obj):
        self.refreshed.append(obj)
