import pandas as pd

# Read the CSV file using ISO-8859-1 encoding
df = pd.read_csv('[Year]_Fantasy_Football_Rosters.csv', encoding='ISO-8859-1')

# Remove the "[Year] Final Rank", "Current O-Rank" columns
df_filtered = df.drop(columns=['[Year] Final Rank','Current O-Rank'])

# Use regex to keep everything before and including ' - position'
df_filtered['Player'] = df_filtered['Player'].str.replace(r'( - \w+).*$', r'\1', regex=True)

# Filter rows where "[Year] Draft Position" starts with "Round"
df_filtered = df_filtered[df_filtered['[Year] Draft Position'].str.startswith('Round', na=False)].copy()

# Extract the number after "Round" and create a new column "[Year] Position Number"
df_filtered.loc[:, '[Year] Position Number'] = df_filtered['[Year] Draft Position'].str.extract(r'Round (\d+)').astype(int)

# Filter out rows where "[Year] Position Number" is less than 4
df_filtered = df_filtered[df_filtered['[Year] Position Number'] > 3]

# Add a new column "[New Year] Round" that is "[Year] Position Number" minus 3
df_filtered.loc[:, '[New Year] Round*'] = df_filtered['[Year] Position Number'] - 3

# Sort the filtered DataFrame by "Manager" and "[New Year] Round"
df_sorted = df_filtered.sort_values(by=['Manager', '[New Year] Round*'])

# Save the sorted DataFrame to a new CSV file
df_sorted.to_csv('[New Year]_rosters_filtered_sorted.csv', index=False)

print("File modified and saved as '[New Year]_rosters_filtered_sorted.csv'")