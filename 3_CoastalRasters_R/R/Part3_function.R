# Part 3 - Decay Function
# Maddie Berger
# Created May 2023, Updated Jan 2025


## This script executes the last two steps of the V1 land-based runoff model, which are:
## 1. To multiply the nearshore rasters we extended by a decay function. This operation relies on a basic assumption that impact (ie our "impact metric") decreases as a function of its distance from shore. 
## 2. Divide the entire raster by the max value to create a normalized nearshore raster


offshore_decay <- function(impact_rast,dist_rast,year){
  
  nearshore_impact <- impact_rast
  dist_from_shore <- dist_rast
  
  ## Make sure rasters align and stack them
  
  impact_ext <- terra::extend(nearshore_impact,dist_from_shore)
  
  dist_ext <- terra::extend(dist_from_shore, impact_ext)
  
  rstack <- c(impact_ext,dist_ext)
  
  ## Apply the decay function 
  
  nearshore_decay <- terra::lapp(
    rstack,
    fun = function(x,y){
      return(x * exp(-1 *(y^2.5)/10^7.5))
    }
  )
  
  
  ### Find the max value and divide the raster by that to normalize it
  ### Update July 2024 - I commented this out because we are going to want to normalize by the highest value for any of the rasters we make
  
  nearshore_decay_01 <- nearshore_decay / minmax(nearshore_decay)[2]
  
  nearshore_decay_01_global <- nearshore_decay / 23.73366 # this is the maximum value for all, which is 2011
  
  # Save raster to output folder - comment out based on if you are doing ag or golf
  #writeRaster(nearshore_decay, filename = paste0(ag_dir,"/output_data/final_Golf/V1/GolfRunoff_",year,"_decay_qaqc.tif"), overwrite = TRUE)
  writeRaster(nearshore_decay, filename = paste0(urban_dropbox,"/output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_",year,"_decay_masked.tif"), overwrite = TRUE)
  writeRaster(nearshore_decay_01, filename = paste0(urban_dropbox,"/output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_",year,"_01.tif"), overwrite = TRUE)
  writeRaster(nearshore_decay_01_global, filename = paste0(urban_dropbox,"/output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_",year,"_decay_01_global.tif"), overwrite = TRUE)
  
  return(nearshore_decay)
  
  
}