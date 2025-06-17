# Post-processing PuT skims from Visum based on "Code" field in Procedure Sequence
# 6/16/2025 - Luke Gordon (RSG)
# Adapted from code from Chetan Joshi (PTV)

import tables
import numpy as np
import pandas as pd
import os
import VisumPy.helpers as h
import openmatrix as omx


# Create function to build skim matrices that weren't built during the skimming procedure itself if they don't yet exist
def creatematrices(code,mtx_dseg):
    try:
        mx = h.GetMatrixRaw(Visum, {"CODE": code , "DSegCode": mtx_dseg})
    except Exception as e:
        mx = Visum.Net.AddMatrix(No=-1,ObjectTypeRef=2,MatrixType=4)
        mx.SetAttValue("CODE",code)
        mx.SetAttValue("DSegCode",mtx_dseg)


def putskim_postprocessing(mtx_dseg):
    
    # Build matrices if they don't yet exist
    creatematrices("NBR"  ,mtx_dseg)
    creatematrices("IVTT" ,mtx_dseg)
    creatematrices("STC"  ,mtx_dseg)
    creatematrices("OVT"  ,mtx_dseg)
    creatematrices("VTC_a",mtx_dseg)
    creatematrices("VTC_e",mtx_dseg)
    creatematrices("VTC_l",mtx_dseg)
    creatematrices("VTC_r",mtx_dseg)

    # Pull matrices out of Visum as numpy arrays
    wkt    = h.GetMatrixRaw(Visum, {"CODE": "WKT"     , "DSegCode": mtx_dseg})  # Walk time
    act    = h.GetMatrixRaw(Visum, {"CODE": "ACT"     , "DSegCode": mtx_dseg})  # Access time
    egt    = h.GetMatrixRaw(Visum, {"CODE": "EGT"     , "DSegCode": mtx_dseg})  # Egress time
    ntr    = h.GetMatrixRaw(Visum, {"CODE": "NTR"     , "DSegCode": mtx_dseg})  # Number of transfers
    nbr    = h.GetMatrixRaw(Visum, {"CODE": "NBR"     , "DSegCode": mtx_dseg})  # Number of boardings
    wowt   = h.GetMatrixRaw(Visum, {"CODE": "WOWT"    , "DSegCode": mtx_dseg})  # Weighted origin wait time
    wtwt   = h.GetMatrixRaw(Visum, {"CODE": "WTWT"    , "DSegCode": mtx_dseg})  # Weighted transfer wait time
    ivtt   = h.GetMatrixRaw(Visum, {"CODE": "IVTT"    , "DSegCode": mtx_dseg})  # In-vehicle travel time
    ivtt_a = h.GetMatrixRaw(Visum, {"CODE": "IVTT(a)" , "DSegCode": mtx_dseg})  # In-vehicle travel time (BRT)
    ivtt_b = h.GetMatrixRaw(Visum, {"CODE": "IVTT(b)" , "DSegCode": mtx_dseg})  # In-vehicle travel time (Bus)
    ivtt_e = h.GetMatrixRaw(Visum, {"CODE": "IVTT(e)" , "DSegCode": mtx_dseg})  # In-vehicle travel time (Streetcar)
    ivtt_l = h.GetMatrixRaw(Visum, {"CODE": "IVTT(l)" , "DSegCode": mtx_dseg})  # In-vehicle travel time (LRT)
    ivtt_r = h.GetMatrixRaw(Visum, {"CODE": "IVTT(r)" , "DSegCode": mtx_dseg})  # In-vehicle travel time (WES)
    pla    = h.GetMatrixRaw(Visum, {"CODE": "PLA"     , "DSegCode": mtx_dseg})  # Stop type constant (raw sum)
    stc    = h.GetMatrixRaw(Visum, {"CODE": "STC"     , "DSegCode": mtx_dseg})  # Stop type constant (final average)
    ovt    = h.GetMatrixRaw(Visum, {"CODE": "OVT"     , "DSegCode": mtx_dseg})  # Out of vehicle time
    vtc_a  = h.GetMatrixRaw(Visum, {"CODE": "VTC_a"   , "DSegCode": mtx_dseg})  # Vehicle type constant (BRT)
    vtc_e  = h.GetMatrixRaw(Visum, {"CODE": "VTC_e"   , "DSegCode": mtx_dseg})  # Vehicle type constant (Streetcar)
    vtc_l  = h.GetMatrixRaw(Visum, {"CODE": "VTC_l"   , "DSegCode": mtx_dseg})  # Vehicle type constant (LRT)
    vtc_r  = h.GetMatrixRaw(Visum, {"CODE": "VTC_r"   , "DSegCode": mtx_dseg})  # Vehicle type constant (WES)

    # Process matrices
    # Walk time
    wkt = np.minimum(wkt + act + egt , 9999.00)                     
    wkt = np.where((wkt < 0.01) | (wkt > 20.0) , 9999.00, wkt)
    np.fill_diagonal(wkt, 9999.00)
    # Weighted origin wait time
    wowt = np.where(wkt == 9999.00, 9999.00, wowt)
    # Perceived In-vehicle time by Mode
    if mtx_dseg == 'amPuT' or mtx_dseg == 'pmPuT':                      # Peak
        ivtt_a = np.where(ivtt_a == 9999.00, 9999.00, ivtt_a * 0.95)
        ivtt_l = np.where(ivtt_l == 9999.00, 9999.00, ivtt_l * 0.88)
        ivtt_r = np.where(ivtt_r == 9999.00, 9999.00, ivtt_r * 0.88)
    else:                                                               # Off-Peak
        ivtt_a = np.where(ivtt_a == 9999.00, 9999.00, ivtt_a * 0.95)
        ivtt_l = np.where(ivtt_l == 9999.00, 9999.00, ivtt_l * 0.86)
        ivtt_r = np.where(ivtt_r == 9999.00, 9999.00, ivtt_r * 0.86)
    # Number of boardings
    nbr = np.where(ntr == 9999.00, 9999.00, ntr + 1)
    # Stop type constant
    stc = np.where((pla == 9999.00) | (nbr == 9999.00) , 9999.00, pla / nbr)
    stc = np.where(stc == 9999.00, 0.00, stc)
    # In-Vehicle time
    ivtt = np.minimum(ivtt_a + ivtt_b + ivtt_e + ivtt_l + ivtt_r, 9999.00)
    np.fill_diagonal(ivtt, 9999.00)
    # Out of vehicle time
    ovt = np.minimum(wowt + wtwt + wkt, 9999.00)
    # Vehicle type constant by Mode
    if mtx_dseg == 'amPuT' or mtx_dseg == 'pmPuT':                                                                      # Peak
        vtc_a = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.0557 * ivtt_a) / ivtt)
        vtc_e = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.0000 * ivtt_e) / ivtt)
        vtc_l = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.1858 * ivtt_l) / ivtt)
        vtc_r = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.1858 * ivtt_r) / ivtt)
    else:                                                                                                               # Off-Peak
        vtc_a = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.0432 * ivtt_a) / ivtt)
        vtc_e = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.0984 * ivtt_e) / ivtt)
        vtc_l = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.1442 * ivtt_l) / ivtt)
        vtc_r = np.where((ivtt == 9999.00) | (ivtt == 9999.00) | (ivtt == 0.00), 9999.00, (0.1442 * ivtt_r) / ivtt)

    # Set matrices in Visum
    h.SetMatrixRaw(Visum, {"CODE": "WKT"     , "DSegCode": mtx_dseg}, wkt   )  # Walk time
    h.SetMatrixRaw(Visum, {"CODE": "ACT"     , "DSegCode": mtx_dseg}, act   )  # Access time
    h.SetMatrixRaw(Visum, {"CODE": "EGT"     , "DSegCode": mtx_dseg}, egt   )  # Egress time
    h.SetMatrixRaw(Visum, {"CODE": "NTR"     , "DSegCode": mtx_dseg}, ntr   )  # Number of transfers
    h.SetMatrixRaw(Visum, {"CODE": "NBR"     , "DSegCode": mtx_dseg}, nbr   )  # Number of boardings
    h.SetMatrixRaw(Visum, {"CODE": "WOWT"    , "DSegCode": mtx_dseg}, wowt  )  # Weighted origin wait time
    h.SetMatrixRaw(Visum, {"CODE": "WTWT"    , "DSegCode": mtx_dseg}, wtwt  )  # Weighted transfer wait time
    h.SetMatrixRaw(Visum, {"CODE": "IVTT"    , "DSegCode": mtx_dseg}, ivtt  )  # In-vehicle travel time
    h.SetMatrixRaw(Visum, {"CODE": "IVTT(a)" , "DSegCode": mtx_dseg}, ivtt_a)  # In-vehicle travel time (BRT)
    h.SetMatrixRaw(Visum, {"CODE": "IVTT(b)" , "DSegCode": mtx_dseg}, ivtt_b)  # In-vehicle travel time (Bus)
    h.SetMatrixRaw(Visum, {"CODE": "IVTT(e)" , "DSegCode": mtx_dseg}, ivtt_e)  # In-vehicle travel time (Streetcar)
    h.SetMatrixRaw(Visum, {"CODE": "IVTT(l)" , "DSegCode": mtx_dseg}, ivtt_l)  # In-vehicle travel time (LRT)
    h.SetMatrixRaw(Visum, {"CODE": "IVTT(r)" , "DSegCode": mtx_dseg}, ivtt_r)  # In-vehicle travel time (WES)
    h.SetMatrixRaw(Visum, {"CODE": "PLA"     , "DSegCode": mtx_dseg}, pla   )  # Stop type constant (raw sum)
    h.SetMatrixRaw(Visum, {"CODE": "STC"     , "DSegCode": mtx_dseg}, stc   )  # Stop type constant (final average)
    h.SetMatrixRaw(Visum, {"CODE": "OVT"     , "DSegCode": mtx_dseg}, ovt   )  # Out of vehicle time
    h.SetMatrixRaw(Visum, {"CODE": "VTC_a"   , "DSegCode": mtx_dseg}, vtc_a )  # Vehicle type constant (BRT)
    h.SetMatrixRaw(Visum, {"CODE": "VTC_e"   , "DSegCode": mtx_dseg}, vtc_e )  # Vehicle type constant (Streetcar)
    h.SetMatrixRaw(Visum, {"CODE": "VTC_l"   , "DSegCode": mtx_dseg}, vtc_l )  # Vehicle type constant (LRT)
    h.SetMatrixRaw(Visum, {"CODE": "VTC_r"   , "DSegCode": mtx_dseg}, vtc_r )  # Vehicle type constant (WES)



# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

# Pull "Code" field from procedure sequence containing Code, DSegCode, and filename
dsegcode = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like -> '[["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]'
#procedure_codes = eval(procedure_code)   # Example: outputs a list of lists like -> [["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]

# Loop thru each matrix set in the "Code" field and export
#for x in range(len(procedure_codes)):
#    #code     = procedure_codes[x][0]
#    dsegcode = procedure_codes[x][1]


putskim_postprocessing(dsegcode)

