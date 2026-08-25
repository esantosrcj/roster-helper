import unittest

from draft_results_to_csv import create_keeper_dataframe, parse_draft_text

DRAFT_TEXT = """\
Round 1

1. Ja'Marr Chase
   (Cin - WR)
   Team A
2. Saquon Barkley
   (Phi - RB)
   Team B

Round 4

7. George Kittle
   (SF - TE)
   Team C
"""


class DraftResultsTests(unittest.TestCase):
    def test_parses_three_line_player_entries_into_dataframe(self):
        draft = parse_draft_text(DRAFT_TEXT, "draft.txt")

        self.assertEqual(
            draft.to_dict("records"),
            [
                {
                    "Manager": "Team A",
                    "Player": "Ja'Marr Chase Cin - WR",
                    "Keeper": "",
                    "Draft Round": 1,
                    "Pick": 1,
                },
                {
                    "Manager": "Team B",
                    "Player": "Saquon Barkley Phi - RB",
                    "Keeper": "",
                    "Draft Round": 1,
                    "Pick": 2,
                },
                {
                    "Manager": "Team C",
                    "Player": "George Kittle SF - TE",
                    "Keeper": "",
                    "Draft Round": 4,
                    "Pick": 7,
                },
            ],
        )

    def test_keeps_first_three_picks_and_skips_empty_placeholders(self):
        draft_text = """\
Round 4
1. Jayden Higgins
(Hou - WR)
Team A
2. --empty--\tTeam B
3. Ollie Gordon II
(Mia - RB)
Team C

4. George Kittle
(SF - TE)
Team D
"""

        draft = parse_draft_text(draft_text, "draft.txt")

        self.assertEqual(draft["Pick"].tolist(), [1, 3, 4])
        self.assertEqual(
            draft["Player"].tolist(),
            [
                "Jayden Higgins Hou - WR",
                "Ollie Gordon II Mia - RB",
                "George Kittle SF - TE",
            ],
        )

    def test_snake_draft_manager_alternates_between_pick_eight_and_three(self):
        draft_text = """\
Round 4
3. Even Round Player
(NYJ - RB)
Blouses
Round 5
8. Odd Round Player
(Buf - WR)
Blouses
Round 6
3. Next Even Round Player
(GB - TE)
Blouses
"""

        draft = parse_draft_text(draft_text, "draft.txt")
        keepers = create_keeper_dataframe(draft, draft_year=2030)

        self.assertEqual(
            keepers["2030 Draft Position"].tolist(),
            ["Round 4, Pick 3", "Round 5, Pick 8", "Round 6, Pick 3"],
        )

    def test_marks_keeper_and_removes_marker_from_player_name(self):
        draft_text = """\
Round 5
5. Jayden Daniels \ue03e
(Was - QB)
Team F
"""

        draft = parse_draft_text(draft_text, "draft.txt")
        keepers = create_keeper_dataframe(draft, draft_year=2030)

        self.assertEqual(keepers.iloc[0]["Player"], "Jayden Daniels Was - QB")
        self.assertEqual(keepers.iloc[0]["Keeper"], "Yes")

    def test_dataframe_calculates_keeper_round_and_output_columns(self):
        draft = parse_draft_text(DRAFT_TEXT)

        keepers = create_keeper_dataframe(draft, draft_year=2030)

        self.assertEqual(
            keepers.to_dict("records"),
            [
                {
                    "Manager": "Team C",
                    "Player": "George Kittle SF - TE",
                    "Keeper": "",
                    "2030 Draft Position": "Round 4, Pick 7",
                    "2031 Round": 1,
                }
            ],
        )

    def test_reports_malformed_team_position_line(self):
        malformed = """\
Round 4
4. A Player
Not parenthesized
A Manager
"""

        with self.assertRaisesRegex(ValueError, r"expected '\(Team - Position\)'"):
            parse_draft_text(malformed, "draft.txt")


if __name__ == "__main__":
    unittest.main()
