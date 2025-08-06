# LCOG: Pull PrT Assignment Quality Report from Visum and save as csv file

"""
created 5/21/2025

@author: edna.aguilar

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
list = Visum.Workbench.Lists.CreatePuTStatList

list.AddKeyColumns()

attributes = [
    "MeanJourneyTimePut", "MeanRideTimePuT", "MeanInVehTimePuT",
    "MeanTransferWaitTimePut", "MeanOriginWaitTimePuT", "MeanWalkTimePuT",
    "MeanPuTAuxTimePuT", "MeanSharingTravelTimePuT", "MeanAccessTimePuT", 
    "MeanEgressTimePuT", "MeanJourneyDistPuT", "MeanRideDistPuT", 
    "MeanNumTransfersPuT",
    "TotalJourneyTimePuT", "TotalRideTimePuT", "TotalInVehTimePuT",
    "TotalTransferWaitTimePuT", "TotalOriginWaitTimePuT", "TotalWalkTimePuT",
    "TotalPuTAuxTimePut", "TotalSharingTravelTimePuT", "TotalAccessTimePuT",
    "TotalEgressTimePuT", "TotalJourneyDistPuT", "TotalRideDistPuT",
    "TotalNumTransfersPuT",
    "PTripsUnlinkedPuT", "PTripsLinkedTot", "PTripsLinked0", "PTripsLinked1",
    "PTripsLinked2", "PTripsLinkedGt2", "PTripsLinkedWRide",
    "PTripsLinkedWoRide", "PTripsLinkedWoCon"
]

for attr in attributes:
    list.AddColumn(Attribut=attr)

df = pd.DataFrame(list.SaveToArray())

# Convert to long format
data_only = df.iloc[0]
data_only.index = attributes
df_long = data_only.reset_index()
df_long.columns = ['Attribute', 'Value']

# Save
df_long.to_csv(proj_dir + "outputs/reports/ModelRun_" + date + "/PuT Assignment Stats/PuTAssignment_" + code + "_Iter" + iter + ".csv")

