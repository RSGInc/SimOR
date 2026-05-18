import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os
import importlib

pd.set_option('display.max_columns', None)
os.chdir(os.path.dirname(os.path.dirname(__file__)))

import src.visualize as viz
importlib.reload(viz)

# %% 
# Define directories
data_dir = 'data'
raw_dir = f'{data_dir}/raw'
interim_dir = f'{data_dir}/interim'
processed_dir = f'{data_dir}/processed'
# %%
# Load data
person_btrips = pd.read_csv(f'{interim_dir}/person_btrips.csv')
btrips_person = pd.read_csv(f'{interim_dir}/btrips_person.csv')
ltrips = pd.read_csv(f'{raw_dir}/ex_trip_linked.csv')
value_labels = pd.read_csv(f'{raw_dir}/ex_value_labels.csv')

# Convert to categorical
age_lab_cat = ['Under5', '5-10', '11-15', '16-17', '18-24', '25-34', '35-44', '45-54', '55-64', '65-74', '75-84']
freq_bin_cat = ['VeryFrequent', 'Occasional', 'Infrequent', 'Never', 'Missing']
att_cat = ['PhysicallyUnable', 'DoesNotKnowHow', 'NotInterested', 'WantBikeLess', 'HappyWithCurrent', 'WantBikeMore', 'Missing']
att_bin_cat = ['NotInterestedCant', 'WantBikeLess', 'HappyWithCurrent', 'WantBikeMore', 'Missing']

person_btrips['age_lab'] = pd.Categorical(person_btrips['age_lab'], categories=age_lab_cat, ordered=True)
person_btrips['bike_freq_bin'] = pd.Categorical(person_btrips['bike_freq_bin'], categories=freq_bin_cat, ordered=True)
person_btrips['bike_att'] = pd.Categorical(person_btrips['bike_att'], categories=att_cat, ordered=True)
person_btrips['bike_att_bin'] = pd.Categorical(person_btrips['bike_att_bin'], categories=att_bin_cat, ordered=True)
# person['gender'] = pd.Categorical(person['gender'], categories=person_mapping['gender'], ordered=True)

# %% ===============
# Basic Statistics
print(f"Number of bike trips: {btrips_person['ltrip_weight'].sum():,.2f}")
print(f"Percent bike trips: {btrips_person['ltrip_weight'].sum() / ltrips['linked_trip_weight'].sum() * 100:.2f}%")

# Demographics of Revealed Bikers 
bikers = person_btrips[person_btrips['bike_trips'] > 0]
bikers_gender = viz.weighted_total(bikers, 'gender_bin', 'person_weight')
bikers_age = viz.weighted_total(bikers, 'age_lab', 'person_weight')
bikers_attitude = viz.weighted_total(bikers, 'bike_att', 'person_weight')
bikers_income = viz.weighted_total(bikers, 'income_bin', 'person_weight')

viz.plot_hist(bikers_gender, 'gender_bin', 'pct', title='Revealed Bikers by Gender')
viz.plot_hist(bikers_age, 'age_lab', 'pct', title='Revealed Bikers by Age')
viz.plot_hist(bikers_income, 'income_bin', 'pct', title='Revealed Bikers by Income')
viz.plot_hist(bikers_attitude, 'bike_att', 'pct', title='Revealed Bikers by Stated Attitude')

# Num of bike trips per day
bikers_bike_count = viz.weighted_total(bikers, 'bike_trips', 'person_weight')
bikers_bike_count['bin'] = pd.cut(bikers_bike_count['bike_trips'], bins=[-0.1,0,1,2,3,4,5,50])
bin_labels = ['0', '1', '2', '3', '4', '5', '6+']
ax = (bikers_bike_count
       .groupby('bin')['pct']
       .sum()
       .plot(kind='bar',
             color='skyblue',
             xlabel='Number of Bike Trips',
             ylabel='Pct',
             title='Bike Trips per Day by Revealed Bikers'))
