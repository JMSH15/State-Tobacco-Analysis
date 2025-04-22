import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# Set working directory 
work_dir = "C:/Users/james/Desktop/Second Year Paper/BRFSS Data"
os.chdir(work_dir)

def clean_brfss_data_from_stata():
    print("Starting BRFSS data cleaning from Stata files...")
    
    dfs = []
    
    # Import Stata files
    for year in range(2011, 2021):
        print(f"Processing BRFSS data for {year}...")
        
        try:

            df = pd.read_stata(f"data{year}.dta")
            
            # Add year variable if it doesn't exist
            if 'year' not in df.columns:
                df['year'] = year
                
            # Keep only relevant variables
            keep_vars = ['_state', 'smoke100', 'smokday2', 'stopsmk2', 'lastsmk2', 
                         'income2', '_incomg', 'sex', 'educa', 'race2', 'marital', 
                         '_ageg5yr', 'employ', '_wt2', 'children', 'pregnant', '_llcpwt', 
                         '_ststr', '_psu', 'numadult', 'hhadult', 'year']
            
            # Filter variables that exist in the dataframe
            available_vars = [var for var in keep_vars if var in df.columns]
            df = df[available_vars]
            
            # Append to the list of dataframes
            dfs.append(df)
            print(f"Successfully processed data for {year}")
            
        except Exception as e:
            print(f"Error processing {year}: {e}")
    
    # Combine all years
    print("Combining data from all years...")
    combined_data = pd.concat(dfs, ignore_index=True)
    print(f"Combined data shape: {combined_data.shape}")
    
    # Load Medicaid expansion data
    print("Loading Medicaid expansion data...")
    try:
        
        medicaid_expansion = pd.read_stata("medicaid_expansion.dta")
    except Exception as e:
        print(f"Error loading Medicaid expansion data: {e}")
        # Create the data manually
        medicaid_expansion = pd.DataFrame({
            'state_name': [
                "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", 
                "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia", 
                "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", 
                "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", 
                "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire", 
                "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", 
                "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", 
                "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", 
                "Washington", "Wisconsin", "Wyoming"
            ],
            '_state': [
                1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23, 
                24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 
                42, 44, 45, 46, 47, 48, 49, 50, 51, 53, 55, 56
            ],
            'expansion': [
                0, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 
                0, 0, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0
            ]
        })
    
    # Merge with Medicaid expansion data
    print("Merging with Medicaid expansion data...")
    combined_data = combined_data.merge(medicaid_expansion, on='_state', how='left')
    
    # Load FIPS code mapping
    print("Loading FIPS code mapping...")
    try:
        # Try to read the Stata file
        fips_mapping = pd.read_stata("fips_gnis_mapping.dta")
    except Exception as e:
        print(f"Error loading FIPS mapping: {e}")
        # Use the medicaid_expansion data as a fallback
        fips_mapping = medicaid_expansion[['_state', 'state_name']].copy()
        
    # Load Medicaid cessation treatment coverage data
    print("Loading Medicaid cessation treatment coverage data...")
    try:
        # Try to read the Stata file
        cessation_data = pd.read_stata("Cessation_Treatments_Coverage_2011_2020.dta")
    except Exception as e:
        print(f"Error loading cessation data: {e}")
        print("Skipping cessation data merge...")
        cessation_data = None
    
    
    # Create consistent adults variable
    print("Creating consistent adults variable...")
    combined_data['totaladult'] = np.nan
    
    # For 2011-2013, use numadult
    mask_2011_2013 = combined_data['year'].between(2011, 2013)
    if 'numadult' in combined_data.columns:
        combined_data.loc[mask_2011_2013, 'totaladult'] = combined_data.loc[mask_2011_2013, 'numadult']
    
    # For 2014-2020, use numadult if available, otherwise hhadult
    mask_2014_2020 = combined_data['year'].between(2014, 2020)
    
    if 'numadult' in combined_data.columns:
        # First use numadult if available
        mask_numadult = mask_2014_2020 & combined_data['numadult'].notna()
        combined_data.loc[mask_numadult, 'totaladult'] = combined_data.loc[mask_numadult, 'numadult']
    
    if 'hhadult' in combined_data.columns:
        # Then use hhadult for those where numadult is missing
        mask_hhadult = mask_2014_2020 & combined_data['numadult'].isna() & combined_data['hhadult'].notna()
        combined_data.loc[mask_hhadult, 'totaladult'] = combined_data.loc[mask_hhadult, 'hhadult']
    
    # Calculate Federal Poverty Level (FPL)
    print("Calculating Federal Poverty Level thresholds...")
    # Create FPL base amounts by year
    fpl_base_dict = {
        2011: 10890, 2012: 11170, 2013: 11490, 2014: 11670, 2015: 11770,
        2016: 11880, 2017: 12060, 2018: 12140, 2019: 12490, 2020: 12760
    }
    combined_data['fpl_base'] = combined_data['year'].map(fpl_base_dict)
    
    # Create FPL additional person amounts by year
    fpl_additional_dict = {
        2011: 3820, 2012: 3960, 2013: 4020, 2014: 4060, 2015: 4160,
        2016: 4160, 2017: 4180, 2018: 4320, 2019: 4420, 2020: 4480
    }
    combined_data['fpl_additional'] = combined_data['year'].map(fpl_additional_dict)
    
    # Calculate household FPL threshold
    combined_data['fpl_threshold'] = combined_data['fpl_base'] + (combined_data['fpl_additional'] * (combined_data['totaladult'] - 1))
    
    # Generate income upper bounds based on income2
    income_upper_dict = {
        1: 10000, 2: 15000, 3: 20000, 4: 25000, 5: 35000, 6: 50000, 7: 75000, 8: 100000
    }
    if 'income2' in combined_data.columns:
        combined_data['income_upper'] = combined_data['income2'].map(income_upper_dict)
    else:
        print("Warning: income2 not found, using default value")
        combined_data['income_upper'] = 15000  # Default value for testing
    
    # Calculate FPL percentage
    combined_data['fpl_percent'] = np.round((combined_data['income_upper'] / combined_data['fpl_threshold']) * 100)
    
    # Create Medicaid eligibility indicator
    combined_data['Medicaidelig'] = (combined_data['fpl_percent'] <= 100).astype(int)
    
    # Final filters
    print("Applying final sample filters...")
    
    # Keep only Medicaid eligible
    combined_data = combined_data[combined_data['Medicaidelig'] == 1]
    
    # Filter for children == 88 (no children)
    if 'children' in combined_data.columns:
        combined_data = combined_data[combined_data['children'] == 88]
    
    # Keep only males and females (sex == 1 or sex == 2)
    if 'sex' in combined_data.columns:
        combined_data = combined_data[combined_data['sex'].isin([1, 2])]
    
    # Save the final dataset
    print("Saving final dataset...")
    final_path = os.path.join(work_dir, "Final_2011_2020_Medicaidelig.csv")
    combined_data.to_csv(final_path, index=False)
    
    print(f"Data processing complete. Final dataset saved to {final_path}")
    print(f"Final dataset shape: {combined_data.shape}")
    
    return combined_data

if __name__ == "__main__":
    clean_brfss_data_from_stata()