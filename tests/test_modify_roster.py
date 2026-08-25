import unittest

from draft_results_to_csv import create_keeper_dataframe
from modify_roster import parse_final_roster_text


FINAL_ROSTER_TEXT = """\
Blouses
Player
2030 Draft Position
2030 Final Rank
Current O-Rank
Lamar Jackson Bal - QB No new player Notes\tRound 1, Pick 8\t36\t50
A.J. Brown NE - WR No new player Notes\tRound 2, Pick 3\t49\t23
David Montgomery Hou - RB Player Note\tRound 4, Pick 3\t100\t54
Zay Flowers Bal - WR Player Note\tRound 5, Pick 8\t40\t31
Sam LaPorta Det - TE Player Note\tRound 6, Pick 3\t181\t70
Waiver Player NYJ - RB Player Note\t-\t52\t121
"""


class FinalRosterTests(unittest.TestCase):
    def test_parses_manager_players_and_draft_positions(self):
        roster = parse_final_roster_text(FINAL_ROSTER_TEXT, draft_year=2030)

        self.assertEqual(roster["Manager"].unique().tolist(), ["Blouses"])
        self.assertEqual(roster["Draft Round"].tolist(), [1, 2, 4, 5, 6])
        self.assertEqual(roster["Pick"].tolist(), [8, 3, 3, 8, 3])
        self.assertEqual(roster.iloc[0]["Player"], "Lamar Jackson Bal - QB")

    def test_creates_same_keeper_projection_columns(self):
        roster = parse_final_roster_text(FINAL_ROSTER_TEXT, draft_year=2030)

        keepers = create_keeper_dataframe(roster, draft_year=2030)

        self.assertEqual(
            keepers.columns.tolist(),
            [
                "Manager",
                "Player",
                "Keeper",
                "2030 Draft Position",
                "2031 Round",
            ],
        )
        self.assertEqual(
            keepers["2030 Draft Position"].tolist(),
            ["Round 4, Pick 3", "Round 5, Pick 8", "Round 6, Pick 3"],
        )


if __name__ == "__main__":
    unittest.main()
