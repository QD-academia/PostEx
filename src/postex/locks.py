from __future__ import annotations

from dataclasses import dataclass

from postex.errors import LockViolation


@dataclass(frozen=True)
class DesignLock:
    target_id: str
    target_type: str
    value_digest: str
    actor: str


class LockRegistry:
    def __init__(self, locks: tuple[DesignLock, ...] = ()) -> None:
        self._locks = {lock.target_id: lock for lock in locks}

    def lock(self, lock: DesignLock) -> None:
        self._locks[lock.target_id] = lock

    def unlock(self, target_id: str) -> DesignLock:
        try:
            return self._locks.pop(target_id)
        except KeyError as exc:
            raise LockViolation(f"No lock exists for {target_id}") from exc

    def require_mutable(self, target_ids: tuple[str, ...]) -> None:
        blocked = sorted(target_id for target_id in target_ids if target_id in self._locks)
        if blocked:
            raise LockViolation("Mutation targets locked elements: " + ", ".join(blocked))

    def snapshot(self) -> tuple[DesignLock, ...]:
        return tuple(self._locks[key] for key in sorted(self._locks))
