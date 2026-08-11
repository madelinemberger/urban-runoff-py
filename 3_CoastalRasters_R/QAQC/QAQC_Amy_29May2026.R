
#==========================================================================================================#
# Title: GIS QAQC - Urban Runoff
# Author: Amy Carrillo
# Date: 05/29/2026
#==========================================================================================================#
# A. Notes ----------------------------------------------------------------
# - final layer names don't match with the file sin the output folder

#==========================================================================================================#
# B. Packages/Libraries ---------------------------------------------------
library(sf)
library(dplyr)
library(raster)
library(terra)
library(here)
library(mapview)
library(ggplot2)
library(tidyr)

#==========================================================================================================#
# C. Data -----------------------------------------------------------------
## User path (substitute with computer user)
getwd()
user <- "C:/Users/Amy/Donovan Lab Dropbox/Donovan Lab Team Folder"
my_directory <- file.path(user, "Donovan_Lab_GIS/Drivers/2_Urban_Runoff")
setwd(my_directory)

## Output Layers
CCAP_2011_01 <- rast("output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_2011_01.tif")
CCAP_2011_01_global <- rast("output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_2011_decay_01_global.tif")
CCAP_2011_decay <- rast("output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_2011_decay_masked.tif")
CCAP_2021_01 <- rast("output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_2021_01.tif")
CCAP_2021_01_global <- rast("output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_2021_decay_01_global.tif")
CCAP_2021_decay <- rast("output_data/finalized_Urban/V1.5/UrbanRunoff_CCAP_2021_decay_masked.tif")


## QAQC Layer
OceanMask_100m_2023_10 <- rast("qaqc/QAQC_layer/OceanMask_100m_2023_10.tif") # QAQC


#==========================================================================================================#
# D. Methods -----------------------------------------------------------------
#==========================================================================================================#
# Part I. GIS QAQC   ---------------------------------------------------------
#==========================================================================================================#
## 1.01. The projections for the layers are in NAD 83 UTM 4
st_crs(CCAP_2011_01)$epsg
st_crs(CCAP_2011_01_global)$epsg
st_crs(CCAP_2011_decay)$epsg
st_crs(CCAP_2021_01)$epsg
st_crs(CCAP_2021_01_global)$epsg
st_crs(CCAP_2021_decay)$epsg

## 1.02. The resolution of the layers is a 100 x 100 m  cell size
res(CCAP_2011_01)
res(CCAP_2011_01_global)
res(CCAP_2011_decay)
res(CCAP_2021_01)
res(CCAP_2021_01_global)
res(CCAP_2021_decay)
res(OceanMask_100m_2023_10)

## 1.03. The layers align to the OceanMask_100m_2023_10 layer in the CommonInputs_2022_2023 geodatabase.
origin(CCAP_2011_01)
origin(CCAP_2011_01_global)
origin(CCAP_2011_decay)
origin(CCAP_2021_01)
origin(CCAP_2021_01_global)
origin(CCAP_2021_decay)
origin(OceanMask_100m_2023_10)

## 1.04. The extent is aligned to the ocean mask as well (no cut corners or edges)
ext(CCAP_2011_01)
ext(CCAP_2011_01_global)
ext(CCAP_2011_decay)
ext(CCAP_2021_01)
ext(CCAP_2021_01_global)
ext(CCAP_2021_decay)
ext(OceanMask_100m_2023_10)

## 1.05 Final Check
### SA Report Layer
compareGeom(CCAP_2011_01, OceanMask_100m_2023_10)      # Why is OTP a different extent?
compareGeom(CCAP_2011_01_global, OceanMask_100m_2023_10)
compareGeom(CCAP_2011_decay, OceanMask_100m_2023_10)
compareGeom(CCAP_2021_01, OceanMask_100m_2023_10)
compareGeom(CCAP_2021_01_global, OceanMask_100m_2023_10)
compareGeom(CCAP_2021_decay, OceanMask_100m_2023_10)

