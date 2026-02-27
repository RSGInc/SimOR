import pandas as pd
import numpy as np
import os
pd.set_option('display.max_columns', None)
os.chdir(os.path.dirname(os.path.dirname(__file__)))

# %%
# Directories
data_dir = 'data'
raw_dir = f'{data_dir}/raw'
interim_dir = f'{data_dir}/interim'
processed_dir = f'{data_dir}/processed'

# %%
# Load data
hh = pd.read_csv(f'{raw_dir}/ex_hh.csv')
# day = pd.read_csv(f'{raw_dir}/ex_day.csv')
person = pd.read_csv(f'{raw_dir}/ex_person.csv')
trips = pd.read_csv(f'{raw_dir}/ex_trip_unlinked.csv')
ltrips = pd.read_csv(f'{raw_dir}/ex_trip_linked.csv')

# %% Rename variables
ltrips.rename(
    columns=
    {'linked_trip_weight': 'ltrip_weight'},
    inplace=True
)

# Re-map values to labels
person_mapping = {
    'gender': {1: 'Female', 2: 'Male', 3:'Non-binary', 995:'Missing', 997:'Other', 999:'PNTA'},
    'age': {1:'Under5', 2:'5-10', 3:'11-15', 4:'16-17', 5:'18-24', 6:'25-34', 7:'35-44', 8:'45-54', 9:'55-64', 10:'65-74', 11:'75-84', 12:'85plus'},
    'bike_freq': {1: '6-7days', 2: '5days', 3: '4days', 4: '3days', 5: '2days',  6: '1day', 7: '1-3month', 8: '<1month', 996: 'Never', 995: 'Missing'},
    'bike_attitude': {1:'PhysicallyUnable', 2:'DoesNotKnowHow', 3:'NotInterested', 4:'WantBikeLess', 5:'HappyWithCurrent', 6:'WantBikeMore', 995:'Missing'}
}

# Re-map to broader categories
bike_freq_map = {
    '6-7days': 'VeryFrequent',
    '5days': 'VeryFrequent',
    '4days': 'VeryFrequent',
    '3days': 'Occasional',
    '2days': 'Occasional',
    '1day': 'Occasional',
    '1-3month': 'Infrequent',
    '<1month': 'Infrequent',
    'Never': 'Never',
    'Missing': 'Missing'
}

bike_att_bin = {
    'PhysicallyUnable': 'NotInterestedCant',
    'DoesNotKnowHow': 'NotInterestedCant',
    'NotInterested': 'NotInterestedCant',
    'WantBikeLess': 'WantBikeLess',
    'HappyWithCurrent': 'HappyWithCurrent',
    'WantBikeMore': 'WantBikeMore',
    'Missing': 'Missing'
}

income_bin = {
    1: 'Low',
    2: 'Low',
    3: 'Mid',
    4: 'Mid',
    5: 'High',
    6: 'High',
    995: 'Missing',
    999: 'Missing'
}

income_num = {
    1: 25000,
    2: 37500,
    3: 62500,
    4: 87500,
    5: 150000,
    6: 200000,
    995: np.nan,
    999: np.nan
}

age_bin = {
    'Under5': 'Under10',
    '5-10': 'Under10',
    '11-15': '10-17',
    '16-17': '10-17',
    '18-24': '18-34',
    '25-34': '18-34',
    '35-44': '35-64',
    '45-54': '35-64',
    '55-64': '35-64',
    '65-74': '65+',
    '75-84': '65+',
    '85plus': '65+'
}

age_num = {
    'Under5': 2.5,
    '5_10': 8,
    '11-15': 13,
    '16-17': 16,
    '18-24': 21,
    '25-34': 30,
    '35-44': 40,
    '45-54': 50,
    '55-64': 60,
    '65-74': 70,
    '75-84': 80,
    '85plus': 85
}

person['gender_num'] = np.where(
    person['gender'].isin([1,3,997]), 1, # Female & Others
    np.where(person['gender'] == 2, 2, 3) # Male and Missing
)
person['gender_lab'] = person['gender'].map(person_mapping['gender'])
person['gender_bin'] = person['gender_num'].map({1:'Female & Others', 2: 'Male', 3: 'Missing'})

person['age_lab'] = person['age'].map(person_mapping['age'])
person['age_bin'] = person['age_lab'].map(age_bin)
person['age_num'] = person['age_lab'].map(age_num) 

person['bike_freq_lab'] = person['bike_freq'].map(person_mapping['bike_freq'])
person['bike_freq_bin'] = person['bike_freq_lab'].map(bike_freq_map)

person['bike_att'] = person['bike_attitude'].map(person_mapping['bike_attitude'])
person['bike_att_bin'] = person['bike_att'].map(bike_att_bin)

