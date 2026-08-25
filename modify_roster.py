#!/usr/bin/env python3
"""Create keeper-round projections from a final-roster text export."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

from draft_results_to_csv import KEEPER_MARKER, RAW_COLUMNS, create_keeper_dataframe


DRAFT_POSITION_PATTERN = re.compile(r"Round\s+(\d+),\s*Pick\s+(\d+)", re.IGNORECASE)
PLAYER_PATTERN = re.compile(r"^(.+? - [A-Za-z]+)(?:\s|$)")


def parse_final_roster_text(
    text: str, draft_year: int, source_name: str = "input"
) -> pd.DataFrame:
    """Parse manager sections from a final-roster text export."""
    lines = text.splitlines()
    records = []
    index = 0

    expected_headers = [
        "Player",
        f"{draft_year} Draft Position",
        f"{draft_year} Final Rank",
        "Current O-Rank",
    ]

    while index < len(lines):
        if not lines[index].strip():
            index += 1
            continue

        manager = lines[index].strip()
        headers = [line.strip() for line in lines[index + 1 : index + 5]]
        if headers != expected_headers:
            raise ValueError(
                f"{source_name}:{index + 1}: expected a manager followed by "
                f"the headers {expected_headers}; found {manager!r}"
            )
        index += 5

        # Read player rows until the next manager/header section.
        while index < len(lines):
            if index + 1 < len(lines) and lines[index + 1].strip() == "Player":
                break

            row = lines[index].strip()
            index += 1
            if not row:
                continue

            columns = row.split("\t")
            if len(columns) != 4:
                raise ValueError(
                    f"{source_name}:{index}: expected four tab-separated values; "
                    f"found {len(columns)}"
                )

            player_text, draft_position, _, _ = columns
            position_match = DRAFT_POSITION_PATTERN.fullmatch(draft_position.strip())

            # Undrafted/free-agent players use '-' and have no keeper cost.
            if not position_match:
                continue

            player_match = PLAYER_PATTERN.match(player_text.strip())
            if not player_match:
                raise ValueError(
                    f"{source_name}:{index}: could not find team and position in "
                    f"{player_text!r}"
                )

            player = player_match.group(1).replace(KEEPER_MARKER, "").strip()
            records.append(
                {
                    "Manager": manager,
                    "Player": player,
                    "Keeper": "Yes" if KEEPER_MARKER in player_text else "",
                    "Draft Round": int(position_match.group(1)),
                    "Pick": int(position_match.group(2)),
                }
            )

    return pd.DataFrame(records, columns=RAW_COLUMNS)


def read_final_roster(path: Path, draft_year: int, encoding: str) -> pd.DataFrame:
    """Read and parse one final-roster text file."""
    try:
        text = path.read_text(encoding=encoding)
    except UnicodeDecodeError as error:
        raise ValueError(
            f"{path}: could not decode the file as {encoding}; "
            "try --encoding cp1252"
        ) from error
    except OSError as error:
        raise ValueError(f"{path}: {error.strerror or error}") from error

    return parse_final_roster_text(text, draft_year, str(path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert final-roster text files into a CSV of next season's "
            "keeper rounds."
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
        help="final-roster text file",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="output CSV path (default: NEXT_YEAR_final_roster_rounds.csv)",
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
    output_path = args.output or Path(
        f"{args.draft_year + 1}_final_roster_rounds.csv"
    )

    if output_path.resolve() in input_paths:
        print("error: the output path cannot also be an input file", file=sys.stderr)
        return 2

    try:
        rosters = [
            read_final_roster(path, args.draft_year, args.encoding)
            for path in input_paths
        ]
        roster = pd.concat(rosters, ignore_index=True)
        keepers = create_keeper_dataframe(roster, args.draft_year)

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
