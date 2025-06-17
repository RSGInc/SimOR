# Post-processing PrT skims from Visum based on "Code" field in Procedure Sequence
# 6/17/2025 - Luke Gordon (RSG)
# Adapted from code from Chetan Joshi (PTV)

import tables
import numpy as np
import pandas as pd
import os
import VisumPy.helpers as h
import openmatrix as omx


def prtskim_postprocessing(mtx_dseg):
    
    # Pull Intrazonal attributes out to set to diagonals
    intrtime     = np.array(h.GetMulti(Visum.Net.Zones,r"intrtime"    , activeOnly = True))
    intrdist     = np.array(h.GetMulti(Visum.Net.Zones,r"intrdist"    , activeOnly = True))
    intrdist_wlk = np.array(h.GetMulti(Visum.Net.Zones,r"intrdist_wlk", activeOnly = True))
    
    # Pull, Process, and Set matrices as needed by DSegCode
    if mtx_dseg == 'wlk':                                                           # Run Walk distance processing
        # Pull
        dis_wlk  = h.GetMatrixRaw(Visum, {"CODE": "DIS" , "DSegCode": mtx_dseg})           # Walk Distance
        # Process
        np.fill_diagonal(dis_wlk, intrdist_wlk)                                     
        # Set
        h.SetMatrixRaw(Visum, {"CODE": "DIS"     , "DSegCode": mtx_dseg}, dis_wlk)

    elif mtx_dseg == 'amsov':                                                       # Run Auto distance and time processing
        # Pull
        dis      = h.GetMatrixRaw(Visum, {"CODE": "DIS" , "DSegCode": mtx_dseg})        # Auto Distance
        # Process
        np.fill_diagonal(dis, intrdist)                                             
        # Set
        h.SetMatrixRaw(Visum, {"CODE": "DIS"     , "DSegCode": mtx_dseg}, dis)

        # Pull
        ad1      = h.GetMatrixRaw(Visum, {"CODE": "AD1" , "DSegCode": mtx_dseg})        # Auto Congested Travel Time
        # Process
        ad1 = np.where(ad1 == 9999.00, 9999.00, ad1 / 60)                         
        np.fill_diagonal(ad1, intrtime)                                           
        # Set
        h.SetMatrixRaw(Visum, {"CODE": "AD1"     , "DSegCode": mtx_dseg}, ad1)

    else:                                                                           # Run Auto time processing only
        # Pull
        ad1      = h.GetMatrixRaw(Visum, {"CODE": "AD1" , "DSegCode": mtx_dseg})        # Auto Congested Travel Time
        # Process
        ad1 = np.where(ad1 == 9999.00, 9999.00, ad1 / 60)                           
        np.fill_diagonal(ad1, intrtime)                                             
        # Set
        h.SetMatrixRaw(Visum, {"CODE": "AD1"     , "DSegCode": mtx_dseg}, ad1)

# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

# Pull "Code" field from procedure sequence containing Code, DSegCode, and filename
procedure_code = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like -> '[["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]'
procedure_codes = eval(procedure_code)   # Example: outputs a list of lists like -> [["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]

# Loop thru each matrix set in the "Code" field and export
for x in range(len(procedure_codes)):
    #code     = procedure_codes[x][0]
    dsegcode = procedure_codes[x][0]

    prtskim_postprocessing(dsegcode)

