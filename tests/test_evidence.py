import unittest

from postex.errors import EvidenceError
from postex.evidence import EvidenceRegistry
from postex.models import EvidenceRecord, PosterBlock, SourceLocator


class EvidenceTests(unittest.TestCase):
    def test_coverage_and_unknown_ids(self) -> None:
        record = EvidenceRecord(
            "ev-1",
            "claim-1",
            SourceLocator("paper-1", "page", page=3),
            "direct",
        )
        registry = EvidenceRegistry([record])
        blocks = [
            PosterBlock("b1", "result", "Effect was observed", ("ev-1",)),
            PosterBlock("b2", "heading", "Key finding", synthesis=True),
        ]
        registry.assert_covered(blocks)
        self.assertEqual(registry.coverage(blocks), 1.0)

        with self.assertRaises(EvidenceError):
            registry.assert_covered([PosterBlock("b3", "result", "Unsupported", ("missing",))])


if __name__ == "__main__":
    unittest.main()
