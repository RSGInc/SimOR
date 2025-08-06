# LCOG: Pull PrT Assignment Quality Report from Visum and save as csv file

"""
created 5/14/2025

@author: luke.gordon

"""

# Libraries
import VisumPy.helpers
import VisumPy.excel
import pandas as pd
import numpy as np
import csv
#from datetime import datetime
import math
import os.path


# Pull timestamp for folder name and iteration number from Visum network attribute
date = Visum.Net.AttValue("output_date")
iter = Visum.Net.AttValue("iter")
iter = str(int(iter))

# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

# Pull "Code" field from procedure sequence to name files
code = Visum.Procedures.OperationExecutor.GetCurrentOperation().AttValue("CODE")

# Pull PrT assignment quality report and format into a table for export
list = Visum.Workbench.Lists.CreatePrTAssQualityList

list.AddKeyColumns()

list.AddColumn(Attribut="MEANABSVOLDIFFTOTAL")
list.AddColumn(Attribut="MEANRELVOLDIFFTOTAL")
list.AddColumn(Attribut="ASSIGNEDDEMAND")
list.AddColumn(Attribut="VEHMITRAVPRT")
list.AddColumn(Attribut="VEHHOURTRAVT0")
list.AddColumn(Attribut="VEHHOURTRAVTCUR")
list.AddColumn(Attribut="VEHHOURIMP")
list.AddColumn(Attribut="TOTALEXCESSCOST")
list.AddColumn(Attribut="AVGEXCESSCOST")
list.AddColumn(Attribut="GAP")

df = list.SaveToArray()


df = pd.DataFrame(df)


df = df.rename(columns={0 : 'Demand segment set code' , 1 : 'Iteration' , 2 : 'Mean absolute volume difference total' , 3 : 'Mean relative volume difference total' , 
                        4 : 'Assigned demand' , 5 : 'Vehicle miles traveled PrT' , 6 : 'Vehicle hours traveled t0' , 7 : 'Vehicle hours traveled tCur' , 
                    	8 : 'Vehicle hour impedance' , 9 : 'Total excess cost' , 10: 'Mean excess cost', 11: 'Gap'})

df.to_csv(proj_dir+"outputs/reports/ModelRun_"+date+"/PrT Assignment Quality Reports/"+code+"_Iter"+iter+".csv")

