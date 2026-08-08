import unittest

from postex.errors import ApprovalRequired
from postex.privacy import PrivacyGate


class PrivacyGateTests(unittest.TestCase):
    def test_payload_requires_approval_and_redacts_email(self) -> None:
        gate = PrivacyGate()
        content = {"abstract": "Contact lead@example.org for data"}
        gate.disclose("openai", "unpublished.pdf", content)
        with self.assertRaises(ApprovalRequired):
            gate.build_payload("openai", content)
        gate.approve("owner")
        payload = gate.build_payload("openai", content)
        self.assertIn("[redacted-email]", payload.content["abstract"])

    def test_changed_same_length_content_needs_new_disclosure(self) -> None:
        gate = PrivacyGate()
        gate.disclose("anthropic", "study.pdf", {"abstract": "AAAA"})
        gate.approve("owner")
        with self.assertRaisesRegex(ValueError, "Content changed"):
            gate.build_payload("anthropic", {"abstract": "BBBB"})


if __name__ == "__main__":
    unittest.main()
