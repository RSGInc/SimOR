"""
Preprocessor for ActivitySim input files.
Adds derived columns to land_use, households, and persons tables.
"""

import pandas as pd
import numpy as np
import geopandas as gpd
import sys
import time
import yaml
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class PreprocessorSettings:
    """Settings for the preprocessor."""
    data_dir: Path = field(default_factory=lambda: Path("data"))
    output_dir: Path = None  # None means overwrite input files
    households_file: str = "households.csv"
    persons_file: str = "persons.csv"
    land_use_file: str = "land_use.csv"
    maz_shp_file: str = None  # Path to MAZ shapefile for calculating acres
    maz_stop_walk_file: str = None  # Path to MAZ stop walk distances file
    maz_maz_walk_file: str = None
    nodes_file: str = None
    links_file: str = None
    density_radius: float = 0.50 # Buffer radius for density calcs, miles 
    crs: int = None
    link_filter_col: str = None
    keep_link_types: dict = None
    
    def __post_init__(self):
        # Convert strings to Path objects
        if isinstance(self.data_dir, str):
            self.data_dir = Path(self.data_dir)
        if isinstance(self.output_dir, str):
            self.output_dir = Path(self.output_dir)
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "PreprocessorSettings":
        """Load settings from a YAML file."""
        with open(yaml_path, "r") as f:
            config = yaml.safe_load(f) or {}
        return cls(**config)


def load_data(settings: PreprocessorSettings) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load the three input CSV files."""
    households = pd.read_csv(settings.data_dir / settings.households_file)
    persons = pd.read_csv(settings.data_dir / settings.persons_file)
    land_use = pd.read_csv(settings.data_dir / settings.land_use_file)
    return households, persons, land_use


def fix_duplicate_household_ids(
    households: pd.DataFrame, 
    persons: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Check if household_id is unique. If not, create new unique IDs.
    
    Uses MAZ to match persons to the correct duplicated household.
    Original household_id is saved to non_unique_household_id.
    
    Parameters
    ----------
    households : pd.DataFrame
        Households table
    persons : pd.DataFrame
        Persons table
        
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame]
        Updated (households, persons) DataFrames
    """
    # Check for duplicates
    duplicate_mask = households.duplicated(subset=["household_id"], keep=False)
    num_duplicates = duplicate_mask.sum()
    
    if num_duplicates == 0:
        print("All household_id values are unique")
        return households, persons
    
    print(
        f"Found {num_duplicates} rows with duplicate household_id values:\n\t \
            {households[duplicate_mask].sort_values('household_id')}"
    )

    # Save original household_id
    households["non_unique_household_id"] = households["household_id"]
    persons["non_unique_household_id"] = persons["household_id"]
    
    # Create new unique IDs for each duplicate row
    # Start new IDs from max existing ID + 1
    max_id = households["household_id"].max()
    
    # Assign a unique new ID to EACH row that has a duplicate household_id
    # (not just unique combinations, since same household_id + MAZ can appear multiple times)
    num_duplicates_to_fix = duplicate_mask.sum()
    households.loc[duplicate_mask, "household_id"] = range(
        max_id + 1, max_id + 1 + num_duplicates_to_fix
    )
    
    # Update persons table
    # Join persons with households to get MAZ, then map to new household_id
    persons_with_maz = persons.merge(
        households[["household_id", "non_unique_household_id", "MAZ"]].drop_duplicates(),
        left_on="non_unique_household_id",
        right_on="non_unique_household_id",
        how="left",
        suffixes=("_old", "")
    )
    
    # For persons that matched, use the new household_id
    if "household_id_old" in persons_with_maz.columns:
        persons_with_maz["household_id"] = persons_with_maz["household_id"].fillna(
            persons_with_maz["household_id_old"]
        )
        persons_with_maz = persons_with_maz.drop(columns=["household_id_old"])
    
    # Drop the MAZ column we added from the merge (keep original if exists)
    if "MAZ" in persons.columns:
        persons_with_maz = persons_with_maz.drop(columns=["MAZ"])
    
    persons = persons_with_maz
    
    # Verify the fix
    remaining_duplicates = households.duplicated(subset=["household_id"], keep=False).sum()
    if remaining_duplicates > 0:
        print(f"Warning: {remaining_duplicates} duplicate household_id values remain")
    else:
        print(f"Successfully created unique household_id values")
        print(f"Original IDs saved to 'non_unique_household_id' column")
    
    return households, persons


