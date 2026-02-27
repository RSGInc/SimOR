import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import importlib
import os

pd.set_option('display.max_columns', None)
os.chdir(os.path.dirname(os.path.dirname(__file__)))

import src.visualize as viz
importlib.reload(viz)

# %%
def pct_summary(df, col='biker_type', weight_col='person_weight', label=None):
    """Return weighted percent share of each category."""
    weighted = (
        df.groupby(col, observed=True)[weight_col]
        .sum()
        .div(df[weight_col].sum())
        .mul(100)
    )
    return weighted.rename(label)

def classify_bikers(df, comfort_cols):
    """Classify and reclassify bikers, tracking weighted % change after each step."""

    biker_types = [
        'NoWayNoHow',
        'InterestedButConcerned',
        'EnthusedAndConfident',
        'StrongAndFearless'
    ]
    
    biker_type_map = {
        'Never': biker_types[0],
        '<1month': biker_types[1],
        '1-3month': biker_types[1],
        '1day': biker_types[2],
        '2days': biker_types[2],
        '3days': biker_types[2],
        '4days': biker_types[3],
        '5days': biker_types[3],
        '6-7days': biker_types[3],
    }
    
    # Step 0: Initial classification
    df['biker_type'] = df['bike_freq_lab'].map(biker_type_map)
    pct_table = pct_summary(df, label='initial')
    
    # Step 1: Reclassify based on actual frequency
    df.loc[(df['biker_type'] == 'Never') & (df['bike_trips'] > 0), 'biker_type'] = biker_types[1]
    df.loc[(df['biker_type'] == biker_types[2]) & (df['bike_trips'] == 0), 'biker_type'] = biker_types[1]
    df.loc[(df['biker_type'] == biker_types[3]) & (df['bike_trips'] == 0), 'biker_type'] = biker_types[1]
    df.loc[(df['biker_type'] == biker_types[3]) & (df['bike_trips'] < 2), 'biker_type'] = biker_types[2]
    pct_table = pd.concat([pct_table, pct_summary(df, label='after_actual_freq')], axis=1)
    
    # Step 2: Reclassify based on Bike Attitude
    print(f"Attitudes before att: {df['bike_att'].unique()}")
    mask = df['biker_type'].isin(biker_types[1:])
    df.loc[mask & df['bike_att'].isin(['NotInterested', 'PhysicallyUnable']), 'biker_type'] = 'NoWayNoHow'
    pct_table = pd.concat([pct_table, pct_summary(df, label='after_att')], axis=1)
    
    # Step 3: Reclassify based on Bike Comfort
    df.loc[
        (df['biker_type'] == biker_types[2]) &
        (~df['bike_comfort_four_lanes'].isin([3, 4])),
        'biker_type'
    ] = biker_types[1]

    df.loc[
        (df['biker_type'] == biker_types[3]) &
        (~df[comfort_cols] == 4).all(axis=1),
        'biker_type'
    ] = biker_types[2]

    pct_table = pd.concat([pct_table, pct_summary(df, label='after_comfort')], axis=1)

    # Step 4: Reclassify by Bike Ownership
    mask = df['biker_type'].isin(biker_types[1:])
    df.loc[mask & (df['num_bicycle_adult'] == 0), 'biker_type'] = 'InterestedButConcerned'
    pct_table = pd.concat([pct_table, pct_summary(df, label='after_ownership')], axis=1)

    # Final tidy-up
    pct_table = pct_table.reindex(biker_types)
    pct_table = pct_table.fillna(0).round(2)

    return df, pct_table
# %%
# Define directories
data_dir = 'data'
raw_dir = f'{data_dir}/raw'
interim_dir = f'{data_dir}/interim'
processed_dir = f'{data_dir}/processed'
# %%
# Load data
person_btrips = pd.read_csv(f'{interim_dir}/person_btrips.csv')
# %% ============
# Clean dataframe
df = person_btrips.copy()

# Keep complete records only 
print(f"Total records before: {df.shape[0]:,}")
print(f"Total persons before: {df['person_weight'].sum():,.2f}")

comfort_cols = [col for col in df.columns if 'bike_comfort' in col]
df = df[df['bike_complete_flag'] == 1] # defined in 01_cleaning.py
df = df[df['bike_freq_lab'] != 'Missing']
df = df[~(df[comfort_cols] == 995).all(axis=1)] # Remove missing

print(f"Total records after: {df.shape[0]:,}")
print(f"Total persons after: {df['person_weight'].sum():,.2f}")

# %%
# Classify
df_classified, tbl = classify_bikers(df, comfort_cols)
# %% ==============
# Analysis
age_within = viz.weighted_crosstab(df, 'biker_type', 'age_bin', 'person_weight', 'col')
age_across = viz.weighted_crosstab(df, 'biker_type', 'age_bin', 'person_weight', 'row')

viz.plot_stacked(age_within, 'Age Distribution Within Each Biker Type')
viz.plot_stacked(age_across, 'Biker Type Distribution Across Age Groups')
# %%
gender_within = viz.weighted_crosstab(df, 'biker_type', 'gender_bin', 'person_weight', 'col')
gender_across = viz.weighted_crosstab(df, 'biker_type', 'gender_bin', 'person_weight', 'row')
viz.plot_stacked(gender_within, 'Gender Distribution Within Each Biker Type')
viz.plot_stacked(gender_across, 'Biker Type Distribution Across Gender Groups')

# %%
income_within = viz.weighted_crosstab(df, 'biker_type', 'income_bin', 'person_weight', 'col')
income_across = viz.weighted_crosstab(df, 'biker_type', 'income_bin', 'person_weight', 'row')
viz.plot_stacked(income_within, 'Income Distribution Within Each Biker Type')
viz.plot_stacked(income_across, 'Biker Type Distribution Across Income')