ax.set_xticklabels(bin_labels, rotation=0)
ax.bar_label(ax.containers[0], fmt='%.1f')
# %%
# Bike Trips by Purpose
bike_purpose = viz.weighted_total(btrips_person, 'd_purpose_category', 'ltrip_weight')
top_purpose = bike_purpose.sort_values(by='pct', ascending=False).head(10)
labels = value_labels[value_labels['variable'] == 'd_purpose_category'][['value', 'label']]
bin_labels = labels[labels['value'].isin(top_purpose['d_purpose_category'])]['label'].tolist()

ax = top_purpose.plot(
    kind='barh', 
    x='d_purpose_category',
    y='pct', 
    color='skyblue',
    title="Bike Trips by Purpose",
    legend=False
)
ax.set_yticks(range(len(bin_labels)))
ax.set_yticklabels(bin_labels, rotation=0)
ax.bar_label(ax.containers[0], fmt='%.1f', label_type='edge')

# %% ====================
# Cross tabulations
df = person_btrips.copy()
df = df[df['comfort_bin'].notna()]

freq_vs_trips_col = viz.weighted_crosstab(df, 'bike_freq_bin', 'recorded_btrip', 'person_weight', 'col', 0)
freq_vs_trips_row = viz.weighted_crosstab(df, 'bike_freq_bin', 'recorded_btrip', 'person_weight', 'row', 0)

att_vs_trips_row = viz.weighted_crosstab(df, 'bike_att_bin', 'recorded_btrip', 'person_weight', 'row', 0)
att_vs_trips_col = viz.weighted_crosstab(df, 'bike_att_bin', 'recorded_btrip', 'person_weight', 'col', 0)

comfort_vs_trips_row = viz.weighted_crosstab(df, 'comfort_bin', 'recorded_btrip', 'person_weight', 'row', 0)
comfort_vs_trips_col = viz.weighted_crosstab(df, 'comfort_bin', 'recorded_btrip', 'person_weight', 'col', 0)

comfort_vs_att_row = viz.weighted_crosstab(df, 'bike_att_bin', 'comfort_bin', 'person_weight', 'row', 0)
comfort_vs_att_col = viz.weighted_crosstab(df, 'bike_att_bin', 'comfort_bin', 'person_weight', 'col', 0)

# %% ====================================
# Bike trip distance by reported frequency
df = btrips_person[(btrips_person['bike_freq_bin'] != 'Missing') &
                   (btrips_person['d_purpose_category'] != 14)]

bins = [0, 1, 5, 10, np.inf]
labels2 = ['<1', '1-5', '5-10', '10+']
df['dist_bin'] = pd.cut(df['distance_miles'], bins=bins, labels=labels2, right=False)

summary = []
for freq in df['bike_freq_bin'].unique():
    tbl = df[df['bike_freq_bin'] == freq].groupby('dist_bin')['ltrip_weight'].sum().reset_index()
    tbl['pct'] = tbl['ltrip_weight'] / tbl['ltrip_weight'].sum() * 100
    tbl['bike_freq_bin'] = freq
    summary.append(tbl)

summary = pd.concat(summary)

pivot = summary.pivot(index='dist_bin', columns='bike_freq_bin', values='pct').fillna(0)
pivot = pivot[df['bike_freq_bin'].unique()]

ax = pivot.plot(kind='bar', figsize=(10,6), edgecolor='black')
ax.tick_params(axis='x', rotation=0)
ax.set_xlabel('Trip distance (miles)')
ax.set_ylabel('Percent')
ax.set_title('Bike Trip Distances by Reported Frequency')
ax.legend(title='Reported Frequency')
plt.tight_layout()
plt.show()

# %% =========================
# Trip Distance by Bike Type
df = btrips_person.copy()
bins = [0, 1, 2, 3, 4, 5, 10, np.inf]
labels = ['<1', '1-2', '2-3', '3-4', '4-5', '5-10', '10+']
df['dist_bin'] = pd.cut(df['distance_miles'], bins=bins, labels=labels, right=False)

