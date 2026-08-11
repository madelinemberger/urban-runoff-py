
# to start environment needed here simply do conda activate arcpro

import arcpy
import os
from arcpy.sa import *

# 1. SET PATHS
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")

#gdb_path = r"C:\Users\mmtb\src\urban_runoff_py\data\Urban_Scratch.gdb"
sr_utm4 = arcpy.SpatialReference(32604)
arcpy.env.overwriteOutput = True
# 2. Define function to process each tile.
def preprocess_county_tilepair(tile_name, path_2011, path_2021, gdb_path, sr_utm4):
    try:
        print(f"\n--- Starting {tile_name} ---")

        # --- STEP 1: CLEAN 2011 ---
        # We ensure it is 1s and 0s and save it to the GDB
        print(f"[{tile_name}] Step 1: Cleaning 2011 (Binary 1/0)...")
        raw_2011 = arcpy.Raster(path_2011)
        # Using the IsNull logic to ensure "NoData" becomes "0"
        clean_2011 = Con(raw_2011 == 1, 1, Con(IsNull(raw_2011), 0, 0))
        
        clean_2011_path = os.path.join(gdb_path, f"Final_2011_{tile_name}")
        clean_2011.save(clean_2011_path)

        # --- STEP 2: ALIGN 2021 TO 2011 ---
        print(f"[{tile_name}] Step 2: Binary conversion of 2021 (Value 2 -> 1)...")
        binary_2021_raw = Con(arcpy.Raster(path_2021) == 2, 1, 0)

        print(f"[{tile_name}] Step 3: Aggregating and Projecting 2021...")
        # We aggregate first to get close to 2m -> 4m logic, then project to exactly 2.4m
        agg_2021 = Aggregate(binary_2021_raw, 2, "MAXIMUM", "EXPAND", "DATA")

        # The MAGIC STEP: Force 2021 to live on the 2011 grid
        proj_2021_path = os.path.join(gdb_path, f"Final_2021_{tile_name}")
        
        with arcpy.EnvManager(snapRaster=clean_2011_path, extent=clean_2011_path):
            arcpy.management.ProjectRaster(
                in_raster=agg_2021, 
                out_raster=proj_2021_path, 
                out_coor_system=sr_utm4, 
                resampling_type="NEAREST",
                cell_size="2.4 2.4"
            )

        print(f"[{tile_name}] SUCCESS: Aligned rasters created.")
        
        # Memory Cleanup: Delete large temporary objects
        del clean_2011, binary_2021_raw, agg_2021
        return True

    except Exception as e:
        print(f"[{tile_name}] FAILED: {e}")
        return False

# 3. Define jobs for each tile pair


job_list = [
    {
        "tile_name": "HI",
        "p11": os.path.join(gdb_path, "CCAP_2011_HIcnty"),
        "p21": os.path.join(
            ccap_2021_dir, 
            "hi_hawaii_county_2021_ccap_draft_20260202", 
            "hi_hawaii_county_2021_ccap_draft_20260202.img"
        )
    },
    {
        "tile_name": "Oahu",
        "p11": os.path.join(gdb_path, "CCAP_OAHUcnty_2011_tif"),
        "p21": os.path.join(
            ccap_2021_dir, 
            "hi_honolulu_county_2021_ccap_draft_20260202", 
            "hi_honolulu_county_2021_ccap_draft_20260202.img"
        )
    },
    {
        "tile_name": "MauiNui",
        "p11": os.path.join(gdb_path, "CCAP_MAUINcnty_2011_tif"),
        "p21": os.path.join(
            ccap_2021_dir, 
            "hi_maui_county_2021_ccap_draft_20260202", 
            "hi_maui_county_2021_ccap_draft_20260202.img"
        )
    },
    {
        "tile_name": "Kauai",
        "p11": os.path.join(gdb_path, "CCAP_KAUAIcnty_2011_TIF"),
        "p21": os.path.join(
            ccap_2021_dir, 
            "hi_kauai_county_2021_ccap_draft_20260202", 
            "hi_kauai_county_2021_ccap_draft_20260202.img"
        ) 
    }  
]


#3. Run the function for each tile pair
# Loop through the job list and unpack the paths into the function
for job in job_list:
    # Use the keys from the dictionary as the arguments for your function
    success = preprocess_county_tilepair(
        tile_name = job["tile_name"],
        path_2011 = job["p11"],
        path_2021 = job["p21"],
        gdb_path=gdb_path,
        sr_utm4=sr_utm4)
    
    if success:
        print(f"Finished {job['tile_name']} successfully.")
    else:
        print(f"Something went wrong with {job['tile_name']}. Moving to next...")