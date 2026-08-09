import unittest
from pathlib import Path

from postex.palette_catalog import load_palette_catalog

ROOT = Path(__file__).resolve().parents[1]


class PaletteCatalogTests(unittest.TestCase):
    def setUp(self) -> None:
        self.catalog = load_palette_catalog(ROOT)

    def test_requested_collections_are_complete(self) -> None:
        self.assertEqual(len(self.catalog.entries), 104)
        self.assertEqual(len(self.catalog.by_collection("city-landmarks")), 19)
        self.assertEqual(len(self.catalog.by_collection("universities")), 50)
        self.assertEqual(len(self.catalog.by_collection("genshin-characters")), 35)

    def test_genshin_has_seven_groups_of_five(self) -> None:
        entries = self.catalog.by_collection("genshin-characters")
        groups = {item.group for item in entries}
        self.assertEqual(
            groups,
            {"蒙德", "璃月", "稻妻", "须弥", "枫丹", "纳塔", "挪德卡莱"},
        )
        self.assertTrue(all(sum(item.group == group for item in entries) == 5 for group in groups))

    def test_university_ranks_match_2026_top_50_contract(self) -> None:
        entries = self.catalog.by_collection("universities")
        self.assertEqual(entries[0].name, "清华大学")
        self.assertEqual(entries[-1].name, "北京邮电大学")
        self.assertEqual([item.rank for item in entries].count(48), 2)
        self.assertNotIn(49, [item.rank for item in entries])

    def test_all_selected_assets_are_release_ready(self) -> None:
        blockers = self.catalog.release_blockers()
        self.assertEqual(blockers, {})
        self.assertTrue(
            all((self.catalog.root / entry.artwork.path).exists() for entry in self.catalog.entries)
        )
        self.assertTrue(
            all(
                (self.catalog.root / entry.artwork.palette_path).exists()
                for entry in self.catalog.entries
            )
        )


if __name__ == "__main__":
    unittest.main()
