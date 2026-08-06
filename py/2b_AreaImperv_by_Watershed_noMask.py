
# May 5, 2026 - last updated by MMTB
# This script takes each of the new Impervious surface rasters we created for 2011 and 2021 and uses the watershed vector to calculate the area of impervious surface within each watershed for both years. 
# It then outputs a table with the results.

# Note on environment: this script is designed to use the `geoenv` environment, NOT the arcpy environment
# Note from last run - everything ran exept Maui Nui. Warning on proj path, too much memory
#Updated script on 5/5/2026 to remove masking and deal with raster size better


import gc
import os
import sys

# 1. ==================================== Environment setup
# HARDCODE to geoenv to prevent it from grabbing arcpro paths
env_path = r"C:\Users\mmtb\miniconda3\envs\geoenv"
bin_path = os.path.join(env_path, "Library", "bin")
# FORCE these to be the only thing the script sees
os.environ["PROJ_LIB"] = os.path.join(env_path, "Library", "share", "proj")
os.environ["GDAL_DATA"] = os.path.join(env_path, "Library", "share", "gdal")

# CLEAR any existing PROJ_DATA variable that might be pointing elsewhere
if "PROJ_DATA" in os.environ:
    del os.environ["PROJ_DATA"]
# 1b. Handle DLLs for Windows
if sys.platform == 'win32' and os.path.exists(bin_path):
    # This is the most important line for the "DLL load failed" error
    os.add_dll_directory(bin_path)
    # Add to PATH as a backup
    os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')



import rasterio
from rasterio.features import rasterize
import rioxarray
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import box


# 2. ==================================== Define local paths
# For now just work locally, and then we can reorganize into the dropbox later

# Define local paths
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.abspath(os.path.join(script_dir, ".."))
gdb_path = r"C:\Users\mmtb\projects\urban_runoff_local\GIS_temp\Urban_Scratch.gdb"
sheds_vector_path = os.path.join(base_dir, "data", "WBD_HU12_n83utm4_2023fixed.shp")
rasters_gdb_path = os.path.join(base_dir, "GIS_temp", "Urban_Scratch.gdb")

int_dir = os.path.join(base_dir, "int")
output_dir = os.path.join(base_dir, "outputs")

# Ensure directories exist
os.makedirs(int_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Prefix for GDB rasters - CHANGE
gdb_prefix = "Final_2011_v3_nomask_" 

# define one raster name for testing - we'll loop later

# get all the rasters in the GDB and filter for our prefix
with rasterio.open(gdb_path) as src:
    all_rasters = src.subdatasets
    #Filter for rasters that match our prefix
input_rasters = [ds for ds in all_rasters if gdb_prefix in ds]

# 3. =================================== Zonal stats for UNMASKED Rasters

aggregated_results = pd.DataFrame()

# Calculate pixels and area imperivous surface per watershed

def zonal_stats_unmasked(connection_string, sheds_vector_path):
    raster_name = connection_string.split(":")[-1]  # Extract raster name from connection string
    print(f"----Processing: {raster_name}----")

    # Use a hardcoded PROJ string to bypass the broken proj.db
    # This is the string for UTM Zone 4N (EPSG:32604 / 26904 equivalent)
    utm4_proj = "+proj=utm +zone=4 +datum=NAD83 +units=m +no_defs"

    zone_gdf = gpd.read_file(sheds_vector_path)
    zone_gdf = zone_gdf.to_crs(utm4_proj) # reproject to match raster CRS, which we know is UTM4. This is critical for accurate rasterization and area calculations
    zone_ids_str = zone_gdf["HUC12"].astype(str)
    zone_id_map = {z: i+1 for i, z in enumerate(zone_ids_str)}  # +1 to avoid 0 as background
    zone_gdf["zone_int"] = zone_ids_str.map(zone_id_map) # add new column to gdf with the integer zone ids for rasterization

    # Open raster with chunking
    da = rioxarray.open_rasterio(connection_string, masked=True, chunks={'x': 4096, 'y': 4096}).squeeze().astype("uint8")
    da.rio.write_crs(utm4_proj, inplace=True) # force the CRS to be correct, since some of these are missing it. We know they should all be in 32604
    # Get footprint of the raster
    b = da.rio.bounds()
    raster_extent_geom = box(b[0], b[1], b[2], b[3])
    # Only keep zones that intersect with the raster extent to speed up processing
    zone_gdf_subset = zone_gdf[zone_gdf.geometry.intersects(raster_extent_geom)]
    
    print(f"Rasterizing{len(zone_gdf_subset)} zones for {os.path.basename(connection_string)}...")
    # Rasterize zone polygons to match raster shape
    zone_mask = rasterize(
           [(geom, value) for geom, value in zip(zone_gdf_subset.geometry, zone_gdf_subset.zone_int)],
           out_shape=da.shape,
           transform=da.rio.transform(),
           fill=0,
           dtype="int32"
           )

    print("Calculating pixel counts (this may take a moment)...")
    # CRITICAL: We avoid da.values here to save RAM. 
    # We use a boolean mask on the dask array and find where zone_mask has data.
    # We flatten only the necessary pixels.
    data_flat = da.data.flatten() # This is a Dask array, won't load yet
    mask_flat = (data_flat == 1).compute() # This triggers a filtered load
    
    target_zone_ids = zone_mask.flatten()[mask_flat]

    # Count pixels per zone
    unique, counts = np.unique(target_zone_ids, return_counts=True)
    pixel_results = dict(zip(unique, counts))

    # Build final dataframe
    results_df = pd.DataFrame({
        "HUC12": zone_ids_str,
        "zone_id": zone_gdf["zone_int"],
        "impervious_pixel_count": zone_gdf["zone_int"].map(pixel_results).fillna(0).astype(int)
    })

    return results_df

# 4. ================= Execution loop 
for connection_string in input_rasters:
    raster_name = connection_string.split(":")[-1]
    try:
        final_df = zonal_stats_unmasked(connection_string, sheds_vector_path)
        out_file = os.path.join(output_dir, f"ZonalStats_{raster_name}_nomask_1.6.csv")
        final_df.to_csv(out_file, index=False)
        print(f"✅ Success! Saved to: {out_file}")
        
        # Explicitly clean up memory before next loop
        del final_df
        gc.collect() 
        
    except Exception as e:
        print(f"❌ Error processing {raster_name}: {e}")