def add_tothhs(land_use: pd.DataFrame, households: pd.DataFrame) -> pd.DataFrame:
    """Add TOTHHS (total households per zone) to land_use if not present."""
    if "TOTHHS" not in land_use.columns:
        tothhs = (
            households.groupby("MAZ")
            .size()
            .reindex(land_use.index)
            .fillna(0)
            .astype(int)
        )
        land_use["TOTHHS"] = tothhs.values
        print("Added TOTHHS to land_use")
    else:
        print("TOTHHS already exists in land_use")
    return land_use


def add_totpop(land_use: pd.DataFrame, persons: pd.DataFrame, households: pd.DataFrame) -> pd.DataFrame:
    """Add TOTPOP (total population per zone) to land_use if not present."""
    if "TOTPOP" not in land_use.columns:
        # Join persons to households to get MAZ
        if "MAZ" not in persons.columns:
            persons_with_zone = persons.merge(
                households[["household_id", "MAZ"]],
                on="household_id",
                how="left"
            )
        else:
            persons_with_zone = persons
        totpop = (
            persons_with_zone.groupby("MAZ")
            .size()
            .reindex(land_use.index)
            .fillna(0)
            .astype(int)
        )
        land_use["TOTPOP"] = totpop.values
        print("Added TOTPOP to land_use")
    else:
        print("TOTPOP already exists in land_use")
    return land_use


