import pandas as pd
import numpy as np
import os

# Set working directory 
work_dir = "C:/Users/james/Desktop/Second Year Paper/BRFSS Data"
os.chdir(work_dir)

def merge_brfss_data():
    print("Starting BRFSS data merge process...")
    
    # Create empty list to hold all dataframes
    dfs = []
    
    # Import Stata files for all years
    for year in range(2011, 2021):
        print(f"Loading BRFSS data for {year}...")
        
        # Load the data file
        df = pd.read_stata(f"data{year}.dta")
        
        # Add year variable if not present
        if 'year' not in df.columns:
            df['year'] = year
            
        # Keep only relevant variables
        keep_vars = ['_state', 'smoke100', 'smokday2', 'stopsmk2', 'lastsmk2', 
                     'income2', '_incomg', 'sex', 'educa', 'race2', 'marital', 
                     '_ageg5yr', 'employ', '_wt2', 'children', 'pregnant', '_llcpwt', 
                     '_ststr', '_psu', 'numadult', 'hhadult', 'year']
        
        # Filter to variables that exist in the dataframe
        available_vars = [var for var in keep_vars if var in df.columns]
        df = df[available_vars]
        
        # Add to list of dataframes
        dfs.append(df)
        print(f"Successfully loaded data for {year}")
    
    # Combine all years
    print("Combining data from all years...")
    combined_data = pd.concat(dfs, ignore_index=True)
    print(f"Combined data shape: {combined_data.shape}")
    
    # Step 1: Load FIPS code mapping and merge with combined data
    print("Loading and merging FIPS code mapping...")
    fips_mapping = pd.read_stata("fips_gnis_mapping.dta")
    # In the Stata script, fips_gnis_mapping.dta has _state and state_name
    combined_data = combined_data.merge(fips_mapping, on='_state', how='inner')
    
    # Step 2: Load and merge Medicaid expansion data
    print("Merging with Medicaid expansion data...")
    medicaid_expansion = pd.read_stata("medicaid_expansion.dta")
    combined_data = combined_data.merge(medicaid_expansion, on='_state', how='left')
    
    # Step 3: Load Cessation Treatments Coverage data
    print("Merging with Cessation Treatments Coverage data...")
    # In the Stata script, this file has state_name (not _state) and year as keys
    cessation_data = pd.read_stata("Cessation_Treatments_Coverage.dta")
    combined_data = combined_data.merge(cessation_data, on=['state_name', 'year'], how='left')
    
    # Step 4: Filter out states with _state > 56
    combined_data = combined_data[combined_data['_state'] <= 56]
    
    # Step 5: Load and merge Smokefree Indoor Air Bar data
    print("Merging with Smokefree Indoor Air Bar data...")
    sia_bar = pd.read_stata("Smokefree Indoor Air Bar.dta")
    # This file has state_name and year as keys
    combined_data = combined_data.merge(sia_bar, on=['state_name', 'year'], how='inner')
    
    # Step 6: Load and merge Smokefree Indoor Air Private Worksites data
    print("Merging with Smokefree Indoor Air Private Worksites data...")
    sia_worksites = pd.read_stata("Smokefree Indoor Private Worksites.dta")
    combined_data = combined_data.merge(sia_worksites, on=['state_name', 'year'], how='inner')
    
    # Step 7: Load and merge Smokefree Indoor Air Restaurants data
    print("Merging with Smokefree Indoor Air Restaurants data...")
    sia_restaurants = pd.read_stata("Smokefree Indoor Air Restaurants.dta")
    combined_data = combined_data.merge(sia_restaurants, on=['state_name', 'year'], how='inner')
    
    # Step 8: Load and merge Cigarette Tax Per Pack data
    print("Merging with Cigarette Tax Per Pack data...")
    cig_tax = pd.read_stata("CigTax_PerPack.dta")
    combined_data = combined_data.merge(cig_tax, on=['state_name', 'year'], how='inner')
    
    # Create consistent adults variable
    print("Creating consistent adults variable...")
    combined_data['totaladult'] = np.nan
    
    # For 2011-2013, use numadult
    mask_2011_2013 = combined_data['year'].between(2011, 2013)
    combined_data.loc[mask_2011_2013, 'totaladult'] = combined_data.loc[mask_2011_2013, 'numadult']
    
    # For 2014-2020, use numadult if available, otherwise hhadult
    mask_2014_2020 = combined_data['year'].between(2014, 2020)
    
    # First use numadult if available
    mask_numadult = mask_2014_2020 & combined_data['numadult'].notna()
    combined_data.loc[mask_numadult, 'totaladult'] = combined_data.loc[mask_numadult, 'numadult']
    
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
    combined_data['income_upper'] = combined_data['income2'].map(income_upper_dict)
    
    # Calculate FPL percentage
    combined_data['fpl_percent'] = np.round((combined_data['income_upper'] / combined_data['fpl_threshold']) * 100)
    
    # Create Medicaid eligibility indicator
    combined_data['Medicaidelig'] = (combined_data['fpl_percent'] <= 100).astype(int)
    
    # Apply final filters
    print("Applying final sample filters...")
    
    # Keep only Medicaid eligible
    combined_data = combined_data[combined_data['Medicaidelig'] == 1]
    
    # Filter for no children
    combined_data = combined_data[combined_data['children'] == 88]
    
    # Keep only males and females
    combined_data = combined_data[combined_data['sex'].isin([1, 2])]
    
    # Save the final dataset
    print("Saving final dataset...")
    csv_path = os.path.join(work_dir, "Final_2011_2020_Medicaidelig.csv")
    combined_data.to_csv(csv_path, index=False)
    
    # Save as Stata .dta file
    dta_path = os.path.join(work_dir, "Final_2011_2020_Medicaidelig.dta")
    combined_data.to_stata(dta_path, write_index=False)
    
    return combined_data

if __name__ == "__main__":
    merge_brfss_data()