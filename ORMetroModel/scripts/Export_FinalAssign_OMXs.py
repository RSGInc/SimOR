# Export OMX files from LCOG model based on "Code" field in Procedure Sequence
# 4/29/2025 - Luke Gordon (RSG)
# Adapted from code from Chetan Joshi (PTV)

import tables
import numpy as np
import pandas as pd
import os
import VisumPy.helpers as h
import openmatrix as omx



def omx_export(mtx_code, mtx_dseg, omx_fn): #mtx_num, mtx_code):
    omx_file = omx.open_file(omx_fn, 'w')
    # Pull matrix out but close .omx file if there is an error
    try:
        mx = h.GetMatrixRaw(Visum, {"CODE": mtx_code , "DSegCode": mtx_dseg})
    except Exception as e:
        print(f"Error getting matrix for CODE={mtx_code}, DSegCode={mtx_dseg}: {e}")
        omx_file.close()
    core_name = mtx_code
    omx_file[core_name] = mx
    omx_file.close()


# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

# Pull "Code" field from procedure sequence containing Code, DSegCode, and filename
procedure_code = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")   # Example: outputs a string like -> '[["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]'
procedure_codes = eval(procedure_code)   # Example: outputs a list of lists like -> [["mfamsov","PuT","AM2_SOV.omx"],["mfmdMpe","PuT","MD1_MPE.omx"]]

# Loop thru each matrix set in the "Code" field and export
for x in range(len(procedure_codes)):
    code     = procedure_codes[x][0]
    dsegcode = procedure_codes[x][1]
    filename = procedure_codes[x][2]


    omx_export(code, dsegcode, proj_dir + "outputs\\assignment\\final_assign\\" + filename)

