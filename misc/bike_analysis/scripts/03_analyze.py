import pandas as pd
import numpy as np
import seaborn as sns
import importlib
import os
pd.set_option('display.max_columns', None)
pd.options.display.float_format = '{:.2f}'.format 
os.chdir(os.path.dirname(os.path.dirname(__file__)))

import src.visualize
importlib.reload(src.visualize)

from src.stats import weighted_ttest, weighted_pt
importlib.reload(src.stats)

from scipy.stats import chi2_contingency

# %%
# Directoriess
data_dir = 'data'
raw_dir = f'{data_dir}/raw'
interim_dir = f'{data_dir}/interim'
processed_dir = f'{data_dir}/processed'

# %%
# Load data
btrips_person = pd.read_csv(f"{interim_dir}/btrips_person.csv")
person_btrips = pd.read_csv(f"{interim_dir}/person_btrips.csv")
# %%
# Difference between male/female & level of comfort
df = person_btrips[person_btrips['avg_comfort'] > 0]
results1 = weighted_ttest(
    df,
    group_col = 'gender_bin',
    value_col = 'avg_comfort',
    group1_val = 'Male', 
    group2_val = 'Female & Others',
    weight_col = 'person_weight'
)
results1

sns.histplot(df[df['gender_bin'] != "Missing"], 
             x = 'avg_comfort',
             bins = [0, 1, 2, 3, 4], 
             weights='person_weight',
             hue='gender_bin',
             stat = 'percent',
             multiple='dodge')

# Alternative method
# group1 = df.loc[df['gender_bin'] == 'Male', 'avg_comfort']
# group2 = df.loc[df['gender_bin'] == 'Female & Others', 'avg_comfort']

# weights1 = df.loc[df['gender_bin'] == 'Male', 'person_weight']
# weights2 = df.loc[df['gender_bin'] == 'Female & Others', 'person_weight']

# t_stat, p_value, degrees_of_freedom = ttest_ind(group1, group2, weights = (weights1, weights2))
# %% ====================================
# Gender vs number of bike trips reported
results2 = weighted_ttest(
    person_btrips,
    group_col = 'gender_bin',
    group1_val='Male',
    group2_val='Female & Others',
    value_col='bike_trips',
    weight_col='person_weight'
)
results2
# %%
# Differences between comfort level & bike trips
df = person_btrips[person_btrips['comfort_bin'].notna()]
results3 = weighted_ttest(
    df,
    group_col = 'comfort_bin',
    value_col = 'bike_trips',
    group1_val = 'Comfortable',
    group2_val = 'Uncomfortable',
    weight_col = 'person_weight'
)
results3

# %%
# Reported bike frequency & bike trips
df = person_btrips[person_btrips['bike_freq_bin'] != 'Missing']
results4 = weighted_ttest(
    df,
    group_col = 'bike_freq_bin',
    value_col = 'bike_trips',
    group1_val = 'VeryFrequent',
    group2_val = 'Occasional',
    weight_col = 'person_weight'
)
results4
# %%
# Reported attitude & bike trips
results4 = weighted_ttest(
    person_btrips[person_btrips['bike_att_bin'] != "Missing"],
    group_col = 'bike_att_bin',
    value_col = 'bike_trips',
    group1_val = 'HappyWithCurrent',
    group2_val = 'WantBikeMore',
    weight_col = 'person_weight'
)
results4
# %%
# Frequency vs distance
df = btrips_person[
    (btrips_person['d_purpose_category'] != 14) & 
    (btrips_person['distance_miles'].notna())]

results5 = weighted_ttest(
    df,
    group_col = 'bike_freq_bin',
    value_col = 'distance_miles',
    group1_val = 'VeryFrequent',
    group2_val = 'Infrequent',
    weight_col = 'ltrip_weight'
)
results5

results6 = weighted_ttest(
    df,
    group_col = 'bike_freq_bin',
    value_col = 'distance_miles',
    group1_val = 'VeryFrequent',
    group2_val = 'Occasional',
    weight_col = 'ltrip_weight'
)
results6
# %%
# Bike comfort vs age
df = person_btrips[person_btrips['avg_comfort'] > 0]
results7 = weighted_ttest(
    df,
    group_col = 'age_bin',
    value_col = 'avg_comfort',
    group1_val = '18-34', 
    group2_val = '35-64',
    weight_col = 'person_weight'
)
results7

