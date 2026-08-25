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
                    "Draft Round": 1,
                    "Pick": 1,
                },
                {
                    "Manager": "Team B",
                    "Player": "Saquon Barkley Phi - RB",
                    "Draft Round": 1,
                    "Pick": 2,
                },
                {
                    "Manager": "Team C",
                    "Player": "George Kittle SF - TE",
                    "Draft Round": 4,
                    "Pick": 7,
                },
            ],
        )

    def test_dataframe_calculates_keeper_round_and_output_columns(self):
        draft = parse_draft_text(DRAFT_TEXT)

        keepers = create_keeper_dataframe(draft, draft_year=2030)

        self.assertEqual(
            keepers.to_dict("records"),
            [
                {
                    "Manager": "Team C",
                    "Player": "George Kittle SF - TE",
                    "2030 Draft Position": "Round 4, Pick 7",
                    "2031 Round": 1,
                }
            ],
        )

    def test_reports_malformed_team_position_line(self):
        malformed = """\
Round 4
1. A Player
Not parenthesized
A Manager
"""

        with self.assertRaisesRegex(ValueError, r"expected '\(Team - Position\)'"):
            parse_draft_text(malformed, "draft.txt")


if __name__ == "__main__":
    unittest.main()
