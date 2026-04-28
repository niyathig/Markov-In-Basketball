import pandas as pd
from pathlib import Path

# Read the combined transition matrix
data_dir = Path(__file__).parent
input_file = data_dir / 'All_Games_transition_matrix.csv'

df = pd.read_csv(input_file, index_col=0)

# Divide each row by its sum to get probabilities
probability_df = df.div(df.sum(axis=1), axis=0)

# Save to CSV
output_file = data_dir / 'All_Games_probability_matrix.csv'
probability_df.to_csv(output_file)

print(f"Saved: {output_file.name}")
