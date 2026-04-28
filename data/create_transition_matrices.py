import pandas as pd
import numpy as np
import os
from pathlib import Path

# Get directory
data_dir = Path(__file__).parent

# Find all CSV files
csv_files = sorted(data_dir.glob('*_shots.csv'))

print(f"Found {len(csv_files)} CSV files\n")

for csv_file in csv_files:
    print(f"Processing: {csv_file.name}")

    # Read CSV
    df = pd.read_csv(csv_file)

    # Get states from Category column
    states = df['Category'].dropna().tolist()

    # Get unique states (sorted for consistent ordering)
    unique_states = sorted(df['Category'].dropna().unique())
    n_states = len(unique_states)

    print(f"  States found: {n_states}")
    print(f"  State list: {unique_states}")

    # Create mapping from state to index
    state_to_idx = {state: i for i, state in enumerate(unique_states)}

    # Initialize transition matrix
    transition_matrix = np.zeros((n_states, n_states), dtype=int)

    # Count transitions
    for i in range(len(states) - 1):
        current_state = states[i]
        next_state = states[i + 1]

        current_idx = state_to_idx[current_state]
        next_idx = state_to_idx[next_state]

        transition_matrix[current_idx][next_idx] += 1

    # Create DataFrame with state labels
    transition_df = pd.DataFrame(
        transition_matrix,
        index=unique_states,
        columns=unique_states
    )

    # Save to CSV
    output_file = csv_file.parent / csv_file.name.replace('_shots.csv', '_transition_matrix.csv')
    transition_df.to_csv(output_file)

    print(f"  Saved: {output_file.name}")
    print(f"  Total transitions: {transition_matrix.sum()}")
    print()

print("All transition matrices created")
