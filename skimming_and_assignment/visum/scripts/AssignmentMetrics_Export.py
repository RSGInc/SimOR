# SRTC: Full script to handle Assignment Summary, Model Reporting, and Results export. Uses same timestamped folder for all outputs
# Adapted to LCOG, only outputs Assignment Summary

"""
created 5/13/2025

@author: luke.gordon

"""

# Libraries
import VisumPy.helpers
import VisumPy.excel
import pandas as pd
import numpy as np
import csv
from datetime import datetime
import math
import os.path


# Pull timestamp for folder name from Visum network attribute
date = Visum.Net.AttValue("output_date")

# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

# Formatting functions
# Formatting for columns
# Create formatting function for large numbers (no decimals and thousand commas)
def format_commas(column):
	return column.apply(lambda x: '{:,.0f}'.format(x) if pd.notna(x) else None)
# Create formatting function for percentages (2 decimals and percent symbol, also multiplies by 100)
def format_percent(column):
	return column.apply(lambda x: '{:.2%}'.format(x) if pd.notna(x) else None)
# Create formatting function for small numbers (2 decimals)
def format_twoplaces(column):
	return column.apply(lambda x: '{:.2f}'.format(x) if pd.notna(x) else None)
# Create formatting function for small numbers (1 decimal)
def format_oneplace(column):
	return column.apply(lambda x: '{:.1f}'.format(x) if pd.notna(x) else None)
# Create formatting function for small numbers (0 decimals)
def format_zeroplaces(column):
	return column.apply(lambda x: '{:.0f}'.format(x) if pd.notna(x) else None)
	
	
# Formatting for single cells
# Create formatting function for large numbers (no decimals and thousand commas)
def format_commas_cell(cell_value):
	return '{:,.0f}'.format(cell_value) if pd.notna(cell_value) else None
# Create formatting function for percentages (2 decimals and percent symbol, also multiplies by 100)
def format_percent_cell(cell_value):
	return '{:.2%}'.format(cell_value) if pd.notna(cell_value) else None
# Create formatting function for small numbers (2 decimals)
def format_twoplaces_cell(cell_value):
	return '{:.2f}'.format(cell_value) if pd.notna(cell_value) else None
# Create formatting function for small numbers (0 decimals)
def format_zeroplaces_cell(cell_value):
	return '{:.0f}'.format(cell_value) if pd.notna(cell_value) else None

	
# Round to nearest even number function. Used in Volume corridor reporting
def round_to_nearest_even(number):
    rounded = round(number)
    return rounded + (rounded % 2 == 1)

# Create Percent Error function
def pct_error(count , flow):
	error = ((sum(flow)/len(flow)) - (sum(count)/len(count))) / (sum(count)/len(count))

	return error
	
# Create Percent RMSE function
def pct_rmse(count , sqerror):
	rmse = math.sqrt(sum(sqerror)/len(sqerror))/(sum(count)/len(count))

	return rmse
	
# Create VMT function (needs to pull data from all links, not just ones with counts)	
def vmt(flow , length):
	vmt = sum(flow*length)

	return vmt


# Create VHT function (needs to pull data from all links and periods, not just ones with counts) 
		# Need to have logic to handle daily vs. a single period
def vht_dly(am_flow, am_time, pm_flow, pm_time, op_flow, op_time):
		vht = sum(am_flow*(am_time/3600)) + sum(pm_flow*(pm_time/3600)) + sum(op_flow*(op_time/3600))
		return vht
def vht_per(flow, time):
		vht = sum(flow*time)
		return vht



