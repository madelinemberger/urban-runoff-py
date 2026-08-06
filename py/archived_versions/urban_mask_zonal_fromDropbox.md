# Urban Runoff: Workflow for KOA 

Maddie Berger  
12-09-2024

This script contains the python code used to run on the KOA super computer for big jobs. Once it works here, we can export the cell chunks and .py scripts and upload to KOA. 

Inputs: 
- Tiled raw impervious surface rasters for 2011, 2017 and 2021
- Analysis mask at 200 m and 500 m
- Watersheds for zonal statistics

Outputs:
- Masked tiles
- Table per raster of zonal statistics (ie area of impervious per watershed)




## Set up 


```python
!where python;
!pip install rasterio geopandas rasterstats numpy
```


```python
import os
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import pandas as pd
from rasterstats import zonal_stats

# Define paths
raster_folder = (r".\data\rasters")
rasters_out = os.path.expanduser(r".\outputs")
mask_vector_path = os.path.expanduser(r".\data\analysis_mask_500_wNiihau.shp")
sheds_vector_path = os.path.expanduser(r".\data\WBD_HU12_n83utm4_2023fixed.shp")
#watersheds_vector_path = "/path/to/watersheds.shp"


# Load the vector mask
mask_gdf = gpd.read_file(mask_vector_path)
mask_geometry = mask_gdf.geometry

#Load the watersheds input
sheds_gdf = gpd.read_file(sheds_vector_path)
sheds_geometry = sheds_gdf.geometry
print(sheds_gdf.columns) # get the column with unique IDS for step 3
print(sheds_gdf["HUC12"].is_unique)

```

    Index(['TNMID', 'MetaSource', 'SourceData', 'SourceOrig', 'SourceFeat',
           'LoadDate', 'GNIS_ID', 'AreaAcres', 'AreaSqKm', 'States', 'HUC12',
           'Name', 'HUType', 'HUMod', 'ToHUC', 'NonContrib', 'NonContr_1',
           'Shape_Leng', 'Shape_Area', 'Area_Ag_sq', 'Area_Ag__1', 'geometry'],
          dtype='object')
    True
    

## Step 1: Check that CRS of the inputs match 


```python

# Check CRS of the inputs
# Path to the raster file
raster_samp = os.path.join(raster_folder,"ccap2011_rast12.TIF")

with rasterio.open(raster_samp) as src:
    raster_crs = src.crs
    print(f"Raster CRS: {raster_crs}")


# vectors

# Load the vector files
#mask = gpd.read_file(mask_vector_path)

# Print the CRS of the vector files
mask_crs = mask_gdf.crs
sheds_crs = sheds_gdf.crs
print(f"Mask CRS: {mask_crs}")
print(f"Sheds CRS: {sheds_crs}")

# check match between mask and the raster file

if raster_crs == mask_crs:
    print("The CRS of the raster and mask files match.")
else:
    print("The CRS of the raster and vector files do not match.")
    print(f"Raster CRS: {raster_crs}")
    print(f"Mask CRS: {vector_crs}")

```

    Raster CRS: EPSG:26904
    Mask CRS: EPSG:26904
    Sheds CRS: EPSG:26904
    The CRS of the raster and mask files match.
    

## Step 2: Mask Each Raster


```python
raster_list = [f for f in os.listdir(raster_folder) if f.endswith('.TIF')] # list rasters in the directory

if not raster_list:
    print("No rasters found in the specified folder.")
else:
    for raster in raster_list:
        raster_path = os.path.join(raster_folder, raster)
        output_path = os.path.join(rasters_out, f"masked_{raster}")

        # Check if the raster has already been processed
        if os.path.exists(output_path):
            print(f"Skipping {raster}, already processed.")
            continue

        # Process the raster
        try:
            with rasterio.open(raster_path) as src:
                # Apply the mask
                out_image, out_transform = mask(src, mask_geometry, crop=True)
                out_meta = src.meta.copy()
                
                # Update metadata
                out_meta.update({
                    "driver": "GTiff",
                    "height": out_image.shape[1],
                    "width": out_image.shape[2],
                    "transform": out_transform
                })

                # Save the masked raster
                with rasterio.open(output_path, "w", **out_meta) as dest:
                    dest.write(out_image)

            print(f"Processed and saved {output_path}")
        except Exception as e:
            print(f"Failed to process {raster}. Error: {e}")
```

    Processed and saved .\outputs\masked_ccap2011_rast11.TIF
    Processed and saved .\outputs\masked_ccap2011_rast12.TIF
    

## Step 3: Calculate pixels within each watershed

