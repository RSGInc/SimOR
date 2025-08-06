# Export OMX files from LCOG model based on "Code" field in Procedure Sequence
# 4/30/2025 - Luke Gordon (RSG)
# Adapted from code from Chetan Joshi (PTV)

import openmatrix as omx
import os
import shutil
import numpy as np
import pandas as pd
import VisumPy.matrices as vmx
import VisumPy.helpers as h


def omx_import(mtx_code, mtx_dseg, omx_fn): 
    omx_file = omx.open_file(omx_fn, 'r')
    mx_name  = omx_file.list_matrices()[0] # 1 matrix per .omx file
    mx_array = omx_file[mx_name][:]
    # Read matrix but close .omx file if there is an error
    try:
        h.SetMatrixRaw(Visum, {"CODE": mtx_code , "DSegCode": mtx_dseg}, mx_array)
    except Exception as e:
        print(f"Error getting matrix for CODE={mtx_code}, DSegCode={mtx_dseg}: {e}")
        omx_file.close()
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


    omx_import(code, dsegcode, proj_dir + "outputs\\assignment\\final_assign\\" + filename)
