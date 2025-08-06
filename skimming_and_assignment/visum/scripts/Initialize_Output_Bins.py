# Set output_date field in Visum network attributes and create folders for reports

"""
created 5/14/2025

@author: luke.gordon

"""

# Libraries
import VisumPy.helpers
import VisumPy.excel
import pandas as pd
import numpy as np
from datetime import datetime
import os.path



# Calculate timestamp for folder name and save in Network attribute in Visum
date = datetime.now().strftime("(%Y-%m-%d)-%H_%M_%S")
Visum.Net.SetAttValue("output_date", date)

# Read user inputs from Visum
proj_dir = Visum.GetPath(2)

# Create timestamped folder for all results
os.mkdir(proj_dir+"outputs/reports/ModelRun_"+date)

# Create folder for storing this runs assignment quality results
os.mkdir(proj_dir+"outputs/reports/ModelRun_"+date+"/PrT Assignment Quality Reports")

# Create folder for storing this runs assignment results (Pct. Error, RMSE, etc.)
os.mkdir(proj_dir+"outputs/reports/ModelRun_"+date+"/Assignment Results")

# Create folder for PuT assignment stats
os.mkdir(proj_dir+"outputs/reports/ModelRun_"+date+"/PuT Assignment Stats")