import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.patches as mpatches
from matplotlib.cm import ScalarMappable

# Define custom colors for treatment groups with light/dark variants
COLORS = {
    # Blue color scheme for NRT+Med
    'nrt_med_low': '#c6dbef',       # Light blue for low values
    'nrt_med_high': '#084594',      # Dark blue for high values
    
    # Red-orange color scheme for NRT+Med+Counseling
    'all_three_low': '#fee8c8',     # Light orange for low values
    'all_three_high': '#e34a33',    # Dark orange-red for high values
    
    # Other colors
    'border': '#333333',            # Dark gray for borders
    'no_data': '#f0f0f0'            # Light gray for no data
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
    
    return df

# Function to create a combined map visualization with all four maps
def create_combined_maps(df, shapefile_path, output_dir):
    """
    Create a 2x2 grid of maps showing smoking prevalence and quit success rate
    for 2011 and 2020, using different colors for treatment groups.
    """
    # Load the US states shapefile
    us_states = gpd.read_file(shapefile_path)
    
    # Convert state FIPS codes for joining
    us_states['_state'] = us_states['STATEFP'].astype(int)
    
    # Filter to continental US (exclude Alaska, Hawaii, territories)
    continental_us = us_states[~us_states['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'MP', 'AS'])]
    
    # Create custom colormaps for each treatment group
    nrt_med_cmap = LinearSegmentedColormap.from_list('nrt_med_cmap', 
                                                    [COLORS['nrt_med_low'], 
                                                     COLORS['nrt_med_high']])
    
    all_three_cmap = LinearSegmentedColormap.from_list('all_three_cmap', 
                                                      [COLORS['all_three_low'], 
                                                       COLORS['all_three_high']])
    
    # Create figure with 2x2 grid
    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    
    # Flatten axes for easier iteration
    axes = axes.flatten()
    
    # Set up parameters for each of the four maps
    map_params = [
        {
            'year': 2011, 
            'column': 'current_smoker_prev', 
            'title': 'Smoking Prevalence (2011)',
            'ax': axes[0]
        },
        {
            'year': 2020, 
            'column': 'current_smoker_prev', 
            'title': 'Smoking Prevalence (2020)',
            'ax': axes[1]
        },
        {
            'year': 2011, 
            'column': 'past_year_quit_attempt_prev', 
            'title': 'Quit Success Rate (2011)',
            'ax': axes[2]
        },
        {
            'year': 2020, 
            'column': 'past_year_quit_attempt_prev', 
            'title': 'Quit Success Rate (2020)',
            'ax': axes[3]
        }
    ]
    
    # Calculate global min/max values for consistent colormaps
    smoking_min = df['current_smoker_prev'].min()
    smoking_max = df['current_smoker_prev'].max()
    quit_min = df['past_year_quit_attempt_prev'].min()
    quit_max = df['past_year_quit_attempt_prev'].max()
    
    # Loop through each map
    for params in map_params:
        ax = params['ax']
        year = params['year']
        column = params['column']
        title = params['title']
        
        # Select the appropriate norm based on column
        if 'current_smoker_prev' in column:
            norm = Normalize(vmin=smoking_min, vmax=smoking_max)
        else:
            norm = Normalize(vmin=quit_min, vmax=quit_max)
        
        # Filter data for the current year
        year_data = df[df['year'] == year]
        
        # Merge with shapefile
        merged_data = continental_us.merge(year_data, on='_state', how='left')
        
        # First, draw all states with light gray
        continental_us.plot(
            ax=ax,
            color=COLORS['no_data'],
            edgecolor=COLORS['border'],
            linewidth=0.5,
        )
        
        # Separate by treatment group
        nrt_med_states = merged_data[merged_data['treatment_group'] == 2].copy()
        all_three_states = merged_data[merged_data['treatment_group'] == 4].copy()
        
        # Plot NRT+Med states with blue color scheme
        if not nrt_med_states.empty:
            nrt_med_states.plot(
                column=column,
                ax=ax,
                cmap=nrt_med_cmap,
                norm=norm,
                linewidth=0.5,
                edgecolor=COLORS['border']
            )
        
        # Plot All Three states with orange-red color scheme
        if not all_three_states.empty:
            all_three_states.plot(
                column=column,
                ax=ax,
                cmap=all_three_cmap,
                norm=norm,
                linewidth=0.5,
                edgecolor=COLORS['border']
            )
        
        # Set title and remove axes
        ax.set_title(title, fontsize=14)
        ax.set_axis_off()
    
    # Add a common legend for all maps at the bottom of the figure
    # Create legend patches
    legend_patches = [
        # Blue treatment group (low and high values)
        mpatches.Patch(facecolor=COLORS['nrt_med_low'], 
                      edgecolor=COLORS['border'],
                      label='NRT + Medication (Low Value)'),
        mpatches.Patch(facecolor=COLORS['nrt_med_high'], 
                      edgecolor=COLORS['border'],
                      label='NRT + Medication (High Value)'),
        
        # Orange treatment group (low and high values)
        mpatches.Patch(facecolor=COLORS['all_three_low'], 
                      edgecolor=COLORS['border'],
                      label='NRT + Med + Counseling (Low Value)'),
        mpatches.Patch(facecolor=COLORS['all_three_high'], 
                      edgecolor=COLORS['border'],
                      label='NRT + Med + Counseling (High Value)')
    ]
    
    # Add the legend to the center bottom of the figure
    fig.legend(
        handles=legend_patches,
        loc='lower center',
        ncol=4,
        bbox_to_anchor=(0.5, 0.02),
        frameon=True,
        fontsize=12
    )
    
    # Add overall title
    fig.suptitle('Impact of Medicaid Tobacco Cessation Coverage on Smoking Outcomes (2011-2020)', 
                fontsize=18, y=0.98)
    
    # Add note about the data 
    plt.figtext(0.5, 0.01, 
               'Data: State-level Medicaid tobacco cessation coverage analysis',
               ha='center', fontsize=10, style='italic')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.08, 1, 0.95])
    
    # Save the combined figure
    map_file = os.path.join(output_dir, 'combined_tobacco_maps.png')
    plt.savefig(map_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Combined map saved to {map_file}")

def main():
    """Main function to execute the map visualization."""
    # Set output directory
    output_dir = "C:/Users/James/Desktop/Github/State-Tobacco-Analysis/Visualizations"
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Set path to your downloaded shapefile
    shapefile_dir = os.path.join(output_dir, "shapefiles")
    shapefile_path = os.path.join(shapefile_dir, "cb_2018_us_state_500k.shp")
    
    # Verify that the shapefile exists
    if not os.path.exists(shapefile_path):
        print(f"Shapefile not found at: {shapefile_path}")
        print("Please ensure the shapefile is extracted to the correct location.")
        return
    else:
        print(f"Found shapefile at: {shapefile_path}")
    
    # Load the data
    print("\nLoading tobacco data...")
    df = load_data()
    
    if df is None:
        print("Failed to load data. Exiting.")
        return
    
    print(f"Data loaded successfully with {len(df)} observations.")
    print(f"Found {df['_state'].nunique()} states across {df['year'].nunique()} years.")
    
    # Create the combined maps visualization
    print("\nCreating combined map visualization...")
    create_combined_maps(df, shapefile_path, output_dir)
    
    print("\nMap visualization completed successfully!")

if __name__ == "__main__":
    main()