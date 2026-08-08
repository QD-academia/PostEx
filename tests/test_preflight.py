import unittest

from postex.enums import PosterSize
from postex.preflight import _minimum_body_font


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


if __name__ == "__main__":
    unittest.main()