def add_acres(land_use: pd.DataFrame, maz_shp_file: str = None) -> pd.DataFrame:
    """Add ACRES to land_use if not present, calculating from shapefile.
    
    Parameters
    ----------
    land_use : pd.DataFrame
        Land use table with MAZ index
    maz_shp_file : str, optional
        Path to MAZ shapefile. Required if ACRES field is missing.
        
    Returns
    -------
    pd.DataFrame
        Updated land_use with ACRES field
    """
    if "ACRES" in land_use.columns:
        print("ACRES already exists in land_use")
        return land_use
    
    if maz_shp_file is None:
        print("Warning: ACRES field not found and no maz_shp_file provided, skipping")
        return land_use
    
    print(f"Reading shapefile: {maz_shp_file}")
    gdf = gpd.read_file(maz_shp_file)
    
    # Identify the MAZ ID column in the shapefile
    # Common variations: MAZ, MAZ_ID, maz, ID, etc.
    maz_col = None
    for col in gdf.columns:
        if col.upper() in ['MAZ', 'MAZ_ID', 'ID', 'MAZ_NO']:
            maz_col = col
            break
    
    if maz_col is None:
        print(f"Warning: Could not identify MAZ ID column in shapefile")
        print(f"Available columns: {list(gdf.columns)}")
        return land_use
    
    print(f"Using '{maz_col}' as MAZ identifier")
    
    # Calculate area in acres
    # Convert to appropriate CRS if needed (shapefile should be in projected coordinates)
    if gdf.crs is None:
        print("Warning: Shapefile has no CRS defined, assuming units are in feet")
        sq_units_per_acre = 43560  # square feet per acre
    elif gdf.crs.is_geographic:
        print(f"Warning: Shapefile is in geographic CRS ({gdf.crs}), reprojecting to UTM for accurate area calculation")
        # Estimate UTM zone from centroid
        gdf = gdf.to_crs(gdf.estimate_utm_crs())
        sq_units_per_acre = 4046.86  # square meters per acre
    else:
        # Check the linear units of the projected CRS
        axis_info = gdf.crs.axis_info
        if axis_info and len(axis_info) > 0:
            unit_name = axis_info[0].unit_name.lower()
            if 'foot' in unit_name or 'feet' in unit_name or 'ft' in unit_name:
                sq_units_per_acre = 43560  # square feet per acre
                print(f"CRS units: feet")
            elif 'metre' in unit_name or 'meter' in unit_name or 'm' in unit_name:
                sq_units_per_acre = 4046.86  # square meters per acre
                print(f"CRS units: meters")
            else:
                raise RuntimeError("Warning: Could not determine CRS units from shapefile for ACRES calculation")
        else:
            raise RuntimeError("Warning: Could not determine CRS units from shapefile for ACRES calculation")
    
    # Calculate area in native units, then convert to acres
    gdf['ACRES'] = gdf.geometry.area / sq_units_per_acre
    
    # Create a mapping from MAZ to ACRES
    acres_map = gdf.set_index(maz_col)['ACRES'].to_dict()
    
    # Add ACRES to land_use based on MAZ index
    land_use['ACRES'] = land_use.index.map(acres_map)
    
    # Check for missing values
    missing_count = land_use['ACRES'].isna().sum()
    if missing_count > 0:
        print(f"Warning: {missing_count} MAZ zones have no matching geometry in shapefile")
        # Fill missing with 0 or leave as NaN?
        land_use['ACRES'] = land_use['ACRES'].fillna(0)
    
    # Reasonableness checks
    min_acres = land_use['ACRES'].min()
    max_acres = land_use['ACRES'].max()
    mean_acres = land_use['ACRES'].mean()
    median_acres = land_use['ACRES'].median()
    
    print(f"Added ACRES to land_use (calculated from shapefile)")
    print(f"  Min: {min_acres:.2f}, Max: {max_acres:.2f}, Mean: {mean_acres:.2f}, Median: {median_acres:.2f}")
    
    # Sanity checks for typical urban MAZ sizes
    assert median_acres >= 0.1, f"Median ACRES ({median_acres:.4f}) seems too small. Check CRS units."
    assert median_acres <= 1000, f"Median ACRES ({median_acres:.2f}) seems too large. Check CRS units."
    # assert max_acres <= 50000, f"Max ACRES ({max_acres:.2f}) is very large. Some zones may be rural or external."
    assert min_acres >= 0, f"Negative ACRES detected ({min_acres:.4f}). Check for invalid geometries."
    
    return land_use


def merge_maz_stop_walk(land_use: pd.DataFrame, maz_stop_walk_file: str = None) -> pd.DataFrame:
    """Merge MAZ to stop walk distances to land_use.
    
    Parameters
    ----------
    land_use : pd.DataFrame
        Land use table with MAZ column
    maz_stop_walk_file : str, optional
        Path to MAZ stop walk distances CSV file.
        
    Returns
    -------
    pd.DataFrame
        Updated land_use with walk distance columns
    """
    if maz_stop_walk_file is None:
        print("No maz_stop_walk_file provided, skipping")
        return land_use
    
    print(f"Reading MAZ stop walk file: {maz_stop_walk_file}")
    maz_stop_walk = pd.read_csv(maz_stop_walk_file)
    
    # Check which columns will be added
    new_cols = [col for col in maz_stop_walk.columns if col != 'maz' and col not in land_use.columns]
    existing_cols = [col for col in maz_stop_walk.columns if col != 'maz' and col in land_use.columns]
    
    if existing_cols:
        print(f"  Columns already in land_use (skipping): {existing_cols}")
    
    if not new_cols:
        print("  All columns already exist in land_use, skipping merge")
        return land_use
    
    # Merge on MAZ
    # Determine the MAZ column name in land_use (could be 'MAZ' or 'maz')
    if 'MAZ' in land_use.columns:
        land_use_maz_col = 'MAZ'
    elif 'maz' in land_use.columns:
        land_use_maz_col = 'maz'
    else:
        print("Warning: Could not find MAZ column in land_use")
        return land_use
    
    # Merge only the new columns plus the join key
    cols_to_merge = ['maz'] + new_cols
    land_use = land_use.merge(
        maz_stop_walk[cols_to_merge],
        left_on=land_use_maz_col,
        right_on='maz',
        how='left'
    )
    
    # Drop the duplicate maz column from the merge if it was added
    if 'maz' in land_use.columns and land_use_maz_col == 'MAZ':
        land_use = land_use.drop(columns=['maz'])
    
    # Check for missing values
    for col in new_cols:
        missing_count = land_use[col].isna().sum()
        if missing_count > 0:
            print(f"  Warning: {missing_count} MAZ zones have no {col} value, filling with 0")
            land_use[col] = land_use[col].fillna(0)
    
    print(f"  Added columns to land_use: {new_cols}")
    
    return land_use

