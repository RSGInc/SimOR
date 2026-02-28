# Setting up for PrT cost skimming
# 6/24/2025 - Luke Gordon (RSG)
# Adapted from code from Chetan Joshi (PTV)

import tables
import numpy as np
import pandas as pd
import os
import VisumPy.helpers as h
import openmatrix as omx
import yaml


# YAML file constants management
# Get the folder where this script lives
script_dir = os.path.dirname(os.path.abspath(__file__))

# Go up directories to reach SimOR directory
folder_a = script_dir
while True:
    if os.path.basename(folder_a) == "SimOR":
        break
    parent = os.path.dirname(folder_a)
    if parent == folder_a:  # reached root directory
        raise FileNotFoundError("Folder 'SimOR' not found in parent hierarchy.")
    folder_a = parent

# Read the path from the pointer file
with open(os.path.join(folder_a, 'path_config.txt'), 'r') as f:
    yaml_relative_path = f.read().strip()

# Build the absolute path to the YAML file
yaml_path = os.path.join(folder_a, yaml_relative_path)

# Pull constants from the YAML file
with open(yaml_path, 'r') as file:
    config_data = yaml.safe_load(file)



def prt_skim_setup(period, mode, vot):
    
    # LINKS
    # Pull Travel Time by period for skimming
    EA_TTC      = h.GetMulti(Visum.Net.Links,r"EA_TTC"    , activeOnly = True)
    AM_TTC      = h.GetMulti(Visum.Net.Links,r"AM_TTC"    , activeOnly = True)
    MD_TTC      = h.GetMulti(Visum.Net.Links,r"MD_TTC"    , activeOnly = True)
    PM_TTC      = h.GetMulti(Visum.Net.Links,r"PM_TTC"    , activeOnly = True)
    EV_TTC      = h.GetMulti(Visum.Net.Links,r"EV_TTC"    , activeOnly = True)
    # Pull Toll Fields
    EA_SOV_TOLL = h.GetMulti(Visum.Net.Links,r"EA_SOV_TOLL", activeOnly = True)
    EA_SR2_TOLL = h.GetMulti(Visum.Net.Links,r"EA_SR2_TOLL", activeOnly = True)
    EA_SR3_TOLL = h.GetMulti(Visum.Net.Links,r"EA_SR3_TOLL", activeOnly = True)
    EA_MT_TOLL  = h.GetMulti(Visum.Net.Links,r"EA_MT_TOLL" , activeOnly = True)
    EA_HT_TOLL  = h.GetMulti(Visum.Net.Links,r"EA_HT_TOLL" , activeOnly = True)
    AM_SOV_TOLL = h.GetMulti(Visum.Net.Links,r"AM_SOV_TOLL", activeOnly = True)
    AM_SR2_TOLL = h.GetMulti(Visum.Net.Links,r"AM_SR2_TOLL", activeOnly = True)
    AM_SR3_TOLL = h.GetMulti(Visum.Net.Links,r"AM_SR3_TOLL", activeOnly = True)
    AM_MT_TOLL  = h.GetMulti(Visum.Net.Links,r"AM_MT_TOLL" , activeOnly = True)
    AM_HT_TOLL  = h.GetMulti(Visum.Net.Links,r"AM_HT_TOLL" , activeOnly = True)
    MD_SOV_TOLL = h.GetMulti(Visum.Net.Links,r"MD_SOV_TOLL", activeOnly = True)
    MD_SR2_TOLL = h.GetMulti(Visum.Net.Links,r"MD_SR2_TOLL", activeOnly = True)
    MD_SR3_TOLL = h.GetMulti(Visum.Net.Links,r"MD_SR3_TOLL", activeOnly = True)
    MD_MT_TOLL  = h.GetMulti(Visum.Net.Links,r"MD_MT_TOLL" , activeOnly = True)
    MD_HT_TOLL  = h.GetMulti(Visum.Net.Links,r"MD_HT_TOLL" , activeOnly = True)
    PM_SOV_TOLL = h.GetMulti(Visum.Net.Links,r"PM_SOV_TOLL", activeOnly = True)
    PM_SR2_TOLL = h.GetMulti(Visum.Net.Links,r"PM_SR2_TOLL", activeOnly = True)
    PM_SR3_TOLL = h.GetMulti(Visum.Net.Links,r"PM_SR3_TOLL", activeOnly = True)
    PM_MT_TOLL  = h.GetMulti(Visum.Net.Links,r"PM_MT_TOLL" , activeOnly = True)
    PM_HT_TOLL  = h.GetMulti(Visum.Net.Links,r"PM_HT_TOLL" , activeOnly = True)
    EV_SOV_TOLL = h.GetMulti(Visum.Net.Links,r"EV_SOV_TOLL", activeOnly = True)
    EV_SR2_TOLL = h.GetMulti(Visum.Net.Links,r"EV_SR2_TOLL", activeOnly = True)
    EV_SR3_TOLL = h.GetMulti(Visum.Net.Links,r"EV_SR3_TOLL", activeOnly = True)
    EV_MT_TOLL  = h.GetMulti(Visum.Net.Links,r"EV_MT_TOLL" , activeOnly = True)
    EV_HT_TOLL  = h.GetMulti(Visum.Net.Links,r"EV_HT_TOLL" , activeOnly = True)


    # Make Visum list with link data
    att_list = [EA_TTC,AM_TTC,MD_TTC,PM_TTC,EV_TTC,
                EA_SOV_TOLL,EA_SR2_TOLL,EA_SR3_TOLL,EA_MT_TOLL,EA_HT_TOLL,
                AM_SOV_TOLL,AM_SR2_TOLL,AM_SR3_TOLL,AM_MT_TOLL,AM_HT_TOLL,
                MD_SOV_TOLL,MD_SR2_TOLL,MD_SR3_TOLL,MD_MT_TOLL,MD_HT_TOLL,
                PM_SOV_TOLL,PM_SR2_TOLL,PM_SR3_TOLL,PM_MT_TOLL,PM_HT_TOLL,
                EV_SOV_TOLL,EV_SR2_TOLL,EV_SR3_TOLL,EV_MT_TOLL,EV_HT_TOLL]
    
	# Put Visum link list into dataframe
    df = pd.DataFrame(np.column_stack(att_list), columns = [
                'EA_TTC','AM_TTC','MD_TTC','PM_TTC','EV_TTC',
                'EA_SOV_TOLL','EA_SR2_TOLL','EA_SR3_TOLL','EA_MT_TOLL','EA_HT_TOLL',
                'AM_SOV_TOLL','AM_SR2_TOLL','AM_SR3_TOLL','AM_MT_TOLL','AM_HT_TOLL',
                'MD_SOV_TOLL','MD_SR2_TOLL','MD_SR3_TOLL','MD_MT_TOLL','MD_HT_TOLL',
                'PM_SOV_TOLL','PM_SR2_TOLL','PM_SR3_TOLL','PM_MT_TOLL','PM_HT_TOLL',
                'EV_SOV_TOLL','EV_SR2_TOLL','EV_SR3_TOLL','EV_MT_TOLL','EV_HT_TOLL'])

    # Mode VOTs
    sov_low  = config_data['SOV_LOW_VOT']
    sov_med  = config_data['SOV_MED_VOT']
    sov_high = config_data['SOV_HI_VOT']
    sr2_low  = config_data['SR2_LOW_VOT']
    sr2_med  = config_data['SR2_MED_VOT']
    sr2_high = config_data['SR2_HI_VOT']
    sr3_low  = config_data['SR3_LOW_VOT']
    sr3_med  = config_data['SR3_MED_VOT']
    sr3_high = config_data['SR3_HI_VOT']

    # Set AddVal2 to Cost in Time
    # SOV, Low VOT
    if   mode == "SOV" and vot == "Low":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sov_low) * 3600               # Gen Cost (Time in Seconds)
    # SR2, Low VOT
    elif mode == "SR2" and vot == "Low":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sr2_low) * 3600               # Gen Cost (Time in Seconds)
    # SR3, Low VOT
    elif mode == "SR3" and vot == "Low":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sr3_low) * 3600               # Gen Cost (Time in Seconds)
    # SOV, Medium VOT
    elif mode == "SOV" and vot == "Medium":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sov_med) * 3600               # Gen Cost (Time in Seconds)
    # SR2, Medium VOT
    elif mode == "SR2" and vot == "Medium":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sr2_med) * 3600               # Gen Cost (Time in Seconds)
    # SR3, Medium VOT
    elif mode == "SR3" and vot == "Medium":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sr3_med) * 3600               # Gen Cost (Time in Seconds)
    # SOV, High VOT
    elif mode == "SOV" and vot == "High":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sov_high) * 3600              # Gen Cost (Time in Seconds)
    # SR2, High VOT
    elif mode == "SR2" and vot == "High":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sr2_high) * 3600              # Gen Cost (Time in Seconds)
    # SR3, High VOT
    elif mode == "SR3" and vot == "High":
        df['GenCost'] = df[period+'_TTC'] + (df[period+'_'+mode+'_TOLL'] / sr3_high) * 3600              # Gen Cost (Time in Seconds)
                                           

    # Set fields back in Visum
    # Period Travel Time
    h.SetMulti(Visum.Net.Links ,r"ADDVAL1", df[period+'_TTC'], activeOnly = True)   # Time in seconds
    # Gen Cost
    h.SetMulti(Visum.Net.Links ,r"ADDVAL2", df['GenCost'], activeOnly = True)       # Gen Cost (Time in Seconds)
    # Toll
    if mode == "SOV":
        h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(S)",   df[period+'_'+mode+'_TOLL'], activeOnly = True)   # Money in Dollars 
    elif mode == "SR2":
        h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(SR2)", df[period+'_'+mode+'_TOLL'], activeOnly = True)   # Money in Dollars 
    elif mode == "SR3":
        h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(SR3)", df[period+'_'+mode+'_TOLL'], activeOnly = True)   # Money in Dollars 

    

    # CONNECTORS
    # Pull Connector Time for skimming (set to Length / (20mph * 3600) in Network_Initialization.py for all PrT modes)
    DefaultTime  = h.GetMulti(Visum.Net.Connectors,r"T0_TSYS(S)", activeOnly = True) 

    # Make Visum list with link data
    att_list = [DefaultTime]
    
	# Put Visum link list into dataframe
    df = pd.DataFrame(np.column_stack(att_list), columns = ['DefaultTime'])

    # Set fields back in Visum
    h.SetMulti(Visum.Net.Connectors ,r"ADDVAL1", df['DefaultTime'], activeOnly = True) # Travel time
    h.SetMulti(Visum.Net.Connectors ,r"ADDVAL2", df['DefaultTime'], activeOnly = True) # GenCost = Travel time, no tolls on connectors



# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

# Pull "Code" field from procedure sequence containing Code, DSegCode, and filename
procedure_code = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like -> '[["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]'
procedure_codes = eval(procedure_code)   # Example: outputs a list of lists like -> [["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]

# Loop thru each matrix set in the "Code" field and export
#for x in range(len(procedure_codes)):
per  = procedure_codes[0]
m    = procedure_codes[1]
tval = procedure_codes[2]

prt_skim_setup(per, m, tval)

