# Prep for Skimming for Oregon Metro
# 6/12/2025 - Luke Gordon (RSG)
# Adapted from code from Chetan Joshi (PTV)

import tables
import numpy as np
import pandas as pd
import os
import VisumPy.helpers as h
import openmatrix as omx


def skim_setup(period):

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
        # Change Screenline field names	
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
        tp_emmeheadway   = h.GetMulti(Visum.Net.TimeProfiles,r"Emme_Headway", activeOnly = True)
        tp_headwayhalved = h.GetMulti(Visum.Net.TimeProfiles,r"Headway_Halved", activeOnly = True)
        
        if period == 'AM' or period == 'PM':
            tp_periodheadway = h.GetMulti(Visum.Net.TimeProfiles,r"LINEROUTE\EMME_DATA1", activeOnly = True)
        else:
            tp_periodheadway = h.GetMulti(Visum.Net.TimeProfiles,r"LINEROUTE\EMME_DATA2", activeOnly = True)

        # Make Visum list with link data
        att_list = [tp_emmeheadway,tp_periodheadway,tp_headwayhalved]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['tp_emmeheadway','tp_periodheadway','tp_headwayhalved'])

        # Calculate fields
        df['tp_emmeheadway']   = df['tp_periodheadway'] * 60
        df['tp_headwayhalved'] = df['tp_emmeheadway'] / 2
    
        # Set fields back in Visum
        h.SetMulti(Visum.Net.TimeProfiles ,r"Emme_Headway", df['tp_emmeheadway'])
        h.SetMulti(Visum.Net.TimeProfiles ,r"Headway_Halved", df['tp_headwayhalved'])


    def op_bushr(): # op_bushr on lineroutes and stopareas
        
        # Line Routes
        # Pull attributes
        lr_opbushr   = h.GetMulti(Visum.Net.LineRoutes,r"op_bushr", activeOnly = True)
        lr_opheadway = h.GetMulti(Visum.Net.LineRoutes,r"EMME_DATA2", activeOnly = True)

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
                    df.at[y,'sa_stcon'] = 0.1582
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_stcon'] = 0.0531
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_stcon'] = 0.0000   
            else:                                 # Off-Peak
                if df.at[y,'sa_sttyp'] == 'A,B,C':
                    df.at[y,'sa_stcon'] = 0.1075
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_stcon'] = 0.0756
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_stcon'] = 0.0000

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
                    df.at[y,'sa_wtpf'] = 0.88
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_wtpf'] = 0.93
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_wtpf'] = 1.00   
            else:                                 # Off-Peak
                if df.at[y,'sa_sttyp'] == 'A,B,C':
                    df.at[y,'sa_wtpf'] = 0.86
                elif df.at[y,'sa_sttyp'] == 'D':
                    df.at[y,'sa_wtpf'] = 0.94
                elif df.at[y,'sa_sttyp'] == 'E':
                    df.at[y,'sa_wtpf'] = 1.00

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
                    df.at[y,'tp_ivpf'] = 0.95
                elif ((df.at[y,'tp_tsyscode'] == 'l') or (df.at[y,'tp_tsyscode'] == 'r')):
                    df.at[y,'tp_ivpf'] = 0.88
                else:
                    df.at[y,'tp_ivpf'] = 1.00   
            else:                                 # Off-Peak
                if df.at[y,'tp_tsyscode'] == 'a':
                    df.at[y,'tp_ivpf'] = 0.95
                elif ((df.at[y,'tp_tsyscode'] == 'l') or (df.at[y,'tp_tsyscode'] == 'r')):
                    df.at[y,'tp_ivpf'] = 0.86
                else:
                    df.at[y,'tp_ivpf'] = 1.00

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
                if ((df.at[y,'tp_tsyscode'] == 'l') or (df.at[y,'tp_tsyscode'] == 'r')):
                    df.at[y,'tp_brdpen'] = 000.0
                elif ((df.at[y,'tp_tsyscode'] == 'a') or (df.at[y,'tp_tsyscode'] == 'e')):
                    df.at[y,'tp_brdpen'] = 372.0
                else:
                    df.at[y,'tp_brdpen'] = 439.8
            else:                                 # Off-Peak
                if ((df.at[y,'tp_tsyscode'] == 'l') or (df.at[y,'tp_tsyscode'] == 'r')):
                    df.at[y,'tp_brdpen'] = 000.0
                elif ((df.at[y,'tp_tsyscode'] == 'a') or (df.at[y,'tp_tsyscode'] == 'e')):
                    df.at[y,'tp_brdpen'] = 166.8
                else:
                    df.at[y,'tp_brdpen'] = 540.6

        # Add global boarding penalty
        for y in range(len(df)):
            df.at[y,'tp_brdpen'] = df.at[y,'tp_brdpen'] + 231

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
                    transit_time = timau * 1.15
                elif ft == 2:
                    transit_time = timau * 1.20
                elif ft == 3:
                    transit_time = timau
                elif ft == 4:
                    transit_time = timau * 1.09
                elif ft == 5:
                    transit_time = 60* (60 * length / us1)
                elif ft == 6:
                    transit_time = 60* (60 * length / us1 + 60 * length / 180)
                elif ft ==11:
                    transit_time = timau * 1.15
                elif ft ==12:
                    transit_time = timau * 1.30
                elif ft ==13:
                    transit_time = timau
                elif ft ==14:
                    transit_time =timau * 1.09
                elif ft == 15:
                    transit_time = 60* (60 * length / us1)
                elif ft == 16:
                    transit_time = 60* (60 * length / us1 + 60 * length / 180)
                elif ft == 21:
                    transit_time = timau * 1.05
                elif ft == 22:
                    transit_time = timau * 1.03
        else:
            transit_time = 1

        return transit_time

    def runtime(period):
        tpitems = Visum.Net.TimeProfileItems.GetMultipleAttributes(["LINEROUTEITEM\\EMME_TTFINDEX", "SUM:USEDLINEROUTEITEMS\\OUTLINK\\"+period+"_TTC","SUM:USEDLINEROUTEITEMS\\POSTLENGTH", 
                                                                    "LINEROUTEITEM\\EMME_DATA1"])
        
        #else: 
        #    tpitems = Visum.Net.TimeProfileItems.GetMultipleAttributes(["LINEROUTEITEM\\EMME_TTFINDEX", "SUM:USEDLINEROUTEITEMS\\OUTLINK\\AddVal3","SUM:USEDLINEROUTEITEMS\\POSTLENGTH", 
        #                                                            "LINEROUTEITEM\\EMME_DATA1"])
        result  = []

        default_speed = 30
        for ft, timau, length, us1 in tpitems:
            haul_time = calc_ttf(ft, timau, length, us1, default_speed)
            result.append([haul_time, ])

        Visum.Net.TimeProfileItems.SetMultipleAttributes(["AddVal"], result)

    def combinerundwelltimes():
        
        # Pull attributes
        tpi_addval    = h.GetMulti(Visum.Net.TimeProfileItems,r"ADDVAL"     , activeOnly = True)
        tpi_dwelltime = h.GetMulti(Visum.Net.TimeProfileItems,r"DWELL_TIME" , activeOnly = True)

        # Make Visum list with link data
        att_list = [tpi_addval,tpi_dwelltime]
    
	    # Put Visum link list into dataframe
        df = pd.DataFrame(np.column_stack(att_list), columns = ['tpi_addval','tpi_dwelltime'])

        # Convert fields to float
        df[['tpi_addval','tpi_dwelltime']] = df[['tpi_addval','tpi_dwelltime']].astype(float)

        # Calculate field
        df['tpi_addval'] = df['tpi_addval'] +  df['tpi_dwelltime']

        # Set fields back in Visum
        h.SetMulti(Visum.Net.TimeProfileItems ,r"ADDVAL", df['tpi_addval'])



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
    combinerundwelltimes()


per = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like 'AM' from AM in the code box
skim_setup(per)