std_dist = df[df['bike_type'] == 'standard'].groupby('dist_bin')['ltrip_weight'].sum().reset_index()
std_dist['pct'] = std_dist['ltrip_weight'] / std_dist['ltrip_weight'].sum() * 100

ebike_dist = df[df['bike_type'] == 'ebike'].groupby('dist_bin')['ltrip_weight'].sum().reset_index()
ebike_dist['pct'] = ebike_dist['ltrip_weight'] / ebike_dist['ltrip_weight'].sum() * 100

x = np.arange(len(labels))
width = 0.35 
fig, ax = plt.subplots(figsize=(10,6))
ax.bar(x - width/2, std_dist['pct'], width, label='Standard')
ax.bar(x + width/2, ebike_dist['pct'], width, label='E-bike')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_xlabel('Bike trip distance (miles)')
ax.set_ylabel('Percent of Trips')
ax.set_title('Trip Distance by Bike Type')
ax.legend()
plt.show()

# %%
# Gender vs Bike Type
df = btrips_person[btrips_person['gender_bin']!= "Missing"]
btype_fem = df[df['gender_bin'] == 'Female & Others'].groupby('bike_type')['ltrip_weight'].sum().reset_index()
btype_fem['pct'] = btype_fem['ltrip_weight'] / btype_fem['ltrip_weight'].sum() * 100

btype_male = df[df['gender_bin'] == 'Male'].groupby('bike_type')['ltrip_weight'].sum().reset_index()
btype_male['pct'] = btype_male['ltrip_weight'] / btype_male['ltrip_weight'].sum() * 100

btype_fem['gender'] = 'Female & Others'
btype_male['gender'] = 'Male'

btype_combined = pd.concat([btype_fem, btype_male], ignore_index=True)
btype_pivot = btype_combined.pivot(index='bike_type', columns='gender', values='pct')
btype_pivot.plot(kind='bar', figsize=(8, 5))
plt.ylabel('Percent of Trips (%)')
plt.title('Bike Type Share by Gender')
plt.legend(title='Gender')
plt.xticks(rotation=0)
plt.tight_layout()
plt.show()

# %% ==============================
# Reported frequency vs comfort
df = person_btrips[(person_btrips['avg_comfort'] > 0)]
avg_comfort_freq_plt, avg_comfort_freq_tbl = viz.plot_weighted_comfort_by_group(df, 'bike_freq_bin', 'person_weight')

# Age vs average comfort ratinga
avg_comfort_age_plt, avg_comfort_age_tbl = viz.plot_weighted_comfort_by_group(df, 'age_bin', 'person_weight')
# %% =====================
# Avg comfort by gender
df = person_btrips.copy()
df = df[(df['gender_bin'] != 'Missing') & (df['avg_comfort'] > 0)]
bins = [0, 1, 2, 3, 4]
df['rate_bin'] = pd.cut(df['avg_comfort'], bins=bins, right=True)

comfort_fem_rate = (
    df[df['gender_bin'] == 'Female & Others']
    .groupby('rate_bin')['person_weight']
    .sum()
    .div(df[df['gender_bin'] == 'Female & Others']['person_weight'].sum())
    .mul(100)
    .reset_index()
)

comfort_male_rate = (
    df[df['gender_bin'] == 'Male']
    .groupby('rate_bin')['person_weight']
    .sum()
    .div(df[df['gender_bin'] == 'Male']['person_weight'].sum())
    .mul(100)
    .reset_index()
)

comfort_fem_rate['gender'] = 'Female & Others'
comfort_male_rate['gender'] = 'Male'

merge = pd.concat([comfort_male_rate, comfort_fem_rate], axis=0)

sns.barplot(
    merge,
    x = 'rate_bin',
    y = 'person_weight',
    hue = 'gender'
)
plt.xticks(
    ticks=range(len(merge['rate_bin'].unique())),
    labels=['0–1', '1–2', '2–3', '3–4']
)
plt.xlabel("Average comfort")
plt.title("Average Comfort by Gender")
plt.show()
