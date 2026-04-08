# This script prepares inputs for 2zoneSkim.py using Visum outputs:
# - Links: [NO, FROMNODENO, TONODENO, TSYSSET, TYPENO]
# - Nodes: [NO, XCOORD, YCOORD]
# - MAZs: [MAZ, TAZ]
# - Transit stops: transit stops with list of routes: [NO, LINES, XCOORD, YCOORD]
# - Routes/Lines: [LINE, TSYSCODE]

# And generates the following outputs:
# - MAZ centroids
# - Connectors: from MAZ centorid to nearest node on walk network
# - Nodes: walk network nodes + MAZ centroids (consistent node numbering); [MAZ, NO]
# - Links: walk links + connectors (consistent node numbering; [FROMNODENO, TONODENO]
# - Routes: one route per row; [Route_ID, Mode]
# - Stops: one stop per row; [NO, Route_ID, Latitute, Longitute]

import yaml
import os
import sys
import geopandas as gpd
import numpy as np
import pandas as pd
from datetime import datetime
from pyproj import CRS
from shapely.geometry import LineString

class ConfigLoader():
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        with open(self.config_file, "r") as file:
            return yaml.load(file, Loader = yaml.FullLoader)

class DataLoader():
    def __init__(self, config):
        self.config = config.config
        self.links = None
        self.mazs = None
        self.nodes = None
        self.source_crs = None
        self.target_crs = None
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
        self.routes = pd.read_csv(os.path.join(input_dir, self.config["preprocessing"]["routes"]))
        self.stops = pd.read_csv(os.path.join(input_dir, self.config["preprocessing"]["stops"]))
        self.walk_modes = self.config["preprocessing"]["walk_modes"]
        self.source_crs = self._infer_source_crs()
        self.target_crs = self._infer_proj_crs()
        self.links = self._ensure_projected_feet(self.links, "Links")
        self.nodes = self._ensure_projected_feet(self.nodes, "Nodes")
        self.mazs = self._ensure_projected_feet(self.mazs, "MAZs")
        self.maz_centroids = self._get_maz_centroids()

    def _infer_source_crs(self):
        for layer, gdf in (("links", self.links), ("nodes", self.nodes), ("MAZs", self.mazs)):
            if gdf.crs is not None:
                print(f"Using {layer} CRS as source CRS reference: {gdf.crs}")
                return CRS.from_user_input(gdf.crs)

    def _infer_proj_crs(self):
        reference_layer = next(gdf for gdf in (self.mazs, self.links, self.nodes) if gdf.crs is not None)
        utm_crs_meters = reference_layer.estimate_utm_crs()

        if utm_crs_meters is None:
            raise ValueError("Unable to determine a UTM CRS from the input geometries.")

        utm_proj4 = utm_crs_meters.to_proj4()
        if "+units=m" in utm_proj4:
            utm_proj4 = utm_proj4.replace("+units=m", "+units=us-ft")
        elif "+to_meter=1" in utm_proj4:
            utm_proj4 = utm_proj4.replace("+to_meter=1", "+units=us-ft")
        else:
            utm_proj4 = f"{utm_proj4} +units=us-ft"

        target_crs = CRS.from_proj4(utm_proj4)
        print(f"Inferred projected CRS in feet: {target_crs}")
        return target_crs

    def _is_projected_in_feet(self, crs):
        if crs is None:
            return False

        crs = CRS.from_user_input(crs)
        if not crs.is_projected:
            return False

        foot_unit_names = {"foot", "feet", "us survey foot", "foot_us", "us foot"}
        for axis in crs.axis_info:
            if axis.unit_name and axis.unit_name.lower() in foot_unit_names:
                return True

        return False

    def _ensure_projected_feet(self, gdf, layer):
        source_crs = CRS.from_user_input(gdf.crs)
        if self._is_projected_in_feet(source_crs):
            print(f"{layer} are already projected coordinates in feet: {source_crs}")
            if source_crs != self.target_crs:
                print(f"{layer} use a different feet-based CRS. Converting to {self.target_crs}")
                return gdf.to_crs(self.target_crs)
            return gdf

        if source_crs.is_projected:
            print(f"{layer} are projected, but not in feet. Converting to {self.target_crs}")
        else:
            print(f"{layer} are not projected. Converting to {self.target_crs}")

        return gdf.to_crs(self.target_crs)
        
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
        crs = inputs.source_crs
    )
    stops_gdf = stops_gdf.to_crs(epsg=4326)
    stops_gdf["Latitude"] = stops_gdf.geometry.y
    stops_gdf["Longitude"] = stops_gdf.geometry.x

    stops_gdf.rename(columns = {
        "StopID":"NO"}, inplace=True)

    # Remove NaNs
    stops_gdf = stops_gdf[stops_gdf["LINES"].notna()]
    
    # Explode mode - need route per row
    stops_gdf["Route_ID"] = stops_gdf["LINES"].apply(lambda x: [i for i in x.split(",")])
    stops_gdf = stops_gdf.explode("Route_ID")

    # Format
    keep_cols = ["NO", "Route_ID","Latitude", "Longitude"]
    
    return routes, stops_gdf[keep_cols]

def write_outputs(nodes, links, routes, stops, output_dir):
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(output_dir, exist_ok=True)
    nodes.to_file(os.path.join(output_dir, "walk_nodes.shp"))
    links.to_file(os.path.join(output_dir, "walk_links.shp"))
    routes.to_csv(os.path.join(output_dir, "routes.csv"), index=False)
    stops.to_csv(os.path.join(output_dir, "stops.csv"), index=False)

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
    
    # Export outputs
    output_dir = config.config["preprocessing"]["output_dir"]
    write_outputs(nodes, links, routes, stops, output_dir)

    elapsed = datetime.now() - start_time
    print(f"Non-motorized skim preprocessing complete! Total time: {elapsed}")

if __name__ == "__main__":
    main(sys.argv[1])