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

    else:                                                                           # Run Auto distance, time, and tolls processing
        # Pull
        dis      = h.GetMatrixRaw(Visum, {"CODE": "DIS" , "DSegCode": mtx_dseg})                # Distance
        time     = h.GetMatrixRaw(Visum, {"CODE": "AD1" , "DSegCode": mtx_dseg})                # Time
        toll     = h.GetMatrixRaw(Visum, {"CODE": "TOL" , "DSegCode": mtx_dseg})                # Tolls
        # Process
        np.fill_diagonal(dis, intrdist)                                                         # Distance
        np.fill_diagonal(time, intrtime)                                                        # Time                                                 
        time = np.where(time == 9999.00, 9999.00, time / 60)        # Seconds to Minutes
        np.fill_diagonal(toll, 0)                                                               # Tolls
        # Set
        h.SetMatrixRaw(Visum, {"CODE": "DIS"     , "DSegCode": mtx_dseg}, dis)
        h.SetMatrixRaw(Visum, {"CODE": "AD1"     , "DSegCode": mtx_dseg}, time)
        h.SetMatrixRaw(Visum, {"CODE": "TOL"     , "DSegCode": mtx_dseg}, toll)





# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

dseg = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like 'AM' from AM in the code box
prtskim_postprocessing(dseg)


## Pull "Code" field from procedure sequence containing Code, DSegCode, and filename
#procedure_code = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like -> '[["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]'
#procedure_codes = eval(procedure_code)   # Example: outputs a list of lists like -> [["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]
#
## Loop thru each matrix set in the "Code" field and export
#for x in range(len(procedure_codes)):
#    dsegcode = procedure_codes[x][0]
#
#    prtskim_postprocessing(dsegcode)

