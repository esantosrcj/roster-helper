#!/usr/bin/env python3
"""Convert fantasy draft results into next season's keeper rounds."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd


ROUND_PATTERN = re.compile(r"Round\s+(\d+)", re.IGNORECASE)
PICK_PATTERN = re.compile(r"(\d+)\.\s+(.+)")
TEAM_POSITION_PATTERN = re.compile(r"\((.+)\)")

RAW_COLUMNS = ["Manager", "Player", "Draft Round", "Pick"]


def parse_draft_text(text: str, source_name: str = "input") -> pd.DataFrame:
    """Parse the text file's three-line player entries into a DataFrame."""
    # Blank lines and indentation do not contain draft information.
    lines = [
        (line_number, line.strip())
        for line_number, line in enumerate(text.splitlines(), start=1)
        if line.strip()
    ]

    if not lines:
        raise ValueError(f"{source_name}: the file is empty")

    records = []
    current_round = None
    index = 0

    while index < len(lines):
        line_number, line = lines[index]

        round_match = ROUND_PATTERN.fullmatch(line)
        if round_match:
            current_round = int(round_match.group(1))
            if current_round == 0:
                raise ValueError(
                    f"{source_name}:{line_number}: round must be greater than zero"
                )
            index += 1
            continue

        pick_match = PICK_PATTERN.fullmatch(line)
        if not pick_match:
            raise ValueError(
                f"{source_name}:{line_number}: expected 'Round N' or "
                f"'N. Player Name'; found {line!r}"
            )
        if current_round is None:
            raise ValueError(
                f"{source_name}:{line_number}: player appears before a round heading"
            )

        pick = int(pick_match.group(1))
        if pick == 0:
            raise ValueError(
                f"{source_name}:{line_number}: pick must be greater than zero"
            )

        # Ignore the first three picks in each round as complete blocks. This
        # also handles one-line placeholders such as "2. --empty-- Team Name".
        # Draft rounds 1-3 are ineligible as well, regardless of pick number.
        if pick <= 3 or current_round <= 3:
            index += 1
            while index < len(lines):
                next_line = lines[index][1]
                if ROUND_PATTERN.fullmatch(next_line) or PICK_PATTERN.fullmatch(
                    next_line
                ):
                    break
                index += 1
            continue

        if index + 2 >= len(lines):
            raise ValueError(
                f"{source_name}:{line_number}: player entry is missing the "
                "team/position or manager line"
            )

        team_line_number, team_line = lines[index + 1]
        _, manager = lines[index + 2]
        team_match = TEAM_POSITION_PATTERN.fullmatch(team_line)
        if not team_match:
            raise ValueError(
                f"{source_name}:{team_line_number}: expected '(Team - Position)'; "
                f"found {team_line!r}"
            )

        player_name = pick_match.group(2).strip()
        team_position = team_match.group(1).strip()
        records.append(
            {
                "Manager": manager,
                "Player": f"{player_name} {team_position}",
                "Draft Round": current_round,
                "Pick": pick,
            }
        )
        index += 3

    return pd.DataFrame(records, columns=RAW_COLUMNS)


def create_keeper_dataframe(draft: pd.DataFrame, draft_year: int) -> pd.DataFrame:
    """Calculate next season's keeper round and select the output columns."""
    next_year = draft_year + 1
    draft_position_column = f"{draft_year} Draft Position"
    keeper_round_column = f"{next_year} Round"

    # Rounds 1-3 cannot move up three rounds, and picks 1-3 are excluded.
    eligible = (draft["Draft Round"] > 3) & (draft["Pick"] > 3)
    keepers = draft.loc[eligible].copy()

    keepers[draft_position_column] = (
        "Round "
        + keepers["Draft Round"].astype(str)
        + ", Pick "
        + keepers["Pick"].astype(str)
    )
    keepers[keeper_round_column] = keepers["Draft Round"] - 3

    output_columns = [
        "Manager",
        "Player",
        draft_position_column,
        keeper_round_column,
    ]
    keepers = keepers[output_columns]
    return keepers.sort_values(["Manager", keeper_round_column], ignore_index=True)


def read_draft_file(path: Path, encoding: str) -> pd.DataFrame:
    """Read and parse one draft-results text file."""
    try:
        text = path.read_text(encoding=encoding)
    except UnicodeDecodeError as error:
        raise ValueError(
            f"{path}: could not decode the file as {encoding}; "
            "try --encoding cp1252"
        ) from error
    except OSError as error:
        raise ValueError(f"{path}: {error.strerror or error}") from error

    return parse_draft_text(text, str(path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert draft-result text files into a CSV of next season's keeper "
            "rounds. Players drafted in rounds 1-3 are omitted."
        )
    )
    parser.add_argument(
        "--draft-year",
        required=True,
        type=int,
        help="year in which the source draft took place",
    )
    parser.add_argument(
        "input_files",
        metavar="INPUT",
        nargs="+",
        type=Path,
        help="draft-results text file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output CSV path (default: NEXT_YEAR_draft_rounds.csv)",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="input text encoding (default: utf-8-sig)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.draft_year < 1:
        parser.error("--draft-year must be greater than zero")

    input_paths = [path.resolve() for path in args.input_files]
    output_path = args.output or Path(f"{args.draft_year + 1}_draft_rounds.csv")

    if output_path.resolve() in input_paths:
        print("error: the output path cannot also be an input file", file=sys.stderr)
        return 2

    try:
        drafts = [read_draft_file(path, args.encoding) for path in input_paths]
        draft = pd.concat(drafts, ignore_index=True)
        keepers = create_keeper_dataframe(draft, args.draft_year)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        keepers.to_csv(output_path, index=False)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"error: could not write {output_path}: {error}", file=sys.stderr)
        return 2

    print(f"Wrote {len(keepers)} eligible player(s) to {output_path}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
