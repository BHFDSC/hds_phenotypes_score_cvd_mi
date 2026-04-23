# SCORE-CVD: Myocardial infarction alogrithm 
# Run the MI algorithm 
# pipeline_run.R
# BHF Data Science Centre, 2025
#
# Authors:
# - Laura Sherlock, BHF Data Science Centre
# 
# Date Created: 2025-05-12
# Last updated: 2025-05-12
# Version:      v0.1
#
# This script runs each of the function scripts needed to process the HES APC data and ONS deaths data through the MI algorithm. 
# This includes the following scripts which have been refactored to function:
# 01_hes_apc_prepare_function.R - prepares the HES APC data
# 01b_ons_deaths_prepare_fucntion.R - prepares the ONS deaths data
# 02_hes_apc_generate_cips_function.R - generates the continuous inpatoent spell (CIPS) ID
# 03_hes_apc_mi_function.R - identifies MI events in the HES APC data and outputs the number of MI events, and the 
# terminal node of the decision tree logic which the event corresponds to
# 04_ons_deaths_mi_function.R - identifies MI events in ONS Deaths data and outputs the number of MI events, and the 
# terminal node of the decision tree logic which the event corresponds to

# user required to add their data to the folders "data/hes_apc_data" and "ons_deaths_data" 
# user required to input the name of the person ID in their data
 
# Load necessary libraries
library(tidyverse)
library(glue)

# --- Define ID name ---
# NB to be changed by algorithm user depending on ID name in the data set
person_id_var <- "person_id"

# --- Defines the paths to input and output files ---
input_hes_apc_path <- here::here ("data", "hes_apc_data")
output_hes_apc_path <- here::here ("data", "interim_data")

input_ons_deaths_path <- here::here ("data", "ons_deaths_data", "ons_deaths_data.csv")
output_ons_deaths_path <- here::here ("data", "interim_data")

cips_input_path <- here::here ("data", "interim_data", "hes_apc_prepared.rds")
output_cips_path <-  here::here ("data", "interim_data")

mi_hes_apc_input_path <- here::here ("data", "interim_data", "hes_apc_prepared_cips.rds")
output_mi_hes_apc_path <-  here::here ("outputs")

mi_ons_deaths_input_path <-  here::here ("data", "interim_data", "ons_deaths_prepared.rds")
output_mi_ons_deaths_path <-  here::here ("outputs")
mi_hes_apc_processed_path <- here::here ("outputs", "hes_apc_mi_processed.rds")

# --- Validate required columns in raw HES APC and raw ONS Deaths data ---
# columns in raw data set can be upper or lower case
required_hes_cols <- c(person_id_var, "EPIKEY", "EPIORDER", "EPISTAT", "EPIEND", "ADMIDATE", "DISDATE", "PROCODE5", "ADMISORC", "ADMIMETH", "DISDEST", "DISMETH", "DIAG_3_CONCAT") 
required_ons_cols <- c(person_id_var, "DATE_OF_DEATH", "S_UNDERLYING_COD_ICD10", "S_COD_CODE_1", "S_COD_CODE_2") 

validate_columns <- function(df, required_cols, dataset_name = "Dataset") {
  df_cols_lower <- tolower(names(df))
  required_cols_lower <- tolower(required_cols)
  
  missing_cols <- required_cols[!tolower(required_cols) %in% df_cols_lower]
  
  if (length(missing_cols) > 0) {
    stop(paste("Missing required columns in", dataset_name, ":", paste(missing_cols, collapse = ", ")))
  } else {
    message(paste(dataset_name, "passed column validation"))
  }
}

# Load one of HES APC csv files for validating columns
hes_raw_file <- list.files(input_hes_apc_path, full.names = TRUE)[1]
hes_raw <- read_csv(hes_raw_file) 
validate_columns(hes_raw, required_hes_cols, "Raw HES-APC data")

# Load ONS deaths csv file for validating columns
ons_raw <- read_csv(input_ons_deaths_path)
validate_columns(ons_raw, required_ons_cols, "Raw ONS Deaths data")


# --- Source the functions ---
source(here::here("R", "functions", "hes_apc_prepare_function.R"))         # Function for 01_hes_apc_prepare.R
source(here::here("R", "functions", "ons_deaths_prepare_function.R"))      # Function for 01b_ons_deaths_prepare.R
source(here::here("R", "functions", "hes_apc_generate_cips_function.R"))   # Function for 02_hes_apc_generate_cips.R
source(here::here("R", "functions", "hes_apc_mi_function.R"))    # Function for 03_hes_apc_mi.R
source(here::here("R", "functions", "ons_deaths_mi_function.R"))    # Function for 04_ons_deaths_mi.R

# --- Pipeline process ---
# Step 1: Prepare HES-APC Data
prepare_hes_apc(input_hes_apc_path = input_hes_apc_path, 
                person_id_var = person_id_var,
                output_hes_apc_path =  output_hes_apc_path)

# Step 2: Prepare ONS Deaths Data
prepare_ons_deaths(input_ons_deaths_path =input_ons_deaths_path, 
                   person_id_var = person_id_var,
                    output_ons_deaths_path = output_ons_deaths_path)


# Step 3: Generate CIPS for HES-APC Data
generate_cips(cips_input_path = cips_input_path, 
               output_cips_path = output_cips_path)

# Step 4: Process HES-APC MI events
process_hes_apc_mi(  mi_hes_apc_input_path = mi_hes_apc_input_path,
                    output_mi_hes_apc_path =  output_mi_hes_apc_path)

# Step 5: Process ONS Deaths MI events
process_ons_deaths_mi(mi_ons_deaths_input_path = mi_ons_deaths_input_path, 
                      output_mi_ons_deaths_path = output_mi_ons_deaths_path, 
                      mi_hes_apc_input_path = mi_hes_apc_input_path, 
                      mi_hes_apc_processed_path = mi_hes_apc_processed_path)

# End of pipeline
cat("Pipeline run completed successfully.\n")

