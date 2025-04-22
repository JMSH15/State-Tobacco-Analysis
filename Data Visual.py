import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from matplotlib.ticker import PercentFormatter

# Set the aesthetics for the visualizations
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 12,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 16
})

# Define custom colors for consistent visualization
COLORS = {
    'nrt_med': '#1f77b4',           # Blue for NRT+Med
    'all_three': '#ff7f0e',         # Orange for All Three
    'bg_light': '#f8f9fa',          # Light background
    'grid': '#e6e6e6',              # Grid lines
    'text': '#333333'               # Text color
}

# Function to load and prepare data
def load_data(file_path="C:/Users/James/Desktop/Github/State-Tobacco-Analysis/state_level_descriptive_data.csv"):
    """Load the state-level tobacco data."""
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"File {file_path} not found. Please provide the correct path.")
        return None
    
    # Load the data
    df = pd.read_csv(file_path)
    
    # Convert to percentage for easier interpretation
    df['current_smoker_prev'] = df['current_smoker_prev'] * 100
    df['past_year_quit_attempt_prev'] = df['past_year_quit_attempt_prev'] * 100
    
    # Create treatment group labels
    df['treatment_label'] = df['treatment_group'].map({
        2: 'NRT + Medication', 
        4: 'NRT + Medication + Counseling'
    })
    
    # Create a column for year as category for better plotting
    df['year_cat'] = df['year'].astype(str)
    
    return df

# 1. Smoking Prevalence Trends - First panel
def plot_smoking_prevalence_trends(df, output_dir):
    """Create a figure showing smoking prevalence trends by treatment group."""
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Calculate aggregated statistics by treatment group and year
    grouped_data = df.groupby(['year', 'treatment_label']).agg({
        'current_smoker_prev': 'mean'
    }).reset_index()
    
    # Create pivot table for easier plotting
    smoking_pivot = grouped_data.pivot(index='year', columns='treatment_label', values='current_smoker_prev')
    
    # Plot the data
    smoking_pivot.plot(linewidth=2.5, marker='o', markersize=8)
    
    # Add average lines
    for i, treatment in enumerate(['NRT + Medication', 'NRT + Medication + Counseling']):
        avg = smoking_pivot[treatment].mean()
        plt.axhline(avg, color=list(COLORS.values())[i], linestyle='--', alpha=0.5)
        plt.text(2011.5, avg + 0.5, f'Avg: {avg:.1f}%', color=list(COLORS.values())[i])
    
    # Add labels and title
    plt.title('Smoking Prevalence Trends by Treatment Group (2011-2020)', fontsize=16)
    plt.xlabel('Year')
    plt.ylabel('Current Smoker Prevalence (%)')
    plt.grid(alpha=0.3)
    
    # Adjust legend
    plt.legend(title='Treatment Group', loc='best')
    
    # Add note about data source
    plt.figtext(0.5, 0.01, 
               'Data: State-level Medicaid tobacco cessation coverage analysis',
               ha='center', fontsize=9, style='italic')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save figure
    plt.savefig(os.path.join(output_dir, '1_smoking_prevalence_trends.png'), dpi=300, bbox_inches='tight')
    plt.close()

# 2. Quit Success Rate - Second panel
def plot_quit_success_rate(df, output_dir):
    """Create a figure showing quit success rate by treatment group."""
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Calculate aggregated statistics by treatment group and year
    grouped_data = df.groupby(['year', 'treatment_label']).agg({
        'past_year_quit_attempt_prev': 'mean'
    }).reset_index()
    
    # Create pivot table for easier plotting
    quit_pivot = grouped_data.pivot(index='year', columns='treatment_label', values='past_year_quit_attempt_prev')
    
    # Plot the data
    quit_pivot.plot(linewidth=2.5, marker='o', markersize=8)
    
    # Add average lines
    for i, treatment in enumerate(['NRT + Medication', 'NRT + Medication + Counseling']):
        avg = quit_pivot[treatment].mean()
        plt.axhline(avg, color=list(COLORS.values())[i], linestyle='--', alpha=0.5)
        plt.text(2011.5, avg + 0.5, f'Avg: {avg:.1f}%', color=list(COLORS.values())[i])
    
    # Add labels and title
    plt.title('Quit Success Rate by Treatment Group (2011-2020)', fontsize=16)
    plt.xlabel('Year')
    plt.ylabel('Quit Success Rate (%)', fontsize=10)
    plt.grid(alpha=0.3)
    
    # Get current axis and set y-tick font size smaller
    ax = plt.gca()
    ax.tick_params(axis='y', labelsize=8)  # Make y-axis tick labels smaller
    
    # Adjust legend
    plt.legend(title='Treatment Group', loc='best')
    
    # Add note about data source
    plt.figtext(0.5, 0.01, 
               'Data: State-level Medicaid tobacco cessation coverage analysis',
               ha='center', fontsize=9, style='italic')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save figure
    plt.savefig(os.path.join(output_dir, '2_quit_success_rate.png'), dpi=300, bbox_inches='tight')
    plt.close()