# Assignment summary function
def assignment_summary(auto_count, sut_count, mut_count, all_count, auto_flow, sut_flow, mut_flow, all_flow): #, cong_auto_time, cong_trk_time, period):
	# DAILY
	# Percent Error and Percent RMSE
	# Import ID fields and fields with Counts and Flows
	# Link ID fields
	NO          = VisumPy.helpers.GetMulti(Visum.Net.Links,"No", activeOnly = True)
	FCLASS      = VisumPy.helpers.GetMulti(Visum.Net.Links,"TYPENO", activeOnly = True)
	LENGTH      = VisumPy.helpers.GetMulti(Visum.Net.Links,"Length", activeOnly = True)
	SCRNLINE    = VisumPy.helpers.GetMulti(Visum.Net.Links,r"CONCATENATE:SCREENLINES\CODE", activeOnly = True)

 	# Counts
	Auto_Count  = VisumPy.helpers.GetMulti(Visum.Net.Links,auto_count, activeOnly = True)
	SUT_Count   = VisumPy.helpers.GetMulti(Visum.Net.Links,sut_count, activeOnly = True)
	MUT_Count   = VisumPy.helpers.GetMulti(Visum.Net.Links,mut_count, activeOnly = True)
	Tot_Count   = VisumPy.helpers.GetMulti(Visum.Net.Links,all_count, activeOnly = True)
	AADT        = VisumPy.helpers.GetMulti(Visum.Net.Links,'AADT', activeOnly = True)
	# Link Daily Flows
	Auto_Flow  = VisumPy.helpers.GetMulti(Visum.Net.Links,auto_flow, activeOnly = True)
	SUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,sut_flow, activeOnly = True)
	MUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,mut_flow, activeOnly = True)
	Tot_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,all_flow, activeOnly = True)

	# Screenline Names for Report
	SL_NAME    = VisumPy.helpers.GetMulti(Visum.Net.Screenlines,"Name", activeOnly = True)
	SL_NAME    = list(dict.fromkeys(SL_NAME))
	
	# Make Visum list with link data
	summary_list = [NO, FCLASS, SCRNLINE, LENGTH, Auto_Flow, SUT_Flow, MUT_Flow, Tot_Flow, Auto_Count, SUT_Count, MUT_Count, Tot_Count, AADT]    
			
	# Put Visum link list into dataframe
	df = pd.DataFrame(np.column_stack(summary_list), columns = ['NO', 'FCLASS', 'SCRNLINE', 'LENGTH',
                                                                'Auto_Flow', 'SUT_Flow', 'MUT_Flow', 'Tot_Flow', 
							     								'Auto_Count', 'SUT_Count', 'MUT_Count', 'Tot_Count','AADT'])
	
	# Break out SCRNLINE field to separate by commas into individual columns	
	df[['SCRNLINE']] = df[['SCRNLINE']].astype(str)																													
	df = pd.concat([df,df['SCRNLINE'].str.split(',', expand = True)], axis = 1)
	# Change Screenline field names
	if 1 not in df:
			df[1] = None
	df = df.rename(columns = {0:'SCRNLINE1',1:'SCRNLINE2'})
	# Replace null values with 0 in the screenline fields
	df['SCRNLINE1'] = df['SCRNLINE1'].replace('',np.nan).fillna(0)
	df['SCRNLINE2'] = df['SCRNLINE2'].replace('',np.nan).fillna(0)
	
	# Define custom_sum function to maintain null values when aggregating Counts and Flows by LinkNO
	def custom_sum(series):
    # If all values are null, return null; otherwise, return the sum of the values
		return series.sum() if series.notna().any() else None																												
	## GROUP EACH DATAFRAME BY 'NO' COLUMN TO COMBINE COUNTS ON EACH LINK INTO BOTH DIRECTIONS
	df = df.groupby('NO').agg(
		FCLASS      =('FCLASS', 'max'),
		LENGTH      =('LENGTH', 'max'),
		SCRNLINE1   =('SCRNLINE1', 'first'),
		SCRNLINE2   =('SCRNLINE2', 'first'),
		Auto_Flow   =('Auto_Flow', custom_sum),
		SUT_Flow    =('SUT_Flow', custom_sum),
		MUT_Flow    =('MUT_Flow', custom_sum),
		Tot_Flow    =('Tot_Flow', custom_sum),
		Auto_Count  =('Auto_Count', custom_sum),
		SUT_Count   =('SUT_Count', custom_sum),
		MUT_Count   =('MUT_Count', custom_sum),
		Tot_Count   =('Tot_Count', custom_sum),
		AADT        =('AADT', custom_sum)).reset_index()
	
	# Drop AADT from df and join in AADT from df_aadt (to have 2-way AADT by link)
	#df = df.drop('AADT', axis=1)
	#df = pd.merge(df, df_aadt, on='NO', how='left')

	# Convert FCLASS to integer
	df[['FCLASS']] = df[['FCLASS']].astype(int)
	
	# Convert SCRNLINE1 and SCRNLINE2 to Integer
	df[['SCRNLINE1','SCRNLINE2']] = df[['SCRNLINE1','SCRNLINE2']].astype(float)
	df[['SCRNLINE1','SCRNLINE2']] = df[['SCRNLINE1','SCRNLINE2']].astype(int)
	
	
	# Build results dictionary to use as results dataframe to save summary stats for group stats
	results = {"Segment":['Auto',
						'Auto: AADT <5k','Auto: AADT 5-10k','Auto: AADT 10-15k','Auto: AADT 15-20k','Auto: AADT 20-30k','Auto: AADT 30-40k','Auto: AADT 40-50k',
						'Auto: LinkType 1', 'Auto: LinkType 2', 'Auto: LinkType 3', 'Auto: LinkType 4', 'Auto: LinkType 5', 'Auto: LinkType 6', 'Auto: LinkType 7', 
						'Auto: LinkType 8', 'Auto: LinkType 9', 'Auto: LinkType 10', 'Auto: LinkType 11', 'Auto: LinkType 12', 'Auto: LinkType 30', 'Auto: LinkType 32', 
						'Auto: SL '+SL_NAME[0] ,'Auto: SL '+SL_NAME[1] ,'Auto: SL '+SL_NAME[2] ,'Auto: SL '+SL_NAME[3] ,'Auto: SL '+SL_NAME[4] ,'Auto: SL '+SL_NAME[5] ,'Auto: SL '+SL_NAME[6] ,
						'Auto: SL '+SL_NAME[7] ,'Auto: SL '+SL_NAME[8] ,'Auto: SL '+SL_NAME[9] ,'Auto: SL '+SL_NAME[10],'Auto: SL '+SL_NAME[11],'Auto: SL '+SL_NAME[12],
      					'SUT',
						'SUT: AADT <5k','SUT: AADT 5-10k','SUT: AADT 10-15k','SUT: AADT 15-20k','SUT: AADT 20-30k','SUT: AADT 30-40k','SUT: AADT 40-50k',
						'SUT: LinkType 1', 'SUT: LinkType 2', 'SUT: LinkType 3', 'SUT: LinkType 4', 'SUT: LinkType 5', 'SUT: LinkType 6', 'SUT: LinkType 7', 
						'SUT: LinkType 8', 'SUT: LinkType 9', 'SUT: LinkType 10', 'SUT: LinkType 11', 'SUT: LinkType 12', 'SUT: LinkType 30', 'SUT: LinkType 32', 
						'SUT: SL '+SL_NAME[0] ,'SUT: SL '+SL_NAME[1] ,'SUT: SL '+SL_NAME[2] ,'SUT: SL '+SL_NAME[3] ,'SUT: SL '+SL_NAME[4] ,'SUT: SL '+SL_NAME[5] ,'SUT: SL '+SL_NAME[6] ,
						'SUT: SL '+SL_NAME[7] ,'SUT: SL '+SL_NAME[8] ,'SUT: SL '+SL_NAME[9] ,'SUT: SL '+SL_NAME[10],'SUT: SL '+SL_NAME[11],'SUT: SL '+SL_NAME[12],
						'MUT',
						'MUT: AADT <5k','MUT: AADT 5-10k','MUT: AADT 10-15k','MUT: AADT 15-20k','MUT: AADT 20-30k','MUT: AADT 30-40k','MUT: AADT 40-50k',
						'MUT: LinkType 1', 'MUT: LinkType 2', 'MUT: LinkType 3', 'MUT: LinkType 4', 'MUT: LinkType 5', 'MUT: LinkType 6', 'MUT: LinkType 7', 
						'MUT: LinkType 8', 'MUT: LinkType 9', 'MUT: LinkType 10', 'MUT: LinkType 11', 'MUT: LinkType 12', 'MUT: LinkType 30', 'MUT: LinkType 32', 
      					'MUT: SL '+SL_NAME[0] ,'MUT: SL '+SL_NAME[1] ,'MUT: SL '+SL_NAME[2] ,'MUT: SL '+SL_NAME[3] ,'MUT: SL '+SL_NAME[4] ,'MUT: SL '+SL_NAME[5] ,'MUT: SL '+SL_NAME[6] ,
						'MUT: SL '+SL_NAME[7],'MUT: SL '+SL_NAME[8] ,'MUT: SL '+SL_NAME[9] ,'MUT: SL '+SL_NAME[10],'MUT: SL '+SL_NAME[11],'MUT: SL '+SL_NAME[12],
						'All Modes',
						'All Modes: AADT <5k','All Modes: AADT 5-10k','All Modes: AADT 10-15k','All Modes: AADT 15-20k','All Modes: AADT 20-30k','All Modes: AADT 30-40k','All Modes: AADT 40-50k',
						'All Modes: LinkType 1', 'All Modes: LinkType 2', 'All Modes: LinkType 3', 'All Modes: LinkType 4', 'All Modes: LinkType 5', 'All Modes: LinkType 6', 'All Modes: LinkType 7', 
						'All Modes: LinkType 8', 'All Modes: LinkType 9', 'All Modes: LinkType 10', 'All Modes: LinkType 11', 'All Modes: LinkType 12', 'All Modes: LinkType 30', 'All Modes: LinkType 32',
						'All Modes: SL '+SL_NAME[0] ,'All Modes: SL '+SL_NAME[1] ,'All Modes: SL '+SL_NAME[2] ,'All Modes: SL '+SL_NAME[3] ,'All Modes: SL '+SL_NAME[4] ,'All Modes: SL '+SL_NAME[5] ,
						'All Modes: SL '+SL_NAME[6] ,'All Modes: SL '+SL_NAME[7] ,'All Modes: SL '+SL_NAME[8] ,'All Modes: SL '+SL_NAME[9] ,'All Modes: SL '+SL_NAME[10],'All Modes: SL '+SL_NAME[11],
						'All Modes: SL '+SL_NAME[12]
						]}
						
						
						
	# Plug results dictionary into results_df dataframe                           
	results_df = pd.DataFrame(data = results)
	
	# Add stats columns
	results_df['Percent Error'] = None
	results_df['Percent RMSE'] = None
	results_df['Total VMT'] = None
	results_df['Total VHT'] = None
	results_df['Number of Observations'] = None
	results_df['Sum of Counts'] = None
	results_df['Mean of Counts'] = None
	results_df['Median of Counts'] = None
	results_df['Count VMT, Links with Counts'] = None
	results_df['Modeled VMT, Links with Counts'] = None
	
	
	# For links with counts only, used for Pct. Error and Pct. RMSE
	# Filter out links where count is null or 0 and by each condition
	# All Links with Auto Counts
	count_df     = df[df['Auto_Count'].notna()]

	# By AADT Volume
	under_5k_df     = count_df[(count_df['AADT'] < 5000)]
	btwn_5_10k_df   = count_df[(count_df['AADT'] >= 5000) & (count_df['AADT'] < 10000)]
	btwn_10_15k_df  = count_df[(count_df['AADT'] >= 10000) & (count_df['AADT'] < 15000)]
	btwn_15_20k_df  = count_df[(count_df['AADT'] >= 15000) & (count_df['AADT'] < 20000)]
	btwn_20_30k_df  = count_df[(count_df['AADT'] >= 20000) & (count_df['AADT'] < 30000)]
	btwn_30_40k_df  = count_df[(count_df['AADT'] >= 30000) & (count_df['AADT'] < 40000)]
	btwn_40_50k_df  = count_df[(count_df['AADT'] >= 40000) & (count_df['AADT'] < 50000)]
	#over_50k_df     = count_df[(count_df['AADT'] >= 50000)]
	# By Functional Class
	fc1_df    = count_df[(count_df['FCLASS'] == 1)]
	fc2_df    = count_df[(count_df['FCLASS'] == 2)]
	fc3_df    = count_df[(count_df['FCLASS'] == 3)]
	fc4_df    = count_df[(count_df['FCLASS'] == 4)]
	fc5_df    = count_df[(count_df['FCLASS'] == 5)]
	fc6_df    = count_df[(count_df['FCLASS'] == 6)]
	fc7_df    = count_df[(count_df['FCLASS'] == 7)]
	fc8_df    = count_df[(count_df['FCLASS'] == 8)]
	fc9_df    = count_df[(count_df['FCLASS'] == 9)]
	fc10_df   = count_df[(count_df['FCLASS'] == 10)]
	fc11_df   = count_df[(count_df['FCLASS'] == 11)]
	fc12_df   = count_df[(count_df['FCLASS'] == 12)]
	fc30_df   = count_df[(count_df['FCLASS'] == 30)]
	fc32_df   = count_df[(count_df['FCLASS'] == 32)]
	
 	# By Screenline
	sl_1_df    = count_df[(count_df['SCRNLINE1'] ==  1) | (count_df['SCRNLINE2'] ==  1)]
	sl_2_df    = count_df[(count_df['SCRNLINE1'] ==  2) | (count_df['SCRNLINE2'] ==  2)]
	sl_3_df    = count_df[(count_df['SCRNLINE1'] ==  3) | (count_df['SCRNLINE2'] ==  3)]
	sl_4_df    = count_df[(count_df['SCRNLINE1'] ==  4) | (count_df['SCRNLINE2'] ==  4)]
	sl_5_df    = count_df[(count_df['SCRNLINE1'] ==  5) | (count_df['SCRNLINE2'] ==  5)]
	sl_6_df    = count_df[(count_df['SCRNLINE1'] ==  6) | (count_df['SCRNLINE2'] ==  6)]
	sl_7_df    = count_df[(count_df['SCRNLINE1'] ==  7) | (count_df['SCRNLINE2'] ==  7)]
	sl_8_df    = count_df[(count_df['SCRNLINE1'] ==  8) | (count_df['SCRNLINE2'] ==  8)]
	sl_9_df    = count_df[(count_df['SCRNLINE1'] ==  9) | (count_df['SCRNLINE2'] ==  9)]
	sl_10_df   = count_df[(count_df['SCRNLINE1'] == 10) | (count_df['SCRNLINE2'] == 10)]
	sl_11_df   = count_df[(count_df['SCRNLINE1'] == 11) | (count_df['SCRNLINE2'] == 11)]
	sl_12_df   = count_df[(count_df['SCRNLINE1'] == 12) | (count_df['SCRNLINE2'] == 12)]
	sl_13_df   = count_df[(count_df['SCRNLINE1'] == 13) | (count_df['SCRNLINE2'] == 13)]
	#sl_14_df   = count_df[(count_df['SCRNLINE1'] == 14) | (count_df['SCRNLINE2'] == 14)]
	#sl_15_df   = count_df[(count_df['SCRNLINE1'] == 15) | (count_df['SCRNLINE2'] == 15)]
	#sl_16_df   = count_df[(count_df['SCRNLINE1'] == 16) | (count_df['SCRNLINE2'] == 16)]
	#sl_17_df   = count_df[(count_df['SCRNLINE1'] == 17) | (count_df['SCRNLINE2'] == 17)]
	#sl_18_df   = count_df[(count_df['SCRNLINE1'] == 18) | (count_df['SCRNLINE2'] == 18)]
	#sl_19_df   = count_df[(count_df['SCRNLINE1'] == 19) | (count_df['SCRNLINE2'] == 19)]
	#sl_20_df   = count_df[(count_df['SCRNLINE1'] == 20) | (count_df['SCRNLINE2'] == 20)]
	#sl_21_df   = count_df[(count_df['SCRNLINE1'] == 21) | (count_df['SCRNLINE2'] == 21)]
	#sl_22_df   = count_df[(count_df['SCRNLINE1'] == 22) | (count_df['SCRNLINE2'] == 22)]
	#sl_23_df   = count_df[(count_df['SCRNLINE1'] == 23) | (count_df['SCRNLINE2'] == 23)]
	#sl_24_df   = count_df[(count_df['SCRNLINE1'] == 24) | (count_df['SCRNLINE2'] == 24)]
	#sl_25_df   = count_df[(count_df['SCRNLINE1'] == 25) | (count_df['SCRNLINE2'] == 25)]
	#sl_26_df   = count_df[(count_df['SCRNLINE1'] == 26) | (count_df['SCRNLINE2'] == 26)]
	
	# Build list of dataframes to loop thru
	auto_df_list = [count_df,#internal_df,external_df,
					under_5k_df,btwn_5_10k_df,btwn_10_15k_df,btwn_15_20k_df,btwn_20_30k_df,btwn_30_40k_df,btwn_40_50k_df,
					fc1_df,fc2_df,fc3_df,fc4_df,fc5_df,fc6_df,fc7_df,fc8_df,fc9_df,fc10_df,fc11_df,fc12_df,fc30_df,fc32_df,
					sl_1_df,sl_2_df,sl_3_df,sl_4_df,sl_5_df,sl_6_df,sl_7_df,sl_8_df,sl_9_df,sl_10_df,sl_11_df,sl_12_df,sl_13_df]

				
				
	# All Links with SUT Counts
	count_df     = df[df['SUT_Count'].notna()]
	# By AADT Volume
	under_5k_df     = count_df[(count_df['AADT'] < 5000)]
	btwn_5_10k_df   = count_df[(count_df['AADT'] >= 5000) & (count_df['AADT'] < 10000)]
	btwn_10_15k_df  = count_df[(count_df['AADT'] >= 10000) & (count_df['AADT'] < 15000)]
	btwn_15_20k_df  = count_df[(count_df['AADT'] >= 15000) & (count_df['AADT'] < 20000)]
	btwn_20_30k_df  = count_df[(count_df['AADT'] >= 20000) & (count_df['AADT'] < 30000)]
	btwn_30_40k_df  = count_df[(count_df['AADT'] >= 30000) & (count_df['AADT'] < 40000)]
	btwn_40_50k_df  = count_df[(count_df['AADT'] >= 40000) & (count_df['AADT'] < 50000)]
	#over_50k_df     = count_df[(count_df['AADT'] >= 50000)]
	# By Functional Class
	fc1_df    = count_df[(count_df['FCLASS'] == 1)]
	fc2_df    = count_df[(count_df['FCLASS'] == 2)]
	fc3_df    = count_df[(count_df['FCLASS'] == 3)]
	fc4_df    = count_df[(count_df['FCLASS'] == 4)]
	fc5_df    = count_df[(count_df['FCLASS'] == 5)]
	fc6_df    = count_df[(count_df['FCLASS'] == 6)]
	fc7_df    = count_df[(count_df['FCLASS'] == 7)]
	fc8_df    = count_df[(count_df['FCLASS'] == 8)]
	fc9_df    = count_df[(count_df['FCLASS'] == 9)]
	fc10_df   = count_df[(count_df['FCLASS'] == 10)]
	fc11_df   = count_df[(count_df['FCLASS'] == 11)]
	fc12_df   = count_df[(count_df['FCLASS'] == 12)]
	fc30_df   = count_df[(count_df['FCLASS'] == 30)]
	fc32_df   = count_df[(count_df['FCLASS'] == 32)]
	# By Screenline
	sl_1_df    = count_df[(count_df['SCRNLINE1'] ==  1) | (count_df['SCRNLINE2'] ==  1)]
	sl_2_df    = count_df[(count_df['SCRNLINE1'] ==  2) | (count_df['SCRNLINE2'] ==  2)]
	sl_3_df    = count_df[(count_df['SCRNLINE1'] ==  3) | (count_df['SCRNLINE2'] ==  3)]
	sl_4_df    = count_df[(count_df['SCRNLINE1'] ==  4) | (count_df['SCRNLINE2'] ==  4)]
	sl_5_df    = count_df[(count_df['SCRNLINE1'] ==  5) | (count_df['SCRNLINE2'] ==  5)]
	sl_6_df    = count_df[(count_df['SCRNLINE1'] ==  6) | (count_df['SCRNLINE2'] ==  6)]
	sl_7_df    = count_df[(count_df['SCRNLINE1'] ==  7) | (count_df['SCRNLINE2'] ==  7)]
	sl_8_df    = count_df[(count_df['SCRNLINE1'] ==  8) | (count_df['SCRNLINE2'] ==  8)]
	sl_9_df    = count_df[(count_df['SCRNLINE1'] ==  9) | (count_df['SCRNLINE2'] ==  9)]
	sl_10_df   = count_df[(count_df['SCRNLINE1'] == 10) | (count_df['SCRNLINE2'] == 10)]
	sl_11_df   = count_df[(count_df['SCRNLINE1'] == 11) | (count_df['SCRNLINE2'] == 11)]
	sl_12_df   = count_df[(count_df['SCRNLINE1'] == 12) | (count_df['SCRNLINE2'] == 12)]
	sl_13_df   = count_df[(count_df['SCRNLINE1'] == 13) | (count_df['SCRNLINE2'] == 13)]
	#sl_14_df   = count_df[(count_df['SCRNLINE1'] == 14) | (count_df['SCRNLINE2'] == 14)]
	#sl_15_df   = count_df[(count_df['SCRNLINE1'] == 15) | (count_df['SCRNLINE2'] == 15)]
	#sl_16_df   = count_df[(count_df['SCRNLINE1'] == 16) | (count_df['SCRNLINE2'] == 16)]
	#sl_17_df   = count_df[(count_df['SCRNLINE1'] == 17) | (count_df['SCRNLINE2'] == 17)]
	#sl_18_df   = count_df[(count_df['SCRNLINE1'] == 18) | (count_df['SCRNLINE2'] == 18)]
	#sl_19_df   = count_df[(count_df['SCRNLINE1'] == 19) | (count_df['SCRNLINE2'] == 19)]
	#sl_20_df   = count_df[(count_df['SCRNLINE1'] == 20) | (count_df['SCRNLINE2'] == 20)]
	#sl_21_df   = count_df[(count_df['SCRNLINE1'] == 21) | (count_df['SCRNLINE2'] == 21)]
	#sl_22_df   = count_df[(count_df['SCRNLINE1'] == 22) | (count_df['SCRNLINE2'] == 22)]
	#sl_23_df   = count_df[(count_df['SCRNLINE1'] == 23) | (count_df['SCRNLINE2'] == 23)]
	#sl_24_df   = count_df[(count_df['SCRNLINE1'] == 24) | (count_df['SCRNLINE2'] == 24)]
	#sl_25_df   = count_df[(count_df['SCRNLINE1'] == 25) | (count_df['SCRNLINE2'] == 25)]
	#sl_26_df   = count_df[(count_df['SCRNLINE1'] == 26) | (count_df['SCRNLINE2'] == 26)]
	
	# Build list of dataframes to loop thru
	sut_df_list = [count_df,#internal_df,external_df,
					under_5k_df,btwn_5_10k_df,btwn_10_15k_df,btwn_15_20k_df,btwn_20_30k_df,btwn_30_40k_df,btwn_40_50k_df,
					fc1_df,fc2_df,fc3_df,fc4_df,fc5_df,fc6_df,fc7_df,fc8_df,fc9_df,fc10_df,fc11_df,fc12_df,fc30_df,fc32_df,
					sl_1_df,sl_2_df,sl_3_df,sl_4_df,sl_5_df,sl_6_df,sl_7_df,sl_8_df,sl_9_df,sl_10_df,sl_11_df,sl_12_df,sl_13_df]
	

	# All Links with MUT Counts
	count_df     = df[df['MUT_Count'].notna()]
	# By AADT Volume
	under_5k_df     = count_df[(count_df['AADT'] < 5000)]
	btwn_5_10k_df   = count_df[(count_df['AADT'] >= 5000) & (count_df['AADT'] < 10000)]
	btwn_10_15k_df  = count_df[(count_df['AADT'] >= 10000) & (count_df['AADT'] < 15000)]
	btwn_15_20k_df  = count_df[(count_df['AADT'] >= 15000) & (count_df['AADT'] < 20000)]
	btwn_20_30k_df  = count_df[(count_df['AADT'] >= 20000) & (count_df['AADT'] < 30000)]
	btwn_30_40k_df  = count_df[(count_df['AADT'] >= 30000) & (count_df['AADT'] < 40000)]
	btwn_40_50k_df  = count_df[(count_df['AADT'] >= 40000) & (count_df['AADT'] < 50000)]
	#over_50k_df     = count_df[(count_df['AADT'] >= 50000)]
	# By Functional Class
	fc1_df    = count_df[(count_df['FCLASS'] == 1)]
	fc2_df    = count_df[(count_df['FCLASS'] == 2)]
	fc3_df    = count_df[(count_df['FCLASS'] == 3)]
	fc4_df    = count_df[(count_df['FCLASS'] == 4)]
	fc5_df    = count_df[(count_df['FCLASS'] == 5)]
	fc6_df    = count_df[(count_df['FCLASS'] == 6)]
	fc7_df    = count_df[(count_df['FCLASS'] == 7)]
	fc8_df    = count_df[(count_df['FCLASS'] == 8)]
	fc9_df    = count_df[(count_df['FCLASS'] == 9)]
	fc10_df   = count_df[(count_df['FCLASS'] == 10)]
	fc11_df   = count_df[(count_df['FCLASS'] == 11)]
	fc12_df   = count_df[(count_df['FCLASS'] == 12)]
	fc30_df   = count_df[(count_df['FCLASS'] == 30)]
	fc32_df   = count_df[(count_df['FCLASS'] == 32)]
	# By Screenline
	sl_1_df    = count_df[(count_df['SCRNLINE1'] ==  1) | (count_df['SCRNLINE2'] ==  1)]
	sl_2_df    = count_df[(count_df['SCRNLINE1'] ==  2) | (count_df['SCRNLINE2'] ==  2)]
	sl_3_df    = count_df[(count_df['SCRNLINE1'] ==  3) | (count_df['SCRNLINE2'] ==  3)]
	sl_4_df    = count_df[(count_df['SCRNLINE1'] ==  4) | (count_df['SCRNLINE2'] ==  4)]
	sl_5_df    = count_df[(count_df['SCRNLINE1'] ==  5) | (count_df['SCRNLINE2'] ==  5)]
	sl_6_df    = count_df[(count_df['SCRNLINE1'] ==  6) | (count_df['SCRNLINE2'] ==  6)]
	sl_7_df    = count_df[(count_df['SCRNLINE1'] ==  7) | (count_df['SCRNLINE2'] ==  7)]
	sl_8_df    = count_df[(count_df['SCRNLINE1'] ==  8) | (count_df['SCRNLINE2'] ==  8)]
	sl_9_df    = count_df[(count_df['SCRNLINE1'] ==  9) | (count_df['SCRNLINE2'] ==  9)]
	sl_10_df   = count_df[(count_df['SCRNLINE1'] == 10) | (count_df['SCRNLINE2'] == 10)]
	sl_11_df   = count_df[(count_df['SCRNLINE1'] == 11) | (count_df['SCRNLINE2'] == 11)]
	sl_12_df   = count_df[(count_df['SCRNLINE1'] == 12) | (count_df['SCRNLINE2'] == 12)]
	sl_13_df   = count_df[(count_df['SCRNLINE1'] == 13) | (count_df['SCRNLINE2'] == 13)]
	#sl_14_df   = count_df[(count_df['SCRNLINE1'] == 14) | (count_df['SCRNLINE2'] == 14)]
	#sl_15_df   = count_df[(count_df['SCRNLINE1'] == 15) | (count_df['SCRNLINE2'] == 15)]
	#sl_16_df   = count_df[(count_df['SCRNLINE1'] == 16) | (count_df['SCRNLINE2'] == 16)]
	#sl_17_df   = count_df[(count_df['SCRNLINE1'] == 17) | (count_df['SCRNLINE2'] == 17)]
	#sl_18_df   = count_df[(count_df['SCRNLINE1'] == 18) | (count_df['SCRNLINE2'] == 18)]
	#sl_19_df   = count_df[(count_df['SCRNLINE1'] == 19) | (count_df['SCRNLINE2'] == 19)]
	#sl_20_df   = count_df[(count_df['SCRNLINE1'] == 20) | (count_df['SCRNLINE2'] == 20)]
	#sl_21_df   = count_df[(count_df['SCRNLINE1'] == 21) | (count_df['SCRNLINE2'] == 21)]
	#sl_22_df   = count_df[(count_df['SCRNLINE1'] == 22) | (count_df['SCRNLINE2'] == 22)]
	#sl_23_df   = count_df[(count_df['SCRNLINE1'] == 23) | (count_df['SCRNLINE2'] == 23)]
	#sl_24_df   = count_df[(count_df['SCRNLINE1'] == 24) | (count_df['SCRNLINE2'] == 24)]
	#sl_25_df   = count_df[(count_df['SCRNLINE1'] == 25) | (count_df['SCRNLINE2'] == 25)]
	#sl_26_df   = count_df[(count_df['SCRNLINE1'] == 26) | (count_df['SCRNLINE2'] == 26)]

	
	# Build list of dataframes to loop thru
	mut_df_list = [count_df,#internal_df,external_df,
					under_5k_df,btwn_5_10k_df,btwn_10_15k_df,btwn_15_20k_df,btwn_20_30k_df,btwn_30_40k_df,btwn_40_50k_df,
					fc1_df,fc2_df,fc3_df,fc4_df,fc5_df,fc6_df,fc7_df,fc8_df,fc9_df,fc10_df,fc11_df,fc12_df,fc30_df,fc32_df,
					sl_1_df,sl_2_df,sl_3_df,sl_4_df,sl_5_df,sl_6_df,sl_7_df,sl_8_df,sl_9_df,sl_10_df,sl_11_df,sl_12_df,sl_13_df]

	# All Links with All Modes Counts
	count_df     = df[df['Tot_Count'].notna()]
	# By AADT Volume
	under_5k_df     = count_df[(count_df['AADT'] < 5000)]
	btwn_5_10k_df   = count_df[(count_df['AADT'] >= 5000) & (count_df['AADT'] < 10000)]
	btwn_10_15k_df  = count_df[(count_df['AADT'] >= 10000) & (count_df['AADT'] < 15000)]
	btwn_15_20k_df  = count_df[(count_df['AADT'] >= 15000) & (count_df['AADT'] < 20000)]
	btwn_20_30k_df  = count_df[(count_df['AADT'] >= 20000) & (count_df['AADT'] < 30000)]
	btwn_30_40k_df  = count_df[(count_df['AADT'] >= 30000) & (count_df['AADT'] < 40000)]
	btwn_40_50k_df  = count_df[(count_df['AADT'] >= 40000) & (count_df['AADT'] < 50000)]
	# By Functional Class
	fc1_df    = count_df[(count_df['FCLASS'] == 1)]
	fc2_df    = count_df[(count_df['FCLASS'] == 2)]
	fc3_df    = count_df[(count_df['FCLASS'] == 3)]
	fc4_df    = count_df[(count_df['FCLASS'] == 4)]
	fc5_df    = count_df[(count_df['FCLASS'] == 5)]
	fc6_df    = count_df[(count_df['FCLASS'] == 6)]
	fc7_df    = count_df[(count_df['FCLASS'] == 7)]
	fc8_df    = count_df[(count_df['FCLASS'] == 8)]
	fc9_df    = count_df[(count_df['FCLASS'] == 9)]
	fc10_df   = count_df[(count_df['FCLASS'] == 10)]
	fc11_df   = count_df[(count_df['FCLASS'] == 11)]
	fc12_df   = count_df[(count_df['FCLASS'] == 12)]
	fc30_df   = count_df[(count_df['FCLASS'] == 30)]
	fc32_df   = count_df[(count_df['FCLASS'] == 32)]
	# By Screenline
	sl_1_df    = count_df[(count_df['SCRNLINE1'] ==  1) | (count_df['SCRNLINE2'] ==  1)]
	sl_2_df    = count_df[(count_df['SCRNLINE1'] ==  2) | (count_df['SCRNLINE2'] ==  2)]
	sl_3_df    = count_df[(count_df['SCRNLINE1'] ==  3) | (count_df['SCRNLINE2'] ==  3)]
	sl_4_df    = count_df[(count_df['SCRNLINE1'] ==  4) | (count_df['SCRNLINE2'] ==  4)]
	sl_5_df    = count_df[(count_df['SCRNLINE1'] ==  5) | (count_df['SCRNLINE2'] ==  5)]
	sl_6_df    = count_df[(count_df['SCRNLINE1'] ==  6) | (count_df['SCRNLINE2'] ==  6)]
	sl_7_df    = count_df[(count_df['SCRNLINE1'] ==  7) | (count_df['SCRNLINE2'] ==  7)]
	sl_8_df    = count_df[(count_df['SCRNLINE1'] ==  8) | (count_df['SCRNLINE2'] ==  8)]
	sl_9_df    = count_df[(count_df['SCRNLINE1'] ==  9) | (count_df['SCRNLINE2'] ==  9)]
	sl_10_df   = count_df[(count_df['SCRNLINE1'] == 10) | (count_df['SCRNLINE2'] == 10)]
	sl_11_df   = count_df[(count_df['SCRNLINE1'] == 11) | (count_df['SCRNLINE2'] == 11)]
	sl_12_df   = count_df[(count_df['SCRNLINE1'] == 12) | (count_df['SCRNLINE2'] == 12)]
	sl_13_df   = count_df[(count_df['SCRNLINE1'] == 13) | (count_df['SCRNLINE2'] == 13)]
	#sl_14_df   = count_df[(count_df['SCRNLINE1'] == 14) | (count_df['SCRNLINE2'] == 14)]
	#sl_15_df   = count_df[(count_df['SCRNLINE1'] == 15) | (count_df['SCRNLINE2'] == 15)]
	#sl_16_df   = count_df[(count_df['SCRNLINE1'] == 16) | (count_df['SCRNLINE2'] == 16)]
	#sl_17_df   = count_df[(count_df['SCRNLINE1'] == 17) | (count_df['SCRNLINE2'] == 17)]
	#sl_18_df   = count_df[(count_df['SCRNLINE1'] == 18) | (count_df['SCRNLINE2'] == 18)]
	#sl_19_df   = count_df[(count_df['SCRNLINE1'] == 19) | (count_df['SCRNLINE2'] == 19)]
	#sl_20_df   = count_df[(count_df['SCRNLINE1'] == 20) | (count_df['SCRNLINE2'] == 20)]
	#sl_21_df   = count_df[(count_df['SCRNLINE1'] == 21) | (count_df['SCRNLINE2'] == 21)]
	#sl_22_df   = count_df[(count_df['SCRNLINE1'] == 22) | (count_df['SCRNLINE2'] == 22)]
	#sl_23_df   = count_df[(count_df['SCRNLINE1'] == 23) | (count_df['SCRNLINE2'] == 23)]
	#sl_24_df   = count_df[(count_df['SCRNLINE1'] == 24) | (count_df['SCRNLINE2'] == 24)]
	#sl_25_df   = count_df[(count_df['SCRNLINE1'] == 25) | (count_df['SCRNLINE2'] == 25)]
	#sl_26_df   = count_df[(count_df['SCRNLINE1'] == 26) | (count_df['SCRNLINE2'] == 26)]

	
	# Build list of dataframes to loop thru
	allmodes_df_list = [count_df,#internal_df,external_df,
					under_5k_df,btwn_5_10k_df,btwn_10_15k_df,btwn_15_20k_df,btwn_20_30k_df,btwn_30_40k_df,btwn_40_50k_df,
					fc1_df,fc2_df,fc3_df,fc4_df,fc5_df,fc6_df,fc7_df,fc8_df,fc9_df,fc10_df,fc11_df,fc12_df,fc30_df,fc32_df,
					sl_1_df,sl_2_df,sl_3_df,sl_4_df,sl_5_df,sl_6_df,sl_7_df,sl_8_df,sl_9_df,sl_10_df,sl_11_df,sl_12_df,sl_13_df]
	

	# Add squared error column to each df 
	# Auto
	for i in auto_df_list:
		i['Auto_SqError']  = (i.Auto_Flow - i.Auto_Count)**2	
	# SUT          
	for i in sut_df_list:
		i['SUT_SqError']   = (i.SUT_Flow - i.SUT_Count)**2
	# MUT          
	for i in mut_df_list:
		i['MUT_SqError']   = (i.MUT_Flow - i.MUT_Count)**2
	# All Modes          
	for i in allmodes_df_list:
		i['Tot_SqError']   = (i.Tot_Flow - i.Tot_Count)**2
			
	# Create attributes for 'y' in the next section
	auto_loc = 0
	sut_loc = auto_loc + len(sut_df_list)
	mut_loc = sut_loc + len(mut_df_list)
	allmodes_loc = mut_loc + len(allmodes_df_list)


	# Calculate Auto pct error and pct rmse from each dataframe and save in results dataframe
	y = auto_loc
	for i in auto_df_list:
		if len(i) == 0:
			results_df.at[y,"Number of Observations"] = 0
			y = y + 1
			#continue
		else:
			results_df.at[y,"Percent Error"]                  = pct_error(i.Auto_Count,i.Auto_Flow)
			results_df.at[y,"Percent RMSE"]                   = pct_rmse(i.Auto_Count,i.Auto_SqError)
			results_df.at[y,"Number of Observations"]         = len(i)
			results_df.at[y,"Sum of Counts"]                  = np.sum(i.Auto_Count)
			results_df.at[y,"Mean of Counts"]                 = np.mean(i.Auto_Count)
			results_df.at[y,"Median of Counts"]               = np.median(i.Auto_Count)
			results_df.at[y,"Count VMT, Links with Counts"]   = vmt(i.Auto_Count,i.LENGTH)
			results_df.at[y,'Modeled VMT, Links with Counts'] = vmt(i.Auto_Flow,i.LENGTH)
			y = y + 1
	
	# Calculate SUT pct error and pct rmse from each dataframe and save in results dataframe
	y = sut_loc
	for i in sut_df_list:
		if len(i) == 0:
			results_df.at[y,"Number of Observations"] = 0
			y = y + 1
			#continue
		else:
			results_df.at[y,"Percent Error"]                  = pct_error(i.SUT_Count,i.SUT_Flow)
			results_df.at[y,"Percent RMSE"]                   = pct_rmse(i.SUT_Count, i.SUT_SqError)
			results_df.at[y,"Number of Observations"]         = len(i)
			results_df.at[y,"Sum of Counts"]                  = np.sum(i.SUT_Count)
			results_df.at[y,"Mean of Counts"]                 = np.mean(i.SUT_Count)
			results_df.at[y,"Median of Counts"]               = np.median(i.SUT_Count)
			results_df.at[y,"Count VMT, Links with Counts"]   = vmt(i.SUT_Count,i.LENGTH)
			results_df.at[y,'Modeled VMT, Links with Counts'] = vmt(i.SUT_Flow,i.LENGTH)
			y = y + 1     

	# Calculate MUT pct error and pct rmse from each dataframe and save in results dataframe
	y = mut_loc
	for i in mut_df_list:
		if len(i) == 0:
			results_df.at[y,"Number of Observations"] = 0
			y = y + 1
			#continue
		else:
			results_df.at[y,"Percent Error"]                  = pct_error(i.MUT_Count,i.MUT_Flow)
			results_df.at[y,"Percent RMSE"]                   = pct_rmse(i.MUT_Count, i.MUT_SqError)
			results_df.at[y,"Number of Observations"]         = len(i)
			results_df.at[y,"Sum of Counts"]                  = np.sum(i.MUT_Count)
			results_df.at[y,"Mean of Counts"]                 = np.mean(i.MUT_Count)
			results_df.at[y,"Median of Counts"]               = np.median(i.MUT_Count)
			results_df.at[y,"Count VMT, Links with Counts"]   = vmt(i.MUT_Count,i.LENGTH)
			results_df.at[y,'Modeled VMT, Links with Counts'] = vmt(i.MUT_Flow,i.LENGTH)
			y = y + 1   

	# Calculate All Modes pct error and pct rmse from each dataframe and save in results dataframe
	y = allmodes_loc
	for i in allmodes_df_list:
		if len(i) == 0:
			results_df.at[y,"Number of Observations"] = 0
			y = y + 1
			#continue
		else:
			results_df.at[y,"Percent Error"]                  = pct_error(i.Tot_Count,i.Tot_Flow)
			results_df.at[y,"Percent RMSE"]                   = pct_rmse(i.Tot_Count,i.Tot_SqError)
			results_df.at[y,"Number of Observations"]         = len(i)
			results_df.at[y,"Sum of Counts"]                  = np.sum(i.Tot_Count)
			results_df.at[y,"Mean of Counts"]                 = np.mean(i.Tot_Count)
			results_df.at[y,"Median of Counts"]               = np.median(i.Tot_Count)
			results_df.at[y,"Count VMT, Links with Counts"]   = vmt(i.Tot_Count,i.LENGTH)
			results_df.at[y,'Modeled VMT, Links with Counts'] = vmt(i.Tot_Flow,i.LENGTH)
			y = y + 1     
	
	
	# Total VMT and Total VHT
	
	# Import ID fields and fields with Counts and Flows
	# Link ID fields
	NO			= VisumPy.helpers.GetMulti(Visum.Net.Links,"No", activeOnly = True)
	FCLASS		= VisumPy.helpers.GetMulti(Visum.Net.Links,"TYPENO", activeOnly = True)
	LENGTH		= VisumPy.helpers.GetMulti(Visum.Net.Links,"Length", activeOnly = True)
	SCRNLINE    = VisumPy.helpers.GetMulti(Visum.Net.Links,r"CONCATENATE:SCREENLINES\CODE", activeOnly = True)
	# Pull CONGTIME Auto by period, Length, and Flows by Period for Total VMT/Total VHT Calculations 	
	CONGTIME_AM_C   = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMTCUR_A", activeOnly = True)
	CONGTIME_PM_C   = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMTCUR_A", activeOnly = True)
	CONGTIME_OP_C   = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPTCUR_A", activeOnly = True)
	# Pull CONGTIME SUT by period, Length, and Flows by Period for Total VMT/Total VHT Calculations 	
	CONGTIME_AM_S   = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMTCUR_MED", activeOnly = True)
	CONGTIME_PM_S   = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMTCUR_MED", activeOnly = True)
	CONGTIME_OP_S   = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPTCUR_MED", activeOnly = True)
	# Pull CONGTIME SUT by period, Length, and Flows by Period for Total VMT/Total VHT Calculations 	
	CONGTIME_AM_M   = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMTCUR_HVY", activeOnly = True)
	CONGTIME_PM_M   = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMTCUR_HVY", activeOnly = True)
	CONGTIME_OP_M   = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPTCUR_HVY", activeOnly = True)
	
	# Link Flows by Period
	# AM
	sov_flow      = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMSVOL", activeOnly = True)
	hov_flow      = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMHVOL", activeOnly = True)
	
	AM_Auto_Flow  = np.add(sov_flow,hov_flow)
	AM_SUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMMTVOL", activeOnly = True)
	AM_MUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMHTVOL", activeOnly = True)
	AM_Tot_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"AMVOLPCU_N", activeOnly = True)
	# OP
	sov_flow      = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMSVOL", activeOnly = True)
	hov_flow      = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMHVOL", activeOnly = True)
	
	PM_Auto_Flow  = np.add(sov_flow,hov_flow)
	PM_SUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMMTVOL", activeOnly = True)
	PM_MUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMHTVOL", activeOnly = True)
	PM_Tot_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"PMVOLPCU_N", activeOnly = True)
	# OP
	sov_flow      = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPSVOL", activeOnly = True)
	hov_flow      = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPHVOL", activeOnly = True)
	
	OP_Auto_Flow  = np.add(sov_flow,hov_flow)
	OP_SUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPMTVOL", activeOnly = True)
	OP_MUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPHTVOL", activeOnly = True)
	OP_Tot_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,"OPVOLPCU_N", activeOnly = True)

	# Period for functions
	Auto_Flow  = VisumPy.helpers.GetMulti(Visum.Net.Links,auto_flow, activeOnly = True)
	SUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,sut_flow,  activeOnly = True)
	MUT_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,mut_flow,  activeOnly = True)
	Tot_Flow   = VisumPy.helpers.GetMulti(Visum.Net.Links,all_flow,  activeOnly = True)
	
	
	# Make Visum list with link data
	summary_list = [NO, FCLASS, LENGTH, SCRNLINE,
					CONGTIME_AM_C, CONGTIME_PM_C, CONGTIME_OP_C,
					CONGTIME_AM_S, CONGTIME_PM_S, CONGTIME_OP_S,
					CONGTIME_AM_M, CONGTIME_PM_M, CONGTIME_OP_M,
					AM_Auto_Flow, AM_SUT_Flow, AM_MUT_Flow, AM_Tot_Flow,
					PM_Auto_Flow, PM_SUT_Flow, PM_MUT_Flow, PM_Tot_Flow,
					OP_Auto_Flow, OP_SUT_Flow, OP_MUT_Flow, OP_Tot_Flow,
					Auto_Flow, SUT_Flow, MUT_Flow, Tot_Flow]
			
	# Put Visum link list into dataframe  
	df_all = pd.DataFrame(np.column_stack(summary_list), columns = ['NO', 'FCLASS', 'LENGTH', 'SCRNLINE', 
								 									'CONGTIME_AM_C', 'CONGTIME_PM_C', 'CONGTIME_OP_C',
																	'CONGTIME_AM_S', 'CONGTIME_PM_S', 'CONGTIME_OP_S',
																	'CONGTIME_AM_M', 'CONGTIME_PM_M', 'CONGTIME_OP_M',
																	'AM_Auto_Flow', 'AM_SUT_Flow', 'AM_MUT_Flow', 'AM_Tot_Flow',
																	'PM_Auto_Flow', 'PM_SUT_Flow', 'PM_MUT_Flow', 'PM_Tot_Flow',
																	'OP_Auto_Flow', 'OP_SUT_Flow', 'OP_MUT_Flow', 'OP_Tot_Flow',
																	'Auto_Flow', 'SUT_Flow', 'MUT_Flow', 'Tot_Flow'])
	
	
	# Break out SCRNLINE field to separate by commas into individual columns	
	df_all[['SCRNLINE']] = df_all[['SCRNLINE']].astype(str)																													
	df_all = pd.concat([df_all,df_all['SCRNLINE'].str.split(',', expand = True)], axis = 1)
	# Change Screenline field names
	if 1 not in df_all:
		df_all[1] = 0
	df_all = df_all.rename(columns = {0:'SCRNLINE1',1:'SCRNLINE2'})
	
	## Break out SCRNLINE field to separate by commas into individual columns																														
	#df_all = pd.concat([df_all,df_all['SCRNLINE'].str.split(',', expand = True)], axis = 1)
	## Change Screenline field names
	#df_all = df_all.rename(columns = {0:'SCRNLINE1',1:'SCRNLINE2'})

	# Replace null values with 0 in the screenline fields
	df_all['SCRNLINE1'] = df_all['SCRNLINE1'].replace('',np.nan).fillna(0)
	df_all['SCRNLINE2'] = df_all['SCRNLINE2'].replace('',np.nan).fillna(0)

	# Convert all flow and time fields to float to make multiplication and other operations run smoothly. Read in as strings
	df_all[['NO', 'FCLASS', 'LENGTH', 'SCRNLINE1','SCRNLINE2',
			'CONGTIME_AM_C', 'CONGTIME_PM_C', 'CONGTIME_OP_C',
			'CONGTIME_AM_S', 'CONGTIME_PM_S', 'CONGTIME_OP_S',
			'CONGTIME_AM_M', 'CONGTIME_PM_M', 'CONGTIME_OP_M',
			'AM_Auto_Flow', 'AM_SUT_Flow', 'AM_MUT_Flow', 'AM_Tot_Flow',
			'PM_Auto_Flow', 'PM_SUT_Flow', 'PM_MUT_Flow', 'PM_Tot_Flow',
			'OP_Auto_Flow', 'OP_SUT_Flow', 'OP_MUT_Flow', 'OP_Tot_Flow',
			'Auto_Flow', 'SUT_Flow', 'MUT_Flow', 'Tot_Flow']] = df_all[['NO', 'FCLASS', 'LENGTH', 'SCRNLINE1','SCRNLINE2',
																		'CONGTIME_AM_C', 'CONGTIME_PM_C', 'CONGTIME_OP_C',
																		'CONGTIME_AM_S', 'CONGTIME_PM_S', 'CONGTIME_OP_S',
																		'CONGTIME_AM_M', 'CONGTIME_PM_M', 'CONGTIME_OP_M',
																		'AM_Auto_Flow', 'AM_SUT_Flow', 'AM_MUT_Flow', 'AM_Tot_Flow',
																		'PM_Auto_Flow', 'PM_SUT_Flow', 'PM_MUT_Flow', 'PM_Tot_Flow',
																		'OP_Auto_Flow', 'OP_SUT_Flow', 'OP_MUT_Flow', 'OP_Tot_Flow',
																		'Auto_Flow', 'SUT_Flow', 'MUT_Flow', 'Tot_Flow']].astype(float)
		
	# Convert ID fields to integer
	df_all[['NO','FCLASS','SCRNLINE1','SCRNLINE2']] = df_all[['NO','FCLASS','SCRNLINE1','SCRNLINE2']].astype(int)

	
	# For links with counts only, used for Pct. Error and Pct. RMSE
	# Filter out links where count is null and by each condition
	# All Links with Counts
	count_df_all     = df_all
	# By AADT Volume
	under_5k_df_all     = df_all[df_all['NO'].isin(under_5k_df['NO'])]
	btwn_5_10k_df_all   = df_all[df_all['NO'].isin(btwn_5_10k_df['NO'])]
	btwn_10_15k_df_all  = df_all[df_all['NO'].isin(btwn_10_15k_df['NO'])]
	btwn_15_20k_df_all  = df_all[df_all['NO'].isin(btwn_15_20k_df['NO'])]
	btwn_20_30k_df_all  = df_all[df_all['NO'].isin(btwn_20_30k_df['NO'])]
	btwn_30_40k_df_all  = df_all[df_all['NO'].isin(btwn_30_40k_df['NO'])]
	btwn_40_50k_df_all  = df_all[df_all['NO'].isin(btwn_40_50k_df['NO'])]
	# By Functional Class
	fc1_df_all    = df_all[(df_all['FCLASS'] == 1)]
	fc2_df_all    = df_all[(df_all['FCLASS'] == 2)]
	fc3_df_all    = df_all[(df_all['FCLASS'] == 3)]
	fc4_df_all    = df_all[(df_all['FCLASS'] == 4)]
	fc5_df_all    = df_all[(df_all['FCLASS'] == 5)]
	fc6_df_all    = df_all[(df_all['FCLASS'] == 6)]
	fc7_df_all    = df_all[(df_all['FCLASS'] == 7)]
	fc8_df_all    = df_all[(df_all['FCLASS'] == 8)]
	fc9_df_all    = df_all[(df_all['FCLASS'] == 9)]
	fc10_df_all   = df_all[(df_all['FCLASS'] == 10)]
	fc11_df_all   = df_all[(df_all['FCLASS'] == 11)]
	fc12_df_all   = df_all[(df_all['FCLASS'] == 12)]
	fc30_df_all   = df_all[(df_all['FCLASS'] == 30)]
	fc32_df_all   = df_all[(df_all['FCLASS'] == 32)]
 	# By Screenline
	sl_1_df_all    = df_all[(df_all['SCRNLINE1'] ==  1) | (df_all['SCRNLINE2'] ==  1)]
	sl_2_df_all    = df_all[(df_all['SCRNLINE1'] ==  2) | (df_all['SCRNLINE2'] ==  2)]
	sl_3_df_all    = df_all[(df_all['SCRNLINE1'] ==  3) | (df_all['SCRNLINE2'] ==  3)]
	sl_4_df_all    = df_all[(df_all['SCRNLINE1'] ==  4) | (df_all['SCRNLINE2'] ==  4)]
	sl_5_df_all    = df_all[(df_all['SCRNLINE1'] ==  5) | (df_all['SCRNLINE2'] ==  5)]
	sl_6_df_all    = df_all[(df_all['SCRNLINE1'] ==  6) | (df_all['SCRNLINE2'] ==  6)]
	sl_7_df_all    = df_all[(df_all['SCRNLINE1'] ==  7) | (df_all['SCRNLINE2'] ==  7)]
	sl_8_df_all    = df_all[(df_all['SCRNLINE1'] ==  8) | (df_all['SCRNLINE2'] ==  8)]
	sl_9_df_all    = df_all[(df_all['SCRNLINE1'] ==  9) | (df_all['SCRNLINE2'] ==  9)]
	sl_10_df_all   = df_all[(df_all['SCRNLINE1'] == 10) | (df_all['SCRNLINE2'] == 10)]
	sl_11_df_all   = df_all[(df_all['SCRNLINE1'] == 11) | (df_all['SCRNLINE2'] == 11)]
	sl_12_df_all   = df_all[(df_all['SCRNLINE1'] == 12) | (df_all['SCRNLINE2'] == 12)]
	sl_13_df_all   = df_all[(df_all['SCRNLINE1'] == 13) | (df_all['SCRNLINE2'] == 13)]
	#sl_14_df_all   = df_all[(df_all['SCRNLINE1'] == 14) | (df_all['SCRNLINE2'] == 14)]
	#sl_15_df_all   = df_all[(df_all['SCRNLINE1'] == 15) | (df_all['SCRNLINE2'] == 15)]
	#sl_16_df_all   = df_all[(df_all['SCRNLINE1'] == 16) | (df_all['SCRNLINE2'] == 16)]
	#sl_17_df_all   = df_all[(df_all['SCRNLINE1'] == 17) | (df_all['SCRNLINE2'] == 17)]
	#sl_18_df_all   = df_all[(df_all['SCRNLINE1'] == 18) | (df_all['SCRNLINE2'] == 18)]
	#sl_19_df_all   = df_all[(df_all['SCRNLINE1'] == 19) | (df_all['SCRNLINE2'] == 19)]
	#sl_20_df_all   = df_all[(df_all['SCRNLINE1'] == 20) | (df_all['SCRNLINE2'] == 20)]
	#sl_21_df_all   = df_all[(df_all['SCRNLINE1'] == 21) | (df_all['SCRNLINE2'] == 21)]
	#sl_22_df_all   = df_all[(df_all['SCRNLINE1'] == 22) | (df_all['SCRNLINE2'] == 22)]
	#sl_23_df_all   = df_all[(df_all['SCRNLINE1'] == 23) | (df_all['SCRNLINE2'] == 23)]
	#sl_24_df_all   = df_all[(df_all['SCRNLINE1'] == 24) | (df_all['SCRNLINE2'] == 24)]
	#sl_25_df_all   = df_all[(df_all['SCRNLINE1'] == 25) | (df_all['SCRNLINE2'] == 25)]
	#sl_26_df_all   = df_all[(df_all['SCRNLINE1'] == 26) | (df_all['SCRNLINE2'] == 26)]
	
	
	# Build list of dataframes to loop thru
	df_list_all = [count_df_all,#internal_df_all,external_df_all,
					under_5k_df_all,btwn_5_10k_df_all,btwn_10_15k_df_all,btwn_15_20k_df_all,btwn_20_30k_df_all,btwn_30_40k_df_all,btwn_40_50k_df_all,
					fc1_df_all,fc2_df_all,fc3_df_all,fc4_df_all,fc5_df_all,fc6_df_all,fc7_df_all,fc8_df_all,fc9_df_all,fc10_df_all,fc11_df_all,fc12_df_all,
					fc30_df_all,fc32_df_all,
					sl_1_df_all,sl_2_df_all,sl_3_df_all,sl_4_df_all,sl_5_df_all,sl_6_df_all,sl_7_df_all,sl_8_df_all,sl_9_df_all,sl_10_df_all,sl_11_df_all,
					sl_12_df_all,sl_13_df_all]
	
	
	# Calculate Auto Total VMT and Total VHT from each dataframe and save in results dataframe
	y = auto_loc
	for i in df_list_all:
		if len(i) == 0: #sum(i.Auto_Flow) == 0.0:
			y = y + 1
			continue
		else:
			results_df.at[y,"Total VMT"]       = vmt(i.Auto_Flow,i.LENGTH)
			results_df.at[y,"Total VHT"]       = vht_dly(i.AM_Auto_Flow,i.CONGTIME_AM_C,i.PM_Auto_Flow,i.CONGTIME_PM_C,i.OP_Auto_Flow,i.CONGTIME_OP_C)
			y = y + 1

	# Calculate SUT Total VMT and Total VHT from each dataframe and save in results dataframe
	y = sut_loc
	for i in df_list_all:
		if len(i) == 0: #sum(i.Auto_Flow) == 0.0:
			y = y + 1
			continue
		else:
			results_df.at[y,"Total VMT"]       = vmt(i.SUT_Flow,i.LENGTH)
			results_df.at[y,"Total VHT"]       = vht_dly(i.AM_SUT_Flow,i.CONGTIME_AM_S,i.PM_SUT_Flow,i.CONGTIME_PM_S,i.OP_SUT_Flow,i.CONGTIME_OP_S)
			y = y + 1

	# Calculate MUT Total VMT and Total VHT from each dataframe and save in results dataframe
	y = mut_loc
	for i in df_list_all:
		if len(i) == 0: #sum(i.Auto_Flow) == 0.0:
			y = y + 1
			continue
		else:
			results_df.at[y,"Total VMT"]       = vmt(i.MUT_Flow,i.LENGTH)
			results_df.at[y,"Total VHT"]       = vht_dly(i.AM_MUT_Flow,i.CONGTIME_AM_M,i.PM_MUT_Flow,i.CONGTIME_PM_M,i.OP_MUT_Flow,i.CONGTIME_OP_M)
			y = y + 1

	# Calculate All Modes Total VMT and Total VHT from each dataframe and save in results dataframe
	y = allmodes_loc
	a = auto_loc
	s = sut_loc
	m = mut_loc
	for i in df_list_all:
		if len(i) == 0: #sum(i.Tot_Flow) == 0.0:
			y = y + 1
			continue
		else:
			results_df.at[y,"Total VMT"]           = results_df.at[a,"Total VMT"] + results_df.at[s,"Total VMT"] + results_df.at[m,"Total VMT"]        # vmt(i.Tot_Flow,i.LENGTH)
			results_df.at[y,"Total VHT"]           = results_df.at[a,"Total VHT"] + results_df.at[s,"Total VHT"] + results_df.at[m,"Total VHT"]        # vht(i.AM_Tot_Flow,i.CONGTIME_AM,i.MD_Tot_Flow,i.CONGTIME_MD,i.PM_Tot_Flow,i.CONGTIME_PM,i.NI_Tot_Flow,i.CONGTIME_NT)
			y = y + 1
			a = a + 1
			s = s + 1
			m = m + 1


	# Apply the formatting function to specific columns
	results_df['Percent Error'] = format_percent(results_df['Percent Error'])
	results_df['Percent RMSE'] = format_percent(results_df['Percent RMSE'])	
	results_df['Total VMT'] = format_commas(results_df['Total VMT'])
	results_df['Total VHT'] = format_commas(results_df['Total VHT'])
	results_df['Number of Observations'] = format_commas(results_df['Number of Observations'])
	results_df['Sum of Counts'] = format_commas(results_df['Sum of Counts'])
	results_df['Mean of Counts'] = format_commas(results_df['Mean of Counts'])
	results_df['Median of Counts'] = format_commas(results_df['Median of Counts'])
	results_df['Count VMT, Links with Counts'] = format_commas(results_df['Count VMT, Links with Counts'])
	results_df['Modeled VMT, Links with Counts'] = format_commas(results_df['Modeled VMT, Links with Counts'])

	
	# Save Daily Summary file to new timestamped folder
	results_df.to_csv(proj_dir+"outputs/reports/ModelRun_"+date+"/Assignment Results/AssignmentSummary.csv")

