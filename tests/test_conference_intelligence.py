import unittest
from pathlib import Path

from postex.conference import ConferenceRegistry, apply_conference_render_context
from postex.conference_preflight import ConferencePreflightValidator

ROOT = Path(__file__).resolve().parents[1]


class ConferenceRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry = ConferenceRegistry.from_repository(ROOT)
        cls.cvpr = cls.registry.load("cvpr-2026")
        cls.aacr = cls.registry.load("aacr-2026")
        cls.asco = cls.registry.load("asco-2026")
        cls.esmo = cls.registry.load("esmo-2026")
        cls.rsna = cls.registry.load("rsna-2026")
        cls.aha = cls.registry.load("aha-scientific-sessions-2026")
        cls.esc = cls.registry.load("esc-congress-2026")

    def test_registry_packs_validate_as_complete_units(self) -> None:
        packs = self.registry.validate_all()
        self.assertEqual(
            [item.pack_id for item in packs],
            [
                "cvpr-2026",
                "aacr-2026",
                "asco-2026",
                "esmo-2026",
                "rsna-2026",
                "aha-scientific-sessions-2026",
                "esc-congress-2026",
            ],
        )
        self.assertEqual(self.cvpr.edition["verification"]["state"], "verified")
        self.assertEqual(
            self.aacr.edition["verification"]["state"], "partially-verified"
        )
        self.assertIn("physical-poster.canvas", self.aacr.edition["verification"]["unverified_fields"])
        self.assertEqual(self.asco.edition["verification"]["state"], "verified")
        self.assertEqual(self.esc.edition["verification"]["state"], "verified")

    def test_partial_medical_packs_do_not_present_postex_canvas_as_official(self) -> None:
        for pack in (self.esmo, self.rsna, self.aha):
            presentation = pack.presentation()
            self.assertEqual(presentation["official_canvas"]["status"], "unspecified")
            self.assertTrue(pack.edition["verification"]["unverified_fields"])
            canvas_rules = [rule for rule in pack.rules if rule.path.startswith("canvas.")]
            self.assertTrue(canvas_rules)
            self.assertTrue(all(rule.origin == "postex" for rule in canvas_rules))

    def test_official_rules_are_source_bound_and_postex_rules_are_explicit(self) -> None:
        for pack in (self.cvpr, self.aacr):
            official = [rule for rule in pack.rules if rule.origin == "official"]
            recommendations = [rule for rule in pack.rules if rule.origin == "postex"]
            self.assertTrue(official)
            self.assertTrue(recommendations)
            self.assertTrue(all(rule.provenance_ref for rule in official))
            self.assertTrue(all(rule.level == "postex" for rule in recommendations))
            self.assertFalse(pack.conference["rights"]["logos_bundled"])
            self.assertFalse(pack.palette_set["rights"]["official_template_used"])

    def test_palette_dna_and_renderer_adapter_are_data_driven(self) -> None:
        context = self.cvpr.render_context(
            presentation_id="main-poster", palette_mode="balanced-fusion"
        )
        self.assertEqual(context.palette.palette_id, "cvpr-2026-balanced-fusion")
        self.assertEqual(context.canvas["width_in"], 84)
        render_spec = apply_conference_render_context(
            {"canvas": {}, "theme": {}, "content": {"title": "Example"}}, context
        )
        self.assertEqual(render_spec["canvas"]["width"], 84 * 96)
        self.assertEqual(render_spec["theme"]["primary"], "#123B5D")
        self.assertEqual(render_spec["content"], {"title": "Example"})
        self.assertEqual(render_spec["conference"]["pack_id"], "cvpr-2026")


class ConferencePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        registry = ConferenceRegistry.from_repository(ROOT)
        cls.cvpr = registry.load("cvpr-2026")
        cls.aacr = registry.load("aacr-2026")
        cls.asco = registry.load("asco-2026")
        cls.esc = registry.load("esc-congress-2026")
        cls.validator = ConferencePreflightValidator()

    def test_cvpr_snapshot_passes_all_official_and_postex_rules(self) -> None:
        report = self.validator.validate(
            self.cvpr,
            {
                "canvas": {"width_in": 84, "height_in": 42, "orientation": "landscape"},
                "export": {"format": "pdf", "effective_dpi": 150, "has_bleed": False},
                "layout": {"column_count": 4},
                "presentation": {"duration_minutes": 8},
                "typography": {"minimum_body_font_pt": 30},
            },
            presentation_id="main-poster",
        )
        self.assertTrue(report.passed)
        self.assertTrue(report.recommendations_satisfied)
        self.assertTrue(all(item.passed for item in report.findings))

    def test_required_cvpr_dimension_failure_blocks_compliance(self) -> None:
        report = self.validator.validate(
            self.cvpr,
            {
                "canvas": {"width_in": 48, "height_in": 36, "orientation": "landscape"},
                "export": {"format": "pdf", "effective_dpi": 150, "has_bleed": True},
                "layout": {"column_count": 4},
                "presentation": {"duration_minutes": 8},
                "typography": {"minimum_body_font_pt": 30},
            },
        )
        self.assertFalse(report.passed)
        failed = {item.code for item in report.findings if not item.passed}
        self.assertIn("conference.cvpr.canvas.width", failed)
        self.assertIn("conference.cvpr.export.bleed", failed)

    def test_wrong_artifact_fact_type_is_a_finding_not_a_validator_crash(self) -> None:
        report = self.validator.validate(
            self.cvpr,
            {
                "canvas": {"width_in": "eighty-four", "height_in": 42, "orientation": "landscape"},
                "export": {"format": "pdf", "effective_dpi": "vector", "has_bleed": False},
                "layout": {"column_count": 4},
                "presentation": {"duration_minutes": 8},
                "typography": {"minimum_body_font_pt": 30},
            },
        )
        self.assertFalse(report.passed)
        self.assertFalse(
            next(
                item
                for item in report.findings
                if item.code == "conference.cvpr.export.dpi"
            ).passed
        )

    def test_aacr_conditional_privacy_marker(self) -> None:
        artifact = {
            "submission": {"eposter_submitted": True},
            "canvas": {"width_in": 36, "height_in": 24},
            "export": {
                "format": "pdf",
                "file_size_mb": 12,
                "has_extraneous_margin": False,
            },
            "privacy": {"social_media_opt_out": False},
            "typography": {"minimum_body_font_pt": 26},
        }
        report = self.validator.validate(self.aacr, artifact)
        self.assertTrue(report.passed)
        self.assertTrue(report.recommendations_satisfied)

        artifact["privacy"] = {"social_media_opt_out": True}
        blocked = self.validator.validate(self.aacr, artifact)
        self.assertFalse(blocked.passed)
        marker = next(
            item
            for item in blocked.findings
            if item.code == "conference.aacr.privacy.do-not-post"
        )
        self.assertFalse(marker.passed)
        self.assertIsNone(marker.as_payload()["actual"])

    def test_asco_regular_poster_and_commercial_content_guard(self) -> None:
        artifact = {
            "canvas": {"width_in": 72, "height_in": 42, "orientation": "landscape"},
            "submission": {"eposter_submitted": True},
            "content": {
                "title": "Example trial",
                "abstract_number": "101",
                "contact_email": "presenter@example.org",
                "has_commercial_logo": False,
                "has_proprietary_drug_name": False,
            },
            "typography": {"minimum_body_font_pt": 30},
        }
        report = self.validator.validate(
            self.asco, artifact, presentation_id="regular-poster"
        )
        self.assertTrue(report.passed)
        self.assertTrue(report.recommendations_satisfied)

        artifact["content"]["has_commercial_logo"] = True
        blocked = self.validator.validate(
            self.asco, artifact, presentation_id="regular-poster"
        )
        self.assertFalse(blocked.passed)
        self.assertFalse(
            next(
                item
                for item in blocked.findings
                if item.code == "conference.asco.content.commercial-logo"
            ).passed
        )

    def test_esc_moderated_eposter_contract(self) -> None:
        artifact = {
            "canvas": {"orientation": "landscape", "aspect_ratio": 16 / 9},
            "export": {"format": "pdf", "page_count": 1, "effective_dpi": 240},
            "typography": {"minimum_body_font_pt": 20},
            "content": {
                "has_qr_code": False,
                "has_organizer_logo": False,
                "has_embedded_video": False,
            },
            "presentation": {"commentary_minutes": 3, "zoom_zone_count": 3},
        }
        report = self.validator.validate(self.esc, artifact)
        self.assertTrue(report.passed)
        self.assertTrue(report.recommendations_satisfied)

        artifact["content"]["has_qr_code"] = True
        blocked = self.validator.validate(self.esc, artifact)
        self.assertFalse(blocked.passed)
        self.assertIn(
            "conference.esc.content.qr-code",
            {item.code for item in blocked.findings if not item.passed},
        )


if __name__ == "__main__":
    unittest.main()