def get_intersection_count(
    settings: PreprocessorSettings, 
    land_use: pd.DataFrame
) -> pd.DataFrame:
    """ Count number of intersections in network 
    
    Parameters
    ----------
    land_use : pd.DataFrame
        Land use table with MAZ column
 
    Returns
    -------
    pd.DataFrame
        Updated land_use with intersection counts
    
    """   
    # Load settings 
    nodes_file = settings.nodes_file
    links_file = settings.links_file
    maz_shp_file = settings.maz_shp_file
    filter_col = settings.link_filter_col
    keep_link_types = settings.keep_link_types
    
    if nodes_file is None:
        print("Warning: missing node data, skipping intersection count")
        return land_use
    if links_file is None:
        print("Warning: missing link data, skipping intersection count")
        return land_use
    if maz_shp_file is None:
        print("Warning: missing maz_shp_file, skipping intersection count")
        return land_use
    
    # Load data
    print(f"Reading nodes file: {nodes_file}")
    nodes = gpd.read_file(nodes_file)
    print(f"Reading links file: {links_file}")
    links = gpd.read_file(links_file)
    print(f"Reading maz_shp_file: {maz_shp_file}")
    maz = gpd.read_file(settings.maz_shp_file)
    
    links[filter_col] = pd.to_numeric(links[filter_col], errors='coerce')
    
    # Check crs
    if not nodes.crs.is_projected:
        print(f"Converted nodes to projected CRS: {settings.crs}")
        nodes = nodes.to_crs(settings.crs)
   
    if maz.crs != nodes.crs:
        print(f"Converted maz shp to {nodes.crs}")
        maz = maz.to_crs(nodes.crs)
    
    # Filter links
    links = links[links[filter_col].isin(keep_link_types)]
    links['link_count'] = 1
    
    # Aggregate by NodeA and NodeB
    links_nodeA = links[['FROMNODENO', 'link_count']].groupby('FROMNODENO').sum().reset_index().rename(columns = {'FROMNODENO':'A'})
    links_nodeB = links[['TONODENO', 'link_count']].groupby("TONODENO").sum().reset_index().rename(columns = {'TONODENO':'B'})
    
    # Merge the two and keep all recrods from both dataframe (how='outer')
    nodes_linkcount = pd.merge(links_nodeA, links_nodeB, left_on='A', right_on = 'B', how='outer')
    nodes_linkcount = nodes_linkcount.fillna(0)
    nodes_linkcount['link_count'] = nodes_linkcount['link_count_x'] + nodes_linkcount['link_count_y']
    
    # Get node id from both dataframes
    nodes_linkcount['N'] = 0.0 # float
    nodes_linkcount.loc[nodes_linkcount.A > 0, 'N'] = nodes_linkcount['A']
    nodes_linkcount.loc[nodes_linkcount.B > 0, 'N'] = nodes_linkcount['B']
    nodes_linkcount = nodes_linkcount[['N', 'link_count']]
        
    # Keep nodes with 3+ links
    intersections_temp = nodes_linkcount.loc[nodes_linkcount.link_count >= 3]

    # Get node X and Y
    intersections = pd.merge(intersections_temp, nodes[['NO', 'XCOORD', 'YCOORD']], left_on='N', right_on='NO', how='left')
    intersections = intersections[['N', 'XCOORD', 'YCOORD']]
    intersections = intersections.rename(columns = {'XCOORD':'X', 'YCOORD':'Y'})

    # Find MAZ col in maz_shp
    maz_col = None
    for col in maz.columns:
        if col.upper() in ['MAZ', 'MAZ_NO', 'MAZ_ID', 'ID']:
            maz_col = col
            break
    
    # Find maz centroids
    maz['XCOORD'] = maz.geometry.centroid.x
    maz['YCOORD'] = maz.geometry.centroid.y
    maz_nodes = maz[[maz_col] + ['XCOORD', 'YCOORD']]
    maz_nodes.columns = ['MAZ', 'X', 'Y']

    # Find nearest maz for each intersection (euclidean distance)
    int_dict = {}
    for i in intersections.iterrows():
        maz_nodes['dist'] = np.sqrt((i[1][1] - maz_nodes['X'])**2+(i[1][2] - maz_nodes['Y'])**2)
        int_dict[i[1][0]] = maz_nodes.loc[maz_nodes['dist'] == maz_nodes['dist'].min()]['MAZ'].values[0]
        
    intersections['near_maz'] = intersections['N'].map(int_dict)
    intersections = intersections.groupby('near_maz', as_index = False).count()[['near_maz','N']].rename(columns = {'near_maz':'MAZ','N':'icnt'})
    
    # Merge counts with land use data
    land_use = pd.merge(land_use, intersections, on = "MAZ", how = "left").fillna(0)
    return land_use

