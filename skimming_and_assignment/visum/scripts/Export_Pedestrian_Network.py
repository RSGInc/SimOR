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
    link_shp_export_params.AddColumn("TYPENO")
    link_shp_export_params.AddColumn("TSYSSET")
    
    Visum.IO.ExportShapefile(nonmotorizedinputs_path + "/AllStreets_Network.shp", link_shp_export_params)
     
    # Nodes
    # Create export shapefile parameters object
    node_shp_export_params = Visum.IO.CreateExportShapeFilePara()
    
    # Set options for export in parameters object
    node_shp_export_params.SetAttValue("OBJECTTYPE", 1) # Nodes
    node_shp_export_params.SetAttValue("ONLYACTIVE", 1)
    
    # Set columns for export in parameters object
    node_shp_export_params.ClearLayout()
    node_shp_export_params.AddColumn("NO")
    node_shp_export_params.AddColumn("XCOORD")
    node_shp_export_params.AddColumn("YCOORD")
    
    Visum.IO.ExportShapefile(nonmotorizedinputs_path + "/AllStreets_Network.shp", node_shp_export_params)

# Export network shapefile
network_shp_export()