# Transit Unlinked Trips Summary Table
def transit_report():
	
	# Pull Lines table attributes
	Name        = VisumPy.helpers.GetMulti(Visum.Net.Lines,"Name", activeOnly = True)
	Description = VisumPy.helpers.GetMulti(Visum.Net.Lines,"Emme_Description", activeOnly = True)
	AM_Trips    = VisumPy.helpers.GetMulti(Visum.Net.Lines,"AM_UL_TRIPS", activeOnly = True)
	PM_Trips    = VisumPy.helpers.GetMulti(Visum.Net.Lines,"PM_UL_TRIPS", activeOnly = True)
	OP_Trips    = VisumPy.helpers.GetMulti(Visum.Net.Lines,"OP_UL_TRIPS", activeOnly = True)
	DLY_Trips   = VisumPy.helpers.GetMulti(Visum.Net.Lines,"DLY_UL_TRIPS", activeOnly = True)

	# Make Visum list with link data
	summary_list = [Name, Description, AM_Trips, PM_Trips, OP_Trips, DLY_Trips]    
			
	# Put Visum link list into dataframe
	df = pd.DataFrame(np.column_stack(summary_list), columns = ['Name', 'Description', 'AM_Trips', 'PM_Trips', 'OP_Trips', 'DLY_Trips'])

	# Save Transit results to folder
	df.to_csv(proj_dir+"outputs/reports/ModelRun_"+date+"/Assignment Results/TransitSummary.csv")



# Daily
assignment_summary('AUTO_COUNT_DLY', 'SUT_COUNT_DLY', 'MUT_COUNT_DLY', 'TOT_COUNT_DLY', 'AUTO_VOL_DLY', 'SUT_VOL_DLY', 'MUT_VOL_DLY', 'TOT_VOL_DLY') # 'DAILY_LCV_VOL', 'AM3_CTIME_C', 'AM3_CTIME_T', 'Daily')  # Daily VHT Calculated from full day, so AM3_CTIME here is just a placeholder for the function

# Transit
transit_report()


