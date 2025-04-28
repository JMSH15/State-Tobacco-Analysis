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

# Function to create a single map visualization with filled colors
def create_filled_color_map(df, shapefile_path, year, column, column_label, title, output_file, output_dir):
    """
    Create a map where states are filled with different colors based on treatment group,
    and the intensity of the color shows the outcome variable value.
    
    Parameters:
    -----------
    df : DataFrame
        The tobacco data
    shapefile_path : str
        Path to the US states shapefile
    year : int
        Year to visualize (e.g., 2011 or 2020)
    column : str
        Column name to visualize (e.g., 'current_smoker_prev')
    column_label : str
        Label for the legend (e.g., 'Smoking Prevalence (%)')
    title : str
        Title for the map
    output_file : str
        Filename for saving the visualization
    output_dir : str
        Directory for saving the visualization
    """
    # Load the US states shapefile
    us_states = gpd.read_file(shapefile_path)
    
    # Convert state FIPS codes for joining
    us_states['_state'] = us_states['STATEFP'].astype(int)
    
    # Filter to continental US (exclude Alaska, Hawaii, territories)
    continental_us = us_states[~us_states['STUSPS'].isin(['AK', 'HI', 'PR', 'VI', 'GU', 'MP', 'AS'])]
    
    # Filter data for the specified year
    year_data = df[df['year'] == year]
    
    # Merge with shapefile
    merged_data = continental_us.merge(year_data, on='_state', how='left')
    
    # Create figure
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # First, draw all states with a light border
    continental_us.plot(
        ax=ax,
        color=COLORS['no_data'],
        edgecolor=COLORS['border'],
        linewidth=0.5,
    )
    
    # Create separate dataframes for each treatment group
    nrt_med_states = merged_data[merged_data['treatment_group'] == 2].copy()
    all_three_states = merged_data[merged_data['treatment_group'] == 4].copy()
    
    # Get min and max values for normalization
    vmin = df[column].min()
    vmax = df[column].max()
    norm = Normalize(vmin=vmin, vmax=vmax)
    
    # Create custom colormaps for each treatment group
    nrt_med_cmap = LinearSegmentedColormap.from_list('nrt_med_cmap', 
                                                    [COLORS['nrt_med_low'], 
                                                     COLORS['nrt_med_high']])
    
    all_three_cmap = LinearSegmentedColormap.from_list('all_three_cmap', 
                                                      [COLORS['all_three_low'], 
                                                       COLORS['all_three_high']])
    
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
    
    # Create color bar patches for the legend
    # For NRT+Med
    nrt_med_low_patch = mpatches.Patch(facecolor=COLORS['nrt_med_low'], 
                                     label=f'NRT + Medication (Low {column_label})')
    nrt_med_high_patch = mpatches.Patch(facecolor=COLORS['nrt_med_high'], 
                                      label=f'NRT + Medication (High {column_label})')
    
    # For All Three
    all_three_low_patch = mpatches.Patch(facecolor=COLORS['all_three_low'], 
                                       label=f'NRT + Med + Counseling (Low {column_label})')
    all_three_high_patch = mpatches.Patch(facecolor=COLORS['all_three_high'], 
                                        label=f'NRT + Med + Counseling (High {column_label})')
    
    # Add the legend
    ax.legend(
        handles=[nrt_med_low_patch, nrt_med_high_patch, 
                all_three_low_patch, all_three_high_patch], 
        loc='lower right', 
        frameon=True,
        fontsize=9
    )
    
    # Set title
    ax.set_title(title, fontsize=16)
    ax.set_axis_off()
    
    # Add note about data source and value range
    plt.figtext(0.5, 0.01, 
               f'Data: State-level Medicaid tobacco cessation coverage analysis\n'
               f'Value range: {vmin:.1f}% to {vmax:.1f}%',
               ha='center', fontsize=9, style='italic')
    
    # Adjust layout
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    
    # Save figure
    map_file = os.path.join(output_dir, output_file)
    plt.savefig(map_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Map saved to {map_file}")

def main():
    """Main function to execute the map visualizations."""
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
    
    # Create four separate map visualizations
    print("\nCreating map visualizations...")
    
    # Smoking Prevalence 2011
    create_filled_color_map(
        df=df,
        shapefile_path=shapefile_path,
        year=2011,
        column='current_smoker_prev',
        column_label='Smoking Prevalence',
        title='Smoking Prevalence by State (2011)',
        output_file='map_1_smoking_2011.png',
        output_dir=output_dir
    )
    
    # Smoking Prevalence 2020
    create_filled_color_map(
        df=df,
        shapefile_path=shapefile_path,
        year=2020,
        column='current_smoker_prev',
        column_label='Smoking Prevalence',
        title='Smoking Prevalence by State (2020)',
        output_file='map_2_smoking_2020.png',
        output_dir=output_dir
    )
    
    # Quit Success Rate 2011
    create_filled_color_map(
        df=df,
        shapefile_path=shapefile_path,
        year=2011,
        column='past_year_quit_attempt_prev',
        column_label='Quit Success Rate',
        title='Quit Success Rate by State (2011)',
        output_file='map_3_quit_success_2011.png',
        output_dir=output_dir
    )
    
    # Quit Success Rate 2020
    create_filled_color_map(
        df=df,
        shapefile_path=shapefile_path,
        year=2020,
        column='past_year_quit_attempt_prev',
        column_label='Quit Success Rate',
        title='Quit Success Rate by State (2020)',
        output_file='map_4_quit_success_2020.png',
        output_dir=output_dir
    )
    
    print("\nAll map visualizations completed successfully!")
    print("The following files were created:")
    print("  - map_1_smoking_2011.png")
    print("  - map_2_smoking_2020.png")
    print("  - map_3_quit_success_2011.png")
    print("  - map_4_quit_success_2020.png")

if __name__ == "__main__":
    main()