# %% ======================
# Chi-square test 
# Reported biking vs gender
table = person_btrips[person_btrips['gender_bin'].isin(['Male', 'Female & Others'])].pivot_table(
    index = 'gender_bin', 
    columns = 'reported_btrip', 
    values = 'person_weight', 
    aggfunc = 'sum', 
    fill_value=0
)
chi2, p_value, dof, expected = chi2_contingency(table)
# %%
# Reported biking vs comfort
table2 = person_btrips[person_btrips['comfort_bin'].notna()].pivot_table(
    index = 'bike_freq_bin',
    columns = 'reported_btrip',
    aggfunc = 'sum',
    values = 'person_weight',
    fill_value = 0
)
chi2, p_value, dof, expected = chi2_contingency(table2)
print(f"chi-square: {chi2}, p-value: {p_value}, expected {expected}")

# %%
# Comfort vs gender
table3 = person_btrips[(person_btrips['comfort_bin'].notna()) & (person_btrips['gender_bin'] != 'Missing')].pivot_table(
    index = 'comfort_bin',
    columns = 'gender_bin',
    aggfunc = 'sum',
    values = 'person_weight',
    fill_value = 0
)
chi2, p_value, dof, expected = chi2_contingency(table3)
print(f"chi-square: {chi2}, p-value: {p_value}, expected {expected}")

print(f"chi-square: {chi2}, p-value: {p_value}, expected {expected}")# %%
# Reported btrip and attitude
table4 = person_btrips[(person_btrips['bike_att_bin'] != "Missing")].pivot_table(
    index = 'bike_att_bin',
    columns = 'reported_btrip',
    aggfunc = 'sum',
    values = 'person_weight',
    fill_value = 0
)
chi2, p_value, dof, expected = chi2_contingency(table4)
print(f"chi-square: {chi2}, p-value: {p_value}, expected {expected}")

# %%
# Reported frequency and comfort
df = person_btrips[(person_btrips['bike_att_bin'] != "Missing") & (person_btrips['bike_att_bin'] != "Missing")]
table5 = df.pivot_table(
    index = 'bike_att_bin',
    columns = 'bike_freq_bin',
    aggfunc = 'sum',
    values = 'person_weight',
    fill_value = 0
)
chi2, p_value, dof, expected = chi2_contingency(table5)
print(f"chi-square: {chi2}, p-value: {p_value}, expected {expected}")

weighted_pt(
    df,
    index = 'bike_att_bin',
    cols='bike_freq_bin',
    values = 'person_weight'
)

weighted_pt(
    df,
    index = 'bike_att_bin',
    cols='bike_freq_bin',
    values = 'person_weight',
    prop = 'col'
)

# %%
bike_comf_cols = [col for col in person_btrips.columns if "bike_comfort_" in col]
df = person_btrips[person_btrips[bike_comf_cols] != 995]

# %% ==================================
# Logistic regression 
import statsmodels.api as sm
from sklearn.preprocessing import StandardScaler

# Prepare and filter dataframe
df = person_btrips.copy()
df = df[(df['comfort_bin'].notna()) &
        (df['gender_bin'] != "Missing") &
        (df['age_num'].notna()) & 
        (df['income_num'].notna()) &
        (df['bike_freq_bin'] != 'Missing') & 
        (df['bike_att_bin'] != "Missing") &
        (df['avg_comfort'] > 0 )
        ]

# Dummies for categorical predictors
X_dummies = pd.get_dummies(
    df[['gender_bin', 'comfort_bin', 'bike_freq_bin', 'bike_att_bin', 'age_bin']],
    drop_first=True
).astype(float)

# Scaled continuous predictors
cont = df[['income_num', 'avg_comfort']]
scaler = StandardScaler()
cont_scaled = pd.DataFrame(
    scaler.fit_transform(cont),
    columns=cont.columns,
    index=df.index
)

# Combine predictors
X = pd.concat([X_dummies, cont_scaled], axis=1)

# Remove NaN's
y = df['reported_btrip'].astype(float)
mask_nonnull = X.notna().all(axis=1) & y.notna()
X = X.loc[mask_nonnull]
y = y.loc[mask_nonnull]
weights = df.loc[mask_nonnull, 'person_weight']

# Add intercept
X = sm.add_constant(X, has_constant='add')

model = sm.GLM(y, X, family=sm.families.Binomial(), freq_weights=weights)
result = model.fit()
print(result.summary())