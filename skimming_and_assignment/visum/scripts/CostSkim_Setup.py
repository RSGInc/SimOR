# Setting up for PrT cost skimming
# 6/24/2025 - Luke Gordon (RSG)
# Adapted from code from Chetan Joshi (PTV)

import tables
import numpy as np
import pandas as pd
import os
import VisumPy.helpers as h
import openmatrix as omx


def costskim_setup(period, mode, vot):
    
    # Links
    # Pull AddVals for skimming
    addval1     = h.GetMulti(Visum.Net.Links,r"ADDVAL1"    , activeOnly = True)  # TEMPORARY, NEED TO REPLACE WITH ACTUAL TRAVEL TIME BY PERIOD USING VDF 
    addval2     = h.GetMulti(Visum.Net.Links,r"ADDVAL2"    , activeOnly = True)
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
    att_list = [addval1,addval2,
                EA_SOV_TOLL,EA_SR2_TOLL,EA_SR3_TOLL,EA_MT_TOLL,EA_HT_TOLL,
                AM_SOV_TOLL,AM_SR2_TOLL,AM_SR3_TOLL,AM_MT_TOLL,AM_HT_TOLL,
                MD_SOV_TOLL,MD_SR2_TOLL,MD_SR3_TOLL,MD_MT_TOLL,MD_HT_TOLL,
                PM_SOV_TOLL,PM_SR2_TOLL,PM_SR3_TOLL,PM_MT_TOLL,PM_HT_TOLL,
                EV_SOV_TOLL,EV_SR2_TOLL,EV_SR3_TOLL,EV_MT_TOLL,EV_HT_TOLL]
    
	# Put Visum link list into dataframe
    df = pd.DataFrame(np.column_stack(att_list), columns = ['addval1','addval2',
                'EA_SOV_TOLL','EA_SR2_TOLL','EA_SR3_TOLL','EA_MT_TOLL','EA_HT_TOLL',
                'AM_SOV_TOLL','AM_SR2_TOLL','AM_SR3_TOLL','AM_MT_TOLL','AM_HT_TOLL',
                'MD_SOV_TOLL','MD_SR2_TOLL','MD_SR3_TOLL','MD_MT_TOLL','MD_HT_TOLL',
                'PM_SOV_TOLL','PM_SR2_TOLL','PM_SR3_TOLL','PM_MT_TOLL','PM_HT_TOLL',
                'EV_SOV_TOLL','EV_SR2_TOLL','EV_SR3_TOLL','EV_MT_TOLL','EV_HT_TOLL'])
    
    # TEMPORARY, NEED TO REPLACE WITH ACTUAL TRAVEL TIME BY PERIOD USING VDF AND VOLUME
    df['time'] = df['addval1']

    # Mode VOTs
    sov_low  = 3.39
    sov_med  = 7.49
    sov_high = 20.51
    sr2_low  = 5.11
    sr2_med  = 10.92
    sr2_high = 27.30
    sr3_low  = 7.76
    sr3_med  = 16.82
    sr3_high = 44.04

    # Set AddVal2 to Cost in Time
    # SOV, Low VOT
    if   mode == "SOV" and vot == "Low":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sov_low) * 3600               # Gen Cost (Time in Seconds)
    # SR2, Low VOT
    elif mode == "SR2" and vot == "Low":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr2_low) * 3600               # Gen Cost (Time in Seconds)
    # SR3, Low VOT
    elif mode == "SR3" and vot == "Low":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr3_low) * 3600               # Gen Cost (Time in Seconds)
    # SOV, Medium VOT
    elif mode == "SOV" and vot == "Medium":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sov_med) * 3600               # Gen Cost (Time in Seconds)
    # SR2, Medium VOT
    elif mode == "SR2" and vot == "Medium":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr2_med) * 3600               # Gen Cost (Time in Seconds)
    # SR3, Medium VOT
    elif mode == "SR3" and vot == "Medium":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr3_med) * 3600               # Gen Cost (Time in Seconds)
    # SOV, High VOT
    elif mode == "SOV" and vot == "High":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sov_high) * 3600              # Gen Cost (Time in Seconds)
    # SR2, High VOT
    elif mode == "SR2" and vot == "High":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr2_high) * 3600              # Gen Cost (Time in Seconds)
    # SR3, High VOT
    elif mode == "SR3" and vot == "High":
        df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr3_high) * 3600              # Gen Cost (Time in Seconds)

    
    # Set tolls by period and mode
    df['toll']    = df[period+'_'+mode+'_TOLL']                                                  # Money in Dollars 

    # Set fields back in Visum
    # Gen Cost
    h.SetMulti(Visum.Net.Links ,r"ADDVAL2", df['addval2'])
    # Toll
    if mode == "SOV":
        h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(S)", df['toll'])
    elif mode == "SR2":
        h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(SR2)", df['toll'])
    elif mode == "SR3":
        h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(SR3)", df['toll'])

    



    # REPEAT FOR CONNECTORS
    # Pull AddVals for skimming
    addval1     = h.GetMulti(Visum.Net.Connectors,r"ADDVAL1"    , activeOnly = True)  # TEMPORARY, NEED TO REPLACE WITH ACTUAL TRAVEL TIME BY PERIOD USING VDF

    # Make Visum list with link data
    att_list = [addval1]
    
	# Put Visum link list into dataframe
    df = pd.DataFrame(np.column_stack(att_list), columns = ['addval1'])
    
    # TEMPORARY, NEED TO REPLACE WITH ACTUAL TRAVEL TIME BY PERIOD USING VDF AND VOLUME
    df['time'] = df['addval1']

    # Set fields back in Visum
    h.SetMulti(Visum.Net.Connectors ,r"ADDVAL1", df['time'])
    h.SetMulti(Visum.Net.Connectors ,r"ADDVAL2", df['time'])



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

costskim_setup(per, m, tval)

