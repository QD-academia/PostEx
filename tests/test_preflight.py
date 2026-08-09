import unittest

from postex.enums import PosterSize
from postex.preflight import _layout_typography_findings, _minimum_body_font


class PreflightTypographyTests(unittest.TestCase):
    def test_a1_uses_shorter_distance_font_threshold(self) -> None:
        pixels, points = _minimum_body_font(PosterSize.A1_LANDSCAPE)
        self.assertAlmostEqual(points, 20.0)
        self.assertAlmostEqual(pixels, 26.6666667)

    def test_larger_formats_retain_28_point_threshold(self) -> None:
        for size in (
            PosterSize.A0_LANDSCAPE,
            PosterSize.INCH_36X48_LANDSCAPE,
        ):
            pixels, points = _minimum_body_font(size)
            self.assertAlmostEqual(points, 28.0)
            self.assertAlmostEqual(pixels, 37.3333333)

    def test_multiline_metric_fails_line_limit_and_capacity(self) -> None:
        report = _layout_typography_findings(
            {
                "elements": [
                    {
                        "name": "biology-3-value",
                        "text": "0.031 / 0.038",
                        "bbox": [100, 100, 420, 78],
                        "resolvedFontSize": 68,
                        "textLayout": {
                            "lineCount": 2,
                            "lines": [{"text": "0.031 /"}, {"text": "0.038"}],
                        },
                    }
                ]
            }
        )
        by_code = {item["code"]: item for item in report}
        self.assertFalse(by_code["text_line_limits"]["passed"])
        self.assertFalse(by_code["text_capacity"]["passed"])

    def test_overlapping_text_boxes_fail_collision_check(self) -> None:
        report = _layout_typography_findings(
            {
                "elements": [
                    {
                        "name": "metric-value",
                        "text": "92%",
                        "bbox": [0, 0, 120, 60],
                        "resolvedFontSize": 48,
                        "textLayout": {"lineCount": 1, "lines": [{"text": "92%"}]},
                    },
                    {
                        "name": "metric-label",
                        "text": "stability",
                        "bbox": [0, 55, 120, 50],
                        "resolvedFontSize": 24,
                        "textLayout": {"lineCount": 1, "lines": [{"text": "stability"}]},
                    },
                ]
            }
        )
        by_code = {item["code"]: item for item in report}
        self.assertFalse(by_code["text_collisions"]["passed"])

    def test_cjk_punctuation_break_is_reported(self) -> None:
        report = _layout_typography_findings(
            {
                "elements": [
                    {
                        "name": "conclusion",
                        "text": "第一行。\n，第二行",
                        "bbox": [0, 0, 300, 120],
                        "resolvedFontSize": 32,
                        "textLayout": {
                            "lineCount": 2,
                            "lines": [{"text": "第一行。"}, {"text": "，第二行"}],
                        },
                    }
                ]
            }
        )
        by_code = {item["code"]: item for item in report}
        self.assertFalse(by_code["cjk_line_breaks"]["passed"])


if __name__ == "__main__":
    unittest.main()
