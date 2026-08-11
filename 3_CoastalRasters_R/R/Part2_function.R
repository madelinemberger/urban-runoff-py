# LBSP Layers Part 2 - Disperse to Neashore
## Maddie Berger
## Created in March 2023, Updated Jan 2025


## This second part of the model does 2 major transformations to the output of the first model.
## 1. It rasterizes the watershed based on the percent of land
## 2. It applies focal statistics to extend the rasterized wateshed values to the nearshore area
## 3. It extracts using the ocean mask 



# Inputs: 
# column we are interested in rasterizing, 
# year in character form (for file paths)
# To prep for this you must have the ocean mask and watersheds with agriculture file read in and named a certainthing

# Outputs:
# A raster of relative runoff impact, masked to the nearshore areas

rasterize_expand <- function(col,year){
  
  ### testing ###
  
  #col = "areaImp_11_km"
  #year = "2011"
  
  ###########
  
  # 1. Rasterize watersheds
  
  ## create raster template with ocean mask 
  
  r_om <- raster(ocean_mask_nad83utm)
  
  ## use fasterize to raster watersheds
  
  watershed_area_ras <- fasterize(watershed_nad83utm,r_om,field = col, fun = "max")
  
  ## convert to spat raster for next steps (terra uses less memory than the raster package)
  
  watershed_area_spatras <- as(watershed_area_ras,"SpatRaster")
  
  # 2. Apply focal statistics
  
  ## first need to create a matrix to pass to the focal argument
  
  
  fw_mat <- focalMat(watershed_area_spatras,2500, type = "circle") #2100 does not cover all indicator maps
  fw_mat[fw_mat > 0 ] <- 1
  
  tic()
  focalStat <- terra::focal(watershed_area_spatras,w = fw_mat, fun = "mean", na.rm = T) # na.rm key to making it expand out
  toc() #128.58
  
  # 3. Write to scratch folder
  
  #focalStat_ras <- raster(focalStat)
  
  writeRaster(focalStat,
              filename = paste0(urban_dropbox,"/scratch_data/focStat_urban_",year,".tif"), 
              overwrite = TRUE)
  
  print("write focal stats raster to scratch folder on Dropbox")
  
  
  # 4. Bonus: Extract by mask
  
  # replace 0s with NAs - not always necessary
  # ocean_mask[ocean_mask != 10] <- NA # I had to change this because it reads in the new om weird
  # 
  # ocean_mask_spat <- as(ocean_mask,"SpatRaster")
  
  # use mask function from terra
  
  focalStat_nearshore <- mask(focalStat,ocean_mask_nad83utm)
  
  writeRaster(focalStat_nearshore, 
              filename = paste0(urban_dropbox,"/scratch_data/focSt_extract_urban_",year,".tif"),
              overwrite = TRUE)
  
  print("wrote ocean mask extracted faster to scratch folder on Dropbox")
  
  return(focalStat_nearshore)
  
  
}



