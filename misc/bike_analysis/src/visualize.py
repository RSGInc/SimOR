import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

def weighted_total(df, gb_col, wgt_col):
    freq = df.groupby(gb_col)[wgt_col].sum().reset_index(name='total')
    freq['pct'] = freq['total'] / freq['total'].sum() * 100
    return freq

def plot_hist(df, x, y, title = None):
    fig, ax = plt.subplots(figsize=(8, 6))
    bars = ax.bar(df[x], df[y], color='skyblue')
    for bar, pct in zip(bars, df['pct']):
        ax.text(
            bar.get_x() + bar.get_width() / 2,  
            bar.get_height(),                   
            f"{pct:.1f}%",                      
            ha='center', va='bottom', fontsize=10
        )
    ax.set_xlabel(f"{x}")
    ax.set_ylabel(f"{y}")
    ax.set_title(f"{title}")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()
    
    
def check_dup_cols(df):
    if df.columns.duplicated().any():
        print("Duplicate column names:", df.columns[df.columns.duplicated()].unique())
    else:
        print("No duplicate columns!")

def plot_weighted_comfort_by_group(
    df,
    group_by,
    weight_col='person_weight',
    comfort_prefix='bike_comfort',
    figsize=(10, 6),
    ylabel='Average Comfort (1=Very Uncomfortable, 4=Very Comfortable)',
    xlabel='Scenario',
    title=None,
    rotate_xticks=45,
):
    """
    Compute weighted mean comfort for all columns containing `comfort_prefix`, grouped by `group_by`,
    and plot a bar chart of the results.
    """
    # comfort columns
    comfort_cols = [col for col in df.columns if comfort_prefix in col]
    
    def weighted_mean(x):
        w = df.loc[x.index, weight_col]
        if (w.isna() | (w == 0)).all():
            return np.nan
        return np.average(x.fillna(np.nan), weights=w)

    summary_comfort = pd.DataFrame()
    for col in comfort_cols:
        tbl = df.groupby(group_by)[col].apply(weighted_mean)
        summary_comfort = pd.concat([summary_comfort, tbl], axis=1)

    summary_plot = summary_comfort.T
    summary_plot.index = comfort_cols

    ax = summary_plot.plot(
        kind='bar',
        figsize=figsize,
        ylabel=ylabel,
        xlabel=xlabel,
        title=title,
    )
    ax.set_xticklabels(ax.get_xticklabels(), rotation=rotate_xticks, ha='right')
    plt.tight_layout()
    plt.show()

    return ax, summary_plot

def weighted_crosstab(df, index, columns, weight=None, prop='col', fill_value=0):
    """
    Creates a weighted cross-tab and returns percentages
    either across rows or columns.
    """
    pivot = pd.pivot_table(
        df,
        index=index,
        columns=columns,
        values=weight,
        aggfunc='sum' if weight else 'count',
        fill_value=fill_value
    )

    # Compute row or column percentages
    if prop == 'row':
        pct = pivot.div(pivot.sum(axis=1), axis=0) * 100
    elif prop == 'col':
        pct = pivot.div(pivot.sum(axis=0), axis=1) * 100

    return pct.round(0)

def plot_stacked(pct_table, title, ylabel='Percent'):
    pct_table = pct_table.reindex(biker_order)
    
    plt.figure(figsize=(8, 5))
    pct_table.T[biker_order].plot(
        kind='bar',
        stacked=True,
        color=[biker_colors[b] for b in biker_order]
    )
    
    plt.title(title, fontsize=12)
    plt.ylabel(ylabel)
    plt.xlabel('')
    plt.legend(
        title='Biker Type',
        bbox_to_anchor=(1.05, 1),
        loc='upper left',
        labels=biker_order
    )
    plt.xticks(rotation = 0)
    plt.tight_layout()
    plt.show()

biker_order = [
    'NoWayNoHow',
    'InterestedButConcerned',
    'EnthusedAndConfident',
    'StrongAndFearless'
]

biker_colors = {
    'NoWayNoHow': '#D9523B',             
    'InterestedButConcerned': '#fc8d59', 
    'EnthusedAndConfident': '#91bfdb',   
    'StrongAndFearless': '#4575b4'       
}    