hh['income_bin'] = hh['income_broad'].map(income_bin)
hh['income_num'] = hh['income_broad'].map(income_num)

# %%
# Define comfort variable
comfort_cols = [col for col in person.columns if 'bike_comfort' in col]
likert_scale = {1:4, 2:3, 3:2, 4:1}  # Reverse scoring for comfort
person[comfort_cols] = person[comfort_cols].replace(likert_scale)
person['avg_comfort'] = person[comfort_cols].replace(995, pd.NA).mean(axis=1, skipna=True).fillna(0)
comfort_labels = ['Uncomfortable', 'Comfortable']
person['comfort_bin'] = np.where(
    person['avg_comfort'] >= 3, 'Comfortable',
    np.where(person['avg_comfort'] != 0 , 'Uncomfortable', pd.NA)
)

# %%
# Identify complete rmove households (for comfort classification - 04_classify.py)
print(f"Total households: {hh['hh_weight'].sum():,.2f}")

hh_rmove = hh[hh['diary_platform'] == 'rmove']
print(f"Total households with rmove: {hh_rmove['hh_weight'].sum():,.2f}")

hh_rmove_complete = hh_rmove[hh_rmove['num_days_complete'] == 7]
print(f"Total number of households with 7 complete days: {hh_rmove_complete['hh_weight'].sum():,.2f}")
print(f"Total sample size of households with 7 complete days: {hh_rmove_complete.shape[0]:,}")

bike_complete_hh_ids = hh_rmove_complete['hh_id'].unique().tolist()

# Add flag to identify complete records
person['bike_complete_flag'] = 0
person.loc[person['hh_id'].isin(bike_complete_hh_ids), 'bike_complete_flag'] = 1

# %% Merge bike trips with person table
# Count bike trips
bike_trip_mask = (ltrips['linked_trip_mode'] == 11)
bike_trips= ltrips[bike_trip_mask].copy()
bike_counts = bike_trips.groupby('person_id').size().reset_index(name='bike_trips')

# Keep relevant cols
per_cols = ['hh_id', 'person_id', 'age_lab', 'age_bin', 'age_num', 
            'gender_bin', 'num_days_complete', 'bike_complete_flag',
            'avg_comfort', 'comfort_bin',
            'student', 'person_weight']
bike_cols_per = [col for col in person.columns if 'bike' in col]

# Merge bike trip info with person data
person_btrips = pd.merge(
    person[per_cols + bike_cols_per],
    bike_counts,
    on='person_id',
    how='left',
    validate='1:1'
).fillna({'bike_trips': 0})

# Merge with hh data
hh_cols = ['hh_id', 'num_bicycle_adult', 'num_bicycle_child', 'income_broad', 'income_bin', 'income_num']
person_btrips = pd.merge(
    person_btrips,
    hh[hh_cols],
    on = 'hh_id',
    how = 'left'
)

# Add dummy if person reported bike trip
person_btrips['recorded_btrip'] = np.where(person_btrips['bike_trips'] > 0, 1, 0)

# %% Merge bike trips with person info
btrips_person = pd.merge(
    bike_trips.drop(columns = ['hh_id']),
    person[per_cols + bike_cols_per],
    how = 'left',
    on = 'person_id'
)

# Add hh data
btrips_person = pd.merge(
    btrips_person,
    hh[hh_cols],
    how = 'left',
    on = 'hh_id'
)

# Add bike type to bike trip info
ltrip_bike_ids = bike_trips['linked_trip_id'].to_list()
subset = trips[trips['linked_trip_id'].isin(ltrip_bike_ids)] # bike type is unlinked trip table

bike_modes = [2, 3, 4, 5, 69, 70, 82, 103, 300] # bike modes and hierarchy

def get_highest_bike_mode(modes):
    found_bikes = [m for m in modes if m in bike_modes]
    if found_bikes:
        return max(found_bikes)   
    else:
        return None 

modes = subset.groupby('linked_trip_id')['mode_1'].agg(list).reset_index().rename(columns = {'mode_1':'mode_list'})
modes['bike_mode'] = modes['mode_list'].apply(get_highest_bike_mode)

# Add bike type
btrips_person = pd.merge(
    btrips_person,
    modes[['linked_trip_id', 'bike_mode']],
    how = 'left',
    on = 'linked_trip_id',
)

ebikes = [70, 82] # ebike from bikeshare, ebike in household
btrips_person['bike_type'] = np.where(btrips_person['bike_mode'].isin(ebikes), 'ebike', 'standard')

# %% Export
person_btrips.to_csv(f'{interim_dir}/person_btrips.csv', index=False)
btrips_person.to_csv(f'{interim_dir}/btrips_person.csv', index=False)
