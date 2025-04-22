import pandas as pd
import numpy as np
import os

# Set file path to the data
file_path = "C:\\Users\\James\\Desktop\\Github\\State-Tobacco-Analysis\\Final_2011_2020_Medicaidelig.csv"

# Load the dataset
df = pd.read_csv(file_path)

# Rename Medicaidelig to medicaidelig to match STATA code
df.rename(columns={'Medicaidelig': 'medicaidelig'}, inplace=True)

# Restrict to the relevant time period (before COVID-19)
df = df[df['year'] <= 2020]


###############################################################################
#                   STEP 1: CLEAN INDIVIDUAL-LEVEL DATA                       #
###############################################################################

# Keep only the necessary variables
variables_to_keep = [
    '_state', 'year', 'state_name', '_llcpwt', 'smoke100', 'smokday2', 
    'lastsmk2', 'stopsmk2', 'sex', '_ageg5yr', 'race2', 'educa', 'employ', 
    'income2', '_incomg', 'fpl_percent', 'pregnant', 'children', 'medicaidelig',
    'individual_counseling', 'group_counseling', 'nicotine_patch', 'nicotine_gum',
    'nicotine_lozenge', 'nicotine_nasal_spray', 'nicotine_inhaler',
    'bupropion', 'varenicline'
]
df = df[variables_to_keep]

# Clean smoking status variables
# Drop observations with missing values for key smoking variables
df = df[(df['smoke100'] < 7) & (~df['smoke100'].isna())]  # Invalid or missing responses
df['smokday2'] = df['smokday2'].fillna(3)  # replace missing with 'No'
df = df[df['smokday2'] < 7]  # Invalid responses to current smoking frequency
df = df[(df['lastsmk2'] != 77) & (df['lastsmk2'] != 99) | (df['lastsmk2'].isna())]

# Create smoking status variables
# Current smoker
df['current_smoker'] = ((df['smoke100'] == 1) & 
                        ((df['smokday2'] == 1) | (df['smokday2'] == 2))).astype(int)

# Former smoker
df['former_smoker'] = ((df['smoke100'] == 1) & (df['smokday2'] == 3)).astype(int)

# Never smoker
df['never_smoker'] = (df['smoke100'] == 2).astype(int)

# Create quit attempt variables
# Current smoker quit attempts
df['quit_attempt'] = 0
df.loc[(df['stopsmk2'] == 1) & (df['current_smoker'] == 1), 'quit_attempt'] = 1

# Recent quitters (former smokers who quit within past year)
df['recent_quitter'] = 0
df.loc[(df['lastsmk2'] <= 4) & (df['former_smoker'] == 1), 'recent_quitter'] = 1
df.loc[((df['lastsmk2'] >= 77) | (df['lastsmk2'].isna())) & 
       (df['former_smoker'] == 1), 'recent_quitter'] = 0

# Combined quit attempt variable
df['past_year_quit_attempt'] = 0
df.loc[df['recent_quitter'] == 1, 'past_year_quit_attempt'] = 1

# Create demographic and control variables
# Demographics
df['low_education'] = ((df['educa'] < 4) & (df['educa'] < 9)).astype(int)
df['unemployed'] = ((df['employ'] > 2) & (df['employ'] < 9)).astype(int)
df['low_income'] = (df['fpl_percent'] <= 100).astype(int)
df['male'] = (df['sex'] == 1).astype(int)
df['white'] = (df['race2'] == 1).astype(int)
df['black'] = (df['race2'] == 2).astype(int)
df['hispanic'] = (df['race2'] == 8).astype(int)

# Age category indicators
df['age_18_24'] = ((df['_ageg5yr'] == 1) & (df['_ageg5yr'] < 14)).astype(int)
df['age_25_34'] = (((df['_ageg5yr'] == 2) | (df['_ageg5yr'] == 3)) & 
                  (df['_ageg5yr'] < 14)).astype(int)
df['age_35_44'] = (((df['_ageg5yr'] == 4) | (df['_ageg5yr'] == 5)) & 
                  (df['_ageg5yr'] < 14)).astype(int)
df['age_45_54'] = (((df['_ageg5yr'] == 6) | (df['_ageg5yr'] == 7)) & 
                  (df['_ageg5yr'] < 14)).astype(int)
