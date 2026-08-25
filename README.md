# roster-helper

Convert a fantasy-football draft export into a CSV containing each player's
projected keeper round for the following season. The keeper cost moves up three
rounds, so a player drafted in Round 4 costs a Round 1 pick the next season.
Players drafted in Rounds 1–3 are omitted because they cannot move up three
rounds.

## Input

The primary input format is a round heading followed by three lines per pick:

```text
Round 1

1. Ja'Marr Chase
   (Cin - WR)
   Team A
2. Saquon Barkley
   (Phi - RB)
   Team B
```

Blank lines and indentation are optional. The script joins the player and
team/position lines, so `Ja'Marr Chase` and `(Cin - WR)` become
`Ja'Marr Chase Cin - WR` in the CSV.

## Usage

Install pandas, then run the converter:

```sh
python3 -m pip install -r requirements.txt
python3 draft_results_to_csv.py --draft-year 2030 draft_results.txt
```

Replace `2030` with the year the source draft took place. The script uses that
value to generate the column names and the following season's keeper year. In
this example, the default output is `2031_draft_rounds.csv`.

Choose a different output path with `--output`, or combine multiple input files
from the same draft year:

```sh
python3 draft_results_to_csv.py --draft-year 2030 league_a.txt league_b.txt \
  --output projected_keepers.csv
```

The output columns are generated from `--draft-year`:

```text
Manager,Player,<draft year> Draft Position,<next year> Round
```

For the example command above, an output row would be:

```csv
Manager,Player,2030 Draft Position,2031 Round
Team A,George Kittle SF - TE,"Round 4, Pick 7",1
```

Run the tests with:

```sh
python3 -m unittest discover -s tests
```
