# Prep for Skimming for Oregon Metro
# 6/12/2025 - Luke Gordon (RSG)
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


def put_skim_setup(period):

    def ismode():  # isbrt, isscr, islrt, & iswes

        # Pull attributes
        sa_isbrt      = h.GetMulti(Visum.Net.StopAreas,r"isbrt", activeOnly = True)
        sa_isscr      = h.GetMulti(Visum.Net.StopAreas,r"isscr", activeOnly = True)
        sa_islrt      = h.GetMulti(Visum.Net.StopAreas,r"islrt", activeOnly = True)
        sa_iswes      = h.GetMulti(Visum.Net.StopAreas,r"iswes", activeOnly = True)
        sp_lrtsyscode = h.GetMulti(Visum.Net.StopAreas,r"FIRST:STOPPOINTS\DISTINCT:LINEROUTES\TSYSCODE", activeOnly = True)

        # Make Visum list with link data
        att_list = [sa_isbrt,sa_isscr,sa_islrt,sa_iswes,sp_lrtsyscode] 
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['sa_isbrt','sa_isscr','sa_islrt','sa_iswes','sp_lrtsyscode'])
        
        # Break out 'DISTINCT:LINEROUTES\TSYSCODE' field to separate by commas into individual columns	
        df[['sp_lrtsyscode']] = df[['sp_lrtsyscode']].astype(str)																													
        df = pd.concat([df,df['sp_lrtsyscode'].str.split(',', expand = True)], axis = 1)
        # Fill empty fields with None
        if 1 not in df:
            df[1] = None
        if 2 not in df:
            df[2] = None
        if 3 not in df:
            df[3] = None
        if 4 not in df:
            df[4] = None
        df = df.rename(columns = {0:'Mode1',1:'Mode2',2:'Mode3',3:'Mode4',4:'Mode5'})

        # Calculate fields
        df['isbrt'] = df.apply(lambda row: 1 if row['Mode1'] == 'a' or row['Mode2'] == 'a' or row['Mode3'] == 'a' or row['Mode4'] == 'a' or row['Mode5'] == 'a' else 0, axis=1)
        df['isscr'] = df.apply(lambda row: 1 if row['Mode1'] == 'e' or row['Mode2'] == 'e' or row['Mode3'] == 'e' or row['Mode4'] == 'e' or row['Mode5'] == 'e' else 0, axis=1)
        df['islrt'] = df.apply(lambda row: 1 if row['Mode1'] == 'l' or row['Mode2'] == 'l' or row['Mode3'] == 'l' or row['Mode4'] == 'l' or row['Mode5'] == 'l' else 0, axis=1)
        df['iswes'] = df.apply(lambda row: 1 if row['Mode1'] == 'r' or row['Mode2'] == 'r' or row['Mode3'] == 'r' or row['Mode4'] == 'r' or row['Mode5'] == 'r' else 0, axis=1)
    
        # Set fields back in Visum
        h.SetMulti(Visum.Net.StopAreas ,r"isbrt", df['isbrt'])
        h.SetMulti(Visum.Net.StopAreas ,r"isscr", df['isscr'])
        h.SetMulti(Visum.Net.StopAreas ,r"islrt", df['islrt'])
        h.SetMulti(Visum.Net.StopAreas ,r"iswes", df['iswes'])

    def headway(period): # Headway and Headway_Halved

        # Pull attributes
        tp_headwayhalved = h.GetMulti(Visum.Net.TimeProfiles,r"Headway_Halved", activeOnly = True)

        if period == 'EA':
            tp_periodheadway = h.GetMulti(Visum.Net.TimeProfiles,r"LINEROUTE\NT5", activeOnly = True)
        elif period == 'AM':
            tp_periodheadway = h.GetMulti(Visum.Net.TimeProfiles,r"LINEROUTE\AM4", activeOnly = True)
        elif period == 'MD':
            tp_periodheadway = h.GetMulti(Visum.Net.TimeProfiles,r"LINEROUTE\MD6", activeOnly = True)
        elif period == 'PM':
            tp_periodheadway = h.GetMulti(Visum.Net.TimeProfiles,r"LINEROUTE\PM4", activeOnly = True)
        elif period == 'EV':
            tp_periodheadway = h.GetMulti(Visum.Net.TimeProfiles,r"LINEROUTE\EV5", activeOnly = True)

        # Make Visum list with link data
        att_list = [tp_headwayhalved,tp_periodheadway]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['tp_headwayhalved','tp_periodheadway'])

        # Calculate fields
        df['tp_headwayhalved'] = (df['tp_periodheadway'] * 60) / 2  # Need to divide by 2 for Optimal Strategies to work (Headway = Wait Time)
    
        # Set fields back in Visum
        h.SetMulti(Visum.Net.TimeProfiles ,r"HEADWAY(AP)",    df['tp_headwayhalved']) # For Optimal Strategies, need headway = wait time


    def op_bushr(): # op_bushr on lineroutes and stopareas
        
        # Line Routes
        # Pull attributes
        lr_opbushr   = h.GetMulti(Visum.Net.LineRoutes,r"op_bushr", activeOnly = True)
        lr_opheadway = h.GetMulti(Visum.Net.LineRoutes,r"MD6", activeOnly = True)

        # Make Visum list with link data
        att_list = [lr_opbushr,lr_opheadway]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['lr_opbushr','lr_opheadway'])

        # Calculate fields
        df['lr_opbushr']   = df.apply(lambda row: 1 / (row['lr_opheadway'] / 60) if row['lr_opheadway'] != 0 else 0,axis=1)
    
        # Set field back in Visum
        h.SetMulti(Visum.Net.LineRoutes ,r"op_bushr", df['lr_opbushr'])

        
        # Stop Areas
        # Pull attributes
        sa_lropbushr = h.GetMulti(Visum.Net.StopAreas,r"FIRST:STOPPOINTS\SUM:LINEROUTES\OP_BUSHR", activeOnly = True)

        # Set field back in Visum
        h.SetMulti(Visum.Net.StopAreas ,r"op_bushr", sa_lropbushr)


    def stoptype(period): # Stop type & stop type constant

        # Pull attributes
        # Fields to set
        sa_sttyp   = h.GetMulti(Visum.Net.StopAreas,r"sttyp"  , activeOnly = True)
        sa_stcon   = h.GetMulti(Visum.Net.StopAreas,r"stcon"  , activeOnly = True)
        # Condition Fields
        sa_istc    = h.GetMulti(Visum.Net.StopAreas,r"istc"   , activeOnly = True)
        sa_istm    = h.GetMulti(Visum.Net.StopAreas,r"istm"   , activeOnly = True)
        sa_isbrt   = h.GetMulti(Visum.Net.StopAreas,r"isbrt"  , activeOnly = True)
        sa_isscr   = h.GetMulti(Visum.Net.StopAreas,r"isscr"  , activeOnly = True)
        sa_islrt   = h.GetMulti(Visum.Net.StopAreas,r"islrt"  , activeOnly = True)
        sa_iswes   = h.GetMulti(Visum.Net.StopAreas,r"iswes"  , activeOnly = True)
        sa_opbushr = h.GetMulti(Visum.Net.StopAreas,r"op_bushr", activeOnly = True)

        # Make Visum list with link data
        att_list = [sa_sttyp,sa_stcon,sa_istc,sa_istm ,sa_isbrt,sa_isscr,sa_islrt,sa_iswes,sa_opbushr]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['sa_sttyp','sa_stcon','sa_istc','sa_istm','sa_isbrt','sa_isscr','sa_islrt','sa_iswes','sa_opbushr'])

        # Convert condition fields & stop type constant to float
        df[['sa_stcon','sa_istc','sa_istm','sa_isbrt','sa_isscr','sa_islrt','sa_iswes','sa_opbushr']] = df[[
            'sa_stcon','sa_istc','sa_istm','sa_isbrt','sa_isscr','sa_islrt','sa_iswes','sa_opbushr']].astype(float)

        # Calculate Stop Type field
        for x in range(len(df)):
            if ((df.at[x,'sa_istc'] == 1) | (df.at[x,'sa_istm'] == 1) | (df.at[x,'sa_islrt'] == 1) | (df.at[x,'sa_iswes'] == 1)):
                df.at[x,'sa_sttyp'] = 'A,B,C'   # Is transit center, is transit mall, is LRT stop, is WES stop
            elif ((df.at[x,'sa_isbrt'] == 1) | (df.at[x,'sa_isscr'] == 1) | (df.at[x,'sa_opbushr'] >= 4)):
                df.at[x,'sa_sttyp'] = 'D'       # Is BRT stop, is streetcar stop, has >= 4 transit vehicles per hour
            else:
                df.at[x,'sa_sttyp'] = 'E'       # All stops with infrequent local bus service

        
        # Calculate Stop Type Constant field
        for y in range(len(df)):
            if period == 'AM' or period == 'PM':  # Peak
                if df.at[y,'sa_sttyp'] == 'A,B,C':
                    df.at[y,'sa_stcon'] = config_data['PkSTCabc']
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_stcon'] = config_data['PkSTCd']
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_stcon'] = config_data['PkSTCe']   
            else:                                 # Off-Peak
                if df.at[y,'sa_sttyp'] == 'A,B,C':
                    df.at[y,'sa_stcon'] = config_data['OpSTCabc']
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_stcon'] = config_data['OpSTCd']
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_stcon'] = config_data['OpSTCe']

        # Set fields back in Visum
        h.SetMulti(Visum.Net.StopAreas ,r"sttyp", df['sa_sttyp'])
        h.SetMulti(Visum.Net.StopAreas ,r"stcon", df['sa_stcon'])


    def waittime(period): # Wait time perception factor

        # Pull attributes
        sa_sttyp   = h.GetMulti(Visum.Net.StopAreas,r"sttyp"  , activeOnly = True)
        sa_wtpf    = h.GetMulti(Visum.Net.StopAreas,r"wtpf"  , activeOnly = True)

        # Make Visum list with link data
        att_list = [sa_sttyp,sa_wtpf]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['sa_sttyp','sa_wtpf'])

        # Calculate field
        for y in range(len(df)):
            if period == 'AM' or period == 'PM':  # Peak
                if df.at[y,'sa_sttyp'] == 'A,B,C':
                    df.at[y,'sa_wtpf'] = config_data['PkWTPFabc']
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_wtpf'] = config_data['PkWTPFd']
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_wtpf'] = config_data['PkWTPFe'] 
            else:                                 # Off-Peak
                if df.at[y,'sa_sttyp'] == 'A,B,C':
                    df.at[y,'sa_wtpf'] = config_data['OpWTPFabc']
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_wtpf'] = config_data['OpWTPFd']
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_wtpf'] = config_data['OpWTPFe']

        # Set fields back in Visum
        h.SetMulti(Visum.Net.StopAreas ,r"wtpf", df['sa_wtpf'])

    
    def invehicleperceptionfactor(period): # In-vehicle perception factors

        # Pull attributes
        tp_tsyscode  = h.GetMulti(Visum.Net.TimeProfiles,r"TSYSCODE", activeOnly = True)
        tp_ivpf      = h.GetMulti(Visum.Net.TimeProfiles,r"ivpf"    , activeOnly = True)

        # Make Visum list with link data
        att_list = [tp_tsyscode,tp_ivpf]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['tp_tsyscode','tp_ivpf'])

        # Calculate field
        for y in range(len(df)):
            if period == 'AM' or period == 'PM':  # Peak
                if df.at[y,'tp_tsyscode'] == 'a':
                    df.at[y,'tp_ivpf'] = config_data['PkIVPFa']
                elif df.at[y,'tp_tsyscode'] == 'l':
                    df.at[y,'tp_ivpf'] = config_data['PkIVPFl']
                elif df.at[y,'tp_tsyscode'] == 'r':
                    df.at[y,'tp_ivpf'] = config_data['PkIVPFr']
                else:
                    df.at[y,'tp_ivpf'] = config_data['PkIVPFelse']
            else:                                 # Off-Peak
                if df.at[y,'tp_tsyscode'] == 'a':
                    df.at[y,'tp_ivpf'] = config_data['OpIVPFa']
                elif df.at[y,'tp_tsyscode'] == 'l':
                    df.at[y,'tp_ivpf'] = config_data['OpIVPFl']
                elif df.at[y,'tp_tsyscode'] == 'r':
                    df.at[y,'tp_ivpf'] = config_data['OpIVPFr']
                else:
                    df.at[y,'tp_ivpf'] = config_data['OpIVPFelse']

        # Set fields back in Visum
        h.SetMulti(Visum.Net.TimeProfiles ,r"ivpf", df['tp_ivpf'])


    def boardingpenalty(period):  # Boarding penalty (seconds)

        # Pull attributes
        tp_tsyscode  = h.GetMulti(Visum.Net.TimeProfiles,r"TSYSCODE", activeOnly = True)
        tp_brdpen    = h.GetMulti(Visum.Net.TimeProfiles,r"brdpen"  , activeOnly = True)

        # Make Visum list with link data
        att_list = [tp_tsyscode,tp_brdpen]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['tp_tsyscode','tp_brdpen'])

        # Calculate field
        for y in range(len(df)):
            if period == 'AM' or period == 'PM':  # Peak
                if df.at[y,'tp_tsyscode'] == 'l':
                    df.at[y,'tp_brdpen'] = config_data['PkBrdPl']
                elif df.at[y,'tp_tsyscode'] == 'r':
                    df.at[y,'tp_brdpen'] = config_data['PkBrdPr']
                elif df.at[y,'tp_tsyscode'] == 'a':
                    df.at[y,'tp_brdpen'] = config_data['PkBrdPa']
                elif df.at[y,'tp_tsyscode'] == 'e':
                    df.at[y,'tp_brdpen'] = config_data['PkBrdPe']
                else:
                    df.at[y,'tp_brdpen'] = config_data['PkBrdPelse']
            else:                                 # Off-Peak
                if df.at[y,'tp_tsyscode'] == 'l':
                    df.at[y,'tp_brdpen'] = config_data['OpBrdPl']
                elif df.at[y,'tp_tsyscode'] == 'r':
                    df.at[y,'tp_brdpen'] = config_data['OpBrdPr']
                elif df.at[y,'tp_tsyscode'] == 'a':
                    df.at[y,'tp_brdpen'] = config_data['OpBrdPa']
                elif df.at[y,'tp_tsyscode'] == 'e':
                    df.at[y,'tp_brdpen'] = config_data['OpBrdPe']
                else:
                    df.at[y,'tp_brdpen'] = config_data['OpBrdPelse']

        # Add global boarding penalty
        for y in range(len(df)):
            df.at[y,'tp_brdpen'] = df.at[y,'tp_brdpen'] + config_data['BrdPenGlb']

        # Set fields back in Visum
        h.SetMulti(Visum.Net.TimeProfiles ,r"brdpen", df['tp_brdpen'])


    def dwelltime():

        # Pull attributes
        tpi_tsyscode  = h.GetMulti(Visum.Net.TimeProfileItems,r"TIMEPROFILE\TSYSCODE"  , activeOnly = True)
        tpi_emmedwt   = h.GetMulti(Visum.Net.TimeProfileItems,r"LINEROUTEITEM\EMME_DWT", activeOnly = True)
        tpi_prelength = h.GetMulti(Visum.Net.TimeProfileItems,r"PreLength"             , activeOnly = True)
        tpi_dwelltime = h.GetMulti(Visum.Net.TimeProfileItems,r"DWELL_TIME"            , activeOnly = True)


        # Make Visum list with link data
        att_list = [tpi_tsyscode,tpi_emmedwt,tpi_prelength,tpi_dwelltime]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['tpi_tsyscode','tpi_emmedwt','tpi_prelength','tpi_dwelltime'])

        # Convert fields to float
        df[['tpi_emmedwt','tpi_prelength','tpi_dwelltime']] = df[['tpi_emmedwt','tpi_prelength','tpi_dwelltime']].astype(float)

        # Calculate field
        for y in range(len(df)):
            if df.at[y,'tpi_tsyscode'] == 'b':  # Local Bus dwell time based on prelength and Emme_DWT
                df.at[y,'tpi_dwelltime'] = df.at[y,'tpi_emmedwt'] * 60 * df.at[y,'tpi_prelength']
            else:                               # Non-Local Bus dwell time based on Emme_DWT only
                df.at[y,'tpi_dwelltime'] = df.at[y,'tpi_emmedwt'] * 60

        # Set fields back in Visum
        h.SetMulti(Visum.Net.TimeProfileItems ,r"DWELL_TIME", df['tpi_dwelltime'])


    def calc_ttf(ft, timau, length, us1, default_speed):  # INPUT TO RUNTIME FUNCTION
        if us1 <= 0:
            us1 = default_speed

        if length:
            transit_time = 3600*length / default_speed

            if timau < 999:
                if ft == 1:
                    transit_time = timau * config_data['ft1']
                elif ft == 2:
                    transit_time = timau * config_data['ft2']
                elif ft == 3:
                    transit_time = timau * config_data['ft3']
                elif ft == 4:
                    transit_time = timau * config_data['ft4']
                elif ft == 5:
                    transit_time = 60* (60 * length / us1)
                elif ft == 6:
                    transit_time = 60* (60 * length / us1 + 60 * length / 180)
                elif ft ==11:
                    transit_time = timau * config_data['ft11']
                elif ft ==12:
                    transit_time = timau * config_data['ft12']
                elif ft ==13:
                    transit_time = timau * config_data['ft13']
                elif ft ==14:
                    transit_time = timau * config_data['ft14']
                elif ft == 15:
                    transit_time = 60* (60 * length / us1)
                elif ft == 16:
                    transit_time = 60* (60 * length / us1 + 60 * length / 180)
                elif ft == 21:
                    transit_time = timau * config_data['ft21']
                elif ft == 22:
                    transit_time = timau * config_data['ft22']
        else:
            transit_time = 1

        return transit_time

    def runtime(period):
        tpitems = Visum.Net.TimeProfileItems.GetMultipleAttributes(["LINEROUTEITEM\\EMME_TTFINDEX", "SUM:USEDLINEROUTEITEMS\\OUTLINK\\"+period+"_TTC","SUM:USEDLINEROUTEITEMS\\POSTLENGTH", 
                                                                    "LINEROUTEITEM\\EMME_DATA1"])
        result  = []

        default_speed = config_data['DefaultTransitSpeed'] # 30mph
        for ft, timau, length, us1 in tpitems:
            haul_time = calc_ttf(ft, timau, length, us1, default_speed)
            result.append([haul_time, ])

        Visum.Net.TimeProfileItems.SetMultipleAttributes(["RUN_TIME"], result)

    def combinerundwelltimes():
        
        # Pull attributes
        tpi_runtime    = h.GetMulti(Visum.Net.TimeProfileItems,r"RUN_TIME"     , activeOnly = True)
        tpi_dwelltime = h.GetMulti(Visum.Net.TimeProfileItems,r"DWELL_TIME" , activeOnly = True)

        # Make Visum list with link data
        att_list = [tpi_runtime,tpi_dwelltime]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['tpi_runtime','tpi_dwelltime'])

        # Convert fields to float
        df[['tpi_runtime','tpi_dwelltime']] = df[['tpi_runtime','tpi_dwelltime']].astype(float)

        # Calculate field
        df['tpi_runtime'] = df['tpi_runtime'] +  df['tpi_dwelltime']

        # Set fields back in Visum
        h.SetMulti(Visum.Net.TimeProfileItems ,r"RUN_TIME", df['tpi_runtime'])



    # RUN FUNCTIONS
    # Setting Skim Attributes
    ismode()
    headway(period)
    op_bushr()
    stoptype(period)
    waittime(period)
    invehicleperceptionfactor(period)
    boardingpenalty(period)
    # Setting Dwell and Run times
    dwelltime()
    runtime(period)
    #combinerundwelltimes()  # Not needed in Visum 26


per = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like 'AM' from AM in the code box
put_skim_setup(per)