def get_density(land_use: pd.DataFrame, settings: PreprocessorSettings,) -> pd.DataFrame:
    """Calculate land use densities and intersections
    
    Parameters
    ----------
    land_use : pd.DataFrame
        Land use table with MAZ column
        
    Returns
    -------
    pd.DataFrame
        Updated land_use with empden, retempden, duden,
        popden, popempdenpermi, totint
    
    """
    # Load settings
    if settings.maz_maz_walk_file is None:
        print("No maz_maz_walk file provided, skipping densities")
        return land_use
    
    print(f"Reading MAZ walk file: {settings.maz_maz_walk_file}")
    maz_maz_walk = pd.read_csv(settings.maz_maz_walk_file)
    
    new_cols = ['empden', 'retempden', 'duden', 'popden', 'popempdenpermi', 'totint']
    for col in new_cols:
        if col in land_use.columns:
            land_use = land_use.drop(col, axis=1)
            
    maz_col = None
    for col in land_use.columns:
        if col.upper() in ['MAZ', 'MAZ_NO', 'MAZ_ID', 'ID']:
            maz_col = col
            break
    
    # Count intersections per MAZ
    land_use = get_intersection_count(settings, land_use)
    
    def _density_function(maz_in: int) -> tuple:
        """Calculate densities for one MAZ by including other MAZs within walking radius.
        
        Parameters
        ----------
        maz_in: MAZ ID to analyze
            
        Returns
        -------
        Tuple with density metrics 
        
        """
        dist_skim = maz_maz_walk[maz_maz_walk['OMAZ'] == maz_in]
        maz_circa_int = dist_skim[dist_skim['DISTWALK'] < settings.density_radius]['j'].unique()
        nearby_maz = land_use[land_use[maz_col].isin(maz_circa_int)]
        sums = nearby_maz[['EMP_TOTAL', 'EMP_RET', 'TOTHHS', 'TOTPOP', 'ACRES', 'icnt']].sum()

        if (sums['ACRES'] > 0):
            empDen = sums['EMP_TOTAL'] / sums['ACRES']
            retDen = sums['EMP_RET'] / sums['ACRES']    
            duDen = sums['TOTHHS'] / sums['ACRES']     
            popDen = sums['TOTPOP'] / sums['ACRES']      
            popEmpDenPerMi = (sums['EMP_TOTAL'] + sums['TOTPOP']) / (sums['ACRES'] / 640) # acres to miles
            totInt = sums['icnt']
        else:
            empDen = 0.0
            retDen = 0.0
            duDen = 0.0
            popDen = 0.0
            popEmpDenPerMi = 0.0 
            totInt = 0
        
        return empDen, retDen, duDen, popDen, popEmpDenPerMi, totInt
    
    (
        land_use[new_cols[0]], 
        land_use[new_cols[1]], 
        land_use[new_cols[2]], 
        land_use[new_cols[3]], 
        land_use[new_cols[4]], 
        land_use[new_cols[5]]
    ) = zip(*land_use['MAZ'].map(_density_function))    
    
    land_use[new_cols] = round(land_use[new_cols], 3)
    print(f"Added columns to land_use: {new_cols}")
    return land_use

