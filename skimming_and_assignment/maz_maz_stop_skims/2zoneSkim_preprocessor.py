# This script prepares inputs for 2zoneSkim.py using Visum outputs:
# - Links: [TSYSSET, TYPNO]
# - Nodes: [NO]
# - MAZs: (provided separately)
# - Transit stops: transit stops with list of routes; [STOP_ID, Lines, X-Coordinate, Y-Coordinate]
# - Routes/Lines: [LineName, TSysCode]

# And generates the following outputs:
# - MAZ centroids
# - Connectors: from MAZ centorid to nearest node on walk network
# - Nodes: network nodes + MAZ centroids (consistent node numbering); [MAZ, NO]
# - Links: links + connectors (consistent node numbering; [FROMNODENO, TONODENO]
# - Routes: one route per row; [Route_ID, Mode]
# - Stops: one stop per row; [NO, Latitute, Longitute, Route_ID]

import yaml
import os
import sys
import geopandas as gpd
import numpy as np
import pandas as pd
from datetime import datetime
from shapely.geometry import LineString

class ConfigLoader():
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        os.chdir(os.path.dirname(__file__))
        with open(self.config_file, "r") as file:
            return yaml.load(file, Loader = yaml.FullLoader)

class DataLoader():
    def __init__(self, config):
        self.config = config.config
        self.links = None
        self.mazs = None
        self.nodes = None
        self.epsg = None
        self.routes = None
        self.stops = None
        self.walk_modes = None
        self.maz_centroids = None
        self.load_data()
        
    def load_data(self):
        input_dir = self.config["preprocessing"]["input_dir"]
        self.links = gpd.read_file(os.path.join(input_dir, self.config["preprocessing"]["links_file"]))
        self.nodes = gpd.read_file(os.path.join(input_dir, self.config["preprocessing"]["nodes_file"])).rename(columns = {"NO":"NODE_NO"})
        self.mazs = gpd.read_file(os.path.join(input_dir, self.config["preprocessing"]["maz_file"])).rename(columns = {"MAZ_NO":"MAZ"})
        self.epsg = self.config["preprocessing"]["network_epsg"]
        self.routes = pd.read_csv(os.path.join(input_dir, self.config["preprocessing"]["routes"]))
        self.stops = pd.read_csv(os.path.join(input_dir, self.config["preprocessing"]["stops"]))
        self.walk_modes = self.config["preprocessing"]["walk_modes"]
        self.maz_centroids = self._get_maz_centroids()
        
    def _get_maz_centroids(self):
        """
        Find centroids of MAZ polygons
        """
        centroids = self.mazs[["MAZ", "geometry"]].copy()
        centroids["centroid_geom"] = centroids["geometry"].centroid
        centroids = centroids[["MAZ", "centroid_geom"]].rename(columns={"centroid_geom":"geometry"}) 
        return centroids

def create_centroid_connectors(inputs):
    """ 
    Create connector links that go from the MAZ centroid to the nearest node on the walk network
    """
    # Load data
    links = inputs.links[["NO", "FROMNODENO", "TONODENO", "TYPENO", "TSYSSET", "geometry"]]
    maz_centroids = inputs.maz_centroids
    nodes = inputs.nodes[["geometry", "NODE_NO"]]    
    
    # Clean ODOT network
    # FIXME: move somewhere more visible like config yaml
    links["TSYSSET"] = np.where(
        (links["TYPENO"] == 0) & (links["TSYSSET"].isna()),
        "wlk",
        links["TSYSSET"]
    )
    
    walk_modes = "|".join(inputs.walk_modes)
    walk_network_links = links[links["TSYSSET"].str.contains(walk_modes, na=False)] 

    # Remove nodes that are not in the walk network
    walk_network_nodes = nodes[nodes["NODE_NO"].isin(walk_network_links["FROMNODENO"]) | nodes["NODE_NO"].isin(walk_network_links["TONODENO"])]

    # Check if centroids and nodes have the same CRS
    if maz_centroids.crs != walk_network_nodes.crs:
        maz_centroids = maz_centroids.to_crs(walk_network_nodes.crs)

    # Find nearest walk node for each centroid
    centroids_to_nearest_node = gpd.sjoin_nearest(
        maz_centroids, walk_network_nodes, how="left", distance_col="distance"
    )

    # Create connector polyline from centroid to nearest node
    centroids_to_nearest_node = centroids_to_nearest_node.merge(
        nodes[["NODE_NO", "geometry"]],
        on="NODE_NO",
        how="left",
        suffixes=("_left", "_right")
    )

    centroids_to_nearest_node["connector"] = centroids_to_nearest_node.apply(
        lambda row: LineString([row["geometry_right"], row["geometry_left"]]), axis=1
    )

    # Rename columns
    connectors = centroids_to_nearest_node[["MAZ", "NODE_NO", "connector"]].rename(
        columns={"connector": "geometry"}
    )
    connectors = gpd.GeoDataFrame(connectors, geometry="geometry", crs=walk_network_nodes.crs)

    # Create new node id"s for MAZ centroids
    no_range = np.arange(nodes["NODE_NO"].max() + 1, nodes["NODE_NO"].max() + 1 + len(maz_centroids))
    connectors = connectors.sort_values(by = "MAZ")
    connectors["MAZ_NO"] = no_range
    
    return connectors, walk_network_nodes, walk_network_links