df['age_55_64'] = (((df['_ageg5yr'] == 8) | (df['_ageg5yr'] == 9)) & 
                  (df['_ageg5yr'] < 14)).astype(int)

# Smoke-free air law binary indicators are removed as requested


###############################################################################
#               STEP 2: CREATE TREATMENT CATEGORY VARIABLES                   #
###############################################################################

# Generate binary variables for each treatment
treatment_vars = [
    'nicotine_patch', 'nicotine_gum', 'nicotine_lozenge', 'nicotine_nasal_spray',
    'nicotine_inhaler', 'bupropion', 'varenicline', 'individual_counseling',
    'group_counseling'
]

for var in treatment_vars:
    df[f'{var}_covered'] = ((df[var] == "Yes") | (df[var] == "Varies")).astype(int)

# Create category-specific coverage indicators
# NRT category
df['any_nrt'] = ((df['nicotine_patch_covered'] == 1) | 
                 (df['nicotine_gum_covered'] == 1) |
                 (df['nicotine_lozenge_covered'] == 1) | 
                 (df['nicotine_nasal_spray_covered'] == 1) |
                 (df['nicotine_inhaler_covered'] == 1)).astype(int)

# Medication category
df['any_medication'] = ((df['bupropion_covered'] == 1) | 
                        (df['varenicline_covered'] == 1)).astype(int)

# Counseling category
df['any_counseling'] = ((df['individual_counseling_covered'] == 1) | 
                        (df['group_counseling_covered'] == 1)).astype(int)

# Define output directory
output_dir = "C:\\Users\\James\\Desktop\\Github\\State-Tobacco-Analysis"

# Save individual-level dataset before collapsing
df.to_csv(os.path.join(output_dir, "individual_level_with_category_indicators.csv"), index=False)


###############################################################################
#                  STEP 3: AGGREGATE TO STATE-LEVEL DATA                      #
###############################################################################

# Create a count variable for each observation
df['count_all'] = 1

# Calculate outcome variables
# Current smoking prevalence
current_smoker_df = df.groupby(['_state', 'year', 'state_name']).apply(
    lambda x: pd.Series({
        'current_smoker_count': np.sum(x['current_smoker'] * x['_llcpwt']),
        'total_count': np.sum(x['count_all'] * x['_llcpwt'])
    })
).reset_index()

current_smoker_df['current_smoker_prev'] = (current_smoker_df['current_smoker_count'] / 
                                           current_smoker_df['total_count'])

# Past-year quit attempt prevalence in total population
quit_attempt_df = df.groupby(['_state', 'year', 'state_name']).apply(
    lambda x: pd.Series({
        'past_year_quit_attempt_count': np.sum(x['past_year_quit_attempt'] * x['_llcpwt']),
        'total_count': np.sum(x['count_all'] * x['_llcpwt'])
    })
).reset_index()

quit_attempt_df['past_year_quit_attempt_prev'] = (quit_attempt_df['past_year_quit_attempt_count'] / 
                                                 quit_attempt_df['total_count'])

# Calculate control variables - demographics
demographics_df = df.groupby(['_state', 'year', 'state_name']).apply(
    lambda x: pd.Series({
        'male_pct': np.average(x['male'], weights=x['_llcpwt']),
        'white_pct': np.average(x['white'], weights=x['_llcpwt']),
        'black_pct': np.average(x['black'], weights=x['_llcpwt']),
        'hispanic_pct': np.average(x['hispanic'], weights=x['_llcpwt']),
        'low_educ_pct': np.average(x['low_education'], weights=x['_llcpwt']),
        'unemployed_pct': np.average(x['unemployed'], weights=x['_llcpwt']),
        'poverty_pct': np.average(x['low_income'], weights=x['_llcpwt']),
        'medicaid_elig_pct': np.average(x['medicaidelig'], weights=x['_llcpwt']),
        'age_18_24_pct': np.average(x['age_18_24'], weights=x['_llcpwt']),
        'age_25_34_pct': np.average(x['age_25_34'], weights=x['_llcpwt']),
        'age_35_44_pct': np.average(x['age_35_44'], weights=x['_llcpwt']),
        'age_45_54_pct': np.average(x['age_45_54'], weights=x['_llcpwt']),
        'age_55_64_pct': np.average(x['age_55_64'], weights=x['_llcpwt'])
    })
).reset_index()

# Policy variables - removed as requested

