from scipy import stats
import numpy as np
from statsmodels.stats.weightstats import ttest_ind


def weighted_mean(x, w):
    return np.sum(w * x) / np.sum(w)

def weighted_std(x, w, unbiased=True):
    mean = weighted_mean(x, w)
    var = np.sum(w * (x - mean)**2)
    if unbiased:
        eff_n = np.sum(w) - (np.sum(w**2) / np.sum(w))
        return np.sqrt(var / eff_n)
    else:
        return np.sqrt(var / np.sum(w))

def weighted_ttest(df, group_col, value_col, group1_val, group2_val, weight_col):
    """
    Performs an independent t-test between two groups and returns key statistics.
    """
    group1 = df.loc[df[group_col] == group1_val, value_col]
    group2 = df.loc[df[group_col] == group2_val, value_col]
    
    weights1 = df.loc[df[group_col] == group1_val, weight_col]
    weights2 = df.loc[df[group_col] == group2_val, weight_col]
    
    # Sample sizes
    n1, n2 = weights1.sum(), weights2.sum()
    
    # Means and SDs
    mean1, mean2 = weighted_mean(group1, weights1), weighted_mean(group2, weights2)
    std1, std2 = weighted_std(group1, weights1), weighted_std(group2, weights2)
    
    # Mean difference
    mean_diff = mean1 - mean2
    
    # t-test
    t_stat, p_value, degrees_of_freedom = ttest_ind(group1, group2, weights = (weights1, weights2))

    results = {
        'group1_val': group1_val,
        'group2_val': group2_val,
        'n1': n1,
        'n2': n2,
        'mean1': mean1,
        'mean2': mean2,
        'std1': std1,
        'std2': std2,
        'mean_diff': mean_diff,
        't_stat': t_stat,
        'p_val': p_value,
        # 'cohen_d': cohen_d
    }
    
    return results

def weighted_total(df, gb_col, wgt_col, ):
    """ 
    Incomplete
    """
    freq = df.groupby(gb_col)[wgt_col].sum().reset_index(name='total')
    freq['pct'] = freq['total'] / freq['total'].sum() * 100
    return freq

def weighted_pt(df, index, cols, values, prop='row'):
    """
    Creates a weighted pivot table showing percentages. 
    prop (row, col)
    """
    pt = df.pivot_table(
        index = index,
        columns = cols,
        values = values,
        aggfunc = 'sum'
    )
    
    if prop == 'row':
        pct = pt.div(pt.sum(axis=1), axis=0) * 100
    elif prop == 'col':
        pct = pt.div(pt.sum(axis=0), axis=1) * 100
    else:
        raise ValueError("prop must be either 'row' or 'col'")

    return pct