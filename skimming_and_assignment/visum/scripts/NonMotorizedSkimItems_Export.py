# Exports shapefile of model network (links, nodes, connectors) and csv files of stops and line routes

"""
created 1/12/2026

@author: luke.gordon

"""

# Libraries
import VisumPy.helpers as h
import VisumPy.excel
import pandas as pd
import numpy as np
import csv
from datetime import datetime
import math
import os.path
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



# Get file path for exports
# Read the path from the pointer file
with open(os.path.join(folder_a, 'path_nonmotorizedinputs.txt'), 'r') as n:
    nonmotorizedinputs_relative_path = n.read().strip()

# Build the absolute path to the YAML file
nonmotorizedinputs_path = os.path.join(folder_a, nonmotorizedinputs_relative_path)



# Export Shapefiles of network Links, Nodes, and Connectors
def network_shp_export():

    # Links
	# Create export shapefile parameters object
	link_shp_export_params = Visum.IO.CreateExportShapeFilePara()
	
	# Set options for export in parameters object
	link_shp_export_params.SetAttValue("OBJECTTYPE", 0) # Links
	link_shp_export_params.SetAttValue("DIRECTED", 1)
	link_shp_export_params.SetAttValue("ONLYACTIVE", 1)
	
	# Set columns for export in parameters object
	link_shp_export_params.ClearLayout()
	link_shp_export_params.AddColumn("NO")
	link_shp_export_params.AddColumn("FROMNODENO")
	link_shp_export_params.AddColumn("TONODENO")
	link_shp_export_params.AddColumn("LINKSERIAL")
	link_shp_export_params.AddColumn("TYPENO")
	link_shp_export_params.AddColumn("TSYSSET")
	link_shp_export_params.AddColumn("Length")
	
	Visum.IO.ExportShapefile(nonmotorizedinputs_path + "/Network.shp", link_shp_export_params)
     


    # Nodes
	# Create export shapefile parameters object
	node_shp_export_params = Visum.IO.CreateExportShapeFilePara()
	
	# Set options for export in parameters object
	node_shp_export_params.SetAttValue("OBJECTTYPE", 1) # Nodes
	node_shp_export_params.SetAttValue("ONLYACTIVE", 1)
	
	# Set columns for export in parameters object
	node_shp_export_params.ClearLayout()
	node_shp_export_params.AddColumn("NO")
	
	Visum.IO.ExportShapefile(nonmotorizedinputs_path + "/Network.shp", node_shp_export_params)
     


    # Connectors (CC)
	# Create export shapefile parameters object
	cc_shp_export_params = Visum.IO.CreateExportShapeFilePara()
	
	# Set options for export in parameters object
	cc_shp_export_params.SetAttValue("OBJECTTYPE", 4) # Connectors
	cc_shp_export_params.SetAttValue("ONLYACTIVE", 1)
	
	# Set columns for export in parameters object
	cc_shp_export_params.ClearLayout()
	cc_shp_export_params.AddColumn("ZONENO")
	cc_shp_export_params.AddColumn("NODENO")
	cc_shp_export_params.AddColumn("DIRECTION")
	cc_shp_export_params.AddColumn("Length")
	
	Visum.IO.ExportShapefile(nonmotorizedinputs_path + "/Network.shp", cc_shp_export_params)
     


	# MAZs
	# Create export shapefile parameters object
	maz_shp_export_params = Visum.IO.CreateExportShapeFilePara()
	
	# Set options for export in parameters object
	maz_shp_export_params.SetAttValue("OBJECTTYPE", 9) # POIs
	maz_shp_export_params.SetAttValue("ONLYACTIVE", 1)
	
	# Set columns for export in parameters object
	maz_shp_export_params.ClearLayout()
	maz_shp_export_params.AddColumn("XCOORD")
	maz_shp_export_params.AddColumn("YCOORD")
	maz_shp_export_params.AddColumn("MAZ_NO")
	
	Visum.IO.ExportShapefile(nonmotorizedinputs_path + "/MAZs.shp", maz_shp_export_params)




# Export Transit Tables to csv's (Stop Points and Line Routes)
def transittbls_export():
	
	# EXPORT TRANSIT TABLES TO CSV FILES
	# Import Stop Points fields
	NO          = h.GetMulti(Visum.Net.StopPoints,r"NO", activeOnly = True)
	XCOORD      = h.GetMulti(Visum.Net.StopPoints,r"XCOORD", activeOnly = True)
	YCOORD      = h.GetMulti(Visum.Net.StopPoints,r"YCOORD", activeOnly = True)
	LINES       = h.GetMulti(Visum.Net.StopPoints,r"CONCATENATE:LINEROUTES\LINENAME", activeOnly = True)
    
	# Make Visum list with link data
	stoppoints_list = [NO, XCOORD, YCOORD, LINES]
			
	# Put Visum link list into dataframe  
	stoppoints_df = pd.DataFrame(np.column_stack(stoppoints_list), columns = ['NO', 'XCOORD', 'YCOORD', 'LINES'])

	# Export link table as csv
	stoppoints_df.to_csv(nonmotorizedinputs_path + "/StopPointsTbl.csv")
     
	

	# Import Line Routes fields
	LINE          = h.GetMulti(Visum.Net.LineRoutes,r"LINENAME", activeOnly = True)
	TSYSCODE      = h.GetMulti(Visum.Net.LineRoutes,r"TSYSCODE", activeOnly = True)

	# Make Visum list with link data
	lineroutes_list = [LINE, TSYSCODE]
			
	# Put Visum link list into dataframe  
	lineroutes_df = pd.DataFrame(np.column_stack(lineroutes_list), columns = ['LINE', 'TSYSCODE'])

	# Export link table as csv
	lineroutes_df.to_csv(nonmotorizedinputs_path + "/LineRoutesTbl.csv")
	


# Export network shapefile
network_shp_export()

# Export Transit csv's
transittbls_export()







