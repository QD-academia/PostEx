import unittest

from postex.approvals import ApprovalGate
from postex.enums import ApprovalSubject
from postex.errors import ApprovalRequired


class ApprovalGateTests(unittest.TestCase):
    def test_changed_proposal_invalidates_approval(self) -> None:
        gate = ApprovalGate(ApprovalSubject.CONTENT_DELETION)
        first = gate.propose("v1", {"source_ids": ["s1"]})
        record = gate.decide(True, "researcher")
        self.assertEqual(first.digest, record.digest)
        gate.require_approved()

        gate.propose("v2", {"source_ids": ["s1", "s2"]})
        with self.assertRaises(ApprovalRequired):
            gate.require_approved()

    def test_rejection_never_unlocks_gate(self) -> None:
        gate = ApprovalGate(ApprovalSubject.PALETTE_APPLICATION)
        gate.propose("palette-v1", {"colors": ["#000000"]})
        gate.decide(False, "researcher")
        with self.assertRaises(ApprovalRequired):
            gate.require_approved()


if __name__ == "__main__":
    unittest.main()
