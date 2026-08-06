# Open-Source Urban Runoff Spatial Analysis Pipeline

This repository contains a suite of open-source Python scripts and Jupyter notebooks designed for urban runoff modeling, raster resampling, masking, and zonal statistics calculations. 

The pipeline has been fully refactored to rely exclusively on open-source GIS libraries (`geopandas`, `rasterio`, `rioxarray`, `shapely`) to ensure full reproducibility and transparency without requiring proprietary software licenses (e.g., ArcGIS / `arcpy`).

---

## Repository Layout

```text
├── .gitignore
├── README.md
├── environment.yml          # Conda / Mamba environment definition
├── requirements.txt         # Pip dependency manifest
├── py/                      # Core analysis scripts and notebooks
│   ├── 1_Urban_resample_mask_zonal.ipynb # Raw raster prep - resample, create zoned watershed raster 
│   ├── 2a_AreaImperv_by_Watershed.py        # Calculate impervious pixels by watershed 
│   ├── 2b_AreaImperv_by_Watershed_nomask.py # Calculate impervious pixels by watershed, and mask to urban areas only
│   └── zone_id_mapping.csv      # Mapping for rasterized watersheds: raster can only take integers, and this csv matches each zone number to the longer HUC watershed ID and Name
│   └── archived_versions/  # old scripts no longer used