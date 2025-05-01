import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def main():
    # Load the individual‐level category indicators
    csv_path = 'individual_level_with_category_indicators.csv'
    df = pd.read_csv(csv_path)

    # Collapse to state‑year: did the state ever cover each category?
    state_year = (
        df
        .groupby(['_state', 'year'])
        .agg({
            'any_nrt': 'max',
            'any_medication': 'max',
            'any_counseling': 'max'
        })
        .reset_index()
    )

    # Define the six mutually‑exclusive coverage combos
    conds = [
        (state_year[['any_nrt','any_medication','any_counseling']]==[0,0,0]).all(axis=1),
        (state_year[['any_nrt','any_medication','any_counseling']]==[1,0,0]).all(axis=1),
        (state_year[['any_nrt','any_medication','any_counseling']]==[0,1,0]).all(axis=1),
        (state_year[['any_nrt','any_medication','any_counseling']]==[1,1,0]).all(axis=1),
        (state_year[['any_nrt','any_medication','any_counseling']]==[1,0,1]).all(axis=1),
        (state_year[['any_nrt','any_medication','any_counseling']]==[1,1,1]).all(axis=1)
    ]
    choices = [
        'No coverage',
        'NRT only',
        'Medication only',
        'NRT + Medication',
        'NRT + Counseling',
        'All categories'
    ]
    state_year['combo'] = np.select(conds, choices, default='Other')

    # Count number of unique states per year×combo
    counts = (
        state_year
        .groupby(['year','combo'])['_state']
        .nunique()
        .unstack(fill_value=0)
    )

    # Re‑order columns
    order = [
        'No coverage','NRT only','Medication only',
        'NRT + Medication','NRT + Counseling','All categories'
    ]
    counts = counts[order]

    # Convert year index to strings so ticks read "2011", "2012", etc.
    counts.index = counts.index.astype(int).astype(str)

    # Define colors
    colors = {
        'No coverage':      '#006400',
        'NRT only':         '#FF4500',
        'Medication only':  '#1f77b4',
        'NRT + Medication': '#8B0000',
        'NRT + Counseling':'#2E8B57',
        'All categories':   '#A0522D'
    }

    # Plot and save
    output_dir = 'Visualizations'
    os.makedirs(output_dir, exist_ok=True)

    fig, ax = plt.subplots(figsize=(12, 6))
    counts.plot(
        kind='bar',
        stacked=True,
        color=[colors[c] for c in counts.columns],
        ax=ax
    )
    ax.set_title('Treatment Coverage Combinations by Year', fontsize=16)
    ax.set_xlabel('Year', fontsize=14)
    ax.set_ylabel('Number of States', fontsize=14)
    ax.legend(
        title='',
        bbox_to_anchor=(0.5, -0.15),
        loc='upper center',
        ncol=3
    )
    plt.xticks(rotation=0)
    plt.tight_layout()

    save_path = os.path.join(output_dir, 'treatment_coverage_combinations_by_year.png')
    fig.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close(fig)

    print(f'Plot saved to {save_path}')

if __name__ == "__main__":
    main()