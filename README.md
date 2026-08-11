# Urban Runoff Spatial Analysis Pipeline - Steps 1 and 2

This repository contains Python scripts  designed for urban runoff modeling, raster resampling, masking, and zonal statistics calculations. 

The pipeline has been NOT been fully refactored to rely exclusively on open-source GIS libraries (`geopandas`, `rasterio`, `rioxarray`, `shapely`. Currently Script 1 requires proprietary software licenses (e.g., ArcGIS / `arcpy`), but Script 2 runs on open source Python packages. 


---

## Repository Layout

```text

├── README.md
├── 1_Preprocess_2011_2021_NoMosaic_NoMask.py   # Step 1: Preprocess, align rasters, and prepare zones (ArcPy)
├── 2_AreaImperv_by_Watershed.py                # Step 2: Calculate impervious surface areas per watershed (Open-Source)
├── zone_id_mapping.csv                         # Mapping table linking integer zone IDs to HUC Watershed IDs/Names
│
├── envs/
│   ├── arcpro.yml                               # Conda environment definition for Step 1 (ArcPy dependent)
│   └── geoenv.yml                               # Conda environment definition for Step 2 (Open-Source)
│
├── data/                                       # Local input data (ignored by Git)
│   ├── Urban_scratch.gdb/
│   └── README.txt
│
├── outputs/                                    # Processed outputs and summary tables (for Step 4)
│
└── archive/                                    # Legacy and experimental scripts
│
└── int/                                    # intermediate products from Script 2

```



## Execution Flow

Step 1: Raster Alignment & Zone Preparation
Script: 1_Preprocess_2011_2021_NoMosaic_NoMask.py

Environment: arcpro

Description: Cleans 2011 CCAP data, resamples and aligns 2021 CCAP rasters to the 2011 cell grid (2.4m resolution, UTM Zone 4N), and prepares rasterized watershed zones.

Note: Script 1 currently requires the Urban_scratch.gdb database located in your local data/ directory or specified C: Drive path.

Step 2: Impervious Surface Calculation by Watershed
Script: 2_AreaImperv_by_Watershed.py

Environment: geoenv

Description: Runs zonal statistics across urban watershed boundaries using open-source tools to calculate total impervious surface areas. Translates integer raster IDs back to standard HUC watershed identifiers using zone_id_mapping.csv. Outputs final summary tables into the outputs/ folder.


Step 3: Create Coastal Impact Raster

Environement: R

Description: This part of the model is done in R. The markdown walks through each step in detail, calling R scripts to load custom built functions that execute each step. Outputs the final coastal impact raster into the versioned folder on Dropbox.


Notes: 

- To run script 1, you must be working from your own C Drive and have the Urban_Scratch downloaded onto your local machine. In the future we hope to have script one independent of ArcPro to avoid this barrier. 


- The data/ folder is excluded from version control via .gitignore due to file size constraints. Ensure you place Urban_scratch.gdb and any raw input rasters inside the data/ directory before running the scripts.