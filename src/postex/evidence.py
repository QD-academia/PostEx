from __future__ import annotations

from collections.abc import Iterable

from postex.errors import EvidenceError
from postex.models import EvidenceRecord, PosterBlock


class EvidenceRegistry:
    def __init__(self, records: Iterable[EvidenceRecord] = ()) -> None:
        self._records = {record.evidence_id: record for record in records}

    def add(self, record: EvidenceRecord) -> None:
        if record.evidence_id in self._records:
            raise EvidenceError(f"Duplicate evidence ID: {record.evidence_id}")
        self._records[record.evidence_id] = record

    def resolve(self, evidence_id: str) -> EvidenceRecord:
        try:
            return self._records[evidence_id]
        except KeyError as exc:
            raise EvidenceError(f"Unknown evidence ID: {evidence_id}") from exc

    def assert_covered(self, blocks: Iterable[PosterBlock]) -> None:
        problems: list[str] = []
        for block in blocks:
            if not block.evidence_ids and not block.synthesis:
                problems.append(f"{block.block_id}: no evidence")
            for evidence_id in block.evidence_ids:
                if evidence_id not in self._records:
                    problems.append(f"{block.block_id}: unknown {evidence_id}")
        if problems:
            raise EvidenceError("; ".join(problems))

    def coverage(self, blocks: Iterable[PosterBlock]) -> float:
        items = list(blocks)
        if not items:
            return 1.0
        covered = sum(bool(block.evidence_ids) or block.synthesis for block in items)
        return covered / len(items)
