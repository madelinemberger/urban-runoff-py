
# Feb 22nd, 2026 - last updated by MMTB
# This script takes each of the new Impervious surface rasters we created for 2011 and 2021 and uses the watershed vector to calculate the area of impervious surface within each watershed for both years. 
# It then outputs a table with the results.

# Note on environment: this script is designed to use the `geoenv` environment, NOT the arcpy environment
# Note from last run - everything ran exept Maui Nui. Warning on proj path


import os
import sys

# 1a. HARDCODE to geoenv to prevent it from grabbing arcpro paths
env_path = r"C:\Users\mmtb\miniconda3\envs\geoenv"
# Set the PROJ database location
os.environ["PROJ_LIB"] = proj_lib_path
os.environ["GDAL_DATA"] = gdal_data_path


# 1b. Handle DLLs for Windows
if sys.platform == 'win32' and os.path.exists(bin_path):
    # This is the most important line for the "DLL load failed" error
    os.add_dll_directory(bin_path)
    # Add to PATH as a backup
    os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')

# 2. File Paths
gdal_data_path = os.path.join(env_path, "Library", "share", "gdal")
proj_lib_path = os.path.join(env_path, "Library", "share", "proj")
bin_path = os.path.join(env_path, "Library", "bin")


#1b. Handle DLLs for Windows Dynamically

if sys.platform == "win32":
    env_path = sys.prefix  # automatically gets active env path dynamically
    gdal_data_path = os.path.join(env_path, "Library", "share", "gdal")
    proj_lib_path = os.path.join(env_path, "Library", "share", "proj")
    bin_path = os.path.join(env_path, "Library", "bin")

    os.environ["PROJ_LIB"] = proj_lib_path
    os.environ["GDAL_DATA"] = gdal_data_path

    if os.path.exists(bin_path):
        os.add_dll_directory(bin_path)
        os.environ["PATH"] = bin_path + os.pathsep + os.environ.get("PATH", "")


import rasterio
from rasterio.features import rasterize
import rioxarray
import geopandas as gpd
import pandas as pd
import numpy as np
import glob
from shapely.geometry import box



######################### SET UP #######################
# Toggles for masking or no masking. Set TRUE or FALSE depdning on which workflow you want to run. 
RUN_ANALYSIS_1 = False# Masking/Clipping (GDB -> TIF)
RUN_ANALYSIS_2 = True  # Zonal Statistics (TIF -> CSV)

# 1. PROJECT ROOT DIRECTORY
# Since 2_AreaImperv_by_Watershed.py is in the root folder, this resolves to the repo root:
base_dir = os.path.dirname(os.path.abspath(__file__))

# 2. INPUT DATA PATHS (Relative to repo root)
data_dir = os.path.join(base_dir, "data")
gdb_path = os.path.join(data_dir, "Urban_Scratch.gdb")

sheds_vector_path = os.path.join(data_dir, "WBD_HU12_n83utm4_2023fixed.shp")
mask_vector_path = os.path.join(data_dir, "analysis_mask_500_wNiihau.shp")

# 3. INTERMEDIATE & OUTPUT DIRECTORIES
int_dir = os.path.join(base_dir, "int")
output_dir = os.path.join(base_dir, "outputs")

