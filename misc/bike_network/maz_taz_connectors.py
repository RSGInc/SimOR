# This script generates MAZ and TAZ connectors with two links per connector, one for each direction
import pandas as pd
import geopandas as gpd
import numpy as np
import os
from shapely import LineString

# Settings
root_dir ="../../skimming_and_assignment/maz_maz_stop_skims"
mpo = "SKATS" #LCOG, SKATS
maz_output_file = os.path.join(root_dir, f"Visum_Outputs_{mpo}", "bike_maz_connectors.shp")
taz_output_file = os.path.join(root_dir, f"Visum_Outputs_{mpo}", "bike_taz_connectors.shp")

# Load network
network_files = {
    "SKATS": ["Network_link.shp", "Network_node.shp"],
    "LCOG": ["AllStreets_Network_link.shp", "AllStreets_Network_node.shp"]
}

link_file = network_files[mpo][0]
node_file = network_files[mpo][1]

mazs = gpd.read_file(os.path.join(root_dir, f"Visum_Outputs_{mpo}", "MAZ_poi_surface.shp"))
network = gpd.read_file(os.path.join(root_dir, f"Visum_Outputs_{mpo}", link_file))
nodes = gpd.read_file(os.path.join(root_dir, f"Visum_Outputs_{mpo}", node_file))

# External stations
ext_stations = np.arange(1,31,1) if mpo == 'SKATS' else [None]

# Convert to same crs
assert (mazs.crs == nodes.crs == network.crs), "crs is not the equal for MAZs, nodes, and network"
assert (mazs.crs.is_projected), "MAZ crs is not projected"

# Filter bike links
bike_modes = "k"
bike_modes = "|".join(bike_modes)
bike_links = network[network['TSYSSET'].str.contains(bike_modes, na=False)]

# Extract bike nodes
bike_nodes = nodes[
    (nodes['NO'].isin(bike_links['FROMNODENO'])) |
    (nodes['NO'].isin(bike_links['TONODENO']))
]

# Check if for each link there is a duplicate in the opposite direction
pairs = bike_links[['FROMNODENO', 'TONODENO']].copy()
pairs['forward'] = list(zip(pairs['FROMNODENO'], pairs['TONODENO']))
pairs['reverse'] = list(zip(pairs['TONODENO'], pairs['FROMNODENO']))

# Check if the reverse direction exists in the set of all links
all_pairs = set(pairs['forward'])
pairs['has_reverse'] = pairs['reverse'].isin(all_pairs)

# Note links missing a reverse direction (for information only)
missing_reverse = pairs[~pairs['has_reverse']]
print(f"{len(missing_reverse)} links missing reverse direction")
print(missing_reverse[['FROMNODENO', 'TONODENO']]).head()

# Get TAZ centroids
tazs = mazs[['TAZ', 'geometry']].dissolve('TAZ', aggfunc='first').reset_index()
tazs = tazs[~tazs['TAZ'].isin(ext_stations)] # remove externals
taz_centroids = tazs.copy()
taz_centroids["centroid_geom"] = taz_centroids['geometry'].centroid
taz_centroids = taz_centroids[["TAZ", "centroid_geom"]].rename(columns={'centroid_geom':'geometry'})

# Get MAZ centroids
maz_centroids = mazs[['MAZ', "geometry"]].copy()
maz_centroids = maz_centroids[~maz_centroids['MAZ'].isin(ext_stations)]
maz_centroids['centroid_geom'] = maz_centroids['geometry'].centroid
maz_centroids = maz_centroids[["MAZ", "centroid_geom"]].rename(columns={"centroid_geom":"geometry"}) 

# ================
# Create connectors
def add_connectors(centroids, nodes, zone_id):
    centroids['ZONENO'] = centroids[zone_id]
    
    # Find nearest node from centroid
    centroids_to_nearest_node = gpd.sjoin_nearest(
        centroids, nodes[["NO", "geometry"]], how="left", distance_col="distance"
    )
    
    # Create connector polyline from centroid to nearest node
    centroids_to_nearest_node = centroids_to_nearest_node.merge(
            nodes[["NO", "geometry"]],
            on="NO",
            how="left",
            suffixes=("_left", "_right")
        )
    
    centroids_to_nearest_node["geometry"] = centroids_to_nearest_node.apply(
        lambda row: LineString([row["geometry_right"], row["geometry_left"]]), axis=1
    )
    
    # Call nearest node "TONODENO"
    maz_connectors = centroids_to_nearest_node.rename(columns = {'NO': 'NODENO'})
    
    # Convert to gdf
    maz_connectors =gpd.GeoDataFrame(
        maz_connectors[['ZONENO', 'NODENO', 'geometry']], 
        geometry="geometry", 
        crs=centroids.crs)
    
    # Duplicate connectors to create second direction
    maz_connectors['DIRECTION'] = 1
    maz_connectors2 = maz_connectors.copy()
    
    # For duplicates, change polyline coordinate order
    maz_connectors2['DIRECTION'] = 2
    maz_connectors2['geometry'] = maz_connectors2['geometry'].apply(
    lambda geom: LineString(list(geom.coords)[::-1])
    )

    maz_connectors_final = pd.concat(
        [maz_connectors, maz_connectors2],
        axis=0,
        ignore_index=True
        ).sort_values(by=["ZONENO", "NODENO"])
    
    return maz_connectors_final.reset_index(drop=True)

maz_connectors = add_connectors(maz_centroids, bike_nodes, 'MAZ')
taz_connectors = add_connectors(taz_centroids, bike_nodes, 'TAZ')

# Export
maz_connectors.to_file(maz_output_file)
taz_connectors.to_file(taz_output_file)
