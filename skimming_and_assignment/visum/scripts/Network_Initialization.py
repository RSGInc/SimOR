# Setting up network links and connectors
# 11/12/2025 - Luke Gordon (RSG)
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



def net_initialization():

    # Constants from Config.yaml
    walk_speed              = config_data['Walk_Speed']              # 3.5 mph
    connector_vehicle_speed = config_data['Connector_Vehicle_Speed'] # 20 mph

    # LINKS
    # Pull Attributes
    no        = h.GetMulti(Visum.Net.Links,r"NO"        , activeOnly = False)
    from_node = h.GetMulti(Visum.Net.Links,r"FROMNODENO", activeOnly = False)
    to_node   = h.GetMulti(Visum.Net.Links,r"TONODENO"  , activeOnly = False)
    link_length    = h.GetMulti(Visum.Net.Links,r"LENGTH"    , activeOnly = False)

    # Make Visum list with data
    att_list = [no,from_node,to_node,link_length]
    
	# Put Visum list into dataframe
    link_df = pd.DataFrame(np.column_stack(att_list), columns = ['no','from_node','to_node','link_length'])
    
    # Convert NO, FromNode, and ToNode to Strings
    link_df['no']          = link_df['no'].astype(int).astype(str)
    link_df['from_node']   = link_df['from_node'].astype(int).astype(str)
    link_df['to_node']     = link_df['to_node'].astype(int).astype(str)
    # Convert Length to float
    link_df['link_length'] = link_df['link_length'].astype(float)

    # Calculate LINKSERIAL and Walk Time
    link_df['linkserial'] = link_df['no'] + '-' + link_df['from_node'] + '-' + link_df['to_node']  
    link_df['wlk_time']   = link_df['link_length'] / (walk_speed/3600)

    # Set Calculated attributes on ALL links
    h.SetMulti(Visum.Net.Links ,r"LINKSERIAL" , link_df['linkserial'], activeOnly = False)
    h.SetMulti(Visum.Net.Links ,r"T_PUTSYS(W)", link_df['wlk_time']  , activeOnly = False)


    # CONNECTORS
    # Pull Attributes
    cc_length    = h.GetMulti(Visum.Net.Connectors,r"LENGTH"      , activeOnly = False)
    tsys_holding = h.GetMulti(Visum.Net.Connectors,r"TSYS_HOLDING", activeOnly = False) # Holding field that has the default "TSysSet" values pre KnR processes

    # Make Visum list with data
    att_list = [cc_length,tsys_holding]
    
	# Put Visum list into dataframe
    cc_df = pd.DataFrame(np.column_stack(att_list), columns = ['cc_length','tsys_holding'])

    # Convert Length to float
    cc_df['cc_length'] = cc_df['cc_length'].astype(float)

    # Calculate default connector times
    cc_df['veh_time'] = cc_df['cc_length'] / (connector_vehicle_speed/3600)
    cc_df['wlk_time'] = cc_df['cc_length'] / (walk_speed/3600)

    # Set Calculated attributes on ALL connectors
    # Vehicles
    h.SetMulti(Visum.Net.Connectors ,r"ADDVAL1"      , cc_df['veh_time'], activeOnly = False)
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(C)"   , cc_df['veh_time'], activeOnly = False)
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(S)"   , cc_df['veh_time'], activeOnly = False)
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(SR2)" , cc_df['veh_time'], activeOnly = False)
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(SR3)" , cc_df['veh_time'], activeOnly = False)
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(MT)"  , cc_df['veh_time'], activeOnly = False)
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(HT)"  , cc_df['veh_time'], activeOnly = False)
    # Walk
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(WLK)" , cc_df['wlk_time'], activeOnly = False)
    h.SetMulti(Visum.Net.Connectors ,r"T0_TSYS(W)"   , cc_df['wlk_time'], activeOnly = False)
    # TSys (set to "holding" field which has the default values pre KnR processes)
    h.SetMulti(Visum.Net.Connectors ,r"TSYSSET"      , cc_df['tsys_holding'], activeOnly = False)


    #
    ## TEMPORARY, NEED TO REPLACE WITH ACTUAL TRAVEL TIME BY PERIOD
    #df['time'] = df['addval1']