# Treatment category variables
treatment_df = df.groupby(['_state', 'year', 'state_name']).apply(
    lambda x: pd.Series({
        'any_nrt': x['any_nrt'].max(),
        'any_medication': x['any_medication'].max(),
        'any_counseling': x['any_counseling'].max()
    })
).reset_index()

# Population variables
population_df = df.groupby(['_state', 'year', 'state_name']).apply(
    lambda x: pd.Series({
        'weighted_pop': x['_llcpwt'].sum(),
        'sample_size': len(x)
    })
).reset_index()

# Merge all state-level datasets
state_df = current_smoker_df.merge(
    quit_attempt_df[['_state', 'year', 'state_name', 'past_year_quit_attempt_prev', 'past_year_quit_attempt_count']], 
    on=['_state', 'year', 'state_name']
).merge(
    demographics_df, 
    on=['_state', 'year', 'state_name']
).merge(
    treatment_df, 
    on=['_state', 'year', 'state_name']
).merge(
    population_df, 
    on=['_state', 'year', 'state_name']
)



###############################################################################
#               STEP 4: CREATE FOCUSED TREATMENT VARIABLES                    #
###############################################################################

# Create mutually exclusive treatment categories
state_df['treatment_group'] = 0  # No coverage (control)
state_df.loc[(state_df['any_nrt'] == 1) & (state_df['any_medication'] == 0) & 
            (state_df['any_counseling'] == 0), 'treatment_group'] = 1  # NRT only
state_df.loc[(state_df['any_nrt'] == 1) & (state_df['any_medication'] == 1) & 
            (state_df['any_counseling'] == 0), 'treatment_group'] = 2  # NRT + Med
state_df.loc[(state_df['any_nrt'] == 0) & (state_df['any_medication'] == 0) & 
            (state_df['any_counseling'] == 1), 'treatment_group'] = 3  # Counseling only
state_df.loc[(state_df['any_nrt'] == 1) & (state_df['any_medication'] == 1) & 
            (state_df['any_counseling'] == 1), 'treatment_group'] = 4  # All three

# Validation to ensure mutual exclusivity in treatment_group assignment
# Generate indicator variables for the two key treatment groups we're focusing on
state_df['nrt_med'] = (state_df['treatment_group'] == 2).astype(int)
state_df['all_three'] = (state_df['treatment_group'] == 4).astype(int)

# Restrict sample to only the relevant treatment groups
state_df = state_df[(state_df['treatment_group'] == 2) | (state_df['treatment_group'] == 4)]


###############################################################################
#                 STEP 5: FINALIZE DATA (DESCRIPTIVE ONLY)                    #
###############################################################################

# Check data coverage by state
state_coverage = state_df.groupby('_state').agg(
    min_year=('year', 'min'),
    max_year=('year', 'max')
)
state_coverage['num_years'] = state_coverage['max_year'] - state_coverage['min_year'] + 1
state_coverage['num_obs'] = state_df.groupby('_state').size()


# Track treatment status changes over time
state_df = state_df.sort_values(['_state', 'year'])

# Save the final dataset
state_df.to_csv(os.path.join(output_dir, "state_level_descriptive_data.csv"), index=False)

# Optionally, save summary statistics to a text file
with open(os.path.join(output_dir, "summary_statistics.txt"), 'w') as f:
    f.write("Treatment groups and composition:\n")
    f.write(str(state_df['treatment_group'].value_counts()) + "\n\n")
    
    f.write("Cross-tabulation of treatment group by year:\n")
    f.write(str(pd.crosstab(state_df['treatment_group'], state_df['year'])) + "\n\n")
    
    f.write("Outcome variables by treatment status:\n")
    f.write(str(state_df.groupby('treatment_group')[
        ['current_smoker_prev', 'past_year_quit_attempt_prev']
    ].agg(['mean', 'std', 'min', 'max', 'count'])) + "\n\n")

# Display some summary statistics
print("\nTreatment groups and composition:")
print(state_df['treatment_group'].value_counts())
print("\nCross-tabulation of treatment group by year:")
print(pd.crosstab(state_df['treatment_group'], state_df['year']))

print("\nOutcome variables by treatment status:")
print(state_df.groupby('treatment_group')[
    ['current_smoker_prev', 'past_year_quit_attempt_prev']
].agg(['mean', 'std', 'min', 'max', 'count']))

print("\nComplete!")