def prepare_nodes(inputs, walk_network_nodes):
    """
    Prepare nodes file by adding MAZ centroids as nodes and adjusting numbering
    """
    # Load data
    maz_centroids = inputs.maz_centroids
    walk_network_nodes = walk_network_nodes.rename(columns = {"NODE_NO": "NO"})
    
    # Make sure both are the same CRS
    if maz_centroids.crs != walk_network_nodes.crs:
        maz_centroids = maz_centroids.to_crs(walk_network_nodes.crs)

    # Add MAZ column
    walk_network_nodes["MAZ"] = 0
    
    # Add node numbering consistent with links/connectors
    no_range = np.arange(walk_network_nodes["NO"].max() + 1, walk_network_nodes["NO"].max() + 1 + len(maz_centroids))
    maz_centroids = maz_centroids.sort_values(by = "MAZ")
    maz_centroids["NO"] = no_range

    # Join walk nodes with MAZ centroids
    nodes_merged = pd.concat([walk_network_nodes[[ "geometry", "NO", "MAZ"]], maz_centroids[["geometry", "NO", "MAZ"]]], ignore_index=True)
        
    return nodes_merged

def prepare_links(connectors, walk_network_links, walk_network_nodes):
    """ 
    Add connector links to network links 
    """
    # Network is bi-directionaly (one link per direction)
    # Add FROMNODENO and TONODENO to connectors
    connectors["FROMNODENO"] = connectors["MAZ_NO"]
    connectors["TONODENO"] = connectors["NODE_NO"]

    # Duplicate connectors to create other direction link
    connectors_2 = connectors.copy()
    connectors_2["FROMNODENO"] = connectors_2["NODE_NO"]
    connectors_2["TONODENO"] = connectors_2["MAZ_NO"]
    
    # Make sure they are the same crs
    if connectors.crs != walk_network_links.crs:
        connectors = connectors.to_crs(walk_network_links.crs)

    # Merge connectors with links
    keep_cols = ["FROMNODENO", "TONODENO", "geometry"]
    links_merged = pd.concat([
        walk_network_links[keep_cols],
        connectors[keep_cols],
        connectors_2[keep_cols]], 
        ignore_index = True,
    )
    
    assert  (links_merged["FROMNODENO"].isin(walk_network_nodes["NO"]).all()) and \
            (links_merged["TONODENO"].isin(walk_network_nodes["NO"]).all()), "not all nodes in links are in nodes list"
        
    # Add length
    links_merged["length"] = links_merged["geometry"].length
        
    return links_merged

def prepare_transit_routes_and_stops(inputs):
    """ 
    Rename Routes cols and 
    """
    routes = inputs.routes
    stops = inputs.stops
    
    # Prepare routes
    routes.rename(columns={"TSYSCODE":"Mode",
                           "LINE":"Route_ID"}, inplace=True)

    # Create dictionary for mapping
    routes_mode_dict = dict(zip(routes["Route_ID"], routes["Mode"]))
    
    # Prepare stops
    # Convert coordinates to epsg 4326
    stops_gdf = gpd.GeoDataFrame(
        stops,
        geometry = gpd.points_from_xy(stops["XCOORD"], stops["YCOORD"]),
        crs = inputs.epsg
    )
    stops_gdf = stops_gdf.to_crs(epsg=4326)
    stops_gdf["Latitude"] = stops_gdf.geometry.y
    stops_gdf["Longitude"] = stops_gdf.geometry.x

    stops_gdf.rename(columns = {
        "StopID":"NO"}, inplace=True)

    # Explode mode - need route per row
    stops_gdf["Route_ID"] = stops["LINES"].apply(lambda x: [i for i in x.split(",")])
    stops_gdf = stops_gdf.explode("Route_ID")

    # Format
    keep_cols = ["NO", "Route_ID","Latitude", "Longitude"]
    
    return routes, stops_gdf[keep_cols]

def main(config_file):
    print("Starting non-motorized skim preprocessing....")
    start_time = datetime.now()
    
    config = ConfigLoader(config_file)
    inputs = DataLoader(config)
    
    # Process data
    connectors, walk_network_nodes, walk_network_links = create_centroid_connectors(inputs)
    nodes = prepare_nodes(inputs, walk_network_nodes)
    links = prepare_links(connectors, walk_network_links, nodes)
    routes, stops = prepare_transit_routes_and_stops(inputs)
    
    # Export
    output_dir = config.config["preprocessing"]["output_dir"]
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(output_dir, exist_ok=True)
    nodes.to_file(os.path.join(output_dir, "nodes.shp"))
    links.to_file(os.path.join(output_dir, "links.shp"))
    routes.to_csv(os.path.join(output_dir, "routes.csv"))
    stops.to_csv(os.path.join(output_dir, "stops.csv"))
    
    elapsed = datetime.now() - start_time
    print(f"Non-motorized skim preprocessing complete! Total time: {elapsed}")

if __name__ == "__main__":
    main(sys.argv[1])