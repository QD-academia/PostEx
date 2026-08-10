import hashlib
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from postex.approvals import canonical_digest
from postex.manifest import MANIFEST_FILENAME, output_hashes
from postex.provenance import (
    PROVENANCE_OBJECT_NAME,
    embed_png_metadata,
    provenance_metadata,
    resolve_provenance_policy,
    source_short_id,
)


class ProvenanceManifestTests(unittest.TestCase):
    def test_legacy_project_defaults_to_visual_mark(self) -> None:
        project = {"project_id": "legacy-v03"}
        policy = resolve_provenance_policy(project, "a" * 64, {"records": []})
        self.assertTrue(policy.enabled)
        self.assertRegex(policy.source_id, r"^PX-[A-F0-9]{8}$")
        self.assertEqual(
            policy.mark_text,
            f"Made with PostEx™ · {policy.source_id}",
        )
        self.assertEqual(policy.as_dict()["object_name"], PROVENANCE_OBJECT_NAME)

    def test_omission_requires_exact_digest_approval(self) -> None:
        project = {
            "project_id": "approved-omission",
            "provenance": {
                "enabled": False,
                "omission": {"proposal_id": "omit-1", "reason": "blind review"},
            },
        }
        source_hash = "b" * 64
        denied = resolve_provenance_policy(project, source_hash, {"records": []})
        self.assertFalse(denied.omission_approved)
        payload = {
            "project_id": project["project_id"],
            "source_id": source_short_id(project["project_id"], source_hash),
            "enabled": False,
            "reason": "blind review",
        }
        log = {
            "records": [
                {
                    "subject": "omit_provenance_mark",
                    "proposal_id": "omit-1",
                    "digest": canonical_digest(payload),
                    "decision": "approved",
                }
            ]
        }
        approved = resolve_provenance_policy(project, source_hash, log)
        self.assertTrue(approved.omission_approved)

    def test_png_metadata_does_not_change_pixels(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "poster.png"
            Image.new("RGB", (12, 8), "#123456").save(path)
            before = hashlib.sha256(Image.open(path).tobytes()).hexdigest()
            metadata = provenance_metadata(
                project_id="demo",
                source_id="PX-1234ABCD",
                enabled=True,
                manifest_name=MANIFEST_FILENAME,
            )
            embed_png_metadata(path, metadata)
            with Image.open(path) as image:
                after = hashlib.sha256(image.tobytes()).hexdigest()
                self.assertEqual(image.info["PostExSourceId"], "PX-1234ABCD")
            self.assertEqual(before, after)

    def test_manifest_hash_map_never_hashes_itself(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            poster = root / "poster.png"
            manifest = root / MANIFEST_FILENAME
            poster.write_bytes(b"poster")
            manifest.write_bytes(b"manifest")
            hashes = output_hashes({"png": poster, MANIFEST_FILENAME: manifest})
            self.assertEqual(set(hashes), {"png"})
            self.assertEqual(
                hashes["png"]["sha256"], hashlib.sha256(b"poster").hexdigest()
            )


if __name__ == "__main__":
    unittest.main()