def dataframes_equal(df1: pd.DataFrame, df2: pd.DataFrame) -> bool:
    """Check if two DataFrames are equal."""
    if df1.shape != df2.shape:
        return False
    if list(df1.columns) != list(df2.columns):
        return False
    return df1.equals(df2)


def write_output(
    settings: PreprocessorSettings,
    households: pd.DataFrame,
    persons: pd.DataFrame,
    land_use: pd.DataFrame,
    original_households: pd.DataFrame,
    original_persons: pd.DataFrame,
    original_land_use: pd.DataFrame,
) -> None:
    """
    Write output files to the output directory.
    
    If overwriting input files (output_dir is None), only write files that changed.
    """
    output_dir = settings.output_dir if settings.output_dir else settings.data_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    overwriting = settings.output_dir is None
    
    # Write households
    households_path = output_dir / settings.households_file
    if overwriting and dataframes_equal(households, original_households):
        print(f"No changes to households, skipping write")
    else:
        households.to_csv(households_path, index=False)
        print(f"Saved households to {households_path}")
    
    # Write persons
    persons_path = output_dir / settings.persons_file
    if overwriting and dataframes_equal(persons, original_persons):
        print(f"No changes to persons, skipping write")
    else:
        persons.to_csv(persons_path, index=False)
        print(f"Saved persons to {persons_path}")
    
    # Write land_use
    land_use_path = output_dir / settings.land_use_file
    if overwriting and dataframes_equal(land_use, original_land_use):
        print(f"No changes to land_use, skipping write")
    else:
        land_use.to_csv(land_use_path, index=False)
        print(f"Saved land_use to {land_use_path}")


def preprocess(settings: PreprocessorSettings) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Main preprocessing function.
    
    Parameters
    ----------
    settings : PreprocessorSettings
        Configuration settings for the preprocessor
    
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Updated (households, persons, land_use) DataFrames
    """
    # Load data
    households, persons, land_use = load_data(settings)
    
    # Keep copies of originals for change detection
    original_households = households.copy()
    original_persons = persons.copy()
    original_land_use = land_use.copy()
    
    # Fix duplicate household IDs
    households, persons = fix_duplicate_household_ids(households, persons)
    
    # Add TOTHHS and TOTPOP
    land_use = add_tothhs(land_use, households)
    land_use = add_totpop(land_use, persons, households)
    
    # Add ACRES if needed
    land_use = add_acres(land_use, settings.maz_shp_file)
    
    # Merge MAZ stop walk distances if provided
    land_use = merge_maz_stop_walk(land_use, settings.maz_stop_walk_file)
    
    # Calculate land use densities
    land_use = get_density(land_use, settings)
    
    # Write output files
    write_output(
        settings,
        households,
        persons,
        land_use,
        original_households,
        original_persons,
        original_land_use,
    )
    
    return households, persons, land_use


if __name__ == "__main__":
    start_time = time.time()
    
    # Load settings from YAML if path provided, otherwise use defaults
    if len(sys.argv) > 1:
        yaml_path = Path(sys.argv[1])
        if not yaml_path.exists():
            print(f"Error: YAML file not found: {yaml_path}")
            sys.exit(1)
        settings = PreprocessorSettings.from_yaml(yaml_path)
        print(f"Loaded settings from {yaml_path}")
    else:
        settings = PreprocessorSettings()
        print("Using default settings")
    
    preprocess(settings)
    
    elapsed_time = time.time() - start_time
    print(f"\nPreprocessor completed in {elapsed_time:.2f} seconds")