# Auto-create intermediate and output directories if they don't exist
os.makedirs(int_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Ensure directories exist
os.makedirs(int_dir, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)

# Prefix for GDB rasters - CHANGE
gdb_prefix = "Final_v3_Mosaic_2021_MauiNui" 

# define one raster name for testing - we'll loop later

#raster_name = "imperv2021_no0s_SouthHI"
#connection_string = f'OpenFileGDB:{gdb_path}:{raster_name}' # needed for opening a gdb using rasterio
#target_tile = "imperv2021_no0s_SouthHI"  # Adjust this to match the specific tile name you want to access

###########################################################################################################
############################################## ANALYSIS 1  ################################################
###########################################################################################################
    # 1. Get all rasters in gdb
with rasterio.open(gdb_path) as src:
    all_rasters = src.subdatasets
    #Filter for rasters that match our prefix
input_rasters = [ds for ds in all_rasters if gdb_prefix in ds]

if RUN_ANALYSIS_1:
    print("Starting analysis 1: Masking GDB rasters")
    #2. Prepare mask
    gdf = gpd.read_file(mask_vector_path)
    gdf_simplified = gdf.copy()
    gdf_simplified['geometry'] = gdf_simplified.geometry.simplify(tolerance=0.5, preserve_topology=True)


    for connection_string in input_rasters:
    
        raster_name = connection_string.split(":")[-1] # extract raster name from connection string
        print(f"\nProcessing: {raster_name}")
        print(f"Connection string: {connection_string}")
        output_path = os.path.join(int_dir, f"{raster_name}_clipped.tif")

        if os.path.exists(output_path):
            print(f"Skipping {raster_name}, already processed.")
            continue

        try:
            # Load the raster as xarray DataArray
            da = rioxarray.open_rasterio(connection_string, masked=True, chunks={'x': 2048, 'y': 2048})
            if da.rio.crs is None:
                da.rio.write_crs("EPSG:26904", inplace=True)
            #standardize data type 
            da = da.astype("float32")

            # Ensure mask CRS matches raster
            gdf_mask = gdf_simplified.to_crs(da.rio.crs) if gdf_simplified.crs != da.rio.crs else gdf_simplified
            shapes = gdf_mask.geometry.values

            # Clips and save
            da_clipped = da.rio.clip(shapes, crs=da.rio.crs, drop=True)
            print(f"Successfully clipped: {raster_name}")

            # Check if anything remains after the clip
            if da_clipped.rio.width == 0 or da_clipped.rio.height == 0:
                print("⚠️ Clipped raster is empty — skipping save.")
                continue

            # Save clipped raster
            if da_clipped.rio.width > 0:
                # 1. Get the original nodata value (usually 0 or 255 for these rasters)
                nodata_val = da.rio.nodata if da.rio.nodata is not None else 0
                
                # 2. Fill NaNs with that value and cast back to integer (e.g., uint8 or int16)
                da_final = da_clipped.fillna(nodata_val).astype(da.dtype)
                
                #3. Save with the explicit nodata value defined
                da_final.rio.to_raster(output_path, nodata=nodata_val)

        except Exception as e:
            print(f"Failed to process {raster_name}: {e}")
else:
    print("Analysis 1 is FALSE. Ensuring files existing in int folder for Analysis 2...")
    for connection_string in input_rasters:
        raster_name = connection_string.split(":")[-1] # extract raster name from connection string
        output_path = os.path.join(int_dir, f"{raster_name}_clipped.tif")
        if not os.path.exists(output_path):
            print(f"Expected file not found for Analysis 2: {output_path}. Please run Analysis 1 or check your files.")
            try:
                with rioxarray.open_rasterio(connection_string, chunks={'x': 2048, 'y': 2048}) as da:
                    if da.rio.crs is None: da.rio.write_crs("EPSG:26904", inplace=True)
                    da.rio.to_raster(output_path)
                    print(f"✅ Transfer complete: {output_path}")
            except Exception as e:
                print(f"Failed to transfer {raster_name} from GDB to TIF: {e}")
        else:
            print(f"Existing TIF found for {raster_name}, no transfer needed")
############################################## ANALYSIS 2  ################################################

# Calculate pixels and area imperivous surface per watershed

if RUN_ANALYSIS_2:
    print("\nStarting analysis 2: Zonal statistics for masked rasters")
    # Logic: Read files from the intermediate folder (the outputs of Analysis 1)
    # This works whether you just ran Analysis 1 or are starting fresh from Analysis 2
    analysis_2_inputs = glob.glob(os.path.join(int_dir, f"{gdb_prefix}*.tif"))

    if not analysis_2_inputs:
        print("No input rasters found for Analysis 2. Did you run analysis 1?")
    else: 
        zone_gdf = gpd.read_file(sheds_vector_path)

        # Prepare zone mapping
        zone_ids_str = zone_gdf["HUC12"].astype(str)
        zone_id_map = {z: i+1 for i, z in enumerate(zone_ids_str)}  # +1 to avoid 0 as background
        zone_gdf["zone_int"] = zone_ids_str.map(zone_id_map) # add new column to gdf with the integer zone ids

        aggregated_results = pd.DataFrame()

        for tif_path in analysis_2_inputs:
            raster_name = os.path.basename(tif_path)
            print(f"\nProcessing: {raster_name}")
            try:
                da = rioxarray.open_rasterio(tif_path, masked=True, chunks={'x': 1024, 'y': 1024}).squeeze()
                # Get footprint of the raster
                b = da.rio.bounds()
                raster_extent_geom = box(b[0], b[1], b[2], b[3])
                # Only keep zones that intersect with the raster extent to speed up processing
                zone_gdf_subset = zone_gdf[zone_gdf.geometry.intersects(raster_extent_geom)]
                # Rasterize zone polygons to match raster shape
                zone_mask = rasterize(
                    [(geom, value) for geom, value in zip(zone_gdf_subset.geometry, zone_gdf_subset.zone_int)],
                    out_shape=da.shape,
                    transform=da.rio.transform(),
                    fill=0,
                    dtype="int32"
                )
                # Find where imperivous pixels exist
                # Adjust (da == 1) if your imperivous value happens to be different (it shouldnt be if you ran script 1)
                target_zone_ids = zone_mask[da.values == 1]

                # Count pixels per zone
                unique, counts = np.unique(target_zone_ids, return_counts=True)
                zone_counts = dict(zip(unique, counts))

                # Build df to hold results
                temp_df = pd.DataFrame({
                    "zone_id": zone_gdf["zone_int"],
                    f"pixel_count_{raster_name}": [zone_counts.get(zid, 0) for zid in zone_gdf["zone_int"].values]
                })
                print(temp_df.head())

                if aggregated_results.empty:
                    aggregated_results = temp_df
                else:
                    aggregated_results = pd.merge(aggregated_results, temp_df, on="zone_id", how="outer")

            except Exception as e:
                print(f"❌ Failed to process {raster_name}: {type(e).__name__} - {e}")
        # Final Save
        if not aggregated_results.empty:
            out_name = "aggregated_pixel_counts_2021_MauiNui_v1.6.csv"
            aggregated_results.to_csv(os.path.join(output_dir, out_name), index=False)
            print(f"✅ Process complete. Results saved to {out_name}")