Goal: To estimate the area of impervious surface in each watershed

Assumptions: Each pixel that is classfied as impervious is fully impervious and can be multiplied by the area of the pixel (resolution squared)


```python

# Define file paths
masked_rasters = os.path.abspath(r".\outputs")
output_folder = os.path.abspath(r".\outputs")

# Print out the paths to check if they are correct
print(f"Raster folder path: {masked_rasters}")
print(f"Output folder path: {output_folder}")

# Initialize a DataFrame to store aggregated results
aggregated_results = pd.DataFrame()


# Process each raster in the folder
for raster_file in os.listdir(masked_rasters):
    if raster_file.endswith(".TIF"):  # Process only .tif files
        print(f"Processing {raster_file}...")
        raster_path = os.path.join(masked_rasters, raster_file)

    try:  
        # Open the raster file
        with rasterio.open(raster_path) as src:
            raster_data = src.read(1)  # Read the first band
            raster_meta = src.meta  # Metadata for the raster

        # Calculate zonal statistics
        stats = zonal_stats(
            sheds_gdf, # this doesn't have to be the geometries which is cool
            raster_data,
            affine=raster_meta['transform'],
            stats=['count'],
            nodata=raster_meta.get('nodata')  # Handle nodata values
        )
        print(f"Zonal stats for {raster_file}: {stats}")

        # Add results to the aggregated DataFrame
        temp_df = pd.DataFrame({
            "zone_id": sheds_gdf["HUC12"].values,  # Add unique ID for zones
            f"pixel_count_{raster_file}": [stat["count"] for stat in stats]
        })
        
        print(f"Temporary DataFrame for {raster_file}:\n{temp_df}")
        
        aggregated_results = pd.merge(
            aggregated_results, temp_df, on="zone_id", how="outer"
        ) if not aggregated_results.empty else temp_df
        
    except Exception as e:
        print(f"Error processing {raster_file}: {e}")


# Save the aggregated results to a CSV file
#aggregated_results.to_csv(os.path.join(output_folder, "aggregated_pixel_counts.csv"), index=False)

#print("Processing complete. Results saved to the output folder.")

```

    Raster folder path: C:\Users\Maddie\src\driver_py\outputs
    Output folder path: C:\Users\Maddie\src\driver_py\outputs
    Error processing aggregated_pixel_counts.csv: name 'raster_path' is not defined
    Processing masked_ccap2011_rast11.TIF...
    Zonal stats for masked_ccap2011_rast11.TIF: [{'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 32331}, {'count': 0}, {'count': 0}, {'count': 85276}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 1462}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 63622}, {'count': 40657}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 1039}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 35639}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}]
    Temporary DataFrame for masked_ccap2011_rast11.TIF:
              zone_id  pixel_count_masked_ccap2011_rast11.TIF
    0    200700000103                                       0
    1    200700000205                                       0
    2    200700000102                                       0
    3    200600000101                                       0
    4    200600000303                                       0
    ..            ...                                     ...
    168  200200000403                                   35639
    169  200100000903                                       0
    170  200100000502                                       0
    171  200100000302                                       0
    172  200100000405                                       0
    
    [173 rows x 2 columns]
    Processing masked_ccap2011_rast12.TIF...
    Zonal stats for masked_ccap2011_rast12.TIF: [{'count': 150627}, {'count': 322542}, {'count': 4900}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 52667}, {'count': 515460}, {'count': 95986}, {'count': 427966}, {'count': 505431}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 25691}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 44195}, {'count': 1074257}, {'count': 634382}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 25327}, {'count': 152180}, {'count': 283364}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 59827}, {'count': 193199}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 49492}, {'count': 5917}, {'count': 57950}, {'count': 25660}, {'count': 380092}, {'count': 356092}, {'count': 210136}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}, {'count': 0}]
    Temporary DataFrame for masked_ccap2011_rast12.TIF:
              zone_id  pixel_count_masked_ccap2011_rast12.TIF
    0    200700000103                                  150627
    1    200700000205                                  322542
    2    200700000102                                    4900
    3    200600000101                                       0
    4    200600000303                                       0
    ..            ...                                     ...
    168  200200000403                                       0
    169  200100000903                                       0
    170  200100000502                                       0
    171  200100000302                                       0
    172  200100000405                                       0
    
    [173 rows x 2 columns]
    


```python
# Save the aggregated results to a CSV file
aggregated_results.to_csv(os.path.join(output_folder, "aggregated_pixel_counts.csv"), index=False)

#print("Processing complete. Results saved to the output folder.")
```


```python

```