# 3. Average Outcomes Bar Chart - Third panel
def plot_average_outcomes(df, output_dir):
    """Create a bar chart comparing average outcomes by treatment approach."""
    # Create figure
    plt.figure(figsize=(10, 6))
    
    # Calculate aggregated statistics by treatment group and year
    grouped_data = df.groupby(['year', 'treatment_label']).agg({
        'current_smoker_prev': 'mean',
        'past_year_quit_attempt_prev': 'mean'
    }).reset_index()
    
    # Calculate average outcomes by treatment
    avg_by_treatment = grouped_data.groupby('treatment_label').agg({
        'current_smoker_prev': 'mean',
        'past_year_quit_attempt_prev': 'mean'
    }).reset_index()
    
    # Reshape for bar plotting
    avg_melted = pd.melt(
        avg_by_treatment, 
        id_vars='treatment_label', 
        value_vars=['current_smoker_prev', 'past_year_quit_attempt_prev'],
        var_name='Outcome', 
        value_name='Percentage'
    )
    
    # Map variable names to better labels
    avg_melted['Outcome'] = avg_melted['Outcome'].map({
        'current_smoker_prev': 'Smoking Prevalence', 
        'past_year_quit_attempt_prev': 'Quit Success Rate'
    })
    
    # Create grouped bar chart
    ax = sns.barplot(
        x='Outcome', 
        y='Percentage', 
        hue='treatment_label', 
        data=avg_melted,
        palette=[COLORS['nrt_med'], COLORS['all_three']]
    )
    
    # Add value labels
    for i, p in enumerate(ax.patches):
        height = p.get_height()
        ax.text(
            p.get_x() + p.get_width()/2.,
            height + 0.5,
            f'{height:.1f}%',
            ha="center", 
            fontsize=10
        )
    
    # Add labels and title
    plt.title('Average Outcomes by Treatment Approach (2011-2020)', fontsize=16)
    plt.xlabel('')
    plt.ylabel('Percentage (%)')
    plt.grid(axis='y', alpha=0.3)
    
    # Adjust legend
    plt.legend(title='Treatment Group', loc='upper right')
    
    # Add note about data source
    plt.figtext(0.5, 0.01, 
               'Data: State-level Medicaid tobacco cessation coverage analysis',
               ha='center', fontsize=9, style='italic')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save figure
    plt.savefig(os.path.join(output_dir, '3_average_outcomes.png'), dpi=300, bbox_inches='tight')
    plt.close()

# Main function
def main():
    """Main function to execute all visualizations."""
    # Set output directory
    output_dir = "C:/Users/James/Desktop/Github/State-Tobacco-Analysis/Visualizations"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load data
    df = load_data()
    
    if df is None:
        print("Failed to load data. Exiting.")
        return
    
    print(f"Data loaded successfully with {len(df)} observations.")
    print(f"Found {df['_state'].nunique()} states across {df['year'].nunique()} years.")
    print(f"Treatment groups present: {df['treatment_group'].unique()}")
    
    # Generate only the first three smoking outcome visualizations
    print("\nGenerating smoking prevalence trends visualization...")
    plot_smoking_prevalence_trends(df, output_dir)
    
    print("Generating quit success rate visualization...")
    plot_quit_success_rate(df, output_dir)
    
    print("Generating average outcomes visualization...")
    plot_average_outcomes(df, output_dir)
    
    print("\nAll visualizations have been saved to:", output_dir)
    print("The following files were created:")
    print("  - 1_smoking_prevalence_trends.png")
    print("  - 2_quit_success_rate.png")
    print("  - 3_average_outcomes.png")
    
if __name__ == "__main__":
    main()