#
    ## Mode VOTs
    #sov_low  = config_data['SOV_LOW_VOT']
    #sov_med  = config_data['SOV_MED_VOT']
    #sov_high = config_data['SOV_HI_VOT']
    #sr2_low  = config_data['SR2_LOW_VOT']
    #sr2_med  = config_data['SR2_MED_VOT']
    #sr2_high = config_data['SR2_HI_VOT']
    #sr3_low  = config_data['SR3_LOW_VOT']
    #sr3_med  = config_data['SR3_MED_VOT']
    #sr3_high = config_data['SR3_HI_VOT']
#
    ## Set AddVal2 to Cost in Time
    ## SOV, Low VOT
    #if   mode == "SOV" and vot == "Low":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sov_low) * 3600               # Gen Cost (Time in Seconds)
    ## SR2, Low VOT
    #elif mode == "SR2" and vot == "Low":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr2_low) * 3600               # Gen Cost (Time in Seconds)
    ## SR3, Low VOT
    #elif mode == "SR3" and vot == "Low":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr3_low) * 3600               # Gen Cost (Time in Seconds)
    ## SOV, Medium VOT
    #elif mode == "SOV" and vot == "Medium":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sov_med) * 3600               # Gen Cost (Time in Seconds)
    ## SR2, Medium VOT
    #elif mode == "SR2" and vot == "Medium":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr2_med) * 3600               # Gen Cost (Time in Seconds)
    ## SR3, Medium VOT
    #elif mode == "SR3" and vot == "Medium":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr3_med) * 3600               # Gen Cost (Time in Seconds)
    ## SOV, High VOT
    #elif mode == "SOV" and vot == "High":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sov_high) * 3600              # Gen Cost (Time in Seconds)
    ## SR2, High VOT
    #elif mode == "SR2" and vot == "High":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr2_high) * 3600              # Gen Cost (Time in Seconds)
    ## SR3, High VOT
    #elif mode == "SR3" and vot == "High":
    #    df['addval2'] = df['time'] + (df[period+'_'+mode+'_TOLL'] / sr3_high) * 3600              # Gen Cost (Time in Seconds)
#
    #
    ## Set tolls by period and mode
    #df['toll']    = df[period+'_'+mode+'_TOLL']                                                  # Money in Dollars 
#
    ## Set fields back in Visum
    ## Gen Cost
    #h.SetMulti(Visum.Net.Links ,r"ADDVAL2", df['addval2'])
    ## Toll
    #if mode == "SOV":
    #    h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(S)", df['toll'])
    #elif mode == "SR2":
    #    h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(SR2)", df['toll'])
    #elif mode == "SR3":
    #    h.SetMulti(Visum.Net.Links ,r"TOLL_PRTSYS(SR3)", df['toll'])
#
    #
#
#
#
    ## REPEAT FOR CONNECTORS
    ## Pull AddVals for skimming
    #addval1     = h.GetMulti(Visum.Net.Connectors,r"ADDVAL1"    , activeOnly = True)  # TEMPORARY, NEED TO REPLACE WITH ACTUAL TRAVEL TIME BY PERIOD USING VDF
#
    ## Make Visum list with link data
    #att_list = [addval1]
    #
	## Put Visum link list into dataframe
    #df = pd.DataFrame(np.column_stack(att_list), columns = ['addval1'])
    #
    ## TEMPORARY, NEED TO REPLACE WITH ACTUAL TRAVEL TIME BY PERIOD USING VDF AND VOLUME
    #df['time'] = df['addval1']
#
    ## Set fields back in Visum
    #h.SetMulti(Visum.Net.Connectors ,r"ADDVAL1", df['time'])
    #h.SetMulti(Visum.Net.Connectors ,r"ADDVAL2", df['time'])



# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

## Pull "Code" field from procedure sequence containing Code, DSegCode, and filename
#procedure_code = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like -> '[["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]'
#procedure_codes = eval(procedure_code)   # Example: outputs a list of lists like -> [["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]
#
## Loop thru each matrix set in the "Code" field and export
##for x in range(len(procedure_codes)):
#per  = procedure_codes[0]
#m    = procedure_codes[1]
#tval = procedure_codes[2]

net_initialization()

